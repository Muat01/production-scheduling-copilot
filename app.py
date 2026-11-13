"""
Production Scheduling Copilot · control room (Streamlit)

Run:  streamlit run app.py
"""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import streamlit as st

import charts
import ui
from copilot import HELP, METHODS, OBJECTIVES, Copilot, llm_config
from jobshop import check, kpis, make_shop, to_rows
from reschedule import Event, repair
from rules import RULES, all_rules
from solver import solve
from theme import C_EMERALD, C_GOLD, C_ROSE, C_STEEL

RESULTS = Path(__file__).parent / "results"
QUICK = ["Mill down at 120 for 60", "Saw broken from 60 to 180", "rush J4", "J3 due 200",
         "new job Saw 20, Lathe 25, Inspect 10 due 300 weight 3", "compare rules", "keep the plan stable", "undo"]
PAGES = ["Overview", "Planner", "Rules vs optimal", "Disruptions", "Benchmarks", "Method & sources"]
CRUMB = {"Overview": "Production Scheduling Copilot · the story in one page",
         "Planner": "Tell the planner what happened. Watch the plan change.",
         "Rules vs optimal": "30 simulated order books · six dispatching rules vs CP-SAT",
         "Disruptions": "After a breakdown: repair the plan or re-plan?",
         "Benchmarks": "Is the solver right? 10 classic job-shop instances",
         "Method & sources": "How it works, limits and references"}
EVENT_KINDS = ("breakdown", "rush", "due_change", "new_job")

st.set_page_config(page_title="Production Scheduling Copilot", page_icon="🗓️", layout="wide", initial_sidebar_state="expanded")
ui.inject()


def html(s: str, where=None) -> None:
    (where or st).markdown(s, unsafe_allow_html=True)


def plot(fig, key=None) -> None:
    st.plotly_chart(fig, width="stretch", config=charts.CONFIG, key=key)


def card(title: str, sub: str = "", right: str = ""):
    c = st.container(border=True)
    with c:
        ui.card_head(title, sub, right)
    return c


@st.cache_data(show_spinner=False)
def study():
    out = {}
    for name in ("benchmarks", "rules_vs_optimal", "rules_vs_optimal_runs", "disruptions", "disruption_paired",
                 "disruption_runs", "stability"):
        f = RESULTS / f"{name}.csv"
        out[name] = pd.read_csv(f) if f.exists() else None
    return out


@st.cache_resource(show_spinner=False)
def optimal(seed: int, objective: str = "weighted_tardiness"):
    inst = make_shop(seed)
    return inst, solve(inst, objective, 10, workers=1).schedule


@st.cache_resource(show_spinner=False)
def story():
    """Order book 1, the saw breaks at 120 for 60 min: optimal plan, right-shift repair, stable CP-SAT re-plan."""
    inst, base = optimal(1)
    ev = Event("breakdown", 120, machine=0, duration=60)
    return inst, base, repair(inst, base, ev, "right_shift"), repair(inst, base, ev, "stable", time_limit=5)


def moved(old: dict, new: dict) -> tuple[int, int]:
    keys = [k for k in old if k in new]
    shifts = [abs(new[k] - old[k]) for k in keys]
    return sum(s > 0 for s in shifts), sum(shifts)


def go_to(page: str) -> None:
    st.session_state.nav = page


S = study()

# ─── Sidebar: brand, navigation, footer ───────────────────────────────────
ui.sidebar_brand()
page = st.sidebar.radio("Pages", PAGES, key="nav", label_visibility="collapsed")
ui.sidebar_foot()

meta = f'Order book <b>{st.session_state.get("seed", 1)}</b> · 30 · simulated'
ui.topbar(CRUMB[page], page, meta)


