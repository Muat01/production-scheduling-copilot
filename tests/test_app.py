"""Charts and headless Streamlit tests."""
import os
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

import charts
from jobshop import Downtime, make_shop
from rules import RULES
from solver import solve

ROOT = Path(__file__).resolve().parents[1]


def _res(n):
    return pd.read_csv(ROOT / "results" / f"{n}.csv")


def test_charts_build():
    inst = make_shop(1).with_(downtimes=(Downtime(2, 50, 120),))
    s = solve(inst, "weighted_tardiness", 5).schedule
    figs = [charts.gantt(inst, s, now=60, changed={next(iter(s))}), charts.utilization(inst, [0.5] * 6),
            charts.rules_bars(_res("rules_vs_optimal"), "weighted_tardiness"), charts.rules_bars(_res("rules_vs_optimal"), "makespan"),
            charts.benchmark_gaps(_res("benchmarks"), RULES), charts.disruption_panels(_res("disruptions")),
            charts.tradeoff(_res("stability"))]
    assert all(len(f.data) for f in figs)
    assert any(t.name == "Machine down" for t in figs[0].data)


def test_saved_study_is_consistent():
    bm = _res("benchmarks")
    assert (bm.cpsat == bm.optimum).all()
    rv = _res("rules_vs_optimal").set_index(["objective", "method"])["mean"]
    for obj in ("weighted_tardiness", "makespan"):
        assert rv[(obj, "CP-SAT")] <= min(rv[(obj, r)] for r in RULES)


def _app():
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=240)
        at.run()
    finally:
        os.chdir(cwd)
    return at


def test_app_runs():
    at = _app()
    assert not at.exception, at.exception
    assert len(at.tabs) == 4
    assert any("Copilot" in m.value for m in at.markdown)


def test_app_chat_and_buttons():
    at = _app()
    at.chat_input[0].set_value("Mill down at 80 for 90").run()
    assert not at.exception, at.exception
    assert any("Mill down 80–170" in m.value for m in at.markdown)
    at.button(key="ex1").click().run()            # rush J4
    assert not at.exception, at.exception
    at.selectbox(key="rule_pick").set_value("EDD").run()
    assert not at.exception, at.exception
    at.radio(key="objective").set_value("makespan").run()
    assert not at.exception, at.exception
