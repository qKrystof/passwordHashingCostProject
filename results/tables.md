## Table 1 – Capacity per configuration (E1)

Capacity = highest mean logins/s over all concurrency levels. Latency at c=1 is the mean latency of a single uncontended login. CPU and peak RSS are at c=128. Relative capacity is vs. bcrypt cost 10 (OWASP minimum).

| Configuration | Latency c=1 (ms) | Capacity (logins/s) | ±95% CI | Rel. to bcrypt-10 | p99 c=16 (ms) | p99 c=128 (ms) | Server CPU cores c=128 | Peak RSS c=128 (MiB) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SHA-256 control | 0.03 | 119,075 | 682.6 | 507.40× | 0.4 | 3.2 | 0.80 | 45.2 |
| bcrypt c=4 | 0.76 | 13,955 | 32.3 | 59.46× | 2.3 | 34.8 | 9.93 | 44.0 |
| bcrypt c=10 | 39.89 | 234.7 | 0.7 | 1.00× | 170.9 | 1,998 | 9.98 | 30.4 |
| bcrypt c=12 | 158.71 | 58.8 | 0.0 | 0.25× | 681.0 | 7,489 | 9.98 | 29.2 |
| Argon2id 4MiB/t1 | 1.87 | 3,161 | 5.2 | 13.47× | 12.7 | 161.4 | 9.90 | 90.9 |
| Argon2id 7MiB/t5 | 15.09 | 345.0 | 0.4 | 1.47× | 116.8 | 1,491 | 9.93 | 106.5 |
| Argon2id 19MiB/t2 | 17.15 | 268.7 | 0.7 | 1.14× | 158.0 | 1,844 | 9.95 | 228.3 |
| Argon2id 46MiB/t1 | 21.14 | 222.2 | 0.2 | 0.95× | 194.2 | 2,302 | 9.95 | 490.8 |
| Argon2id 64MiB/t2 | 61.92 | 82.4 | 0.2 | 0.35× | 497.5 | 6,974 | 9.94 | 669.6 |

## Table 2 – Logins/s (mean ± sd, n=5) by concurrency (E1)

| Configuration | c=1 | c=2 | c=4 | c=8 | c=16 | c=32 | c=64 | c=128 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SHA-256 control | 37,698 ± 1,795 | 79,731 ± 1,337 | 99,093 ± 489.9 | 110,642 ± 3,859 | 119,075 ± 549.8 | 118,928 ± 395.9 | 117,429 ± 322.9 | 115,132 ± 525.7 |
| bcrypt c=4 | 1,314 ± 3.5 | 2,633 ± 4.4 | 5,526 ± 3.3 | 10,696 ± 1.1 | 13,069 ± 198.5 | 13,947 ± 23.8 | 13,955 ± 26.0 | 13,935 ± 76.8 |
| bcrypt c=10 | 25.0 ± 0.0 | 50.5 ± 0.1 | 99.8 ± 0.1 | 191.1 ± 0.8 | 234.4 ± 0.5 | 234.7 ± 0.5 | 234.5 ± 0.7 | 234.6 ± 0.5 |
| bcrypt c=12 | 6.3 ± 0.1 | 12.8 ± 0.0 | 25.5 ± 0.0 | 47.7 ± 0.2 | 58.8 ± 0.0 | 58.8 ± 0.0 | 58.7 ± 0.1 | 58.7 ± 0.1 |
| Argon2id 4MiB/t1 | 533.4 ± 4.7 | 1,095 ± 7.8 | 2,005 ± 10.9 | 2,948 ± 4.4 | 3,069 ± 155.2 | 3,161 ± 4.2 | 3,117 ± 100.9 | 3,102 ± 116.0 |
| Argon2id 7MiB/t5 | 66.3 ± 0.9 | 134.8 ± 0.8 | 233.5 ± 3.5 | 320.1 ± 1.9 | 344.9 ± 0.2 | 345.0 ± 0.3 | 344.9 ± 0.6 | 339.1 ± 12.1 |
| Argon2id 19MiB/t2 | 58.6 ± 4.7 | 106.2 ± 4.4 | 182.6 ± 0.6 | 249.8 ± 0.6 | 262.5 ± 12.5 | 268.7 ± 0.5 | 268.2 ± 1.2 | 268.1 ± 0.3 |
| Argon2id 46MiB/t1 | 47.3 ± 0.1 | 87.9 ± 0.4 | 148.8 ± 0.2 | 204.8 ± 0.3 | 217.9 ± 9.9 | 218.3 ± 8.8 | 221.8 ± 0.5 | 222.2 ± 0.2 |
| Argon2id 64MiB/t2 | 16.2 ± 0.1 | 30.2 ± 0.1 | 53.8 ± 0.2 | 75.3 ± 0.1 | 82.4 ± 0.2 | 82.3 ± 0.3 | 82.3 ± 0.3 | 82.4 ± 0.3 |