# ═══════════════════════════════ OVERVIEW ═════════════════════════════════
def page_overview():
    rv = S["rules_vs_optimal"].set_index(["objective", "method"])["mean"]
    rules_wt = sorted(((m, rv[("weighted_tardiness", m)]) for m in RULES), key=lambda x: x[1])
    opt_wt = rv[("weighted_tardiness", "CP-SAT")]
    best, best_v = rules_wt[0]
    bm = S["benchmarks"]
    ds = S["disruptions"].set_index("method")
    pp = S["disruption_paired"].set_index(["from", "to"])
    rs, re_ = ds.loc["right_shift"], ds.loc["reoptimize"]
    sp = pp.loc[("reoptimize", "stable")]
    red = 1 - opt_wt / best_v
    k = ui.kpis([
        ui.kpi("Weighted tardiness vs best rule", f"−{red * 100:.0f}<small>%</small>", f"{best_v:,.0f} ({best}) → {opt_wt:,.0f} · mean of 30 books", ui.pill("CP-SAT")),
        ui.kpi("Benchmarks solved to optimum", f"{int((bm.cpsat == bm.optimum).sum())}<small>/ {len(bm)}</small>", f"ft06 … abz5 · max {bm.cpsat_seconds.max():.1f} s", ui.pill("JSPLIB", "mu")),
        ui.kpi("Tardiness after a breakdown", f"−{(1 - re_.weighted_tardiness / rs.weighted_tardiness) * 100:.0f}<small>%</small>",
               f"re-plan vs right-shift · {rs.weighted_tardiness:,.0f} → {re_.weighted_tardiness:,.0f}", ui.pill(f"n = {int(rs.n)}")),
        ui.kpi("Plan changes with stability", f"{sp.dev_diff / re_.deviation_min * 100:+.0f}<small>%</small>".replace("-", "−"),
               f"for only {sp.wt_diff / re_.weighted_tardiness * 100:+.0f}% tardiness", ui.pill("w = 0.2", "wn"))])
    ui.hero("Production Scheduling Copilot · simulated machine shop, 6 machines, 10 jobs per order book",
            f"Planners speak in plain words. <em>The solver plans</em>, a checker verifies, and the copilot explains: "
            f"<strong>{red * 100:.0f}% less weighted tardiness</strong> than the best rule of thumb.",
            "Machines break, customers call with rush orders. This control room runs the full loop on simulated order books: "
            "the language layer only picks the action, OR-Tools CP-SAT builds the plan, and every plan passes an independent feasibility check.", k)

    inst, base, rsr, sbr = story()
    with card("One breakdown, three answers", "Order book 1 · the Saw breaks at 120 min for 60 min · Gantt of the six machines"):
        names = [("Optimal plan", "CP-SAT minimises weighted tardiness before anything goes wrong."),
                 ("Right-shift repair", "Keep every machine's sequence and push work later. Delays cascade down the line."),
                 ("Copilot re-plan", "CP-SAT re-plans from now: started work is frozen, moving operations is penalised (w = 0.2).")]
        step = st.segmented_control("Step", [n for n, _ in names], default=names[0][0], key="story_step", label_visibility="collapsed") or names[0][0]
        i = [n for n, _ in names].index(step)
        html(ui.steps(names, i))
        k0 = kpis(inst, base)
        if i == 0:
            html(ui.kstrip(k0, None, 0, 0, len(check(inst, base))))
            plot(charts.gantt(inst, base, height=330), key="story_g0")
        else:
            r = rsr if i == 1 else sbr
            html(ui.kstrip(r["kpis"], k0, r["moved_ops"], r["deviation_min"], len(r["violations"])))
            plot(charts.gantt(r["instance"], r["schedule"], now=120, prev=base, height=350), key=f"story_g{i}")
        st.button("Open the planner", type="primary", on_click=go_to, args=("Planner",), key="open_pl")

    a, b = st.columns([2, 1])
    with a:
        with card("The copilot loop", "Language proposes, the solver decides, the checker verifies"):
            html(ui.pipe() + '<div class="cmdex"><code>"Mill down at 120 for 60"</code><span>→</span>'
                 '<code>{"action": "breakdown", "machine": 2, "start": 120, "duration": 60}</code></div>')
    with b:
        with card("What the numbers say"):
            html(ui.insights([
                (f"Rules of thumb leave jobs <b>{best_v / opt_wt:.1f}×</b> later than the optimal plan (mean weighted tardiness, 30 books).", C_EMERALD),
                (f"Right-shift keeps every sequence but moves the <b>most</b> minutes ({rs.deviation_min:,.0f}), because each delay cascades.", C_ROSE),
                (f"Stability is almost free: <b>{sp.dev_diff:+,.0f}</b> minutes moved for <b>{sp.wt_diff:+,.0f}</b> weighted tardiness (paired 95% CI).", C_GOLD),
                ("The rule that wins on makespan (FIFO) is not the rule that wins on due dates (CR). There is no universal rule.", C_STEEL)]))


