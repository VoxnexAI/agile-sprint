#!/usr/bin/env python3
"""Sprint board renderer.

Reads a delivery's file-based sprint state and renders a self-contained
HTML board artifact. Python 3 stdlib only (argparse, json, pathlib, re,
html, datetime) -- no yaml dependency, no external assets.

Usage:
    python scripts/sprint_board.py <delivery> --out <file.html> [--root sprint]

Exit codes:
    0 - board rendered successfully
    2 - a clear, user-facing input problem (missing delivery, malformed
        story frontmatter, etc.) -- never render a silently-wrong board
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

COLUMNS = ["Backlog", "To-Do", "Design", "Build", "Test", "Blocked", "Done"]

STATUS_TO_COLUMN = {
    "backlog": "Backlog",
    "groomed": "Backlog",
    "committed": "To-Do",
    "design": "Design",
    "build": "Build",
    "test": "Test",
    # Complex / PO-needed blockers park here mid-sprint; the SM clears or
    # escalates, else the story returns to the backlog (PO bug policy).
    "blocked": "Blocked",
    "done": "Done",
    "shipped": "Done",
}

PULSING_STATUSES = {"design", "build", "test"}

VALID_STATUSES = set(STATUS_TO_COLUMN.keys())

REQUIRED_STORY_KEYS = [
    "id",
    "title",
    "type",
    "points",
    "risk",
    "repo",
    "status",
    "claimed_by",
    "sprint",
]


class BoardInputError(Exception):
    """A clear, user-facing problem with the delivery's state files."""


def _read_text(path: Path) -> str:
    """Read a state file as UTF-8, tolerating a leading BOM (PowerShell's
    `>`/`>>`/Out-File write UTF-8-with-BOM). Any other decode failure becomes
    a BoardInputError naming the file, instead of an uncaught traceback."""
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise BoardInputError(f"{path}: could not be read as UTF-8 ({exc})")


class Story:
    def __init__(self, fields: dict, path: Path, tasks: Optional[list] = None):
        self.path = path
        self.id = fields["id"]
        self.title = fields["title"]
        self.type = fields["type"]
        self.points = fields["points"]
        self.risk = fields["risk"]
        self.repo = fields["repo"]
        self.status = fields["status"]
        self.claimed_by = fields["claimed_by"]
        self.sprint = fields["sprint"]
        # (text, done) granular tasks from the story's Tech design checklist;
        # drives the card's expandable task view (PO request, 2026-08-21).
        self.tasks = tasks or []


