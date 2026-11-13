"""
Priority dispatching rules inside the Giffler & Thompson (1960) active-schedule
generator: the classic way shop-floor systems build a schedule in milliseconds.

At each step the generator finds the machine m* where an operation could
finish earliest (c*). Every operation waiting for m* that could start before
c* is in the conflict set; the dispatching rule picks one of them.
Machine downtime windows are respected: an operation that would overlap one
is pushed to the end of the window.
"""
from __future__ import annotations

from typing import Callable, Dict, List

from jobshop import Instance, Schedule

RULES = {
    "FIFO": "First in, first out: the operation that became ready first",
    "SPT": "Shortest processing time of this operation",
    "EDD": "Earliest due date of the job",
    "MWKR": "Most work remaining in the job",
    "CR": "Critical ratio: (due date - now) / remaining work, smallest first",
    "WSPT": "Weighted shortest processing time: p / weight, smallest first",
}


def _fit(inst: Instance, m: int, start: int, p: int) -> int:
    """Earliest start >= start such that [s, s+p) does not overlap downtime on m."""
    moved = True
    while moved:
        moved = False
        for d in inst.downtimes:
            if d.machine == m and start < d.end and start + p > d.start:
                start, moved = d.end, True
    return start


def dispatch(inst: Instance, rule: str = "SPT") -> Schedule:
    if rule not in RULES:
        raise ValueError(f"Unknown rule {rule}. Use one of {list(RULES)}")
    n = inst.n_jobs
    nxt = [0] * n                                   # next operation index per job
    job_ready = [inst.release_of(j) for j in range(n)]
    mach_ready = [0] * inst.n_machines
    remaining = [sum(p for _, p in r) for r in inst.routes]
    sched: Schedule = {}
    total = sum(len(r) for r in inst.routes)

    def key(j: int, est: int, now: int) -> tuple:
        m, p = inst.routes[j][nxt[j]]
        due = inst.due_of(j)
        due = due if due is not None else 10 ** 9
        if rule == "FIFO":
            v = job_ready[j]
        elif rule == "SPT":
            v = p
        elif rule == "EDD":
            v = due
        elif rule == "MWKR":
            v = -remaining[j]
        elif rule == "CR":
            v = (due - now) / max(remaining[j], 1)
        else:  # WSPT
            v = p / inst.weight_of(j)
        return (v, j)                                 # job index breaks ties deterministically

    while len(sched) < total:
        cand = []
        for j in range(n):
            if nxt[j] < len(inst.routes[j]):
                m, p = inst.routes[j][nxt[j]]
                est = _fit(inst, m, max(job_ready[j], mach_ready[m]), p)
                cand.append((est + p, est, j, m))
        c_star, _, _, m_star = min(cand)
        conflict = [(est, j) for (c, est, j, m) in cand if m == m_star and est < c_star]
        now = min(est for est, _ in conflict)
        _, j = min((key(j, est, now), j) for est, j in conflict)
        est = next(e for e, jj in conflict if jj == j)
        m, p = inst.routes[j][nxt[j]]
        sched[(j, nxt[j])] = est
        job_ready[j] = mach_ready[m] = est + p
        remaining[j] -= p
        nxt[j] += 1
    return sched


def all_rules(inst: Instance) -> Dict[str, Schedule]:
    return {r: dispatch(inst, r) for r in RULES}
