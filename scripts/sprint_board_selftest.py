#!/usr/bin/env python3
"""Self-test for scripts/sprint_board.py.

Builds synthetic delivery directories in temp dirs (no repo state needed),
runs the renderer against them as a subprocess (exercising the real CLI),
and asserts on the produced HTML / exit codes.

Run: python scripts/sprint_board_selftest.py
Expected on success: prints OK and exits 0.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

RENDERER = Path(__file__).resolve().with_name("sprint_board.py")


class SelfTestFailure(AssertionError):
    pass


def _run_renderer(root: Path, delivery: str, out_html: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(RENDERER), delivery, "--out", str(out_html), "--root", str(root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("utf-8"))


def _write_bom(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))


def test_basic_board_renders_all_columns_and_claimed_avatar() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "sprint"
        delivery = "demo"
        ddir = root / "deliveries" / delivery

        _write(root / "crew.md", (
            "# Sprint Crew\n\n"
            "## Crew\n"
            "| Role   | Name   | Seat            | Model policy |\n"
            "|--------|--------|-----------------|--------------|\n"
            # a PO name here must be IGNORED: the PO is always the active user
            "| PO     | Someone Else | human     | -- |\n"
            "| SM     | Riley  | lead session hat | frontier |\n"
            "| Dev    | Jordan | subagent        | opus/sonnet by story size |\n"
            "| Tester | Sam    | subagent, BLIND | always != Dev model |\n"
        ))

        _write(ddir / "backlog.md", (
            "# Backlog\n\n"
            "- [2] [normal] ST-001 — backlog seed story\n"
            "- [1] rough idea not yet groomed — something worth doing\n"
        ))

        _write(ddir / "stories" / "ST-001.md", (
            "---\n"
            "id: ST-001\n"
            "title: Backlog seed story\n"
            "type: story\n"
            "points: 2\n"
            "risk: normal\n"
            "repo: synora\n"
            "status: backlog\n"
            "claimed_by: \n"
            "sprint: \n"
            "---\n"
            "## Story\n"
            "As a PO, I want a seed story, so that grooming has material.\n"
        ))

        _write(ddir / "stories" / "ST-002.md", (
            "---\n"
            "id: ST-002\n"
            "title: In-flight build story\n"
            "type: story\n"
            "points: 3\n"
            "risk: high\n"
            "repo: synora\n"
            "status: build\n"
            "claimed_by: Dev\n"
            "sprint: S01\n"
            "---\n"
            "## Story\n"
            "As a PO, I want this built, so that it ships.\n"
        ))

        _write(ddir / "stories" / "ST-003.md", (
            "---\n"
            "id: ST-003\n"
            "title: Finished story\n"
            "type: story\n"
            "points: 5\n"
            "risk: normal\n"
            "repo: appstoneink\n"
            "status: done\n"
            "claimed_by: Tester\n"
            "sprint: S01\n"
            "---\n"
            "## Story\n"
            "As a PO, I want this done, so that it is shippable.\n"
        ))

        _write(ddir / "sprints" / "S01" / "plan.md", (
            "## Sprint goal\n"
            "Demo goal: prove the board renders.\n"
        ))

        _write(ddir / "sprints" / "S01" / "events.jsonl", (
            '{"actor": "Tester", "story": "ST-003", "from": "test", "to": "done", '
            '"timestamp": "2026-08-20T09:00:00+00:00", "work_product": null}\n'
            '{"actor": "Tester", "story": "ST-002", "from": "build", "to": "test", '
            '"timestamp": "2026-08-20T09:05:00+00:00", "work_product": null}\n'
        ))

        out_html = Path(tmp) / "board.html"
        result = _run_renderer(root, delivery, out_html)
        if result.returncode != 0:
            raise SelfTestFailure(
                f"renderer exited {result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
            )
        if not out_html.exists():
            raise SelfTestFailure("renderer did not write the output file")

        html = out_html.read_text(encoding="utf-8")

        if "Demo goal" not in html:
            raise SelfTestFailure("sprint goal 'Demo goal' missing from board")

        for heading in ("Backlog", "To-Do", "Design", "Build", "Test", "Blocked", "Done"):
            if heading not in html:
                raise SelfTestFailure(f"column heading {heading!r} missing from board")

        if "Jordan" not in html:
            raise SelfTestFailure("claimed story's crew name 'Jordan' missing from board")

        if "@keyframes" not in html:
            raise SelfTestFailure("@keyframes missing from board (no pulse animation defined)")

        if "prefers-reduced-motion" not in html:
            raise SelfTestFailure("prefers-reduced-motion handling missing from board")

        if "<svg" not in html:
            raise SelfTestFailure("burndown SVG missing even though events.jsonl has a done transition")


def test_po_is_always_the_active_user_never_the_crew_file() -> None:
    """A crew file must never be able to pin a person as PO: whoever runs the
    sprint is the PO. Regression for the 'PO defaulted to a real name' defect
    (PO instruction, 2026-08-22)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "sprint"
        _write(root / "crew.md", (
            "## Crew\n"
            "| Role | Name | Seat | Model policy |\n"
            "|------|------|------|--------------|\n"
            "| PO   | Someone Else | human | -- |\n"
            "| Dev  | Jordan | subagent | sonnet |\n"
        ))
        _write(root / "crew.local.md", (
            "| Role | Name | Seat | Model policy |\n"
            "|------|------|------|--------------|\n"
            "| PO   | Another Person | human | -- |\n"
        ))
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import sprint_board
        crew = sprint_board.resolve_crew(root)
        assert crew["PO"] not in ("Someone Else", "Another Person"), (
            f"crew file leaked a PO name: {crew['PO']!r}")
        assert crew["PO"], "PO must always resolve to something displayable"
        assert crew.get("Dev") == "Jordan", "other roles must still come from the file"


