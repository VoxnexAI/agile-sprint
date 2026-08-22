# Agile Delivery in Practice — Practitioner Reference

Date: 2026-08-20 · Purpose: ground the sprint skill (design: `docs/superpowers/specs/2026-08-20-sprint-skill-design.md`)
in real-world practice, not textbook theory or the PO interview alone. Compiled from three parallel research
passes (~60 cited sources, 9 deep-read). Claims supported by only one source are marked UNVERIFIED.
This document ships with the skill as reference material for the crew agents.

## 1. Roles as actually practiced

| Role | Inputs | Outputs | Hands to | Good looks like | Classic failure |
|---|---|---|---|---|---|
| Product Owner | Customer/stakeholder signal, tech constraints | Ordered backlog, sprint goal, AC, decisions | Team | Deep customer AND tech understanding; owns "what", stays out of "how" | "Backlog administrator" — order-taking clerk (svpg.com/product-manager-vs-product-owner) |
| Business Analyst | Stakeholder needs, PO priorities | User stories, requirement models, AC | Developers DIRECTLY | Facilitates direct PO↔dev conversation; just-barely-good-enough docs | **Proxy PO** — a go-between that slows decisions and demoralizes (romanpichler.com/blog/business-analysts-in-scrum) |
| Technical BA / solution designer | Approved stories, system constraints | Tech specs, solution designs, NFRs | Dev (build), QA (test conditions) | Bridges what/how collaboratively, in real time, follow-ups expected | Finished spec dumped before dev = waterfall gate inside a sprint (agilemodeling.com/essays/businessanalysts.htm) |
| Developer | Story + frozen AC + DoD | Working increment, tests, dev notes | QA, PO | Self-organizes task breakdown; coordinates, doesn't report | Standup as status report to a manager figure |
| Tester / QA | Increment, AC, DoD | Defect reports w/ repro, regression coverage, verdict | Dev (defects), PO (acceptance) | **Tests to break, not confirm**; independent mindset; shift-left | End-of-sprint bottleneck OR dissolved into dev with no adversarial check (blogs.zeiss.com — tester independence) |
| Scrum Master | Team friction, impediments | Removed impediments, well-run events, coaching | Whole team | Servant-leader; nearly invisible when it works | "PM in disguise": status-taking, metrics-as-weapon (agilealliance.org/scrum-master-anti-patterns) |

Key practice facts: refinement is whole-team, not PO homework (scrum.org forum); the Scrum Guide has NO BA
role — real teams slot BAs as (1) PO, (2) team member, or (3) the proxy-PO anti-pattern (Pichler); Cagan:
PO-as-subset-of-PM causes mutual disrespect when split across people (svpg).

## 2. Ceremony agendas as actually run

**Backlog refinement** (Atlassian + DEEP): walk TOP items only → clarify → split too-big → estimate → flag
missing info w/ owner → check against Definition of Ready → reconfirm order. Backlog is **DEEP**: Detailed
appropriately (top only), Estimated, Emergent, Prioritized (Cohn, mountaingoatsoftware.com). Pre-2020 rule of
thumb: ~10% capacity on refinement. Anti-patterns: refinement by PO+lead clique; items entering planning as
bare titles; over-refining ("marginal return… zero or negative", Wolpers).