# ═══════════════════════════════ PLANNER ══════════════════════════════════
def page_planner():
    c1, c2, c3, c4 = st.columns([1, 1.3, 2.1, 0.8], vertical_alignment="bottom")
    seed = c1.selectbox("Order book", list(range(1, 31)), key="seed", format_func=lambda s: f"Order book {s}")
    objective = c2.segmented_control("Objective", list(OBJECTIVES), default="weighted_tardiness", key="objective",
                                     format_func=lambda o: "Due dates" if o == "weighted_tardiness" else "Makespan") or "weighted_tardiness"
    method = c3.segmented_control("Repair method", list(METHODS), default="stable", key="method",
                                  format_func=lambda m: {"right_shift": "Right-shift", "reoptimize": "Full re-opt", "stable": "Stable re-opt"}[m]) or "stable"
    with c4.popover("Settings", width="stretch"):
        now = st.slider("Current time (min)", 0, 300, 60, 10, key="now",
                        help="Rush orders and due-date changes happen at this time; started work is frozen.")
        cfg = llm_config()
        use_llm = st.toggle("Use an LLM to read commands", value=False, disabled=cfg is None, key="use_llm",
                            help="Needs LLM_API_KEY (any OpenAI-compatible endpoint). Without it the built-in parser is used.")
        st.caption("Parser: " + (f"LLM · {cfg['model']}" if (cfg and use_llm) else "built-in rules (offline)"))

    key = (seed, objective)
    if st.session_state.get("cp_key") != key:
        with st.spinner("Solving the order book with CP-SAT…"):
            st.session_state.cp = Copilot(make_shop(seed), objective=objective, method=method, now=now)
        st.session_state.cp_key = key
        st.session_state.chat = [("assistant", "Optimal plan ready. Tell me what happened on the shop floor.\n\n" + HELP)]
        st.session_state.events = []
    cp: Copilot = st.session_state.cp
    cp.method, cp.now, cp.use_llm = method, now, use_llm

    def run(cmd: str) -> None:
        st.session_state.chat.append(("user", cmd))
        n_hist = len(cp.history)
        with st.spinner("Re-planning…"):
            r = cp.handle(cmd)
        st.session_state.chat.append(("assistant", r["message"]))
        ev = st.session_state.events
        if len(cp.history) > n_hist:
            acts = [a for a in r["actions"] if a["action"] in EVENT_KINDS + ("objective",)]
            t = next((int(a["start"]) for a in acts if a["action"] == "breakdown"), cp.now)
            ev.append((" · ".join(cp._describe(a) if a["action"] in EVENT_KINDS else f"Objective: {OBJECTIVES[a['objective']]}"
                                  for a in acts) or "Change", t))
        elif len(cp.history) < n_hist:
            del ev[len(cp.history):]
        if not cp.history:
            ev.clear()

    left, right = st.columns([2, 1])
    with left:
        prev_i, prev_s = (cp.history[-1][0], cp.history[-1][1]) if cp.history else (None, None)
        k = kpis(cp.inst, cp.sched)
        with card("Machine Gantt", "Hover a bar to see the job, its due date and its tardiness"):
            mo, mm = moved(prev_s, cp.sched) if prev_s else (0, 0)
            html(ui.kstrip(k, kpis(prev_i, prev_s) if prev_s else None, mo, mm, len(check(cp.inst, cp.sched))))
            src = (f'<span class="src pre">✓ CP-SAT · {charts.METHOD_LABEL[cp.method]} · checked feasible</span>' if cp.history and cp.method != "right_shift"
                   else '<span class="src live">⚡ Right-shift repair · checked feasible</span>' if cp.history
                   else f'<span class="src pre">✓ CP-SAT optimal plan · {OBJECTIVES[cp.objective]}</span>')
            html(src)
            t_now = st.session_state.events[-1][1] if st.session_state.events else None
            plot(charts.gantt(cp.inst, cp.sched, now=t_now, prev=prev_s, height=400), key="gantt_main")
        with card("Jobs in this plan", "Completion vs due date · sortable · download the plan as CSV"):
            C = [cp.sched[(j, len(r) - 1)] + r[-1][1] for j, r in enumerate(cp.inst.routes)]
            jobs = pd.DataFrame({"Job": [cp.inst.job_name(j) for j in range(cp.inst.n_jobs)],
                                 "Route": [" → ".join(cp.inst.machine_name(m) for m, _ in r) for r in cp.inst.routes],
                                 "Due": [cp.inst.due_of(j) for j in range(cp.inst.n_jobs)],
                                 "Weight": [cp.inst.weight_of(j) for j in range(cp.inst.n_jobs)],
                                 "Completion": C,
                                 "Tardiness": [max(0, c - (cp.inst.due_of(j) or c)) for j, c in enumerate(C)]})
            st.dataframe(jobs, hide_index=True, width="stretch",
                         column_config={"Route": st.column_config.TextColumn(width="medium"), "Tardiness": st.column_config.ProgressColumn("Tardiness (min)", format="%d", min_value=0,
                                                                                    max_value=max(1, int(jobs.Tardiness.max())))})
            plan = pd.DataFrame(to_rows(cp.inst, cp.sched)).drop(columns=["job_idx", "machine_idx"])
            st.download_button("Download plan (CSV)", plan.to_csv(index=False), "plan.csv", "text/csv")
    with right:
        with card("Copilot", "Type what happened, or use a quick command"):
            box = st.container(height=440)
            for role, msg in st.session_state.chat[-14:]:
                box.chat_message(role, avatar="🧑‍🏭" if role == "user" else "🗓️").markdown(msg)
            q1, q2 = st.columns(2)
            for i, ex in enumerate(QUICK):
                if (q1 if i % 2 == 0 else q2).button(ex, key=f"ex{i}", width="stretch"):
                    run(ex)
                    st.rerun()
            cmd = st.chat_input("e.g. Mill down at 120 for 60")
            if cmd:
                run(cmd)
                st.rerun()
        with card("Event log"):
            html(ui.evlog([f"{d}  ·  t = {t}" for d, t in st.session_state.events]))


