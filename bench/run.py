#!/usr/bin/env python3
import argparse, csv, gzip, json, os, random, shutil, signal, subprocess, sys, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOADGEN = ROOT / "loadgen" / "loadgen"
SERVER = ROOT / "server" / "server.ts"
DATA = ROOT / "data"
CLK_TCK = os.sysconf("SC_CLK_TCK")
PAGE_KIB = os.sysconf("SC_PAGE_SIZE") // 1024

CONFIGS = {
    "sha256": ("SHA-256 (insecure control)", {"ALGO": "sha256"}),
    "bcrypt4": ("bcrypt cost 4 (low)", {"ALGO": "bcrypt", "COST": "4"}),
    "bcrypt10": ("bcrypt cost 10 (OWASP minimum)", {"ALGO": "bcrypt", "COST": "10"}),
    "bcrypt12": ("bcrypt cost 12 (stronger)", {"ALGO": "bcrypt", "COST": "12"}),
    "argon_low": (
        "Argon2id m=4 MiB t=1 (low)",
        {"ALGO": "argon2id", "MEM_KIB": "4096", "TIME": "1"},
    ),
    "argon_o5": (
        "Argon2id m=7 MiB t=5 (OWASP)",
        {"ALGO": "argon2id", "MEM_KIB": "7168", "TIME": "5"},
    ),
    "argon_o2": (
        "Argon2id m=19 MiB t=2 (OWASP)",
        {"ALGO": "argon2id", "MEM_KIB": "19456", "TIME": "2"},
    ),
    "argon_o1": (
        "Argon2id m=46 MiB t=1 (OWASP)",
        {"ALGO": "argon2id", "MEM_KIB": "47104", "TIME": "1"},
    ),
    "argon_bun": (
        "Argon2id m=64 MiB t=2 (Bun default)",
        {"ALGO": "argon2id", "MEM_KIB": "65536", "TIME": "2"},
    ),
}

SERVER_CPUS = "0-4,6-10"
LOADGEN_CPUS = "5,11"

EXPERIMENTS = {
    "main": dict(
        configs=list(CONFIGS),
        conc=[1, 2, 4, 8, 16, 32, 64, 128],
        cpus=[SERVER_CPUS],
        memmax=[None],
        reps=5,
    ),
    "cores": dict(
        configs=["bcrypt10", "argon_o5", "argon_o2", "argon_o1", "argon_bun"],
        conc=[32],
        cpus=["0", "0-1", "0-2", "0-3", "0-4", "0-4,6-10"],
        memmax=[None],
        reps=3,
    ),
    "memlimit": dict(
        configs=["bcrypt10", "argon_o2", "argon_bun"],
        conc=[64],
        cpus=[SERVER_CPUS],
        memmax=[None, "512M", "256M", "128M"],
        reps=3,
    ),
    "memthreshold": dict(
        configs=["argon_bun"],
        conc=[4, 6, 7, 8, 9, 10, 12],
        cpus=[SERVER_CPUS],
        memmax=["512M"],
        reps=3,
    ),
}


def read_proc(pid):
    """Return (rss_kib, hwm_kib, cpu_seconds) for a pid, or None if gone."""
    try:
        with open(f"/proc/{pid}/status") as f:
            st = f.read()
        rss = hwm = 0
        for line in st.splitlines():
            if line.startswith("VmRSS:"):
                rss = int(line.split()[1])
            elif line.startswith("VmHWM:"):
                hwm = int(line.split()[1])
        with open(f"/proc/{pid}/stat") as f:
            fields = f.read().rsplit(")", 1)[1].split()
        cpu = (int(fields[11]) + int(fields[12])) / CLK_TCK  # utime + stime
        return rss, hwm, cpu
    except (FileNotFoundError, ProcessLookupError, IndexError, ValueError):
        return None


def sys_cpu():
    with open("/proc/stat") as f:
        v = list(map(int, f.readline().split()[1:]))
    idle = v[3] + v[4]
    return sum(v), idle