## Table 3 – p99 latency in ms (mean ± sd, n=5) by concurrency (E1)

| Configuration | c=1 | c=2 | c=4 | c=8 | c=16 | c=32 | c=64 | c=128 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SHA-256 control | 0.0 ± 0.0 | 0.1 ± 0.0 | 0.1 ± 0.0 | 0.2 ± 0.0 | 0.4 ± 0.0 | 0.8 ± 0.0 | 1.6 ± 0.0 | 3.2 ± 0.0 |
| bcrypt c=4 | 0.9 ± 0.0 | 0.9 ± 0.0 | 0.9 ± 0.0 | 1.3 ± 0.0 | 2.3 ± 0.1 | 6.9 ± 0.1 | 16.0 ± 0.3 | 34.8 ± 0.6 |
| bcrypt c=10 | 40.8 ± 0.4 | 40.8 ± 0.2 | 41.7 ± 0.1 | 42.9 ± 0.6 | 170.9 ± 6.0 | 459.0 ± 18.8 | 1,023 ± 83.7 | 1,998 ± 75.7 |
| bcrypt c=12 | 160.8 ± 1.3 | 159.9 ± 0.4 | 159.7 ± 0.4 | 171.2 ± 1.5 | 681.0 ± 114.7 | 1,906 ± 136.7 | 3,889 ± 439.0 | 7,489 ± 1,685 |
| Argon2id 4MiB/t1 | 2.2 ± 0.1 | 2.7 ± 0.1 | 2.8 ± 0.0 | 3.4 ± 0.1 | 12.7 ± 1.3 | 34.3 ± 0.1 | 76.2 ± 1.3 | 161.4 ± 7.7 |
| Argon2id 7MiB/t5 | 16.6 ± 0.9 | 17.3 ± 0.5 | 22.7 ± 0.5 | 29.1 ± 0.7 | 116.8 ± 10.1 | 315.5 ± 1.5 | 703.7 ± 46.2 | 1,491 ± 55.1 |
| Argon2id 19MiB/t2 | 19.0 ± 2.6 | 22.9 ± 2.5 | 27.7 ± 0.6 | 36.7 ± 0.5 | 158.0 ± 1.6 | 418.1 ± 21.9 | 913.4 ± 64.4 | 1,844 ± 152.5 |
| Argon2id 46MiB/t1 | 22.1 ± 0.3 | 24.6 ± 0.8 | 32.5 ± 0.2 | 44.0 ± 0.2 | 194.2 ± 2.3 | 507.8 ± 51.1 | 1,111 ± 121.2 | 2,302 ± 161.7 |
| Argon2id 64MiB/t2 | 63.0 ± 0.3 | 69.7 ± 2.5 | 81.4 ± 1.1 | 117.2 ± 1.4 | 497.5 ± 3.4 | 1,325 ± 126.3 | 3,050 ± 220.5 | 6,974 ± 1,363 |

## Table 4 – Peak server RSS in MiB (mean, n=5) by concurrency (E1)

