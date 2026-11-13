"""
Study behind the README and the app's "Study" tab.

1. Benchmarks - CP-SAT and six dispatching rules on classic instances with
   known optimal makespans (validates the solver).
2. Rules vs optimal - 30 simulated machine-shop order books (10 jobs x 6
   machines, due dates by the TWK rule): weighted tardiness and makespan.
3. Disruptions - on each order book one machine breaks down for 60-120 min at a
   random moment; the plan is repaired by right-shift, full re-optimisation and
   stable re-optimisation. Paired comparison over the same 30 scenarios.
4. Stability trade-off - weighted tardiness vs schedule changes for a range of
   move penalties.

Run:  python experiments.py           (about 10-15 min on 2 cores)
      python experiments.py --quick   (smoke test)
"""
from __future__ import annotations

import argparse
import math
import os
import random

import numpy as np
import pandas as pd

import benchmarks
from jobshop import check, kpis, make_shop
from reschedule import METHODS, Event, repair
from rules import RULES, all_rules
from solver import solve

T95 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228, 2.201, 2.179, 2.160, 2.145,
       2.131, 2.120, 2.110, 2.101, 2.093, 2.086, 2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045]


def mean_ci(x) -> tuple[float, float]:
    x = np.asarray(list(x), float)
    if len(x) < 2:
        return float(x.mean()), float("nan")
    t = T95[len(x) - 2] if len(x) - 2 < len(T95) else 1.96
    return float(x.mean()), t * float(x.std(ddof=1)) / math.sqrt(len(x))


def gap(v: float, best: float) -> float:
    return 0.0 if best == 0 and v == 0 else (v - best) / best * 100 if best else float("inf")


def bench(names, time_limit, workers) -> pd.DataFrame:
    rows = []
    for n in names:
        inst = benchmarks.load(n)
        res = solve(inst, "makespan", time_limit, workers=workers)
        assert not check(inst, res.schedule), n
        row = {"instance": n, "size": f"{inst.n_jobs}x{inst.n_machines}", "optimum": benchmarks.OPTIMUM[n],
               "cpsat": res.objective, "cpsat_status": res.status, "cpsat_seconds": round(res.seconds, 2)}
        for r, s in all_rules(inst).items():
            row[r] = kpis(inst, s)["makespan"]
        rows.append(row)
        print(f"  {n}: CP-SAT {res.objective:.0f} ({res.status}, {res.seconds:.1f}s) vs optimum {benchmarks.OPTIMUM[n]}")
    return pd.DataFrame(rows)


def rules_vs_optimal(seeds, time_limit, workers) -> pd.DataFrame:
    rows = []
    for sd in seeds:
        inst = make_shop(sd)
        for obj in ("weighted_tardiness", "makespan"):
            res = solve(inst, obj, time_limit, workers=workers)
            assert not check(inst, res.schedule)
            rows.append({"seed": sd, "objective": obj, "method": "CP-SAT", "value": res.objective,
                         "status": res.status, "seconds": res.seconds})
            for r, s in all_rules(inst).items():
                rows.append({"seed": sd, "objective": obj, "method": r, "value": objective_of(inst, s, obj),
                             "status": "RULE", "seconds": 0.0})
    return pd.DataFrame(rows)


def objective_of(inst, s, obj):
    k = kpis(inst, s)
    return k["makespan"] if obj == "makespan" else k["weighted_tardiness"]


def scenario(sd: int):
    """Same breakdown scenario for every method (common random numbers)."""
    inst = make_shop(sd)
    base = solve(inst, "weighted_tardiness", 10, workers=2)
    rng = random.Random(10_000 + sd)
    cmax = kpis(inst, base.schedule)["makespan"]
    ev = Event("breakdown", time=int(rng.uniform(0.2, 0.5) * cmax), machine=rng.randrange(inst.n_machines),
               duration=rng.choice([60, 90, 120]))
    return inst, base.schedule, ev


def disruptions(seeds, time_limit, stability=0.2) -> pd.DataFrame:
    rows = []
    for sd in seeds:
        inst, base, ev = scenario(sd)
        wt0 = kpis(inst, base)["weighted_tardiness"]
        for mth in METHODS:
            r = repair(inst, base, ev, mth, "weighted_tardiness", stability=stability, time_limit=time_limit)
            assert not r["violations"], (sd, mth, r["violations"])
            rows.append({"seed": sd, "method": mth, "machine": inst.machine_name(ev.machine), "t0": ev.time,
                         "duration": ev.duration, "wt_before": wt0, "weighted_tardiness": r["kpis"]["weighted_tardiness"],
                         "late_jobs": r["kpis"]["late_jobs"], "makespan": r["kpis"]["makespan"],
                         "deviation_min": r["deviation_min"], "moved_ops": r["moved_ops"], "status": r["status"]})
    return pd.DataFrame(rows)


