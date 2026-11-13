"""
Job-shop data model, schedule checker and KPIs.

A job is an ordered list of operations; each operation needs one machine for a
fixed processing time. A machine does one operation at a time, an operation is
never interrupted, and a job's operations follow their route. Time unit: minutes.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Op:
    job: int
    idx: int          # position in the job's route
    machine: int
    p: int            # processing time


@dataclass(frozen=True)
class Downtime:
    machine: int
    start: int
    end: int


@dataclass(frozen=True)
class Instance:
    name: str
    routes: Tuple[Tuple[Tuple[int, int], ...], ...]   # per job: ((machine, p), ...)
    n_machines: int
    due: Tuple[int, ...] = ()                         # due date per job (empty = none)
    weight: Tuple[float, ...] = ()                    # tardiness weight per job
    release: Tuple[int, ...] = ()                     # earliest start per job
    job_names: Tuple[str, ...] = ()
    machine_names: Tuple[str, ...] = ()
    downtimes: Tuple[Downtime, ...] = ()

    @property
    def n_jobs(self) -> int:
        return len(self.routes)

    def ops(self) -> List[Op]:
        return [Op(j, k, m, p) for j, r in enumerate(self.routes) for k, (m, p) in enumerate(r)]

    def job_name(self, j: int) -> str:
        return self.job_names[j] if self.job_names else f"J{j + 1}"

    def machine_name(self, m: int) -> str:
        return self.machine_names[m] if self.machine_names else f"M{m + 1}"

    def due_of(self, j: int) -> Optional[int]:
        return self.due[j] if self.due else None

    def weight_of(self, j: int) -> float:
        return self.weight[j] if self.weight else 1.0

    def release_of(self, j: int) -> int:
        return self.release[j] if self.release else 0

    def horizon(self) -> int:
        return (sum(p for r in self.routes for _, p in r) + max(self.release or (0,))
                + sum(d.end - d.start for d in self.downtimes))

    def with_(self, **kw) -> "Instance":
        return replace(self, **kw)


# a schedule maps (job, op index) -> start time
Schedule = Dict[Tuple[int, int], int]


# ─── Parsing & generation ───────────────────────────────────────────────────
def parse_standard(text: str, name: str = "instance") -> Instance:
    """Parse the standard OR-Library / JSPLIB format ('n m' then per job 'm p m p ...')."""
    rows = [ln.split() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    n, m = int(rows[0][0]), int(rows[0][1])
    routes = []
    for r in rows[1:1 + n]:
        vals = list(map(int, r))
        routes.append(tuple((vals[i], vals[i + 1]) for i in range(0, len(vals), 2)))
    return Instance(name, tuple(routes), m)


FT06 = """6 6
2 1 0 3 1 6 3 7 5 3 4 6
1 8 2 5 4 10 5 10 0 10 3 4
2 5 3 4 5 8 0 9 1 1 4 7
1 5 0 5 2 5 3 3 4 8 5 9
2 9 1 3 4 5 5 4 0 3 3 1
1 3 3 3 5 9 0 10 4 4 2 1
"""  # Fisher & Thompson (1963) 6x6 instance, optimal makespan 55


SHOP_MACHINES = ("Saw", "Lathe", "Mill", "Drill", "Grinder", "Inspect")


def make_shop(seed: int = 1, n_jobs: int = 10, n_machines: int = 6, p_range=(8, 45),
              tightness=(1.3, 2.2), flow_bias: float = 0.6) -> Instance:
    """Simulated machine-shop order book.

    Routes are random permutations biased toward a typical flow (saw first,
    inspection last); due dates follow the total-work-content (TWK) rule
    d_j = r_j + k_j * sum(p_j) with k_j ~ U(tightness); weights 1, 2 or 3.
    All values are illustrative.
    """
    rng = random.Random(seed)
    routes, due, weight, release = [], [], [], []
    for _ in range(n_jobs):
        ms = list(range(n_machines))
        if rng.random() < flow_bias:          # typical flow: saw ... inspect
            mid = ms[1:-1]
            rng.shuffle(mid)
            ms = [0] + mid + [n_machines - 1]
        else:
            rng.shuffle(ms)
        k = rng.randint(max(3, n_machines - 2), n_machines)     # some jobs skip machines
        keep = sorted(rng.sample(range(n_machines), k), key=ms.index)
        route = tuple((ms[i], rng.randint(*p_range)) for i in sorted(ms.index(m) for m in keep))
        r = rng.choice([0, 0, 0, 30, 60])
        work = sum(p for _, p in route)
        routes.append(route)
        release.append(r)
        due.append(int(r + rng.uniform(*tightness) * work))
        weight.append(rng.choice([1, 1, 2, 3]))
    names = SHOP_MACHINES[:n_machines] if n_machines <= len(SHOP_MACHINES) else ()
    return Instance(f"shop-{seed}", tuple(routes), n_machines, tuple(due), tuple(weight),
                    tuple(release), tuple(f"J{j + 1}" for j in range(n_jobs)), names)


# ─── Checking ───────────────────────────────────────────────────────────────
def check(inst: Instance, sched: Schedule, frozen_before: Optional[int] = None) -> List[str]:
    """Return a list of violations (empty = feasible). Independent of any solver."""
    errs = []
    for j, route in enumerate(inst.routes):
        for k, (m, p) in enumerate(route):
            if (j, k) not in sched:
                errs.append(f"{inst.job_name(j)} op {k + 1} not scheduled")
                continue
            s = sched[(j, k)]
            if k == 0 and s < inst.release_of(j):
                errs.append(f"{inst.job_name(j)} starts before its release time")
            if k > 0 and (j, k - 1) in sched and s < sched[(j, k - 1)] + route[k - 1][1]:
                errs.append(f"{inst.job_name(j)} op {k + 1} starts before op {k} ends")
    by_m: Dict[int, list] = {}
    for (j, k), s in sched.items():
        m, p = inst.routes[j][k]
        by_m.setdefault(m, []).append((s, s + p, j, k))
    for m, lst in by_m.items():
        lst.sort()
        for a, b in zip(lst, lst[1:]):
            if b[0] < a[1]:
                errs.append(f"{inst.machine_name(m)}: {inst.job_name(a[2])} and {inst.job_name(b[2])} overlap")
        for d in inst.downtimes:
            if d.machine == m:
                for s, e, j, k in lst:
                    if s < d.end and e > d.start:
                        errs.append(f"{inst.machine_name(m)}: {inst.job_name(j)} runs during downtime")
    return errs


# ─── KPIs ───────────────────────────────────────────────────────────────────
def completion_times(inst: Instance, sched: Schedule) -> List[int]:
    return [sched[(j, len(r) - 1)] + r[-1][1] for j, r in enumerate(inst.routes)]


def kpis(inst: Instance, sched: Schedule) -> dict:
    C = completion_times(inst, sched)
    cmax = max(C)
    out = {"makespan": cmax}
    if inst.due:
        T = [max(0, c - d) for c, d in zip(C, inst.due)]
        out.update({
            "total_tardiness": sum(T),
            "weighted_tardiness": sum(t * inst.weight_of(j) for j, t in enumerate(T)),
            "late_jobs": sum(t > 0 for t in T),
            "max_tardiness": max(T),
        })
    out["mean_flow_time"] = sum(c - inst.release_of(j) for j, c in enumerate(C)) / inst.n_jobs
    busy = [0] * inst.n_machines
    for j, r in enumerate(inst.routes):
        for m, p in r:
            busy[m] += p
    out["utilization"] = [b / cmax for b in busy]
    out["bottleneck"] = inst.machine_name(max(range(inst.n_machines), key=lambda m: busy[m]))
    return out


def objective_value(inst: Instance, sched: Schedule, objective: str) -> float:
    k = kpis(inst, sched)
    return k["makespan"] if objective == "makespan" else k["weighted_tardiness"]


def to_rows(inst: Instance, sched: Schedule) -> List[dict]:
    """Flat table of operations, for Gantt charts and exports."""
    C = completion_times(inst, sched)
    rows = []
    for (j, k), s in sorted(sched.items(), key=lambda kv: (kv[1], kv[0])):
        m, p = inst.routes[j][k]
        due = inst.due_of(j)
        rows.append({"job": inst.job_name(j), "job_idx": j, "op": k + 1, "machine": inst.machine_name(m),
                     "machine_idx": m, "start": s, "end": s + p, "p": p, "due": due,
                     "late": bool(due is not None and C[j] > due)})
    return rows
