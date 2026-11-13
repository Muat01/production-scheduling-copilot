"""Plotly figure builders in the MH Emerald & Gold style. Data in, figure out."""
from __future__ import annotations

import math
from typing import Iterable, Optional, Set, Tuple

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from jobshop import Instance, Schedule, completion_times
from theme import (BG, C_EMERALD, C_GOLD, C_ROSE, C_STEEL, CRITICAL, EMERALD, FONT, GOLD, GRID, LINE, MONO,
                   MUTED, STEEL, SURFACE, SURFACE_2, TEXT, TEXT_SOFT)

CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"]}
METHOD_LABEL = {"right_shift": "Right-shift", "reoptimize": "Re-optimise", "stable": "Stable re-optimise"}


def merge(base: dict, over: dict) -> dict:
    """Merge layout dicts one level deep, so no kwarg is passed twice."""
    out = dict(base)
    for k, v in over.items():
        out[k] = {**out[k], **v} if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def base_layout(height: int, title: Optional[str] = None, **over) -> dict:
    lay = dict(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color=TEXT_SOFT, size=12),
        margin=dict(l=64, r=28, t=58 if title else 24, b=52),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=EMERALD, font=dict(family=MONO, size=12, color=TEXT)),
        title=dict(text=f"<b>{title}</b>" if title else "", x=0.01, xanchor="left", font=dict(size=15, color=TEXT, family=FONT)),
        xaxis=dict(gridcolor=GRID, zeroline=False, linecolor=GRID, tickfont=dict(size=11, family=MONO, color=MUTED),
                   title=dict(font=dict(size=12, color=MUTED))),
        yaxis=dict(gridcolor=GRID, zeroline=False, linecolor=GRID, tickfont=dict(size=11, family=MONO, color=MUTED),
                   title=dict(font=dict(size=12, color=MUTED))),
        showlegend=False,
    )
    return merge(lay, over)