def stability_sweep(seeds, weights, time_limit) -> pd.DataFrame:
    rows = []
    for sd in seeds:
        inst, base, ev = scenario(sd)
        for w in weights:
            r = repair(inst, base, ev, "stable" if w > 0 else "reoptimize", "weighted_tardiness",
                       stability=w, time_limit=time_limit)
            rows.append({"seed": sd, "stability": w, "weighted_tardiness": r["kpis"]["weighted_tardiness"],
                         "deviation_min": r["deviation_min"], "moved_ops": r["moved_ops"]})
        rs = repair(inst, base, ev, "right_shift")
        rows.append({"seed": sd, "stability": float("inf"), "weighted_tardiness": rs["kpis"]["weighted_tardiness"],
                     "deviation_min": rs["deviation_min"], "moved_ops": rs["moved_ops"]})
    return pd.DataFrame(rows)


def summarize(df, by, cols):
    out = []
    for keys, g in df.groupby(by, sort=False):
        row = dict(zip([by] if isinstance(by, str) else by, keys if isinstance(keys, tuple) else (keys,)))
        row["n"] = len(g)
        for c in cols:
            row[c], row[c + "_ci"] = mean_ci(g[c])
        out.append(row)
    return pd.DataFrame(out)


def main(quick=False, out="results"):
    os.makedirs(out, exist_ok=True)
    workers = 2
    names = ["ft06", "la01"] if quick else list(benchmarks.OPTIMUM)
    seeds = list(range(1, 4 if quick else 31))
    tl = 3 if quick else 10

    print("1) benchmarks")
    bench(names, 10 if quick else 60, workers).to_csv(f"{out}/benchmarks.csv", index=False)

    print("2) rules vs optimal")
    rv = rules_vs_optimal(seeds, tl, workers)
    rv.to_csv(f"{out}/rules_vs_optimal_runs.csv", index=False)
    best = rv[rv.method == "CP-SAT"].set_index(["seed", "objective"])["value"]
    rv["gap_vs_cpsat"] = [v - best[(s, o)] for s, o, v in zip(rv.seed, rv.objective, rv.value)]
    summ = rv.groupby(["objective", "method"], sort=False).agg(
        mean=("value", "mean"), mean_gap=("gap_vs_cpsat", "mean"),
        optimal_share=("status", lambda s: (s == "OPTIMAL").mean())).reset_index()
    summ.to_csv(f"{out}/rules_vs_optimal.csv", index=False)
    print(summ.round(1).to_string(index=False))

    print("3) disruptions")
    d = disruptions(seeds, 3 if quick else 5)
    d.to_csv(f"{out}/disruption_runs.csv", index=False)
    ds = summarize(d, "method", ["weighted_tardiness", "late_jobs", "makespan", "deviation_min", "moved_ops"])
    ds.to_csv(f"{out}/disruptions.csv", index=False)
    print(ds.round(1).to_string(index=False))
    piv = d.pivot(index="seed", columns="method", values="weighted_tardiness")
    dev = d.pivot(index="seed", columns="method", values="deviation_min")
    pairs = []
    for a, b in (("right_shift", "reoptimize"), ("right_shift", "stable"), ("reoptimize", "stable")):
        m1, h1 = mean_ci(piv[b] - piv[a])
        m2, h2 = mean_ci(dev[b] - dev[a])
        pairs.append({"from": a, "to": b, "wt_diff": m1, "wt_ci": h1, "dev_diff": m2, "dev_ci": h2})
    pd.DataFrame(pairs).to_csv(f"{out}/disruption_paired.csv", index=False)

    print("4) stability sweep")
    sw = stability_sweep(seeds[: 3 if quick else 20], [0, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0], 3 if quick else 5)
    sw.to_csv(f"{out}/stability_runs.csv", index=False)
    summarize(sw, "stability", ["weighted_tardiness", "deviation_min", "moved_ops"]).to_csv(f"{out}/stability.csv", index=False)
    print("done")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    main(ap.parse_args().quick)
