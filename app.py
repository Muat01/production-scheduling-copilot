"""
Production Scheduling Copilot · job-shop planning with a language interface

Run:  streamlit run app.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

import charts
import ui
from copilot import HELP, METHODS, OBJECTIVES, Copilot, llm_config
from jobshop import kpis, make_shop, to_rows
from rules import RULES, all_rules

RESULTS = Path(__file__).parent / "results"
EXAMPLES = ["Mill down at 80 for 90", "rush J4 due 200", "new job Saw 20, Lathe 25, Inspect 10 due 300 weight 3",
            "compare rules", "explain", "undo"]

st.set_page_config(page_title="Production Scheduling Copilot", page_icon="🗓️", layout="wide")
ui.inject()


def html(s: str, col=None) -> None:
    (col or st).markdown(s, unsafe_allow_html=True)


def plot(fig, key=None) -> None:
    with st.container(border=True):
        st.plotly_chart(fig, width="stretch", config=charts.CONFIG, key=key)


@st.cache_data(show_spinner=False)
def study():
    out = {}
    for n in ("benchmarks", "rules_vs_optimal", "disruptions", "disruption_paired", "stability"):
        f = RESULTS / f"{n}.csv"
        out[n] = pd.read_csv(f) if f.exists() else None
    return out


# ─── Sidebar ────────────────────────────────────────────────────────────────
ui.sidebar_brand("Scheduling Copilot", "Job-shop planning lab")
with st.sidebar:
    seed = st.selectbox("Order book (simulated)", list(range(1, 31)), index=0, format_func=lambda s: f"Order book #{s}",
                        help="10 jobs × 6 machines, generated with a fixed seed. Due dates follow the TWK rule.")
    objective = st.radio("Objective", list(OBJECTIVES), format_func=lambda o: OBJECTIVES[o].capitalize(), key="objective")
    method = st.radio("Repair method after a disruption", list(METHODS), index=2, format_func=lambda m: METHODS[m], key="method")
    now = st.slider("Current time (min)", 0, 300, 60, 10,
                    help="Operations that started before this moment are frozen when the plan is repaired.")
    cfg = llm_config()
    use_llm = st.toggle("Use an LLM to read commands", value=False, disabled=cfg is None,
                        help="Needs LLM_API_KEY (any OpenAI-compatible endpoint, e.g. Gemini's free tier). "
                             "Without it the built-in rule-based parser is used.")
    html(f'<div class="note">Language parser: <span class="badge" style="--c:{"#22C98A" if (cfg and use_llm) else "#E6B94A"}">'
         f'{"LLM · " + cfg["model"] if (cfg and use_llm) else "built-in rules (offline)"}</span></div>')
    st.write("")
    html('<div class="note">All order books are <b>simulated</b>. The schedule is always computed by the solver or a '
         'dispatching rule and checked for feasibility; language only selects the action.</div>')

# ─── Session state ──────────────────────────────────────────────────────────
key = (seed, objective)
if st.session_state.get("cp_key") != key:
    with st.spinner("Solving the order book with CP-SAT…"):
        st.session_state.cp = Copilot(make_shop(seed), objective=objective, method=method, now=now)
    st.session_state.cp_key = key
    st.session_state.chat = [("assistant", "Optimal plan ready. Tell me what changed on the shop floor.\n\n" + HELP)]
    st.session_state.changed = set()
cp: Copilot = st.session_state.cp
cp.method, cp.now, cp.use_llm = method, now, use_llm

# ─── Hero ───────────────────────────────────────────────────────────────────
ui.hero("Smart planning · operations research + AI",
        "Production Scheduling <span>Copilot</span>",
        "Tell the planner what happened on the shop floor in plain words (a breakdown, a rush order, a new job). "
        "The copilot turns it into a structured action, an optimisation solver (OR-Tools CP-SAT) builds the new plan, "
        "a checker verifies it, and the copilot explains what changed.",
        [("Simulated order books", "gold"), ("OR-Tools CP-SAT", "emerald"), ("6 dispatching rules", "steel"),
         ("Validated on 10 benchmarks", "emerald")])

tab_cp, tab_rules, tab_study, tab_method = st.tabs(["🗓️  Copilot", "⚖️  Rules vs optimal", "🔬  Study results", "📚  Method & references"])

# ═══════════════════════════════ COPILOT ════════════════════════════════════
with tab_cp:
    def run(cmd: str) -> None:
        before = dict(cp.sched)
        st.session_state.chat.append(("user", cmd))
        with st.spinner("Re-planning…"):
            r = cp.handle(cmd)
        st.session_state.chat.append(("assistant", r["message"]))
        st.session_state.changed = {k for k, s in cp.sched.items() if before.get(k) is not None and before[k] != s} \
            if r["changed"] else st.session_state.changed

    k = kpis(cp.inst, cp.sched)
    c1, c2, c3, c4 = st.columns(4)
    html(ui.kpi("Weighted tardiness", f"{k['weighted_tardiness']:.0f}", "Σ weight × minutes late", "emerald"), c1)
    html(ui.kpi("Late jobs", f"{k['late_jobs']}", f"of {cp.inst.n_jobs} jobs", "critical" if k["late_jobs"] else "emerald"), c2)
    html(ui.kpi("Makespan", f"{k['makespan']}", "all jobs finished", "steel", unit=" min"), c3)
    html(ui.kpi("Bottleneck", k["bottleneck"], "most loaded machine", "gold", text=True), c4)
    st.write("")
    plot(charts.gantt(cp.inst, cp.sched, now=cp.now, changed=st.session_state.changed), key="gantt_main")
    html('<div class="note">Bars show jobs (label = job). <b>Emerald</b> on time · <b>red</b> late · <b>gold</b> rush order · '
         'steel outline = moved by the last change · hatched = machine down · dashed gold = now.</div>')

    st.write("")
    left, right = st.columns([1.35, 1])
    with left:
        ui.section("Copilot", "Talk to the planner", f"Repair method: {METHODS[cp.method]} · objective: {OBJECTIVES[cp.objective]}")
        box = st.container(height=430)
        for role, msg in st.session_state.chat[-14:]:
            box.chat_message(role, avatar="🧑‍🏭" if role == "user" else "🗓️").markdown(msg)
        cmd = st.chat_input("e.g. Mill down at 80 for 90")
        if cmd:
            run(cmd)
            st.rerun()
    with right:
        ui.section("Quick commands", "Try a disruption", "Each button sends the command to the copilot.")
        for i, ex in enumerate(EXAMPLES):
            if st.button(ex, key=f"ex{i}", width="stretch"):
                run(ex)
                st.rerun()
        plot(charts.utilization(cp.inst, k["utilization"]), key="util")

    with st.expander("Plan as a table (export)"):
        df = pd.DataFrame(to_rows(cp.inst, cp.sched)).drop(columns=["job_idx", "machine_idx"])
        st.dataframe(df, hide_index=True, width="stretch", height=300)
        st.download_button("Download plan (CSV)", df.to_csv(index=False), "plan.csv", "text/csv")

# ═══════════════════════════════ RULES ══════════════════════════════════════
with tab_rules:
    ui.section("This order book", "How far are shop-floor rules from optimal?",
               "Dispatching rules build a plan in milliseconds; CP-SAT searches for the best plan. Same order book, same objective.")
    base = cp.base
    rows = []
    for r, s in all_rules(base).items():
        kk = kpis(base, s)
        rows.append({"method": r, "description": RULES[r], "makespan": kk["makespan"],
                     "weighted_tardiness": kk["weighted_tardiness"], "late_jobs": kk["late_jobs"]})
    opt = cp.history[0][1] if cp.history else cp.sched
    ko = kpis(base, opt) if not cp.history else kpis(cp.history[0][0], opt)
    rows.insert(0, {"method": "CP-SAT", "description": f"Optimal for {OBJECTIVES[objective]}", "makespan": ko["makespan"],
                    "weighted_tardiness": ko["weighted_tardiness"], "late_jobs": ko["late_jobs"]})
    tbl = pd.DataFrame(rows)
    best_rule = tbl[tbl.method != "CP-SAT"].sort_values(objective).iloc[0]
    i1, i2 = st.columns(2)
    html(ui.insight("Best rule here", f"<b>{best_rule.method}</b> gives {best_rule[objective]:.0f} "
                    f"vs <b>{ko[objective]:.0f}</b> with CP-SAT on this order book.", "steel"), i1)
    html(ui.insight("Why it matters", "Rules decide one machine at a time with local information; the solver sees the whole "
                    "order book. The gap is what an optimiser is worth before any disruption happens.", "emerald"), i2)
    st.write("")
    st.dataframe(tbl, hide_index=True, width="stretch")
    pick = st.selectbox("Show the plan of", ["CP-SAT"] + list(RULES), key="rule_pick")
    sched = opt if pick == "CP-SAT" else all_rules(base)[pick]
    plot(charts.gantt(base if pick != "CP-SAT" or not cp.history else cp.history[0][0], sched, title=f"{pick} plan"),
         key="gantt_rule")

# ═══════════════════════════════ STUDY ══════════════════════════════════════
with tab_study:
    S = study()
    if S["rules_vs_optimal"] is None:
        st.warning("No study results found. Run `python experiments.py` first.")
    else:
        rv = S["rules_vs_optimal"]
        ui.section("Study 1", "Rules vs optimal on 30 simulated order books", "10 jobs × 6 machines each, TWK due dates.")
        a, b = st.columns(2)
        with a:
            plot(charts.rules_bars(rv, "weighted_tardiness"), key="rv_wt")
        with b:
            plot(charts.rules_bars(rv, "makespan"), key="rv_ms")
        if S["benchmarks"] is not None:
            bm = S["benchmarks"]
            ui.section("Study 2", "Is the solver right? Classic benchmarks",
                       f"CP-SAT matched the published optimum on {int((bm.cpsat == bm.optimum).sum())} of {len(bm)} instances.")
            plot(charts.benchmark_gaps(bm, RULES), key="bench")
        if S["disruptions"] is not None:
            ds = S["disruptions"].set_index("method")
            ui.section("Study 3", "After a breakdown: repair or re-plan?",
                       f"{int(ds['n'].iloc[0])} breakdown scenarios (random machine, moment and 60–120 min duration), same scenarios for every method.")
            plot(charts.disruption_panels(S["disruptions"]), key="disr")
            if S["disruption_paired"] is not None:
                pp = S["disruption_paired"].set_index(["from", "to"])
                r1, r2 = pp.loc[("right_shift", "reoptimize")], pp.loc[("reoptimize", "stable")]
                i1, i2 = st.columns(2)
                html(ui.insight("Re-plan vs repair", f"Full re-optimisation changes weighted tardiness by "
                                f"<b>{r1.wt_diff:+.0f} ± {r1.wt_ci:.0f}</b> vs right-shift (paired 95% CI).", "emerald"), i1)
                html(ui.insight("The price of stability", f"Stable re-optimisation: weighted tardiness {r2.wt_diff:+.0f} ± {r2.wt_ci:.0f} "
                                f"and schedule changes {r2.dev_diff:+.0f} ± {r2.dev_ci:.0f} min vs full re-optimisation.", "gold"), i2)
        if S["stability"] is not None:
            plot(charts.tradeoff(S["stability"]), key="trade")

# ═══════════════════════════════ METHOD ═════════════════════════════════════
with tab_method:
    ui.section("Method", "LLM proposes, solver decides, checker verifies")
    m1, m2 = st.columns(2)
    with m1:
        with st.container(border=True):
            st.markdown("##### 1 · Understand the request")
            st.markdown("A command is turned into a structured action (`breakdown`, `rush`, `due_change`, `new_job`, "
                        "`objective`, `method`…). The built-in parser works offline; an optional LLM can be plugged in "
                        "through any OpenAI-compatible endpoint. Every action is validated against the shop's machines, jobs and times.")
        with st.container(border=True):
            st.markdown("##### 2 · Decide with optimisation")
            st.markdown("The plan comes from **OR-Tools CP-SAT** (interval variables, no-overlap per machine, job precedence, "
                        "downtime as fixed intervals) or from **dispatching rules** inside the Giffler–Thompson active-schedule "
                        "generator. The language model never writes the schedule.")
    with m2:
        with st.container(border=True):
            st.markdown("##### 3 · Verify and explain")
            st.markdown("An independent checker tests precedence, machine overlap, release times and downtime. A plan that fails "
                        "is not applied. The explanation is generated from the numbers: objective before and after, late jobs, "
                        "operations moved, bottleneck.")
        with st.container(border=True):
            st.markdown("##### Repair methods")
            st.markdown("- **Right-shift**: keep every machine's sequence, push work later.\n"
                        "- **Re-optimise**: solve again from *now*, started operations frozen.\n"
                        "- **Stable re-optimise**: same, plus a penalty on every minute an operation moves, "
                        "to limit schedule nervousness on the shop floor.")
    with st.container(border=True):
        st.markdown("##### References")
        st.markdown(
            "- Giffler, B. & Thompson, G. L. (1960). Algorithms for solving production-scheduling problems. *Operations Research*, 8(4), 487–503. doi:10.1287/opre.8.4.487\n"
            "- Panwalkar, S. S. & Iskander, W. (1977). A survey of scheduling rules. *Operations Research*, 25(1), 45–61. doi:10.1287/opre.25.1.45\n"
            "- Baker, K. R. (1984). Sequencing rules and due-date assignments in a job shop. *Management Science*, 30(9), 1093–1104. doi:10.1287/mnsc.30.9.1093\n"
            "- Vieira, G. E., Herrmann, J. W. & Lin, E. (2003). Rescheduling manufacturing systems: a framework of strategies, policies, and methods. *Journal of Scheduling*, 6(1), 39–62. doi:10.1023/A:1022235519958\n"
            "- Ouelhadj, D. & Petrovic, S. (2009). A survey of dynamic scheduling in manufacturing systems. *Journal of Scheduling*, 12(4), 417–431. doi:10.1007/s10951-008-0090-8\n"
            "- Zhang, L. et al. (2026). DScheLLM: Enabling dynamic scheduling through a fine-tuned dual-system large language model. arXiv:2601.09100\n"
            "- Yan, J. & Ji, S. (2026). Industrial mechanism-aware multi-agent collaboration of large language models for job shop scheduling optimization. *Computers & Industrial Engineering*, 217, 112079\n"
            "- Perron, L. & Didier, F. CP-SAT, Google OR-Tools (v9.15). developers.google.com/optimization\n"
            "- Benchmarks: Fisher & Thompson (1963) in Muth & Thompson, *Industrial Scheduling*; Lawrence (1984); Adams, Balas & Zawack (1988), via JSPLIB.")

ui.footer("simulated order books · OR-Tools CP-SAT")