# ─── Gantt ────────────────────────────────────────────────────────────────
def gantt(inst: Instance, sched: Schedule, now: Optional[int] = None, changed: Optional[Set[Tuple[int, int]]] = None,
          title: Optional[str] = None, height: Optional[int] = None, prev: Optional[Schedule] = None) -> go.Figure:
    """Machine Gantt chart. Colour = job status (emerald on time, rose late, gold rush), label = job name.
    Started work (before `now`) is dimmed; with `prev`, moved operations show their previous slot as a dashed outline;
    machine downtime is a hatched block; 'now' is a gold line."""
    changed = changed or set()
    C = completion_times(inst, sched)
    machines = [inst.machine_name(m) for m in range(inst.n_machines)]
    groups = {"On time": ([], C_EMERALD), "Late": ([], C_ROSE), "Rush order": ([], C_GOLD)}
    for (j, k), s in sched.items():
        m, p = inst.routes[j][k]
        due = inst.due_of(j)
        late = due is not None and C[j] > due
        status = "Late" if late else ("Rush order" if inst.weight_of(j) >= 5 else "On time")
        groups[status][0].append((j, k, m, s, p, due, C[j]))
    fig = go.Figure()
    if prev:
        ghost = [(k, prev[k]) for k in sched if k in prev and prev[k] != sched[k]]
        for (j, k), s0 in ghost:
            m, p = inst.routes[j][k]
            y = machines[::-1].index(inst.machine_name(m))
            fig.add_shape(type="rect", x0=s0, x1=s0 + p, y0=y - 0.3, y1=y + 0.3, line=dict(color=MUTED, width=1, dash="dot"),
                          fillcolor="rgba(0,0,0,0)", layer="below")
        if ghost:
            fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="Previous slot", line=dict(color=MUTED, dash="dot")))
    for status, (rows, color) in groups.items():
        if not rows:
            continue
        started = [now is not None and r[3] < now for r in rows]
        fig.add_trace(go.Bar(
            y=[inst.machine_name(r[2]) for r in rows], x=[r[4] for r in rows], base=[r[3] for r in rows],
            orientation="h", name=status,
            marker=dict(color=color, opacity=1, cornerradius=5,
                        line=dict(color=[GOLD if (r[0], r[1]) in changed and not prev else BG for r in rows],
                                  width=[2 if (r[0], r[1]) in changed and not prev else 1.5 for r in rows])),
            text=[inst.job_name(r[0]) if r[4] >= 0.035 * max(C) else "" for r in rows], textposition="inside", insidetextanchor="middle",
            textangle=0, textfont=dict(family=MONO, size=11, color="#FFFFFF" if status == "Late" else BG), constraintext="none",
            customdata=[[inst.job_name(r[0]), r[1] + 1, r[3], r[3] + r[4], "–" if r[5] is None else r[5], r[6],
                         "started (frozen)" if f else "planned"] for r, f in zip(rows, started)],
            hovertemplate="<b>%{customdata[0]}</b> · operation %{customdata[1]}<br>%{customdata[2]} → %{customdata[3]} min"
                          "<br>due %{customdata[4]} · done %{customdata[5]}<br>%{customdata[6]}<extra>" + status + "</extra>"))
    for d in inst.downtimes:
        fig.add_trace(go.Bar(y=[inst.machine_name(d.machine)], x=[d.end - d.start], base=[d.start], orientation="h",
                             name="Machine down", marker=dict(color="rgba(240,97,109,0.08)", pattern=dict(shape="/", fgcolor=CRITICAL, size=6),
                                                              line=dict(color=CRITICAL, width=1)),
                             hovertemplate=f"{inst.machine_name(d.machine)} down {d.start}–{d.end} min<extra></extra>",
                             showlegend=not any(t.name == "Machine down" for t in fig.data)))
    if now:
        fig.add_vline(x=now, line=dict(color=GOLD, width=2))
        fig.add_annotation(x=now, y=1.0, yref="paper", text=f"<b>Now {now}</b>", showarrow=False, yanchor="bottom",
                           bgcolor="#B88A26", borderpad=3, font=dict(family=MONO, size=10.5, color=BG))
    cmax = max(C + [d.end for d in inst.downtimes] + ([max(prev[k] + inst.routes[k[0]][k[1]][1] for k in prev if k[0] < inst.n_jobs)] if prev else []))
    fig.update_layout(**base_layout(height or 90 + 44 * inst.n_machines, title, barmode="overlay", bargap=0.3, showlegend=True,
                                    legend=dict(orientation="h", y=-0.16, yanchor="top", x=0, font=dict(size=12, color=TEXT_SOFT)),
                                    margin=dict(l=76, b=84, t=56 if title else 30),
                                    xaxis=dict(title=dict(text="minutes from shift start", standoff=6), range=[0, cmax * 1.03]),
                                    yaxis=dict(type="category", categoryorder="array", categoryarray=machines[::-1], range=[-0.6, inst.n_machines - 0.4], gridcolor="rgba(0,0,0,0)",
                                               tickfont=dict(family=FONT, size=12, color=TEXT_SOFT))))
    # dim started operations: draw a translucent veil over the past
    if now:
        fig.add_vrect(x0=0, x1=now, fillcolor=BG, opacity=0.35, line_width=0, layer="above")
    return fig


# ─── Rules vs optimal ───────────────────────────────────────────────────────
def _vbars(names, values, colors, title, unit, height, fmt="{:,.0f}", ytitle=""):
    fig = go.Figure(go.Bar(
        x=names, y=values, marker=dict(color=colors, cornerradius=6, line=dict(width=0)),
        text=[fmt.format(v) for v in values], textposition="outside", cliponaxis=False,
        textfont=dict(family=MONO, size=12, color=TEXT),
        hovertemplate="%{x}<br>%{y:,.1f} " + unit + "<extra></extra>"))
    fig.update_layout(**base_layout(height, title, bargap=0.38, yaxis=dict(title=dict(text=ytitle), range=[0, max(values) * 1.18]),
                                    xaxis=dict(tickfont=dict(family=MONO, size=12, color=TEXT_SOFT))))
    return fig


