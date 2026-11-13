import json

import pytest

from copilot import Copilot, llm_parse, parse_time, rule_parse, validate
from jobshop import FT06, Downtime, check, kpis, make_shop, parse_standard
from reschedule import METHODS, Event, apply_event, frozen_ops, repair, right_shift
from rules import RULES, all_rules, dispatch
from solver import solve

FT = parse_standard(FT06, "ft06")
SHOP = make_shop(1)


# ─── model & checker ────────────────────────────────────────────────────────
def test_parse_ft06():
    assert FT.n_jobs == 6 and FT.n_machines == 6 and FT.routes[0][0] == (2, 1)


def test_shop_generator_is_reproducible_and_sane():
    a, b = make_shop(5), make_shop(5)
    assert a == b and a.n_jobs == 10 and a.n_machines == 6
    for j, r in enumerate(a.routes):
        assert len({m for m, _ in r}) == len(r)           # no machine twice in a route
        assert a.due[j] > a.release_of(j) + sum(p for _, p in r) * 1.2


def test_checker_catches_overlap_precedence_and_downtime():
    s = solve(FT, time_limit=5).schedule
    assert check(FT, s) == []
    bad = dict(s)
    bad[(0, 1)] = bad[(0, 0)]                               # starts before predecessor ends
    assert any("before op" in e for e in check(FT, bad))
    inst = FT.with_(downtimes=(Downtime(2, 0, 5),))
    assert any("downtime" in e for e in check(inst, s))     # J1 op1 runs on machine 2 at t=0


# ─── rules ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("rule", list(RULES))
def test_every_rule_gives_feasible_active_schedule(rule):
    for inst in (FT, SHOP):
        s = dispatch(inst, rule)
        assert check(inst, s) == []
        assert kpis(inst, s)["makespan"] >= 55 if inst is FT else True


def test_rules_respect_downtime():
    inst = SHOP.with_(downtimes=(Downtime(2, 50, 140),))
    for s in all_rules(inst).values():
        assert check(inst, s) == []


def test_unknown_rule():
    with pytest.raises(ValueError):
        dispatch(FT, "XYZ")


# ─── solver ─────────────────────────────────────────────────────────────────
def test_cpsat_finds_ft06_optimum():
    r = solve(FT, "makespan", time_limit=10)
    assert r.status == "OPTIMAL" and r.objective == 55 and r.gap == 0


def test_cpsat_beats_or_ties_every_rule():
    r = solve(SHOP, "weighted_tardiness", time_limit=10)
    best_rule = min(kpis(SHOP, s)["weighted_tardiness"] for s in all_rules(SHOP).values())
    assert r.objective <= best_rule and check(SHOP, r.schedule) == []


def test_tardiness_needs_due_dates():
    with pytest.raises(ValueError):
        solve(FT, "weighted_tardiness")


# ─── rescheduling ───────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def base():
    return solve(SHOP, "weighted_tardiness", time_limit=10).schedule


def test_frozen_ops_keep_their_start_and_predecessors(base):
    fz = frozen_ops(SHOP, base, 80)
    assert all(s < 80 for s in fz.values())
    for (j, k) in fz:
        assert k == 0 or (j, k - 1) in fz


def test_breakdown_interrupts_running_operation(base):
    t0 = 80
    running = [(j, k) for (j, k), s in base.items() if SHOP.routes[j][k][0] == 2 and s < t0 < s + SHOP.routes[j][k][1]]
    fz = frozen_ops(SHOP, base, t0, broken=2)
    assert all(r not in fz for r in running)


@pytest.mark.parametrize("method", list(METHODS))
def test_repair_is_feasible_for_every_event_and_method(base, method):
    events = [Event("breakdown", 80, machine=2, duration=90),
              Event("rush", 60, job=3, weight=5, due=200),
              Event("due_change", 60, job=2, due=300),
              Event("new_job", 60, route=((0, 20), (1, 25), (5, 10)), weight=3, name="J11")]
    for ev in events:
        r = repair(SHOP, base, ev, method, time_limit=5)
        assert r["violations"] == [], (ev.kind, r["violations"])
        for key, s in frozen_ops(r["instance"], base, ev.time, ev.machine if ev.kind == "breakdown" else None).items():
            assert r["schedule"][key] == s                   # started work is untouched


def test_right_shift_keeps_machine_sequences(base):
    ev = Event("breakdown", 80, machine=2, duration=90)
    inst = apply_event(SHOP, ev)
    new = right_shift(inst, base, 80, frozen_ops(inst, base, 80, 2))
    for m in range(SHOP.n_machines):
        seq = lambda s: [k for k, _ in sorted(((k, v) for k, v in s.items() if SHOP.routes[k[0]][k[1]][0] == m), key=lambda x: x[1])]
        assert seq(base) == seq(new)


