---
name: sprint
description: Run agile delivery end to end with an AI crew — backlog grooming, sprint planning, a blind build/test loop, showcase with owner go-live approval, retro — over file-based delivery state in the current project, with a published sprint board and an isometric Sprint Office visual. Use for sprints, grooming, sprint planning, running a sprint, showcase, retrospective, backlog work, delivery status, or opening the sprint office/board.
---

# Agile Sprint — AI-crew agile delivery

Design (NORMATIVE): `${CLAUDE_PLUGIN_ROOT}/docs/design-spec.md`.
Practice reference (NORMATIVE, load on demand): `${CLAUDE_PLUGIN_ROOT}/docs/agile-practitioner-reference.md`.
Templates: `${CLAUDE_PLUGIN_ROOT}/skills/sprint/templates/`.
**Delivery state lives in the CURRENT PROJECT under `sprint/`** — never in the plugin.
The project's binding gates live in that project's `sprint/RAILS.md` (Law 6).

## Invocation and context discipline

`/agile-sprint:sprint <delivery> <phase>` — phases: `office | groom | plan | run | showcase |
retro | status | archive | crew`. `crew` takes no delivery argument and is a reserved word —
never a valid delivery name. No delivery named → list `sprint/deliveries/*` (never `_archive/`)
and ask. New delivery name → ask the PO to name the delivery's owner (the ONLY person who can
approve go-live), then scaffold it from the templates (`backlog.md` + `velocity.md`, with that
name on the `owner:` line; `stories/` and `sprints/` are created as needed).

**Phase: office** — the visual way in. Rebuild the state, re-render, republish, and hand the PO
the link (nothing else):
```
python ${CLAUDE_PLUGIN_ROOT}/scripts/sprint_office_state.py <delivery>
python ${CLAUDE_PLUGIN_ROOT}/scripts/sprint_office_kit.py --delivery <delivery>
```
Both write into the PROJECT: `sprint/deliveries/<delivery>/office-state.json` and
`sprint/deliveries/<delivery>/office.html`. Then publish that `office.html` with the Artifact
tool (`capabilities:{artifact:{}}`, `url:` from `sprint/deliveries/<delivery>/office.url`; on the
FIRST publish write the returned URL there). **Always pass `--delivery`** — the state file is
per-delivery precisely so two deliveries can never share one office, and the renderer refuses to
fall back to another delivery's state. ALWAYS read the page's `#reqlog` first (see Board
publishing) and act on anything unhandled. The office is a small app: Office / Board / Backlog /
Sprint / Ask-the-crew screens plus clickable hotspots in the room — all in-page views over
`office-state.json`, so they can never disagree with the board.

Load ONLY: `sprint/crew.md`, the named delivery's `backlog.md`, its CURRENT sprint folder, and the
story files actually being worked — plus, at plan/retro time, the delivery's `velocity.md` and the
PREVIOUS sprint's `retro.md` (actions + counts only). Never other deliveries, never `_archive/`,
never whole story trees. Nothing sprint-sized goes into auto-memory — state lives in these files;
any session resumes by reading them.

**Crew name resolution (every run):** names come from `sprint/crew.md` (shared defaults),
overridden by `sprint/crew.local.md` when present (per-user, gitignored — same table format,
only rows being overridden). A rename changes LIVE chips (board, office, plates) only —
names already written into showcase/retro prose stay as history and are never retro-edited. The PO's display name is the ACTIVE USER: `git config user.name`.
Display names carry NO authority (see Law 8). Names appear on every board card.

**Phase: crew** — `/sprint crew` personalizes names for THIS user only: show the current
effective names, ask the user for their preferred names (any/all of SM, BA, TechBA, Dev,
Tester), write `sprint/crew.local.md` with only the overridden rows, confirm. `crew.local.md`
must be exactly: a `## Crew` heading, then the same |Role|Name|Seat|Model policy| table containing
only the overridden rows. Never edit `sprint/crew.md` for a personal rename; never commit
`crew.local.md`.

## Laws (binding in every phase)

