#!/usr/bin/env python3
"""Crew naming for Agile Sprint.

Writes a project's `sprint/crew.md`. Two ways in, both offered by the skill's
`crew` phase on first run:

  * the user names the crew themselves, or
  * the system picks names for them.

A picked name never has to be reconciled with an avatar afterwards: each name
in the pool CARRIES its avatar (hair style, hair colour, skin tone), so the
character on the board always presents the way the name reads. Nothing is
inferred from a name at render time.

The PO is never named here. The Product Owner is always the ACTIVE USER
(`git config user.name`), resolved fresh on every run, so a crew file can
never pin one person as the owner of someone else's project.

Run:
  python sprint_crew.py --root sprint --random
  python sprint_crew.py --root sprint --names "SM=Alex,BA=Sam,TechBA=Robin,Dev=Kim,Tester=Jo"
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

# Avatar vocabulary the renderer actually supports. Anything outside these
# lists would render a broken character, so the pool is constrained to them.
HAIR_STYLES = ("bob", "bun", "crop", "curls", "short", "swept")
SKIN_TONES = ("s1", "s2", "s3", "s4")
HAIR_COLOURS = {
    "black": "#332F36",
    "brown": "#5D4632",
    "light-brown": "#8C6D4F",
    "grey": "#CDCAC2",
    "auburn": "#A8552F",
}

# (name, presentation, hair style, skin tone, hair colour)
# `presentation` only decides which pool a random pick draws from; it is
# metadata about the CHARACTER, never about any real person, and the avatar
# always ships with the name so the two can never disagree.
NAME_POOL = [
    # feminine-presenting
    ("Maya",   "fem", "bob",   "s1", "black"),
    ("Priya",  "fem", "bun",   "s2", "black"),
    ("Elena",  "fem", "short", "s1", "brown"),
    ("Amara",  "fem", "curls", "s4", "black"),
    ("Sofia",  "fem", "bob",   "s2", "brown"),
    ("Yuki",   "fem", "short", "s1", "black"),
    ("Nadia",  "fem", "bun",   "s3", "black"),
    ("Leila",  "fem", "curls", "s3", "auburn"),
    ("Ingrid", "fem", "bob",   "s1", "grey"),
    # masculine-presenting
    ("Oliver", "masc", "crop",  "s3", "black"),
    ("Marcus", "masc", "curls", "s4", "black"),
    ("Diego",  "masc", "crop",  "s3", "brown"),
    ("Kenji",  "masc", "short", "s1", "black"),
    ("Omar",   "masc", "crop",  "s3", "black"),
    ("Tomas",  "masc", "swept", "s2", "brown"),
    ("Ravi",   "masc", "crop",  "s3", "black"),
    ("Ethan",  "masc", "swept", "s1", "light-brown"),
    ("Anders", "masc", "short", "s1", "grey"),
    # neutral-presenting
    ("Alex",   "neutral", "short", "s2", "brown"),
    ("Sam",    "neutral", "crop",  "s1", "light-brown"),
    ("Robin",  "neutral", "bob",   "s2", "auburn"),
    ("Jordan", "neutral", "short", "s4", "black"),
    ("Casey",  "neutral", "curls", "s2", "light-brown"),
    ("Riley",  "neutral", "swept", "s3", "brown"),
]

# The five named seats. The PO is deliberately absent: it is always the user.
CREW_ROLES = ["SM", "BA", "TechBA", "Dev", "Tester"]

SEATS = {
    "SM": "lead session hat",
    "BA": "lead session hat",
    "TechBA": "subagent",
    "Dev": "subagent",
    "Tester": "subagent, BLIND",
}
MODEL_POLICY = {
    "SM": "frontier",
    "BA": "frontier",
    "TechBA": "frontier",
    "Dev": "opus/sonnet by story size",
    "Tester": "always != Dev model; Sonnet minimum; frontier on high-risk",
}

DEFAULT_AVATAR = ("short", "s2", "brown")


def pick_crew(presentation: str = "any", seed: int | None = None) -> dict:
    """One distinct name+avatar per named role, drawn from the pool."""
    pool = [e for e in NAME_POOL
            if presentation in ("any", "mixed") or e[1] == presentation]
    if len(pool) < len(CREW_ROLES):
        pool = list(NAME_POOL)
    rng = random.Random(seed)
    chosen = rng.sample(pool, len(CREW_ROLES))
    return {role: entry for role, entry in zip(CREW_ROLES, chosen)}


def avatar_cell(hair: str, skin: str, colour: str) -> str:
    if hair not in HAIR_STYLES:
        hair = DEFAULT_AVATAR[0]
    if skin not in SKIN_TONES:
        skin = DEFAULT_AVATAR[1]
    hexc = HAIR_COLOURS.get(colour, colour if str(colour).startswith("#")
                            else HAIR_COLOURS[DEFAULT_AVATAR[2]])
    return f"{hair}:{skin}:{hexc}"


def render_crew_md(rows: dict) -> str:
    """rows: {role: (name, hair, skin, colour)} for the five named roles."""
    out = [
        "# Sprint Crew",
        "",
        "Names and avatars for this project's crew, shared by everyone working on it.",
        "",
        "**The Product Owner is always the active user** — resolved from `git config user.name`",
        "at render time and never stored here, so this file can never pin one person as the",
        "owner of the work. Approval authority is separate again: it belongs to the delivery's",
        "owner, named on the `owner:` line of that delivery's backlog.",
        "",
        "Personal renames NEVER edit this file — run the skill's `crew` phase and your names are",
        "written to `sprint/crew.local.md` (gitignored, per-user): you see your names, teammates",
        "keep theirs.",
        "",
        "The Avatar column is `hair:skin:hair-colour` and drives the character on the board and",
        f"in the Sprint Office. Hair: {', '.join(HAIR_STYLES)}. Skin: {', '.join(SKIN_TONES)}.",
        "",
        "## Crew",
        "| Role | Name | Seat | Model policy | Avatar |",
        "|------|------|------|--------------|--------|",
        "| PO | (active user) | human | — | swept:s2:#5D4632 |",
    ]
    for role in CREW_ROLES:
        name, hair, skin, colour = rows[role]
        out.append(f"| {role} | {name} | {SEATS[role]} | {MODEL_POLICY[role]} | "
                   f"{avatar_cell(hair, skin, colour)} |")
    out.append("")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Write a project's sprint/crew.md")
    ap.add_argument("--root", default="sprint",
                    help="the project's sprint state directory (default: sprint)")
    ap.add_argument("--random", action="store_true",
                    help="let the system pick names (each carries a matching avatar)")
    ap.add_argument("--presentation", default="any",
                    choices=["any", "fem", "masc", "neutral"],
                    help="restrict a random pick to one presentation (default: any)")
    ap.add_argument("--seed", type=int, default=None, help="reproducible random pick")
    ap.add_argument("--names", default=None,
                    help="explicit names, e.g. \"SM=Alex,BA=Sam,TechBA=Robin,Dev=Kim,Tester=Jo\"")
    ap.add_argument("--local", action="store_true",
                    help="write crew.local.md (per-user override) instead of crew.md")
    ap.add_argument("--print", dest="to_stdout", action="store_true",
                    help="print the file instead of writing it")
    args = ap.parse_args(argv)

    if not args.random and not args.names:
        ap.error("choose one: --random (system picks) or --names (you pick)")

    by_name = {e[0].lower(): e for e in NAME_POOL}
    rows: dict = {}

    if args.random:
        for role, (name, _pres, hair, skin, colour) in pick_crew(
                args.presentation, args.seed).items():
            rows[role] = (name, hair, skin, colour)

    if args.names:
        for pair in args.names.split(","):
            if "=" not in pair:
                ap.error(f"bad --names entry {pair!r} (expected Role=Name)")
            role, _, name = pair.partition("=")
            role, name = role.strip(), name.strip()
            if role == "PO":
                ap.error("the PO is always the active user and is never named here")
            if role not in CREW_ROLES:
                ap.error(f"unknown role {role!r} (expected one of {CREW_ROLES})")
            # a user-supplied name that happens to be in the pool keeps that
            # entry's avatar; anything else gets the neutral default
            known = by_name.get(name.lower())
            rows[role] = ((name,) + (known[2:] if known else DEFAULT_AVATAR))

    missing = [r for r in CREW_ROLES if r not in rows]
    if missing:
        filler = pick_crew(args.presentation, args.seed)
        used = {v[0].lower() for v in rows.values()}
        for role in missing:
            name, _pres, hair, skin, colour = filler[role]
            if name.lower() in used:               # never duplicate a name
                for entry in NAME_POOL:
                    if entry[0].lower() not in used:
                        name, _pres, hair, skin, colour = entry
                        break
            used.add(name.lower())
            rows[role] = (name, hair, skin, colour)

    text = render_crew_md(rows)
    if args.to_stdout:
        print(text)
        return 0

    out = Path(args.root) / ("crew.local.md" if args.local else "crew.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8", newline="\n")
    print(f"crew written to {out}: "
          + ", ".join(f"{r}={rows[r][0]}" for r in CREW_ROLES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