def test_crew_avatar_column_parses_and_is_optional() -> None:
    """The Avatar column drives the character; a crew.md without one must
    still load (older projects), yielding no avatars rather than an error."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "sprint"
        _write(root / "crew.md", (
            "## Crew\n"
            "| Role | Name | Seat | Model policy | Avatar |\n"
            "|------|------|------|--------------|--------|\n"
            "| Dev  | Robin | subagent | sonnet | bob:s2:#A8552F |\n"
        ))
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import sprint_board
        av = sprint_board.load_crew_avatars(root)
        assert av["Dev"] == {"hair": "bob", "skin": "s2",
                             "hair_colour": "#A8552F"}, av

        root2 = Path(tmp) / "sprint2"
        _write(root2 / "crew.md", (
            "## Crew\n"
            "| Role | Name | Seat | Model policy |\n"
            "|------|------|------|--------------|\n"
            "| Dev  | Robin | subagent | sonnet |\n"
        ))
        assert sprint_board.load_crew_avatars(root2) == {}, "no Avatar column -> {}"


def test_backlog_only_delivery_renders_without_crash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "sprint"
        delivery = "bare"
        ddir = root / "deliveries" / delivery

        _write(root / "crew.md", "# Sprint Crew\n\n## Crew\n| Role | Name | Seat | Model policy |\n|---|---|---|---|\n")

        _write(ddir / "backlog.md", (
            "# Backlog\n\n"
            "<!-- next grooming: start here -->\n"
            "- [3] [high] an ungroomed idea — worth exploring\n"
            "- BUG: something broke — fix eventually\n"
        ))
        # deliberately no stories/ dir and no sprints/ dir

        out_html = Path(tmp) / "board.html"
        result = _run_renderer(root, delivery, out_html)
        if result.returncode != 0:
            raise SelfTestFailure(
                f"backlog-only renderer exited {result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
            )

        html = out_html.read_text(encoding="utf-8")
        for heading in ("Backlog", "To-Do", "Design", "Build", "Test", "Blocked", "Done"):
            if heading not in html:
                raise SelfTestFailure(f"column heading {heading!r} missing from backlog-only board")

        if "an ungroomed idea" not in html:
            raise SelfTestFailure("ungroomed backlog line missing from Backlog column")

        if "something broke" not in html:
            raise SelfTestFailure("BUG-prefixed ungroomed backlog line missing from Backlog column")


def test_malformed_story_frontmatter_exits_2() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "sprint"
        delivery = "broken"
        ddir = root / "deliveries" / delivery

        _write(root / "crew.md", "# Sprint Crew\n\n## Crew\n| Role | Name | Seat | Model policy |\n|---|---|---|---|\n")
        _write(ddir / "backlog.md", "# Backlog\n\n- [1] ST-001 — a story\n")
        # missing the "status" key entirely -> malformed
        _write(ddir / "stories" / "ST-001.md", (
            "---\n"
            "id: ST-001\n"
            "title: Broken story\n"
            "type: story\n"
            "points: 1\n"
            "risk: normal\n"
            "repo: synora\n"
            "claimed_by: \n"
            "sprint: \n"
            "---\n"
            "## Story\n"
            "Missing status key above.\n"
        ))

        out_html = Path(tmp) / "board.html"
        result = _run_renderer(root, delivery, out_html)
        if result.returncode != 2:
            raise SelfTestFailure(
                f"expected exit 2 on malformed frontmatter, got {result.returncode}\n"
                f"stdout={result.stdout}\nstderr={result.stderr}"
            )
        combined = result.stdout + result.stderr
        if "ST-001.md" not in combined:
            raise SelfTestFailure("error message does not name the offending story file")
        if "status" not in combined:
            raise SelfTestFailure("error message does not name the missing/malformed key")


def test_status_outside_map_exits_2() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "sprint"
        delivery = "badstatus"
        ddir = root / "deliveries" / delivery

        _write(root / "crew.md", "# Sprint Crew\n\n## Crew\n| Role | Name | Seat | Model policy |\n|---|---|---|---|\n")
        _write(ddir / "backlog.md", "# Backlog\n\n")
        _write(ddir / "stories" / "ST-001.md", (
            "---\n"
            "id: ST-001\n"
            "title: Status outside the map\n"
            "type: story\n"
            "points: 1\n"
            "risk: normal\n"
            "repo: synora\n"
            "status: stalled\n"
            "claimed_by: \n"
            "sprint: \n"
            "---\n"
            "## Story\n"
            "A status value the board has no column for.\n"
        ))

        out_html = Path(tmp) / "board.html"
        result = _run_renderer(root, delivery, out_html)
        if result.returncode != 2:
            raise SelfTestFailure(
                f"expected exit 2 for a status outside STATUS_TO_COLUMN, got {result.returncode}\n"
                f"stdout={result.stdout}\nstderr={result.stderr}"
            )
        combined = result.stdout + result.stderr
        if "stalled" not in combined:
            raise SelfTestFailure("error message does not name the invalid status value 'stalled'")


def test_blocked_status_and_typed_tasks_render() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "sprint"
        delivery = "blockedtasks"
        ddir = root / "deliveries" / delivery

        _write(root / "crew.md", "# Sprint Crew\n\n## Crew\n| Role | Name | Seat | Model policy |\n|---|---|---|---|\n| SM | Sam | lead hat | n/a |\n")
        _write(ddir / "backlog.md", "# Backlog\n\n")
        _write(ddir / "stories" / "ST-001.md", (
            "---\n"
            "id: ST-001\n"
            "title: A story parked on a PO decision\n"
            "type: story\n"
            "points: 3\n"
            "risk: high\n"
            "repo: synora\n"
            "status: blocked\n"
            "claimed_by: SM\n"
            "sprint: S01\n"
            "---\n"
            "## Story\n"
            "As a PO, I want blocked work visible, so nothing stalls silently.\n"
            "## Tasks\n"
            "- [x] [build] wire the widget\n"
            "- [ ] [test] blind-verify the widget\n"
            "- [ ] [bug] widget eats the config on save\n"
        ))
        _write(ddir / "sprints" / "S01" / "plan.md", "## Sprint goal\nBlocked goal.\n")

        out_html = Path(tmp) / "board.html"
        result = _run_renderer(root, delivery, out_html)
        if result.returncode != 0:
            raise SelfTestFailure(
                f"blocked status should render, got exit {result.returncode}\n"
                f"stdout={result.stdout}\nstderr={result.stderr}"
            )
        html = out_html.read_text(encoding="utf-8")
        if "col-blocked" not in html:
            raise SelfTestFailure("Blocked column styling missing from board")
        if 'class="card st-blocked"' not in html:
            raise SelfTestFailure("blocked story card missing its st-blocked class")
        if 'class="task-kind k-bug"' not in html:
            raise SelfTestFailure("typed [bug] task chip missing from the card task view")
        if "1 bug open" not in html:
            raise SelfTestFailure("open-bug count missing from the task summary")
        if "wire the widget" not in html:
            raise SelfTestFailure("'## Tasks' section items missing from the card task view")


def test_bom_events_file_renders_fine() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "sprint"
        delivery = "bom"
        ddir = root / "deliveries" / delivery

        _write(root / "crew.md", "# Sprint Crew\n\n## Crew\n| Role | Name | Seat | Model policy |\n|---|---|---|---|\n")
        _write(ddir / "backlog.md", "# Backlog\n\n")
        _write(ddir / "stories" / "ST-001.md", (
            "---\n"
            "id: ST-001\n"
            "title: BOM tolerance story\n"
            "type: story\n"
            "points: 3\n"
            "risk: normal\n"
            "repo: synora\n"
            "status: done\n"
            "claimed_by: Tester\n"
            "sprint: S01\n"
            "---\n"
            "## Story\n"
            "As a PO, I want BOM-safe reads, so PowerShell redirection does not break the board.\n"
        ))
        _write(ddir / "sprints" / "S01" / "plan.md", "## Sprint goal\nBOM goal.\n")
        _write_bom(ddir / "sprints" / "S01" / "events.jsonl", (
            '{"actor": "Tester", "story": "ST-001", "from": "test", "to": "done", '
            '"timestamp": "2026-08-20T09:00:00+00:00", "work_product": null}\n'
        ))

        out_html = Path(tmp) / "board.html"
        result = _run_renderer(root, delivery, out_html)
        if result.returncode != 0:
            raise SelfTestFailure(
                f"BOM'd events.jsonl should render fine, got exit {result.returncode}\n"
                f"stdout={result.stdout}\nstderr={result.stderr}"
            )
        html = out_html.read_text(encoding="utf-8")
        if "<svg" not in html:
            raise SelfTestFailure("burndown SVG missing for a BOM'd events.jsonl (BOM should be tolerated)")


def test_non_dict_event_line_exits_2() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "sprint"
        delivery = "baddevent"
        ddir = root / "deliveries" / delivery

        _write(root / "crew.md", "# Sprint Crew\n\n## Crew\n| Role | Name | Seat | Model policy |\n|---|---|---|---|\n")
        _write(ddir / "backlog.md", "# Backlog\n\n")
        _write(ddir / "stories" / "ST-001.md", (
            "---\n"
            "id: ST-001\n"
            "title: Event shape story\n"
            "type: story\n"
            "points: 2\n"
            "risk: normal\n"
            "repo: synora\n"
            "status: build\n"
            "claimed_by: \n"
            "sprint: S01\n"
            "---\n"
            "## Story\n"
            "As a PO, I want malformed events caught, so the board never lies.\n"
        ))
        _write(ddir / "sprints" / "S01" / "plan.md", "## Sprint goal\nEvent goal.\n")
        _write(ddir / "sprints" / "S01" / "events.jsonl", '"done"\n')

        out_html = Path(tmp) / "board.html"
        result = _run_renderer(root, delivery, out_html)
        if result.returncode != 2:
            raise SelfTestFailure(
                f"expected exit 2 on a valid-JSON non-object event line, got {result.returncode}\n"
                f"stdout={result.stdout}\nstderr={result.stderr}"
            )
        combined = result.stdout + result.stderr
        if "line 1" not in combined:
            raise SelfTestFailure("error message does not name the offending events.jsonl line")


def test_claimed_by_none_renders_unclaimed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "sprint"
        delivery = "noneclaim"
        ddir = root / "deliveries" / delivery

        _write(root / "crew.md", "# Sprint Crew\n\n## Crew\n| Role | Name | Seat | Model policy |\n|---|---|---|---|\n")
        _write(ddir / "backlog.md", "# Backlog\n\n")
        _write(ddir / "stories" / "ST-001.md", (
            "---\n"
            "id: ST-001\n"
            "title: Freshly scaffolded story\n"
            "type: story\n"
            "points: 1\n"
            "risk: normal\n"
            "repo: synora\n"
            "status: backlog\n"
            "claimed_by: none\n"
            "sprint: \n"
            "---\n"
            "## Story\n"
            "As a PO, I want the template default respected, so scaffolds show Unclaimed.\n"
        ))

        out_html = Path(tmp) / "board.html"
        result = _run_renderer(root, delivery, out_html)
        if result.returncode != 0:
            raise SelfTestFailure(
                f"renderer exited {result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
            )
        html = out_html.read_text(encoding="utf-8")
        if "Unclaimed" not in html:
            raise SelfTestFailure("claimed_by: none should render the Unclaimed chip")
        if ">none<" in html:
            raise SelfTestFailure("claimed_by: none rendered literally as a phantom crew member")


def test_missing_story_file_exits_2() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "sprint"
        delivery = "danglingref"
        ddir = root / "deliveries" / delivery

        _write(root / "crew.md", "# Sprint Crew\n\n## Crew\n| Role | Name | Seat | Model policy |\n|---|---|---|---|\n")
        _write(ddir / "backlog.md", "# Backlog\n\n- [2] [normal] ST-999 — a story with no file\n")
        # deliberately no stories/ dir at all

        out_html = Path(tmp) / "board.html"
        result = _run_renderer(root, delivery, out_html)
        if result.returncode != 2:
            raise SelfTestFailure(
                f"expected exit 2 when backlog references a missing story file, got {result.returncode}\n"
                f"stdout={result.stdout}\nstderr={result.stderr}"
            )
        combined = result.stdout + result.stderr
        if "ST-999" not in combined:
            raise SelfTestFailure("error message does not name the missing story ref ST-999")
        if "backlog.md" not in combined:
            raise SelfTestFailure("error message does not name backlog.md")


def test_comment_block_backlog_line_is_ignored() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "sprint"
        delivery = "commented"
        ddir = root / "deliveries" / delivery

        _write(root / "crew.md", "# Sprint Crew\n\n## Crew\n| Role | Name | Seat | Model policy |\n|---|---|---|---|\n")
        _write(ddir / "backlog.md", (
            "# Backlog\n\n"
            "<!--\n"
            "- [2] [high] a fake card left in an example comment — should never render\n"
            "-->\n"
            "- a real ungroomed idea — should render\n"
        ))

        out_html = Path(tmp) / "board.html"
        result = _run_renderer(root, delivery, out_html)
        if result.returncode != 0:
            raise SelfTestFailure(
                f"renderer exited {result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
            )
        html = out_html.read_text(encoding="utf-8")
        if "a fake card" in html:
            raise SelfTestFailure("a backlog line inside an HTML comment block rendered as a card")
        if "a real ungroomed idea" not in html:
            raise SelfTestFailure("real ungroomed backlog line missing from the Backlog column")


def test_risk_only_bracket_renders_risk_badge_not_points() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "sprint"
        delivery = "riskonly"
        ddir = root / "deliveries" / delivery

        _write(root / "crew.md", "# Sprint Crew\n\n## Crew\n| Role | Name | Seat | Model policy |\n|---|---|---|---|\n")
        _write(ddir / "backlog.md", (
            "# Backlog\n\n"
            "- [high] (ungroomed) C2: RLS bypass — fix the security_invoker regression\n"
        ))

        out_html = Path(tmp) / "board.html"
        result = _run_renderer(root, delivery, out_html)
        if result.returncode != 0:
            raise SelfTestFailure(
                f"renderer exited {result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
            )
        html = out_html.read_text(encoding="utf-8")
        if "highpt" in html:
            raise SelfTestFailure("a lone '[high]' risk bracket was mis-parsed as a points badge ('highpt')")
        if 'class="badge risk-high"' not in html:
            raise SelfTestFailure("a lone '[high]' risk bracket did not render the high-risk badge")
        if "(ungroomed) C2" in html:
            raise SelfTestFailure("leading '(ungroomed)' marker was not stripped from the card title")


def test_showcase_and_retro_render_with_story_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "sprint"
        delivery = "docs"
        ddir = root / "deliveries" / delivery

        _write(root / "crew.md", "# Sprint Crew\n\n## Crew\n| Role | Name | Seat | Model policy |\n|---|---|---|---|\n")
        _write(ddir / "backlog.md", "# Backlog\n\n")
        story_path = ddir / "stories" / "ST-001.md"
        _write(story_path, (
            "---\n"
            "id: ST-001\n"
            "title: Story with a path\n"
            "type: story\n"
            "points: 1\n"
            "risk: normal\n"
            "repo: synora\n"
            "status: build\n"
            "claimed_by: \n"
            "sprint: S01\n"
            "---\n"
            "## Story\n"
            "As a PO, I want the card to name its file, so I can jump straight to it.\n"
        ))
        _write(ddir / "sprints" / "S01" / "plan.md", "## Sprint goal\nDocs goal.\n")
        _write(ddir / "sprints" / "S01" / "showcase.md", "# Showcase\nDemoed the sprint board renderer fixes.\n")
        _write(ddir / "sprints" / "S01" / "retro.md", "# Retro\nWhat went well: the fixes landed clean.\n")

        out_html = Path(tmp) / "board.html"
        result = _run_renderer(root, delivery, out_html)
        if result.returncode != 0:
            raise SelfTestFailure(
                f"renderer exited {result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
            )
        html = out_html.read_text(encoding="utf-8")
        if "Demoed the sprint board renderer fixes" not in html:
            raise SelfTestFailure("showcase.md content missing from the rendered board")
        if "What went well" not in html:
            raise SelfTestFailure("retro.md content missing from the rendered board")

        expected_path = str(story_path).replace("\\", "/")
        if expected_path not in html:
            raise SelfTestFailure("story's file path missing from its card")


def main() -> int:
    tests = [
        test_basic_board_renders_all_columns_and_claimed_avatar,
        test_po_is_always_the_active_user_never_the_crew_file,
        test_crew_avatar_column_parses_and_is_optional,
        test_backlog_only_delivery_renders_without_crash,
        test_malformed_story_frontmatter_exits_2,
        test_status_outside_map_exits_2,
        test_blocked_status_and_typed_tasks_render,
        test_bom_events_file_renders_fine,
        test_non_dict_event_line_exits_2,
        test_claimed_by_none_renders_unclaimed,
        test_missing_story_file_exits_2,
        test_comment_block_backlog_line_is_ignored,
        test_risk_only_bracket_renders_risk_badge_not_points,
        test_showcase_and_retro_render_with_story_path,
    ]
    for test in tests:
        try:
            test()
        except SelfTestFailure as exc:
            print(f"FAIL: {test.__name__}: {exc}")
            return 1
        except Exception as exc:  # unexpected error inside a test
            print(f"ERROR: {test.__name__}: {exc!r}")
            return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
