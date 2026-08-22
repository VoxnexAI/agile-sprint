# Working with the Sprint system — staff guide

This is how change gets delivered in this business now. Feed this guide to your Claude session —
your session picks the skill up when you use `/sprint` or ask for sprint work — and it will know
how to work. This page tells YOU what the system is, the background if you've never worked this
way, what you can do in it, and the rules that keep production safe.

## Background: why we work in sprints (no jargon required)

The old way to build software is to plan everything up front, build for weeks, and release one
big change at the end. It fails predictably: by release day the plan has drifted, nobody can say
exactly what changed, and one bad piece blocks everything behind it. We proved this to ourselves
in August 2026 — days of building piled up 23 database changes waiting to release, and an audit
found one of them would have broken the release for everything behind it.

**Agile** is the industry's answer, and ours: work in small, short cycles called **sprints**.
Each sprint delivers a small set of finished, tested improvements that could go live on their
own. Then we stop, show the work, decide about releasing it, learn something, and start the next
small cycle. Benefits, plainly:

- **Small changes = small risk.** If something's wrong, it's one small thing, found early.
- **Something useful ships regularly**, instead of everything arriving late together.
- **Testing happens during the work, not after it** — failing early is cheap; failing at
  release day is expensive.
- **The business stays in control:** nothing reaches customers without a named person
  (the Product Owner) looking at evidence and saying yes.

## The dictionary — every term you'll hear, in plain English

| Term | Means |
|---|---|
| **Delivery** | One project/initiative. Each has its own separate backlog, sprints, and board — projects never mix. |
| **Backlog** | The delivery's to-do list, in priority order. Detailed at the top, rough at the bottom. |
| **User story** | One small piece of work written from the user's point of view: *"As a collections agent, I want X, so that Y."* Small enough to build and test in one go. |
| **Epic** | A big idea that's too large to build in one piece — it gets chunked into stories. |
| **Grooming** | The working session where rough backlog items become proper stories: what exactly, how do we know it's done, how big is it. |
| **Acceptance criteria** | The checklist that defines "done" for a story — written before building starts and frozen, so the test is against what was agreed, not what got built. |
| **Sprint** | One short cycle: a forecast set of stories → built → tested → shown. Here a sprint is sized by scope, not weeks — the AI crew can finish one in hours. |
| **Sprint board** | The live web page showing every story as a card moving across columns: To-Do → Design → Build → Test → Blocked → Done (the product backlog sits in a collapsible drawer below). Each card has an expandable **Tasks** view showing the granular build/test/bug items inside it, ticked live as they land. |
| **Blocked** | A board column for work parked on something the team can't clear alone — usually a decision only the Product Owner can make. The Scrum Master tries to clear it first; if it can't be cleared this sprint, the item goes back to the backlog. |
| **Showcase** | End-of-sprint meeting: the evidence of what was built and tested is presented, and the Product Owner decides whether it goes live. |
| **Retrospective (retro)** | The five-minute honesty session after each sprint: what worked, what didn't, and one to three concrete things to do better. |
| **Velocity / burndown** | Simple measures of how much the crew finishes per sprint and how a sprint is tracking. Used for planning only — never as a performance score. |
| **Bug** | A defect found at any point. A NEW work item is always created for it, then routed by tier: **easy** → fixed immediately by whoever owns the work; **needs thinking** → goes to To-Do for an agent to work through; **complex or needs the Product Owner** → the work moves to the Blocked column until cleared or sent back to the backlog. Never fixed silently. |

## The crew: who does what

The work is done by a team of AI agents with fixed, separated roles — separated on purpose, so
no one checks their own homework:

| Role | Who | What they do |
|---|---|---|
| **Product Owner (PO)** | A human — the **delivery's owner**, named on the `owner:` line of that delivery's backlog | Owns priorities, answers the crew's questions, and is the ONLY one who can approve a release to production. Your board displays *your* name on the PO chip, but approval authority never moves — it always belongs to the delivery's owner |
| **Scrum Master + Business Analyst** — default names **Maya** & **Oliver** | Your Claude session (the one you talk to) | Runs the process, interviews the PO, writes the stories, routes the work — never builds anything, never marks anything done |
| **Technical BA** — default **Priya** | AI agent | Turns a story into a technical design against the real system; can reject a story as unbuildable |
| **Developer** — default **Marcus** | AI agent | Builds the story — always "dark": nothing switches on for customers from a build alone |
| **Tester** — default **Elena** | AI agent, always independent | Tests blind against the frozen acceptance criteria, on a different AI model than the developer. The Tester's PASS is the only thing that makes a story "done" |

Don't like the names? Run `/sprint crew` — your renames apply to **your sessions only**
(saved in a personal file that's never shared); teammates keep their own names.

## Commands your Claude session understands

```
/sprint                          → lists the deliveries and asks which one
/sprint <delivery> status        → the board + a one-paragraph summary
/sprint <delivery> groom         → refine backlog items into stories (interviews the PO)
/sprint <delivery> plan          → pull a story set and start a sprint
/sprint <delivery> run           → the build/test loop on the committed stories
/sprint <delivery> showcase      → evidence packet + the PO's go-live decision
/sprint <delivery> retro         → what went well/didn't, actions, velocity
/sprint <delivery> archive       → retire a finished delivery (PO-only)
/sprint crew                     → rename the AI crew (applies to you only)
```

Example: `/agile-sprint:sprint <delivery> status`.

## What YOU can do

- **Check progress any time:** `/sprint <delivery> status`, or open the delivery's board page
  (ask your session for the link).
- **Add an idea or request:** tell your session to add it to the delivery's backlog — it lands as
  a rough one-liner for the PO to prioritise. Don't write detailed requirements yourself;
  grooming does that properly with the PO.
- **Report a problem:** describe it to your session — it becomes a bug on the backlog with a
  proper evidence record, and gets triaged into a sprint.
- **Work stories (advanced):** a session may only advance stories it has claimed, and two
  sessions never touch the same files at once. Your Claude handles this automatically — just
  never hand-edit the files under `sprint/` while a sprint is running.

## The rules that protect production (non-negotiable)

1. **Nothing goes to production without the PO's recorded approval at a showcase.** No
   exceptions, no matter who asks. If your session ever proposes a production release outside a
   showcase, stop it and tell Ash.
2. **The test environment is not a sandbox** — it is connected to real customer email/SMS
   pipelines. Checks there are read-only; nothing gets switched on casually.
3. **Nobody marks their own work done** — human or AI. Only the independent Tester's PASS
   completes a story.
4. **If the PO hasn't answered a question a story depends on, the story waits.** Nobody guesses
   on the PO's behalf.

## Where things live (for the curious)

- The skill your session follows: `.claude/skills/sprint/SKILL.md`
- Deliveries and their backlogs: `sprint/deliveries/<name>/`
- The design and the researched practices behind it:
  `docs/superpowers/specs/2026-08-20-sprint-skill-design.md` and
  `docs/superpowers/research/2026-08-20-agile-practitioner-reference.md`

## First-time setup

You need this repo cloned and opened in Claude Code. On a fresh clone run `npm install` first,
and see the "Branch-based .env switching" section of `CLAUDE.md` — you'll need the environment
snapshots from a teammate. Stay on the `test-env` branch unless told otherwise.

Questions about the process → ask your Claude session first (it holds the full design), then Ash.
