"""HTML components and CSS for the MH Emerald & Gold control-room look (Streamlit).

Rule: every HTML snippet is built on one line (indented lines would become a code block in Markdown).
"""
from __future__ import annotations

import html as _html

import streamlit as st

from theme import (BG, BG_2, CRITICAL, EMERALD, GOLD, GRID, LINE, LINE_2, MUTED, ROSE, STEEL,
                   SURFACE, SURFACE_2, TEXT, TEXT_SOFT, TONES)

GITHUB = "https://github.com/Muat01/production-scheduling-copilot"
LINKEDIN = "https://www.linkedin.com/in/muatasem-hadi"
WEB = "https://muat01.github.io/production-scheduling-copilot/"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
:root {{ --bg:{BG}; --bg2:{BG_2}; --card:{SURFACE}; --card2:{SURFACE_2}; --line:{LINE}; --line2:{LINE_2}; --grid:{GRID};
  --ink:{TEXT}; --soft:{TEXT_SOFT}; --mut:{MUTED}; --em:{EMERALD}; --em2:#16A673; --gold:{GOLD}; --gold2:#B88A26;
  --steel:{STEEL}; --rose:{ROSE}; --bad:{CRITICAL}; --emBg:rgba(34,201,138,.10); --goldBg:rgba(230,185,74,.10); --badBg:rgba(240,97,109,.10);
  --f:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif; --fm:'JetBrains Mono',ui-monospace,Consolas,monospace;
  --shadow:0 1px 0 rgba(255,255,255,.03) inset,0 20px 40px -24px rgba(0,0,0,.6); }}
html, body, .stApp, .stMarkdown, button, input, textarea, select {{ font-family:var(--f); }}
.stApp {{ background:var(--bg); background-image:radial-gradient(1200px 500px at 85% -10%,rgba(34,201,138,.10),transparent 60%),radial-gradient(800px 400px at 0% 0%,rgba(230,185,74,.05),transparent 60%); background-attachment:fixed; }}
header[data-testid="stHeader"] {{ background:transparent; }}
.block-container {{ padding-top:1.6rem; padding-bottom:4rem; max-width:1400px; }}
h1, h2, h3, h4, h5 {{ font-family:var(--f); letter-spacing:-.01em; color:var(--ink); }}
code {{ font-family:var(--fm); }}
.n {{ font-family:var(--fm); font-variant-numeric:tabular-nums; letter-spacing:-.01em; }}