# ═══════════════════════════════ RULES ════════════════════════════════════
def page_rules():
    rv = S["rules_vs_optimal"]
    share = rv[(rv.objective == "weighted_tardiness") & (rv.method == "CP-SAT")].optimal_share.iloc[0]
    a, b = st.columns(2)
    with a:
        with card("Mean weighted tardiness", "30 order books · lower is better", ui.pill(f"proven optimal {share * 30:.0f}/30 · 10 s limit")):
            plot(charts.rules_bars(rv, "weighted_tardiness", title=None), key="rv_wt")
    with b:
        with card("Mean makespan (min)", "Same books, objective switched to makespan"):
            plot(charts.rules_bars(rv, "makespan", title=None), key="rv_ms")
    html(ui.note("FIFO first come · SPT shortest operation · EDD earliest due date · MWKR most work remaining · CR critical ratio · WSPT weighted shortest processing time"))
    runs = S["rules_vs_optimal_runs"]
    best = rv[(rv.objective == "weighted_tardiness") & (rv.method != "CP-SAT")].sort_values("mean").method.iloc[0]
    with card("Book by book", f"Weighted tardiness per order book · CP-SAT vs the best rule ({best}) and FIFO"):
        plot(charts.dot_range(runs, best), key="rv_books")
    a, b = st.columns(2)
    with a:
        with card("Try it live", "All six rules and CP-SAT on one order book, computed now"):
            seed = st.selectbox("Order book", list(range(1, 31)), key="rule_seed", format_func=lambda s: f"Order book {s}")
            inst, opt = optimal(seed)
            rows = [("CP-SAT", kpis(inst, opt)["weighted_tardiness"])] + [(r, kpis(inst, s)["weighted_tardiness"]) for r, s in all_rules(inst).items()]
            plot(charts.live_rules(rows), key="rv_live")
    with b:
        with card("All runs", "Weighted tardiness per book and method · best per row in bold"):
            p = runs[runs.objective == "weighted_tardiness"].pivot(index="seed", columns="method", values="value")[["CP-SAT"] + list(RULES)]
            st.dataframe(p.style.highlight_min(axis=1, props="font-weight:700;color:#22C98A").format("{:,.0f}"), width="stretch", height=420)


