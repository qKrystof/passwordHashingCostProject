#!/usr/bin/env python3

import csv
import gzip
import math
from collections import defaultdict
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA, RES = ROOT / "data", ROOT / "results"
FIG = RES / "figures"
FIG.mkdir(parents=True, exist_ok=True)

ORDER = [
    "sha256",
    "bcrypt4",
    "bcrypt10",
    "bcrypt12",
    "argon_low",
    "argon_o5",
    "argon_o2",
    "argon_o1",
    "argon_bun",
]
SHORT = {
    "sha256": "SHA-256 control",
    "bcrypt4": "bcrypt c=4",
    "bcrypt10": "bcrypt c=10",
    "bcrypt12": "bcrypt c=12",
    "argon_low": "Argon2id 4MiB/t1",
    "argon_o5": "Argon2id 7MiB/t5",
    "argon_o2": "Argon2id 19MiB/t2",
    "argon_o1": "Argon2id 46MiB/t1",
    "argon_bun": "Argon2id 64MiB/t2",
}
MEM_MIB = {
    "argon_low": 4,
    "argon_o5": 7,
    "argon_o2": 19,
    "argon_o1": 46,
    "argon_bun": 64,
}

PAL = [
    "#2a78d6",
    "#eb6834",
    "#1baf7a",
    "#eda100",
    "#e87ba4",
    "#008300",
    "#6250d6",
    "#e34948",
]
GRAY = "#8a8985"
COLOR = {
    "sha256": GRAY,
    "bcrypt4": PAL[0],
    "bcrypt10": PAL[1],
    "bcrypt12": PAL[2],
    "argon_low": PAL[0],
    "argon_o5": PAL[1],
    "argon_o2": PAL[2],
    "argon_o1": PAL[3],
    "argon_bun": PAL[4],
}
T95 = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
}

plt.rcParams.update(
    {
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#52514e",
        "axes.labelcolor": "#0b0b0b",
        "xtick.color": "#52514e",
        "ytick.color": "#52514e",
        "axes.grid": True,
        "grid.color": "#e4e3df",
        "grid.linewidth": 0.6,
        "lines.linewidth": 1.6,
        "lines.markersize": 4.5,
        "legend.frameon": False,
        "figure.dpi": 150,
        "savefig.bbox": "tight",
    }
)


def load(name):
    p = DATA / f"{name}_runs.csv"
    if not p.exists():
        return []
    with open(p) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("concurrency", "rep", "ok", "errors", "n_server_cpus"):
            r[k] = int(r[k])
        for k in (
            "rps",
            "p50_ms",
            "p90_ms",
            "p99_ms",
            "max_ms",
            "rss_idle_mib",
            "rss_mean_mib",
            "peak_rss_mib",
            "server_cpu_cores",
            "loadgen_cpu_cores",
            "sys_cpu_util",
        ):
            r[k] = float(r[k]) if r[k] not in ("", "nan") else float("nan")
    return rows


def stats(xs):
    xs = np.asarray([x for x in xs if not math.isnan(x)], dtype=float)
    n = len(xs)
    if n == 0:
        return dict(n=0, mean=float("nan"), sd=float("nan"), ci=float("nan"))
    sd = xs.std(ddof=1) if n > 1 else 0.0
    ci = T95.get(n - 1, 1.96) * sd / math.sqrt(n) if n > 1 else float("nan")
    return dict(n=n, mean=xs.mean(), sd=sd, ci=ci)


def raw_latency_stats(exp, run_id):
    """Recompute mean / p99 latency from the per-request file (independent check of loadgen)."""
    p = DATA / "raw" / exp / f"{run_id}.csv.gz"
    lat = []
    with gzip.open(p, "rt") as f:
        next(f)
        for line in f:
            _, l, s = line.rstrip().split(",")
            if s == "200":
                lat.append(int(l) / 1000)
    lat = np.sort(np.asarray(lat))
    if len(lat) == 0:
        return float("nan"), float("nan")
    k = max(0, math.ceil(0.99 * len(lat)) - 1)
    return lat.mean(), lat[k]