| Configuration | idle | c=1 | c=2 | c=4 | c=8 | c=16 | c=32 | c=64 | c=128 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SHA-256 control | 21.0 | 44.9 | 45.2 | 45.2 | 45.0 | 45.2 | 45.3 | 45.2 | 45.2 |
| bcrypt c=4 | 21.4 | 33.8 | 35.9 | 40.2 | 43.2 | 43.4 | 43.5 | 43.5 | 44.0 |
| bcrypt c=10 | 21.3 | 27.6 | 28.6 | 28.8 | 29.0 | 29.2 | 29.8 | 30.0 | 30.4 |
| bcrypt c=12 | 21.3 | 24.8 | 24.9 | 27.7 | 28.6 | 28.6 | 28.7 | 28.9 | 29.2 |
| Argon2id 4MiB/t1 | 23.2 | 39.9 | 51.1 | 63.1 | 85.1 | 88.4 | 91.4 | 89.1 | 90.9 |
| Argon2id 7MiB/t5 | 22.1 | 42.8 | 55.3 | 72.9 | 99.9 | 102.2 | 106.3 | 101.8 | 106.5 |
| Argon2id 19MiB/t2 | 23.2 | 133.3 | 177.7 | 205.1 | 216.4 | 220.9 | 221.0 | 227.6 | 228.3 |
| Argon2id 46MiB/t1 | 21.6 | 74.8 | 121.1 | 213.2 | 397.4 | 489.6 | 541.5 | 490.3 | 490.8 |
| Argon2id 64MiB/t2 | 21.7 | 91.4 | 155.8 | 284.8 | 559.2 | 688.8 | 669.1 | 701.7 | 669.6 |

## Table 5 – CPU time per login (core-ms), uncontended vs saturated (E1)

core-ms/login = server CPU cores used ÷ logins/s × 1000. A rise under load means each hash got slower while sharing the machine (SMT siblings, shared cache, memory bandwidth).

| Configuration | c=1 | c=128 | Ratio | Speed-up c=1→c=128 (10 logical CPUs) |
|---|---:|---:|---:|---:|
| SHA-256 control | 0.01 | 0.01 | 0.77× | 3.05× |
| bcrypt c=4 | 0.73 | 0.71 | 0.98× | 10.61× |
| bcrypt c=10 | 39.81 | 42.54 | 1.07× | 9.38× |
| bcrypt c=12 | 157.72 | 169.87 | 1.08× | 9.28× |
| Argon2id 4MiB/t1 | 1.83 | 3.19 | 1.74× | 5.82× |
| Argon2id 7MiB/t5 | 14.94 | 29.29 | 1.96× | 5.11× |
| Argon2id 19MiB/t2 | 17.03 | 37.12 | 2.18× | 4.58× |
| Argon2id 46MiB/t1 | 20.91 | 44.79 | 2.14× | 4.69× |
| Argon2id 64MiB/t2 | 61.42 | 120.66 | 1.96× | 5.08× |

## Table 6 – Memory model check (E1)

Model: peak RSS ≈ idle RSS + k × m, where m = Argon2id memoryCost and k = number of hashes in memory at once. k is estimated from the data as (peak − idle)/m.

| Configuration | m (MiB) | k̂ c=1 | k̂ c=2 | k̂ c=4 | k̂ c=8 | k̂ c=16 | k̂ c=32 | k̂ c=64 | k̂ c=128 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Argon2id 4MiB/t1 | 4.0 | 4.2 | 7.0 | 10.1 | 15.6 | 16.2 | 17.2 | 16.6 | 16.9 |
| Argon2id 7MiB/t5 | 7.0 | 3.0 | 4.8 | 7.3 | 11.0 | 11.5 | 12.1 | 11.5 | 12.1 |
| Argon2id 19MiB/t2 | 19.0 | 5.8 | 8.1 | 9.6 | 10.2 | 10.4 | 10.4 | 10.8 | 10.8 |
| Argon2id 46MiB/t1 | 46.0 | 1.2 | 2.2 | 4.2 | 8.2 | 10.2 | 11.3 | 10.2 | 10.2 |
| Argon2id 64MiB/t2 | 64.0 | 1.1 | 2.1 | 4.1 | 8.4 | 10.4 | 10.1 | 10.6 | 10.1 |

## Measurement checks (E1)

- Runs: 360; failed/non-200 responses in all runs: 0.
- Little's law (L = λW): worst relative deviation of logins/s × mean latency from the configured concurrency: 17.9%.
- p99 from load generator vs recomputed from raw per-request files: max difference 0.000 ms.
- Largest run-to-run coefficient of variation of logins/s: 8.0% (Argon2id 19MiB/t2, c=1).
- Highest mean load-generator CPU use: 1.75 cores (SHA-256 control, c=128) out of the 2 logical CPUs reserved for it.