def rules_bars(summary: pd.DataFrame, objective: str, height: int = 340, title: Optional[str] = "auto") -> go.Figure:
    """Mean objective per method on the simulated order books: CP-SAT emerald, best rule gold, other rules steel."""
    d = summary[summary.objective == objective].copy()
    d = pd.concat([d[d.method == "CP-SAT"], d[d.method != "CP-SAT"].sort_values("mean")])
    colors = [C_EMERALD if m == "CP-SAT" else (C_GOLD if i == 1 else C_STEEL) for i, m in enumerate(d.method)]
    unit = "min" if objective == "makespan" else "weighted min late"
    if title == "auto":
        title = "Weighted tardiness · mean of 30 order books" if objective != "makespan" else "Makespan · mean of 30 order books"
    return _vbars(list(d.method), list(d["mean"]), colors, title, unit, height, ytitle=unit)


def live_rules(rows: list, height: int = 300) -> go.Figure:
    """rows = [(method, value)], first row is CP-SAT."""
    return _vbars([r[0] for r in rows], [r[1] for r in rows], [C_EMERALD] + [C_STEEL] * (len(rows) - 1), None,
                  "weighted min late", height)


def dot_range(runs: pd.DataFrame, best_rule: str, height: int = 320) -> go.Figure:
    """Per order book: CP-SAT vs the best rule vs FIFO, connected by a range line."""
    p = runs[runs.objective == "weighted_tardiness"].pivot(index="seed", columns="method", values="value")
    cols = [("FIFO", C_STEEL), (best_rule, C_GOLD), ("CP-SAT", C_EMERALD)]
    fig = go.Figure()
    lo, hi = p[[c for c, _ in cols]].min(axis=1), p[[c for c, _ in cols]].max(axis=1)
    xs, ys = [], []
    for s in p.index:
        xs += [s, s, None]
        ys += [lo[s], hi[s], None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=LINE, width=3), hoverinfo="skip", showlegend=False))
    for c, col in cols:
        fig.add_trace(go.Scatter(x=p.index, y=p[c], mode="markers", name=c, marker=dict(size=9, color=col, line=dict(color=SURFACE, width=1.5)),
                                 hovertemplate="book %{x}<br>" + c + " %{y:,.0f}<extra></extra>"))
    fig.update_layout(**base_layout(height, None, showlegend=True, hovermode="x unified",
                                    legend=dict(orientation="h", y=1.04, yanchor="bottom", x=0, font=dict(size=12, color=TEXT_SOFT)),
                                    margin=dict(t=40, b=44),
                                    xaxis=dict(title=dict(text="order book"), dtick=1, range=[0.4, len(p.index) + 0.6], tickfont=dict(size=10.5, family=MONO, color=MUTED)),
                                    yaxis=dict(title=dict(text="weighted tardiness"))))
    return fig


def benchmark_gaps(bench: pd.DataFrame, rules: Iterable[str], height: int = 340) -> go.Figure:
    """Best dispatching rule, % above the published optimal makespan. CP-SAT is 0% on every instance."""
    rules = list(rules)
    d = bench.copy()
    d["best_rule"] = d[rules].min(axis=1)
    d["best_rule_name"] = [" · ".join(r for r in rules if row[r] == row["best_rule"]) for _, row in d.iterrows()]
    d["rule_gap"] = (d["best_rule"] - d["optimum"]) / d["optimum"] * 100
    fig = go.Figure(go.Bar(x=d.instance, y=d.rule_gap, marker=dict(color=C_GOLD, cornerradius=6), name="Best dispatching rule",
                           text=[f"{g:.1f}" for g in d.rule_gap], textposition="outside", cliponaxis=False,
                           textfont=dict(family=MONO, size=12, color=TEXT),
                           customdata=d[["best_rule_name", "best_rule", "optimum"]].values,
                           hovertemplate="%{x}<br>best rule %{customdata[0]}: %{customdata[1]} vs optimum %{customdata[2]}"
                                         "<br>%{y:.1f}% above<extra></extra>"))
    fig.add_hline(y=0, line=dict(color=C_EMERALD, width=2))
    fig.add_annotation(x=1, xref="paper", y=0, text="CP-SAT = 0% on all", showarrow=False, xanchor="right", yanchor="bottom",
                       font=dict(family=MONO, size=11, color=EMERALD))
    fig.update_layout(**base_layout(height, "Best dispatching rule · % above the published optimum", bargap=0.4,
                                    yaxis=dict(title=dict(text="% above optimum"), range=[0, d.rule_gap.max() * 1.2]),
                                    xaxis=dict(tickfont=dict(family=MONO, size=12, color=TEXT_SOFT))))
    return fig


