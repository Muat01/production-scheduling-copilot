"""HTML components and CSS for the MH Emerald & Gold look (Streamlit)."""
from __future__ import annotations

import html as _html

import streamlit as st

from theme import (BG, CRITICAL, EMERALD, GOLD, LINE, MUTED, ON_EMERALD, STEEL,
                   SURFACE, SURFACE_2, TEXT, TEXT_SOFT, TONES)

GITHUB = "https://github.com/Muat01/production-scheduling-copilot"
LINKEDIN = "https://www.linkedin.com/in/muatasem-hadi"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');
:root {{ --bg:{BG}; --surface:{SURFACE}; --surface2:{SURFACE_2}; --line:{LINE}; --text:{TEXT}; --soft:{TEXT_SOFT};
  --muted:{MUTED}; --emerald:{EMERALD}; --gold:{GOLD}; --steel:{STEEL}; --critical:{CRITICAL};
  --sans:'Inter',system-ui,sans-serif; --mono:'JetBrains Mono',ui-monospace,monospace; }}
html, body, [class*="css"], .stApp, .stMarkdown, button, input, textarea {{ font-family: var(--sans); }}
.stApp {{ background: var(--bg); }}
.block-container {{ padding-top: 2.2rem; max-width: 1280px; }}
section[data-testid="stSidebar"] {{ background: var(--surface); border-right: 1px solid var(--line); }}
h1, h2, h3, h4, h5 {{ font-family: var(--sans); letter-spacing: -0.01em; color: var(--text); }}
code, .mono {{ font-family: var(--mono); }}

/* brand */
.brand {{ display:flex; align-items:center; gap:12px; margin: 4px 0 18px; }}
.brand-mark {{ width:42px; height:42px; border-radius:10px; background:var(--emerald); color:{ON_EMERALD};
  display:flex; align-items:center; justify-content:center; font-weight:800; font-size:17px; position:relative; }}
.brand-mark:after {{ content:""; position:absolute; left:9px; right:9px; bottom:6px; height:3px; border-radius:2px; background:var(--gold); }}
.brand-name {{ font-weight:700; color:var(--text); font-size:15px; line-height:1.15; }}
.brand-sub {{ font-family:var(--mono); font-size:10.5px; letter-spacing:.16em; color:var(--muted); text-transform:uppercase; }}

/* hero */
.hero-eyebrow {{ font-family:var(--mono); font-size:11.5px; letter-spacing:.2em; color:var(--emerald); text-transform:uppercase; }}
.hero-eyebrow:before {{ content:""; display:inline-block; width:28px; height:2px; background:var(--gold); margin-right:12px; vertical-align:middle; }}
.hero-title {{ font-size:2.6rem; font-weight:800; color:var(--text); letter-spacing:-0.02em; margin:.35rem 0 .4rem; line-height:1.08; }}
.hero-title span {{ color:var(--emerald); }}
.hero-sub {{ color:var(--soft); font-size:1.02rem; max-width:860px; line-height:1.55; }}
.pills {{ display:flex; flex-wrap:wrap; gap:8px; margin:14px 0 6px; }}
.pill {{ font-size:12.5px; padding:5px 12px; border-radius:999px; border:1px solid var(--line); color:var(--soft); background:var(--surface); }}
.pill b {{ color:var(--c); font-weight:600; }}
.pill:before {{ content:""; display:inline-block; width:7px; height:7px; border-radius:50%; background:var(--c); margin-right:8px; }}

/* sections */
.sec-label {{ font-family:var(--mono); font-size:11px; letter-spacing:.2em; color:var(--emerald); text-transform:uppercase; margin-top:1.4rem; }}
.sec-title {{ font-size:1.45rem; font-weight:700; color:var(--text); margin:.2rem 0 .15rem; }}
.sec-sub {{ color:var(--muted); font-size:.93rem; margin-bottom:.8rem; }}

/* KPI cards */
.kpi {{ background:var(--surface); border:1px solid var(--line); border-radius:16px; padding:16px 18px 14px; height:100%;
  border-top:3px solid var(--c); }}
.kpi-label {{ font-family:var(--mono); font-size:11px; font-weight:600; letter-spacing:.16em; text-transform:uppercase; color:var(--muted); }}
.kpi-value {{ font-family:var(--mono); font-variant-numeric:tabular-nums; font-weight:700; color:var(--text); margin:8px 0 4px;
  line-height:1.1; letter-spacing:-0.02em; }}