def fmt(x, d=1):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    if abs(x) >= 1000:
        return f"{x:,.0f}"
    return f"{x:.{d}f}"


md = []

main = load("main")
if main:
    for r in main:
        r["mean_lat_ms"], r["p99_raw_ms"] = raw_latency_stats("main", r["run_id"])
        r["little_L"] = r["rps"] * r["mean_lat_ms"] / 1000

    g = defaultdict(list)
    for r in main:
        g[(r["config"], r["concurrency"])].append(r)
    concs = sorted({r["concurrency"] for r in main})
    configs = [c for c in ORDER if any(k[0] == c for k in g)]

    summary = []
    for cfg in configs:
        for c in concs:
            rs = g.get((cfg, c), [])
            if not rs:
                continue
            row = {"config": cfg, "label": SHORT[cfg], "concurrency": c, "n": len(rs)}
            for m in (
                "rps",
                "p50_ms",
                "p99_ms",
                "mean_lat_ms",
                "peak_rss_mib",
                "rss_idle_mib",
                "server_cpu_cores",
                "loadgen_cpu_cores",
                "little_L",
            ):
                s = stats([r[m] for r in rs])
                row[f"{m}_mean"], row[f"{m}_sd"], row[f"{m}_ci95"] = (
                    s["mean"],
                    s["sd"],
                    s["ci"],
                )
            row["errors_total"] = sum(r["errors"] for r in rs)
            row["p99_loadgen_vs_raw_maxdiff_ms"] = max(
                abs(r["p99_ms"] - r["p99_raw_ms"]) for r in rs
            )
            row["cv_rps_pct"] = (
                100 * row["rps_sd"] / row["rps_mean"]
                if row["rps_mean"]
                else float("nan")
            )
            summary.append(row)
    with open(RES / "main_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        for row in summary:
            w.writerow(
                {
                    k: (round(v, 4) if isinstance(v, float) else v)
                    for k, v in row.items()
                }
            )
    S = {(r["config"], r["concurrency"]): r for r in summary}

    cmax = max(concs)
    cap = {
        cfg: max(S[(cfg, c)]["rps_mean"] for c in concs if (cfg, c) in S)
        for cfg in configs
    }
    md.append("## Table 1 – Capacity per configuration (E1)\n")
    md.append(
        "Capacity = highest mean logins/s over all concurrency levels. Latency at c=1 is the "
        "mean latency of a single uncontended login. CPU and peak RSS are at c=%d. "
        "Relative capacity is vs. bcrypt cost 10 (OWASP minimum)." % cmax
    )
    md.append("")
    md.append(
        "| Configuration | Latency c=1 (ms) | Capacity (logins/s) | ±95% CI | Rel. to bcrypt-10 | "
        f"p99 c=16 (ms) | p99 c={cmax} (ms) | Server CPU cores c={cmax} | Peak RSS c={cmax} (MiB) |"
    )
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for cfg in configs:
        cbest = max(
            (c for c in concs if (cfg, c) in S), key=lambda c: S[(cfg, c)]["rps_mean"]
        )
        md.append(
            f"| {SHORT[cfg]} | {fmt(S[(cfg, 1)]['mean_lat_ms_mean'], 2)} | {fmt(cap[cfg])} | "
            f"{fmt(S[(cfg, cbest)]['rps_ci95'])} | {cap[cfg] / cap['bcrypt10']:.2f}× | "
            f"{fmt(S[(cfg, 16)]['p99_ms_mean'])} | {fmt(S[(cfg, cmax)]['p99_ms_mean'])} | "
            f"{fmt(S[(cfg, cmax)]['server_cpu_cores_mean'], 2)} | {fmt(S[(cfg, cmax)]['peak_rss_mib_mean'])} |"
        )
    md.append("")

    md.append("## Table 2 – Logins/s (mean ± sd, n=5) by concurrency (E1)\n")
    md.append("| Configuration | " + " | ".join(f"c={c}" for c in concs) + " |")
    md.append("|---|" + "---:|" * len(concs))
    for cfg in configs:
        md.append(
            f"| {SHORT[cfg]} | "
            + " | ".join(
                f"{fmt(S[(cfg, c)]['rps_mean'])} ± {fmt(S[(cfg, c)]['rps_sd'])}"
                for c in concs
            )
            + " |"
        )
    md.append("")
    md.append("## Table 3 – p99 latency in ms (mean ± sd, n=5) by concurrency (E1)\n")
    md.append("| Configuration | " + " | ".join(f"c={c}" for c in concs) + " |")
    md.append("|---|" + "---:|" * len(concs))
    for cfg in configs:
        md.append(
            f"| {SHORT[cfg]} | "
            + " | ".join(
                f"{fmt(S[(cfg, c)]['p99_ms_mean'])} ± {fmt(S[(cfg, c)]['p99_ms_sd'])}"
                for c in concs
            )
            + " |"
        )
    md.append("")
    md.append("## Table 4 – Peak server RSS in MiB (mean, n=5) by concurrency (E1)\n")
    md.append("| Configuration | idle | " + " | ".join(f"c={c}" for c in concs) + " |")
    md.append("|---|---:|" + "---:|" * len(concs))
    for cfg in configs:
        md.append(
            f"| {SHORT[cfg]} | {fmt(S[(cfg, 1)]['rss_idle_mib_mean'])} | "
            + " | ".join(fmt(S[(cfg, c)]["peak_rss_mib_mean"]) for c in concs)
            + " |"
        )
    md.append("")

    md.append(
        "## Table 5 – CPU time per login (core-ms), uncontended vs saturated (E1)\n"
    )
    md.append(
        "core-ms/login = server CPU cores used ÷ logins/s × 1000. A rise under load means each "
        "hash got slower while sharing the machine (SMT siblings, shared cache, memory bandwidth)."
    )
    md.append("")
    md.append(
        f"| Configuration | c=1 | c={cmax} | Ratio | Speed-up c=1→c={cmax} (10 logical CPUs) |"
    )
    md.append("|---|---:|---:|---:|---:|")
    for cfg in configs:
        a = S[(cfg, 1)]["server_cpu_cores_mean"] / S[(cfg, 1)]["rps_mean"] * 1000
        b = S[(cfg, cmax)]["server_cpu_cores_mean"] / S[(cfg, cmax)]["rps_mean"] * 1000
        md.append(
            f"| {SHORT[cfg]} | {a:.2f} | {b:.2f} | {b / a:.2f}× | "
            f"{S[(cfg, cmax)]['rps_mean'] / S[(cfg, 1)]['rps_mean']:.2f}× |"
        )
    md.append("")

    md.append("## Table 6 – Memory model check (E1)\n")
    md.append(
        "Model: peak RSS ≈ idle RSS + k × m, where m = Argon2id memoryCost and k = number of hashes "
        "in memory at once. k is estimated from the data as (peak − idle)/m."
    )
    md.append("")
    md.append(
        "| Configuration | m (MiB) | " + " | ".join(f"k̂ c={c}" for c in concs) + " |"
    )
    md.append("|---|---:|" + "---:|" * len(concs))
    for cfg in configs:
        if cfg not in MEM_MIB:
            continue
        m = (
            MEM_MIB[cfg]
            * (1.0 if cfg != "argon_o2" else 19456 / 19 / 1024)
            * (1.0 if cfg != "argon_o1" else 47104 / 46 / 1024)
        )
        cells = []
        for c in concs:
            r = S[(cfg, c)]
            cells.append(f"{(r['peak_rss_mib_mean'] - r['rss_idle_mib_mean']) / m:.1f}")
        md.append(f"| {SHORT[cfg]} | {m:.1f} | " + " | ".join(cells) + " |")
    md.append("")

    worst_l = max(
        abs(r["little_L"] - r["concurrency"]) / r["concurrency"]
        for r in main
        if r["rps"] > 0
    )
    worst_p99 = max(r["p99_loadgen_vs_raw_maxdiff_ms"] for r in summary)
    tot_err = sum(r["errors"] for r in main)
    max_cv = max((r["cv_rps_pct"], r["config"], r["concurrency"]) for r in summary)
    lg_max = max((S[k]["loadgen_cpu_cores_mean"], k) for k in S)
    md.append("## Measurement checks (E1)\n")
    md.append(f"- Runs: {len(main)}; failed/non-200 responses in all runs: {tot_err}.")
    md.append(
        f"- Little's law (L = λW): worst relative deviation of logins/s × mean latency from the "
        f"configured concurrency: {100 * worst_l:.1f}%."
    )
    md.append(
        f"- p99 from load generator vs recomputed from raw per-request files: max difference "
        f"{worst_p99:.3f} ms."
    )
    md.append(
        f"- Largest run-to-run coefficient of variation of logins/s: {max_cv[0]:.1f}% "
        f"({SHORT[max_cv[1]]}, c={max_cv[2]})."
    )
    md.append(
        f"- Highest mean load-generator CPU use: {lg_max[0][0] if False else lg_max[0]:.2f} cores "
        f"({SHORT[lg_max[1][0]]}, c={lg_max[1][1]}) out of the 2 logical CPUs reserved for it."
    )
    md.append("")

    fam = [
        (
            "bcrypt (with SHA-256 control)",
            ["sha256", "bcrypt4", "bcrypt10", "bcrypt12"],
        ),
        ("Argon2id", ["argon_low", "argon_o5", "argon_o2", "argon_o1", "argon_bun"]),
    ]

    def family_plot(metric, ylabel, fname, logy=True, title=None):
        fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
        for ax, (name, cfgs) in zip(axes, fam):
            for cfg in cfgs:
                if (cfg, 1) not in S:
                    continue
                y = np.array([S[(cfg, c)][f"{metric}_mean"] for c in concs])
                e = np.array([S[(cfg, c)][f"{metric}_ci95"] for c in concs])
                ax.plot(
                    concs,
                    y,
                    marker="o",
                    color=COLOR[cfg],
                    label=SHORT[cfg],
                    linestyle="--" if cfg == "sha256" else "-",
                )
                ax.fill_between(
                    concs, y - e, y + e, color=COLOR[cfg], alpha=0.15, linewidth=0
                )
            ax.set_xscale("log", base=2)
            ax.set_xticks(concs, [str(c) for c in concs])
            if logy:
                ax.set_yscale("log")
            ax.set_title(name, fontsize=9, loc="left")
            ax.set_xlabel("Concurrent login clients")
            ax.legend(fontsize=7, loc="best")
        axes[0].set_ylabel(ylabel)
        fig.savefig(FIG / fname)
        plt.close(fig)

    family_plot("rps", "Successful logins per second (log)", "fig1_throughput.png")
    family_plot("p99_ms", "p99 latency, ms (log)", "fig2_p99.png")

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    show = ["bcrypt10", "bcrypt12", "argon_o5", "argon_o2", "argon_o1", "argon_bun"]
    col3 = dict(zip(show, PAL))
    for cfg in show:
        y = [S[(cfg, c)]["server_cpu_cores_mean"] for c in concs]
        axes[0].plot(concs, y, marker="o", color=col3[cfg], label=SHORT[cfg])
        y = [S[(cfg, c)]["peak_rss_mib_mean"] for c in concs]
        axes[1].plot(concs, y, marker="o", color=col3[cfg], label=SHORT[cfg])
    axes[0].axhline(10, color=GRAY, linestyle=":", linewidth=1)
    axes[0].text(1, 10.2, "10 logical CPUs allotted", fontsize=7, color="#52514e")
    axes[0].set_ylabel("Server CPU use (cores)")
    axes[0].set_ylim(0, 11.5)
    axes[1].set_ylabel("Peak server RSS (MiB)")
    for ax in axes:
        ax.set_xscale("log", base=2)
        ax.set_xticks(concs, [str(c) for c in concs])
        ax.set_xlabel("Concurrent login clients")
    axes[0].set_title("CPU saturates at c≈8–16", fontsize=9, loc="left")
    axes[1].set_title(
        "Memory plateaus with CPU (≈2% of 30 GiB RAM)", fontsize=9, loc="left"
    )
    axes[1].legend(fontsize=7, loc="upper left")
    fig.savefig(FIG / "fig3_resources.png")
    plt.close(fig)


cores = load("cores")
if cores:
    g = defaultdict(list)
    for r in cores:
        g[(r["config"], r["server_cpus"])].append(r)
    cpu_sets = ["0", "0-1", "0-2", "0-3", "0-4", "0-4,6-10"]
    xlab = {
        "0": "1",
        "0-1": "2",
        "0-2": "3",
        "0-3": "4",
        "0-4": "5",
        "0-4,6-10": "5+SMT",
    }
    cfgs = [c for c in ORDER if any(k[0] == c for k in g)]
    rows = []
    for cfg in cfgs:
        for cs in cpu_sets:
            s = stats([r["rps"] for r in g[(cfg, cs)]])
            rows.append(
                dict(  # noqa: C408
                    config=cfg,
                    server_cpus=cs,
                    n=s["n"],
                    rps_mean=s["mean"],
                    rps_sd=s["sd"],
                    rps_ci95=s["ci"],
                    p99_ms_mean=stats([r["p99_ms"] for r in g[(cfg, cs)]])["mean"],
                    cpu_cores_mean=stats([r["server_cpu_cores"] for r in g[(cfg, cs)]])[
                        "mean"
                    ],
                )
            )
    with open(RES / "cores_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    C = {(r["config"], r["server_cpus"]): r for r in rows}
    md.append(
        "## Table 7 – Core scaling at c=32 (E2): logins/s and speed-up over one core\n"
    )
    md.append(
        "Server pinned to 1–5 physical cores (one hardware thread each), then 5 cores with both SMT "
        "threads. Efficiency = speed-up ÷ cores. SMT gain = (5 cores + SMT) ÷ (5 cores)."
    )
    md.append("")
    md.append(
        "| Configuration | "
        + " | ".join(f"{xlab[c]} cores" for c in cpu_sets)
        + " | Speed-up @5 | Efficiency @5 | SMT gain |"
    )
    md.append("|---|" + "---:|" * (len(cpu_sets) + 3))
    for cfg in cfgs:
        b = C[(cfg, "0")]["rps_mean"]
        cells = [
            f"{fmt(C[(cfg, c)]['rps_mean'])} ± {fmt(C[(cfg, c)]['rps_sd'])}"
            for c in cpu_sets
        ]
        sp5 = C[(cfg, "0-4")]["rps_mean"] / b
        smt = C[(cfg, "0-4,6-10")]["rps_mean"] / C[(cfg, "0-4")]["rps_mean"]
        md.append(
            f"| {SHORT[cfg]} | "
            + " | ".join(cells)
            + f" | {sp5:.2f}× | {100 * sp5 / 5:.0f}% | {smt:.2f}× |"
        )
    md.append("")

    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    xs = list(range(1, 7))
    col = dict(zip(cfgs, PAL))
    ax.plot([1, 5], [1, 5], color=GRAY, linestyle=":", linewidth=1)
    ax.text(4.2, 4.55, "linear", fontsize=7, color="#52514e", rotation=35)
    for cfg in cfgs:
        b = C[(cfg, "0")]["rps_mean"]
        ys = [C[(cfg, c)]["rps_mean"] / b for c in cpu_sets]
        ax.plot(xs, ys, marker="o", color=col[cfg], label=SHORT[cfg])
    ax.set_xticks(xs, [xlab[c] for c in cpu_sets])
    ax.set_xlabel("Physical cores given to the server")
    ax.set_ylabel("Speed-up vs. 1 core (logins/s)")
    ax.legend(fontsize=7, loc="upper left")
    fig.savefig(FIG / "fig4_core_scaling.png")
    plt.close(fig)


ml = load("memlimit")
if ml:
    g = defaultdict(list)
    for r in ml:
        g[(r["config"], r["memmax"])].append(r)
    limits = ["none", "512M", "256M", "128M"]
    cfgs = [c for c in ORDER if any(k[0] == c for k in g)]
    md.append("## Table 8 – Behaviour under a cgroup memory limit at c=64 (E3)\n")
    md.append(
        "MemoryMax set on the server's cgroup with swap disabled (MemorySwapMax=0). "
        "Values: mean logins/s · mean p99 · total failed requests · runs where the server died (of n)."
    )
    md.append("")
    md.append("| Configuration | " + " | ".join(f"limit {l}" for l in limits) + " |")
    md.append("|---|" + "---|" * len(limits))
    rows = []
    for cfg in cfgs:
        cells = []
        for l in limits:
            rs = g.get((cfg, l), [])
            if not rs:
                cells.append("–")
                continue
            died = sum(1 for r in rs if r["server_survived"] != "True")
            rps = stats([r["rps"] for r in rs])["mean"]
            p99 = stats([r["p99_ms"] for r in rs if r["ok"] > 0])["mean"]
            err = sum(r["errors"] for r in rs)
            peak = stats([r["peak_rss_mib"] for r in rs])["mean"]
            cells.append(
                f"{fmt(rps)}/s · {fmt(p99)} ms · {err} err · {died}/{len(rs)} died"
            )
            rows.append(
                dict(
                    config=cfg,
                    memmax=l,
                    n=len(rs),
                    rps_mean=rps,
                    p99_ms_mean=p99,
                    errors=err,
                    died=died,
                    peak_rss_mib_mean=peak,
                )
            )
        md.append(f"| {SHORT[cfg]} | " + " | ".join(cells) + " |")
    md.append("")
    with open(RES / "memlimit_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

mt = load("memthreshold")
if mt:
    g = defaultdict(list)
    for r in mt:
        g[r["concurrency"]].append(r)
    md.append(
        "## Table 9 – OOM threshold, Argon2id 64 MiB/t=2 under MemoryMax=512M (E4)\n"
    )
    md.append(
        "Pre-registered prediction: idle (~21 MiB) + c × 64 MiB > 512 MiB ⇒ the server is killed for c ≥ 8."
    )
    md.append("")
    md.append(
        "| Concurrency c | Model peak (MiB) | Runs killed | Peak RSS of surviving runs (MiB) | Logins/s (survivors) |"
    )
    md.append("|---:|---:|---:|---|---:|")
    rows = []
    for c in sorted(g):
        rs = g[c]
        died = [r for r in rs if r["server_survived"] != "True"]
        surv = [r for r in rs if r["server_survived"] == "True"]
        peaks = ", ".join(fmt(r["peak_rss_mib"]) for r in surv) or "–"
        rps = stats([r["rps"] for r in surv])["mean"] if surv else float("nan")
        md.append(
            f"| {c} | {21.5 + 64 * c:.0f} | {len(died)}/{len(rs)} | {peaks} | {fmt(rps)} |"
        )
        rows.append(
            dict(
                concurrency=c,
                model_peak_mib=21.5 + 64 * c,
                killed=len(died),
                n=len(rs),
                surviving_peaks_mib=peaks,
                rps_survivors=rps,
            )
        )
    md.append("")
    with open(RES / "memthreshold_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

(RES / "tables.md").write_text("\n".join(md) + "\n")
print("\n".join(md))