# ─── Disruptions ───────────────────────────────────────────────────────────
METHOD_ORDER = ["right_shift", "reoptimize", "stable"]
METHOD_COLOR = {"right_shift": C_ROSE, "reoptimize": C_STEEL, "stable": C_EMERALD}
METHOD_LABEL = {"right_shift": "Right-shift", "reoptimize": "Full re-optimisation", "stable": "Stable re-optimisation"}


def disruption_panels(ds: pd.DataFrame, height: int = 300) -> go.Figure:
    """Three panels of horizontal bars with 95% CI: weighted tardiness, late jobs, minutes moved."""
    d = ds.set_index("method").loc[[m for m in METHOD_ORDER if m in set(ds.method)]].reset_index()
    names = [METHOD_LABEL[m] for m in d.method]
    panels = [("weighted_tardiness", "Weighted tardiness", "{:,.0f}"), ("late_jobs", "Late jobs", "{:.1f}"),
              ("deviation_min", "Minutes moved", "{:,.0f}")]
    fig = make_subplots(rows=1, cols=3, horizontal_spacing=0.06, shared_yaxes=True, subplot_titles=[p[1] for p in panels])
    for col, (kpi, _, fmt) in enumerate(panels, start=1):
        ci = d[f"{kpi}_ci"].fillna(0)
        fig.add_trace(go.Bar(y=names, x=d[kpi], orientation="h", marker=dict(color=[METHOD_COLOR[m] for m in d.method], cornerradius=5),
                             error_x=dict(type="data", array=ci, color=TEXT, thickness=1.4, width=5),
                             text=[fmt.format(v) for v in d[kpi]], textposition="inside", insidetextanchor="start",
                             textfont=dict(family=MONO, size=12, color=BG), textangle=0,
                             hovertemplate="%{y}<br>%{x:,.1f} ± %{error_x.array:,.1f}<extra></extra>"), row=1, col=col)
        fig.update_xaxes(range=[0, float((d[kpi] + ci).max()) * 1.12], row=1, col=col)
    fig.update_layout(**base_layout(height, None, bargap=0.38, margin=dict(t=40, l=160)))
    fig.update_xaxes(gridcolor=GRID, zeroline=False, tickfont=dict(size=10.5, family=MONO, color=MUTED))
    fig.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)", tickfont=dict(size=12, family=FONT, color=TEXT_SOFT))
    fig.update_annotations(font=dict(size=13, color=TEXT, family=FONT))
    return fig


