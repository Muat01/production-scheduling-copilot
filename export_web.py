"""
Export everything the static HTML control room needs (web/data.js).

The browser cannot run CP-SAT, so optimal plans and CP-SAT repairs are computed
here and embedded. Dispatching rules, right-shift repair, the feasibility checker
and the command parser are re-implemented in JavaScript and run live.

Precomputed scenarios (order books 1-5):
  breakdowns  : every machine x start {60, 120, 180} x duration {60, 120}
  rush orders : every job, weight 5, at t = 60
each repaired with full re-optimisation and stable re-optimisation (w = 0.2).

Run:  python export_web.py        (about 15-25 min on 2 cores)
"""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from jobshop import make_shop
from reschedule import Event, repair
from rules import RULES, all_rules
from solver import solve

N_BOOKS, N_LIVE = 30, 5
BD_T, BD_D = [60, 120, 180], [60, 120]
OUT = os.path.join(os.path.dirname(__file__), "web")


def inst_json(inst):
    return {"routes": [[list(op) for op in r] for r in inst.routes], "due": list(inst.due), "w": list(inst.weight),
            "rel": list(inst.release), "jobs": list(inst.job_names), "mach": list(inst.machine_names)}


def starts(inst, sched):
    return [[sched[(j, k)] for k in range(len(r))] for j, r in enumerate(inst.routes)]


def book(seed):
    inst = make_shop(seed)
    res = solve(inst, "weighted_tardiness", 10, workers=1, seed=0)
    out = {"seed": seed, "inst": inst_json(inst), "opt": starts(inst, res.schedule), "status": res.status}
    if seed <= N_LIVE:
        sc = {}
        evs = [(f"b:{m}:{t0}:{d}", Event("breakdown", t0, machine=m, duration=d)) for m in range(inst.n_machines) for t0 in BD_T for d in BD_D]
        evs += [(f"r:{j}", Event("rush", 60, job=j, weight=5)) for j in range(inst.n_jobs)]
        for key, ev in evs:
            sc[key] = {}
            for mth in ("reoptimize", "stable"):
                r = repair(inst, res.schedule, ev, mth, "weighted_tardiness", stability=0.2, time_limit=4)
                assert not r["violations"], (seed, key, mth, r["violations"])
                sc[key][mth] = {"s": starts(r["instance"], r["schedule"]), "st": r["status"]}
        out["sc"] = sc
    print(f"book {seed} done", flush=True)
    return out


def study():
    R = os.path.join(os.path.dirname(__file__), "results")
    rd = lambda n: pd.read_csv(os.path.join(R, n + ".csv"))
    return {"bench": rd("benchmarks").to_dict("records"),
            "rv": rd("rules_vs_optimal").to_dict("records"),
            "rvruns": rd("rules_vs_optimal_runs")[["seed", "objective", "method", "value"]].values.tolist(),
            "dis": rd("disruptions").to_dict("records"),
            "disruns": rd("disruption_runs")[["seed", "method", "machine", "t0", "duration", "wt_before", "weighted_tardiness", "deviation_min", "moved_ops"]].values.tolist(),
            "pair": rd("disruption_paired").to_dict("records"),
            "stab": rd("stability").replace([float("inf")], 1e9).to_dict("records")}


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    seeds = list(range(1, N_BOOKS + 1)) if "--quick" not in sys.argv else [1, 2]
    with ProcessPoolExecutor(2) as ex:
        books = list(ex.map(book, seeds))
    data = {"books": books, "study": study(), "rules": list(RULES), "grid": {"t": BD_T, "d": BD_D}}
    # reference values from Python for JS parity tests: every rule on every book
    data["ref"] = {}
    for b in books:
        inst = make_shop(b["seed"])
        data["ref"][b["seed"]] = {r: starts(inst, s) for r, s in all_rules(inst).items()}
    s = json.dumps(data, separators=(",", ":"))
    open(os.path.join(OUT, "data.js"), "w").write("const D=" + s + ";")
    print("data.js", round(len(s) / 1024), "KB")