1. **Independence:** no agent ever verifies work it built or specified. The SM never builds and
   never marks a story done — only a Tester PASS does. The Tester is BLIND (receives the story +
   frozen AC only, never the dev's reasoning) and always runs on a **different model than the Dev,
   Sonnet minimum**; high-risk stories get a frontier tester, optionally a Codex cross-family
   second opinion.
2. **The BA never answers FOR the PO.** An open PO question halts the story — it never gets guessed.
3. **Definition of Ready gates the sprint:** a story enters planning only with its DoR checklist
   fully ticked (see the story template). No bare titles into a sprint.
4. **Acceptance criteria FREEZE at planning** (log a `frozen` event per story). Later edits are
   scope changes: logged as events, visible at showcase, never silent.
5. **Claiming and write-sets:** the sprint plan's Forecast table allocates each story a dev seat, a
   tester seat, and a declared write-set; parallel stories must have DISJOINT write-sets. A session
   working a story logs a `claim` event (actor = session tag) before advancing it and may only
   advance stories it claimed. `claimed_by` in story frontmatter holds the crew ROLE currently
   holding the story (drives the board avatar); set it at every hand-off.
6. **The project's delivery rails are binding.** Read `sprint/RAILS.md` in the CURRENT project at
   the start of every phase and obey it as if written here: it holds that project's build,
   promotion and safety gates (type-check and lint commands, migration/deploy rules, environment
   hazards, mirrored repos). A rail is not advice — a story cannot be `done`, and nothing may be
   promoted, while a rail is unmet, and each rail's stated command must actually be RUN and its
   exit code reported, never assumed. If `sprint/RAILS.md` does not exist, say so plainly and ask
   the owner what the project's gates are before the first story reaches `build` — never invent
   rails, and never silently proceed without any.
7. **Regression is read-only.** A non-production environment may still reach real customers
   (live pipelines, copied production data — see the project's rails); the regression pack never
   sends, arms, or mutates.
8. **A promotion to the production branch happens ONLY on a showcase Approval record** (the
   owner's exact words + timestamp in showcase.md). Follow the project's rails for HOW to promote
   and what to do afterwards. Pushes to the working branch during a sprint follow the project's
   standing push policy. **Approval authority belongs to the DELIVERY'S OWNER** (the `owner:` line
   in the delivery's backlog header) — the PO display name showing the active user never transfers
   that authority; a non-owner session records the showcase and STOPS, telling the user the owner
   must approve. Approval is always the owner's recorded words: never a click, never inferred.
9. **Zero undisclosed defects:** Sev-1/Sev-2 defects block the sprint; lower severity ships only as
   a documented Accepted exception with the PO's quote.
10. **Event log is the record:** every story transition appends one line to the sprint's
    `events.jsonl` — `{"actor": <crew role>, "story": "ST-###", "from": <state>, "to": <state>,
    "timestamp": <iso8601+tz>, "work_product": <path/commit/report link or null>, "event":
    <optional>}`. `actor` is the crew ROLE (SM/BA/TechBA/Dev/Tester) for story transitions;
    `claim` events use the session tag; display names never appear in events.jsonl. States:
    backlog, groomed, committed, design, build, test, blocked, done, shipped (`committed` is a
    state label meaning pulled-into-the-forecast; spoken/written language stays forecast, never
    commitment; a FAIL is an event `to:"build"` with the defect report as work_product;
    `blocked` = parked on a complex/PO-needed blocker per the bug-tier rule in run step 3b). The
    optional `"event"` field marks non-transition entries: `"event": "claim"` (from/to `null`)
    when a session claims a story; `"event": "frozen"` (from/to `null`) when acceptance criteria
    freeze at planning. The board re-renders after every transition. **Before the delivery's
    first sprint folder exists, transition events (e.g. backlog→groomed) append to the
    DELIVERY-level `sprint/deliveries/<delivery>/events.jsonl`** — never into story History as a
    substitute. **Every date or timestamp written into any file is minted from the wall clock at
    write time** (run `date`), never recalled from session memory — a session that crosses
    midnight otherwise stamps yesterday (defect, 2026-08-21).

## Definition of Done

A story is DONE only when: Tester PASS on frozen AC · every gate in the project's
`sprint/RAILS.md` run and passing (Law 6) · CI green on the working branch · every transition
event logged (Law 10) · all defects disclosed per Law 9. `retro.md`'s velocity line counts points meeting this bar.

## Phase: groom (PO + BA hat)

**BA language rule (PO, 2026-08-20): every PO-facing question is asked in plain business English.**
One short paragraph of background first (what this is, why it matters to the business), then the
question and options phrased as business consequences — never mechanisms. Technical identifiers
(table/view/function names, RLS, crons, migrations) belong in the story file, not the interview;
the BA translates them. If a question cannot be asked without jargon, the BA does not yet
understand it well enough to ask — go back and understand it first. This is the conduit skill the
BA role exists for.

1. Open `backlog.md`; walk the TOP items only (DEEP — never refine the tail).
2. Interview the PO **one question at a time** to turn top items into story files (copy
   `templates/story.md`, next `ST-###` — scoped PER DELIVERY: next = highest number present in that
   delivery's `stories/` + 1; IDs are never reused or renumbered): Connextra one-liner, business
   case, AC in the right style (behavior → Gherkin; rules → checklist), regression notes sketched
   WITH the AC, risk + repo tags. Theme/epic items are CHUNKED into INVEST-sized stories: the epic
   stays in the backlog as the parent line; each child story carries the optional `epic:` key.
3. **Independent estimation:** obtain three estimates per story WITHOUT cross-contamination — the
   BA hat estimates first and records it privately; then dispatch TechBA and Dev seats each with the
   story file ONLY (no other estimate mentioned) to return points + any open questions/DoR concerns
   — modified Fibonacci: 0,1,2,3,5,8,13,20 (larger = split the story). The BA records each open item
   with an OWNER in the story History; a story with open PO questions cannot tick DoR (ties to Law
   2). Divergence >1 step → surface the divergent reasoning; the PO clarifies scope; the three
   estimating seats set the final number. Record all four numbers in the story History (they feed
   plan.md's table at planning).
4. Tick the DoR checklist honestly; a story that fails DoR stays `backlog`; one that passes becomes
   `groomed` (event logged).
5. Reorder the backlog with the PO; close by showing the sprint-ready set.

## Phase: plan (SM hat)

1. **WHY:** PO frames the value; write the sprint goal as ONE outcome (never a story list).
2. **WHAT:** pull `groomed` stories only, against honest capacity (a sprint is scope-boxed — no
   calendar padding; the forecast is a FORECAST, never a commitment). **Smallness rule (PO,
   2026-08-20): pull the SMALLEST story set that achieves one sprint goal — a one-story sprint is
   normal; when in doubt, pull less.** Only the NEXT sprint is ever planned: never lay out a
   sprint roadmap or predict how many sprints remain — the backlog and velocity answer that, not
   a plan. Capacity signal = the rolling
   3–5-sprint average in `velocity.md`; a first sprint uses judgment and says so in `plan.md`. The
   pulled set must form one promotable increment: fill in `## Promotable increment statement` and
   `## Couplings`, and check the migration queue for unpromoted versions beneath ours (if found:
   STOP, tell the PO).
3. **HOW:** allocate dev/tester seats per crew.md policy (tester model ≠ dev model, Sonnet minimum,
   frontier tester on high-risk), declare write-sets, verify disjointness.
4. Create `sprints/S##/` (next number — two digits, zero-padded: S01, S02, ...; a story's `sprint:`
   frontmatter must equal the folder name exactly), write `plan.md` from the template, set pulled
   stories to `committed` with `frozen` events for their AC, and publish the board (see Board
   publishing).

## Phase: run (SM orchestrates; never builds)

Per story, in write-set-safe parallel where allocated:
1. `design`: dispatch the **TechBA** seat with the story file + pointers to the live system docs it
   names. Output goes INTO the story's Tech design section. TechBA may REJECT (back to grooming
   with the reason — event logged). Conversational, follow-ups expected.
2. `build`: dispatch the **Dev** seat with the story file (now incl. tech design), the write-set as
   a hard boundary, and the rails of Law 6. Dark-by-default. Dev commits locally with task-scoped
   messages; never pushes.
3. `test`: dispatch the **Tester** BLIND — a fresh agent, different model than the dev, given the
   story's one-liner + FROZEN AC + regression notes + the diff/paths ONLY (never dev notes or this
   session's reasoning). Verdict PASS/FAIL; the Tester's verdict + defect record are written to
   `sprints/S##/test-reports/ST-###.md`, and that path is the work_product of the test-transition
   event. FAIL → 8-field defect record (environment/build · preconditions · numbered repro ·
   expected quoted from AC · actual literal · timestamped evidence · severity+owner · priority +
   off-diagonal justification) → triage on the severity×priority matrix (practitioner ref §4: the
   diagonal is the default — Critical→P1 fix immediately … Low→P4 eventually): the Tester sets
   SEVERITY with evidence; the SM proposes PRIORITY on the diagonal; the PO confirms priority
   (off-diagonal needs recorded justification). Sev-1/2 → fix in-sprint (story back to `build`);
   P3 → `BUG:` backlog item for the next sprint; P4 → backlog tail. P3/P4: the Tester re-issues a
   verdict excluding the deferred defect — PASS-with-deferred-defect moves the story to `done`; the
   defect MUST appear in showcase.md's Accepted exceptions with the PO's quote before the story may
   ship.
3b. **Bug tiers (PO policy, 2026-08-21) — applied to every defect found at ANY point, not just
   Tester FAILs.** When a bug is found, a NEW work item is ALWAYS created to complete: a typed
   `- [ ] [bug] ...` line in the story's `## Tasks` section (board cards live-show these), or a
   `BUG:` backlog item when it outlives the story. Then route by tier:
   - **EASY** → fix it NOW; it stays with the current owner (no hand-off, no ceremony); tick the
     task when confirmed.
   - **NEEDS BRAINSTORMING** → the item goes to To-Do; an agent seat picks it up and brainstorms
     the resolution before any fix.
   - **COMPLEX / BLOCKED / PO NEEDED** → the story moves to `blocked` (event logged; the board's
     Blocked column). The SM FIRST tries to remove the blocker or brings it to the PO for
     guidance; if it cannot be cleared in-sprint, the story returns to the backlog for
     prioritisation (event `blocked → groomed`, `sprint:` cleared) and a backlog item records
     the blocker.
   These tiers route WHO acts and WHERE the work sits; Law 9's severity rules still decide
   whether the sprint may ship.
4. PASS → story `done` (only the Tester's PASS does this). Every transition: event + board
   republish + `claimed_by` updated to the holding role. **Work flows Build → Test → Done BEFORE
   any showcase — a card never waits in Build for a ceremony** (PO, 2026-08-21).
5. The SM narrates progress toward the SPRINT GOAL in-session (this IS the standup — there is no
   ceremony; walk the board work-focused, never per-agent status), halts EARLY to the PO on any
   blocker needing a PO decision or a story blowing well past its estimate, and keeps the foreman
   ledger exactly as today. With the PO's decision, a story may be DE-SCOPED: event
   `<current-state> → groomed`, note it in `plan.md`'s Forecast table. This is normal forecast
   adjustment, not failure.

## Phase: showcase (the go-live gate)

0. **ALL-RESOLVED GATE (PO principle, 2026-08-21, verbatim: "by the time it gets to showcase and
   retro everything should be confirmed built and gone through testing — nothing should be
   picked up in showcase").** Before opening: every story in the sprint must be resolved — `done`
   (Tester PASS) or explicitly de-scoped back to `groomed`. ANY story still in committed/design/
   build/test/blocked → REFUSE to open the showcase; tell the PO exactly which stories are
   unresolved and what each is waiting on. The showcase is presentation-only; discovery ended
   before it opened.
1. Run the read-only regression pack (per the stories' regression notes + the delivery's standing
   checks; on this repo: counter expectations, coverage view, queue depths, trigger states,
   the project's standing regression checks named in `sprint/RAILS.md`).
2. Fill `showcase.md` from the template — it IS the UAT sign-off packet. DONE work only; tell the
   sprint-goal story, never task-by-task accounting; quantify day-one prod impact.
3. Present to the PO. Record the decision VERBATIM with timestamp in `## Approval record`.
4. Only a recorded approval authorizes: promotion per the increment statement, same-window
   coupling arming, the post-promotion watch (define it in the packet), and any branch
   equalization the project's rails require.
   Refusal withholds RELEASE only: done stories stay done/unshipped and are never demoted; new
   requirements or rework go on the backlog as NEW items. Stories promote to `shipped` only after
   the approved push lands.

## Phase: retro

1. FIRST: count last retro's actions closed vs opened — say the number. Then walk the sprint's
   burndown and velocity trend with the PO (the "did we get better?" read).
2. Fill `retro.md`: went well / didn't / unrecorded-deviations count (headline metric, target
   zero — an unrecorded deviation found here is a process failure to root-cause, not a note).
3. Agree 1–3 owned actions with the PO. Update `velocity.md` (points meeting the Definition of
   Done this sprint; rolling 3–5 average; wall-clock as a stat). Velocity is a planning signal for
   the crew ONLY — never a target, never a cross-delivery comparison. Seed the next sprint's
   candidate set.
4. Every story not `done` at retro reverts to `groomed` (event `to:"groomed"`, `sprint:` cleared,
   `claimed_by` cleared); it re-enters the next planning explicitly — never rides across sprints.

## Phase: status / archive

- `status`: render + publish the board; give the PO a one-paragraph text summary (sprint goal,
  stories by state, blockers, next PO decision needed).
- `archive`: ONLY on the PO saying the delivery is finished — `git mv` the delivery folder into
  `sprint/deliveries/_archive/`, commit, confirm it no longer lists.

## Board publishing

Render: `python ${CLAUDE_PLUGIN_ROOT}/scripts/sprint_board.py <delivery> --out <scratchpad>/board-<delivery>.html` (run
from the project root, or pass `--root <project>/sprint` explicitly). Publish with the
Artifact tool (favicon stable per delivery). On the delivery's FIRST publish, write the returned
artifact URL to `sprint/deliveries/<delivery>/board.url`; every later publish passes `url:` from
that file (fallback: Artifact `action:"list"` if the file is missing) — the local render path no
longer matters for URL stability. Load the `artifact-design` skill before the first board publish
of each session. Republish after every transition (transitions applied together in one action may
share one republish); never hand-write board HTML — fix the renderer instead.

**The Sprint Office (live visual, 2026-08-22).** The office is a second view over the SAME
state, published alongside the board:
```
python ${CLAUDE_PLUGIN_ROOT}/scripts/sprint_office_state.py <delivery>            # -> office-state.json (real state)
python ${CLAUDE_PLUGIN_ROOT}/scripts/sprint_office_kit.py --delivery <delivery>   # -> office.html
```
Then publish `sprint/deliveries/<delivery>/office.html` with the Artifact tool, keeping its URL in
`sprint/deliveries/<delivery>/office.url` exactly as `board.url` works. **Regenerate the state
and republish the office on the SAME transitions that republish the board** — that is what keeps
it live; there is no polling today. Also **push the delivery's state files to the test-tier
branch on every transition** (state files only — never migrations), so the office and board can
be re-derived by any session and so the future connector-polling upgrade has something to read.
Nothing about the office may invent workflow: it renders `office-state.json`, which is built
from the story files, `events.jsonl` and `crew.md` by the board's own parsers.

*Not yet live-polling:* true auto-refresh needs the claude.ai GitHub connector authorised for the
repo's org (verified 2026-08-22: the connector cannot see `VoxnexAI/*`, so the page must not call
it — a page must never ship a connector call whose real response has not been observed).

**Tap-to-request controls (2026-08-22).** The office is published with `capabilities:
{artifact: {}}`, which makes its markup a LIVE DOCUMENT: a PO tap on an "Ask the crew" button
appends a row to `#reqlog` and that change is saved as them. Publish it that way every time, or
the buttons stop persisting. Per-viewer controls (theme, ambient) sit inside `<artifact-local>`
so one viewer's preference never lands on everyone else's page; keep it that way.

**Reading requests (do this at the START of any `/sprint` invocation, and whenever the PO says
they tapped something):** `WebFetch` the delivery's `office.url` and look for `#reqlog` rows —
each carries `data-phase` (groom|plan|run|status|retro|showcase|unblock) and `data-requested-at`
(ISO). Treat an unhandled row as the PO asking for that phase: run it through the normal
procedure — a request NEVER shortcuts a gate. Specifically `showcase` still requires the
all-resolved gate, and no row can approve a release: **Law 8 stands, approval is the owner's
recorded words, never a click.** After handling a row, note it in the sprint's events/records so
the same request is not served twice, and republish the office so the log reflects reality.

**Staleness enforcement (deviation B, 2026-08-21):** the renderer writes
`sprint/deliveries/<delivery>/board.stamp` (gitignored) on every render. On ENTERING any phase,
compare the delivery's newest `events.jsonl` mtime against `board.stamp` — if events are newer
(or the stamp is missing), render + republish FIRST, before doing anything else. A published
board that disagrees with events.jsonl is a recorded deviation, not a cosmetic lag. The board
also live-shows each card's granular tasks (the `## Tasks` / Tech-design checklists, typed
`[build]`/`[test]`/`[bug]`) — keep those checklists ticked as work lands or the expand view lies.

## References

- Staff guide (share with team members; plain-language agile background): `${CLAUDE_PLUGIN_ROOT}/skills/sprint/ONBOARDING.md`
- Design spec: `${CLAUDE_PLUGIN_ROOT}/docs/design-spec.md`
- Practitioner reference (agendas, formats, anti-patterns): `${CLAUDE_PLUGIN_ROOT}/docs/agile-practitioner-reference.md`
- Templates: `${CLAUDE_PLUGIN_ROOT}/skills/sprint/templates/` (story, backlog, plan, showcase, retro)
- Renderer: `${CLAUDE_PLUGIN_ROOT}/scripts/sprint_board.py` (self-test: `${CLAUDE_PLUGIN_ROOT}/scripts/sprint_board_selftest.py`)