## Table 7 – Core scaling at c=32 (E2): logins/s and speed-up over one core

Server pinned to 1–5 physical cores (one hardware thread each), then 5 cores with both SMT threads. Efficiency = speed-up ÷ cores. SMT gain = (5 cores + SMT) ÷ (5 cores).

| Configuration | 1 cores | 2 cores | 3 cores | 4 cores | 5 cores | 5+SMT cores | Speed-up @5 | Efficiency @5 | SMT gain |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bcrypt c=10 | 25.2 ± 0.0 | 50.7 ± 0.1 | 76.1 ± 0.1 | 101.4 ± 0.1 | 126.2 ± 0.0 | 234.1 ± 0.5 | 5.00× | 100% | 1.85× |
| Argon2id 7MiB/t5 | 67.3 ± 0.1 | 135.1 ± 0.1 | 198.6 ± 0.4 | 256.5 ± 0.7 | 303.9 ± 1.2 | 345.1 ± 0.1 | 4.51× | 90% | 1.14× |
| Argon2id 19MiB/t2 | 54.2 ± 0.1 | 109.1 ± 1.1 | 153.5 ± 0.5 | 191.5 ± 0.3 | 226.2 ± 0.8 | 268.8 ± 0.2 | 4.18× | 84% | 1.19× |
| Argon2id 46MiB/t1 | 44.8 ± 0.5 | 88.2 ± 0.1 | 124.1 ± 0.2 | 152.4 ± 3.9 | 182.8 ± 0.3 | 221.6 ± 0.5 | 4.08× | 82% | 1.21× |
| Argon2id 64MiB/t2 | 15.4 ± 0.1 | 30.3 ± 0.1 | 43.0 ± 0.1 | 54.8 ± 0.1 | 65.1 ± 0.2 | 82.3 ± 0.1 | 4.22× | 84% | 1.27× |

## Table 8 – Behaviour under a cgroup memory limit at c=64 (E3)

MemoryMax set on the server's cgroup with swap disabled (MemorySwapMax=0). Values: mean logins/s · mean p99 · total failed requests · runs where the server died (of n).

| Configuration | limit none | limit 512M | limit 256M | limit 128M |
|---|---|---|---|---|
| bcrypt c=10 | 234.0/s · 1,016 ms · 0 err · 0/3 died | 233.5/s · 1,037 ms · 0 err · 0/3 died | 233.9/s · 1,120 ms · 0 err · 0/3 died | 233.2/s · 1,028 ms · 0 err · 0/3 died |
| Argon2id 19MiB/t2 | 249.6/s · 994.8 ms · 0 err · 0/3 died | 250.3/s · 985.2 ms · 0 err · 0/3 died | 251.8/s · 912.2 ms · 0 err · 0/3 died | 0.0/s · – ms · 1783700 err · 3/3 died |
| Argon2id 64MiB/t2 | 79.8/s · 3,188 ms · 0 err · 0/3 died | 0.0/s · – ms · 1753774 err · 3/3 died | 0.0/s · – ms · 1816609 err · 3/3 died | 0.0/s · – ms · 1819084 err · 3/3 died |

## Table 9 – OOM threshold, Argon2id 64 MiB/t=2 under MemoryMax=512M (E4)

Pre-registered prediction: idle (~21 MiB) + c × 64 MiB > 512 MiB ⇒ the server is killed for c ≥ 8.

| Concurrency c | Model peak (MiB) | Runs killed | Peak RSS of surviving runs (MiB) | Logins/s (survivors) |
|---:|---:|---:|---|---:|
| 4 | 278 | 0/3 | 410.5, 283.6, 459.2 | 53.5 |
| 6 | 406 | 1/3 | 412.1, 412.0 | 66.7 |
| 7 | 470 | 0/3 | 476.2, 476.6, 476.5 | 70.1 |
| 8 | 534 | 3/3 | – | – |
| 9 | 598 | 3/3 | – | – |
| 10 | 662 | 3/3 | – | – |
| 12 | 790 | 3/3 | – | – |

