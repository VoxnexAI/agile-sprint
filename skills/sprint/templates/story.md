---
id: ST-000
title: (short noun phrase)
type: story
points: 0
risk: normal
repo: synora
status: backlog
claimed_by: none
sprint: none
---

<!-- type: story|bug · risk: normal|high (high = prod money paths, customer comms, migration queue)
     repo: synora|appstoneink|both · status: backlog|groomed|committed|design|build|test|done|shipped
     points: modified Fibonacci 0,1,2,3,5,8,13,20 (larger = split the story)
     Optional extra key `epic: <backlog epic line's short name>` links a story to its parent
     theme/epic (BA chunks themes → epics → stories at grooming); ignored by the v1 renderer. -->

## Story
<!-- One sentence, Connextra form. Keep AC OUT of this line. -->
As a <role>, I want <capability>, so that <benefit>.

## Business case
<!-- BA: why this matters, in the PO's language. Just barely good enough. -->

## Acceptance criteria
<!-- FROZEN at planning; edits after pull-in are scope changes logged as events, never silent edits.
     Style rule (practitioner ref §3): behavior/workflow → Gherkin (Given/When/Then);
     flat validation/permission/quality rules → checklist. Only conditions whose failure
     means the PO rejects the item. The Tester verifies against THIS section alone. -->

## Regression notes
<!-- Sketched WITH the AC at grooming, not invented at sprint end: which read-only checks
     prove nothing else broke. -->

## Tech design
<!-- TechBA: conversational design against the live system — follow-ups expected, never a
     spec dump. May REJECT the story as unbuildable/conflicting; rejection goes back to grooming.
     Derive the ## Tasks checklist below from this design. -->

## Tasks
<!-- The granular work items INSIDE this story — the board card's expand view live-shows these
     with their tick state (PO model, 2026-08-21: the card is the product; tasks live inside it).
     One `- [ ]` line per item, typed with a leading tag:
       - [ ] [build] <what the Dev builds>
       - [ ] [test]  <what the blind Tester verifies>   (testing gets its OWN items)
       - [ ] [bug]   <defect found — a NEW item is ALWAYS created for a bug, then routed by
                      tier: easy=fix now with owner · brainstorm=To-Do · complex/PO=blocked>
     Tick items AS THEY LAND (the board republishes on every transition); an unticked done
     task means the board lies. Untyped lines render untagged — fine for scaffolding notes. -->

## Definition of Ready check
<!-- ALL boxes ticked before the story may enter a sprint. -->
- [ ] INVEST-graded (independent, negotiable, valuable, estimable, small, testable)
- [ ] Acceptance criteria written in the right style
- [ ] Points set via independent estimation (BA/TechBA/Dev, divergence >1 step reconciled)
- [ ] Risk tier tagged
- [ ] Repo tagged (drift scan implications known if `both`)
- [ ] Regression notes sketched with the AC (read-only checks named)

## History
<!-- Append-only: ISO date · actor · what changed. -->