def environment():
    def sh(cmd):
        try:
            return subprocess.run(
                cmd, shell=True, capture_output=True, text=True
            ).stdout.strip()
        except Exception as e:
            return str(e)

    return {
        "bun": sh("bun --version"),
        "go": sh("go version"),
        "python": sys.version.split()[0],
        "kernel": sh("uname -r"),
        "cpu": sh("lscpu | grep 'Model name' | sed 's/.*: *//'"),
        "logical_cpus": os.cpu_count(),
        "mem_total": sh("grep MemTotal /proc/meminfo"),
        "governor": sh("cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor"),
        "date": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def start_server(cfg_env, cpus, memmax, port):
    env = dict(os.environ, PORT=str(port), N_USERS="100", **cfg_env)
    cmd = ["taskset", "-c", cpus, "bun", str(SERVER)]
    if memmax:
        env["SEED_CONCURRENCY"] = "1"
        cmd = [
            "systemd-run",
            "--user",
            "--scope",
            "--quiet",
            "-p",
            f"MemoryMax={memmax}",
            "-p",
            "MemorySwapMax=0",
        ] + cmd
    p = subprocess.Popen(
        cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    deadline = time.time() + 120
    while time.time() < deadline:
        line = p.stdout.readline()
        if not line:
            break
        if line.startswith("READY"):
            pid = int(line.strip().rsplit("pid=", 1)[1])
            threading.Thread(
                target=lambda: [None for _ in p.stdout], daemon=True
            ).start()
            return p, pid
    p.kill()
    raise RuntimeError(f"server failed to start: {cfg_env} cpus={cpus} memmax={memmax}")


def stop_server(p):
    if p.poll() is None:
        p.send_signal(signal.SIGTERM)
        try:
            p.wait(5)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()


def run_one(exp, run_id, cfg, conc, cpus, memmax, rep, dur, warm, port, rawdir):
    label, cfg_env = CONFIGS[cfg]
    try:
        p, pid = start_server(cfg_env, cpus, memmax, port)
    except RuntimeError as e:
        print("START FAILED:", e, flush=True)
        return {
            "experiment": exp,
            "run_id": run_id,
            "config": cfg,
            "label": label,
            "algo": cfg_env["ALGO"],
            "cost": cfg_env.get("COST", ""),
            "mem_kib": cfg_env.get("MEM_KIB", ""),
            "time_cost": cfg_env.get("TIME", ""),
            "concurrency": conc,
            "server_cpus": cpus,
            "n_server_cpus": len(expand_cpus(cpus)),
            "memmax": memmax or "none",
            "rep": rep,
            "duration_s": dur,
            "ok": 0,
            "errors": 0,
            "rps": 0.0,
            "p50_ms": "",
            "p90_ms": "",
            "p99_ms": "",
            "max_ms": "",
            "rss_idle_mib": "",
            "rss_mean_mib": "",
            "rss_max_sampled_mib": "",
            "peak_rss_mib": "",
            "server_cpu_cores": "",
            "loadgen_cpu_cores": "",
            "sys_cpu_util": "",
            "server_survived": "start_failed",
        }
    time.sleep(0.5)
    base = read_proc(pid)
    try:
        with open(f"/proc/{pid}/clear_refs", "w") as f:
            f.write("5")
    except OSError as e:
        print("clear_refs failed:", e, file=sys.stderr)

    raw_csv = rawdir / f"{run_id}.csv"
    lg_cmd = [
        "taskset",
        "-c",
        LOADGEN_CPUS,
        str(LOADGEN),
        "-url",
        f"http://127.0.0.1:{port}/login",
        "-c",
        str(conc),
        "-d",
        f"{dur}s",
        "-warmup",
        f"{warm}s",
        "-out",
        str(raw_csv),
    ]
    t_start = time.time()
    lg = subprocess.Popen(
        lg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    samples = []
    while lg.poll() is None:
        t = time.time() - t_start
        s = read_proc(pid)
        lgs = read_proc(lg.pid)
        tot, idle = sys_cpu()
        samples.append(
            (
                t,
                *(s or (0, 0, float("nan"))),
                lgs[2] if lgs else float("nan"),
                tot,
                idle,
                0 if s else 1,
            )
        )
        time.sleep(0.1)
    out, err = lg.communicate()
    end = read_proc(pid)
    server_alive = p.poll() is None and end is not None
    stop_server(p)

    summary = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}

    win = [s for s in samples if warm <= s[0] <= warm + dur and s[7] == 0]
    if len(win) >= 2:
        a, b = win[0], win[-1]
        dt = b[0] - a[0]
        srv_cores = (b[3] - a[3]) / dt
        lg_cores = (b[4] - a[4]) / dt
        sys_util = 1 - (b[6] - a[6]) / max(1, (b[5] - a[5]))
        rss_mean = sum(s[1] for s in win) / len(win)
        rss_max_sampled = max(s[1] for s in win)
    else:
        srv_cores = lg_cores = sys_util = rss_mean = rss_max_sampled = float("nan")

    with open(raw_csv, "rb") as fi, gzip.open(str(raw_csv) + ".gz", "wb") as fo:
        shutil.copyfileobj(fi, fo)
    raw_csv.unlink()
    with gzip.open(rawdir / f"{run_id}.samples.csv.gz", "wt") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "t_s",
                "rss_kib",
                "hwm_kib",
                "server_cpu_s",
                "loadgen_cpu_s",
                "sys_total_ticks",
                "sys_idle_ticks",
                "server_missing",
            ]
        )
        w.writerows(samples)

    return {
        "experiment": exp,
        "run_id": run_id,
        "config": cfg,
        "label": label,
        "algo": cfg_env["ALGO"],
        "cost": cfg_env.get("COST", ""),
        "mem_kib": cfg_env.get("MEM_KIB", ""),
        "time_cost": cfg_env.get("TIME", ""),
        "concurrency": conc,
        "server_cpus": cpus,
        "n_server_cpus": len(expand_cpus(cpus)),
        "memmax": memmax or "none",
        "rep": rep,
        "duration_s": dur,
        "ok": summary.get("ok", 0),
        "errors": summary.get("errors", 0),
        "rps": summary.get("rps_ok", 0),
        "p50_ms": summary.get("p50_ms", ""),
        "p90_ms": summary.get("p90_ms", ""),
        "p99_ms": summary.get("p99_ms", ""),
        "max_ms": summary.get("max_ms", ""),
        "rss_idle_mib": round(base[0] / 1024, 1) if base else "",
        "rss_mean_mib": round(rss_mean / 1024, 1),
        "rss_max_sampled_mib": round(rss_max_sampled / 1024, 1),
        "peak_rss_mib": round(end[1] / 1024, 1) if end else "",
        "server_cpu_cores": round(srv_cores, 3),
        "loadgen_cpu_cores": round(lg_cores, 3),
        "sys_cpu_util": round(sys_util, 3),
        "server_survived": server_alive,
    }