def forest(paired: pd.DataFrame, metric: str = "wt", height: int = 230) -> go.Figure:
    """Paired differences (to − from) with 95% CI; negative is better."""
    short = {"right_shift": "right-shift", "reoptimize": "full re-opt", "stable": "stable"}
    lab = [f"{short[t].capitalize()} vs {short[f]}" for f, t in zip(paired["from"], paired["to"])]
    v, ci = paired[f"{metric}_diff"], paired[f"{metric}_ci"]
    cols = [C_EMERALD if x < 0 else C_ROSE for x in v]
    fig = go.Figure(go.Scatter(x=v, y=lab, mode="markers+text", cliponaxis=False, marker=dict(size=12, color=cols, line=dict(color=SURFACE, width=2)),
                               error_x=dict(type="data", array=ci, color=MUTED, thickness=3, width=0),
                               text=[f"{x:+,.0f} ± {c:,.0f}" for x, c in zip(v, ci)], textposition="top center",
                               textfont=dict(family=MONO, size=11, color=TEXT),
                               hovertemplate="%{y}<br>%{x:+,.0f} ± %{error_x.array:,.0f}<extra></extra>"))
    fig.add_vline(x=0, line=dict(color=LINE, width=1.5))
    title = "Δ weighted tardiness" if metric == "wt" else "Δ minutes moved"
    lo, hi = float(min(0, (v - ci).min())), float(max(0, (v + ci).max()))
    pad = (hi - lo) * 0.18
    fig.update_layout(**base_layout(height, title, margin=dict(l=170, r=24, t=46, b=36),
                                    yaxis=dict(autorange="reversed", gridcolor="rgba(0,0,0,0)", tickfont=dict(size=12, family=FONT, color=TEXT_SOFT)),
                                    xaxis=dict(zeroline=False, range=[lo - pad, hi + pad])))
    return fig


def tradeoff(st: pd.DataFrame, height: int = 360, title: Optional[str] = "Stability trade-off · gold = w 0.2 used in the app") -> go.Figure:
    """Stability frontier: each point is a move-penalty weight w (mean over scenarios). w = ∞ is left out (worse on both axes)."""
    d = st[st.stability.apply(lambda v: math.isfinite(v))].sort_values("deviation_min")
    d = (d.assign(_k=d.deviation_min.round(1).astype(str) + "|" + d.weighted_tardiness.round(1).astype(str))
         .groupby("_k", sort=False).agg(stability=("stability", lambda w: list(w)), deviation_min=("deviation_min", "first"),
                                         weighted_tardiness=("weighted_tardiness", "first")).reset_index(drop=True))
    labels = ["w = " + " · ".join(f"{w:g}" for w in ws) for ws in d.stability]
    hl = [0.2 in ws for ws in d.stability]
    fig = go.Figure(go.Scatter(x=d.deviation_min, y=d.weighted_tardiness, mode="lines+markers+text",
                               line=dict(color=C_EMERALD, width=2),
                               marker=dict(size=[13 if h else 9 for h in hl], color=[C_GOLD if h else C_EMERALD for h in hl], line=dict(color=SURFACE, width=2)),
                               text=labels, textposition=["top right" if i % 2 == 0 else "bottom right" for i in range(len(labels))],
                               textfont=dict(family=MONO, size=10.5, color=TEXT_SOFT),
                               hovertemplate="moved %{x:,.0f} min<br>weighted tardiness %{y:,.0f}<extra>%{text}</extra>"))
    fig.update_layout(**base_layout(height, title, margin=dict(r=60),
                                    xaxis=dict(title=dict(text="minutes moved (mean)"), range=[d.deviation_min.min() * 0.95, d.deviation_min.max() * 1.08]),
                                    yaxis=dict(title=dict(text="weighted tardiness (mean)"),
                                               range=[d.weighted_tardiness.min() * 0.95, d.weighted_tardiness.max() * 1.05])))
    return fig


def utilization(inst: Instance, util: list, height: int = 260) -> go.Figure:
    names = [inst.machine_name(m) for m in range(inst.n_machines)]
    top = max(range(len(util)), key=lambda i: util[i])
    fig = go.Figure(go.Bar(x=names, y=[u * 100 for u in util],
                           marker=dict(color=[C_GOLD if i == top else C_EMERALD for i in range(len(util))],
                                       line=dict(color=BG, width=2)),
                           text=[f"{u * 100:.0f}%" for u in util], textposition="inside", insidetextanchor="end",
                           textfont=dict(family=MONO, size=12, color=BG),
                           hovertemplate="%{x}<br>%{y:.0f}% busy until makespan<extra></extra>"))
    fig.update_layout(**base_layout(height, "Machine load (gold = bottleneck)", bargap=0.35,
                                    yaxis=dict(range=[0, 105], title=dict(text="% of makespan")),
                                    xaxis=dict(tickfont=dict(family=FONT, size=12, color=TEXT_SOFT))))
    return fig