def parse_story_frontmatter(text: str, path: Path) -> dict:
    """Parse the leading ``---``-delimited frontmatter block of a story file.

    Only simple ``key: value`` lines are supported (no YAML dependency).
    Raises BoardInputError with a message naming the file and the problem
    on anything malformed -- callers must never render a silently-wrong
    board on bad input.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise BoardInputError(f"{path}: malformed frontmatter (must start with '---')")

    fields: dict = {}
    closed = False
    idx = 1
    # 20-line cap per the plan -- frontmatter blocks are small and fixed-shape.
    for idx in range(1, min(len(lines), 21)):
        line = lines[idx]
        if line.strip() == "---":
            closed = True
            break
        if not line.strip():
            continue
        if ":" not in line:
            raise BoardInputError(
                f"{path}: malformed frontmatter line {idx + 1} (expected 'key: value'): {line!r}"
            )
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()

    if not closed:
        raise BoardInputError(f"{path}: malformed frontmatter (no closing '---' found within 20 lines)")

    missing = [k for k in REQUIRED_STORY_KEYS if k not in fields]
    if missing:
        raise BoardInputError(
            f"{path}: malformed frontmatter (missing required key(s): {', '.join(missing)})"
        )

    if not fields["id"]:
        raise BoardInputError(f"{path}: malformed frontmatter (empty 'id')")
    if not fields["title"]:
        raise BoardInputError(f"{path}: malformed frontmatter (empty 'title')")
    if fields["status"] not in VALID_STATUSES:
        raise BoardInputError(
            f"{path}: malformed frontmatter (status {fields['status']!r} is not one of "
            f"{sorted(VALID_STATUSES)})"
        )

    return fields


_TASK_LINE_RE = re.compile(r"^\s*-\s*\[( |x|X)\]\s*(.+)$")

_TASK_KIND_RE = re.compile(r"^\[(build|test|bug)\]\s*", re.IGNORECASE)


def extract_story_tasks(text: str) -> list:
    """(text, done, kind) tuples from the checklists inside the story's
    '## Tasks' and '## Tech design' sections ONLY -- the AC and DoR
    checklists are gates, not work items. An item may be typed with a
    leading [build] / [test] / [bug] tag (PO task model, 2026-08-21);
    untyped items get kind None."""
    tasks = []
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            low = stripped.lower()
            in_section = low.startswith("## tech design") or low.startswith("## tasks")
            continue
        if not in_section:
            continue
        m = _TASK_LINE_RE.match(line)
        if m:
            label = re.sub(r"\*\*", "", m.group(2)).strip()
            kind = None
            km = _TASK_KIND_RE.match(label)
            if km:
                kind = km.group(1).lower()
                label = label[km.end():].strip()
            tasks.append((label, m.group(1).lower() == "x", kind))
        elif tasks and stripped and line[:1] in (" ", "\t") \
                and not stripped.startswith(("-", "#", "|", ">")):
            # wrapped task text: indented continuation lines belong to the
            # item above them, not to the void
            label, done, kind = tasks[-1]
            tasks[-1] = (label + " " + stripped, done, kind)
    return tasks


def load_stories(stories_dir: Path) -> list:
    stories = []
    if not stories_dir.is_dir():
        return stories
    for story_path in sorted(stories_dir.glob("*.md")):
        text = _read_text(story_path)
        fields = parse_story_frontmatter(text, story_path)
        stories.append(Story(fields, story_path, extract_story_tasks(text)))
    return stories


BACKLOG_LINE_RE = re.compile(
    r"""^\s*-\s*
        (?:\[(?P<points>[^\]]*)\]\s*)?
        (?:\[(?P<risk>[^\]]*)\]\s*)?
        (?P<rest>.+)$""",
    re.VERBOSE,
)

STORY_REF_RE = re.compile(r"\bST-\d+\b")


UNGROOMED_PREFIX_RE = re.compile(r"(?i)^\(ungroomed\)\s*")

DASH_SPLIT_RE = re.compile(r"\s+[—–-]\s+")


def load_ungroomed_backlog_lines(backlog_path: Path, known_story_ids: set) -> list:
    """Return plain (title, intent, points, risk) tuples for backlog.md lines
    that are NOT already represented by a groomed story file.

    A line carrying an ST-### ref is skipped only when that id is among
    ``known_story_ids`` (a real story file exists for it); otherwise it is a
    dangling reference and raises BoardInputError rather than silently
    dropping the item off the board. Lines inside ``<!-- ... -->`` comment
    blocks are ignored entirely.
    """
    if not backlog_path.is_file():
        return []
    items = []
    in_comment = False
    for lineno, raw_line in enumerate(_read_text(backlog_path).splitlines(), start=1):
        line = raw_line.strip()
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if "<!--" in line:
            if "-->" not in line:
                in_comment = True
            continue
        if not line.startswith("-"):
            continue
        ref_match = STORY_REF_RE.search(line)
        if ref_match:
            ref = ref_match.group(0)
            if ref in known_story_ids:
                continue
            raise BoardInputError(
                f"{backlog_path}: line {lineno} references {ref} but no story file for it "
                f"exists under stories/ (typo, or the story file was deleted)"
            )
        m = BACKLOG_LINE_RE.match(line)
        if not m:
            continue
        points, risk = m.group("points"), m.group("risk")
        # A lone bracket like '[high]' matches the `points` group first; if
        # there's no separate risk bracket and what we captured as points
        # isn't numeric, it's actually the risk tag.
        if risk is None and points is not None and not points.strip().isdigit():
            points, risk = None, points
        rest = m.group("rest").strip()
        parts = DASH_SPLIT_RE.split(rest, maxsplit=1)
        title = parts[0].strip()
        intent = parts[1].strip() if len(parts) > 1 else ""
        title = UNGROOMED_PREFIX_RE.sub("", title).strip()
        if not title:
            continue
        items.append((title, intent, points, risk))
    return items


def load_crew(crew_path: Path) -> dict:
    """Parse a markdown crew table into {role: name}. Missing file or
    missing table -> empty map (renderer degrades gracefully).

    Preferred shape is a '## Crew' heading followed by the table, but a
    crew.local.md written exactly as the skill instructs -- "same table
    format, only rows being overridden", with no heading -- is also
    accepted: when no '## Crew' heading is found anywhere in the file, any
    markdown table in the file is parsed instead of ignoring it.
    """
    crew: dict = {}
    if not crew_path.is_file():
        return crew
    lines = _read_text(crew_path).splitlines()
    has_heading = any(line.strip().startswith("## Crew") for line in lines)
    in_table = not has_heading
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Crew"):
            in_table = True
            continue
        if not in_table:
            continue
        if not stripped.startswith("|"):
            if crew:  # table already collected at least one row -> table ended
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        role, name = cells[0], cells[1]
        if role in ("Role", "") or set(role) <= {"-", ":"}:
            continue
        crew[role] = name
    return crew


def resolve_crew(sprint_root: Path) -> dict:
    """Effective crew names: shared defaults from crew.md, overridden per-user
    by crew.local.md (gitignored). A PO name of "(active user...)" resolves to
    `git config user.name`; when that is unset or the call fails we fall back to
    the ROLE LABEL "Product Owner" — never the raw placeholder, which reads as a
    bug on a published page (observed 2026-08-22: user.name empty on this
    machine). Set `git config user.name` to see a real name instead."""
    crew = load_crew(sprint_root / "crew.md")
    crew.update(load_crew(sprint_root / "crew.local.md"))
    if crew.get("PO", "").strip().lower().startswith("(active user"):
        name = ""
        try:
            import subprocess
            name = subprocess.run(
                ["git", "config", "user.name"],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()
        except Exception:
            name = ""
        crew["PO"] = name or "Product Owner"
    return crew


def newest_sprint_dir(delivery_dir: Path) -> Optional[Path]:
    sprints_dir = delivery_dir / "sprints"
    if not sprints_dir.is_dir():
        return None
    candidates = []
    for child in sprints_dir.iterdir():
        if not child.is_dir():
            continue
        m = re.match(r"^S(\d+)$", child.name)
        if m:
            candidates.append((int(m.group(1)), child))
    if not candidates:
        return None
    candidates.sort(key=lambda pair: pair[0])
    return candidates[-1][1]


def load_sprint_goal(plan_path: Path) -> Optional[str]:
    if not plan_path.is_file():
        return None
    lines = _read_text(plan_path).splitlines()
    goal_lines = []
    in_section = False
    for line in lines:
        if line.strip().startswith("## "):
            if in_section:
                break
            if line.strip().lower() == "## sprint goal":
                in_section = True
            continue
        if in_section and line.strip():
            goal_lines.append(line.strip())
    if not goal_lines:
        return None
    return " ".join(goal_lines)


def load_events(events_path: Path) -> list:
    if not events_path.is_file():
        return []
    events = []
    for lineno, raw in enumerate(_read_text(events_path).splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise BoardInputError(f"{events_path}: malformed event on line {lineno}: {exc}")
        if not isinstance(event, dict):
            raise BoardInputError(
                f"{events_path}: event on line {lineno} is not a JSON object: {raw!r}"
            )
        events.append(event)
    return events


def points_as_number(points) -> float:
    try:
        return float(points)
    except (TypeError, ValueError):
        return 0.0


def compute_burndown(events: list, stories: list, sprint_id: Optional[str]):
    """Burndown data over events.jsonl `to: "done"` transitions for the
    current sprint's stories. Returns None when there is nothing to chart,
    else {"series": points remaining after each done event (starting at the
    sprint total), "labels": timestamps aligned to the series, "total"}."""
    if not events or not sprint_id:
        return None

    sprint_points = {s.id: points_as_number(s.points) for s in stories if s.sprint == sprint_id}
    total = sum(sprint_points.values())
    if total <= 0:
        return None

    done_events = [e for e in events if e.get("to") == "done" and e.get("story") in sprint_points]
    if not done_events:
        return None

    remaining = total
    series = [total]
    labels = ["start"]
    for event in done_events:
        remaining -= sprint_points.get(event["story"], 0.0)
        series.append(max(remaining, 0.0))
        ts = str(event.get("timestamp") or "")
        labels.append(ts[5:16].replace("T", " ") if len(ts) >= 16 else str(event.get("story") or ""))
    return {"series": series, "labels": labels, "total": total}


def render_burndown_svg(bd) -> str:
    """Burndown with axes, quarter gridlines, the ideal guideline, and value
    markers -- readable at a glance, not a bare line."""
    series = bd["series"]
    labels = bd["labels"]
    total = bd["total"] or 1.0
    w, h = 560, 210
    pl, pr, pt, pb = 46, 18, 18, 34
    iw, ih = w - pl - pr, h - pt - pb
    n = len(series)
    step = iw / (n - 1) if n > 1 else 0.0

    def gx(i: int) -> float:
        return pl + i * step

    def gy(v: float) -> float:
        return pt + ih * (1 - v / total)

    parts = []
    for k in range(5):
        val = total * k / 4
        yy = gy(val)
        parts.append(f'<line x1="{pl}" y1="{yy:.1f}" x2="{pl + iw}" y2="{yy:.1f}" class="bd-grid"/>')
        parts.append(f'<text x="{pl - 8}" y="{yy + 3.5:.1f}" class="bd-lab" text-anchor="end">{val:g}</text>')
    parts.append(
        f'<line x1="{gx(0):.1f}" y1="{gy(total):.1f}" x2="{gx(n - 1):.1f}" y2="{gy(0):.1f}" class="bd-ideal"/>'
    )
    pts = " ".join(f"{gx(i):.1f},{gy(v):.1f}" for i, v in enumerate(series))
    parts.append(
        f'<polygon points="{pts} {gx(n - 1):.1f},{pt + ih:.1f} {gx(0):.1f},{pt + ih:.1f}" class="bd-area"/>'
    )
    parts.append(f'<polyline points="{pts}" class="bd-line"/>')
    label_every = 1 if n <= 7 else max(1, n // 6)
    for i, v in enumerate(series):
        parts.append(f'<circle cx="{gx(i):.1f}" cy="{gy(v):.1f}" r="4" class="bd-dot"/>')
        parts.append(f'<text x="{gx(i):.1f}" y="{gy(v) - 9:.1f}" class="bd-lab bd-val" text-anchor="middle">{v:g}</text>')
        if i % label_every == 0 or i == n - 1:
            parts.append(
                f'<text x="{gx(i):.1f}" y="{pt + ih + 16:.1f}" class="bd-lab" text-anchor="middle">{esc(labels[i])}</text>'
            )
    parts.append(f'<line x1="{pl}" y1="{pt + ih}" x2="{pl + iw}" y2="{pt + ih}" class="bd-axis"/>')
    return (
        f'<svg class="burndown" viewBox="0 0 {w} {h}" role="img" preserveAspectRatio="xMinYMin meet" '
        f'aria-label="Burndown: points remaining over sprint events">{"".join(parts)}</svg>'
    )


def load_velocity(velocity_path: Path) -> Optional[str]:
    if not velocity_path.is_file():
        return None
    text = _read_text(velocity_path).strip()
    return text or None


def load_optional_text(path: Path) -> Optional[str]:
    """Read a small optional markdown doc (showcase.md, retro.md) verbatim.
    Missing file -> None (renderer degrades gracefully)."""
    if not path.is_file():
        return None
    text = _read_text(path).strip()
    return text or None


def esc(value) -> str:
    return html.escape(str(value), quote=True)


_MD_CODE_RE = re.compile(r"`([^`]+)`")
_MD_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")


def _md_inline(text: str) -> str:
    """Escape, then apply the two inline marks the sprint docs actually use."""
    out = esc(text)
    out = _MD_CODE_RE.sub(r"<code>\1</code>", out)
    out = _MD_BOLD_RE.sub(r"<strong>\1</strong>", out)
    return out


def md_to_html(text: str) -> str:
    """Small markdown renderer for showcase.md / retro.md (stdlib only).
    Supports #..#### headings, paragraphs, -/* and 1. lists (with hanging
    indents), pipe tables, `code`, **bold**, --- rules, <!-- --> comments.
    Anything else degrades to an escaped paragraph -- the board never shows
    raw markdown in a <pre> again."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    out: list = []
    para: list = []
    lst: list = []
    lst_tag = [""]
    table: list = []

    def flush_para():
        if para:
            out.append("<p>" + " ".join(_md_inline(p) for p in para) + "</p>")
            para.clear()

    def flush_list():
        if lst:
            items = "".join(f"<li>{_md_inline(i)}</li>" for i in lst)
            out.append(f"<{lst_tag[0]}>{items}</{lst_tag[0]}>")
            lst.clear()
        lst_tag[0] = ""

    def flush_table():
        if table:
            rows = []
            for ri, cells in enumerate(table):
                tag = "th" if ri == 0 else "td"
                rows.append("<tr>" + "".join(f"<{tag}>{_md_inline(c)}</{tag}>" for c in cells) + "</tr>")
            out.append('<div class="tablewrap"><table>' + "".join(rows) + "</table></div>")
            table.clear()

    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("|") and stripped.count("|") >= 2:
            flush_para()
            flush_list()
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if not all(c and set(c) <= {"-", ":"} for c in cells):  # skip separator rows
                table.append(cells)
            continue
        flush_table()
        if not stripped:
            flush_para()
            flush_list()
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            flush_para()
            flush_list()
            level = min(len(m.group(1)) + 2, 6)
            out.append(f"<h{level}>{_md_inline(m.group(2))}</h{level}>")
            continue
        if re.fullmatch(r"-{3,}", stripped):
            flush_para()
            flush_list()
            out.append("<hr>")
            continue
        m = re.match(r"^[-*]\s+(.*)$", stripped)
        if m and not raw.startswith(("   ", "\t")):
            flush_para()
            if lst_tag[0] and lst_tag[0] != "ul":
                flush_list()
            lst_tag[0] = "ul"
            lst.append(m.group(1))
            continue
        m = re.match(r"^\d+[.)]\s+(.*)$", stripped)
        if m and not raw.startswith(("   ", "\t")):
            flush_para()
            if lst_tag[0] and lst_tag[0] != "ol":
                flush_list()
            lst_tag[0] = "ol"
            lst.append(m.group(1))
            continue
        if lst and raw.startswith((" ", "\t")):  # hanging indent continues the item
            lst[-1] += " " + stripped
            continue
        flush_list()
        para.append(stripped)

    flush_table()
    flush_para()
    flush_list()
    return "".join(out)


