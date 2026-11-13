"""Plotly figure builders in the MH Emerald & Gold style. Data in, figure out."""
from __future__ import annotations

import math
from typing import Iterable, Optional, Set, Tuple

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from jobshop import Instance, Schedule, completion_times
from theme import (BG, C_EMERALD, C_GOLD, C_STEEL, CRITICAL, EMERALD, FONT, GOLD, GRID, LINE, MONO,
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


# ─── Gantt ──────────────────────────────────────────────────────────────────
def gantt(inst: Instance, sched: Schedule, now: Optional[int] = None, changed: Optional[Set[Tuple[int, int]]] = None,
          title: Optional[str] = None, height: Optional[int] = None) -> go.Figure:
    """Machine Gantt chart. Colour = job status (on time / late / rush), label = job name.
    Moved operations get a steel outline; machine downtime is a hatched block; 'now' is a gold line."""
    changed = changed or set()
    C = completion_times(inst, sched)
    machines = [inst.machine_name(m) for m in range(inst.n_machines)]
    groups = {"On time": ([], C_EMERALD), "Late": ([], CRITICAL), "Rush order": ([], C_GOLD)}
    for (j, k), s in sched.items():
        m, p = inst.routes[j][k]
        due = inst.due_of(j)
        late = due is not None and C[j] > due
        status = "Rush order" if inst.weight_of(j) >= 5 else ("Late" if late else "On time")
        groups[status][0].append((j, k, m, s, p, due, C[j]))
    fig = go.Figure()
    for status, (rows, color) in groups.items():
        if not rows:
            continue
        fig.add_trace(go.Bar(
            y=[inst.machine_name(r[2]) for r in rows], x=[r[4] for r in rows], base=[r[3] for r in rows],
            orientation="h", name=status,
            marker=dict(color=color, line=dict(color=[STEEL if (r[0], r[1]) in changed else BG for r in rows],
                                               width=[2.5 if (r[0], r[1]) in changed else 1.5 for r in rows])),
            text=[inst.job_name(r[0]) for r in rows], textposition="inside", insidetextanchor="middle",
            textfont=dict(family=MONO, size=11, color=BG), constraintext="both",
            customdata=[[inst.job_name(r[0]), r[1] + 1, r[3], r[3] + r[4], "–" if r[5] is None else r[5], r[6]] for r in rows],
            hovertemplate="%{customdata[0]} · op %{customdata[1]}<br>%{customdata[2]}–%{customdata[3]} min"
                          "<br>job due %{customdata[4]} · done %{customdata[5]}<extra>" + status + "</extra>"))
    for d in inst.downtimes:
        fig.add_trace(go.Bar(y=[inst.machine_name(d.machine)], x=[d.end - d.start], base=[d.start], orientation="h",
                             name="Machine down", marker=dict(color=SURFACE_2, pattern=dict(shape="/", fgcolor=CRITICAL, size=6),
                                                              line=dict(color=CRITICAL, width=1)),
                             hovertemplate=f"{inst.machine_name(d.machine)} down {d.start}–{d.end} min<extra></extra>",
                             showlegend=not any(t.name == "Machine down" for t in fig.data)))
    if now:
        fig.add_vline(x=now, line=dict(color=GOLD, width=2, dash="dash"))
        fig.add_annotation(x=now, y=1.0, yref="paper", text=f"now {now}", showarrow=False, yanchor="bottom",
                           font=dict(family=MONO, size=11, color=GOLD))
    cmax = max(C)
    fig.update_layout(**base_layout(height or 90 + 46 * inst.n_machines, title, barmode="overlay", bargap=0.28, showlegend=True,
                                    legend=dict(orientation="h", y=-0.16 if inst.n_machines > 3 else -0.3, x=0,
                                                font=dict(size=12, color=TEXT_SOFT)),
                                    margin=dict(l=84, b=70),
                                    xaxis=dict(title=dict(text="minutes from shift start"), range=[0, cmax * 1.03]),
                                    yaxis=dict(categoryorder="array", categoryarray=machines[::-1], gridcolor="rgba(0,0,0,0)",
                                               tickfont=dict(family=FONT, size=12, color=TEXT_SOFT))))
    return fig


# ─── Rules vs optimal ───────────────────────────────────────────────────────
def rules_bars(summary: pd.DataFrame, objective: str, height: int = 360) -> go.Figure:
    """Mean objective per method on the simulated order books. CP-SAT highlighted in emerald."""
    d = summary[summary.objective == objective].copy()
    d = pd.concat([d[d.method == "CP-SAT"], d[d.method != "CP-SAT"].sort_values("mean")])
    colors = [C_EMERALD if m == "CP-SAT" else SURFACE_2 for m in d.method]
    edge = [C_EMERALD if m == "CP-SAT" else MUTED for m in d.method]
    unit = "min" if objective == "makespan" else "weighted min late"
    fig = go.Figure(go.Bar(
        x=d.method, y=d["mean"], marker=dict(color=colors, line=dict(color=edge, width=1.2)),
        text=[f"{v:.0f}" for v in d["mean"]], textposition="outside", cliponaxis=False,
        textfont=dict(family=MONO, size=12, color=TEXT),
        hovertemplate="%{x}<br>mean %{y:.0f} " + unit + "<extra></extra>"))
    title = "Weighted tardiness · mean of 30 order books" if objective != "makespan" else "Makespan · mean of 30 order books"
    fig.update_layout(**base_layout(height, title, bargap=0.38, yaxis=dict(title=dict(text=unit), range=[0, d["mean"].max() * 1.18]),
                                    xaxis=dict(tickfont=dict(family=MONO, size=12, color=TEXT_SOFT))))
    return fig


def benchmark_gaps(bench: pd.DataFrame, rules: Iterable[str], height: int = 360) -> go.Figure:
    """Gap to the published optimum: best dispatching rule vs CP-SAT, per benchmark instance."""
    rules = list(rules)
    d = bench.copy()
    d["best_rule"] = d[rules].min(axis=1)
    d["best_rule_name"] = d[rules].idxmin(axis=1)
    d["rule_gap"] = (d["best_rule"] - d["optimum"]) / d["optimum"] * 100
    d["cpsat_gap"] = (d["cpsat"] - d["optimum"]) / d["optimum"] * 100
    fig = go.Figure()
    fig.add_trace(go.Bar(y=d.instance, x=d.rule_gap, orientation="h", name="Best dispatching rule",
                         marker=dict(color=C_STEEL, line=dict(color=BG, width=2)),
                         text=[f"{g:.1f}% ({n})" for g, n in zip(d.rule_gap, d.best_rule_name)], textposition="outside",
                         cliponaxis=False, textfont=dict(family=MONO, size=11, color=TEXT_SOFT),
                         hovertemplate="%{y}<br>best rule %{x:.1f}% above optimum<extra></extra>"))
    fig.add_trace(go.Scatter(y=d.instance, x=d.cpsat_gap, mode="markers", name="CP-SAT",
                             marker=dict(symbol="diamond", size=12, color=C_EMERALD, line=dict(color=BG, width=2)),
                             hovertemplate="%{y}<br>CP-SAT %{x:.1f}% above optimum<extra></extra>"))
    fig.update_layout(**base_layout(height, "Gap to the published optimal makespan (%)", showlegend=True,
                                    legend=dict(orientation="h", y=-0.18, x=0, font=dict(size=12, color=TEXT_SOFT)),
                                    margin=dict(l=70, r=110, b=70),
                                    xaxis=dict(title=dict(text="% above optimum"), range=[-1, d.rule_gap.max() * 1.3]),
                                    yaxis=dict(autorange="reversed", gridcolor="rgba(0,0,0,0)",
                                               tickfont=dict(family=MONO, size=12, color=TEXT_SOFT))))
    return fig


# ─── Disruptions ────────────────────────────────────────────────────────────
def disruption_panels(ds: pd.DataFrame, height: int = 380) -> go.Figure:
    order = ["right_shift", "reoptimize", "stable"]
    d = ds.set_index("method").loc[[m for m in order if m in set(ds.method)]].reset_index()
    names = [METHOD_LABEL[m] for m in d.method]
    colors = [C_STEEL, C_EMERALD, C_GOLD][: len(d)]
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.14,
                        subplot_titles=("Weighted tardiness after repair", "Schedule changes (minutes moved)"))
    for col, kpi, fmt in ((1, "weighted_tardiness", ".0f"), (2, "deviation_min", ".0f")):
        ci = d[f"{kpi}_ci"].fillna(0)
        fig.add_trace(go.Bar(x=names, y=d[kpi], marker=dict(color=colors, line=dict(color=BG, width=2)),
                             error_y=dict(type="data", array=ci, color=TEXT_SOFT, thickness=1.3, width=6),
                             text=[f"{v:{fmt}}" for v in d[kpi]], textposition="inside", insidetextanchor="start",
                             textfont=dict(family=MONO, size=13, color=BG), textangle=0,
                             hovertemplate="%{x}<br>%{y:.0f} ± %{error_y.array:.0f}<extra></extra>"), row=1, col=col)
        fig.update_yaxes(range=[0, float((d[kpi] + ci).max()) * 1.15], row=1, col=col)
    fig.update_layout(**base_layout(height, None, bargap=0.36, margin=dict(t=48)))
    fig.update_xaxes(gridcolor=GRID, linecolor=GRID, tickfont=dict(size=12, family=FONT, color=TEXT_SOFT))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont=dict(size=11, family=MONO, color=MUTED))
    fig.update_annotations(font=dict(size=13, color=TEXT, family=FONT))
    return fig


