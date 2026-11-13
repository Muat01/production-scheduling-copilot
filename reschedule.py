"""
Reacting to disruptions: machine breakdowns, rush orders and new jobs.

Three classic repair strategies are compared (see Vieira, Herrmann & Lin, 2003):
* right_shift  - keep every machine's sequence, push operations later just
                 enough to absorb the disruption (fast, very stable, often poor);
* reoptimize   - solve again from the reschedule time with CP-SAT (best objective,
                 may reshuffle much of the plan);
* stable       - re-optimise with a penalty on moving operations away from the
                 current plan (trade-off between performance and nervousness).

Operations that started before the reschedule time are frozen, except one that
is running on a machine that breaks down at that moment: it is interrupted and
restarts after the repair (non-resumable).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from jobshop import Downtime, Instance, Schedule, check, kpis
from rules import _fit
from solver import solve

METHODS = {
    "right_shift": "Right-shift repair (keep sequences)",
    "reoptimize": "Full re-optimisation (CP-SAT)",
    "stable": "Stable re-optimisation (CP-SAT + move penalty)",
}


@dataclass
class Event:
    kind: str                       # "breakdown" | "rush" | "new_job" | "due_change"
    time: int                       # reschedule moment (minutes)
    machine: Optional[int] = None
    duration: int = 0
    job: Optional[int] = None
    weight: float = 0.0
    due: Optional[int] = None
    route: Tuple[Tuple[int, int], ...] = ()
    name: str = ""


def apply_event(inst: Instance, ev: Event) -> Instance:
    """Return the instance as it looks after the event."""
    if ev.kind == "breakdown":
        return inst.with_(downtimes=inst.downtimes + (Downtime(ev.machine, ev.time, ev.time + ev.duration),))
    if ev.kind in ("rush", "due_change"):
        w = list(inst.weight or [1.0] * inst.n_jobs)
        d = list(inst.due or [inst.horizon()] * inst.n_jobs)
        if ev.weight:
            w[ev.job] = ev.weight
        if ev.due is not None:
            d[ev.job] = ev.due
        return inst.with_(weight=tuple(w), due=tuple(d))
    if ev.kind == "new_job":
        n = inst.n_jobs
        name = ev.name or f"J{n + 1}"
        work = sum(p for _, p in ev.route)
        return inst.with_(
            routes=inst.routes + (tuple(ev.route),),
            due=(inst.due or tuple([inst.horizon()] * n)) + ((ev.due if ev.due is not None else ev.time + 2 * work),),
            weight=(inst.weight or tuple([1.0] * n)) + ((ev.weight or 1.0),),
            release=(inst.release or tuple([0] * n)) + (ev.time,),
            job_names=(inst.job_names or tuple(f"J{j + 1}" for j in range(n))) + (name,),
        )
    raise ValueError(f"unknown event kind {ev.kind}")


def frozen_ops(inst: Instance, sched: Schedule, t0: int, broken: Optional[int] = None) -> Dict[Tuple[int, int], int]:
    """Operations already started at t0 keep their start time (except one interrupted by a breakdown)."""
    fz = {}
    for (j, k), s in sched.items():
        if j >= inst.n_jobs or s >= t0:
            continue
        m, p = inst.routes[j][k]
        if broken is not None and m == broken and s + p > t0:
            continue                                   # interrupted -> restarts after repair
        fz[(j, k)] = s
    # an op can only stay frozen if its predecessor is frozen too
    changed = True
    while changed:
        changed = False
        for (j, k) in list(fz):
            if k > 0 and (j, k - 1) not in fz:
                del fz[(j, k)]
                changed = True
    return fz


def right_shift(inst: Instance, sched: Schedule, t0: int, frozen: Dict) -> Schedule:
    """Keep each machine's order from the old plan; move operations later only as needed."""
    order = sorted(((s, j, k) for (j, k), s in sched.items() if j < inst.n_jobs), key=lambda x: (x[0], x[1], x[2]))
    # operations that are new (not in the old plan) go at the end, in route order;
    # they have no old start time, so None means "as early as possible"
    for j in range(inst.n_jobs):
        for k in range(len(inst.routes[j])):
            if (j, k) not in sched:
                order.append((None, j, k))
    new: Schedule = {}
    mach_free = [0] * inst.n_machines
    job_free = [inst.release_of(j) for j in range(inst.n_jobs)]
    for s_old, j, k in order:
        m, p = inst.routes[j][k]
        if (j, k) in frozen:
            s = frozen[(j, k)]
        else:
            s = max(s_old if s_old is not None else 0, job_free[j], mach_free[m], t0)
            s = _fit(inst, m, s, p)
        new[(j, k)] = s
        job_free[j] = s + p
        mach_free[m] = max(mach_free[m], s + p)
    return new


def deviation(old: Schedule, new: Schedule, frozen: Dict) -> Tuple[int, int]:
    """(sum of |start shift| in minutes, number of operations moved) over non-frozen ops."""
    keys = [k for k in old if k in new and k not in frozen]
    shifts = [abs(new[k] - old[k]) for k in keys]
    return sum(shifts), sum(s > 0 for s in shifts)


def repair(inst: Instance, sched: Schedule, ev: Event, method: str = "stable", objective: str = "weighted_tardiness",
           stability: float = 0.2, time_limit: float = 5.0) -> dict:
    """Apply the event and build a new plan with the chosen method. Returns plan + diagnostics."""
    if method not in METHODS:
        raise ValueError(f"method must be one of {list(METHODS)}")
    new_inst = apply_event(inst, ev)
    broken = ev.machine if ev.kind == "breakdown" else None
    fz = frozen_ops(new_inst, sched, ev.time, broken)
    rs = right_shift(new_inst, sched, ev.time, fz)
    if method == "right_shift":
        plan, status = rs, "HEURISTIC"
    else:
        res = solve(new_inst, objective, time_limit, frozen=fz, not_before=ev.time,
                    baseline=sched if method == "stable" else None,
                    stability=stability if method == "stable" else 0.0, hint=rs)
        plan, status = (res.schedule, res.status) if res.schedule else (rs, "FALLBACK_RIGHT_SHIFT")
    errs = check(new_inst, plan)
    dev, moved = deviation(sched, plan, fz)
    return {"instance": new_inst, "schedule": plan, "status": status, "violations": errs,
            "kpis": kpis(new_inst, plan), "deviation_min": dev, "moved_ops": moved, "frozen": len(fz)}