_VELOCITY_ROW_RE = re.compile(r"^\s*[-|]?\s*(S\d+)\s*[:|]\s*(\d+(?:\.\d+)?)")


def parse_velocity_rows(text: str) -> list:
    """Extract (sprint, points) pairs from velocity.md; empty list when the
    file is prose-only (the caller then shows the text verbatim)."""
    rows = []
    for line in text.splitlines():
        m = _VELOCITY_ROW_RE.match(line)
        if m:
            rows.append((m.group(1), float(m.group(2))))
    return rows


def humanize_events(events: list, crew: dict, limit: int = 12) -> list:
    """Newest-first activity rows for the board's timeline."""
    rows = []
    for e in reversed(events):
        if len(rows) >= limit:
            break
        actor = str(e.get("actor") or "")
        ts = str(e.get("timestamp") or "")
        marker = e.get("event")
        rows.append({
            "when": ts[5:16].replace("T", " ") if len(ts) >= 16 else ts,
            "name": crew.get(actor, actor) or "?",
            "role": actor,
            "story": str(e.get("story") or ""),
            "desc": str(marker) if marker else f'{e.get("from") or "?"} → {e.get("to") or "?"}',
            "to": "" if marker else str(e.get("to") or ""),
        })
    return rows


def _initials(name: str) -> str:
    parts = [p for p in re.split(r"\s+", name.strip()) if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def render_avatar_chip(claimed_by: str, status: str, crew: dict) -> str:
    if not claimed_by or claimed_by.strip().lower() in ("none", "-"):
        return '<span class="avatar-chip unclaimed">Unclaimed</span>'
    name = crew.get(claimed_by, claimed_by)
    pulsing = " pulsing" if status in PULSING_STATUSES else ""
    title = esc(f"{claimed_by}: {name}") if name != claimed_by else esc(claimed_by)
    return (
        f'<span class="avatar-chip{pulsing}" title="{title}">'
        f'<span class="avatar-dot" aria-hidden="true">{esc(_initials(name))}</span>{esc(name)}</span>'
    )


def render_story_card(story: Story, crew: dict) -> str:
    risk_class = "risk-high" if story.risk == "high" else "risk-normal"
    risk_badge = f'<span class="badge {risk_class}">{esc(story.risk)} risk</span>' if story.risk else ""
    points_badge = f'<span class="badge points">{esc(story.points)} pts</span>' if str(story.points).strip() else ""
    type_badge = f'<span class="badge tag">{esc(story.type)}</span>' if str(story.type).strip() else ""
    avatar = render_avatar_chip(story.claimed_by, story.status, crew)
    story_path = str(story.path).replace("\\", "/")
    file_name = story_path.rsplit("/", 1)[-1]

    tasks_html = ""
    if story.tasks:
        done = sum(1 for _, is_done, _ in story.tasks if is_done)
        bugs_open = sum(1 for _, is_done, kind in story.tasks if kind == "bug" and not is_done)
        items = []
        for label, is_done, kind in story.tasks:
            kind_chip = f'<span class="task-kind k-{kind}">{kind}</span>' if kind else ""
            items.append(
                f'<li class="task {"done" if is_done else "open"}">'
                f'<span class="task-box" aria-hidden="true"></span>{kind_chip}{esc(label)}</li>'
            )
        bug_chip = f'<span class="task-count bug-open">{bugs_open} bug{"" if bugs_open == 1 else "s"} open</span>' if bugs_open else ""
        tasks_html = (
            f'<details class="card-tasks"><summary>Tasks '
            f'<span class="task-count">{done}/{len(story.tasks)}</span>{bug_chip}</summary>'
            f"<ul>{''.join(items)}</ul></details>"
        )

    return (
        f'<div class="card st-{esc(story.status)}">'
        f'<div class="card-top"><span class="card-id">{esc(story.id)}</span>{type_badge}</div>'
        f'<div class="card-title">{esc(story.title)}</div>'
        f'<div class="card-meta">{points_badge}{risk_badge}</div>'
        f"{tasks_html}"
        f'<div class="card-foot">{avatar}'
        f'<span class="card-path" title="{esc(story_path)}">{esc(file_name)}</span></div>'
        "</div>"
    )


def render_ungroomed_card(title: str, intent: str, points: Optional[str], risk: Optional[str]) -> str:
    points_badge = f'<span class="badge points">{esc(points)} pts</span>' if points and points.strip() else ""
    risk_badge = (
        f'<span class="badge {"risk-high" if (risk or "").strip() == "high" else "risk-normal"}">{esc(risk)} risk</span>'
        if risk and risk.strip()
        else ""
    )
    intent_html = f'<div class="card-intent">{esc(intent)}</div>' if intent else ""
    return (
        '<div class="card ungroomed">'
        f'<div class="card-title">{esc(title)}</div>'
        f"{intent_html}"
        f'<div class="card-meta">{points_badge}{risk_badge}<span class="badge tag">ungroomed</span></div>'
        "</div>"
    )


_LIGHT_TOKENS = """
  --bg: #F3F5FA;
  --panel: #FFFFFF;
  --panel-border: #DEE5F1;
  --text: #17233E;
  --text-dim: #5D6C8A;
  --accent: #1E40AF;
  --accent-2: #D97706;
  --column-bg: #E9EDF6;
  --column-border: #DDE4F0;
  --badge-bg: #EBF0FA;
  --badge-text: #3A4A6B;
  --badge-risk-high-bg: #FBE3E1;
  --badge-risk-high-text: #9F2318;
  --badge-risk-normal-bg: #E4F3E9;
  --badge-risk-normal-text: #1D6B36;
  --avatar-bg: #1E40AF;
  --avatar-text: #FFFFFF;
  --chip-bg: #E7EDFB;
  --chip-text: #20397F;
  --unclaimed-bg: #EDF0F6;
  --unclaimed-text: #66718A;
  --chart-grid: #E1E7F2;
  --chart-ideal: #A9B7D4;
  --goal-bg: #FBF3E4;
  --bar-bg: #E4EAF5;
  --col-todo: #64748B;
  --col-design: #0E7490;
  --col-build: #1E40AF;
  --col-test: #B45309;
  --col-blocked: #BE123C;
  --col-done: #15803D;
  --shadow: 0 1px 2px rgba(16, 24, 40, 0.06);
  --shadow-hover: 0 4px 12px rgba(16, 24, 40, 0.12);
"""

_DARK_TOKENS = """
  --bg: #0F1420;
  --panel: #181F2E;
  --panel-border: #2A3550;
  --text: #E9EEF9;
  --text-dim: #98A6C4;
  --accent: #8AACFF;
  --accent-2: #F0A44E;
  --column-bg: #141B29;
  --column-border: #243250;
  --badge-bg: #232D44;
  --badge-text: #BCC9E4;
  --badge-risk-high-bg: #43201E;
  --badge-risk-high-text: #F5ABA4;
  --badge-risk-normal-bg: #1C3524;
  --badge-risk-normal-text: #A5E3B8;
  --avatar-bg: #3D62D8;
  --avatar-text: #FFFFFF;
  --chip-bg: #22304F;
  --chip-text: #C3D2F6;
  --unclaimed-bg: #232B3D;
  --unclaimed-text: #8C99B5;
  --chart-grid: #243150;
  --chart-ideal: #4A5B82;
  --goal-bg: #2B2312;
  --bar-bg: #22304A;
  --col-todo: #8B99AC;
  --col-design: #4CC3DE;
  --col-build: #8AACFF;
  --col-test: #EFB459;
  --col-blocked: #F27E9D;
  --col-done: #5FCE8A;
  --shadow: 0 1px 2px rgba(0, 0, 0, 0.35);
  --shadow-hover: 0 4px 14px rgba(0, 0, 0, 0.5);
"""

PALETTE_CSS = (
    ":root {" + _LIGHT_TOKENS + "}\n"
    "@media (prefers-color-scheme: dark) {\n"
    '  :root:not([data-theme="light"]) {' + _DARK_TOKENS + "}\n"
    "}\n"
    ':root[data-theme="dark"] {' + _DARK_TOKENS + "}\n"
)

BASE_CSS = """
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  padding: 1.25rem;
  background: var(--bg);
  color: var(--text);
  font-family: "Fira Sans", -apple-system, "Segoe UI", system-ui, sans-serif;
  font-size: 16px;
  line-height: 1.5;
}
.wrap { max-width: 1480px; margin: 0 auto; }
.mono, .card-id, .card-path, .tl-when, .tl-story, .kpi-value, .task-count,
.vel-lab, .vel-val, .col-count, .mast-sub {
  font-family: "Fira Code", ui-monospace, "Cascadia Mono", Consolas, monospace;
}

/* ---- masthead ---- */
.mast {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: 14px;
  box-shadow: var(--shadow);
  padding: 1.1rem 1.35rem;
  margin-bottom: 0.9rem;
  display: flex;
  flex-wrap: wrap;
  gap: 1.1rem 2rem;
  align-items: stretch;
}
.mast-id { min-width: 220px; }
.eyebrow {
  font-size: 0.66rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--accent-2);
  margin-bottom: 0.2rem;
}
h1 { font-size: 1.55rem; font-weight: 700; margin: 0 0 0.25rem; text-transform: capitalize; letter-spacing: -0.01em; }
.mast-sub { color: var(--text-dim); font-size: 0.72rem; }
.mast-goal {
  flex: 1 1 340px;
  background: var(--goal-bg);
  border-left: 3px solid var(--accent-2);
  border-radius: 10px;
  padding: 0.7rem 0.95rem;
  min-width: 280px;
}
.goal-label {
  font-size: 0.64rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-dim);
  margin-bottom: 0.25rem;
}
.goal-text { font-size: 0.95rem; font-weight: 500; line-height: 1.45; }
.goal-more { font-size: 0.76rem; color: var(--text-dim); margin-top: 0.35rem; line-height: 1.45; }
.mast-crew { display: flex; flex-direction: column; gap: 0.35rem; justify-content: center; }
.crew-row { display: flex; flex-wrap: wrap; gap: 0.35rem; }
.crew-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--badge-bg);
  color: var(--badge-text);
  border-radius: 999px;
  padding: 0.16rem 0.65rem 0.16rem 0.18rem;
  font-size: 0.74rem;
  font-weight: 500;
}
.crew-role { color: var(--text-dim); font-size: 0.6rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-right: 0.15rem; }

/* ---- KPI strip ---- */
.kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 0.7rem;
  margin-bottom: 0.9rem;
}
.kpi {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: 12px;
  box-shadow: var(--shadow);
  padding: 0.75rem 0.95rem;
}
.kpi-label {
  font-size: 0.64rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-dim);
  margin-bottom: 0.3rem;
}
.kpi-value { font-size: 1.45rem; font-weight: 600; line-height: 1.1; }
.kpi-sub { font-size: 0.7rem; color: var(--text-dim); margin-top: 0.3rem; line-height: 1.4; }
.kpi-bar { height: 6px; border-radius: 999px; background: var(--bar-bg); margin-top: 0.55rem; overflow: hidden; }
.kpi-bar-fill { display: block; height: 100%; border-radius: 999px; background: var(--accent); }

/* ---- analytics ---- */
.analytics {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  gap: 0.7rem;
  margin-bottom: 0.9rem;
}
.panel {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: 12px;
  box-shadow: var(--shadow);
  padding: 0.9rem 1.1rem;
  min-width: 0;
}
.panel > h2 {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-dim);
  margin: 0 0 0.65rem;
}
.burndown { width: 100%; max-width: 660px; height: auto; display: block; }
.bd-grid { stroke: var(--chart-grid); stroke-width: 1; }
.bd-axis { stroke: var(--chart-ideal); stroke-width: 1; }
.bd-ideal { stroke: var(--chart-ideal); stroke-width: 1.5; stroke-dasharray: 5 4; }
.bd-area { fill: var(--accent); opacity: 0.1; }
.bd-line { fill: none; stroke: var(--accent); stroke-width: 2.5; stroke-linejoin: round; stroke-linecap: round; }
.bd-dot { fill: var(--panel); stroke: var(--accent); stroke-width: 2; }
.bd-lab { fill: var(--text-dim); font-family: "Fira Code", monospace; font-size: 10px; }
.bd-val { fill: var(--text); font-weight: 600; font-size: 11px; }
.bd-insight { font-size: 0.78rem; color: var(--text-dim); margin-top: 0.55rem; line-height: 1.5; }
.bd-legend { display: flex; gap: 1rem; font-size: 0.68rem; color: var(--text-dim); margin-top: 0.3rem; }
.bd-legend .swatch { display: inline-block; width: 16px; height: 0; border-top: 2.5px solid var(--accent); vertical-align: middle; margin-right: 0.3rem; }
.bd-legend .swatch.ideal { border-top: 1.5px dashed var(--chart-ideal); }
.burndown-note, .empty-note { color: var(--text-dim); font-size: 0.8rem; font-style: italic; }

.timeline { list-style: none; margin: 0; padding: 0; }
.tl-item {
  display: flex;
  gap: 0.55rem;
  align-items: baseline;
  padding: 0.32rem 0;
  font-size: 0.76rem;
  border-bottom: 1px dashed var(--column-border);
}
.tl-item:last-child { border-bottom: none; }
.tl-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--col-todo); flex: none; align-self: center; }
.tl-dot.to-design { background: var(--col-design); }
.tl-dot.to-build { background: var(--col-build); }
.tl-dot.to-test { background: var(--col-test); }
.tl-dot.to-blocked { background: var(--col-blocked); }
.tl-dot.to-done, .tl-dot.to-shipped { background: var(--col-done); }
.tl-when { color: var(--text-dim); font-size: 0.64rem; flex: none; width: 5.2rem; }
.tl-story { font-weight: 600; font-size: 0.7rem; color: var(--accent); }
.tl-name { color: var(--text-dim); }

.vel { margin-top: 0.4rem; }
.vel-row { display: flex; align-items: center; gap: 0.5rem; margin: 0.3rem 0; }
.vel-lab { font-size: 0.68rem; color: var(--text-dim); width: 2.6rem; flex: none; }
.vel-bar { flex: 1; height: 10px; background: var(--bar-bg); border-radius: 999px; overflow: hidden; }
.vel-fill { display: block; height: 100%; background: var(--accent); border-radius: 999px; }
.vel-val { font-size: 0.7rem; font-weight: 600; width: 2.2rem; text-align: right; }

/* ---- board ---- */
.board-scroll { overflow-x: auto; padding-bottom: 0.3rem; }
.board {
  display: grid;
  grid-template-columns: repeat(6, minmax(200px, 1fr));
  gap: 0.7rem;
  min-width: 1230px;
}
.column {
  background: var(--column-bg);
  border: 1px solid var(--column-border);
  border-radius: 12px;
  padding: 0.55rem;
  min-height: 140px;
}
.column h3 {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-dim);
  margin: 0.1rem 0.2rem 0.55rem;
  padding: 0 0.15rem 0.45rem;
  border-bottom: 2px solid var(--col-todo);
}
.column.col-todo h3 { border-bottom-color: var(--col-todo); }
.column.col-design h3 { border-bottom-color: var(--col-design); }
.column.col-build h3 { border-bottom-color: var(--col-build); }
.column.col-test h3 { border-bottom-color: var(--col-test); }
.column.col-blocked h3 { border-bottom-color: var(--col-blocked); }
.column.col-done h3 { border-bottom-color: var(--col-done); }
.col-count {
  background: var(--panel);
  border-radius: 999px;
  padding: 0 0.5rem;
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--text);
}

.card {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-left-width: 3px;
  border-radius: 10px;
  padding: 0.55rem 0.65rem 0.5rem;
  margin-bottom: 0.55rem;
  font-size: 0.84rem;
  box-shadow: var(--shadow);
  transition: box-shadow 0.18s ease;
}
.card:hover { box-shadow: var(--shadow-hover); }
.card.st-committed { border-left-color: var(--col-todo); }
.card.st-design { border-left-color: var(--col-design); }
.card.st-build { border-left-color: var(--col-build); }
.card.st-test { border-left-color: var(--col-test); }
.card.st-blocked { border-left-color: var(--col-blocked); }
.card.st-done, .card.st-shipped { border-left-color: var(--col-done); }
.card.ungroomed { border-style: dashed; border-left-width: 1px; box-shadow: none; }
.card.st-backlog, .card.st-groomed { border-left-color: var(--col-todo); }
.card-top { display: flex; justify-content: space-between; align-items: center; gap: 0.4rem; }
.card-id { font-size: 0.72rem; font-weight: 600; color: var(--accent); }
.card-title { font-weight: 500; line-height: 1.35; margin: 0.15rem 0 0.4rem; }
.card-intent { color: var(--text-dim); font-size: 0.76rem; line-height: 1.4; margin-bottom: 0.35rem; }
.card-meta { display: flex; flex-wrap: wrap; gap: 0.3rem; align-items: center; margin-bottom: 0.45rem; }
.badge {
  background: var(--badge-bg);
  color: var(--badge-text);
  border-radius: 999px;
  padding: 0.08rem 0.5rem;
  font-size: 0.68rem;
  font-weight: 500;
}
.badge.risk-high { background: var(--badge-risk-high-bg); color: var(--badge-risk-high-text); }
.badge.risk-normal { background: var(--badge-risk-normal-bg); color: var(--badge-risk-normal-text); }
.card-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.4rem;
  padding-top: 0.4rem;
  border-top: 1px dashed var(--column-border);
}
.card-path {
  color: var(--text-dim);
  font-size: 0.62rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 46%;
}
.avatar-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: var(--chip-bg);
  color: var(--chip-text);
  border-radius: 999px;
  padding: 0.12rem 0.55rem 0.12rem 0.14rem;
  font-size: 0.72rem;
  font-weight: 600;
}
.avatar-dot {
  width: 1.2rem;
  height: 1.2rem;
  border-radius: 50%;
  background: var(--avatar-bg);
  color: var(--avatar-text);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: "Fira Code", monospace;
  font-size: 0.56rem;
  font-weight: 700;
  flex: none;
}
.avatar-chip.unclaimed { background: var(--unclaimed-bg); color: var(--unclaimed-text); font-weight: 400; padding: 0.12rem 0.55rem; }
.avatar-chip.pulsing { animation: pulse 1.6s ease-in-out infinite; }
@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 var(--accent); opacity: 1; }
  50% { box-shadow: 0 0 0 4px transparent; opacity: 0.75; }
}
@media (prefers-reduced-motion: reduce) {
  .avatar-chip.pulsing { animation: none; }
  .card, .card-tasks summary { transition: none; }
}
.empty-column { color: var(--text-dim); font-size: 0.78rem; font-style: italic; padding: 0.3rem 0.2rem; }

/* expandable granular tasks inside a story card (PO request 2026-08-21) */
.card-tasks { margin: 0 0 0.45rem; }
.card-tasks summary {
  cursor: pointer;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--accent);
  list-style: none;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.1rem 0.2rem;
  border-radius: 6px;
  transition: background 0.15s ease;
}
.card-tasks summary:hover { background: var(--badge-bg); }
.card-tasks summary::-webkit-details-marker { display: none; }
.card-tasks summary::before {
  content: "";
  display: inline-block;
  width: 0;
  height: 0;
  border-left: 5px solid currentColor;
  border-top: 4px solid transparent;
  border-bottom: 4px solid transparent;
  transition: transform 0.15s ease;
}
.card-tasks[open] summary::before { transform: rotate(90deg); }
.task-count { background: var(--badge-bg); color: var(--badge-text); border-radius: 999px; padding: 0 0.4rem; font-size: 0.64rem; }
.task-count.bug-open { background: var(--badge-risk-high-bg); color: var(--badge-risk-high-text); }
.task-kind {
  flex: none;
  font-size: 0.56rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-radius: 4px;
  padding: 0 0.3rem;
  align-self: center;
  background: var(--badge-bg);
  color: var(--badge-text);
}
.task-kind.k-test { background: var(--badge-risk-normal-bg); color: var(--badge-risk-normal-text); }
.task-kind.k-bug { background: var(--badge-risk-high-bg); color: var(--badge-risk-high-text); }
.card-tasks ul { list-style: none; margin: 0.35rem 0 0; padding: 0; }
.card-tasks .task {
  display: flex;
  gap: 0.45rem;
  align-items: baseline;
  font-size: 0.72rem;
  line-height: 1.4;
  padding: 0.22rem 0;
  border-bottom: 1px dashed var(--column-border);
  color: var(--text);
}
.card-tasks .task:last-child { border-bottom: none; }
.task-box {
  flex: none;
  width: 0.62rem;
  height: 0.62rem;
  border-radius: 3px;
  border: 1.5px solid var(--col-todo);
  align-self: center;
}
.task.done { color: var(--text-dim); }
.task.done .task-box { background: var(--col-done); border-color: var(--col-done); }

/* ---- backlog drawer ---- */
.backlog {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: 12px;
  box-shadow: var(--shadow);
  margin-top: 0.9rem;
}
.backlog > summary {
  cursor: pointer;
  padding: 0.85rem 1.15rem;
  font-weight: 600;
  font-size: 0.92rem;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  list-style: none;
}
.backlog > summary::-webkit-details-marker { display: none; }
.backlog > summary::before {
  content: "";
  display: inline-block;
  width: 0;
  height: 0;
  border-left: 6px solid var(--text-dim);
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  transition: transform 0.15s ease;
}
.backlog[open] > summary::before { transform: rotate(90deg); }
.backlog-counts { color: var(--text-dim); font-size: 0.74rem; font-weight: 400; }
.backlog-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 0.6rem;
  padding: 0 1.1rem 1.1rem;
}
.backlog-grid .card { margin-bottom: 0; }

/* ---- sprint documents (showcase / retro) ---- */
.sprint-doc {
  background: var(--panel);
  border: 1px solid var(--panel-border);
  border-radius: 12px;
  box-shadow: var(--shadow);
  padding: 1.1rem 1.4rem 1.3rem;
  margin-top: 0.9rem;
}
.sprint-doc > h2 {
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin: 0 0 0.9rem;
  padding-bottom: 0.6rem;
  border-bottom: 1px solid var(--panel-border);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.sprint-doc > h2::before {
  content: "";
  width: 0.62rem;
  height: 0.62rem;
  border-radius: 3px;
  background: var(--accent-2);
  flex: none;
}
.md h3 { font-size: 1.12rem; font-weight: 700; margin: 0.2rem 0 0.5rem; letter-spacing: -0.01em; }
.md h4 {
  font-size: 0.92rem;
  font-weight: 650;
  color: var(--accent);
  margin: 1.15rem 0 0.4rem;
  padding-top: 0.8rem;
  border-top: 1px dashed var(--column-border);
}
.md h3 + h4, .md h4:first-child { border-top: none; padding-top: 0; margin-top: 0.6rem; }
.md h5, .md h6 { font-size: 0.84rem; font-weight: 650; margin: 0.8rem 0 0.3rem; }
.md p { font-size: 0.86rem; line-height: 1.6; margin: 0.45rem 0; max-width: 82ch; }
.md ul, .md ol { margin: 0.45rem 0; padding-left: 1.4rem; }
.md li { font-size: 0.86rem; line-height: 1.55; margin: 0.3rem 0; max-width: 78ch; }
.md code {
  font-family: "Fira Code", ui-monospace, Consolas, monospace;
  font-size: 0.78em;
  background: var(--badge-bg);
  color: var(--text);
  padding: 0.08em 0.35em;
  border-radius: 4px;
}
.md strong { font-weight: 650; }
.md hr { border: none; border-top: 1px solid var(--panel-border); margin: 1rem 0; }
.tablewrap { overflow-x: auto; margin: 0.6rem 0; }
.md table { border-collapse: collapse; font-size: 0.8rem; min-width: 460px; }
.md th { text-align: left; background: var(--column-bg); font-weight: 600; }
.md th, .md td { border: 1px solid var(--panel-border); padding: 0.4rem 0.65rem; vertical-align: top; line-height: 1.5; }

.footer-note { color: var(--text-dim); font-size: 0.72rem; margin-top: 1.1rem; }

@media (max-width: 960px) {
  body { padding: 0.8rem; }
  .analytics { grid-template-columns: 1fr; }
  .mast { flex-direction: column; gap: 0.8rem; }
}
"""


_COL_SLUGS = {"To-Do": "todo", "Design": "design", "Build": "build", "Test": "test", "Blocked": "blocked", "Done": "done"}

_ROLE_ORDER = ["PO", "SM", "BA", "TechBA", "Dev", "Tester"]


def build_board_html(delivery: str, delivery_dir: Path, crew_path: Path) -> str:
    stories = load_stories(delivery_dir / "stories")
    known_story_ids = {s.id for s in stories}
    ungroomed = load_ungroomed_backlog_lines(delivery_dir / "backlog.md", known_story_ids)
    crew = resolve_crew(crew_path.parent)

    sprint_dir = newest_sprint_dir(delivery_dir)
    goal = None
    burndown = None
    showcase_text = None
    retro_text = None
    events: list = []
    sprint_id = sprint_dir.name if sprint_dir else None
    if sprint_dir is not None:
        goal = load_sprint_goal(sprint_dir / "plan.md")
        events = load_events(sprint_dir / "events.jsonl")
        burndown = compute_burndown(events, stories, sprint_id)
        showcase_text = load_optional_text(sprint_dir / "showcase.md")
        retro_text = load_optional_text(sprint_dir / "retro.md")

    velocity_text = load_velocity(delivery_dir / "velocity.md")

    columns: dict = {c: [] for c in COLUMNS}
    for story in stories:
        # A 'shipped' story from an earlier sprint would otherwise pile into
        # Done forever; only the current sprint's shipped work belongs here.
        if story.status == "shipped" and story.sprint != sprint_id:
            continue
        columns[STATUS_TO_COLUMN[story.status]].append(render_story_card(story, crew))
    groomed_count = len(columns["Backlog"])
    for title, intent, points, risk in ungroomed:
        columns["Backlog"].append(render_ungroomed_card(title, intent, points, risk))

    # ---- sprint columns (Backlog is a drawer below, so the sprint owns the width)
    column_html = []
    for name in COLUMNS:
        if name == "Backlog":
            continue
        cards = columns[name]
        body = "".join(cards) if cards else '<div class="empty-column">No cards</div>'
        column_html.append(
            f'<div class="column col-{_COL_SLUGS[name]}"><h3><span>{esc(name)}</span>'
            f'<span class="col-count">{len(cards)}</span></h3>{body}</div>'
        )

    # ---- masthead: goal split into headline + method/metric detail
    goal_head, goal_more = "No active sprint goal.", ""
    if goal:
        parts = re.split(r"\s+(?=Method:)", goal, maxsplit=1)
        goal_head = parts[0].strip()
        goal_more = parts[1].strip() if len(parts) > 1 else ""
        if goal_head.lower().startswith("goal:"):
            goal_head = goal_head[5:].strip()
    goal_more_html = f'<div class="goal-more">{esc(goal_more)}</div>' if goal_more else ""

    crew_chips = []
    for role in _ROLE_ORDER + [r for r in crew if r not in _ROLE_ORDER]:
        if role in crew:
            crew_chips.append(
                f'<span class="crew-chip"><span class="avatar-dot" aria-hidden="true">{esc(_initials(crew[role]))}</span>'
                f'<span><span class="crew-role">{esc(role)}</span>{esc(crew[role])}</span></span>'
            )
    crew_html = f'<div class="mast-crew"><div class="crew-row">{"".join(crew_chips)}</div></div>' if crew_chips else ""

    # ---- KPIs
    sprint_stories = [s for s in stories if sprint_id and s.sprint == sprint_id]
    total_pts = sum(points_as_number(s.points) for s in sprint_stories)
    done_pts = sum(points_as_number(s.points) for s in sprint_stories if s.status in ("done", "shipped"))
    done_count = sum(1 for s in sprint_stories if s.status in ("done", "shipped"))
    in_flight = [s for s in sprint_stories if s.status in PULSING_STATUSES]
    pct = round(done_pts / total_pts * 100) if total_pts else 0

    vel_rows = parse_velocity_rows(velocity_text) if velocity_text else []
    if vel_rows:
        window = vel_rows[-5:]
        vel_value = f"{sum(v for _, v in window) / len(window):g}"
        vel_sub = f"rolling avg of last {len(window)} sprint(s)"
    else:
        vel_value = "&mdash;"
        vel_sub = "first sprint &mdash; set when it closes"

    if in_flight:
        flight_sub = ", ".join(f"{s.id} in {STATUS_TO_COLUMN[s.status]}" for s in in_flight)
    else:
        flight_sub = "nothing mid-stage"

    kpis_html = ""
    if sprint_id:
        kpis_html = f"""<div class="kpis">
  <div class="kpi"><div class="kpi-label">Points burned</div>
    <div class="kpi-value">{done_pts:g} / {total_pts:g}</div>
    <div class="kpi-bar"><span class="kpi-bar-fill" style="width:{pct}%"></span></div>
    <div class="kpi-sub">{pct}% of the sprint forecast</div></div>
  <div class="kpi"><div class="kpi-label">Stories done</div>
    <div class="kpi-value">{done_count} / {len(sprint_stories)}</div>
    <div class="kpi-sub">Tester PASS is the only door to Done</div></div>
  <div class="kpi"><div class="kpi-label">In flight</div>
    <div class="kpi-value">{len(in_flight)}</div>
    <div class="kpi-sub">{esc(flight_sub)}</div></div>
  <div class="kpi"><div class="kpi-label">Velocity</div>
    <div class="kpi-value">{vel_value}</div>
    <div class="kpi-sub">{vel_sub}</div></div>
</div>"""

    # ---- analytics: burndown + insight, activity, velocity bars
    if burndown:
        remaining = total_pts - done_pts
        open_bits = [f"{s.id} ({points_as_number(s.points):g} pts, {STATUS_TO_COLUMN[s.status]})"
                     for s in sprint_stories if s.status not in ("done", "shipped")]
        insight = f"{done_pts:g} of {total_pts:g} points burned."
        insight += f" Open: {', '.join(open_bits)}." if open_bits else " All sprint stories are done."
        burndown_html = (
            render_burndown_svg(burndown)
            + '<div class="bd-legend"><span><span class="swatch"></span>actual remaining</span>'
              '<span><span class="swatch ideal"></span>ideal</span></div>'
            + f'<div class="bd-insight">{esc(insight)} Remaining: {remaining:g} pts.</div>'
        )
    else:
        burndown_html = '<div class="burndown-note">No burndown data yet &mdash; it appears with the first story done.</div>'

    act_items = []
    for r in humanize_events(events, crew):
        state = r["to"] if r["to"] in ("design", "build", "test", "blocked", "done", "shipped") else "todo"
        who = f' <span class="tl-name">&mdash; {esc(r["name"])}</span>' if r["name"] != "?" else ""
        story_span = f'<span class="tl-story">{esc(r["story"])}</span> ' if r["story"] else ""
        act_items.append(
            f'<li class="tl-item"><span class="tl-dot to-{state}" aria-hidden="true"></span>'
            f'<span class="tl-when">{esc(r["when"])}</span>'
            f"<span>{story_span}{esc(r['desc'])}{who}</span></li>"
        )
    activity_html = (
        f'<ul class="timeline">{"".join(act_items)}</ul>'
        if act_items else '<div class="empty-note">No activity recorded yet.</div>'
    )

    if vel_rows:
        vmax = max(v for _, v in vel_rows) or 1.0
        bars = "".join(
            f'<div class="vel-row"><span class="vel-lab">{esc(lab)}</span>'
            f'<span class="vel-bar"><span class="vel-fill" style="width:{v / vmax * 100:.0f}%"></span></span>'
            f'<span class="vel-val">{v:g}</span></div>'
            for lab, v in vel_rows[-6:]
        )
        velocity_html = f'<div class="vel">{bars}</div>'
    elif velocity_text:
        velocity_html = f'<p class="empty-note">{esc(velocity_text)}</p>'
    else:
        velocity_html = '<p class="empty-note">First sprint in flight &mdash; velocity is recorded when it closes.</p>'

    # ---- backlog drawer (kept out of the sprint's way; PO feedback 2026-08-21)
    backlog_cards = columns["Backlog"]
    idea_count = len(backlog_cards) - groomed_count
    backlog_body = "".join(backlog_cards) if backlog_cards else '<div class="empty-column">No cards</div>'
    backlog_html = f"""<details class="backlog">
  <summary>Backlog <span class="backlog-counts">{groomed_count} groomed stor{'y' if groomed_count == 1 else 'ies'} &middot; {idea_count} ungroomed item{'' if idea_count == 1 else 's'}</span></summary>
  <div class="backlog-grid">{backlog_body}</div>
</details>"""

    extra_sections = []
    if showcase_text:
        extra_sections.append(
            f'<section class="sprint-doc"><h2>Showcase &mdash; UAT sign-off</h2>'
            f'<div class="md">{md_to_html(showcase_text)}</div></section>'
        )
    if retro_text:
        extra_sections.append(
            f'<section class="sprint-doc"><h2>Retro</h2>'
            f'<div class="md">{md_to_html(retro_text)}</div></section>'
        )
    extra_sections_html = "".join(extra_sections)

    rendered_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sprint_chip = f"Sprint {esc(sprint_id)} &middot; " if sprint_id else ""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sprint Board — {esc(delivery)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
{PALETTE_CSS}
{BASE_CSS}
</style>
</head>
<body>
<div class="wrap">
<header class="mast">
  <div class="mast-id">
    <div class="eyebrow">Sprint board</div>
    <h1>{esc(delivery)}</h1>
    <div class="mast-sub">{sprint_chip}rendered {esc(rendered_at)}</div>
  </div>
  <div class="mast-goal">
    <div class="goal-label">Sprint goal</div>
    <div class="goal-text">{esc(goal_head)}</div>
    {goal_more_html}
  </div>
  {crew_html}
</header>
{kpis_html}
<div class="analytics">
  <div class="panel"><h2>Burndown</h2>{burndown_html}</div>
  <div>
    <div class="panel" style="margin-bottom:0.7rem"><h2>Latest activity</h2>{activity_html}</div>
    <div class="panel"><h2>Velocity</h2>{velocity_html}</div>
  </div>
</div>
<div class="board-scroll">
<div class="board">
{''.join(column_html)}
</div>
</div>
{backlog_html}
{extra_sections_html}
<p class="footer-note">Rendered {esc(rendered_at)} &middot; the board re-renders on every story transition (not self-refreshing)</p>
</div>
</body>
</html>
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Render a sprint delivery's board to self-contained HTML.")
    parser.add_argument("delivery", help="delivery name under <root>/deliveries/<delivery>")
    parser.add_argument("--out", required=True, help="output HTML file path")
    parser.add_argument("--root", default="sprint", help="sprint state root (default: sprint)")
    args = parser.parse_args(argv)

    root = Path(args.root)
    delivery_dir = root / "deliveries" / args.delivery
    crew_path = root / "crew.md"

    if not delivery_dir.is_dir():
        print(f"error: delivery directory not found: {delivery_dir}", file=sys.stderr)
        return 2

    try:
        board_html = build_board_html(args.delivery, delivery_dir, crew_path)
    except (BoardInputError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(board_html)

    # Staleness stamp (gitignored): any sprint phase compares the newest
    # events.jsonl mtime against this to enforce publish-on-transition.
    try:
        (delivery_dir / "board.stamp").write_text(
            datetime.now(timezone.utc).isoformat(timespec="seconds") + "\n", encoding="utf-8"
        )
    except OSError:
        pass  # a read-only checkout must not fail the render

    print(f"Board written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
