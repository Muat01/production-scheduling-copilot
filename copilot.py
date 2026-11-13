"""
The planning copilot: plain-language commands -> validated actions -> solver -> explanation.

Design principle (LLM proposes, solver decides, checker verifies):
1. A command is turned into structured actions, either by a built-in rule-based
   parser (works offline, no API key) or, optionally, by an LLM through any
   OpenAI-compatible endpoint.
2. Every action is validated against the shop (machines, jobs, times) before use.
3. The schedule itself is ALWAYS produced by the dispatching rules or CP-SAT,
   never by the language model, and every plan is checked by `jobshop.check`.
4. The copilot explains what changed in plain words, from the numbers.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from jobshop import Instance, Schedule, kpis
from reschedule import METHODS, Event, repair
from rules import RULES, all_rules
from solver import solve

OBJECTIVES = {"weighted_tardiness": "weighted tardiness (due dates)", "makespan": "makespan (finish everything early)"}

HELP = (
    "Try: **Mill down at 80 for 90** · **rush J4 due 150** · **J3 due 300** · "
    "**new job Saw 20, Lathe 25, Inspect 10 due 300 weight 3** · **minimize makespan** · "
    "**keep the plan stable** · **compare rules** · **explain** · **undo**"
)


# ─── Parsing helpers ────────────────────────────────────────────────────────
def parse_time(s: str) -> Optional[int]:
    """'120', '120 min', '2h', '2 h', '1h30', '1.5h' -> minutes."""
    if s is None:
        return None
    s = s.strip().lower().replace(" ", "")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)h(?:(\d+)(?:m|min)?)?", s)
    if m:
        return int(round(float(m.group(1)) * 60)) + int(m.group(2) or 0)
    m = re.fullmatch(r"(\d+)(?:m|min|mins|minutes)?", s)
    return int(m.group(1)) if m else None


_T = r"(\d+(?:\.\d+)?(?:\s*(?:h(?:\s*\d+(?:\s*(?:min|m))?)?|minutes|mins|min|m)\b)?)"  # number + optional unit, no trailing space


def _machine(inst: Instance, token: str) -> Optional[int]:
    token = token.strip().lower()
    for m in range(inst.n_machines):
        if token in (inst.machine_name(m).lower(), f"m{m + 1}", str(m + 1)):
            return m
    return None


def _job(inst: Instance, token: str) -> Optional[int]:
    token = token.strip().lower()
    for j in range(inst.n_jobs):
        if token in (inst.job_name(j).lower(), f"j{j + 1}", f"job{j + 1}"):
            return j
    return None


def rule_parse(text: str, inst: Instance, now: int) -> Tuple[List[dict], List[str]]:
    """Rule-based parser. Returns (actions, problems)."""
    t = text.strip().lower()
    acts, probs = [], []
    mnames = "|".join(re.escape(inst.machine_name(m).lower()) for m in range(inst.n_machines)) + r"|m\d+"

    # machine breakdown
    for mm in re.finditer(rf"(?:machine\s+)?({mnames})\s+(?:is\s+)?(?:down|broken|breaks?\s*down|failed|fails?|stopped|stops?)"
                          rf"(?:\s+(?:at|from)\s+{_T})?(?:\s+(?:for)\s+{_T}|\s+(?:to|until|-)\s+{_T})?", t):
        m = _machine(inst, mm.group(1))
        start = parse_time(mm.group(2)) if mm.group(2) else now
        if mm.group(3):
            dur = parse_time(mm.group(3))
        elif mm.group(4):
            dur = (parse_time(mm.group(4)) or 0) - start
        else:
            dur = 60
            probs.append("No duration given: assumed 60 min.")
        if m is None:
            probs.append(f"Unknown machine '{mm.group(1)}'.")
        else:
            acts.append({"action": "breakdown", "machine": m, "start": start, "duration": dur})

    # rush / priority
    for mm in re.finditer(r"(?:rush|prioriti[sz]e|expedite|urgent)\s+(?:order\s+|job\s+)?(j\d+|job\s*\d+)(?:\s+due\s+(?:at\s+)?" + _T + ")?", t):
        j = _job(inst, mm.group(1).replace(" ", ""))
        if j is None:
            probs.append(f"Unknown job '{mm.group(1)}'.")
        else:
            acts.append({"action": "rush", "job": j, "weight": 5, "due": parse_time(mm.group(2)) if mm.group(2) else None})
    for mm in re.finditer(r"(j\d+)\s+is\s+urgent", t):
        j = _job(inst, mm.group(1))
        if j is not None:
            acts.append({"action": "rush", "job": j, "weight": 5, "due": None})

    # due date change (not part of a rush command or a new-job command)
    if not re.search(r"rush|prioriti|expedite|new\s+(?:job|order)", t):
        for mm in re.finditer(r"(j\d+)\s+(?:is\s+)?due\s+(?:at\s+|to\s+)?" + _T, t):
            j = _job(inst, mm.group(1))
            if j is None:
                probs.append(f"Unknown job '{mm.group(1)}'.")
            else:
                acts.append({"action": "due_change", "job": j, "due": parse_time(mm.group(2))})

    # new job:  new job Saw 20, Lathe 25, Inspect 10 [due 300] [weight 3] [at 60]
    mm = re.search(r"new\s+(?:job|order)\s*:?\s*(.+)", t)
    if mm:
        body = mm.group(1)
        due = re.search(r"due\s+(?:at\s+)?" + _T, body)
        w = re.search(r"weight\s+(\d+(?:\.\d+)?)", body)
        at = re.search(r"\bat\s+" + _T, body)
        route_part = re.split(r"\bdue\b|\bweight\b|\bat\b", body)[0]
        route, bad = [], []
        for name, p in re.findall(rf"({mnames})\s*[:=]?\s*(\d+)", route_part):
            m = _machine(inst, name)
            (bad.append(name) if m is None else route.append([m, int(p)]))
        if not route:
            probs.append("New job: give a route such as 'Saw 20, Lathe 25, Inspect 10'.")
        else:
            acts.append({"action": "new_job", "route": route, "due": parse_time(due.group(1)) if due else None,
                         "weight": float(w.group(1)) if w else 1.0, "time": parse_time(at.group(1)) if at else now})

    # objective / method / meta commands
    if re.search(r"makespan|finish (?:all|everything)|as early as possible", t):
        acts.append({"action": "objective", "objective": "makespan"})
    elif re.search(r"tardiness|due dates?\b|on.time|lateness", t) and not any(a["action"] in ("due_change", "rush", "new_job") for a in acts):
        acts.append({"action": "objective", "objective": "weighted_tardiness"})
    if re.search(r"right.?shift|keep (?:the )?sequence", t):
        acts.append({"action": "method", "method": "right_shift"})
    elif re.search(r"stable|nervous|don.t move|minimi[sz]e changes", t):
        acts.append({"action": "method", "method": "stable"})
    elif re.search(r"full re.?opt|re.?optimi[sz]e everything|best possible", t):
        acts.append({"action": "method", "method": "reoptimize"})
    if re.search(r"compare (?:the )?rules|which rule|dispatching rules", t):
        acts.append({"action": "compare_rules"})
    if re.search(r"\bexplain\b|\bwhy\b|what changed", t):
        acts.append({"action": "explain"})
    if re.search(r"\bundo\b", t):
        acts.append({"action": "undo"})
    if re.search(r"\breset\b|start over", t):
        acts.append({"action": "reset"})
    return acts, probs


# ─── Optional LLM parser (OpenAI-compatible endpoint) ───────────────────────
def llm_config() -> Optional[dict]:
    key = os.environ.get("LLM_API_KEY")
    if not key:
        return None
    return {"key": key,
            "base_url": os.environ.get("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"),
            "model": os.environ.get("LLM_MODEL", "gemini-2.5-flash")}


def llm_prompt(inst: Instance, now: int) -> str:
    machines = ", ".join(f"{m}={inst.machine_name(m)}" for m in range(inst.n_machines))
    jobs = ", ".join(f"{j}={inst.job_name(j)}" for j in range(inst.n_jobs))
    return (
        "You translate a production planner's request into JSON actions for a job-shop scheduler. "
        "Never produce a schedule yourself. Times are minutes from shift start; current time is "
        f"{now}. Machines (index=name): {machines}. Jobs (index=name): {jobs}.\n"
        'Reply with JSON only: {"actions": [...]} where each action is one of\n'
        '{"action":"breakdown","machine":int,"start":int,"duration":int}\n'
        '{"action":"rush","job":int,"weight":5,"due":int|null}\n'
        '{"action":"due_change","job":int,"due":int}\n'
        '{"action":"new_job","route":[[machine,int_minutes],...],"due":int|null,"weight":number,"time":int}\n'
        '{"action":"objective","objective":"makespan"|"weighted_tardiness"}\n'
        '{"action":"method","method":"right_shift"|"reoptimize"|"stable"}\n'
        '{"action":"compare_rules"} {"action":"explain"} {"action":"undo"} {"action":"reset"}\n'
        'If the request is unclear, return {"actions": [], "question": "<one short question>"}.'
    )


def llm_parse(text: str, inst: Instance, now: int, cfg: dict, opener=urllib.request.urlopen) -> Tuple[List[dict], List[str]]:
    body = json.dumps({"model": cfg["model"], "temperature": 0,
                       "response_format": {"type": "json_object"},
                       "messages": [{"role": "system", "content": llm_prompt(inst, now)},
                                    {"role": "user", "content": text}]}).encode()
    req = urllib.request.Request(cfg["base_url"].rstrip("/") + "/chat/completions", data=body,
                                 headers={"Authorization": f"Bearer {cfg['key']}", "Content-Type": "application/json"})
    with opener(req, timeout=30) as r:
        content = json.loads(r.read())["choices"][0]["message"]["content"]
    data = json.loads(re.sub(r"^```(?:json)?|```$", "", content.strip()).strip())
    probs = [data["question"]] if data.get("question") else []
    return list(data.get("actions", [])), probs


# ─── Validation ─────────────────────────────────────────────────────────────
def validate(actions: List[dict], inst: Instance) -> Tuple[List[dict], List[str]]:
    ok, probs = [], []
    for a in actions:
        kind = a.get("action")
        try:
            if kind == "breakdown":
                assert 0 <= int(a["machine"]) < inst.n_machines, "machine out of range"
                assert int(a["start"]) >= 0 and 0 < int(a["duration"]) <= 24 * 60, "bad time or duration"
            elif kind in ("rush", "due_change"):
                assert 0 <= int(a["job"]) < inst.n_jobs, "job out of range"
                if a.get("due") is not None:
                    assert int(a["due"]) >= 0, "bad due date"
            elif kind == "new_job":
                assert a["route"], "empty route"
                for m, p in a["route"]:
                    assert 0 <= int(m) < inst.n_machines and 0 < int(p) <= 24 * 60, "bad route step"
            elif kind == "objective":
                assert a["objective"] in OBJECTIVES, "unknown objective"
            elif kind == "method":
                assert a["method"] in METHODS, "unknown method"
            elif kind not in ("compare_rules", "explain", "undo", "reset"):
                raise AssertionError(f"unknown action '{kind}'")
            ok.append(a)
        except (AssertionError, KeyError, TypeError, ValueError) as e:
            probs.append(f"Ignored {kind or 'action'}: {e}.")
    return ok, probs


# ─── Explanation ────────────────────────────────────────────────────────────
def explain(before_inst: Instance, before: Schedule, after_inst: Instance, after: Schedule, extra: dict | None = None) -> str:
    kb, ka = kpis(before_inst, before), kpis(after_inst, after)
    lines = []
    if "weighted_tardiness" in ka and "weighted_tardiness" in kb:
        lines.append(f"Weighted tardiness {kb['weighted_tardiness']:.0f} → **{ka['weighted_tardiness']:.0f}**, "
                     f"late jobs {kb['late_jobs']} → **{ka['late_jobs']}**.")
    lines.append(f"Makespan {kb['makespan']} → **{ka['makespan']}** min.")
    if extra:
        lines.append(f"{extra.get('moved_ops', 0)} operations moved (total shift {extra.get('deviation_min', 0)} min); "
                     f"{extra.get('frozen', 0)} already-started operations kept as they were.")
    if after_inst.due:
        C_b = {before_inst.job_name(j): before[(j, len(r) - 1)] + r[-1][1] for j, r in enumerate(before_inst.routes)}
        late_now = []
        for j, r in enumerate(after_inst.routes):
            c = after[(j, len(r) - 1)] + r[-1][1]
            name = after_inst.job_name(j)
            if c > after_inst.due[j]:
                was = C_b.get(name)
                tag = "" if was is not None and was > before_inst.due_of(j) else " (newly late)" if was is not None else " (new job)"
                late_now.append(f"{name} +{c - after_inst.due[j]} min{tag}")
        lines.append("Late now: " + (", ".join(late_now) if late_now else "none ✓"))
    lines.append(f"Bottleneck (most loaded machine): {ka['bottleneck']}.")
    return "\n".join(f"- {x}" for x in lines)


# ─── Copilot session ────────────────────────────────────────────────────────
@dataclass
class Copilot:
    base: Instance
    objective: str = "weighted_tardiness"
    method: str = "stable"
    now: int = 0
    time_limit: float = 5.0
    use_llm: bool = False
    inst: Instance = None
    sched: Schedule = None
    history: list = field(default_factory=list)
    last_explanation: str = ""

    def __post_init__(self):
        if self.inst is None:
            self.inst = self.base
            self.sched = solve(self.base, self.objective, self.time_limit).schedule

    def _push(self, label: str):
        self.history.append((self.inst, self.sched, label))

    def handle(self, text: str) -> dict:
        """Process one command. Returns {'message', 'actions', 'changed'}."""
        source = "rules"
        cfg = llm_config() if self.use_llm else None
        try:
            if cfg:
                acts, probs = llm_parse(text, self.inst, self.now, cfg)
                source = "llm"
            else:
                acts, probs = rule_parse(text, self.inst, self.now)
        except Exception as e:                       # LLM unavailable -> fall back, say so
            acts, probs = rule_parse(text, self.inst, self.now)
            probs.append(f"LLM not reachable ({type(e).__name__}); used the built-in parser.")
        acts, bad = validate(acts, self.inst)
        probs += bad
        if not acts:
            return {"message": "I could not turn that into an action. " + " ".join(probs) + "\n\n" + HELP,
                    "actions": [], "changed": False, "source": source}

        msgs, changed = [], False
        for a in acts:
            kind = a["action"]
            if kind == "objective":
                self.objective = a["objective"]
                msgs.append(f"Objective set to **{OBJECTIVES[self.objective]}**.")
                before_i, before_s = self.inst, self.sched
                self._push("objective")
                self.sched = solve(self.inst, self.objective, self.time_limit,
                                   frozen={k: s for k, s in self.sched.items() if s < self.now},
                                   not_before=self.now, hint=self.sched).schedule or self.sched
                self.last_explanation = explain(before_i, before_s, self.inst, self.sched)
                msgs.append(self.last_explanation)
                changed = True
            elif kind == "method":
                self.method = a["method"]
                msgs.append(f"Repair method for the next disruption: **{METHODS[self.method]}**.")
            elif kind == "compare_rules":
                rows = []
                for r, s in all_rules(self.inst).items():
                    k = kpis(self.inst, s)
                    rows.append(f"| {r} | {k['makespan']} | {k.get('weighted_tardiness', 0):.0f} |")
                cur = kpis(self.inst, self.sched)
                rows.append(f"| **Current plan (CP-SAT)** | **{cur['makespan']}** | **{cur.get('weighted_tardiness', 0):.0f}** |")
                msgs.append("| Rule | Makespan | Weighted tardiness |\n|---|---|---|\n" + "\n".join(rows))
            elif kind == "explain":
                msgs.append(self.last_explanation or "Nothing has changed yet: this is the original optimal plan.")
            elif kind == "undo":
                if self.history:
                    self.inst, self.sched, label = self.history.pop()
                    msgs.append(f"Undid the last change ({label}).")
                    changed = True
                else:
                    msgs.append("Nothing to undo.")
            elif kind == "reset":
                self.history.clear()
                self.inst = self.base
                self.sched = solve(self.base, self.objective, self.time_limit).schedule
                self.last_explanation = ""
                msgs.append("Back to the original order book and its optimal plan.")
                changed = True
            else:
                ev = self._event(a)
                before_i, before_s = self.inst, self.sched
                res = repair(self.inst, self.sched, ev, self.method, self.objective, time_limit=self.time_limit)
                if res["violations"]:
                    msgs.append("⚠️ The new plan failed the feasibility check, so it was not applied: "
                                + "; ".join(res["violations"][:3]))
                    continue
                self._push(kind)
                self.inst, self.sched = res["instance"], res["schedule"]
                self.last_explanation = explain(before_i, before_s, self.inst, self.sched, res)
                msgs.append(f"**{self._describe(a)}** → re-planned with *{METHODS[self.method]}* "
                            f"({res['status']}, checked feasible).\n\n" + self.last_explanation)
                changed = True
        if probs:
            msgs.append("_Note: " + " ".join(probs) + "_")
        return {"message": "\n\n".join(msgs), "actions": acts, "changed": changed, "source": source}

    def _event(self, a: dict) -> Event:
        k = a["action"]
        if k == "breakdown":
            return Event("breakdown", int(a["start"]), machine=int(a["machine"]), duration=int(a["duration"]))
        if k == "rush":
            return Event("rush", self.now, job=int(a["job"]), weight=float(a.get("weight") or 5), due=a.get("due"))
        if k == "due_change":
            return Event("due_change", self.now, job=int(a["job"]), due=int(a["due"]))
        n = self.inst.n_jobs
        return Event("new_job", int(a.get("time", self.now)), route=tuple((int(m), int(p)) for m, p in a["route"]),
                     due=a.get("due"), weight=float(a.get("weight") or 1), name=f"J{n + 1}")

    def _describe(self, a: dict) -> str:
        k = a["action"]
        if k == "breakdown":
            return f"{self.inst.machine_name(a['machine'])} down {a['start']}–{a['start'] + a['duration']} min"
        if k == "rush":
            return f"Rush {self.inst.job_name(a['job'])}" + (f" (due {a['due']})" if a.get("due") is not None else "")
        if k == "due_change":
            return f"{self.inst.job_name(a['job'])} due at {a['due']}"
        steps = " → ".join(f"{self.inst.machine_name(m)} {p}" for m, p in a["route"])
        return f"New job ({steps})"