def tradeoff(st: pd.DataFrame, height: int = 400) -> go.Figure:
    """Performance vs stability: each point is a move-penalty weight (mean over scenarios)."""
    d = st.sort_values("deviation_min", ascending=False)
    finite = d[d.stability.apply(lambda v: math.isfinite(v))]
    rs = d[~d.stability.apply(lambda v: math.isfinite(v))]
    # merge weights that gave the same mean point, so labels never overlap
    finite = (finite.assign(_k=finite.deviation_min.round(1).astype(str) + "|" + finite.weighted_tardiness.round(1).astype(str))
              .groupby("_k", sort=False).agg(stability=("stability", lambda w: list(w)), deviation_min=("deviation_min", "first"),
                                             weighted_tardiness=("weighted_tardiness", "first")).reset_index(drop=True))
    labels = ["w = 0 (full re-opt)" if ws == [0] else "w = " + "–".join(f"{w:g}" for w in (ws if len(ws) < 3 else [ws[0], ws[-1]]))
              for ws in finite.stability]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=finite.deviation_min, y=finite.weighted_tardiness, mode="lines+markers+text",
                             line=dict(color=C_EMERALD, width=2), marker=dict(size=9, color=C_EMERALD, line=dict(color=BG, width=2)),
                             text=labels, textposition=["top center" if i % 2 == 0 else "bottom center" for i in range(len(labels))],
                             textfont=dict(family=MONO, size=10.5, color=TEXT_SOFT),
                             name="Stable re-optimisation",
                             hovertemplate="moved %{x:.0f} min<br>weighted tardiness %{y:.0f}<extra>%{text}</extra>"))
    if len(rs):
        fig.add_trace(go.Scatter(x=rs.deviation_min, y=rs.weighted_tardiness, mode="markers+text", name="Right-shift",
                                 marker=dict(size=12, symbol="square", color=C_STEEL, line=dict(color=BG, width=2)),
                                 text=["right-shift"], textposition="bottom left", textfont=dict(family=MONO, size=10.5, color=TEXT_SOFT),
                                 hovertemplate="moved %{x:.0f} min<br>weighted tardiness %{y:.0f}<extra>right-shift</extra>"))
    fig.update_layout(**base_layout(height, "Performance vs stability after a breakdown", showlegend=False,
                                    margin=dict(r=40),
                                    xaxis=dict(title=dict(text="schedule changes · minutes moved (mean)"),
                                               range=[d.deviation_min.min() * 0.92, d.deviation_min.max() * 1.06]),
                                    yaxis=dict(title=dict(text="weighted tardiness (mean)"))))
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