def expand_cpus(s):
    out = []
    for part in s.split(","):
        if "-" in part:
            a, b = map(int, part.split("-"))
            out += range(a, b + 1)
        else:
            out.append(int(part))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("experiment", choices=EXPERIMENTS)
    ap.add_argument("--reps", type=int)
    ap.add_argument("--dur", type=float, default=8)
    ap.add_argument("--warm", type=float, default=2)
    ap.add_argument("--port", type=int, default=3100)
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument(
        "--quick", action="store_true", help="smoke test: 1 rep, 2 s, few points"
    )
    a = ap.parse_args()

    E = dict(EXPERIMENTS[a.experiment])
    reps = a.reps or E["reps"]
    if a.quick:
        reps, a.dur, a.warm = 1, 2, 0.5
        E["conc"] = E["conc"][:: max(1, len(E["conc"]) // 2)]

    plan = [
        (cfg, c, cpus, mm, r)
        for cfg in E["configs"]
        for c in E["conc"]
        for cpus in E["cpus"]
        for mm in E["memmax"]
        for r in range(1, reps + 1)
    ]
    random.Random(a.seed).shuffle(plan)

    tag = a.experiment + ("_quick" if a.quick else "")
    rawdir = DATA / "raw" / tag
    rawdir.mkdir(parents=True, exist_ok=True)
    (DATA / f"environment_{tag}.json").write_text(json.dumps(environment(), indent=2))
    out_csv = DATA / f"{tag}_runs.csv"
    done = set()
    if out_csv.exists():
        with open(out_csv) as f:
            done = {r["run_id"] for r in csv.DictReader(f)}

    est = len(plan) * (a.dur + a.warm + 1.5) / 60
    print(f"{tag}: {len(plan)} runs, ~{est:.0f} min", flush=True)
    for i, (cfg, c, cpus, mm, r) in enumerate(plan, 1):
        run_id = f"{cfg}_c{c}_cpu{cpus.replace(',', '+')}_mem{mm or 'none'}_r{r}"
        if run_id in done:
            continue
        row = run_one(
            a.experiment, run_id, cfg, c, cpus, mm, r, a.dur, a.warm, a.port, rawdir
        )
        new = not out_csv.exists()
        with open(out_csv, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(row))
            if new:
                w.writeheader()
            w.writerow(row)
        print(
            f"[{i}/{len(plan)}] {run_id}: {row['rps']:.1f} rps p99={row['p99_ms']} ms "
            f"peak={row['peak_rss_mib']} MiB cpu={row['server_cpu_cores']} err={row['errors']}",
            flush=True,
        )
        time.sleep(0.3)


if __name__ == "__main__":
    main()