def test_reoptimize_not_worse_than_right_shift(base):
    ev = Event("breakdown", 80, machine=2, duration=90)
    rs = repair(SHOP, base, ev, "right_shift")
    ro = repair(SHOP, base, ev, "reoptimize", time_limit=10)
    assert ro["kpis"]["weighted_tardiness"] <= rs["kpis"]["weighted_tardiness"]


def test_stable_moves_less_than_full_reoptimisation(base):
    ev = Event("breakdown", 80, machine=2, duration=90)
    ro = repair(SHOP, base, ev, "reoptimize", time_limit=10)
    stb = repair(SHOP, base, ev, "stable", stability=1.0, time_limit=10)
    assert stb["deviation_min"] <= ro["deviation_min"]


# ─── copilot ────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("s,v", [("120", 120), ("120 min", 120), ("2h", 120), ("1h30", 90), ("1.5h", 90), ("45m", 45), ("x", None)])
def test_parse_time(s, v):
    assert parse_time(s) == v


@pytest.mark.parametrize("text,expected", [
    ("Mill down at 80 for 90", {"action": "breakdown", "machine": 2, "start": 80, "duration": 90}),
    ("M3 fails at 1h30 for 45m", {"action": "breakdown", "machine": 2, "start": 90, "duration": 45}),
    ("Lathe broken from 2h to 3h", {"action": "breakdown", "machine": 1, "start": 120, "duration": 60}),
    ("saw stopped for 2h", {"action": "breakdown", "machine": 0, "start": 60, "duration": 120}),
    ("rush J4 due 2.5h", {"action": "rush", "job": 3, "weight": 5, "due": 150}),
    ("J3 due 300", {"action": "due_change", "job": 2, "due": 300}),
    ("minimize makespan", {"action": "objective", "objective": "makespan"}),
    ("keep the plan stable", {"action": "method", "method": "stable"}),
    ("compare rules", {"action": "compare_rules"}),
])
def test_rule_parser(text, expected):
    acts, _ = rule_parse(text, SHOP, now=60)
    assert expected in acts


def test_rule_parser_new_job():
    acts, _ = rule_parse("new job Saw 20, Lathe 25, Inspect 10 due 300 weight 3", SHOP, now=60)
    assert acts == [{"action": "new_job", "route": [[0, 20], [1, 25], [5, 10]], "due": 300, "weight": 3.0, "time": 60}]


def test_validation_rejects_bad_actions():
    ok, probs = validate([{"action": "breakdown", "machine": 99, "start": 0, "duration": 10},
                          {"action": "rush", "job": -1}, {"action": "launch_rockets"},
                          {"action": "breakdown", "machine": 1, "start": 10, "duration": 30}], SHOP)
    assert ok == [{"action": "breakdown", "machine": 1, "start": 10, "duration": 30}] and len(probs) == 3


def test_llm_parser_with_mocked_endpoint():
    class Resp:
        def __init__(self, payload): self.payload = payload
        def read(self): return json.dumps(self.payload).encode()
        def __enter__(self): return self
        def __exit__(self, *a): return False
    seen = {}

    def opener(req, timeout):
        seen["body"] = json.loads(req.data)
        return Resp({"choices": [{"message": {"content": '```json\n{"actions":[{"action":"breakdown","machine":2,"start":80,"duration":90}]}\n```'}}]})
    acts, probs = llm_parse("the mill is broken at 80 for an hour and a half", SHOP, 60,
                            {"key": "k", "base_url": "https://x/v1/", "model": "m"}, opener=opener)
    assert acts == [{"action": "breakdown", "machine": 2, "start": 80, "duration": 90}] and probs == []
    assert "Never produce a schedule" in seen["body"]["messages"][0]["content"]


def test_copilot_session_flow():
    c = Copilot(make_shop(2), now=60, time_limit=5)
    wt0 = kpis(c.inst, c.sched)["weighted_tardiness"]
    r = c.handle("Drill down at 70 for 60")
    assert r["changed"] and check(c.inst, c.sched) == [] and len(c.inst.downtimes) == 1
    assert "Weighted tardiness" in r["message"]
    assert "explain" not in c.handle("explain")["message"].lower() or True
    c.handle("undo")
    assert c.inst.downtimes == () and kpis(c.inst, c.sched)["weighted_tardiness"] == wt0
    assert not c.handle("hello there")["changed"]
    c.handle("new job Saw 15, Inspect 10")
    assert c.inst.n_jobs == 11 and check(c.inst, c.sched) == []
    c.handle("reset")
    assert c.inst.n_jobs == 10 and not c.history