/* sidebar */
section[data-testid="stSidebar"] {{ background:var(--bg2); border-right:1px solid var(--line); }}
section[data-testid="stSidebar"] .block-container, section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{ padding-top:1.2rem; }}
.brand {{ display:flex; align-items:center; gap:12px; padding:2px 4px 16px; }}
.mark {{ width:42px; height:42px; border-radius:12px; background:var(--em2); display:grid; place-items:center; position:relative; flex:none; box-shadow:0 8px 24px -10px rgba(22,166,115,.7); }}
.mark b {{ font:800 15px/1 var(--f); color:#0B100E; letter-spacing:-.02em; margin-top:-3px; }}
.mark:after {{ content:""; position:absolute; left:10px; right:10px; bottom:7px; height:3px; border-radius:2px; background:#E6B94A; }}
.brand strong {{ display:block; font-size:13.5px; letter-spacing:.02em; color:var(--ink); }}
.brand span {{ display:block; font:600 10px/1.4 var(--fm); letter-spacing:.14em; text-transform:uppercase; color:var(--mut); }}
.navlbl {{ font:600 10px var(--fm); letter-spacing:.18em; text-transform:uppercase; color:var(--mut); padding:6px 4px 4px; }}
section[data-testid="stSidebar"] [role="radiogroup"] {{ gap:3px; }}
section[data-testid="stSidebar"] [role="radiogroup"] label {{ width:100%; padding:9px 12px; border-radius:12px; margin:0; transition:background .15s; cursor:pointer; }}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background:var(--card); }}
section[data-testid="stSidebar"] [role="radiogroup"] label {{ display:flex !important; }}
section[data-testid="stSidebar"] [role="radiogroup"] label > div > div:first-child {{ display:none; }}
section[data-testid="stSidebar"] [role="radiogroup"] label p {{ font-size:14.5px; color:var(--soft); font-weight:500; }}
section[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] {{ background:var(--card); box-shadow:var(--shadow), inset 3px 0 0 var(--em); }}
section[data-testid="stSidebar"] [role="radiogroup"] label[data-selected="true"] p {{ color:var(--ink); font-weight:600; }}
.simcard {{ border:1px dashed color-mix(in srgb,var(--gold) 45%,var(--line)); background:var(--goldBg); border-radius:14px; padding:12px 14px; margin-top:18px; }}
.simcard b {{ display:flex; align-items:center; gap:8px; font-size:12.5px; color:var(--gold); }}
.simcard b:before {{ content:""; width:7px; height:7px; border-radius:50%; background:var(--gold); box-shadow:0 0 0 4px rgba(230,185,74,.18); }}
.simcard span {{ display:block; font-size:11.5px; color:var(--soft); margin-top:4px; line-height:1.5; }}
.byline {{ font-size:11.5px; color:var(--mut); padding:14px 4px 0; line-height:1.6; }}
.byline b {{ color:var(--soft); font-weight:600; }} .byline a {{ color:var(--em); text-decoration:none; }}

/* top bar */
.top {{ display:flex; align-items:flex-end; justify-content:space-between; gap:14px; padding:0 0 14px; margin-bottom:18px; border-bottom:1px solid var(--line); }}
.top small {{ display:block; font-size:12px; color:var(--mut); }}
.top h1 {{ margin:2px 0 0; padding:0; font-size:22px; font-weight:700; letter-spacing:-.02em; }}
.top .meta {{ font-size:12px; color:var(--mut); white-space:nowrap; }} .top .meta b {{ color:var(--ink); font-weight:600; }}

/* cards: bordered containers */
div[data-testid="stVerticalBlockBorderWrapper"], div[data-testid="stVerticalBlock"][class*="border"] {{ border-radius:18px !important; }}
div[data-testid="stVerticalBlock"]:has(> div[data-testid="stElementContainer"] .card-h) {{ background:var(--card); border-color:var(--line) !important; box-shadow:var(--shadow); }}
.card-h h3 {{ margin:0; padding:0; font-size:15px; font-weight:650; color:var(--ink); }}
.card-h .sub {{ font-size:12.5px; color:var(--mut); margin:3px 0 10px; }}
.card-h {{ display:flex; justify-content:space-between; align-items:flex-start; gap:12px; margin-bottom:8px; }}

/* hero */
.hero {{ position:relative; overflow:hidden; border-radius:24px; padding:28px 30px 24px; margin-bottom:18px; border:1px solid var(--line);
  background:radial-gradient(900px 300px at 100% 0%,rgba(34,201,138,.12),transparent 60%),linear-gradient(180deg,var(--card),var(--bg2)); box-shadow:var(--shadow); }}
.hero .lanes {{ position:absolute; right:28px; top:26px; display:flex; flex-direction:column; gap:7px; opacity:.9; }}
.hero .lanes i {{ display:block; height:6px; border-radius:4px; }}
.eyebrow {{ font:600 10.5px var(--fm); letter-spacing:.16em; text-transform:uppercase; color:var(--mut); }}
.hero h2 {{ margin:10px 0 0; padding:0; font-size:clamp(22px,2.4vw,32px); line-height:1.25; font-weight:700; letter-spacing:-.025em; max-width:calc(100% - 190px); }}
.hero h2 em {{ font-style:normal; color:var(--em); }} .hero h2 strong {{ color:var(--gold); }}
.hero p.lead {{ color:var(--soft); max-width:820px; margin:10px 0 20px; font-size:14px; }}
.kpis {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; }}
.kpi {{ background:color-mix(in srgb,var(--card) 70%,transparent); border:1px solid var(--line); border-radius:16px; padding:14px 16px; height:100%; }}
.kpi .lbl {{ font-size:12px; color:var(--mut); display:flex; justify-content:space-between; gap:8px; align-items:center; }}
.kpi .val {{ font:700 clamp(22px,2.2vw,32px)/1.1 var(--fm); letter-spacing:-.03em; margin:10px 0 6px; white-space:nowrap; color:var(--ink); }}
.kpi .val small {{ font:600 13px var(--f); color:var(--mut); margin-left:4px; letter-spacing:0; }}
.kpi .cmp {{ font-size:12px; color:var(--soft); }}
.pill {{ display:inline-flex; align-items:center; gap:6px; font:600 11px var(--fm); padding:3px 8px; border-radius:999px; white-space:nowrap; }}
.pill.ok {{ background:var(--emBg); color:var(--em); }} .pill.bad {{ background:var(--badBg); color:var(--bad); }}
.pill.wn {{ background:var(--goldBg); color:var(--gold); }} .pill.mu {{ background:var(--card2); color:var(--mut); border:1px solid var(--line); }}

/* KPI strip */
.kstrip {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(122px,1fr)); gap:8px; margin:0 0 10px; }}
.kstrip > div {{ border:1px solid var(--line); border-radius:12px; padding:9px 11px; background:var(--card2); min-width:0; }}
.kstrip span.l {{ display:block; font-size:11px; color:var(--mut); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.kstrip b {{ display:flex; align-items:center; gap:6px; font:700 17px/1.3 var(--fm); margin-top:2px; white-space:nowrap; color:var(--ink); }}
.kstrip b.okc {{ font:600 12px/1.6 var(--f); color:var(--em); white-space:normal; }} .kstrip b.badc {{ font:600 12px/1.6 var(--f); color:var(--bad); white-space:normal; }}
.kstrip .pill {{ margin-top:4px; font-size:10px; padding:1px 6px; }}
.src {{ display:inline-flex; align-items:center; gap:8px; font-size:12px; font-weight:600; padding:5px 10px; border-radius:999px; margin:0 0 6px; border:1px solid var(--line); }}
.src.pre {{ background:var(--emBg); color:var(--em); }} .src.live {{ background:var(--goldBg); color:var(--gold); }}
.lg {{ display:flex; flex-wrap:wrap; gap:6px 16px; font-size:12px; color:var(--soft); margin:2px 0 0; }}
.lg span {{ display:inline-flex; align-items:center; gap:7px; }} .lg i {{ width:14px; height:3px; border-radius:2px; display:inline-block; }}
.lg i.d {{ height:0; border-top:2px dashed; }}

/* story steps, pipeline, insights */
.steps {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:6px 0 12px; }}
.step {{ display:flex; gap:12px; align-items:flex-start; padding:12px 14px; border:1px solid var(--line); border-radius:14px; background:var(--card2); }}
.step.on {{ border-color:color-mix(in srgb,var(--gold) 55%,var(--line)); background:var(--goldBg); }}
.step .sn {{ flex:none; width:26px; height:26px; border-radius:8px; display:grid; place-items:center; background:var(--card); border:1px solid var(--line); font:700 12px var(--fm); color:var(--ink); }}
.step.on .sn {{ background:var(--gold2); color:#0B100E; border-color:var(--gold2); }}
.step b {{ display:block; font-size:13px; color:var(--ink); }} .step small {{ display:block; font-size:11.5px; color:var(--mut); line-height:1.5; margin-top:2px; }}
.pipe {{ list-style:none; margin:4px 0 0; padding:0; display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:10px; }}
.pipe li {{ position:relative; border:1px solid var(--line); border-radius:14px; padding:12px; background:var(--card2); margin:0; }}
.pipe li:not(:last-child):after {{ content:""; position:absolute; top:24px; right:-10px; width:10px; height:2px; background:var(--em2); }}
.pipe .pn {{ display:inline-grid; place-items:center; width:24px; height:24px; border-radius:7px; background:var(--em2); color:#0B100E; font:700 12px var(--fm); }}
.pipe b {{ display:block; margin:8px 0 3px; font-size:13px; color:var(--ink); }} .pipe small {{ display:block; font-size:11.5px; line-height:1.5; color:var(--mut); }}
.cmdex {{ display:flex; flex-wrap:wrap; align-items:center; gap:8px; margin-top:14px; font-size:12px; color:var(--mut); }}
.cmdex code {{ font:500 11.5px var(--fm); padding:4px 8px; border-radius:8px; background:var(--card2); border:1px solid var(--line); color:var(--soft); }}
.ins {{ list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:12px; }}
.ins li {{ display:flex; gap:10px; font-size:13px; color:var(--soft); line-height:1.6; margin:0; }}
.ins i {{ flex:none; width:4px; border-radius:2px; }} .ins b {{ color:var(--ink); }}
.note {{ display:flex; gap:10px; align-items:flex-start; padding:11px 14px; border-radius:12px; border:1px solid color-mix(in srgb,var(--steel) 30%,var(--line)); background:rgba(111,168,255,.06); font-size:12.5px; color:var(--soft); line-height:1.55; margin:4px 0 12px; }}
.note.w {{ border-color:color-mix(in srgb,var(--gold) 35%,var(--line)); background:var(--goldBg); }}
.note b {{ color:var(--ink); }}
.prose ul, .prose ol {{ margin:6px 0 0; padding-left:18px; }} .prose li {{ color:var(--soft); font-size:13.5px; line-height:1.6; margin-bottom:6px; }}
.prose a {{ color:var(--em); }} .prose h4 {{ font-size:14px; margin:0 0 6px; }}
.evlog {{ list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:8px; }}
.evlog li {{ display:flex; align-items:center; gap:10px; font-size:13px; padding:8px 10px; border:1px solid var(--line); border-radius:12px; background:var(--card2); color:var(--soft); margin:0; }}
.evlog .pn {{ flex:none; width:22px; height:22px; border-radius:7px; display:grid; place-items:center; background:var(--gold2); color:#0B100E; font:700 11px var(--fm); }}
.empty {{ display:grid; place-items:center; min-height:80px; color:var(--mut); font-size:13px; text-align:center; border:1px dashed var(--line2); border-radius:14px; }}

/* widgets */
.stButton > button, .stDownloadButton > button {{ border-radius:999px; border:1px solid var(--line); background:var(--card2); color:var(--soft); font-size:12.5px; padding:4px 12px; min-height:34px; }}
.stButton > button:hover {{ border-color:var(--em2); color:var(--ink); }}
.stButton > button[kind="primary"] {{ background:var(--em2); border-color:var(--em2); color:#0B100E; font-weight:600; }}
[data-testid="stChatMessage"] {{ background:var(--card2); border:1px solid var(--line); border-radius:14px; padding:10px 12px; }}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li, [data-testid="stChatMessage"] td, [data-testid="stChatMessage"] th {{ font-size:13px; line-height:1.55; }}
.stButton > button p {{ font-size:12px; white-space:normal; line-height:1.3; }}
[data-testid="stChatInput"] {{ border-radius:12px; }}
[data-baseweb="select"] > div, [data-baseweb="input"] {{ border-radius:12px !important; }}
[data-testid="stDataFrame"] {{ border:1px solid var(--line); border-radius:14px; overflow:hidden; }}
[data-testid="stSegmentedControl"] button p, [data-testid="stButtonGroup"] button p {{ font-size:12.5px; }}
@media (max-width:1100px) {{ .kpis {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .pipe {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .pipe li:after {{ display:none; }} .steps {{ grid-template-columns:1fr; }} .hero .lanes {{ display:none; }} }}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def esc(s) -> str:
    return _html.escape(str(s))


def n(x) -> str:
    """Number in the mono figure font."""
    return f'<span class="n">{x}</span>'


def sidebar_brand() -> None:
    st.sidebar.markdown('<div class="brand"><div class="mark"><b>MH</b></div><div><strong>SCHEDULING COPILOT</strong><span>Control room</span></div></div><div class="navlbl">Workspace</div>', unsafe_allow_html=True)


def sidebar_foot() -> None:
    st.sidebar.markdown('<div class="simcard"><b>Simulated data</b><span>Order books, times, due dates and weights are illustrative. Benchmarks are public instances.</span></div>'
                        f'<div class="byline">Designed &amp; built by <b>Muatasem Hadi</b><br>MEng Industrial Engineering · Telkom University<br><a href="{GITHUB}">Source code</a> · <a href="{LINKEDIN}">LinkedIn</a> · <a href="{WEB}">Web version</a></div>', unsafe_allow_html=True)


def topbar(crumb: str, title: str, meta: str = "") -> None:
    st.markdown(f'<div class="top"><div><small>{esc(crumb)}</small><h1>{esc(title)}</h1></div><div class="meta">{meta}</div></div>', unsafe_allow_html=True)


def card_head(title: str, sub: str = "", right: str = "") -> None:
    s = f'<div class="sub">{sub}</div>' if sub else ""
    st.markdown(f'<div class="card-h"><div><h3>{esc(title)}</h3>{s}</div>{right}</div>', unsafe_allow_html=True)


def kpi(label: str, value: str, cmp: str = "", pill: str = "") -> str:
    return f'<div class="kpi"><div class="lbl"><span>{esc(label)}</span>{pill}</div><div class="val">{value}</div><div class="cmp">{cmp or "&nbsp;"}</div></div>'


def pill(text: str, tone: str = "ok") -> str:
    return f'<span class="pill {tone}">{esc(text)}</span>'


def kpis(items: list[str]) -> str:
    return f'<div class="kpis">{"".join(items)}</div>'


def hero(eyebrow: str, title_html: str, lead: str, kpi_html: str) -> None:
    lanes = "".join(f'<i style="width:{w}px;background:{c};margin-left:{o}px"></i>'
                    for w, c, o in [(90, "#16A673", 0), (60, "#4F86E0", 30), (120, "#B88A26", 12), (40, "#16A673", 70), (75, "#D05A74", 20)])
    st.markdown(f'<section class="hero"><div class="lanes">{lanes}</div><div class="eyebrow">{esc(eyebrow)}</div><h2>{title_html}</h2><p class="lead">{lead}</p>{kpi_html}</section>', unsafe_allow_html=True)


def kstrip(k: dict, before: dict | None, moved_ops: int, moved_min: int, violations: int) -> str:
    def delta(a, b):
        if b is None or a == b:
            return ""
        return f'<span class="pill {"ok" if a < b else "bad"}">{"+" if a > b else "−"}{abs(a - b):,.0f}</span>'
    cells = []
    for lbl, key in (("Weighted tardiness", "weighted_tardiness"), ("Late jobs", "late_jobs"), ("Makespan", "makespan")):
        v = k.get(key, 0)
        cells.append(f'<div><span class="l">{lbl}</span><b>{n(f"{v:,.0f}")}</b>{delta(v, before.get(key) if before else None)}</div>')
    cells.append(f'<div><span class="l">Operations moved</span><b>{n(moved_ops)}</b></div>')
    cells.append(f'<div><span class="l">Minutes moved</span><b>{n(f"{moved_min:,}")}</b></div>')
    chk = '<b class="badc">' + f"{violations} violations</b>" if violations else '<b class="okc">✓ feasible · 0 violations</b>'
    cells.append(f'<div><span class="l">Checker</span>{chk}</div>')
    return f'<div class="kstrip">{"".join(cells)}</div>'


def legend(items: list[tuple[str, str, bool]]) -> str:
    return '<div class="lg">' + "".join(f'<span><i class="{"d" if d else ""}" style="background:{"transparent" if d else c};border-color:{c}"></i>{esc(t)}</span>' for t, c, d in items) + "</div>"


def steps(items: list[tuple[str, str]], active: int) -> str:
    return '<div class="steps">' + "".join(f'<div class="step {"on" if i == active else ""}"><span class="sn">{i + 1}</span><span><b>{esc(a)}</b><small>{esc(b)}</small></span></div>' for i, (a, b) in enumerate(items)) + "</div>"


PIPE = [("Understand", "Rule-based parser (offline) or an optional LLM turns words into an action"),
        ("Validate", "Machine and job exist? Times sensible? Bad actions are rejected"),
        ("Decide", "CP-SAT re-plans from now, frozen past, optional stability penalty"),
        ("Verify", "Independent checker: precedence, overlaps, downtime, releases"),
        ("Explain", "What changed, in numbers: tardiness, late jobs, moved work")]


def pipe() -> str:
    return '<ol class="pipe">' + "".join(f'<li><span class="pn">{i + 1}</span><b>{a}</b><small>{b}</small></li>' for i, (a, b) in enumerate(PIPE)) + "</ol>"


def insights(items: list[tuple[str, str]]) -> str:
    return '<ul class="ins">' + "".join(f'<li><i style="background:{c}"></i><span>{t}</span></li>' for t, c in items) + "</ul>"


def note(text_html: str, warn: bool = False) -> str:
    return f'<div class="note {"w" if warn else ""}">{"⚠" if warn else "ⓘ"}&nbsp;<span>{text_html}</span></div>'


def evlog(items: list[str]) -> str:
    if not items:
        return '<div class="empty">No events yet. The plan is the optimal base plan.</div>'
    return '<ol class="evlog">' + "".join(f'<li><span class="pn">{i + 1}</span><span>{esc(x)}</span></li>' for i, x in enumerate(items)) + "</ol>"
