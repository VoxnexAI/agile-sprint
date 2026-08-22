# Sprint Office — State-to-Visual-State Matrix (NORMATIVE)

Source of truth: `.claude/skills/sprint/SKILL.md` (Laws 1–10, phase procedures). Every row maps
a REAL sprint state or event from the skill — the office invents no workflow. Poses reference
`characters.svg` symbol ids; objects reference the component libraries. "PO reads" = what the
Product Owner should understand at a glance; per Law 8 the display names carry no authority.

## A. Story workflow states (story frontmatter `status:` — the nine real states)

| State | Role involved | Pose | Location | Object / ticket | Indicator (colour + icon + treatment) | Movement? | PO reads |
|---|---|---|---|---|---|---|---|
| backlog | — (unclaimed) | — | Backlog shelf by the door | story card, dimmed, stacked | slate `#64748B`, tray icon, card at 70% opacity | no | "Raw idea; not ready to build" |
| groomed | BA | `pose-reading` at planning wall | Planning wall | story card, full opacity, AC checklist clipped to it | slate + check-list icon, crisp card | no | "Shaped and ready to pull into a sprint" |
| committed | SM | `pose-carrying` | Between planning wall and sprint board | story card in hand → To-Do column | slate, card gains sprint ribbon | walk: wall → board | "Pulled into this sprint's forecast" |
| design | TechBA | `pose-thinking` at desk | TechBA workstation | card on desk + sketch sheet | cyan `#0E7490` + pencil icon | card: board → desk | "Being designed against the live system" |
| build | Dev | `pose-typing` | Dev workstation | card docked on monitor, task cards ticking | blue `#1E40AF` + hammer icon, desk beacon blue | card: board → desk | "Being built; tasks ticking on the card" |
| test | Tester | `pose-testing` (magnifier) | Tester workstation | card + evidence folder | amber `#B45309` + magnifier icon, beacon amber | Dev walks hand-off to Tester | "Independently verified — blind, different model" |
| blocked | SM attending | `pose-blocked` (owner) + SM `pose-talking` | Blocked bay next to board | card with lock chain treatment | rose `#BE123C` + lock icon + desk alarm lamp | card: → blocked bay | "Stuck; SM clearing it or it comes to me" |
| done | Tester stamped | `pose-celebrating` (brief) | Done column | card with PASS stamp | green `#15803D` + check icon, stamp texture | Tester walks card → Done | "Tester PASS — the only door to Done" |
| shipped | PO + SM | — | Release rail by the door | card gains gold ribbon + flag | green + gold `#C9A227` ribbon + flag icon | card: Done → release rail | "Live on production under my recorded approval" |

## B. Events and conditions (events.jsonl `event:` entries + skill procedures)

| Event | Role | Pose | Location | Object | Indicator | Movement? | PO reads |
|---|---|---|---|---|---|---|---|
| story claimed (`event:"claim"`) | claiming seat | `pose-pointing` at card | Sprint board | card gains avatar chip | role-coloured chip appears on card | no | "Someone owns this now" |
| AC frozen (`event:"frozen"`) | SM | `pose-standing` at board | Sprint board | card AC gets lock clasp | lock icon on card edge | no | "Scope is frozen; changes now cost an event" |
| Dev starts work | Dev | `pose-walking` then `pose-typing` | board → Dev desk | card | blue beacon lights at desk | walk | "Build actually started" |
| Dev → Tester hand-off | Dev + Tester | `pose-handoff` (both) | midway between desks | ticket passed hand to hand | card flips to amber | walk | "Work left the builder; verification begins" |
| Tester PASS | Tester | `pose-review-result` then `pose-celebrating` | Tester desk → board | PASS stamp slams on card | green stamp + check | walk to Done column | "Independently proven; may count as done" |
| Tester FAIL | Tester | `pose-review-result` (sheet held out) | Tester desk → Dev desk | FAIL sheet + defect record | rose stamp + cross; card walks BACK | walk (reverse) | "Defects found; work bounced with evidence" |
| bug created | finder | `pose-pointing` | wherever found | new small bug card spawns | rose bug icon, typed `[bug]` card | no | "A defect became a work item — never silent" |
| easy bug — fix now w/ owner | current owner | `pose-typing` (burst) | owner's desk | bug card ticks quickly | bug card → green tick | no | "Small; fixed on the spot by whoever owns it" |
| bug needs brainstorming | agent seat | `pose-thinking` at meeting table | Meeting table | bug card on table | bug card + question icon | card → To-Do | "Needs thought before anyone codes" |
| complex / PO blocker | SM | `pose-talking` toward PO office | Blocked bay | card chained + decision tag | rose + lock + question icon | card → blocked bay | "This one waits on a decision — likely mine" |
| PO decision needed | PO | (PO desk lamp lit) | PO corner office | decision tray gains card | gold tray glow + question icon | card → PO tray | "My queue: the office is literally showing me my inbox" |
| story returned to build (FAIL event `to:"build"`) | Dev | `pose-typing` | Dev desk | card back on monitor, defect sheet clipped | blue again + bug chip retained | walk back | "Rework in progress with the evidence attached" |
| story de-scoped (`→ groomed`) | SM after PO word | `pose-carrying` (reverse) | board → planning wall | card leaves sprint, ribbon removed | slate again | walk | "Forecast adjusted — normal, not failure" |
| showcase ready (all resolved gate) | SM | `pose-presenting` at showcase screen | Showcase area | screen shows packet | screen lights; door lamp green | crew gathers | "Everything is done/tested; presentation only" |
| release approved (Approval record) | PO | (recorded words on screen) | Showcase area | Approval plaque on screen | gold seal + flag | — | "My exact words + timestamp are the trigger — nothing else is" |
| release NOT approved | SM | `pose-standing` | Showcase area | cards stay in Done (never demoted) | done stays green; no ribbon | none | "Withheld release only; done work stays done" |
| production release completed | SM | `pose-celebrating` (restrained) | Release rail | cards gain shipped ribbons; canceller lamp ON | gold ribbons + armed lamp | cards slide to rail | "Live on prod; the safety net is armed" |

## C. Motion layers (PO rule, 2026-08-21)
- **Ambient layer** (non-semantic, restrained, always allowed): breathing, occasional blinks,
  typing at the keyboard while a role is actively working, coffee steam, soft monitor shimmer,
  small posture adjustments. Ambient motion NEVER moves cards, changes indicators, or implies a
  workflow transition. No wandering.
- **Workflow layer** (semantic): every movement in tables A/B corresponds to a real
  events.jsonl line — characters physically WALK the route (walk cycle + facing changes +
  correct layering + carried shadow), tickets travel in hands or between board slots. Never
  pose-fade teleporting.
- Unstaffed role: seated at 85% opacity, ambient breathing only.
- `prefers-reduced-motion`: ambient freezes entirely; workflow renders as stepped keyframes.
- **Journey scale (PO, 2026-08-22): the desks sit close to the wall board, so a board journey
  is a SHORT beat — stand up, a step or two to the wall, pin/move the card, return — never a
  long walk. If a future layout wants real walking distance, move the desks; never fake
  distance with a slow shuffle across two tiles.**