.kpi-value.num {{ white-space:nowrap; font-size:clamp(1.25rem, 2.1vw, 1.9rem); }}
.kpi-value.txt {{ font-family:var(--sans); font-size:clamp(1.05rem, 1.6vw, 1.45rem); word-break:normal; overflow-wrap:normal; }}
.kpi-value small {{ font-size:.9rem; color:var(--soft); font-weight:500; margin-left:3px; }}
.kpi-sub {{ font-size:12.5px; color:var(--soft); }}

/* insight cards */
.insight {{ background:var(--surface); border:1px solid var(--line); border-radius:16px; padding:14px 16px; height:100%; }}
.insight-tag {{ font-family:var(--mono); font-size:10.5px; letter-spacing:.18em; color:var(--c); text-transform:uppercase; }}
.insight-text {{ color:var(--soft); font-size:.92rem; line-height:1.5; margin-top:6px; }}
.insight-text b {{ color:var(--text); }}

/* notes & badges */
.note {{ color:var(--muted); font-size:12.5px; }}
.badge {{ display:inline-block; font-family:var(--mono); font-size:11px; padding:2px 8px; border-radius:6px;
  background:var(--surface2); border:1px solid var(--line); color:var(--c); }}

/* chat */
[data-testid="stChatMessage"] {{ background:var(--surface); border:1px solid var(--line); border-radius:16px; }}
[data-testid="stChatInput"] textarea {{ font-family:var(--sans); }}

/* tabs */
.stTabs [data-baseweb="tab-list"] {{ gap:6px; border-bottom:1px solid var(--line); }}
.stTabs [data-baseweb="tab"] {{ background:var(--surface); border:1px solid var(--line); border-radius:10px 10px 0 0; padding:8px 16px; color:var(--soft); }}
.stTabs [aria-selected="true"] {{ background:var(--surface2); color:var(--text); border-bottom:2px solid var(--emerald); }}

/* footer */
.footer {{ margin-top:2.6rem; padding-top:1rem; border-top:1px solid var(--line); display:flex; justify-content:space-between;
  color:var(--muted); font-size:12.5px; flex-wrap:wrap; gap:8px; }}
.footer a {{ color:var(--emerald); text-decoration:none; }}
.footer b {{ color:var(--text); }}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def _c(tone: str) -> str:
    return TONES.get(tone, tone)


def esc(s: str) -> str:
    return _html.escape(str(s))


def sidebar_brand(name: str, sub: str) -> None:
    st.sidebar.markdown(f'<div class="brand"><div class="brand-mark">MH</div><div><div class="brand-name">{esc(name)}</div>'
                        f'<div class="brand-sub">{esc(sub)}</div></div></div>', unsafe_allow_html=True)


def hero(eyebrow: str, title_html: str, sub: str, pills: list[tuple[str, str]]) -> None:
    p = "".join(f'<span class="pill" style="--c:{_c(t)}">{esc(x)}</span>' for x, t in pills)
    st.markdown(f'<div class="hero-eyebrow">{esc(eyebrow)}</div><div class="hero-title">{title_html}</div>'
                f'<div class="hero-sub">{sub}</div><div class="pills">{p}</div>', unsafe_allow_html=True)


def section(label: str, title: str, sub: str = "") -> None:
    s = f'<div class="sec-sub">{sub}</div>' if sub else ""
    st.markdown(f'<div class="sec-label">{esc(label)}</div><div class="sec-title">{esc(title)}</div>{s}', unsafe_allow_html=True)


def kpi(label: str, value: str, sub: str = "", tone: str = "emerald", unit: str = "", text: bool = False) -> str:
    """KPI card. text=True for a word value: sans font, wraps between words only."""
    u = f"<small>{esc(unit)}</small>" if unit else ""
    cls = "txt" if text else "num"
    return (f'<div class="kpi" style="--c:{_c(tone)}"><div class="kpi-label">{esc(label)}</div>'
            f'<div class="kpi-value {cls}">{value}{u}</div><div class="kpi-sub">{sub or "&nbsp;"}</div></div>')


def insight(tag: str, text_html: str, tone: str = "emerald") -> str:
    return (f'<div class="insight" style="--c:{_c(tone)}"><div class="insight-tag">{esc(tag)}</div>'
            f'<div class="insight-text">{text_html}</div></div>')


def footer(note: str) -> None:
    st.markdown(f'<div class="footer"><div>Built by <b>Muatasem Hadi</b> · MEng Industrial Engineering, Telkom University · {esc(note)}</div>'
                f'<div><a href="{GITHUB}">Source code</a> · <a href="{LINKEDIN}">LinkedIn</a></div></div>', unsafe_allow_html=True)