# ═══════════════════════════════ DISRUPTIONS ══════════════════════════════
def page_disruptions():
    ds = S["disruptions"].set_index("method")
    pp = S["disruption_paired"]
    pr = pp.set_index(["from", "to"]).loc[("right_shift", "reoptimize")]
    cards = [ui.kpi(charts.METHOD_LABEL[m], f"{ds.loc[m].weighted_tardiness:,.0f}",
                    f"late jobs {ds.loc[m].late_jobs:.1f} · minutes moved {ds.loc[m].deviation_min:,.0f}",
                    f'<span style="width:9px;height:9px;border-radius:3px;background:{charts.METHOD_COLOR[m]}"></span>')
             for m in charts.METHOD_ORDER]
    cards.append(ui.kpi("Δ weighted tardiness", f"{pr.wt_diff:+,.0f}".replace("-", "−"), f"± {pr.wt_ci:,.0f} · full re-optimisation vs right-shift", ui.pill("95% CI")))
    html(ui.kpis(cards))
    st.write("")
    with card("Three ways to answer a breakdown", f"{int(ds.n.iloc[0])} books, one random breakdown each · mean ± 95% CI"):
        plot(charts.disruption_panels(S["disruptions"]), key="dis_panels")
    a, b = st.columns(2)
    with a:
        with card("Paired differences", "Same books and events for every method · 95% CI · negative is better"):
            plot(charts.forest(pp, "wt"), key="dis_fw")
            plot(charts.forest(pp, "dev"), key="dis_fd")
    with b:
        with card("Stability trade-off", "Penalty weight w on moved minutes · 20 books · each point is one w"):
            stab = S["stability"]
            plot(charts.tradeoff(stab, title=None), key="dis_trade")
            inf = stab[~stab.stability.apply(math.isfinite)]
            if len(inf):
                html(ui.note(f"Not shown: w = ∞ (never move a planned operation) is worse on both axes: weighted tardiness "
                             f"<b>{inf.weighted_tardiness.iloc[0]:,.0f}</b>, minutes moved <b>{inf.deviation_min.iloc[0]:,.0f}</b>."))
    with card("Every disruption run", "Book, broken machine, start and duration, before and after"):
        dr = S["disruption_runs"].copy()
        dr["method"] = dr.method.map(charts.METHOD_LABEL)
        st.dataframe(dr.rename(columns={"seed": "book", "t0": "start", "wt_before": "WT before", "weighted_tardiness": "WT after",
                                        "deviation_min": "minutes moved", "moved_ops": "ops moved",
                                        "late_jobs": "late jobs", "status": "solver status"}), hide_index=True, width="stretch", height=380)


# ═══════════════════════════════ BENCHMARKS ═══════════════════════════════
def page_benchmarks():
    bm = S["benchmarks"].copy()
    bm["best_rule"] = bm[list(RULES)].min(axis=1)
    bm["gap_pct"] = (bm.best_rule / bm.optimum - 1) * 100
    slow = bm.loc[bm.cpsat_seconds.idxmax()]
    html(ui.kpis([ui.kpi("Solved to optimum", f"{int((bm.cpsat == bm.optimum).sum())}<small>/ {len(bm)}</small>", "ft06 · ft10 · la01–05 · la16 · la19 · abz5", ui.pill("OPTIMAL")),
                  ui.kpi("Slowest solve", f"{slow.cpsat_seconds:.1f}<small>s</small>", f"{slow.instance} · {slow['size']}"),
                  ui.kpi("Best-rule gap (mean)", f"{bm.gap_pct.mean():.1f}<small>%</small>", "best of six rules vs optimum", ui.pill("rules", "wn")),
                  ui.kpi("Mean solve time", f"{bm.cpsat_seconds.mean():.1f}<small>s</small>", "CP-SAT · limit 60 s", ui.pill("CP-SAT", "mu"))]))
    st.write("")
    with card("Best rule, % above optimum", "Makespan of the best of six rules vs the published optimum. CP-SAT: 0% on all ten."):
        plot(charts.benchmark_gaps(bm, RULES), key="bm_gap")
    with card("CP-SAT vs published optimum", "Makespan · every instance solved to the known optimum"):
        st.dataframe(bm[["instance", "size", "optimum", "cpsat", "cpsat_seconds", "best_rule", "gap_pct"]].rename(
            columns={"cpsat": "CP-SAT", "cpsat_seconds": "seconds", "best_rule": "best rule", "gap_pct": "best rule % above"}),
            hide_index=True, width="stretch", column_config={"best rule % above": st.column_config.NumberColumn(format="%.1f")})


