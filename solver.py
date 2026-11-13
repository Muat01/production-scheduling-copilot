"""
Exact / near-exact scheduling with Google OR-Tools CP-SAT.

Model: one interval variable per operation, NoOverlap per machine (machine
downtime added as fixed intervals), precedence inside each job, release times.
Objectives: makespan or total weighted tardiness.

Rescheduling support:
* `frozen`  - operations already started at the reschedule time keep their start;
* `not_before` - every other operation starts at or after the reschedule time;
* `baseline` + `stability` - penalise moving operations away from the old plan
  (schedule nervousness), so the new plan stays close to what the shop expects.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from ortools.sat.python import cp_model

from jobshop import Instance, Schedule


@dataclass
class Result:
    schedule: Schedule
    status: str            # OPTIMAL / FEASIBLE / INFEASIBLE / UNKNOWN
    objective: float
    bound: float
    seconds: float

    @property
    def gap(self) -> float:
        return 0.0 if self.objective == 0 else max(0.0, (self.objective - self.bound) / self.objective)


def solve(inst: Instance, objective: str = "makespan", time_limit: float = 10.0,
          frozen: Optional[Dict[Tuple[int, int], int]] = None, not_before: int = 0,
          baseline: Optional[Schedule] = None, stability: float = 0.0,
          hint: Optional[Schedule] = None, workers: int = 8, seed: int = 0) -> Result:
    if objective not in ("makespan", "weighted_tardiness"):
        raise ValueError("objective must be 'makespan' or 'weighted_tardiness'")
    if objective == "weighted_tardiness" and not inst.due:
        raise ValueError("weighted_tardiness needs due dates")
    frozen = frozen or {}
    H = inst.horizon() + not_before
    m = cp_model.CpModel()
    start, end, per_machine = {}, {}, {k: [] for k in range(inst.n_machines)}

    for j, route in enumerate(inst.routes):
        for k, (mach, p) in enumerate(route):
            if (j, k) in frozen:
                s = m.new_constant(frozen[(j, k)])
                e = m.new_constant(frozen[(j, k)] + p)
            else:
                lo = max(inst.release_of(j) if k == 0 else 0, not_before)
                s = m.new_int_var(lo, H, f"s{j}_{k}")
                e = m.new_int_var(lo + p, H + p, f"e{j}_{k}")
            iv = m.new_interval_var(s, p, e, f"i{j}_{k}")
            start[(j, k)], end[(j, k)] = s, e
            per_machine[mach].append(iv)
            if k > 0:
                m.add(s >= end[(j, k - 1)])
    for d in inst.downtimes:
        per_machine[d.machine].append(m.new_fixed_size_interval_var(d.start, d.end - d.start, f"down{d.machine}_{d.start}"))
    for ivs in per_machine.values():
        m.add_no_overlap(ivs)

    last = [end[(j, len(r) - 1)] for j, r in enumerate(inst.routes)]
    cmax = m.new_int_var(0, 2 * H, "cmax")
    m.add_max_equality(cmax, last)
    if objective == "makespan":
        main = cmax
    else:
        tard = []
        for j, c in enumerate(last):
            t = m.new_int_var(0, 2 * H, f"t{j}")
            m.add(t >= c - inst.due[j])
            tard.append(int(round(inst.weight_of(j))) * t)
        main = sum(tard)

    if baseline and stability > 0:
        devs = []
        for key, s in start.items():
            if key in baseline and key not in frozen:
                d = m.new_int_var(0, 2 * H, f"d{key[0]}_{key[1]}")
                m.add_abs_equality(d, s - baseline[key])
                devs.append(d)
        # integer weights: objective * 100 + stability * 100 * deviation
        m.minimize(100 * main + int(round(100 * stability)) * sum(devs))
    else:
        m.minimize(main)

    if hint:
        for key, s in start.items():
            if key in hint and key not in frozen:
                m.add_hint(s, hint[key])

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = workers
    solver.parameters.random_seed = seed
    t0 = time.time()
    st = solver.solve(m)
    secs = time.time() - t0
    name = solver.status_name(st)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return Result({}, name, float("nan"), float("nan"), secs)
    sched = {key: int(solver.value(s)) for key, s in start.items()}
    obj = float(solver.value(main))
    bound = obj if st == cp_model.OPTIMAL and not (baseline and stability > 0) else (
        solver.best_objective_bound / (100 if baseline and stability > 0 else 1))
    return Result(sched, name, obj, float(bound), secs)
