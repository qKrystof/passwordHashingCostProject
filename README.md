# What does safer password hashing cost your server?

Reproducibility package for the Architecture of Computers 2026/27 research project
*"Stronger password hashing and login capacity: bcrypt vs Argon2id under concurrent load on a Bun server"*.

All accounts are generated dummy accounts (`user0`…`user99`, password `pw-<i>-dummy`).
No real credentials or personal data are used. Every test runs on one machine against a local server.

## Layout

| Path | What it is |
|---|---|
| `server/server.ts` | Minimal Bun login endpoint (`POST /login`) using `Bun.password` (bcrypt / Argon2id) or an insecure SHA-256 control |
| `loadgen/main.go` | Closed-loop HTTP load generator that records every request (Go, standard library only) |
| `bench/run.py` | Experiment orchestrator: starts a fresh server per run, pins CPUs, samples RSS/CPU, randomises run order (Python standard library only) |
| `analysis/analyze.py` | Builds summary tables and figures from the raw data (numpy, matplotlib) |
| `data/*_runs.csv` | One row per run (per-run summary) for experiments E1 `main`, E2 `cores`, E3 `memlimit` |
| `data/raw/<exp>/<run>.csv.gz` | Raw per-request records: completion time, latency (µs), HTTP status |
| `data/raw/<exp>/<run>.samples.csv.gz` | 10 Hz samples of server RSS, peak RSS, CPU time, load-generator CPU time, system CPU |
| `data/environment_*.json` | Hardware/software versions recorded at the start of each experiment |
| `data/run_log.txt` | Console log of the full measurement session |
| `results/` | Generated tables (`tables.md`, `*_summary.csv`) and figures |
| `paper/` | Manuscript (Markdown source, HTML, PDF) |

## Requirements

* Linux (uses `/proc`, `taskset`; E3 needs `systemd-run --user` with cgroup v2 memory control)
* Bun ≥ 1.4 (tested with 1.4.4)
* Go ≥ 1.21 (tested with 1.27.3) – only to build the load generator
* Python ≥ 3.10 (standard library for running; `numpy`, `matplotlib`, `markdown` for analysis — see `requirements.txt`)
* Chromium (optional, to print the paper to PDF)

## Run

```bash
# 1. build the load generator
cd loadgen && go build -o loadgen . && cd ..

# 2. quick smoke test (~1 min)
python3 bench/run.py main --quick

# 3. full experiments (~80 + 15 + 8 min). Keep the machine otherwise idle.
python3 bench/run.py main       # E1: 9 configs x 8 concurrency levels x 5 reps
python3 bench/run.py cores      # E2: 5 configs x 6 CPU sets x 3 reps at c=32
python3 bench/run.py memlimit   # E3: 3 configs x 4 memory limits x 3 reps at c=64
python3 bench/run.py memthreshold  # E4: Argon2id 64 MiB under 512 MiB, c=4..12 x 3 reps (~5 min)

# 4. analysis
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python analysis/analyze.py

# 5. paper (Markdown -> HTML -> PDF)
.venv/bin/python paper/build.py
```

`bench/run.py` resumes an interrupted experiment (runs already in `data/<exp>_runs.csv` are skipped).
The run order is shuffled with a fixed seed (`--seed 2026`).

## Hashing configurations

| id | Algorithm and parameters | Source of the setting |
|---|---|---|
| `sha256` | single salted SHA-256 (**insecure**, control only) | lower bound: server cost without a password hash |
| `bcrypt4` | bcrypt cost 4 | "fast" setting (bcrypt minimum) |
| `bcrypt10` | bcrypt cost 10 | OWASP minimum work factor |
| `bcrypt12` | bcrypt cost 12 | stronger, commonly used |
| `argon_low` | Argon2id m=4096 KiB, t=1, p=1 | "fast" setting, below OWASP |
| `argon_o5` | Argon2id m=7168 KiB, t=5, p=1 | OWASP option |
| `argon_o2` | Argon2id m=19456 KiB, t=2, p=1 | OWASP option (the one in its summary) |
| `argon_o1` | Argon2id m=47104 KiB, t=1, p=1 | OWASP option |
| `argon_bun` | Argon2id m=65536 KiB, t=2, p=1 | Bun's default |

Bun does not expose Argon2 parallelism, so p=1 (as in all OWASP options).
RFC 9106's recommendations use p=4 and cannot be reproduced exactly with `Bun.password`.

## Measurement design

* Server: logical CPUs 0–4 and 6–10 (5 physical cores with SMT). Load generator: CPUs 5 and 11 (the 6th core).
* Closed loop: *c* clients, each with one request in flight. 2 s warm-up, then an 8 s measurement window.
* Logins/s = successful (HTTP 200) responses completed in the window ÷ 8 s. p99 = nearest-rank 99th percentile.
* Peak memory = `VmHWM` of the server, reset with `/proc/PID/clear_refs` after startup so seeding the dummy accounts is not counted.
* CPU = server user+system CPU time over the measurement window ÷ window length (in cores).
* Load-generator correctness check: with a 50 ms `/sleep` endpoint it measured 20, 320 and 2,560 req/s at c = 1, 16, 128 (expected c/0.05 s), with p99 ≈ 50.5–50.8 ms.

## Notes on the raw data

* E3/E4: when the server is OOM-killed it stays a zombie until the orchestrator reaps it, so in
  `*.samples.csv.gz` a killed server shows `rss_kib = 0` rather than `server_missing = 1`.
  The authoritative outcome is the `server_survived` column of the runs CSV (`True` / `False`).
* E3/E4 seed the 100 dummy accounts sequentially (`SEED_CONCURRENCY=1`); E1/E2 seed them in parallel.
  Peak RSS is reset after seeding in all experiments.
* E1 and E2 ran before `SEED_CONCURRENCY` was added to `server.ts`; its default reproduces the original behaviour.

## Limitations

See the paper's limitations section. In short: one machine (AMD Ryzen 5 7600X, 30 GiB RAM), one runtime (Bun 1.4.4),
load generator on the same host (isolated on its own core), loopback networking, closed-loop load (not open arrivals),
one user's credentials per run (hash cost does not depend on the account).