**Sprint planning** (Scrum Guide 2020's three topics): (1) WHY — PO frames value, team drafts the **sprint
goal as an OUTCOME**, not a task list (Pichler's goal/method/metrics template); (2) WHAT — pull ready items
against capacity; language is **forecast, not commitment** (2011 guide change — scope adjustment mid-sprint
is normal, not failure); (3) HOW — break into tasks. Human anti-pattern: task pre-assignment at planning
creates bottlenecks; mature teams sign up just-in-time.

**Daily standup**: 2020 guide prescribes NO format — only "inspect progress toward the sprint goal."
Mature teams walk the board (work-focused) rather than person-by-person status; async standups are
legitimate; "the standup a great team has outgrown" is a real maturity signal (teamretro.com).

**Sprint review / showcase** (Wolpers' 15 anti-patterns, scrum.org): live demo of DONE work only — never
slideware ("Death by PowerPoint"), never undone work ("Undone is the new Done"), never task-by-task
accounting ("Sprint Accounting" — tell the story of the sprint goal). **"Scrum à la Stage-Gate" is a named
anti-pattern**: item-level acceptance belongs continuously DURING the sprint, decoupled from the review.
(See §7 for how our design resolves this against the regulated go-live gate.)

**Retrospective**: pick a format (start/stop/continue, 4Ls, sailboat, or data-driven using cycle-time
trends); root causes not symptoms; **decide 1–3 owned actions max**; **open the NEXT retro by counting how
many of last retro's actions closed** — that number is the team's real improvement rate
(funretrospectives.com). Never-changing no-action retros = "Groundhog Day" (Wolpers).

## 3. Artifacts and formats

**Story template** (Connextra/Cohn): `As a <role>, I want <capability>, so that <benefit>` — narrative stays
one sentence; **acceptance criteria live separately** and contain only conditions whose failure means the PO
rejects the item. Graded by INVEST before estimation.

**AC style decision rule**: behavior/workflow/multi-outcome → **Gherkin** (Given/When/Then; scenarios can
become tests); flat validation/permission/quality conditions → **checklist**. No single format fits all
(altexsoft.com). AC are frozen at sprint pull-in via the DoR; any later change is a tracked scope change,
never a silent edit.

**Estimation**: planning poker on modified Fibonacci (0,1,2,3,5,8,13,20,40,100); private simultaneous
estimates specifically to kill anchoring; points = relative effort (work+risk+uncertainty+complexity), never
time; "once one point equals one day, relative estimation turns back into time estimation" (Cohn). Velocity
= sum of points on stories meeting DoD, forecast from the **last 3–5 sprints**, and is a planning signal for
the team only — never a management target or cross-team comparison. #NoEstimates is a real school (count
similar-sized stories instead); the Ron Jeffries disavowal quote is UNVERIFIED (secondary attribution).

**Definition of Ready** (real example, boost.co.nz): INVEST-conformant + prioritized + assets attached +
understood by whole team incl. risks + external reviewers booked. DoR is a team convention (no Scrum Guide
anchor) — but the small-scale-Scrum experience report found **DoR mattered more than any single ceremony**
at tiny scale (agilealliance.org experience report).

**Definition of Done** (real example, boost.co.nz): tests passing · security scan passing · CI green ·
cross-browser/mobile per analytics · accessibility · peer review · docs updated · AC met. Common defect
variant: **no Sev-1/Sev-2 defects at sprint end; lower-severity defects may ship only with documented
acceptance** — zero *undisclosed* defects, not zero defects (productplan.com, zenexmachina.com). Work not
meeting DoD does not count toward velocity.

**Board columns**: Scrum default To Do → In Progress → Done; regulated/larger teams commonly extend with
Code Review → QA → Ready for Release (Atlassian).

## 4. Quality flow and the regulated go-live gate

**Bug triage** — severity (technical, evidence-owner) × priority (business, context-owner); the diagonal is
the default (Critical→P1-hotfix-now … Low→P4-eventually, auto-close ~6 months); off-diagonal needs explicit
justification (bugreel.io). Rule of thumb: P1/P2 in-sprint, P3 next sprint, P4+ backlog (plane.so).

**Regression cadence**: CI on every merge; a targeted pack tied to the sprint's stories before the
review/demo; broader suite pre-release. Regression scope is sketched WITH the AC at refinement, not bolted
on after (browserstack.com; ISTQB).

**UAT / go-live sign-off in regulated financial services** — informal sign-off is a compliance violation,
not just bad practice (debugg.ai). Evidence must be reproducible · attributable · timed · verifiable ·
durable. The **sign-off packet** (citesvue.com — practitioner framework, UNVERIFIED as an official
standard, but well-formed): scope statement · cycle log · defect register · **accepted exceptions** (known
defects explicitly approved, with the approval quote) · approval record (who/when/exact words) · evidence
appendix. Banking-agile framing: compliance is embedded in AC from refinement and demonstrated AT the
review; "Regulations are Not Agile" (bridgeforce.com, single-firm framing). CABs in mature shops audit the
process and reserve manual review for high-risk changes only (Atlassian).

**Defect record, 7 fields**: environment/build · preconditions · numbered repro steps · expected (quoted
from AC) · actual (literal) · evidence (timestamped) · severity + owner.

## 5. Scrum Guide 2020 deltas that matter

Product Goal→backlog / Sprint Goal→sprint backlog / DoD→increment as explicit per-artifact commitments;
"self-organizing"→"self-managing" (team decides who/how/WHAT); no sub-teams; three-questions standup format
removed; 10%-refinement guidance dropped from text; overall "minimally sufficient." Mature divergences:
Scrumban for volatile priorities; #NoEstimates; continuous delivery decoupling "shippable" from sprint end.

## 6. Tiny teams and AI crews

Small-scale Scrum (experience report): keep planning/review/retro shrunk, drop the separate sprint backlog,
add informal demo checkpoints, flex sprint length down to days; **DoR is the highest-value practice**. Solo
practitioners: keep a timeboxed-ish loop and one prioritized backlog; the merged PO+dev role removes checks
and balances — pull in outside feedback deliberately. AI-crew precedents: Scrum.org draws the line at
delegating PO *tasks* (ticket mining, story drafting, release notes) while ownership stays human; the
copilot-scrum-team repo keeps the human as **sponsor, not coordinator**, with per-role agents and defined
artifacts; the AI-Scrum blog (UNVERIFIED, self-flagged unproven) warns that **the smaller the sprint, the
MORE upfront spec precision matters** and that setup overhead dominates small sprints.

## 7. Design implications for OUR sprint skill (adoptions + resolved conflicts)

**Adopted into the skill** (will appear in the implementation plan):
1. **Definition of Ready checklist** as a hard pull-in gate (INVEST + AC written + points + risk tier) —
   research says this is the single highest-value practice at our scale. Extends spec §3 step 2.
2. Story file = Connextra one-liner + separate AC; **AC style by decision rule** (Gherkin for behavior,
   checklist for rules).
3. **Independent estimation**: BA, TechBA and Dev estimate each story independently before seeing each
   other's numbers (planning-poker anchoring control, agent-native); divergence >1 step triggers discussion.
4. Sprint goal written as an **outcome** (Pichler); "forecast" language, never "commitment".
5. Retro opens by **counting last retro's closed actions**; max 1–3 owned actions; deviation-register
   count stays the headline metric.
6. Velocity from last 3–5 sprints, per delivery, team-signal only.
7. **Bug triage matrix** (severity × priority, diagonal default, off-diagonal justified); P1/P2 in-sprint,
   P3 next sprint; DoD adopts "zero UNDISCLOSED defects": Sev-1/2 block, lower ships only as a documented
   accepted exception.
8. **The showcase page IS the UAT sign-off packet**: scope · cycle log · defect register · accepted
   exceptions · approval record (the PO's exact words, timestamped) · evidence appendix. This is the audit
   trail a regulated collections business needs anyway.
9. Regression scope sketched with AC at grooming, not invented at sprint end.
10. No standup ceremony: the event log + board IS a continuous walked board; SM narrates and halts-early
    on blockers (2020-guide-compliant — format is free).
11. Review tells the sprint-goal story with evidence of DONE work only — no task-by-task accounting, no
    undone work presented as done.

**Conflicts found and resolved (PO to confirm):**
- **"Review-as-stage-gate" anti-pattern vs our showcase go-live gate.** Resolution: they target different
  things. Item-level ACCEPTANCE stays continuous during the sprint (blind tester verdicts) — exactly what
  the anti-pattern demands. The showcase gates only RELEASE AUTHORIZATION, which the regulated-industry
  sign-off literature REQUIRES as a documented approval; our PO-approval-at-showcase is the sign-off
  packet's approval record, not stakeholder theatre. Design stands.
- **Task pre-assignment anti-pattern vs our planning allocations.** Resolution: the anti-pattern is about
  human bottlenecks and self-management. We allocate ROLES/seats and write-sets at planning (needed for
  agent routing and concurrency), but story claiming stays just-in-time within the sprint. Design stands
  with that nuance recorded.
- **Proxy-PO warning vs our BA hat.** Our BA is a facilitator in the lead seat with the PO talking directly
  in-session — no relay hop exists. The warning becomes a standing rule instead: the BA hat never answers
  FOR the PO; open PO questions halt the story, never get guessed.

## 8. Consolidated source list (primary)

Scrum Guide 2020 (scrumguides.org) · Scrum.org (commitment-vs-forecast; 15 sprint review anti-patterns;
DoD; DoR; daily scrum; AI-delegation for POs) · Mountain Goat Software / Mike Cohn (DEEP backlog; story
template; planning poker; story points) · Roman Pichler (BA-in-Scrum; sprint goal template) · SVPG/Cagan
(PM vs PO) · Agile Modeling/Ambler (BA handoff critique) · Agile Alliance (SM anti-patterns; DoD glossary;
small-scale Scrum experience report) · Age-of-Product/Wolpers (backlog + sprint + review anti-patterns;
data-informed retros; 2020 guide) · Atlassian (refinement; DoR; velocity; boards; CAB) · TeamRetro /
FunRetrospectives / Retromat (standup + retro practice) · Cucumber.io (Gherkin reference) · Boost (real
DoR/DoD checklists) · BugReel / Plane.so (triage) · ISTQB (UAT; regression) · Citesvue / DebuggAI (UAT
evidence + sign-off) · Bridgeforce (agile compliance in banking) · BrowserStack (regression in agile) ·
Zeiss Digital (tester independence) · Airbrake (QA models) · cguldogan/copilot-scrum-team ·
engineeringexec.tech (AI-Scrum). Full per-claim URLs in the three research passes (ledger RUN 59, session
2026-08-20 evening).
