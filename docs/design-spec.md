# Sprint Skill — Design

Date: 2026-08-20 · Status: APPROVED by the Product Owner after interview · Author: lead session (facilitating)

## 1. Purpose and scope

A project skill (`/sprint`) that runs agile delivery end to end for this codebase: short, scope-boxed
sprints, each ending in a promotable increment, a showcase with explicit Product Owner go-live
approval, a retrospective, a regression pass, and next-sprint planning.

**V1 is StoneInk-first.** This repo's hard delivery rules are first-class citizens inside the skill,
not abstracted config. A generic, shareable version is a later epic (section 8) extracted only after
the loop is proven on real deliveries. Dev on all product work is PAUSED until this skill exists and
the first sprint is planned (PO, 2026-08-20).

## 2. Roles and crew

| Role | Seat | Model | Notes |
|---|---|---|---|
| Product Owner | **The active user** — whoever is running the sprint | — | Vision, priorities, grooming answers, showcase GO-LIVE approval. The only human gate. Never a name stored in the tool. |
| Scrum Master + Business Analyst | Lead session (hats) | Frontier (Fable-class) | Interviews the PO, writes stories/business cases, plans, routes, unblocks. MAY NEVER build. MAY NEVER mark a story done. |
| Technical BA | Named subagent | Frontier | Translates stories into tech designs against the live system; may REJECT a story as unbuildable/conflicting (independent check #1). |
| Developer | Named subagent | Opus/Sonnet by story size | Builds dark-by-default. Never tests own work. |
| Tester | Named subagent, BLIND | **Always ≠ Developer's model.** Sonnet minimum; Fable on high-risk stories; optional Codex cross-family second opinion on the riskiest | Fresh context; receives ONLY the story + frozen acceptance criteria, never the dev's reasoning. Sole authority to mark a story done (independent check #2). |

Standing independence law: **no agent ever verifies work it built or specified.** The PO's showcase
approval is independent check #3.

**Crew naming (amended 2026-08-20, PO decision):** `sprint/crew.md` ships DEFAULT names for the
five AI roles (Maya/Oliver/Priya/Marcus/Elena — 3F/2M, the closest split five allows). The PO's
display name is the ACTIVE USER (`git config user.name`), never hardcoded. Per-user renames via
the `/sprint crew` phase write `sprint/crew.local.md` (gitignored) — each user sees their own
names; the shared defaults never change. Display names carry NO authority: go-live approval
belongs to the DELIVERY'S OWNER (`owner:` header in the delivery backlog),
and a non-owner session must stop at showcase and defer to the owner.

## 3. Sprint lifecycle and ceremonies

Sprints are **scope-boxed, never time-boxed**: a sprint is its committed story set and ends at the
showcase. No human-calendar padding — multiple sprints per day is normal. The only real clocks are
the PO's ceremonies. The SM halts the sprint early to the PO (fail-early) when a blocker needs a PO
decision or a story blows well past its estimate.

1. **Backlog grooming** (PO + BA hat, per sprint or on demand): interview, refine; top of backlog
   detailed with frozen-able acceptance criteria, bottom stays rough. Points proposed by BA
   (1/2/3/5/8), confirmed by PO. Risk tier tagged per story (high-risk = prod money paths, customer
   comms, migration queue).
2. **Sprint planning** (SM hat): commit a story set that forms ONE promotable increment; **freeze
   acceptance criteria** (the tester's contract); allocate seats/models; declare write-sets.
3. **Build loop** per story: TechBA design → Dev build (dark-by-default) → blind Test →
   PASS = done / FAIL = fix in-sprint or log a bug. Bugs are backlog items defaulting to the next
   sprint.
4. **Regression pass** before showcase: the read-only check pack (counters, coverage view, queue
   depths, trigger states, campaign_action_log name sweep, prod strike simulation where relevant).
   Read-only by law — test-env can email real customers.
5. **Showcase**: evidence page — what shipped, diffs, test verdicts, regression results, day-one
   impact. Then the gate: **the PO approves go-live here, and this is the ONLY place a push to main
   may ever be authorized.** On approval: promote, arm same-window couplings, post-promotion watch.
6. **Retro**: went-well / didn't / one-change; velocity update; **headline metric: unrecorded
   deviations, target zero** (the deviation-register discipline from the 2026-08-20 audit).
7. **Next-sprint planning seed** closes the loop.

## 4. Data model — deliveries, stories, events

All state lives in files; the skill is stateless and any session can resume a sprint by reading the
delivery folder. Nothing sprint-sized ever enters auto-memory (pointers only).

```
sprint/
  crew.md                      # named crew, model mapping, standing config (small, shared)
  deliveries/
    <delivery>/                # one business initiative (may span both repos; stories carry repo tags)
      backlog.md               # live product backlog, priority-ordered, detailed at top
      stories/ST-###.md        # one file per story (see below)
      sprints/S##/             # plan.md, allocations, test-reports/, showcase.md, retro.md, events.jsonl
      velocity.md              # per-delivery velocity history
    _archive/                  # finished deliveries moved here whole (out of every listing/load)
```

- **Story file:** business case (BA), acceptance criteria (FROZEN at planning), tech design
  (TechBA), points, risk tier, repo tag, status, `claimed_by`, history.
- **Event log** (`events.jsonl`, per sprint): every transition as
  `{actor, story, from, to, timestamp, work_product}` — where `work_product` links the real diff /
  test report / design doc. Event-log-not-just-current-state is deliberate: it is the data spine for
  the future live board and office-sim skin (replay + animation) and costs nothing now.
- **Context discipline:** the skill loads crew.md + the named delivery's backlog + current sprint
  folder + only the story files being worked. Never other deliveries, never `_archive/`.
- **Invocation:** `/sprint <delivery> <phase>` — phases: `groom | plan | run | showcase | retro |
  status | archive`.
- **Concurrency:** stories carry `claimed_by`; a session may only advance stories it claimed;
  parallel claims must have disjoint write-sets. Git referees underneath (state files committed), so
  violations surface as conflicts, not silent corruption. Heavier locking is a backlog story only if
  real contention appears.

## 5. Gates and Definition of Done (StoneInk rails, baked in)

A story is DONE only when: built dark-by-default; blind-tested PASS against frozen acceptance
criteria; repo gates green (`npx tsc -b` exit 0; deno baselines exactly 25/2 where touched); drift
scan when any shared supabase file is touched (both repos byte-identical); migration files
full-clock-versioned, CI-deployed only, duplicate-version check after any fetch/rebase.

A sprint is PROMOTABLE only when: its migrations form a contiguous version block; every coupling
(cron arming, cutover toggles) is resolved INSIDE the same sprint and armed in the same window as
promotion; the regression pack passes; the showcase evidence is complete. Promotion to main happens
only on the PO's explicit showcase approval (matches the standing push policy); after any main push,
test-env is equalized to the identical commit. Standing rules X-01/X-02/X-03 from the delivery-plan
workbook apply verbatim.

## 6. Artifacts and visuals (v1)

One persistent **Sprint Board artifact** per delivery (stable URL): columns Backlog → To-Do →
Design → Build → Test → Done; named avatar chips with ambient CSS motion (idle/typing pulses);
sprint goal; burndown (points remaining over events); velocity history; links to story files.
Republished at EVERY state transition — honest framing: it updates when work moves; it is not yet
self-refreshing (that is Epic 1, section 8). Showcase and retro render into the same page at sprint
end.

## 7. Velocity, bugs, retro artifacts

Velocity = points per sprint, per delivery. Wall-clock is a reported stat, never a boundary. Bugs
found by the Tester become backlog items (type: bug) defaulting to the next sprint. Retro output is
`retro.md` (went-well / didn't / one-change / unrecorded-deviation count) and feeds the next
planning.

## 8. Roadmap epics (seeded into the first backlog; NOT v1)

"First backlog" here means the skill-product delivery's own backlog
(`sprint/deliveries/sprint-skill/backlog.md`) — not the `arrangement` delivery, which stays
isolated to arrangement work per the delivery-isolation rule (section 4).

Theme: **Watch the crew work** — the marketable layer. Design principle locked now:
**nothing on screen that isn't real** — every pixel is a view over actual sprint state.

- **Epic 1 — Live self-updating board:** the page refreshes itself while watched, via the artifact
  runtime `mcp` capability (watchTool + refetchInterval, verified available on this account).
  Requires mirroring sprint state somewhere a claude.ai connector can read (state table vs repo file
  via connector — TechBA decides in the story). Cards animate on state change.
- **Epic 2 — Office-sim skin:** isometric cartoon office (Canvas, self-contained): crew at desks,
  state-driven motion (tester walks to dev's desk on FAIL), **clickable avatars** → role, current
  assignment, story links; **real screens** — each desk's monitor renders the actor's actual work
  product from the event log (real diff, real verdict). No fake activity, ever.
- **Epic 3 — Interactive in-browser grooming:** the PO grooms on the board page itself (reorder,
  edit, comment) via the artifact runtime's live-doc capability. Carries a real design problem to
  solve in its story: browser edits vs repo files is a two-masters situation — the sync-back
  contract (files remain source of truth; board edits land as proposed changes the BA applies) is
  decided by the TechBA then.
- **Epic 4 — Marketplace packaging:** extract generic core (StoneInk rails → per-project config);
  **new separate repo, born clean** (no StoneInk data in any commit, ever — a delivery's content
  never leaves its private repo); sign-up onboarding (name your crew); demo mode on synthetic data;
  open-core distribution (free skill core for reach; the visual board is the paid layer).
  OPEN ITEM for the PO: which entity owns the product repo (personal vs company) — decide before Epic 4.

## 9. Build order of the skill's own delivery (PO decision, 2026-08-20)

All epics are IN the product; none is cut. Sequenced so real delivery is never blocked and the
visuals bind to a sprint-proven data model:

1. **Sprint A — the core** (this implementation plan): skill, delivery workspaces, event log, flat
   board with ambient avatar motion. The moment it lands, REAL arrangement sprints start in
   parallel (C2, promotion runbook).
2. **Sprint B — Epic 1** (live self-updating board).
3. **Sprints C+ — Epic 2** (office-sim, incrementally), then **Epic 3** (browser grooming),
   then **Epic 4** (marketplace) when the PO calls it.

Constant exclusions regardless of sprint: Codex-by-default testing (escalation-only); multi-team
coordination beyond story claiming. Product-code changes stay paused only until sprint 1 of the
arrangement delivery is planned through this skill.

## 10. Practitioner-research adoptions (normative)

`docs/superpowers/research/2026-08-20-agile-practitioner-reference.md` (deep research, ~60 cited sources)
is a NORMATIVE input to the implementation plan and ships with the skill as crew reference material. Its
§7 adoptions bind the build — headline additions to this design: a **Definition of Ready** hard pull-in
gate; the Connextra story format with the Gherkin-vs-checklist AC decision rule; **independent estimation**
(BA/TechBA/Dev estimate blind, divergence >1 step discussed); outcome-form sprint goals and forecast (never
commitment) language; retro opens by counting last retro's closed actions (1–3 owned actions max); the
severity×priority bug-triage matrix with "zero UNDISCLOSED defects" DoD; **the showcase page structured as
a regulated UAT sign-off packet** (scope · cycle log · defect register · accepted exceptions · approval
record with the PO's exact words · evidence appendix). Its §7 also records the three resolved conflicts
(review-as-stage-gate vs release authorization; planning allocations vs JIT claiming; BA hat vs proxy-PO —
standing rule: the BA never answers FOR the PO; open PO questions halt the story, never get guessed).

## 11. First delivery

`sprint/deliveries/arrangement/` seeded from the parked state of the 2026-08-20 audit: correction C2
(RLS on the side-by-side views), the promotion runbook (block promotion + canceller arming as a
sprint), audit questions Q2–Q5 as grooming items, P2-07/P2-14/P2-15, and the audit watch items
(dishonour Day-0 volume, 1 Sep quarterly first-fire). C1 is already fixed and committed locally
(`ba3a11abf`, unpushed) — its promotion belongs to the first sprint the PO approves.