# ═══════════════════════════════ METHOD ═══════════════════════════════════
def page_method():
    with card("The copilot loop", "LLM proposes, solver decides, checker verifies"):
        html(ui.pipe())
    a, b = st.columns(2)
    with a:
        with card("Decide with optimisation"):
            html('<div class="prose"><ul><li>Plans come from <b>OR-Tools CP-SAT</b> (interval variables, no-overlap per machine, job precedence, '
                 'downtime as fixed intervals) or from <b>dispatching rules</b> inside the Giffler–Thompson active-schedule generator.</li>'
                 '<li>The language model never writes the schedule. Every action is validated and every plan is checked.</li>'
                 '<li><b>Right-shift</b> keeps every machine sequence and pushes work later. <b>Full re-optimisation</b> solves again from now '
                 'with started work frozen. <b>Stable re-optimisation</b> adds a penalty (w = 0.2) on every minute an operation moves.</li></ul></div>')
    with b:
        with card("Limitations"):
            html('<div class="prose"><ul><li>Simulated order books: the size of the gains will differ in a real shop.</li>'
                 '<li>Deterministic shop: no stochastic times, no setups, no alternative machines (classic job shop).</li>'
                 '<li>Stability is measured as minutes moved; other nervousness measures exist.</li>'
                 '<li>The optional LLM path was tested with a mocked endpoint only. The built-in parser understands a fixed English grammar.</li>'
                 f'<li>A static web version (no install) runs the rules, right-shift and checker in the browser, with precomputed CP-SAT plans: <a href="{ui.WEB}">{ui.WEB}</a></li></ul></div>')
    with card("References"):
        html('<div class="prose"><ol>'
             '<li>Giffler, B., &amp; Thompson, G. L. (1960). Algorithms for solving production-scheduling problems. <i>Operations Research</i>, 8(4), 487–503. <a href="https://doi.org/10.1287/opre.8.4.487">doi:10.1287/opre.8.4.487</a></li>'
             '<li>Panwalkar, S. S., &amp; Iskander, W. (1977). A survey of scheduling rules. <i>Operations Research</i>, 25(1), 45–61. <a href="https://doi.org/10.1287/opre.25.1.45">doi:10.1287/opre.25.1.45</a></li>'
             '<li>Baker, K. R. (1984). Sequencing rules and due-date assignments in a job shop. <i>Management Science</i>, 30(9), 1093–1104. <a href="https://doi.org/10.1287/mnsc.30.9.1093">doi:10.1287/mnsc.30.9.1093</a></li>'
             '<li>Vieira, G. E., Herrmann, J. W., &amp; Lin, E. (2003). Rescheduling manufacturing systems: a framework of strategies, policies, and methods. <i>Journal of Scheduling</i>, 6(1), 39–62. <a href="https://doi.org/10.1023/A:1022235519958">doi:10.1023/A:1022235519958</a></li>'
             '<li>Ouelhadj, D., &amp; Petrovic, S. (2009). A survey of dynamic scheduling in manufacturing systems. <i>Journal of Scheduling</i>, 12(4), 417–431. <a href="https://doi.org/10.1007/s10951-008-0090-8">doi:10.1007/s10951-008-0090-8</a></li>'
             '<li>Zhang, L., et al. (2026). DScheLLM: Enabling dynamic scheduling through a fine-tuned dual-system large language model. <a href="https://arxiv.org/abs/2601.09100">arXiv:2601.09100</a></li>'
             '<li>Yan, J., &amp; Ji, S. (2026). Industrial mechanism-aware multi-agent collaboration of large language models for job shop scheduling optimization. <i>Computers &amp; Industrial Engineering</i>, 217, 112079.</li>'
             '<li>Perron, L., &amp; Didier, F. CP-SAT, Google OR-Tools (v9.15). <a href="https://developers.google.com/optimization">developers.google.com/optimization</a></li>'
             '<li>Benchmarks: Fisher &amp; Thompson (1963) in Muth &amp; Thompson, <i>Industrial Scheduling</i>; Lawrence (1984); Adams, Balas &amp; Zawack (1988), <i>Management Science</i>, 34(3), 391–401. Collected in <a href="https://github.com/tamy0612/JSPLIB">JSPLIB</a>.</li>'
             '</ol></div>')


{"Overview": page_overview, "Planner": page_planner, "Rules vs optimal": page_rules, "Disruptions": page_disruptions,
 "Benchmarks": page_benchmarks, "Method & sources": page_method}[page]()
