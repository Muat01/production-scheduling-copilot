"""
Export README figures (docs/) from the same chart builders the app uses.
Needs kaleido (plotly==5.24.1 + kaleido==0.2.1 work without Chrome).
"""
import os

import pandas as pd

import charts
from jobshop import kpis, make_shop
from reschedule import Event, repair
from rules import RULES
from solver import solve

os.makedirs("docs", exist_ok=True)
R = {n: pd.read_csv(f"results/{n}.csv") for n in ("benchmarks", "rules_vs_optimal", "disruptions", "stability")}

inst = make_shop(1)
base = solve(inst, "weighted_tardiness", 10).schedule
ev = Event("breakdown", 80, machine=2, duration=90)
rep = repair(inst, base, ev, "stable", time_limit=10)
moved = {k for k, s in rep["schedule"].items() if k in base and base[k] != s}
kb, ka = kpis(inst, base), rep["kpis"]

figs = {
    "gantt_optimal.png": (charts.gantt(inst, base, title=f"Optimal plan · order book #1 · weighted tardiness {kb['weighted_tardiness']:.0f}"), 1300),
    "gantt_after_breakdown.png": (charts.gantt(rep["instance"], rep["schedule"], now=80, changed=moved,
                                               title=f"'Mill down at 80 for 90' → stable re-plan · weighted tardiness {ka['weighted_tardiness']:.0f}"), 1300),
    "rules_vs_optimal_wt.png": (charts.rules_bars(R["rules_vs_optimal"], "weighted_tardiness"), 1000),
    "rules_vs_optimal_makespan.png": (charts.rules_bars(R["rules_vs_optimal"], "makespan"), 1000),
    "benchmarks.png": (charts.benchmark_gaps(R["benchmarks"], RULES), 1100),
    "disruption_methods.png": (charts.disruption_panels(R["disruptions"]), 1200),
    "stability_tradeoff.png": (charts.tradeoff(R["stability"]), 1100),
}
for name, (fig, w) in figs.items():
    fig.update_layout(paper_bgcolor="#171E1B")
    fig.write_image(f"docs/{name}", width=w, scale=2)
print(f"{len(figs)} figures written")
