#!/usr/bin/env python3
"""Build the Sprint Office live-state document from real sprint files.

Emits `sprint/deliveries/<delivery>/office-state.json` — the ONLY thing the
office page needs to render real work. Reuses the board's parsers so there is
one interpretation of the state files, never two.

Consumed by:
  * scripts/sprint_office_kit.py  -> office_html(state) embeds it at publish
  * (future) the published page polling the same file through a GitHub
    connector, once that connector is authorised for the repo's org.

Run:  python scripts/sprint_office_state.py <delivery> [--root sprint]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sprint_board import (  # noqa: E402  (shared parsers, single source of truth)
    STATUS_TO_COLUMN, BoardInputError, humanize_events, load_events,
    load_crew_avatars, load_sprint_goal, load_stories,
    load_ungroomed_backlog_lines, newest_sprint_dir, points_as_number,
    resolve_crew,
)

# which role a status implies when a story carries no explicit holder
STATUS_ROLE_HINT = {"design": "TechBA", "build": "Dev", "test": "Tester",
                    "committed": "SM", "groomed": "BA", "blocked": "SM"}
ROLE_KEY = {"PO": "po", "SM": "sm", "BA": "ba", "TechBA": "techba",
            "Dev": "dev", "Tester": "tester"}
# status -> the beacon colour token the office lights at that desk
STATUS_BEACON = {"design": "design", "build": "build", "test": "test",
                 "blocked": "blocked", "done": "done", "shipped": "done",
                 "committed": "todo", "groomed": "todo", "backlog": "todo"}


def build_state(delivery: str, root: Path) -> dict:
    delivery_dir = root / "deliveries" / delivery
    if not delivery_dir.is_dir():
        raise BoardInputError(f"delivery directory not found: {delivery_dir}")

    stories = load_stories(delivery_dir / "stories")
    crew = resolve_crew(root)
    avatars = load_crew_avatars(root)
    sprint_dir = newest_sprint_dir(delivery_dir)
    sprint_id = sprint_dir.name if sprint_dir else None
    events = load_events(sprint_dir / "events.jsonl") if sprint_dir else []
    goal = load_sprint_goal(sprint_dir / "plan.md") if sprint_dir else None
    ungroomed = load_ungroomed_backlog_lines(
        delivery_dir / "backlog.md", {s.id for s in stories})

    sprint_stories = [s for s in stories if sprint_id and s.sprint == sprint_id]
    total_pts = sum(points_as_number(s.points) for s in sprint_stories)
    done_pts = sum(points_as_number(s.points) for s in sprint_stories
                   if s.status in ("done", "shipped"))

    roles = {}
    for role, key in ROLE_KEY.items():
        held = [s for s in sprint_stories if s.claimed_by == role]
        if not held:
            held = [s for s in sprint_stories
                    if not s.claimed_by.strip()
                    and STATUS_ROLE_HINT.get(s.status) == role]
        active = next((s for s in held if s.status not in ("done", "shipped")), None)
        showing = active or (held[0] if held else None)
        tasks_done = tasks_total = bugs_open = 0
        for s in held:
            for _label, is_done, kind in s.tasks:
                tasks_total += 1
                tasks_done += 1 if is_done else 0
                bugs_open += 1 if (kind == "bug" and not is_done) else 0
        roles[key] = {
            "role": role,
            "name": crew.get(role, role),
            "story": showing.id if showing else None,
            "title": showing.title if showing else None,
            "status": showing.status if showing else None,
            "beacon": STATUS_BEACON.get(showing.status, "todo") if showing else None,
            "idle": showing is None,
            "tasks_done": tasks_done, "tasks_total": tasks_total,
            "bugs_open": bugs_open,
            # the character this role wears, chosen with the name so the two
            # can never disagree; None -> renderer's built-in preset
            "avatar": avatars.get(role),
        }

    columns: dict = {}
    for s in sprint_stories:
        col = STATUS_TO_COLUMN[s.status]
        columns.setdefault(col, []).append({
            "id": s.id, "title": s.title, "points": s.points,
            "risk": s.risk, "status": s.status,
            "holder": crew.get(s.claimed_by, s.claimed_by) or None,
            "shipped": s.status == "shipped",
        })

    return {
        "schema": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "delivery": delivery,
        "sprint": sprint_id,
        "goal": goal,
        "points": {"done": done_pts, "total": total_pts,
                   "pct": round(done_pts / total_pts * 100) if total_pts else 0},
        "stories": {"done": sum(1 for s in sprint_stories
                                if s.status in ("done", "shipped")),
                    "total": len(sprint_stories)},
        "roles": roles,
        "columns": columns,
        "backlog": {"groomed": sum(1 for s in stories if s.status == "groomed"),
                    "ideas": len(ungroomed)},
        # full lists so the office's Backlog / Board / Story screens can render
        # real detail without a second data source
        "backlog_items": (
            [{"kind": "story", "id": s.id, "title": s.title, "points": s.points,
              "risk": s.risk, "status": s.status}
             for s in stories if s.status in ("backlog", "groomed")]
            + [{"kind": "idea", "id": None, "title": title, "intent": intent,
                "points": points, "risk": risk}
               for title, intent, points, risk in ungroomed]),
        "story_detail": [
            {"id": s.id, "title": s.title, "status": s.status, "points": s.points,
             "risk": s.risk, "repo": s.repo, "sprint": s.sprint,
             "holder": crew.get(s.claimed_by, s.claimed_by) or None,
             "column": STATUS_TO_COLUMN[s.status],
             "tasks": [{"label": lab, "done": done, "kind": kind}
                       for lab, done, kind in s.tasks]}
            for s in stories],
        "activity": humanize_events(events, crew, limit=8),
        "release": {
            "shipped": sum(1 for s in sprint_stories if s.status == "shipped"),
            "armed": any(e.get("to") == "shipped" for e in events),
        },
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Emit a delivery's office-state.json")
    ap.add_argument("delivery")
    ap.add_argument("--root", default="sprint")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    root = Path(args.root)
    try:
        state = build_state(args.delivery, root)
    except BoardInputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out = Path(args.out) if args.out else (
        root / "deliveries" / args.delivery / "office-state.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(state, indent=1), encoding="utf-8", newline="\n")
    print(f"office state written to {out} "
          f"({state['stories']['done']}/{state['stories']['total']} stories, "
          f"{state['points']['done']:g}/{state['points']['total']:g} pts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
