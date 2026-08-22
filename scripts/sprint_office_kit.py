#!/usr/bin/env python3
"""Sprint Office asset-kit generator v2 (stdlib only).

v2 per PO refinement (2026-08-21): WARM architectural palette (light-first),
true 3/4-isometric jointed character rig with front AND rear bases (4 facings
via mirroring), faces with restrained expressions, soft blurred shadows, and
an emitted MOTION PROTOTYPE page (real walk cycle, sit<->stand joint tweens,
board interaction, ambient-vs-workflow layers, replay control).

Rules: .claude/skills/sprint/assets/office/STYLE.md (NORMATIVE).
Never hand-edit emitted files; change this generator and re-run.

Run:  python scripts/sprint_office_kit.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sprint_board import COLUMNS as BOARD_COLUMNS, esc, md_to_html

# The kit's SOURCE assets live beside this script inside the plugin. Rendered
# per-delivery offices are project output and go wherever --out says, so a
# plugin install is never written into by day-to-day use.
OUT = Path(__file__).resolve().parent.parent / "skills" / "sprint" / "assets" / "office"
U = 32


# ---------------------------------------------------------------- helpers --
def shade(hex_color: str, factor: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    if factor >= 0:
        r, g, b = (round(c + (255 - c) * factor) for c in (r, g, b))
    else:
        r, g, b = (round(c * (1 + factor)) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def iso(x, y, z=0.0):
    return ((x - y) * U, (x + y) * U / 2 - z)


def pts(seq):
    return " ".join(f"{px:.1f},{py:.1f}" for px, py in seq)


CSS_VARS: dict = {}


def var(name, light, dark):
    CSS_VARS[name] = (light, dark)
    return f"var(--{name})"


def face_vars(name, light_base, dark_base):
    return (
        var(f"{name}-t", shade(light_base, 0.08), shade(dark_base, 0.08)),
        var(f"{name}-l", light_base, dark_base),
        var(f"{name}-r", shade(light_base, -0.14), shade(dark_base, -0.14)),
    )


def iso_box(x, y, w, d, h, fills, z=0.0, cls=""):
    """Three-face iso solid; same-colour round-join strokes soften corners."""
    ft, fl, fr = fills
    top = [iso(x, y, z + h), iso(x + w, y, z + h), iso(x + w, y + d, z + h), iso(x, y + d, z + h)]
    left = [iso(x, y + d, z + h), iso(x + w, y + d, z + h), iso(x + w, y + d, z), iso(x, y + d, z)]
    right = [iso(x + w, y, z + h), iso(x + w, y + d, z + h), iso(x + w, y + d, z), iso(x + w, y, z)]
    c = f' class="{cls}"' if cls else ""

    def poly(p, f):
        return (f'<polygon points="{pts(p)}" fill="{f}" stroke="{f}" '
                f'stroke-width="2" stroke-linejoin="round"/>')
    return f"<g{c}>{poly(top, ft)}{poly(left, fl)}{poly(right, fr)}</g>"


def shadow(x, y, w, d):
    cx, cy = iso(x + w / 2, y + d / 2, 0)
    rx = (w + d) * U * 0.42
    return (f'<ellipse class="shadow" filter="url(#softblur)" cx="{cx + 6:.1f}" '
            f'cy="{cy + 3:.1f}" rx="{rx:.1f}" ry="{rx / 2:.1f}"/>')


def flat_shadow(cx, cy, rx):
    return (f'<ellipse class="shadow" filter="url(#softblur)" cx="{cx + 4:.1f}" '
            f'cy="{cy + 2:.1f}" rx="{rx:.1f}" ry="{rx * 0.38:.1f}"/>')


SYM_VB: dict = {}


def iuse(sid, transform="", cls=""):
    vx, vy, vw, vh = SYM_VB[sid]
    t = f' transform="{transform}"' if transform else ""
    c = f' class="{cls}"' if cls else ""
    return (f'<g{c}{t}><use href="#{sid}" x="{vx:g}" y="{vy:g}" '
            f'width="{vw:g}" height="{vh:g}"/></g>')


# ------------------------------------------------------- WARM palette (v2) --
INK = var("ink", "#322D24", "#F0EAE0")
DIM = var("dim", "#7C7365", "#A89D8C")
BG = var("bg", "#F7F4ED", "#211E19")
PANEL = var("panel", "#FFFDF8", "#2A2620")
PANEL_BORDER = var("panel-border", "#E8E0D0", "#3D372E")

FLOOR_A = face_vars("floor-a", "#EFE8D9", "#2B2721")
FLOOR_B = face_vars("floor-b", "#E7DFCC", "#262219")
WALL = face_vars("wall", "#F7F2E7", "#3B352B")
WALL_S = face_vars("wall-s", "#EDE5D5", "#332E25")
DESK = face_vars("desk", "#E7DFCE", "#3A352C")
DESK_LEG = face_vars("desk-leg", "#C9BEA6", "#4A4438")
WOOD = face_vars("wood", "#D9BB8E", "#6B5A42")
SEAT = face_vars("seat", "#93A6C5", "#4E5A70")
DEVICE = face_vars("device", "#4A453D", "#171512")
SCREEN = var("screen", "#ECF0EF", "#2E3833")
SCREEN_UI = var("screen-ui", "#A9BCB6", "#5F7570")
PAPER = var("paper2", "#FBF8F1", "#DDD6C8")
CARD_EDGE = var("card-edge", "#D6CBB6", "#4A4438")
BOARD_BG = var("board-bg", "#F4EFE3", "#302B23")
GOLD = "#C9A227"
TERRA = var("terra", "#A96B58", "#A87763")   # decorative warmth ONLY (rule 3b)
INK_FIX = "#2E2A25"
SKEW = "skewY(26.565)"

ROLE = {
    "po": ("#3A4A66", "#7286A8"), "sm": ("#A96B58", "#C08B77"),
    "ba": ("#3E8E85", "#63B0A7"), "techba": ("#7D5F9E", "#9D82BC"),
    "dev": ("#5C77AE", "#89A2D6"), "tester": ("#6B8A70", "#93B098"),
}
STATUS = {
    # backlog is a LIGHTER slate than to-do: same family (not started), but the
    # two columns must never render as one strip on the wall board
    "backlog": "#94A3B8",
    "todo": "#64748B", "design": "#0E7490", "build": "#1E40AF",
    "test": "#B45309", "blocked": "#BE123C", "done": "#15803D",
    "warn": "#D97706", "danger": "#DC2626",
}
SKIN = {"s1": "#F6D6B2", "s2": "#E5B08A", "s3": "#B77F55", "s4": "#7E5638"}
HAIR = {"h1": "#332F36", "h2": "#5D4632", "h3": "#8C6D4F", "h4": "#CDCAC2", "h5": "#A8552F"}
SHOE = "#3B352C"


# ------------------------------------------------------------ RIG v2 data --
# Jointed 3/4 rig. Origin = feet-centre on the ground. Screen y grows down.
# near = screen-left side. Facings: F (front-3/4, faces SW) and R (rear-3/4,
# faces NE); mirroring (scale -1,1) yields SE and NW.
# Each pose: joints for near/far arm (sh, el, wr), near/far leg (hip, kne,
# ank), head offset, torso lean deg, bob (y shift), plus default mood/prop.

def P(nsh, nel, nwr, fsh, fel, fwr, nhip, nkne, nank, fhip, fkne, fank,
      head=(-2, -92), lean=0.0, bob=0.0, mood="neutral", prop=None,
      shoulders=None, hips_y=-45):
    return {"nsh": nsh, "nel": nel, "nwr": nwr, "fsh": fsh, "fel": fel,
            "fwr": fwr, "nhip": nhip, "nkne": nkne, "nank": nank,
            "fhip": fhip, "fkne": fkne, "fank": fank, "head": head,
            "lean": lean, "bob": bob, "mood": mood, "prop": prop,
            "sh_y": shoulders if shoulders is not None else -75,
            "hips_y": hips_y}


RIG = {
    "stand": P((-12, -75), (-14.5, -61), (-13.5, -49), (11, -74), (13.5, -61), (12.5, -50),
               (-5, -45), (-6.5, -25), (-7.5, -6), (5.5, -44), (6.5, -25), (6, -7)),
    "walkA": P((-12, -75), (-8, -61), (-3.5, -50), (11, -74), (17, -63), (21, -53),
               (-5, -45), (-13, -27), (-18, -7), (5.5, -44), (10, -25), (15, -9),
               lean=3, bob=-1.5),
    "walkB": P((-12, -75), (-17, -62), (-21, -52), (11, -74), (7, -61), (3, -50),
               (-5, -45), (-1, -25), (3.5, -8), (5.5, -44), (-3, -26), (-8, -8),
               lean=3, bob=-1.5),
    "sitmid": P((-12, -66), (-15, -54), (-11, -44), (11, -65), (14, -54), (10, -45),
              (-5, -38), (-13, -30), (-14, -6), (5, -37), (-4, -29), (-5, -6),
              head=(-3, -84), lean=7, shoulders=-66, hips_y=-38),
    "sit": P((-12, -58), (-13, -47), (-7, -40), (11, -57), (12, -47), (6, -41),
             (-5, -30), (-16, -27), (-16.5, -5), (5, -29), (-7, -26), (-7.5, -5),
             head=(-2, -74), shoulders=-58, hips_y=-30),
    "type": P((-12, -58), (-13, -49), (-8, -52), (11, -57), (12, -49), (6.5, -52),
              (-5, -30), (-16, -27), (-16.5, -5), (5, -29), (-7, -26), (-7.5, -5),
              head=(-2, -74), shoulders=-58, hips_y=-30, mood="focus"),
    "carry": P((-12, -75), (-10, -62), (-3, -56), (11, -74), (9, -62), (2, -57),
               (-5, -45), (-11, -27), (-15, -8), (5.5, -44), (8, -25), (12, -9),
               lean=2, prop="folder"),
    "handoff": P((-12, -75), (-23, -64), (-33, -59), (11, -74), (13, -61), (12, -50),
                 (-5, -45), (-6.5, -25), (-7.5, -6), (5.5, -44), (6.5, -25), (6, -7),
                 lean=-2, prop="ticket"),
    "testing": P((-12, -75), (-16.5, -63), (-21, -73), (11, -74), (11.5, -60), (6, -55),
                 (-5, -45), (-6.5, -25), (-7.5, -6), (5.5, -44), (6.5, -25), (6, -7),
                 mood="focus", prop="mag"),
    "review": P((-12, -75), (-12.5, -59), (-6.5, -52), (11, -74), (11.5, -59), (4.5, -53),
                (-5, -45), (-6.5, -25), (-7.5, -6), (5.5, -44), (6.5, -25), (6, -7),
                lean=2, mood="focus", prop="sheet"),
    "celebrate": P((-12, -75), (-16, -89), (-14, -103), (11, -74), (13.5, -61), (12.5, -50),
                   (-5, -45), (-6.5, -25), (-7.5, -6), (5.5, -44), (6.5, -25), (6, -7),
                   lean=-2, mood="smile"),
    "blocked": P((-12, -74), (-8, -59), (5, -56), (11, -73), (7, -59), (-5, -57),
                 (-5, -45), (-6.5, -25), (-7.5, -6), (5.5, -44), (6.5, -25), (6, -7),
                 lean=1, mood="concern"),
    "point": P((-12, -75), (-23, -70), (-34, -70), (11, -74), (13.5, -61), (12.5, -50),
               (-5, -45), (-6.5, -25), (-7.5, -6), (5.5, -44), (6.5, -25), (6, -7),
               lean=-2),
    "present": P((-12, -75), (-21, -76), (-31, -84), (11, -74), (13.5, -61), (12.5, -50),
                 (-5, -45), (-6.5, -25), (-7.5, -6), (5.5, -44), (6.5, -25), (6, -7),
                 lean=-2),
    "think": P((-12, -75), (-14.5, -65), (-6.5, -83), (11, -74), (13.5, -61), (12.5, -50),
               (-5, -45), (-6.5, -25), (-7.5, -6), (5.5, -44), (6.5, -25), (6, -7),
               mood="focus"),
    "read": P((-12, -75), (-13.5, -61), (-7.5, -70), (11, -74), (12.5, -61), (2.5, -68),
              (-5, -45), (-6.5, -25), (-7.5, -6), (5.5, -44), (6.5, -25), (6, -7),
              lean=3, mood="focus", prop="sheet_hi"),
    "talk": P((-12, -75), (-18.5, -67), (-26.5, -73), (11, -74), (13.5, -61), (12.5, -50),
              (-5, -45), (-6.5, -25), (-7.5, -6), (5.5, -44), (6.5, -25), (6, -7),
              lean=-1),
    "alarmed": P((-12, -75), (-17.5, -87), (-19.5, -101), (11, -74), (16.5, -86), (18.5, -100),
                 (-5, -45), (-6.5, -25), (-7.5, -6), (5.5, -44), (6.5, -25), (6, -7),
                 mood="concern"),
}
R_POSES = {"stand", "walkA", "walkB", "sit", "sitmid", "type", "carry"}

MOODS = {
    "neutral": {"browN": "M -7 -5 Q -4.8 -6.4 -2.8 -5.4", "browF": "M 1.5 -5.6 Q 3.7 -6.8 5.6 -5.7",
                "mouth": "M -3.5 6.4 L 0.2 6.4"},
    "smile": {"browN": "M -7 -5.8 Q -4.8 -7.2 -2.8 -6.2", "browF": "M 1.5 -6.3 Q 3.7 -7.5 5.6 -6.4",
              "mouth": "M -4 5.6 Q -1.6 8 0.8 5.8"},
    "focus": {"browN": "M -7.2 -4.6 Q -4.8 -5.2 -2.6 -4.4", "browF": "M 1.3 -4.6 Q 3.6 -5.4 5.7 -4.8",
              "mouth": "M -3 6.6 L -0.2 6.6"},
    "concern": {"browN": "M -7 -4.4 Q -4.6 -6.6 -2.6 -5.8", "browF": "M 1.5 -5.7 Q 3.9 -6.8 5.8 -4.6",
                "mouth": "M -3.6 7 Q -1.6 5.6 0.4 6.8"},
}

HAIR_F = {
    "crop": 'M -12.8 -3 Q -13.4 -15.6 0 -15.6 Q 13.4 -15.6 12.8 -3 L 10.6 -2.5 Q 9 -11.6 0 -11.6 Q -9 -11.6 -10.6 -2.5 Z',
    "bob": 'M -13.6 9 Q -15.4 -15 0 -15 Q 15.4 -15 13.6 9 L 9.8 9 Q 11.8 -8.4 0 -9.2 Q -11.8 -8.4 -9.8 9 Z',
    "bun": 'M -12.6 -2.5 Q -12.9 -14.6 0 -14.6 Q 12.9 -14.6 12.6 -2.5 L 10.4 -1 Q 7.4 -9.8 0 -9.8 Q -7.4 -9.8 -10.4 -1 Z',
    "curls": 'M -12 -2 Q -13.4 -14 0 -14 Q 13.4 -14 12 -2 Q 7.8 -9.2 0 -9.2 Q -7.8 -9.2 -12 -2 Z',
    "swept": 'M -12.6 -3.5 Q -13.8 -15.4 1.6 -15.2 Q 13.6 -14.6 12.6 -5.5 L 11.4 -3 Q 8.6 -11.6 -2 -11 Q -8.8 -10.4 -10.4 -2.5 Z',
    "short": 'M -12 -4.5 Q -11.6 -14.8 0 -15 Q 11.6 -14.8 12 -4.5 L 9.8 -3.5 Q 6.4 -11.2 0 -11.4 Q -6.4 -11.2 -9.8 -3.5 Z',
}
HAIR_F_EXTRA = {
    "bun": '<circle cx="6.8" cy="-13.6" r="4.8" fill="var(--hair)"/>',
    "curls": ('<circle cx="-10.4" cy="-9.4" r="4" fill="var(--hair)"/>'
              '<circle cx="10.4" cy="-9.4" r="4" fill="var(--hair)"/>'
              '<circle cx="-5.4" cy="-14" r="3.9" fill="var(--hair)"/>'
              '<circle cx="5.4" cy="-14" r="3.9" fill="var(--hair)"/>'
              '<circle cx="0" cy="-15" r="4.1" fill="var(--hair)"/>'),
}
HAIR_B = {
    "crop": 'M -12.8 4 Q -14 -15.6 0 -15.6 Q 14 -15.6 12.8 4 Q 7 11.5 0 11.5 Q -7 11.5 -12.8 4 Z',
    "bob": 'M -14 12 Q -16 -15.2 0 -15.2 Q 16 -15.2 14 12 Q 7 15.5 0 15.5 Q -7 15.5 -14 12 Z',
    "bun": 'M -12.6 3.5 Q -13.4 -14.8 0 -14.8 Q 13.4 -14.8 12.6 3.5 Q 6.4 10.5 0 10.5 Q -6.4 10.5 -12.6 3.5 Z',
    "curls": 'M -11.6 2 Q -13 -14 0 -14 Q 13 -14 11.6 2 Q 6 10.5 0 10.5 Q -6 10.5 -11.6 2 Z',
    "swept": 'M -12.6 3 Q -14.2 -15.4 1 -15.4 Q 13.8 -14.8 12.8 3 Q 6 10.8 -0.5 10.8 Q -7 10.8 -12.6 3 Z',
    "short": 'M -12 2.5 Q -12.4 -15 0 -15 Q 12.4 -15 12 2.5 Q 6 10 0 10 Q -6 10 -12 2.5 Z',
}
HAIR_B_EXTRA = {
    "bun": '<circle cx="6.2" cy="-14.6" r="5.2" fill="var(--hair)"/>',
    "curls": ('<circle cx="-9.8" cy="-10" r="4.2" fill="var(--hair)"/>'
              '<circle cx="9.8" cy="-10" r="4.2" fill="var(--hair)"/>'
              '<circle cx="-5" cy="-14.4" r="3.8" fill="var(--hair)"/>'
              '<circle cx="5" cy="-14.4" r="3.8" fill="var(--hair)"/>'
              '<circle cx="0" cy="-15.4" r="4.4" fill="var(--hair)"/>'),
}

PROPS = {
    "folder": f'<g class="prop" transform="translate(-2,-58)"><rect x="-11" y="-7" width="24" height="16" rx="2.5" fill="{shade(GOLD, 0.55)}" stroke="{shade(GOLD, 0.2)}" stroke-width="1"/><path d="M -11 -7 L -4 -7 L -2 -10 L 5 -10 L 6 -7 L 13 -7" stroke="{GOLD}" stroke-width="1.5" fill="none"/></g>',
    "ticket": '<g class="prop prop-ticket" transform="translate(-35,-60)"><rect x="-9" y="-6" width="19" height="13" rx="2.5" fill="var(--paper2)" stroke="var(--card-edge)"/><rect x="-9" y="-6" width="4" height="13" rx="2" fill="var(--status, #64748B)"/><path d="M -2 -2 L 7 -2 M -2 2 L 5 2" stroke="var(--dim)" stroke-width="1.2" stroke-linecap="round"/></g>',
    "sheet": '<g class="prop" transform="translate(-2,-56)"><rect x="-8" y="-10" width="17" height="22" rx="1.5" fill="var(--paper2)" stroke="var(--card-edge)"/><path d="M -4 -5 L 5 -5 M -4 -1 L 5 -1 M -4 3 L 2 3" stroke="var(--dim)" stroke-width="1.2" stroke-linecap="round"/></g>',
    "sheet_hi": '<g class="prop" transform="translate(-4,-72)"><rect x="-8" y="-10" width="17" height="22" rx="1.5" fill="var(--paper2)" stroke="var(--card-edge)"/><path d="M -4 -5 L 5 -5 M -4 -1 L 5 -1 M -4 3 L 2 3" stroke="var(--dim)" stroke-width="1.2" stroke-linecap="round"/></g>',
    "mag": f'<g class="prop" transform="translate(-21,-75)"><circle cx="0" cy="0" r="6.5" fill="none" stroke="{INK_FIX}" stroke-width="2"/><circle cx="0" cy="0" r="5" fill="#AFC4BD" opacity="0.4"/><path d="M 4.5 4.5 L 10 10" stroke="{INK_FIX}" stroke-width="2.6" stroke-linecap="round"/></g>',
}

ACC_HEAD = {  # rides INSIDE the head group, head-local coords
    "sm": {
        "f": ('<path d="M -11 -1 Q -11.5 -11.5 0.5 -11.8" stroke="#2E2A25" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
              '<rect x="-13.6" y="-3" width="5.4" height="9" rx="2.6" fill="#2E2A25"/>'),
        "r": ('<path d="M -11 -3 Q 0 -13.5 11 -3" stroke="#2E2A25" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
              '<rect x="-13.6" y="-3.5" width="5" height="8.6" rx="2.5" fill="#2E2A25"/>'
              '<rect x="8.8" y="-3.5" width="5" height="8.6" rx="2.5" fill="#2E2A25"/>'),
    },
    "techba": {
        "f": ('<g stroke="#2E2A25" stroke-width="1.5" fill="none">'
              '<circle cx="-6.6" cy="-1" r="4.3"/><circle cx="1.8" cy="-1.4" r="3.9"/>'
              '<path d="M -2.4 -1.2 L -2.2 -1.2"/><path d="M 5.6 -1.6 L 9.8 0.4"/></g>'),
        "r": "",
    },
}

ACCESSORIES = {
    "po": f'<path d="M -6 -71 L -2.5 -58 M 6 -70 L 2.5 -58" stroke="{GOLD}" stroke-width="1.5"/><rect x="-3" y="-58" width="6" height="7" rx="1.2" fill="{GOLD}"/>',
    "sm": "",
    "ba": '<circle cx="-1" cy="-70" r="3" fill="var(--garment-2)"/><path d="M -2 -69 L -5 -58 M 0 -69 L 2.5 -60" stroke="var(--garment-2)" stroke-width="2.8" stroke-linecap="round"/>',
    "techba": "",
    "dev": "",
    "tester": '<path d="M -12.5 -72 L -8 -70 L -8 -46 L -11 -45 Z" fill="var(--garment-2)"/><path d="M 11.5 -71 L 7.5 -69.5 L 7.5 -46 L 10 -45 Z" fill="var(--garment-2)"/>',
}
GARMENT_OVERLAY = {
    "po": (f'<path d="M -13 -74 L -5 -72 L -8 -55 L -12 -58 Z" fill="var(--garment-2)"/>'
           f'<path d="M 12 -73 L 5 -71 L 8 -55 L 11 -57 Z" fill="var(--garment-2)"/>'),
    "dev": ('<path d="M -13 -74 Q 0 -81 12 -73 Q 6 -69 0 -69 Q -7 -69 -13 -74 Z" fill="var(--garment-2)"/>'
            '<path d="M -8 -76 Q 0 -85 8 -75 Q 4 -79 0 -79 Q -4 -79 -8 -76 Z" fill="var(--garment-2)"/>'),
    "sm": '<path d="M -1 -72 L -1 -46" stroke="var(--garment-2)" stroke-width="2" stroke-linecap="round"/>',
    "ba": "", "techba": '<path d="M -1 -72 L -1 -46" stroke="var(--garment-2)" stroke-width="2" stroke-linecap="round"/>',
    "tester": "",
}


def _limb(a, b, c, width, color, hand=None, hand_r=3.6):
    d = f"M {a[0]} {a[1]} L {b[0]} {b[1]} L {c[0]} {c[1]}"
    out = (f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="none" '
           f'stroke-linecap="round" stroke-linejoin="round"/>')
    if hand:
        out += f'<circle cx="{c[0]}" cy="{c[1]}" r="{hand_r}" fill="{hand}"/>'
    return out


def _foot_f(ank, far=False):
    ln = 9 if far else 13
    return (f'<path d="M {ank[0] + 2} {ank[1] - 3} L {ank[0] + 3} {ank[1] + 4} '
            f'Q {ank[0] + 2} {ank[1] + 6} {ank[0] - 1} {ank[1] + 6} '
            f'L {ank[0] - ln} {ank[1] + 5} Q {ank[0] - ln - 2} {ank[1] + 4} '
            f'{ank[0] - ln} {ank[1] + 2} L {ank[0] - 2} {ank[1] - 1} Z" fill="{SHOE}"/>')


def _foot_r(ank, far=False):
    ln = 7 if far else 9
    return (f'<path d="M {ank[0] - 3} {ank[1] + 4} L {ank[0] + 3} {ank[1] + 4} '
            f'L {ank[0] + ln} {ank[1]} Q {ank[0] + ln + 1} {ank[1] - 2} {ank[0] + ln - 2} {ank[1] - 3} '
            f'L {ank[0] - 2} {ank[1] - 1} Z" fill="{shade(SHOE, -0.12)}"/>')


def _torso(j, rear=False):
    sy = j["sh_y"]
    hy = j["hips_y"]
    body = (f'<path class="part-torso" d="M -14 {sy + 1} C -7 {sy - 5} 8 {sy - 5} 13 {sy + 2} '
            f'L 10 {hy - 1} C 4 {hy + 3} -6 {hy + 3} -10 {hy - 1} Z" fill="var(--garment)"/>')
    shade_side = (f'<path d="M 3 {sy - 3} C 8 {sy - 4} 11 {sy - 1} 13 {sy + 2} L 10 {hy - 1} '
                  f'C 8 {hy + 1} 5 {hy + 2} 3 {hy + 2} Z" fill="var(--garment-2)" opacity="0.9"/>')
    hips = (f'<path d="M -10 {hy - 2} L 9 {hy - 2} L 8 {hy + 6} Q 0 {hy + 9} -8 {hy + 6} Z" '
            f'fill="var(--trouser)"/>')
    if rear:
        seam = (f'<path d="M -0.5 {sy - 2} L -0.5 {hy + 1}" stroke="var(--garment-2)" '
                f'stroke-width="1.6" stroke-linecap="round"/>'
                f'<path d="M -13 {sy + 1} Q 0 {sy - 6} 12 {sy + 2}" stroke="var(--garment-2)" '
                f'stroke-width="2.4" fill="none" stroke-linecap="round"/>')
        return body + shade_side + seam + hips
    return body + shade_side + hips


def _head_f(j):
    hx, hy = j["head"]
    return (f'<g class="part-head" transform="translate({hx},{hy})">'
            f'<ellipse cx="9.5" cy="1" rx="2.2" ry="2.8" fill="var(--skin-2)"/>'
            f'<rect x="-4" y="9" width="8" height="8" rx="2.6" fill="var(--skin)"/>'
            f'<ellipse cx="0" cy="0" rx="12.5" ry="13.5" fill="var(--skin)"/>'
            f'<path d="M 5 -12 Q 13.5 -8 12.4 3 Q 12.8 9 8 11.5 Q 12 3 10 -4 Z" fill="var(--skin-2)" opacity="0.55"/>'
            f'<g class="hair"></g><g class="acc-head"></g>'
            f'<g class="face">'
            f'<circle class="eye eye-n" cx="-6.6" cy="-1" r="1.8" fill="{INK_FIX}"/>'
            f'<circle class="eye eye-f" cx="1.8" cy="-1.4" r="1.55" fill="{INK_FIX}"/>'
            f'<rect class="lid" x="-9" y="-3.2" width="5" height="4.4" rx="2" fill="var(--skin)" opacity="0"/>'
            f'<rect class="lid" x="-0.6" y="-3.4" width="4.6" height="4.2" rx="2" fill="var(--skin)" opacity="0"/>'
            f'<g>'
            f'<g class="brows" stroke="{INK_FIX}" stroke-opacity="0.75" stroke-width="1.3" fill="none" stroke-linecap="round"></g>'
            f'<path class="mouth" d="" stroke="{INK_FIX}" stroke-opacity="0.7" stroke-width="1.3" fill="none" stroke-linecap="round"/>'
            f'</g></g>'
            f'<ellipse cx="-5" cy="-7" rx="6" ry="3.2" fill="#FFFFFF" opacity="0.12"/>'
            f"</g>")


def _head_r(j):
    hx, hy = j["head"]
    return (f'<g class="part-head" transform="translate({hx},{hy})">'
            f'<rect x="-4" y="8" width="8" height="9" rx="2.6" fill="var(--skin-2)"/>'
            f'<ellipse cx="0" cy="0" rx="12.5" ry="13.5" fill="var(--skin)"/>'
            f'<path d="M 5 -12 Q 13.5 -8 12.4 3 Q 12.8 9 8 11.5 Q 12 3 10 -4 Z" fill="var(--skin-2)" opacity="0.5"/>'
            f'<g class="hair hair-back"></g><g class="acc-head"></g>'
            f"</g>")


REAR_SIT_LEGS = {"nhip": (-5, -30), "nkne": (-6, -24), "nank": (-6.5, -4),
                 "fhip": (5, -29), "fkne": (4, -23), "fank": (3.5, -4)}


def char2_body(pose_name: str, facing: str) -> str:
    j = dict(RIG[pose_name])
    rear = facing == "r"
    if rear and pose_name in ("sit", "type"):
        j.update(REAR_SIT_LEGS)
    far_arm = _limb(j["fsh"], j["fel"], j["fwr"], 8, "var(--garment-2)",
                    hand=None if (rear and pose_name == "type") else "var(--skin-2)")
    near_arm = _limb(j["nsh"], j["nel"], j["nwr"], 8.5, "var(--garment)",
                     hand=None if (rear and pose_name == "type") else "var(--skin)")
    far_leg = _limb(j["fhip"], j["fkne"], j["fank"], 9, "var(--trouser-2)")
    near_leg = _limb(j["nhip"], j["nkne"], j["nank"], 9.5, "var(--trouser)")
    foot_fn = _foot_r if rear else _foot_f
    far_foot = foot_fn(j["fank"], far=True)
    near_foot = foot_fn(j["nank"], far=False)
    head = _head_r(j) if rear else _head_f(j)
    torso = _torso(j, rear=rear)
    prop = PROPS.get(j["prop"], "") if j["prop"] else ""
    extra = ""
    if pose_name == "celebrate":
        extra = (f'<g fill="{GOLD}"><circle cx="-24" cy="-110" r="1.8"/>'
                 f'<circle cx="-12" cy="-115" r="1.4"/><circle cx="-30" cy="-102" r="1.3"/></g>')
    if pose_name == "talk":
        extra = ('<g stroke="var(--dim)" stroke-width="1.6" fill="none" stroke-linecap="round">'
                 '<path d="M -32 -80 Q -36 -76 -32 -72"/><path d="M -37 -83 Q -43 -76 -37 -69"/></g>')
    if pose_name == "think":
        extra = '<circle cx="-20" cy="-102" r="2" fill="var(--dim)"/><circle cx="-15" cy="-108" r="2.8" fill="var(--dim)"/>'
    if pose_name == "alarmed":
        extra = f'<path d="M 20 -104 L 20 -96 M 20 -92 L 20 -91" stroke="{STATUS["warn"]}" stroke-width="3" stroke-linecap="round"/>'
    shadow_el = '<ellipse class="shadow" filter="url(#softblur)" cx="4" cy="2" rx="19" ry="7"/>'
    bust = (f'<g class="bust" transform="rotate({j["lean"]} 0 {j["hips_y"]})">'
            f"{torso}<g class=\"garment-overlay\"></g>{head}<g class=\"accessory\"></g></g>")
    return (f'<g transform="translate(0,{j["bob"]})">' + shadow_el + far_arm + far_leg + far_foot
            + bust + near_leg + near_foot + near_arm + prop + extra + "</g>")


def characters_svg() -> str:
    syms = []
    for pose in RIG:
        SYM_VB[f"c2-f-{pose}"] = (-56.0, -122.0, 112.0, 132.0)
        syms.append(f'<symbol id="c2-f-{pose}" viewBox="-56 -122 112 132" overflow="visible">'
                    f"{char2_body(pose, 'f')}</symbol>")
        if pose in R_POSES:
            SYM_VB[f"c2-r-{pose}"] = (-56.0, -122.0, 112.0, 132.0)
            syms.append(f'<symbol id="c2-r-{pose}" viewBox="-56 -122 112 132" overflow="visible">'
                        f"{char2_body(pose, 'r')}</symbol>")
    return "<defs>" + "".join(syms) + "</defs>"


def char_css() -> str:
    rules = []
    for role, (light, dark) in ROLE.items():
        rules.append(f".role-{role}{{--garment:{light};--garment-2:{shade(light, -0.16)};"
                     f"--trouser:{shade(light, -0.42)};--trouser-2:{shade(light, -0.52)};}}")
        rules.append(f':root[data-theme="dark"] .role-{role}'
                     f"{{--garment:{dark};--garment-2:{shade(dark, -0.16)};}}")
    for k, v in SKIN.items():
        rules.append(f".skin-{k}{{--skin:{v};--skin-2:{shade(v, -0.12)};}}")
    for k, v in HAIR.items():
        rules.append(f".hair-{k}{{--hair:{v};}}")
    for k, v in STATUS.items():
        rules.append(f".status-{k}{{--status:{v};}}")
    return "\n".join(rules)


SKIN_JS = ("""
const OVERLAYS = %s, ACCESSORIES = %s, HAIR_F = %s, HAIR_F_EXTRA = %s,
      HAIR_B = %s, HAIR_B_EXTRA = %s, MOODS = %s, ACC_HEAD = %s;
function skinChars(root) {
  (root || document).querySelectorAll('g.char').forEach(g => {
    if (g.dataset.skinned) return;
    const role = [...g.classList].find(c => c.startsWith('role-'));
    const inner = g.querySelector('use');
    if (!role || !inner) return;
    const key = role.slice(5);
    const sym = document.querySelector(inner.getAttribute('href'));
    if (!sym) return;
    const clone = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    clone.innerHTML = sym.innerHTML;
    const ov = clone.querySelector('.garment-overlay'); if (ov) ov.innerHTML = OVERLAYS[key] || '';
    const ac = clone.querySelector('.accessory'); if (ac) ac.innerHTML = ACCESSORIES[key] || '';
    const isRear = !!clone.querySelector('.hair-back');
    const ah = clone.querySelector('.acc-head');
    if (ah) ah.innerHTML = ((ACC_HEAD[key] || {})[isRear ? 'r' : 'f']) || '';
    const hairCls = [...g.classList].find(c => c.startsWith('hair-style-'));
    const style = hairCls ? hairCls.slice(11) : 'crop';
    const hf = clone.querySelector('.part-head .hair:not(.hair-back)');
    if (hf) hf.innerHTML = '<path d="' + HAIR_F[style] + '" fill="var(--hair)"/>' + (HAIR_F_EXTRA[style] || '');
    const hb = clone.querySelector('.part-head .hair-back');
    if (hb) hb.innerHTML = '<path d="' + HAIR_B[style] + '" fill="var(--hair)"/>' + (HAIR_B_EXTRA[style] || '');
    const moodCls = [...g.classList].find(c => c.startsWith('mood-'));
    const mood = MOODS[moodCls ? moodCls.slice(5) : (g.dataset.mood || 'neutral')] || MOODS.neutral;
    const brows = clone.querySelector('.brows');
    if (brows) brows.innerHTML = '<path d="' + mood.browN + '"/><path d="' + mood.browF + '"/>';
    const mouth = clone.querySelector('.mouth');
    if (mouth) mouth.setAttribute('d', mood.mouth);
    g.replaceChild(clone, inner);
    g.dataset.skinned = '1';
  });
}
skinChars();
""")


def skin_js() -> str:
    return SKIN_JS % (json.dumps(GARMENT_OVERLAY), json.dumps(ACCESSORIES),
                      json.dumps(HAIR_F), json.dumps(HAIR_F_EXTRA),
                      json.dumps(HAIR_B), json.dumps(HAIR_B_EXTRA), json.dumps(MOODS),
                      json.dumps(ACC_HEAD))


# -------------------------------------------------------------- furniture --
def sym(sid, body, vb="-96 -128 192 160"):
    SYM_VB[sid] = tuple(float(v) for v in vb.split())
    return f'<symbol id="{sid}" viewBox="{vb}" overflow="visible">{body}</symbol>'


def furniture_svg() -> str:
    s = []
    s.append(sym("desk",
        shadow(-1, -0.5, 2, 1)
        + iso_box(-1, -0.35, 0.16, 0.7, 34, DESK_LEG)
        + iso_box(0.84, -0.35, 0.16, 0.7, 34, DESK_LEG)
        + iso_box(-1.06, -0.56, 2.12, 1.12, 7, DESK, z=34)))
    s.append(sym("chair",
        shadow(-0.4, -0.4, 0.8, 0.8)
        + iso_box(-0.09, -0.09, 0.18, 0.18, 18, DESK_LEG)
        + iso_box(-0.42, -0.42, 0.84, 0.84, 8, SEAT, z=18)
        + iso_box(-0.42, -0.42, 0.84, 0.16, 32, SEAT, z=26)))
    s.append(sym("monitor",
        "<g>"
        + iso_box(-0.12, -0.12, 0.24, 0.24, 3, DEVICE)
        + f'<rect x="-2.5" y="-14" width="5" height="12" rx="1" fill="{DEVICE[1]}"/>'
        + f'<g transform="translate(0,-14) {SKEW}"><rect x="-20" y="-26" width="40" height="26" rx="2.5" fill="{DEVICE[1]}"/>'
        + f'<rect x="-18" y="-24" width="36" height="22" rx="1.5" fill="{SCREEN}"/>'
        + f'<g class="mon-ui" stroke="{SCREEN_UI}" stroke-width="1.6" stroke-linecap="round">'
        + '<path d="M -14 -19 L 2 -19 M -14 -14 L 12 -14 M -14 -9 L 8 -9"/></g></g></g>'))
    s.append(sym("laptop",
        iso_box(-0.4, -0.26, 0.8, 0.52, 2, DEVICE)
        + f'<g transform="translate(-12,-2) {SKEW}"><rect x="-2" y="-20" width="27" height="19" rx="2" fill="{DEVICE[1]}"/>'
        + f'<rect x="0" y="-18" width="23" height="15" rx="1" fill="{SCREEN}"/></g>'))
    key_lines = ""
    for i in range(5):
        x1, y1 = iso(-0.24 + i * 0.105, -0.08, 2.4)
        x2, y2 = iso(-0.24 + i * 0.105 - 0.05, 0.08, 2.4)
        key_lines += f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'
    s.append(sym("keyboard",
        iso_box(-0.32, -0.14, 0.64, 0.28, 2.4, DESK_LEG)
        + f'<g stroke="{INK}" stroke-opacity="0.16" stroke-width="1.5">{key_lines}</g>'))
    s.append(sym("mouse", iso_box(-0.08, -0.11, 0.16, 0.22, 3, DEVICE)))
    s.append(sym("desk-lamp",
        iso_box(-0.1, -0.1, 0.2, 0.2, 2.5, DEVICE)
        + f'<path d="M 0 -2 L 7 -26 L -6 -38" stroke="{DEVICE[1]}" stroke-width="3" fill="none" stroke-linecap="round"/>'
        + f'<path d="M -13 -44 L -1 -36 L -6 -30 L -17 -37 Z" fill="{DEVICE[2]}"/>'
        + f'<ellipse cx="-10" cy="-33" rx="5" ry="2.5" fill="{GOLD}" opacity="0.55"/>'))
    mug_hi = shade("#A96B58", 0.5)
    s.append(sym("mug",
        '<path d="M -4 -10 L -4 -1 Q -4 1 -1.5 1 L 3 1 Q 5.5 1 5.5 -1 L 5.5 -10 Z" fill="var(--terra)"/>'
        + f'<ellipse cx="0.75" cy="-10" rx="4.9" ry="2.1" fill="{mug_hi}"/>'
        + '<path d="M 5.5 -8 Q 9.5 -8 9.5 -5 Q 9.5 -2.5 5.5 -3" fill="none" stroke="var(--terra)" stroke-width="1.8"/>'
        + '<path class="steam" d="M 0 -13 Q 2 -16 0 -19 Q -2 -22 0 -25" stroke="var(--dim)" stroke-width="1.3" fill="none" stroke-linecap="round" stroke-dasharray="3 3"/>', "-24 -34 48 46"))
    p1 = pts([iso(-0.28, -0.2, 1), iso(0.28, -0.2, 1), iso(0.28, 0.2, 1), iso(-0.28, 0.2, 1)])
    p2 = pts([iso(-0.24, -0.14, 2.4), iso(0.32, -0.14, 2.4), iso(0.32, 0.26, 2.4), iso(-0.24, 0.26, 2.4)])
    s.append(sym("papers",
        f'<g transform="translate(0,-1)"><polygon points="{p1}" fill="{PAPER}" stroke="{CARD_EDGE}" stroke-width="0.8"/>'
        f'<polygon points="{p2}" fill="{PAPER}" stroke="{CARD_EDGE}" stroke-width="0.8"/></g>', "-32 -32 64 40"))
    s.append(sym("desk-plant",
        iso_box(-0.09, -0.09, 0.18, 0.18, 7, WOOD)
        + '<g fill="var(--leaf)"><path d="M 0 -7 Q -8 -14 -3 -22 Q 1 -15 0 -7"/><path d="M 0 -7 Q 8 -15 4 -23 Q -1 -15 0 -7"/><path d="M 0 -8 Q 0 -18 0 -24 Q 3 -16 1 -8"/></g>', "-24 -36 48 44"))
    s.append(sym("beacon",
        f'<rect x="-1.5" y="-16" width="3" height="14" rx="1.5" fill="{DEVICE[1]}"/>'
        + '<circle class="beacon-orb" cx="0" cy="-20" r="5" fill="var(--status, #64748B)"/>'
        + '<circle cx="-1.6" cy="-21.6" r="1.6" fill="#FFFFFF" opacity="0.5"/>', "-16 -32 32 36"))
    return "<defs>" + "".join(s) + "</defs>"


# ------------------------------------------------------------ sprint board --
BOARD_COLS = ["todo", "design", "build", "test", "blocked", "done"]
BOARD_SLOTS = {c: [(-116 + i * 39 + 17.5, -62 + j * 16) for j in range(3)]
               for i, c in enumerate(BOARD_COLS)}


def ticket(w, h, sid, kind=False):
    kind_chip = (f'<rect x="{w / 2 - 9}" y="{-h / 2 + 2.5}" width="7" height="4" rx="1" '
                 f'fill="var(--status, #64748B)"/>') if kind else ""
    return sym(sid,
        f'<rect x="{-w / 2}" y="{-h / 2}" width="{w}" height="{h}" rx="3" fill="var(--paper2)" '
        f'stroke="{CARD_EDGE}" stroke-width="1.2"/>'
        f'<rect x="{-w / 2}" y="{-h / 2}" width="4" height="{h}" rx="2" fill="var(--status, #64748B)"/>'
        f'<path d="M {-w / 2 + 7} {-h / 2 + 6} L {w / 2 - 5} {-h / 2 + 6} M {-w / 2 + 7} {-h / 2 + 11} '
        f'L {w / 2 - 10} {-h / 2 + 11}" stroke="var(--dim)" stroke-width="1.4" stroke-linecap="round"/>'
        + kind_chip, f"{-w / 2 - 4} {-h / 2 - 4} {w + 8} {h + 8}")


def icon(sid, body):
    SYM_VB[sid] = (-4.0, -4.0, 24.0, 24.0)
    return (f'<symbol id="{sid}" viewBox="-4 -4 24 24" overflow="visible">'
            f'<rect x="-4" y="-4" width="24" height="24" rx="7" fill="var(--badge-chip)"/>'
            f'<g fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round">{body}</g></symbol>')


def sprintboard_svg() -> str:
    s = []
    cols = ""
    for i, c in enumerate(BOARD_COLS):
        x = -116 + i * 39
        cols += (f'<rect x="{x}" y="-78" width="35" height="66" rx="2.5" fill="{PANEL}" '
                 f'stroke="{CARD_EDGE}" stroke-width="0.8"/>'
                 f'<rect x="{x}" y="-78" width="35" height="5" rx="2.5" fill="{STATUS[c]}"/>')
        for j in range(2 - (i % 2)):
            cols += (f'<rect x="{x + 3}" y="{-68 + j * 16}" width="29" height="12" rx="2" '
                     f'fill="var(--paper2)" stroke="{CARD_EDGE}" stroke-width="1"/>'
                     f'<rect x="{x + 3}" y="{-68 + j * 16}" width="2.5" height="12" rx="1.2" fill="{STATUS[c]}"/>')
    s.append(sym("sprint-board",
        shadow(-1.8, -0.14, 3.6, 0.28)
        + iso_box(-1.8, -0.1, 3.6, 0.2, 6, DESK_LEG)
        + f'<g class="board-plane" transform="translate(0,-4) {SKEW}"><rect x="-124" y="-86" width="248" height="80" rx="4" fill="{BOARD_BG}" '
        f'stroke="{CARD_EDGE}" stroke-width="1.2"/>{cols}</g>', "-150 -160 300 190"))
    # empty board (no sample cards) for the motion prototype
    cols_empty = ""
    for i, c in enumerate(BOARD_COLS):
        x = -116 + i * 39
        cols_empty += (f'<rect x="{x}" y="-78" width="35" height="66" rx="2.5" fill="{PANEL}"/>'
                       f'<rect x="{x}" y="-78" width="35" height="5" rx="2.5" fill="{STATUS[c]}"/>')
        seeds = {'todo': [1], 'design': [0], 'done': [1, 2]}.get(c, [])
        for j in seeds:
            cols_empty += (f'<rect x="{x + 3}" y="{-68 + j * 16}" width="29" height="12" rx="2" '
                           f'fill="var(--paper2)" stroke="{CARD_EDGE}" stroke-width="1"/>'
                           f'<rect x="{x + 3}" y="{-68 + j * 16}" width="2.5" height="12" rx="1.2" fill="{STATUS[c]}"/>')
    s.append(sym("sprint-board-live",
        shadow(-1.8, -0.14, 3.6, 0.28)
        + iso_box(-1.8, -0.1, 3.6, 0.2, 6, DESK_LEG)
        + f'<g class="board-plane" transform="translate(0,-4) {SKEW}"><rect x="-124" y="-86" width="248" height="80" rx="4" fill="{BOARD_BG}" '
        f'stroke="{CARD_EDGE}" stroke-width="1.2"/>{cols_empty}<g class="board-cards"></g></g>', "-150 -160 300 190"))
    s.append(ticket(36, 24, "story-card"))
    s.append(ticket(28, 18, "task-card"))
    s.append(ticket(28, 18, "task-card-build", True))
    s.append(ticket(28, 18, "task-card-test", True))
    s.append(ticket(28, 18, "task-card-bug", True))
    ac_rows = "".join(
        f'<g transform="translate(-6,{-8 + i * 7})"><rect x="-2" y="-2" width="4" height="4" rx="1" '
        'fill="none" stroke="var(--dim)" stroke-width="1.2"/>'
        '<path d="M 4 0 L 14 0" stroke="var(--dim)" stroke-width="1.2" stroke-linecap="round"/></g>'
        for i in range(4))
    s.append(sym("ac-checklist",
        f'<rect x="-11" y="-14" width="22" height="28" rx="2" fill="var(--paper2)" stroke="{CARD_EDGE}"/>'
        + ac_rows, "-16 -18 32 36"))
    s.append(sym("stamp-pass",
        f'<circle cx="0" cy="0" r="11" fill="none" stroke="{STATUS["done"]}" stroke-width="2.5"/>'
        f'<path d="M -5 0 L -1.5 4 L 5.5 -4" stroke="{STATUS["done"]}" stroke-width="2.6" fill="none" '
        f'stroke-linecap="round" stroke-linejoin="round"/>', "-16 -16 32 32"))
    s.append(sym("stamp-fail",
        f'<circle cx="0" cy="0" r="11" fill="none" stroke="{STATUS["blocked"]}" stroke-width="2.5"/>'
        f'<path d="M -4.5 -4.5 L 4.5 4.5 M 4.5 -4.5 L -4.5 4.5" stroke="{STATUS["blocked"]}" '
        f'stroke-width="2.6" stroke-linecap="round"/>', "-16 -16 32 32"))
    fl, fll, fld = shade(GOLD, 0.45), shade(GOLD, 0.62), shade(GOLD, -0.25)
    s.append(sym("evidence-folder",
        f'<path d="M -14 -9 L -6 -9 L -3.5 -13 L 5 -13 L 7 -9 L 14 -9 L 14 10 L -14 10 Z" fill="{fl}"/>'
        f'<rect x="-14" y="-6" width="28" height="16" rx="2" fill="{fll}"/>'
        f'<path d="M -8 0 L 8 0 M -8 4 L 4 4" stroke="{fld}" stroke-width="1.4" stroke-linecap="round"/>', "-18 -18 36 32"))
    s.append(sym("release-marker",
        f'<path d="M 0 8 L 0 -14" stroke="#6B5F4C" stroke-width="2.2" stroke-linecap="round"/>'
        f'<path d="M 0 -14 L 12 -10.5 L 0 -7 Z" fill="{STATUS["done"]}"/>', "-16 -20 32 32"))
    s.append(sym("shipped-ribbon",
        f'<circle cx="0" cy="-3" r="7" fill="{GOLD}"/>'
        f'<circle cx="0" cy="-3" r="4.4" fill="{shade(GOLD, 0.35)}"/>'
        f'<path d="M -4 2 L -6.5 10 L -2.5 7.5 L 0 11 L 1 3 Z" fill="{GOLD}"/>', "-12 -14 24 28"))
    s.append(sym("blocked-chain",
        f'<g stroke="{STATUS["blocked"]}" stroke-width="2.2" fill="none">'
        '<rect x="-9" y="-4" width="8" height="6" rx="3"/><rect x="1" y="-4" width="8" height="6" rx="3"/>'
        '<path d="M -1 -1 L 1 -1"/></g>', "-14 -10 28 16"))
    s.append(sym("risk-flame",
        f'<path d="M 0 8 Q -7 4 -5 -3 Q -3.5 1 -1 -1 Q -4 -8 1 -12 Q 0 -6 3 -4 Q 6 -1 5 3 Q 4 7 0 8 Z" fill="{STATUS["warn"]}"/>'
        f'<path d="M 0 6 Q -3 3.5 -1.8 0 Q 0 2 1.6 0.5 Q 2.8 3.5 0 6 Z" fill="{shade(STATUS["warn"], 0.5)}"/>', "-10 -14 20 26"))
    s.append(icon("icon-check", '<path d="M 3 8.5 L 6.5 12 L 13 4.5"/>'))
    s.append(icon("icon-cross", '<path d="M 4 4 L 12 12 M 12 4 L 4 12"/>'))
    s.append(icon("icon-bug", '<ellipse cx="8" cy="9" rx="4" ry="5"/><path d="M 8 4 L 8 2 M 4.5 6 L 2.5 4.5 M 11.5 6 L 13.5 4.5 M 4 10 L 1.5 10 M 12 10 L 14.5 10 M 4.5 13 L 3 15 M 11.5 13 L 13 15"/>'))
    s.append(icon("icon-lock", '<rect x="4" y="7" width="8" height="6.5" rx="1.5"/><path d="M 5.5 7 L 5.5 5 Q 5.5 2.5 8 2.5 Q 10.5 2.5 10.5 5 L 10.5 7"/>'))
    s.append(icon("icon-question", '<path d="M 5.5 5.5 Q 5.5 3 8 3 Q 10.5 3 10.5 5.5 Q 10.5 7.5 8 8.5 L 8 10.5"/><path d="M 8 13.5 L 8 13.6"/>'))
    s.append(icon("icon-flag", '<path d="M 4 14 L 4 2.5 M 4 3 L 12 5 L 4 8"/>'))
    s.append(icon("icon-folder", '<path d="M 2 5 L 6 5 L 7.5 3 L 14 3 L 14 13 L 2 13 Z"/>'))
    s.append(icon("icon-magnifier", '<circle cx="7" cy="7" r="4"/><path d="M 10 10 L 14 14"/>'))
    s.append(icon("icon-pencil", '<path d="M 3 13 L 3.8 10 L 11 2.8 L 13.2 5 L 6 12.2 Z M 10 4 L 12 6"/>'))
    s.append(icon("icon-hammer", '<path d="M 9 3 L 13 7 L 11 9 L 7 5 Z M 8 6 L 2.5 11.5 L 4.5 13.5 L 10 8"/>'))
    return "<defs>" + "".join(s) + "</defs>"


# ------------------------------------------------------------------ collab --
def collab_svg() -> str:
    s = []
    s.append(sym("meeting-table",
        shadow(-1.2, -0.7, 2.4, 1.4)
        + iso_box(-0.16, -0.16, 0.32, 0.32, 30, DESK_LEG)
        + iso_box(-1.2, -0.7, 2.4, 1.4, 7, WOOD, z=30)))
    pins = "".join(
        f'<rect x="{-84 + (i % 4) * 45}" y="{-62 + (i // 4) * 26}" width="36" height="20" rx="2.5" '
        f'fill="var(--paper2)" stroke="{CARD_EDGE}" stroke-width="1"/>'
        f'<rect x="{-84 + (i % 4) * 45}" y="{-62 + (i // 4) * 26}" width="3" height="20" rx="1.5" fill="{STATUS["todo"]}"/>'
        for i in range(8))
    s.append(sym("planning-wall",
        iso_box(-1.4, -0.06, 2.8, 0.12, 4, DESK_LEG)
        + f'<g transform="translate(0,-3) {SKEW}"><rect x="-96" y="-72" width="192" height="68" rx="4" fill="{BOARD_BG}" '
          f'stroke="{CARD_EDGE}" stroke-width="1.2"/>{pins}</g>', "-120 -135 240 165"))
    s.append(sym("showcase-screen",
        shadow(-1, -0.12, 2, 0.24)
        + iso_box(-0.14, -0.1, 0.28, 0.2, 26, DEVICE)
        + f'<g transform="translate(0,-24) {SKEW}"><rect x="-70" y="-48" width="140" height="48" rx="4" fill="{DEVICE[1]}"/>'
        f'<rect x="-66" y="-44" width="132" height="40" rx="2.5" fill="{SCREEN}"/>'
        f'<g stroke="{SCREEN_UI}" stroke-width="2" stroke-linecap="round">'
        '<path d="M -56 -34 L -20 -34 M -56 -26 L -8 -26 M -56 -18 L -28 -18 M -56 -10 L -36 -10"/></g>'
        f'<circle cx="48" cy="-22" r="10" fill="none" stroke="{GOLD}" stroke-width="2.5"/>'
        f'<path d="M 43 -22 L 47 -18 L 54 -27" stroke="{GOLD}" stroke-width="2.5" fill="none" stroke-linecap="round"/></g>',
        "-100 -130 200 160"))
    s.append(sym("decision-tray",
        f'<g><path d="M -18 0 L -14 -8 L 14 -8 L 18 0 L 18 6 L -18 6 Z" fill="{shade(GOLD, 0.35)}"/>'
        f'<path d="M -18 0 L 18 0 L 18 6 L -18 6 Z" fill="{GOLD}"/>'
        f'<rect x="-11" y="-14" width="20" height="12" rx="2" fill="var(--paper2)" stroke="{CARD_EDGE}"/>'
        f'<rect x="-11" y="-14" width="3" height="12" rx="1.5" fill="{STATUS["blocked"]}"/></g>', "-24 -22 48 34"))
    s.append(sym("handoff-ticket",
        f'<g><rect x="-11" y="-8" width="22" height="15" rx="2.5" fill="var(--paper2)" stroke="{CARD_EDGE}"/>'
        '<rect x="-11" y="-8" width="4" height="15" rx="2" fill="var(--status, #B45309)"/>'
        f'<g stroke="{DIM}" stroke-width="1.5" stroke-linecap="round" opacity="0.7">'
        '<path d="M -20 -3 L -15 -3 M -22 2 L -15 2"/></g></g>', "-28 -14 52 28"))
    rug_outer = pts([iso(-1.1, -1.1, 0), iso(1.1, -1.1, 0), iso(1.1, 1.1, 0), iso(-1.1, 1.1, 0)])
    rug_inner = pts([iso(-0.85, -0.85, 0), iso(0.85, -0.85, 0), iso(0.85, 0.85, 0), iso(-0.85, 0.85, 0)])
    s.append(sym("retro-rug",
        f'<polygon points="{rug_outer}" fill="var(--rug)" stroke="var(--rug)" stroke-width="2" stroke-linejoin="round"/>'
        f'<polygon points="{rug_inner}" fill="none" stroke="var(--terra)" stroke-width="2" opacity="0.75"/>', "-80 -48 160 96"))
    s.append(sym("beanbag",
        flat_shadow(0, 2, 16)
        + '<path d="M -16 0 Q -18 -14 -6 -18 Q 8 -21 15 -11 Q 19 -3 12 2 Q 0 7 -16 0 Z" fill="var(--terra)"/>'
        + f'<path d="M -12 -4 Q -6 -14 6 -15" stroke="{shade('#A96B58', 0.3)}" stroke-width="2.5" fill="none" stroke-linecap="round"/>', "-28 -30 56 42"))
    return "<defs>" + "".join(s) + "</defs>"


# ------------------------------------------------------------- environment --
def environment_svg() -> str:
    s = []
    tiles = "".join(
        f'<polygon points="{pts([iso(x, y, 0), iso(x + 1, y, 0), iso(x + 1, y + 1, 0), iso(x, y + 1, 0)])}" '
        f'fill="{(FLOOR_A if (x + y) % 2 == 0 else FLOOR_B)[0]}"/>'
        for x in range(-1, 1) for y in range(-1, 1))
    s.append(sym("floor-2x2", tiles, "-80 -48 160 96"))
    s.append(sym("wall-x", iso_box(-2, -0.08, 4, 0.16, 110, WALL), "-150 -160 300 190"))
    s.append(sym("wall-y", iso_box(-0.08, -2, 0.16, 4, 110, WALL_S), "-150 -160 300 190"))
    s.append(sym("stairs", shadow(-0.75, -0.5, 1.5, 1)
              + "".join(iso_box(-0.75, -0.5 + i * 0.33, 1.5, 0.33, 10 + i * 10, FLOOR_B) for i in range(3)),
              "-90 -80 180 120"))
    door_panel = pts([iso(-0.8, 0.08, 80), iso(0.8, 0.08, 80), iso(0.8, 0.08, 0), iso(-0.8, 0.08, 0)])
    knob = iso(0.55, 0.08, 40)
    s.append(sym("doorway",
        iso_box(-1.1, -0.08, 0.25, 0.16, 96, WALL)
        + iso_box(0.85, -0.08, 0.25, 0.16, 96, WALL)
        + iso_box(-1.1, -0.08, 2.2, 0.16, 14, WALL, z=82)
        + f'<polygon points="{door_panel}" fill="{WOOD[1]}" opacity="0.95" stroke="{WOOD[1]}" stroke-width="2" stroke-linejoin="round"/>'
        + f'<circle cx="{knob[0]:.0f}" cy="{knob[1]:.0f}" r="2.2" fill="{GOLD}"/>',
        "-120 -140 240 170"))
    s.append(sym("divider", shadow(-1, -0.07, 2, 0.14) + iso_box(-1, -0.07, 2, 0.14, 52, SEAT), "-90 -90 180 120"))
    s.append(sym("divider-y", shadow(-0.07, -1.1, 0.14, 2.2) + iso_box(-0.07, -1.1, 0.14, 2.2, 52, SEAT), "-90 -90 180 130"))
    s.append(sym("shelf",
        shadow(-0.7, -0.25, 1.4, 0.5)
        + iso_box(-0.7, -0.25, 1.4, 0.5, 4, WOOD, z=0)
        + iso_box(-0.7, -0.25, 1.4, 0.5, 4, WOOD, z=28)
        + iso_box(-0.7, -0.25, 1.4, 0.5, 4, WOOD, z=56)
        # wood uprights, inset so they read as the shelf's own frame (the old
        # full-height grey slabs read as unfinished placeholder blocks)
        + iso_box(-0.68, -0.25, 0.08, 0.5, 56, WOOD, z=4)
        + iso_box(0.6, -0.25, 0.08, 0.5, 56, WOOD, z=4)
        # middle shelf: binder spines at mixed heights
        + iso_box(-0.5, -0.15, 0.1, 0.3, 19, SEAT, z=32)
        + iso_box(-0.36, -0.15, 0.1, 0.3, 16, WOOD, z=32)
        + iso_box(-0.22, -0.15, 0.1, 0.3, 18, SEAT, z=32)
        + iso_box(-0.08, -0.15, 0.1, 0.3, 15, DESK, z=32)
        # lower shelf: document tray + flat folder stack
        + iso_box(0.05, -0.15, 0.42, 0.32, 10, WOOD, z=4)
        + iso_box(-0.5, -0.12, 0.34, 0.26, 6, DESK, z=4), "-90 -110 180 140"))
    s.append(sym("plant-large",
        shadow(-0.3, -0.3, 0.6, 0.6)
        + iso_box(-0.22, -0.22, 0.44, 0.44, 16, WOOD)
        + '<g fill="var(--leaf)" transform="translate(0,-14)">'
          '<path d="M 0 0 Q -16 -10 -12 -30 Q -2 -18 0 0"/>'
          '<path d="M 0 0 Q 16 -12 11 -32 Q 2 -18 0 0"/>'
          '<path d="M 0 -2 Q -4 -26 0 -40 Q 6 -24 0 -2"/>'
          '<path d="M 0 0 Q -22 -4 -26 -18 Q -10 -14 0 0"/>'
          '<path d="M 0 0 Q 22 -6 25 -20 Q 10 -14 0 0"/></g>', "-48 -80 96 108"))
    s.append(sym("floor-lamp",
        flat_shadow(0, 0, 12)
        + iso_box(-0.12, -0.12, 0.24, 0.24, 3, DEVICE)
        + f'<path d="M 0 -3 L 0 -66" stroke="{DEVICE[1]}" stroke-width="3" stroke-linecap="round"/>'
        + f'<path d="M -11 -66 L 11 -66 L 7 -80 L -7 -80 Z" fill="{shade(GOLD, 0.5)}"/>'
        + f'<ellipse cx="0" cy="-66" rx="11" ry="3.5" fill="{GOLD}" opacity="0.5"/>', "-32 -96 64 108"))
    s.append(sym("window",
        f'<g transform="{SKEW}"><rect x="-34" y="-64" width="68" height="52" rx="3" fill="{DEVICE[1]}" opacity="0.14"/>'
        f'<rect x="-30" y="-60" width="60" height="44" rx="2" fill="{SCREEN}" opacity="0.9"/>'
        f'<path d="M 0 -60 L 0 -16 M -30 -38 L 30 -38" stroke="{PANEL_BORDER}" stroke-width="2"/>'
        f'<circle cx="18" cy="-52" r="6" fill="{shade(GOLD, 0.55)}" opacity="0.85"/></g>', "-48 -92 96 112"))
    s.append(sym("art-frame",
        f'<g transform="{SKEW}"><rect x="-16" y="-46" width="32" height="40" rx="2" fill="{WOOD[1]}"/>'
        f'<rect x="-12" y="-42" width="24" height="32" rx="1" fill="{PANEL}"/>'
        f'<path d="M -12 -18 L -4 -30 L 2 -22 L 8 -34 L 12 -26 L 12 -10 L -12 -10 Z" fill="{shade('#3E8E85', 0.35)}"/>'
        f'<circle cx="4" cy="-36" r="3" fill="{shade(GOLD, 0.4)}"/></g>', "-28 -62 56 72"))
    s.append(sym("wall-clock",
        f'<g transform="{SKEW}"><circle cx="0" cy="-40" r="10" fill="{PANEL}" stroke="{CARD_EDGE}" stroke-width="2"/>'
        f'<path d="M 0 -40 L 0 -46 M 0 -40 L 4 -37" stroke="{INK_FIX}" stroke-width="1.6" stroke-linecap="round"/></g>', "-20 -64 40 48"))
    return "<defs>" + "".join(s) + "</defs>"


# ---------------------------------------------------------------- previews --
def theme_css() -> str:
    light = "".join(f"--{k}:{v[0]};" for k, v in CSS_VARS.items())
    dark = "".join(f"--{k}:{v[1]};" for k, v in CSS_VARS.items())
    extra_light = ("--leaf:#5E8A66;--rug:#E3C9BC;--shadow-c:rgba(58,48,36,0.13);"
                   "--badge-chip:#EDE6D7;")
    extra_dark = ("--leaf:#8FA37E;--rug:#4A3A32;--shadow-c:rgba(0,0,0,0.30);"
                  "--badge-chip:#3A342B;")
    return (
        ":root{" + light + extra_light + "}\n"
        '@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){' + dark + extra_dark + "}}\n"
        ':root[data-theme="dark"]{' + dark + extra_dark + "}\n"
        + char_css() + "\n"
        "*{box-sizing:border-box}"
        "body{margin:0;padding:1.4rem;background:var(--bg);color:var(--ink);"
        'font-family:"Fira Sans",-apple-system,"Segoe UI",system-ui,sans-serif;font-size:16px;line-height:1.5}'
        ".wrap{max-width:1480px;margin:0 auto}"
        "h1{font-size:1.5rem;margin:0 0 .2rem;letter-spacing:-.01em}"
        ".sub{color:var(--dim);font-size:.78rem;margin-bottom:1.1rem;font-family:'Fira Code',monospace}"
        ".sec{background:var(--panel);border:1px solid var(--panel-border);border-radius:16px;"
        "padding:1.1rem 1.3rem;margin-bottom:.9rem;box-shadow:0 1px 3px rgba(58,48,36,.07)}"
        ".sec>h2{font-size:.74rem;text-transform:uppercase;letter-spacing:.11em;color:var(--dim);margin:0 0 .8rem;"
        "display:flex;align-items:center;gap:.5rem}"
        ".sec>h2::before{content:'';width:.6rem;height:.6rem;border-radius:3px;background:var(--terra)}"
        ".row{display:flex;flex-wrap:wrap;gap:1.1rem;align-items:flex-end}"
        ".cell{display:flex;flex-direction:column;align-items:center;gap:.3rem}"
        ".cell svg{background:var(--bg);border-radius:12px}"
        ".cell .lab{font-size:.66rem;color:var(--dim);font-family:'Fira Code',monospace;text-align:center;max-width:210px}"
        ".chipname{font-size:.72rem;font-weight:600;background:var(--badge-chip);border-radius:999px;"
        "padding:.05rem .55rem}"
        ".shadow{fill:var(--shadow-c)}"
        ".swatches{display:flex;flex-wrap:wrap;gap:.55rem}"
        ".sw{width:118px;border-radius:10px;overflow:hidden;border:1px solid var(--panel-border)}"
        ".sw .c{height:42px}.sw .t{font-size:.6rem;padding:.25rem .45rem;font-family:'Fira Code',monospace}"
        ".tablewrap{overflow-x:auto}.md table{border-collapse:collapse;font-size:.7rem;min-width:920px}"
        ".md th{text-align:left;background:var(--badge-chip);font-weight:600}"
        ".md th,.md td{border:1px solid var(--panel-border);padding:.3rem .45rem;vertical-align:top;line-height:1.45}"
        ".md h3,.md h4{margin:.8rem 0 .4rem}.md p{font-size:.78rem;max-width:82ch}.md li{font-size:.78rem}"
        ".md code{font-family:'Fira Code',monospace;font-size:.9em;background:var(--badge-chip);"
        "padding:.06em .3em;border-radius:4px}"
        ".note{font-size:.74rem;color:var(--dim);max-width:76ch;line-height:1.55;margin:.5rem 0 0}"
        ".themetoggle{position:fixed;top:.9rem;right:.9rem;font-size:.7rem;padding:.3rem .7rem;border-radius:999px;"
        "border:1px solid var(--panel-border);background:var(--panel);color:var(--ink);cursor:pointer;z-index:9}"
        ".scene{display:flex;justify-content:center;overflow-x:auto}"
    )


TOGGLE_JS = ("document.querySelector('.themetoggle').addEventListener('click',()=>{"
             "const r=document.documentElement;"
             "r.dataset.theme=r.dataset.theme==='dark'?'light':'dark';});")

SOFTBLUR = ('<filter id="softblur" x="-40%" y="-40%" width="180%" height="180%">'
            '<feGaussianBlur stdDeviation="2.5"/></filter>')


def all_defs() -> str:
    return (f'<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>{SOFTBLUR}</defs>'
            f"{characters_svg()}{furniture_svg()}{sprintboard_svg()}{collab_svg()}{environment_svg()}</svg>")


ROLES_ORDER = [
    ("po", "Product Owner", "swept", "s2"), ("sm", "Scrum Master", "bob", "s1"),
    ("ba", "Business Analyst", "crop", "s3"), ("techba", "Technical BA", "bun", "s2"),
    ("dev", "Developer", "curls", "s4"), ("tester", "Tester", "short", "s1"),
]


def use_char(pose, role, hair, skin, scale=1.0, x=0, y=0, flip=False,
             facing="f", mood=None) -> str:
    sid = f"c2-{facing}-{pose}"
    vx, vy, vw, vh = SYM_VB[sid]
    sx = -scale if flip else scale
    mood_cls = f" mood-{mood}" if mood else ""
    return (f'<g class="char role-{role} skin-{skin} hair-style-{hair}{mood_cls}" '
            f'transform="translate({x},{y}) scale({sx},{scale})">'
            f'<use href="#{sid}" x="{vx:g}" y="{vy:g}" width="{vw:g}" height="{vh:g}"/></g>')


def svg_cell(inner, w=120, h=150, lab="", vb=None) -> str:
    vb = vb or f"{-w // 2} {-h + 20} {w} {h}"
    return (f'<div class="cell"><svg width="{w}" height="{h}" viewBox="{vb}">'
            f'<defs>{SOFTBLUR}</defs>{inner}</svg><div class="lab">{lab}</div></div>')


def scene_svg() -> str:
    W, D = 8, 6
    floor = "".join(
        f'<polygon points="{pts([iso(x, y, 0), iso(x + 1, y, 0), iso(x + 1, y + 1, 0), iso(x, y + 1, 0)])}" '
        f'fill="{(FLOOR_A if (x + y) % 2 == 0 else FLOOR_B)[0]}"/>'
        for x in range(0, W) for y in range(0, D))
    walls = iso_box(0, -0.16, W, 0.16, 110, WALL) + iso_box(-0.16, 0, 0.16, D, 110, WALL_S)
    rim = iso_box(0, D - 0.06, W, 0.06, 3, FLOOR_B) + iso_box(W - 0.06, 0, 0.06, D, 3, FLOOR_B)
    w1 = iso(0.75, 0, 0)
    w2 = iso(2.1, 0, 0)
    wallart = (f'<g transform="translate({w1[0]:.0f},{w1[1]:.0f})">{iuse("window")}</g>'
               f'<g transform="translate({w2[0]:.0f},{w2[1]:.0f})">{iuse("wall-clock")}</g>')

    def place(wx, wy, inner, key=None):
        px, py = iso(wx, wy, 0)
        return (key if key is not None else wx + wy,
                f'<g transform="translate({px:.1f},{py:.1f})">{inner}</g>')

    items = [
        # Dev workstation against the BACK wall — dev sits FACING the wall
        # (rear view), so the character belongs in the room.
        place(1.7, 0.75, iuse("desk"), key=0.9),
        place(1.35, 0.62, iuse("monitor", "translate(0,-41)"), key=1.0),
        place(2.0, 0.9, iuse("keyboard", "translate(0,-41)"), key=1.05),
        place(2.5, 0.6, iuse("mug", "translate(0,-41)"), key=1.06),
        place(1.05, 0.95, iuse("beacon", "translate(0,-41)", cls="status-build"), key=1.07),
        place(1.76, 1.64, use_char("type", "dev", "curls", "s4", 0.95, facing="r"), key=3.45),
        place(1.80, 1.78, iuse("chair"), key=3.3),
        # board on the back wall, in-plane
        place(5.5, 0.14, iuse("sprint-board", "scale(0.62)"), key=1.1),
        # hand-off midfloor
        place(3.6, 3.7, use_char("handoff", "sm", "bob", "s1", 0.98, flip=True), key=7.3),
        place(4.9, 2.85, use_char("stand", "tester", "short", "s1", 0.98), key=7.75),
        # warm human corner: terracotta rug + beanbag + plant
        place(1.5, 4.4, iuse("retro-rug"), key=5.0),
        place(1.1, 4.7, iuse("beanbag"), key=5.9),
        place(0.55, 3.6, iuse("plant-large"), key=4.2),
        place(7.2, 4.9, iuse("floor-lamp")),
        place(6.9, 1.3, use_char("read", "ba", "crop", "s3", 0.96), key=8.3),
    ]
    items.sort(key=lambda t: t[0])
    inner = floor + walls + wallart + "".join(i[1] for i in items) + rim
    return (f'<svg width="960" height="742" viewBox="-222 -168 512 396">'
            f"<defs>{SOFTBLUR}</defs>{inner}</svg>")


def kit_board_html() -> str:
    sw = ""
    named = ([("Wall cream", "#F7F2E7"), ("Floor sand", "#EFE8D9"), ("Oak", "#D9BB8E"),
              ("Terracotta deco", "#A96B58"), ("Teal accent", "#3E8E85"),
              ("Dusty blue", "#6C87B8"), ("Gold", GOLD)]
             + [(f"Role - {k.upper()}", v[0]) for k, v in ROLE.items()]
             + [(f"Status - {k}", v) for k, v in STATUS.items()]
             + [(f"Skin {k.upper()}", v) for k, v in SKIN.items()]
             + [(f"Hair {k.upper()}", v) for k, v in HAIR.items()])
    for name, hexv in named:
        sw += f'<div class="sw"><div class="c" style="background:{hexv}"></div><div class="t">{name}<br>{hexv}</div></div>'

    roles_row = "".join(
        svg_cell(use_char("stand", r, hair, skin), 124, 158,
                 f'<span class="chipname">{label}</span>')
        for r, label, hair, skin in ROLES_ORDER)

    facings_row = "".join([
        svg_cell(use_char("stand", "dev", "curls", "s4"), 116, 150, "front-3/4 (SW)"),
        svg_cell(use_char("stand", "dev", "curls", "s4", flip=True), 116, 150, "front-3/4 mirrored (SE)"),
        svg_cell(use_char("stand", "dev", "curls", "s4", facing="r"), 116, 150, "rear-3/4 (NE)"),
        svg_cell(use_char("stand", "dev", "curls", "s4", facing="r", flip=True), 116, 150, "rear-3/4 mirrored (NW)"),
        svg_cell(use_char("walkA", "dev", "curls", "s4"), 116, 150, "walk frame A"),
        svg_cell(use_char("walkB", "dev", "curls", "s4"), 116, 150, "walk frame B"),
        svg_cell(use_char("walkA", "dev", "curls", "s4", facing="r"), 116, 150, "walk A (rear)"),
    ])

    moods_row = "".join(
        svg_cell(use_char("stand", "sm", "bob", "s1", mood=m), 108, 148, m)
        for m in ["neutral", "smile", "focus", "concern"])

    pose_cells = ""
    for i, p in enumerate(RIG):
        r, label, hair, skin = ROLES_ORDER[i % 6]
        pose_cells += svg_cell(use_char(p, r, hair, skin), 120, 150, p)

    workstation = "".join([
        svg_cell(iuse("desk"), 200, 130, "desk", vb="-100 -100 200 130"),
        svg_cell(iuse("chair"), 120, 120, "chair", vb="-60 -90 120 120"),
        svg_cell(iuse("monitor"), 130, 125, "monitor", vb="-65 -95 130 125"),
        svg_cell(iuse("laptop"), 120, 115, "laptop", vb="-60 -85 120 115"),
        svg_cell(iuse("keyboard"), 110, 80, "keyboard", vb="-55 -50 110 80"),
        svg_cell(iuse("mouse"), 70, 60, "mouse", vb="-35 -35 70 60"),
        svg_cell(iuse("desk-lamp"), 110, 110, "desk lamp", vb="-55 -80 110 110"),
        svg_cell(iuse("mug"), 70, 72, "coffee mug", vb="-35 -48 70 72"),
        svg_cell(iuse("papers"), 90, 70, "papers", vb="-45 -40 90 70"),
        svg_cell(iuse("desk-plant"), 80, 80, "desk plant", vb="-40 -55 80 80"),
        svg_cell(iuse("beacon", cls="status-build"), 70, 70, "status beacon", vb="-35 -45 70 70"),
    ])

    sprint_comps = "".join([
        svg_cell(iuse("sprint-board"), 310, 200, "sprint board (6 columns incl. Blocked)", vb="-155 -160 310 200"),
        svg_cell(iuse("story-card", cls="status-todo"), 90, 70, "story card", vb="-30 -25 90 70"),
        svg_cell(iuse("task-card-build", cls="status-build"), 80, 60, "task - build", vb="-25 -20 80 60"),
        svg_cell(iuse("task-card-test", cls="status-test"), 80, 60, "task - test", vb="-25 -20 80 60"),
        svg_cell(iuse("task-card-bug", cls="status-blocked"), 80, 60, "task - bug", vb="-25 -20 80 60"),
        svg_cell(iuse("ac-checklist"), 70, 80, "AC checklist", vb="-20 -25 70 80"),
        svg_cell(iuse("stamp-pass"), 70, 70, "PASS", vb="-22 -22 70 70"),
        svg_cell(iuse("stamp-fail"), 70, 70, "FAIL", vb="-22 -22 70 70"),
        svg_cell(iuse("evidence-folder"), 80, 70, "evidence folder", vb="-25 -25 80 70"),
        svg_cell(iuse("release-marker"), 70, 70, "release marker", vb="-22 -28 70 70"),
        svg_cell(iuse("shipped-ribbon"), 70, 70, "shipped ribbon", vb="-22 -25 70 70"),
        svg_cell(iuse("blocked-chain"), 80, 55, "blocked chain", vb="-25 -18 80 55"),
        svg_cell(iuse("risk-flame"), 60, 70, "high-risk flame", vb="-18 -22 60 70"),
    ])

    icons_row = "".join(
        f'<div class="cell"><svg width="38" height="38" viewBox="-6 -6 28 28" style="color:var(--ink)">'
        f'<use href="#icon-{n}" x="-4" y="-4" width="24" height="24"/></svg><div class="lab">{n}</div></div>'
        for n in ["check", "cross", "bug", "lock", "question", "flag", "folder", "magnifier", "pencil", "hammer"])

    collab_row = "".join([
        svg_cell(iuse("meeting-table"), 220, 130, "meeting table", vb="-110 -95 220 130"),
        svg_cell(iuse("planning-wall"), 250, 165, "planning wall", vb="-125 -135 250 165"),
        svg_cell(iuse("showcase-screen"), 210, 160, "showcase screen", vb="-105 -125 210 160"),
        svg_cell(iuse("decision-tray"), 90, 70, "PO decision tray", vb="-28 -28 90 70"),
        svg_cell(iuse("handoff-ticket", cls="status-test"), 90, 60, "hand-off ticket", vb="-32 -20 90 60"),
        svg_cell(iuse("retro-rug"), 180, 110, "retro rug (terracotta deco)", vb="-90 -55 180 110"),
        svg_cell(iuse("beanbag"), 90, 70, "beanbag", vb="-32 -34 64 52"),
    ])

    env_row = "".join([
        svg_cell(iuse("wall-x"), 300, 190, "wall (X axis)", vb="-150 -165 300 195"),
        svg_cell(iuse("doorway"), 240, 175, "doorway", vb="-120 -145 240 175"),
        svg_cell(iuse("window"), 110, 118, "window (wall)", vb="-50 -94 100 118"),
        svg_cell(iuse("stairs"), 180, 130, "stairs", vb="-90 -85 180 130"),
        svg_cell(iuse("divider"), 180, 120, "divider", vb="-90 -92 180 125"),
        svg_cell(iuse("shelf"), 180, 145, "shelving", vb="-90 -115 180 145"),
        svg_cell(iuse("plant-large"), 110, 115, "plant", vb="-50 -84 110 115"),
        svg_cell(iuse("floor-lamp"), 90, 130, "floor lamp", vb="-36 -100 90 130"),
        svg_cell(iuse("art-frame"), 84, 90, "art frame (wall)", vb="-30 -64 60 76"),
        svg_cell(iuse("wall-clock"), 62, 72, "wall clock", vb="-20 -64 40 48"),
        svg_cell(iuse("floor-2x2"), 160, 100, "floor tiles", vb="-80 -50 160 100"),
    ])

    matrix_html = md_to_html((OUT / "STATE-MATRIX.md").read_text(encoding="utf-8-sig"))
    fonts = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600'
             '&family=Fira+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">')

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sprint Office Asset Kit</title>{fonts}
<style>{theme_css()}</style></head>
<body>{all_defs()}
<button class="themetoggle">theme</button>
<div class="wrap">
<h1>Sprint Office — Asset Kit v2</h1>
<div class="sub">warm flat-isometric · 3/4 jointed rig · 4 facings · light-first · emitted by scripts/sprint_office_kit.py</div>

<div class="sec"><h2>The six roles — one 3/4 rig, garment cuts + accessories + hair carry identity</h2>
<div class="row">{roles_row}</div>
<p class="note">Names render as interface chips, never baked in. Status colours never appear on
clothing; decorative terracotta is distinct from Test/Warning orange (STYLE.md 3a/3b).</p></div>

<div class="sec"><h2>Facings &amp; walk frames — front and rear bases, mirrored to four directions</h2>
<div class="row">{facings_row}</div></div>

<div class="sec"><h2>Expressions — restrained moods on the same face</h2>
<div class="row">{moods_row}</div></div>

<div class="sec"><h2>Pose library — {len(RIG)} poses, jointed transform recipes (tween-ready)</h2>
<div class="row">{pose_cells}</div></div>

<div class="sec"><h2>Workstation components</h2><div class="row">{workstation}</div></div>

<div class="sec"><h2>Sprint components</h2><div class="row">{sprint_comps}</div>
<div class="row" style="margin-top:.6rem">{icons_row}</div></div>

<div class="sec"><h2>Collaboration components — the warm human spaces</h2><div class="row">{collab_row}</div></div>

<div class="sec"><h2>Environment components</h2><div class="row">{env_row}</div></div>

<div class="sec"><h2>Palette — warm architecture, controlled accents, semantic status</h2><div class="swatches">{sw}</div></div>

<div class="sec"><h2>Proof of coherence — small assembled scene (kit components only)</h2>
<div class="scene">{scene_svg()}</div>
<p class="note">Developer works FACING the wall (rear view — belongs in the room) · board lies in
the wall plane · SM hands a ticket to the Tester · BA reading · terracotta retro corner with
beanbag · warm architecture throughout.</p></div>

<div class="sec"><h2>State-to-visual-state matrix</h2><div class="md">{matrix_html}</div></div>
</div>
<script>{skin_js()}
{TOGGLE_JS}</script>
</body></html>"""


def proof_scene_html() -> str:
    fonts = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600'
             '&family=Fira+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">')
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sprint Office — Proof Scene</title>{fonts}
<style>{theme_css()}</style></head>
<body>{all_defs()}
<button class="themetoggle">theme</button>
<div class="wrap">
<h1>Proof of coherence — small assembled scene</h1>
<div class="sub">v2 warm world · rear-view dev at desk · in-plane board · terracotta human corner</div>
<div class="sec scene">{scene_svg()}</div>
</div>
<script>{skin_js()}
{TOGGLE_JS}</script>
</body></html>"""


# ------------------------------------------------------- motion prototype --
def motion_prototype_html() -> str:
    rig_json = json.dumps({p: {k: v for k, v in j.items() if k != "prop"} for p, j in RIG.items()})
    slots_json = json.dumps(BOARD_SLOTS)
    fonts = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600'
             '&family=Fira+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">')
    engine = """
const RIG = __RIG__;
const SLOTS = __SLOTS__;
const U = 32, SKEWM = 0.5;   // skewY slope for the board plane
const iso = (x, y, z=0) => [(x - y) * U, (x + y) * U / 2 - (z||0)];
const lerp = (a, b, t) => a + (b - a) * t;
const lerpJ = (A, B, t) => {
  const o = {};
  for (const k in A) {
    if (Array.isArray(A[k])) o[k] = [lerp(A[k][0], B[k][0], t), lerp(A[k][1], B[k][1], t)];
    else if (typeof A[k] === 'number') o[k] = lerp(A[k], B[k], t);
    else o[k] = t < 0.5 ? A[k] : B[k];
  }
  return o;
};
const svgEl = (tag, attrs={}) => {
  const e = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  return e;
};

// ---- character: drawn from joints every frame (same geometry as the kit) --
class Actor {
  constructor(scene, {role, hair, skin, hairc, x, y, facing='f', mirror=false, pose='stand'}) {
    this.scene = scene; this.role = role; this.hair = hair; this.skin = skin;
    this.x = x; this.y = y; this.facing = facing; this.mirror = mirror;
    this.mood = 'neutral'; this.carrying = null; this.gaitPhase = 0;
    this.g = svgEl('g', {class: `actor role-${role} skin-${skin}`});
    this.g.style.setProperty('--hair', hairc || '#4A4038');
    scene.addItem(this);
    this.setPose(pose);
  }
  key() { return this.x + this.y; }
  setPose(name, mood) { this.joints = {...RIG[name]}; this.poseName = name; if (mood) this.mood = mood; this.draw(); }
  setJoints(j) { this.joints = j; this.draw(); }
  wristScreen() {  // near wrist in scene coords (for ticket carry)
    const [px, py] = iso(this.x, this.y);
    const m = this.mirror ? -1 : 1;
    return [px + m * this.joints.nwr[0], py + this.joints.bob + this.joints.nwr[1]];
  }
  draw() {
    let j = this.joints; const rear = this.facing === 'r';
    if (rear && (this.poseName === 'sit' || this.poseName === 'type'))
      j = Object.assign({}, j, {nhip:[-5,-30], nkne:[-6,-24], nank:[-6.5,-4], fhip:[5,-29], fkne:[4,-23], fank:[3.5,-4]});
    const [px, py] = iso(this.x, this.y);
    const m = this.mirror ? -1 : 1;
    const P = (pt) => `${pt[0]} ${pt[1]}`;
    const limb = (a, b, c, w, col, hand) =>
      `<path d="M ${P(a)} L ${P(b)} L ${P(c)}" stroke="${col}" stroke-width="${w}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>` +
      (hand ? `<circle cx="${c[0]}" cy="${c[1]}" r="3.6" fill="${hand}"/>` : '');
    const footF = (a, far) => { const ln = far ? 9 : 13;
      return `<path d="M ${a[0]+2} ${a[1]-3} L ${a[0]+3} ${a[1]+4} Q ${a[0]+2} ${a[1]+6} ${a[0]-1} ${a[1]+6} L ${a[0]-ln} ${a[1]+5} Q ${a[0]-ln-2} ${a[1]+4} ${a[0]-ln} ${a[1]+2} L ${a[0]-2} ${a[1]-1} Z" fill="#3B352C"/>`; };
    const footR = (a, far) => { const ln = far ? 7 : 9;
      return `<path d="M ${a[0]-3} ${a[1]+4} L ${a[0]+3} ${a[1]+4} L ${a[0]+ln} ${a[1]} Q ${a[0]+ln+1} ${a[1]-2} ${a[0]+ln-2} ${a[1]-3} L ${a[0]-2} ${a[1]-1} Z" fill="#332E26"/>`; };
    const sy = j.sh_y, hy = j.hips_y;
    const torso =
      `<path d="M -14 ${sy+1} C -7 ${sy-5} 8 ${sy-5} 13 ${sy+2} L 10 ${hy-1} C 4 ${hy+3} -6 ${hy+3} -10 ${hy-1} Z" fill="var(--garment)"/>` +
      `<path d="M 3 ${sy-3} C 8 ${sy-4} 11 ${sy-1} 13 ${sy+2} L 10 ${hy-1} C 8 ${hy+1} 5 ${hy+2} 3 ${hy+2} Z" fill="var(--garment-2)" opacity="0.9"/>` +
      (rear ? `<path d="M -0.5 ${sy-2} L -0.5 ${hy+1}" stroke="var(--garment-2)" stroke-width="1.6" stroke-linecap="round"/>` : '') +
      `<path d="M -10 ${hy-2} L 9 ${hy-2} L 8 ${hy+6} Q 0 ${hy+9} -8 ${hy+6} Z" fill="var(--trouser)"/>`;
    const hx = j.head[0], hyy = j.head[1];
    const mood = MOODS[this.mood] || MOODS.neutral;
    const head = rear
      ? `<g transform="translate(${hx},${hyy})"><rect x="-4" y="8" width="8" height="9" rx="2.6" fill="var(--skin-2)"/>` +
        `<ellipse rx="12.5" ry="13.5" fill="var(--skin)"/>` +
        `<g><path d="${HAIR_B[this.hair]}" fill="var(--hair)"/>${HAIR_B_EXTRA[this.hair]||''}</g>` +
        `<g>${(ACC_HEAD[this.role]||{}).r||''}</g></g>`
      : `<g transform="translate(${hx},${hyy})"><ellipse cx="9.5" cy="1" rx="2.2" ry="2.8" fill="var(--skin-2)"/>` +
        `<rect x="-4" y="9" width="8" height="8" rx="2.6" fill="var(--skin)"/>` +
        `<ellipse rx="12.5" ry="13.5" fill="var(--skin)"/>` +
        `<path d="M 5 -12 Q 13.5 -8 12.4 3 Q 12.8 9 8 11.5 Q 12 3 10 -4 Z" fill="var(--skin-2)" opacity="0.55"/>` +
        `<g><path d="${HAIR_F[this.hair]}" fill="var(--hair)"/>${HAIR_F_EXTRA[this.hair]||''}</g>` +
        `<g>${(ACC_HEAD[this.role]||{}).f||''}</g>` +
        `<circle class="eye" cx="-6.6" cy="-1" r="1.8" fill="#2E2A25"/><circle class="eye" cx="1.8" cy="-1.4" r="1.55" fill="#2E2A25"/>` +
        `<rect class="lid" x="-9" y="-3.2" width="5" height="4.4" rx="2" fill="var(--skin)" opacity="0"/>` +
        `<rect class="lid" x="-0.6" y="-3.4" width="4.6" height="4.2" rx="2" fill="var(--skin)" opacity="0"/>` +
        `<g><g stroke="#2E2A25" stroke-opacity="0.75" stroke-width="1.3" fill="none" stroke-linecap="round"><path d="${mood.browN}"/><path d="${mood.browF}"/></g>` +
        `<path d="${mood.mouth}" stroke="#2E2A25" stroke-opacity="0.7" stroke-width="1.3" fill="none" stroke-linecap="round"/></g>` +
        `<ellipse cx="-5" cy="-7" rx="6" ry="3.2" fill="#FFFFFF" opacity="0.12"/></g>`;
    const noHands = rear && this.poseName === 'type';
    const overlay = OVERLAYS[this.role] || '', acc = rear ? '' : (ACCESSORIES[this.role] || '');
    const footN = rear ? footR(j.nank,false) : footF(j.nank,false);
    const footFar = rear ? footR(j.fank,true) : footF(j.fank,true);
    this.g.innerHTML =
      `<g transform="translate(${px},${py}) scale(${m},1) translate(0,${j.bob})">` +
      `<ellipse class="shadow" filter="url(#softblur)" cx="4" cy="2" rx="19" ry="7"/>` +
      limb(j.fsh, j.fel, j.fwr, 8, 'var(--garment-2)', noHands ? null : 'var(--skin-2)') +
      limb(j.fhip, j.fkne, j.fank, 9, 'var(--trouser-2)') + footFar +
      `<g transform="rotate(${j.lean} 0 ${hy})">${torso}${overlay}${head}${acc}</g>` +
      limb(j.nhip, j.nkne, j.nank, 9.5, 'var(--trouser)') + footN +
      limb(j.nsh, j.nel, j.nwr, 8.5, 'var(--garment)', noHands ? null : 'var(--skin)') +
      `</g>`;
    this.scene.requestSort();
  }
}

// ---- scene with painter-order layering ------------------------------------
class Scene {
  constructor(svg) {
    this.svg = svg; this.layer = svg.querySelector('#dyn');
    this.items = []; this.sortQueued = false;
  }
  addItem(actor) { this.items.push(actor); this.layer.appendChild(actor.g); }
  addStatic(key, el) { const it = {key: () => key, g: el}; this.items.push(it); this.layer.appendChild(el); return it; }
  requestSort() {
    if (this.sortQueued) return; this.sortQueued = true;
    requestAnimationFrame(() => {
      this.sortQueued = false;
      [...this.items].sort((a, b) => a.key() - b.key()).forEach(it => this.layer.appendChild(it.g));
    });
  }
}

// ---- timeline engine ------------------------------------------------------
let SPEED = 1, PAUSED = false, AMBIENT = true, ABORT = false;
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
const sleep = ms => new Promise(res => {
  const target = REDUCED ? Math.min(ms, 500) : ms;
  let acc = 0, prev = performance.now();
  const tick = now => {
    if (ABORT) return res();
    if (!PAUSED) acc += (now - prev) * SPEED;
    prev = now;
    if (acc >= target) return res();
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
});
async function tween(dur, fn) {
  if (REDUCED) { fn(1); await sleep(300); return; }
  const t0 = performance.now(); let acc = 0, prev = t0;
  return new Promise(res => {
    const tick = now => {
      if (ABORT) return res();
      if (!PAUSED) acc += (now - prev) * SPEED;
      prev = now;
      const t = Math.min(1, acc / dur);
      fn(t < 0.5 ? 2*t*t : 1 - Math.pow(-2*t+2, 2)/2);  // easeInOutQuad
      if (t >= 1) res(); else requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
}
async function poseTween(actor, toName, dur=380, mood) {
  const A = {...actor.joints}, B = RIG[toName];
  await tween(dur, t => actor.setJoints(lerpJ(A, B, t)));
  actor.setPose(toName, mood);
}
async function sitDown(a) {
  const x0 = a.x, y0 = a.y;
  await Promise.all([poseTween(a, 'sitmid', 210),
    tween(210, t => { a.x = x0 + 0.04 * t; a.y = y0 + 0.04 * t; })]);
  await poseTween(a, 'sit', 250);
}
async function standUp(a) {
  const x0 = a.x, y0 = a.y;
  await poseTween(a, 'sitmid', 210);
  await Promise.all([poseTween(a, 'stand', 250),
    tween(250, t => { a.x = x0 - 0.04 * t; a.y = y0 - 0.04 * t; })]);
}
function gaitJoints(phase) {  // continuous walk cycle between A and B
  const t = (Math.sin(phase * Math.PI * 2) + 1) / 2;
  return lerpJ(RIG.walkA, RIG.walkB, t);
}
async function walkTo(actor, waypoints, speed=2.1) { // world units per second
  for (const [tx, ty] of waypoints) {
    const dx = tx - actor.x, dy = ty - actor.y;
    const dist = Math.hypot(dx, dy);
    if (dist < 0.01) continue;
    // facing from screen direction: toward viewer => front; away => rear
    const sdx = (dx - dy), sdy = (dx + dy);
    actor.facing = sdy >= 0 ? 'f' : 'r';
    actor.mirror = actor.facing === 'f' ? (sdx > 0) : (sdx < 0);
    const dur = dist / speed * 1000;
    const x0 = actor.x, y0 = actor.y;
    await tween(dur, t => {
      actor.x = x0 + dx * t; actor.y = y0 + dy * t;
      actor.gaitPhase += 0.016 * SPEED * 2.2;
      actor.setJoints(gaitJoints(actor.gaitPhase));
      if (actor.carrying) positionTicket(actor.carrying, actor);
    });
    actor.setPose('stand');
    if (actor.carrying) positionTicket(actor.carrying, actor);
  }
}
function face(actor, dirX, dirY) { // turn to face a world direction
  const sdx = (dirX - dirY), sdy = (dirX + dirY);
  actor.facing = sdy >= 0 ? 'f' : 'r';
  actor.mirror = actor.facing === 'f' ? (sdx > 0) : (sdx < 0);
  actor.draw();
}

// ---- board & tickets ------------------------------------------------------
const BOARD_AT = {x: 5.4, y: 0.14, scale: 0.6};
function boardLocalToScene(lx, ly) {
  const [bx, by] = iso(BOARD_AT.x, BOARD_AT.y);
  const s = BOARD_AT.scale;
  return [bx + s * lx, by - 4 * s + s * (ly + SKEWM * lx)];
}
function makeBoardCard(colKey, slot, status) {
  const g = svgEl('g', {class: `bcard status-${status}`});
  g.innerHTML = `<rect x="-14" y="-6" width="29" height="12" rx="2" fill="var(--paper2)" stroke="var(--card-edge)"/>` +
                `<rect x="-14" y="-6" width="2.5" height="12" rx="1.2" fill="var(--status)"/>`;
  boardCardsG.appendChild(g);
  setCardSlot(g, colKey, slot);
  return g;
}
function setCardSlot(g, colKey, slot) {
  const [lx, ly] = SLOTS[colKey][slot];
  g.dataset.col = colKey; g.dataset.slot = slot;
  g.setAttribute('transform', `translate(${lx},${ly})`);
}
async function moveCardOnBoard(g, toCol, slot, dur=650) {
  const [ax, ay] = SLOTS[g.dataset.col][+g.dataset.slot];
  const [bx, by] = SLOTS[toCol][slot];
  await tween(dur, t => g.setAttribute('transform', `translate(${lerp(ax,bx,t)},${lerp(ay,by,t)})`));
  setCardSlot(g, toCol, slot);
}
function positionTicket(t, actor) {
  const [wx, wy] = actor.wristScreen();
  t.el.setAttribute('transform', `translate(${wx},${wy})`);
  t.key = actor.x + actor.y + 0.01;
  scene.requestSort();
}

// ---- ambient layer --------------------------------------------------------
function ambientLoop() {
  let last = 0;
  const blinkT = new Map();
  const step = now => {
    if (AMBIENT && !REDUCED && !PAUSED) {
      for (const a of actors) {
        // breathing: subtle bust scale via bob wobble (visual only)
        if (a.poseName === 'type') {
          a.gaitPhase += 0.02;
          const j = {...a.joints};
          const w = Math.sin(now / 140) * 1.1;
          j.nwr = [a.joints.nwr[0], a.joints.nwr[1] + w];
          j.fwr = [a.joints.fwr[0], a.joints.fwr[1] - w];
          a.setJoints(j);
        }
        if (a.facing === 'f') {
          if (!blinkT.has(a)) blinkT.set(a, now + 1800 + Math.random() * 3500);
          if (now > blinkT.get(a)) {
            a.g.querySelectorAll('.lid').forEach(l => l.setAttribute('opacity', '1'));
            setTimeout(() => a.g.querySelectorAll('.lid').forEach(l => l.setAttribute('opacity', '0')), 130);
            blinkT.set(a, now + 2200 + Math.random() * 4200);
          }
        }
      }
      document.querySelectorAll('.steam').forEach(p => {
        p.setAttribute('stroke-dashoffset', String(-(now / 90) % 24));
      });
      document.querySelectorAll('.mon-ui path').forEach(p => {
        p.setAttribute('stroke-opacity', String(0.75 + 0.25 * Math.sin(now / 900)));
      });
    }
    requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

// ---- the demanded sequence ------------------------------------------------
const cap = t => { document.getElementById('caption').textContent = t; };
let runSeq = 0;
async function sequence(my) {
  const G = () => { if (my !== runSeq || ABORT) throw 'stale'; };
  // reset world
  dev.x = DEV_SEAT.x; dev.y = DEV_SEAT.y; dev.facing = 'r'; dev.mirror = false; dev.setPose('type');
  tess.x = TESS_SEAT.x; tess.y = TESS_SEAT.y; tess.facing = 'r'; tess.mirror = false; tess.setPose('sit');
  cardA.style.display = ''; setCardSlot(cardA, 'build', 0);
  cardA.querySelector('rect:nth-child(2)').setAttribute('fill', 'var(--status)');
  cardA.setAttribute('class', 'bcard status-build');
  ticket.el.style.display = 'none';
  cap('Ambient: the Developer is building (typing); the Tester reads at her desk. Nothing moves cards.');
  G(); await sleep(2600);

  cap('Workflow: build done — the Developer stands and walks to the board.');
  G(); await standUp(dev); face(dev, 0, 1);
  G(); await walkTo(dev, [[DEV_SEAT.x, 2.6], [4.6, 2.6], [BOARD_AT.x - 0.5, 1.35]]);
  face(dev, 0.5, -1); // face the board (rear, toward the wall)
  G(); await sleep(300);

  cap('The Developer moves the story card from Build into Test.');
  ticket.el.style.display = ''; ticket.el.setAttribute('class', 'ticket status-build');
  cardA.style.display = 'none';
  dev.facing='r'; dev.mirror=false; G(); await poseTween(dev, 'carry', 300);
  dev.carrying = ticket; positionTicket(ticket, dev);
  G(); await walkTo(dev, [[BOARD_AT.x + 0.35, 1.35]], 1.4);
  G(); await sleep(250);
  dev.carrying = null; ticket.el.style.display = 'none';
  cardA.setAttribute('class', 'bcard status-test');
  cardA.style.display = ''; setCardSlot(cardA, 'build', 0);
  G(); await moveCardOnBoard(cardA, 'test', 0);
  G(); await poseTween(dev, 'stand', 300);
  G(); await sleep(400);

  cap('Hand-off: the Developer brings the work to the Tester — verification is independent.');
  ticket.el.style.display = ''; ticket.el.setAttribute('class', 'ticket status-test');
  G(); await poseTween(dev, 'carry', 300); dev.carrying = ticket; positionTicket(ticket, dev);
  G(); await walkTo(dev, [[4.4, 3.4]]);
  face(dev, 1, 0.2); G(); await poseTween(dev, 'handoff', 380); positionTicket(ticket, dev);
  dev.carrying = null;
  G(); await standUp(tess); face(tess, -1, -1);
  G(); await walkTo(tess, [[5.15, 3.9]]);
  face(tess, -1, 0); tess.mirror = false; G(); await poseTween(tess, 'handoff', 350);
  tess.carrying = ticket; positionTicket(ticket, tess);
  G(); await sleep(500);
  G(); await poseTween(dev, 'stand', 300);
  cap('The Tester takes the ticket to her desk and reviews it (blind, evidence-first).');
  G(); await poseTween(tess, 'carry', 300);
  G(); await walkTo(tess, [[TESS_SEAT.x, TESS_SEAT.y]]);
  tess.carrying = null; ticket.el.style.display = 'none';
  face(tess, 1, -1); G(); await poseTween(tess, 'sit', 380); G(); await poseTween(tess, 'type', 300, 'focus');
  // dev returns
  walkTo(dev, [[4.0, 2.6], [DEV_SEAT.x, 2.6], [DEV_SEAT.x, DEV_SEAT.y]]).then(async () => {
    face(dev, 0, -1); G(); await sitDown(dev); G(); await poseTween(dev, 'type', 280);
  });
  G(); await sleep(2300);

  cap('PASS — the Tester walks the card into Done. Only her PASS does this.');
  G(); await standUp(tess);
  G(); await walkTo(tess, [[5.9, 2.4], [BOARD_AT.x + 0.55, 1.35]]);
  face(tess, 1, -1); tess.facing='r'; tess.mirror=false;
  G(); await moveCardOnBoard(cardA, 'done', 0);
  cardA.setAttribute('class', 'bcard status-done');
  face(tess, 0, 1); G(); await poseTween(tess, 'celebrate', 420, 'smile');
  G(); await sleep(900);
  G(); await poseTween(tess, 'stand', 350, 'neutral');
  G(); await sleep(500);

  cap('Scenario B (FAIL): a second story is already in Test — the review finds defects.');
  cardB.style.display = ''; setCardSlot(cardB, 'test', 1);
  G(); await walkTo(tess, [[TESS_SEAT.x, TESS_SEAT.y]]);
  face(tess, 0.5, -1); G(); await sitDown(tess); G(); await poseTween(tess, 'type', 300, 'focus');
  G(); await sleep(1400);
  cap('FAIL — the Tester carries the defect evidence to the Developer. The work bounces WITH proof.');
  tess.mood='concern'; G(); await standUp(tess);
  G(); await walkTo(tess, [[3.2, 3.2], [DEV_SEAT.x + 0.9, DEV_SEAT.y + 0.15]]);
  face(tess, -1, 0); G(); await poseTween(tess, 'review', 380, 'concern');
  dev.mood='concern'; dev.draw(); G(); await sleep(200);
  G(); await sleep(900);
  cap('The card returns from Test to Build — rework with the evidence attached.');
  poseTween(dev, 'type', 320, 'focus');
  G(); await standUp(tess);
  G(); await walkTo(tess, [[4.6, 2.5], [BOARD_AT.x + 0.35, 1.35]]);
  tess.facing='r'; tess.mirror=false; tess.draw();
  G(); await moveCardOnBoard(cardB, 'build', 1);
  cardB.setAttribute('class', 'bcard status-build');
  G(); await sleep(400);
  cap('The Tester returns to her desk. Sequence complete — press Replay to watch again.');
  G(); await walkTo(tess, [[TESS_SEAT.x, TESS_SEAT.y]]);
  face(tess, 0.5, -1); tess.mood='neutral'; G(); await sitDown(tess);
  cardB.style.display = 'none';
}

// ---- boot -----------------------------------------------------------------
const svg = document.getElementById('stage');
const scene = new Scene(svg);
const boardCardsG = document.querySelector('#sprint-board-live .board-cards');
const DEV_SEAT = {x: 1.76, y: 1.75}, TESS_SEAT = {x: 6.12, y: 3.63};
const dev = new Actor(scene, {role: 'dev', hair: 'curls', skin: 's4', hairc: '#332F36', x: DEV_SEAT.x, y: DEV_SEAT.y, facing: 'r', pose: 'type'});
const tess = new Actor(scene, {role: 'tester', hair: 'short', skin: 's1', hairc: '#5D4632', x: TESS_SEAT.x, y: TESS_SEAT.y, facing: 'r', pose: 'sit'});
const actors = [dev, tess];
const cardA = makeBoardCard('build', 0, 'build');
const cardB = makeBoardCard('test', 1, 'test'); cardB.style.display = 'none';
const ticket = (() => {
  const g = svgEl('g', {class: 'ticket status-test'});
  g.innerHTML = `<rect x="-9" y="-6" width="19" height="13" rx="2.5" fill="var(--paper2)" stroke="var(--card-edge)"/>` +
                `<rect x="-9" y="-6" width="4" height="13" rx="2" fill="var(--status)"/>`;
  g.style.display = 'none';
  const t = { el: g, key: 99 };
  scene.items.push({key: () => t.key, g}); scene.layer.appendChild(g);
  return t;
})();
ambientLoop();

let currentRun = Promise.resolve();
async function run() {
  ABORT = true;              // any in-flight awaits resolve immediately
  await currentRun;          // old sequence fully unwinds (throws 'stale')
  ABORT = false;
  const my = ++runSeq;
  currentRun = sequence(my).catch(e => { if (e !== 'stale') throw e; });
  await currentRun;
}
document.getElementById('replay').onclick = run;
document.getElementById('pause').onclick = e => { PAUSED = !PAUSED; e.target.textContent = PAUSED ? 'Resume' : 'Pause'; };
document.getElementById('speed').onclick = e => { SPEED = SPEED === 1 ? 0.5 : (SPEED === 0.5 ? 2 : 1); e.target.textContent = SPEED + 'x'; };
document.getElementById('ambient').onclick = e => { AMBIENT = !AMBIENT; e.target.textContent = 'Ambient: ' + (AMBIENT ? 'on' : 'off'); };
if (REDUCED) cap('Reduced motion is on: the sequence renders as stepped keyframes.');
run();
"""
    engine = engine.replace("__RIG__", rig_json).replace("__SLOTS__", slots_json)

    # world for the prototype
    W, D = 8.5, 6
    floor = "".join(
        f'<polygon points="{pts([iso(x, y, 0), iso(x + 1, y, 0), iso(x + 1, y + 1, 0), iso(x, y + 1, 0)])}" '
        f'fill="{(FLOOR_A if (x + y) % 2 == 0 else FLOOR_B)[0]}"/>'
        for x in range(0, 8) for y in range(0, 6))
    walls = iso_box(0, -0.16, 8, 0.16, 110, WALL) + iso_box(-0.16, 0, 0.16, 6, 110, WALL_S)
    rim = iso_box(0, 5.94, 8, 0.06, 3, FLOOR_B) + iso_box(7.94, 0, 0.06, 6, 3, FLOOR_B)
    w1 = iso(0.75, 0)
    statics = []

    def puts(wx, wy, inner, key=None):
        px, py = iso(wx, wy)
        statics.append((key if key is not None else wx + wy,
                        f'<g transform="translate({px:.1f},{py:.1f})">{inner}</g>'))
    puts(1.7, 0.75, iuse("desk"), key=0.9)
    puts(1.35, 0.62, iuse("monitor", "translate(0,-41)"), key=1.0)
    puts(2.0, 0.9, iuse("keyboard", "translate(0,-41)"), key=1.05)
    puts(2.5, 0.6, iuse("mug", "translate(0,-41)"), key=1.06)
    puts(1.05, 0.95, iuse("beacon", "translate(0,-41)", cls="status-build"), key=1.07)
    puts(1.80, 1.79, iuse("chair"), key=3.36)
    puts(6.1, 2.9, iuse("desk"), key=8.9)
    puts(5.8, 2.78, iuse("laptop", "translate(0,-41)"), key=9.0)
    puts(6.16, 3.67, iuse("chair"), key=9.62)
    puts(0.6, 4.6, iuse("plant-large"), key=5.3)
    puts(1.6, 4.75, iuse("retro-rug"), key=5.5)
    puts(1.2, 5.0, iuse("beanbag"), key=6.4)
    board_px, board_py = iso(5.4, 0.14)
    statics.append((1.1, f'<g transform="translate({board_px:.1f},{board_py:.1f})">'
                         f'{iuse("sprint-board-live", "scale(0.6)")}</g>'))
    statics.sort(key=lambda t: t[0])
    static_svg = "".join(s for _, s in statics)
    wallart = f'<g transform="translate({w1[0]:.0f},{w1[1]:.0f})">{iuse("window")}</g>'

    fonts = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600'
             '&family=Fira+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">')
    controls_css = (
        ".controls{display:flex;gap:.5rem;align-items:center;margin:.6rem 0 .2rem;flex-wrap:wrap}"
        ".controls button{font-size:.78rem;padding:.35rem .85rem;border-radius:999px;cursor:pointer;"
        "border:1px solid var(--panel-border);background:var(--panel);color:var(--ink);font-weight:600}"
        ".controls button:hover{background:var(--badge-chip)}"
        "#caption{font-size:.85rem;color:var(--ink);background:var(--badge-chip);border-radius:10px;"
        "padding:.5rem .8rem;min-height:2.2em;max-width:900px}"
        ".legendline{font-size:.7rem;color:var(--dim);margin-top:.4rem}")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sprint Office — Motion Prototype</title>{fonts}
<style>{theme_css()}{controls_css}</style></head>
<body>{all_defs()}
<button class="themetoggle">theme</button>
<div class="wrap">
<h1>Sprint Office — Motion Prototype</h1>
<div class="sub">real walk cycle · joint tweens (never crossfade) · facing changes · board interaction · ambient vs workflow layers</div>
<div class="controls">
  <button id="replay">Replay</button>
  <button id="pause">Pause</button>
  <button id="speed">1x</button>
  <button id="ambient">Ambient: on</button>
  <div id="caption">Loading…</div>
</div>
<div class="sec scene">
<svg id="stage" width="1000" height="742" viewBox="-228 -172 532 395">
<defs>{SOFTBLUR}</defs>
{floor}{walls}{wallart}<g id="dyn">{static_svg}</g>{rim}
</svg>
</div>
<div class="legendline">Ambient layer (breathing hands, blinks, steam, monitor shimmer) never moves cards.
Workflow motion mirrors real sprint events: build→test, hand-off, blind review, PASS→Done, FAIL→evidence back→card returns to Build.</div>
</div>
<script>{skin_js()}
{TOGGLE_JS}
{engine}</script>
</body></html>"""




# ------------------------------------------------------------- full office --
# the wall board's seven columns, in sprint_board.COLUMNS order; STATUS keys
# supply the header colour ("backlog" reuses the neutral todo grey)
WALL_COLS = ["backlog", "todo", "design", "build", "test", "blocked", "done"]
WALL_COL_NAMES = ["Backlog", "To-Do", "Design", "Build", "Test", "Blocked", "Done"]
WALL_X0, WALL_STEP, WALL_W = -119, 34, 30
if WALL_COL_NAMES != list(BOARD_COLUMNS):     # fail loudly, never render a
    raise SystemExit(                          # board that hides a story
        f"office/board column drift: office {WALL_COL_NAMES} != board "
        f"{list(BOARD_COLUMNS)} — a story in a missing column would vanish")

OFFICE_CREW = [
    ("po",     "Product Owner", "swept", "s2", "#5D4632"),
    ("sm",     "Maya",          "bob",   "s1", "#332F36"),
    ("ba",     "Oliver",        "crop",  "s3", "#2F2B33"),
    ("techba", "Priya",         "bun",   "s2", "#332F36"),
    ("dev",    "Marcus",        "curls", "s4", "#332F36"),
    ("tester", "Elena",         "short", "s1", "#5D4632"),
]


def board_with(extra_cards: str) -> str:
    """The wall board rendered with LIVE cards laid into its column slots.

    Seven columns, matching sprint_board.COLUMNS exactly — the office and the
    board must never disagree about where a story is.
    """
    cols = ""
    for i, c in enumerate(WALL_COLS):
        x = WALL_X0 + i * WALL_STEP
        cols += (f'<rect x="{x}" y="-78" width="{WALL_W}" height="66" rx="2.5" fill="{PANEL}" '
                 f'stroke="{CARD_EDGE}" stroke-width="0.8"/>'
                 f'<rect x="{x}" y="-78" width="{WALL_W}" height="5" rx="2.5" fill="{STATUS[c]}"/>')
    return (shadow(-1.8, -0.14, 3.6, 0.28)
            + iso_box(-1.8, -0.1, 3.6, 0.2, 6, DESK_LEG)
            + f'<g transform="translate(0,-4) {SKEW}">'
              f'<rect x="-124" y="-86" width="248" height="80" rx="4" fill="{BOARD_BG}" '
              f'stroke="{CARD_EDGE}" stroke-width="1.2"/>{cols}{extra_cards}</g>')


def office_html(state: dict | None = None) -> str:
    # Build the symbol libraries FIRST: they populate SYM_VB, which every
    # iuse() below reads for identity sizing. Rendering used to work only
    # because the kit emission happened to run first.
    defs_html = all_defs()
    W, D = 14, 10
    floor = "".join(
        f'<polygon points="{pts([iso(x, y, 0), iso(x + 1, y, 0), iso(x + 1, y + 1, 0), iso(x, y + 1, 0)])}" '
        f'fill="{(FLOOR_A if (x + y) % 2 == 0 else FLOOR_B)[0]}"/>'
        for x in range(0, W) for y in range(0, D))
    walls = (iso_box(0, -0.16, 11.85, 0.16, 110, WALL)
             + iso_box(-0.16, 0, 0.16, D, 110, WALL_S))
    rim = iso_box(0, D - 0.06, W, 0.06, 3, FLOOR_B) + iso_box(W - 0.06, 0, 0.06, D, 3, FLOOR_B)

    statics = []

    def puts(wx, wy, inner, key=None):
        px, py = iso(wx, wy)
        statics.append((key if key is not None else wx + wy,
                        f'<g transform="translate({px:.1f},{py:.1f})">{inner}</g>'))

    def put_slot(role, key):
        statics.append((key, f'<g class="actor-slot" data-slot="{role}"></g>'))

    puts(1.5, 0, iuse("window", "scale(1.2)"), key=0.2)
    puts(3.1, 0, iuse("art-frame", "scale(1.15)"), key=0.21)
    puts(4.7, 0.12, f'<g data-hs="sprint">{iuse("planning-wall", "scale(0.68)")}</g>', key=0.3)
    puts(6.9, 0, iuse("wall-clock"), key=0.22)
    board_cards = ""
    if state:
        col_x = {name: WALL_X0 + i * WALL_STEP
                 for i, name in enumerate(WALL_COL_NAMES)}
        for col, items in (state.get("columns") or {}).items():
            if col not in col_x:      # must not happen: WALL_COL_NAMES mirrors
                continue              # sprint_board.COLUMNS exactly
            for i, card in enumerate(items[:3]):
                cx, cy = col_x[col] + 3, -68 + i * 16
                stc = STATUS.get(card.get("status"), STATUS["todo"])
                ribbon = (f'<rect x="{cx + 19}" y="{cy}" width="4" height="12" rx="1.5" '
                          f'fill="{GOLD}"/>') if card.get("shipped") else ""
                board_cards += (
                    f'<rect x="{cx}" y="{cy}" width="24" height="12" rx="2" '
                    f'fill="var(--paper2)" stroke="{CARD_EDGE}" stroke-width="1"/>'
                    f'<rect x="{cx}" y="{cy}" width="2.5" height="12" rx="1.2" fill="{stc}"/>'
                    f'{ribbon}')
            if len(items) > 3:
                board_cards += (
                    f'<text x="{col_x[col] + 15}" y="-15" text-anchor="middle" '
                    f'font-size="8" font-family="Fira Code" fill="var(--dim)">'
                    f'+{len(items) - 3}</text>')
    puts(9.15, 0.14,
         '<g data-hs="board">'
         + (iuse("sprint-board", "scale(0.68)") if not board_cards
            else f'<g transform="scale(0.68)">{board_with(board_cards)}</g>')
         + '</g>', key=0.31)
    puts(12.95, 0, iuse("doorway"), key=0.25)
    puts(12.6, 2.2, f'<g data-hs="backlog">{iuse("shelf")}</g>', key=14.8)
    puts(12.72, 2.14, iuse("release-marker", "translate(0,-66)"), key=14.9)

    puts(3.15, 1.55, iuse("divider-y", "scale(1.15)"), key=4.3)
    puts(1.65, 1.55, iuse("retro-rug", "scale(0.72)"), key=2.2)
    puts(1.5, 0.62, iuse("chair"), key=1.34)
    put_slot("po", key=1.6)
    puts(1.48, 1.35, iuse("desk"), key=2.83)
    # the laptop sits directly in front of the PO's seat (it lived at the far
    # end of the desk, rotated away from him — PO review 2026-08-22)
    puts(1.55, 1.42, iuse("laptop", "translate(0,-41)"), key=2.9)
    puts(1.0, 1.3, iuse("decision-tray", "translate(0,-45)"), key=2.95)
    puts(2.45, 0.95, iuse("desk-lamp", "translate(0,-41) scale(0.75)"), key=2.96)

    def workstation(dx, dy, beacon_status, screen="monitor", extras=(), role=None):
        puts(dx, dy, iuse("desk"), key=dx + dy)
        if screen == "monitor":
            puts(dx - 0.55, dy + 0.05, iuse("monitor", "translate(0,-41)"), key=dx + dy + 0.05)
            puts(dx + 0.12, dy + 0.12, iuse("keyboard", "translate(0,-41)"), key=dx + dy + 0.06)
        else:
            puts(dx - 0.45, dy + 0.05, iuse("laptop", "translate(0,-41)"), key=dx + dy + 0.05)
        puts(dx - 0.65, dy + 0.2, iuse("beacon", "translate(0,-41)", cls=f"status-{beacon_status}"),
             key=dx + dy + 0.07)
        for ex, (exx, exy) in extras:
            puts(dx + exx, dy + exy, iuse(ex, "translate(0,-41)"), key=dx + dy + 0.08)
        # crew sits NORTH of the desk facing the viewer; chair behind, desk in
        # front (desk occludes the lap = seated read); screens offset sideways
        puts(dx + 0.02, dy - 0.72, iuse("chair"), key=dx + dy - 0.78)
        if role:
            put_slot(role, key=dx + dy - 0.55)

    def beacon_of(role_key, fallback):
        r = (state or {}).get("roles", {}).get(role_key)
        if not r:
            return fallback
        return r.get("beacon") or "todo"

    workstation(5.0, 2.35, beacon_of("dev", "build"), extras=[("mug", (0.75, -0.15))], role="dev")
    workstation(7.6, 2.35, beacon_of("techba", "design"), extras=[("desk-plant", (0.78, -0.18))], role="techba")
    workstation(5.0, 4.75, beacon_of("sm", "todo"), screen="laptop", extras=[("mug", (0.6, -0.18))], role="sm")
    workstation(7.6, 4.75, beacon_of("ba", "todo"), screen="laptop", extras=[("papers", (0.5, 0.14))], role="ba")
    workstation(10.4, 4.1, beacon_of("tester", "test"), extras=[("evidence-folder", (0.55, -0.16))], role="tester")

    # explicit paint keys: north chairs behind the table, south chairs in
    # front, so no seat slab ever penetrates the tabletop plane
    puts(10.35, 6.35, iuse("chair"), key=16.0)
    puts(12.2, 6.35, iuse("chair"), key=16.05)
    puts(11.3, 7.0, iuse("meeting-table"), key=18.3)
    puts(10.35, 7.65, iuse("chair"), key=18.6)
    puts(12.2, 7.65, iuse("chair"), key=18.65)
    puts(13.15, 5.5, f'<g data-hs="ask">{iuse("showcase-screen", "scale(0.9)")}</g>', key=17.6)

    puts(2.2, 8.0, iuse("retro-rug"), key=9.4)
    puts(1.55, 8.35, iuse("beanbag"), key=10.1)
    puts(2.85, 8.6, iuse("beanbag"), key=11.6)
    puts(4.2, 9.3, iuse("floor-lamp"))
    puts(0.7, 7.0, iuse("plant-large"), key=7.9)
    puts(13.5, 2.9, iuse("plant-large"))

    statics.sort(key=lambda s: s[0])
    static_svg = "".join(s for _, s in statics)

    # hotspots are placed at runtime from the painted objects' own bounding
    # boxes (data-hs markers) — fixed rects drifted off their targets and
    # overlapped each other (fresh-eyes review 2026-08-22)
    seats = {"po": (1.53, 0.78, 1.48, 1.35), "dev": (5.05, 1.82, 5.0, 2.35),
             "techba": (7.65, 1.82, 7.6, 2.35), "sm": (5.05, 4.22, 5.0, 4.75),
             "ba": (7.65, 4.22, 7.6, 4.75), "tester": (10.45, 3.57, 10.4, 4.1)}
    state_json = json.dumps(state or {})
    live_roles = (state or {}).get("roles", {})

    def av(role_key, field, fallback):
        """The character this role wears: whatever the project's crew file
        chose, else the built-in preset."""
        chosen = (live_roles.get(role_key) or {}).get("avatar") or {}
        return chosen.get(field) or fallback

    crew_js = json.dumps([
        {"role": r, "label": (live_roles.get(r, {}).get("name") or lbl),
         "hair": av(r, "hair", h), "skin": av(r, "skin", s),
         "hairc": av(r, "hair_colour", hc),
         "x": seats[r][0], "y": seats[r][1], "dx": seats[r][2], "dy": seats[r][3],
         "live": live_roles.get(r, {})}
        for r, lbl, h, s, hc in OFFICE_CREW])

    type_js = json.dumps({k: v for k, v in RIG['type'].items() if k != 'prop'})
    office_engine = """
const RIG = { type: __TYPE__ };
// typing hands sit at keyboard height, not chin height (review 2026-08-22)
RIG.type.nwr = [RIG.type.nwr[0] - 1, RIG.type.nwr[1] + 6];
RIG.type.fwr = [RIG.type.fwr[0] + 1, RIG.type.fwr[1] + 6];
// accessories/overlays are authored in STAND body coords; seated torsos sit
// lower, so decorations must drop with them or they land on faces
const DECO_DY = RIG.type.sh_y + 74;
const CREW = __CREW__;
const U = 32;
const iso = (x, y, z=0) => [(x - y) * U, (x + y) * U / 2 - (z||0)];
const svgEl = (tag, attrs={}) => {
  const e = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  return e;
};
let AMBIENT = true;
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;

class Actor {
  constructor(layer, {role, hair, skin, hairc, x, y}) {
    this.role = role; this.hair = hair; this.skin = skin;
    this.x = x; this.y = y; this.poseName = 'type';
    this.g = svgEl('g', {class: `actor role-${role} skin-${skin}`});
    this.g.style.setProperty('--hair', hairc || '#4A4038');
    layer.appendChild(this.g);
    this.joints = JSON.parse(JSON.stringify(RIG.type));
    this.draw();
  }
  draw() {
    const j = Object.assign({}, this.joints,
      {nkne: [-11, -26], nank: [-10, -4], fkne: [-2, -25], fank: [-1, -4]});
    const [px, py] = iso(this.x, this.y);
    const P = pt => `${pt[0]} ${pt[1]}`;
    const limb = (a, b, c, w, col, hand) =>
      `<path d="M ${P(a)} L ${P(b)} L ${P(c)}" stroke="${col}" stroke-width="${w}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>` +
      (hand ? `<circle cx="${c[0]}" cy="${c[1]}" r="3.6" fill="${hand}"/>` : '');
    const footF = (a, far) => { const ln = far ? 9 : 13;
      return `<path d="M ${a[0]+2} ${a[1]-3} L ${a[0]+3} ${a[1]+4} Q ${a[0]+2} ${a[1]+6} ${a[0]-1} ${a[1]+6} L ${a[0]-ln} ${a[1]+5} Q ${a[0]-ln-2} ${a[1]+4} ${a[0]-ln} ${a[1]+2} L ${a[0]-2} ${a[1]-1} Z" fill="#3B352C"/>`; };
    const sy = j.sh_y, hy = j.hips_y;
    const torso =
      `<path d="M -14 ${sy+1} C -7 ${sy-5} 8 ${sy-5} 13 ${sy+2} L 10 ${hy-1} C 4 ${hy+3} -6 ${hy+3} -10 ${hy-1} Z" fill="var(--garment)"/>` +
      `<path d="M 3 ${sy-3} C 8 ${sy-4} 11 ${sy-1} 13 ${sy+2} L 10 ${hy-1} C 8 ${hy+1} 5 ${hy+2} 3 ${hy+2} Z" fill="var(--garment-2)" opacity="0.9"/>` +
      `<path d="M -10 ${hy-2} L 9 ${hy-2} L 8 ${hy+6} Q 0 ${hy+9} -8 ${hy+6} Z" fill="var(--trouser)"/>`;
    const hx = j.head[0], hyy = j.head[1];
    const mood = MOODS.focus;
    const head =
      `<g transform="translate(${hx},${hyy})"><ellipse cx="9.5" cy="1" rx="2.2" ry="2.8" fill="var(--skin-2)"/>` +
      `<rect x="-4" y="9" width="8" height="8" rx="2.6" fill="var(--skin)"/>` +
      `<ellipse rx="12.5" ry="13.5" fill="var(--skin)"/>` +
      `<path d="M 5 -12 Q 13.5 -8 12.4 3 Q 12.8 9 8 11.5 Q 12 3 10 -4 Z" fill="var(--skin-2)" opacity="0.55"/>` +
      `<g><path d="${HAIR_F[this.hair]}" fill="var(--hair)"/>${HAIR_F_EXTRA[this.hair]||''}</g>` +
      `<g>${(ACC_HEAD[this.role]||{}).f||''}</g>` +
      `<circle cx="-6.6" cy="-1" r="1.8" fill="#2E2A25"/><circle cx="1.8" cy="-1.4" r="1.55" fill="#2E2A25"/>` +
      `<rect class="lid" x="-9" y="-3.2" width="5" height="4.4" rx="2" fill="var(--skin)" opacity="0"/>` +
      `<rect class="lid" x="-0.6" y="-3.4" width="4.6" height="4.2" rx="2" fill="var(--skin)" opacity="0"/>` +
      `<g stroke="#2E2A25" stroke-opacity="0.75" stroke-width="1.3" fill="none" stroke-linecap="round"><path d="${mood.browN}"/><path d="${mood.browF}"/></g>` +
      `<path d="${mood.mouth}" stroke="#2E2A25" stroke-opacity="0.7" stroke-width="1.3" fill="none" stroke-linecap="round"/>` +
      `<ellipse cx="-5" cy="-7" rx="6" ry="3.2" fill="#FFFFFF" opacity="0.12"/></g>`;
    this.g.innerHTML =
      `<g transform="translate(${px},${py})">` +
      `<ellipse class="shadow" filter="url(#softblur)" cx="4" cy="2" rx="19" ry="7"/>` +
      limb(j.fsh, j.fel, j.fwr, 8, 'var(--garment-2)', 'var(--skin-2)') +
      limb(j.fhip, j.fkne, j.fank, 9, 'var(--trouser-2)') +
      `<g class="bust">${torso}` +
      `<g transform="translate(0,${DECO_DY})">${OVERLAYS[this.role]||''}</g>${head}` +
      `<g transform="translate(0,${DECO_DY})">${ACCESSORIES[this.role]||''}</g></g>` +
      limb(j.nhip, j.nkne, j.nank, 9.5, 'var(--trouser)') +
      // no foot wedges: desks hide seated feet, and detached shoes were
      // rendering beside the desks (fresh-eyes review 2026-08-22)
      limb(j.nsh, j.nel, j.nwr, 8.5, 'var(--garment)', 'var(--skin)') +
      `</g>`;
  }
}

const slotFor = r => document.querySelector('.actor-slot[data-slot=' + JSON.stringify(r) + ']') || document.getElementById('actors');
const chipLayer = document.getElementById('chips');
document.querySelectorAll('.actor-slot').forEach(s => { s.innerHTML = ''; });
const actors = CREW.map(c => new Actor(slotFor(c.role), c));
CREW.forEach(c => {
  const [px, py] = iso(c.x, c.y);
  const g = svgEl('g', {class: 'namechip', transform: `translate(${px},${py - 26})`});
  const L = c.live || {};
  const sub = L.story ? `${L.story} · ${L.status}` : (L.idle ? 'idle' : '');
  const w = c.label.length * 5.8 + 12;
  const subW = sub.length * 5.4 + 12;
  g.innerHTML = `<rect x="${-w/2}" y="-9" width="${w}" height="18" rx="9" fill="var(--panel)" stroke="var(--card-edge)"/>` +
                `<text text-anchor="middle" dominant-baseline="central" font-size="9" ` +
                `font-family="Fira Sans" font-weight="600" fill="var(--ink)">${c.label}</text>` +
                (sub ? `<rect x="${-subW/2}" y="10.5" width="${subW}" height="13" rx="6.5" ` +
                       `fill="var(--panel)" stroke="var(--card-edge)" stroke-width="0.8"/>` +
                       `<text text-anchor="middle" y="20" font-size="8" font-family="Fira Code" ` +
                       `fill="var(--ink)" opacity="0.8">${sub}</text>` : '');
  if (L.idle) g.setAttribute('opacity', '0.8');
  // chips live INSIDE their actor's painter-ordered slot, so a chip can
  // never paint over the crew member seated in the row behind it
  const slot = slotFor(c.role);
  (slot.classList && slot.classList.contains('actor-slot') ? slot : chipLayer).appendChild(g);
});

function ambient() {
  const blinkT = new Map();
  const step = now => {
    if (AMBIENT && !REDUCED) {
      actors.forEach(a => {
        if (!blinkT.has(a)) blinkT.set(a, now + 1500 + Math.random() * 4000);
        if (now > blinkT.get(a)) {
          a.g.querySelectorAll('.lid').forEach(l => l.setAttribute('opacity', '1'));
          setTimeout(() => a.g.querySelectorAll('.lid').forEach(l => l.setAttribute('opacity', '0')), 130);
          blinkT.set(a, now + 2500 + Math.random() * 4500);
        }
      });
      actors.forEach((a, i) => {
        const w = Math.sin(now / 150 + i * 1.7) * 1.1;
        const j = JSON.parse(JSON.stringify(RIG.type));
        j.nwr = [j.nwr[0], j.nwr[1] + w];
        j.fwr = [j.fwr[0], j.fwr[1] - w];
        j.bob = Math.sin(now / 1400 + i) * 0.7;
        a.joints = j; a.draw();
      });
      document.querySelectorAll('.steam').forEach(p =>
        p.setAttribute('stroke-dashoffset', String(-(now / 90) % 24)));
      document.querySelectorAll('.mon-ui path').forEach(p =>
        p.setAttribute('stroke-opacity', String(0.75 + 0.25 * Math.sin(now / 900))));
    }
    requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}
ambient();
document.getElementById('ambient').onclick = e => {
  AMBIENT = !AMBIENT;
  e.target.textContent = 'Ambient ' + (AMBIENT ? 'on' : 'off');
  e.target.setAttribute('aria-pressed', String(AMBIENT));
};

// ---- screens: the office is the home screen of a small app. Everything
// here is in-page navigation over the SAME state the office renders.
const STATE = __STATE__;
const STATUS_COLOUR = {todo:'#64748B',design:'#0E7490',build:'#1E40AF',test:'#B45309',
                       blocked:'#BE123C',done:'#15803D',shipped:'#15803D',
                       committed:'#64748B',groomed:'#94A3B8',backlog:'#94A3B8'};
// mirrors sprint_board.COLUMNS exactly — a column missing here would silently
// hide any story sitting in it
const COLS = ['Backlog','To-Do','Design','Build','Test','Blocked','Done'];
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => (
  {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

function showScreen(name) {
  document.querySelectorAll('.screen').forEach(s =>
    s.hidden = (s.id !== 'screen-' + name));
  document.querySelectorAll('.navbtn').forEach(b =>
    b.classList.toggle('is-on', b.dataset.screen === name));
  if (name === 'board') renderBoard();
  if (name === 'backlog') renderBacklog();
  if (name === 'sprint') renderSprint();
  // the auto-refresh reload must bring the viewer back to THIS screen,
  // not dump them on the office home
  try { sessionStorage.setItem('office.screen', name); } catch {}
  try { window.scrollTo({top: 0, behavior: 'smooth'}); } catch {}
}
document.querySelectorAll('.navbtn, .backbtn').forEach(b =>
  b.addEventListener('click', () => showScreen(b.dataset.screen)));

function cardHtml(c) {
  const col = STATUS_COLOUR[c.status] || '#64748B';
  return `<div class="scard" data-story="${esc(c.id)}" tabindex="0" role="button"
            style="border-left-color:${col}">
      <div class="sid">${esc(c.id)}${c.shipped ? ' &#9733;' : ''}</div>
      <div class="stitle">${esc(c.title)}</div>
      <div><span class="pill">${esc(c.points)} pts</span>
           <span class="pill">${esc(c.risk)} risk</span>
           ${c.holder ? `<span class="pill">${esc(c.holder)}</span>` : ''}</div>
    </div>`;
}
function wireCards(root) {
  root.querySelectorAll('.scard').forEach(el => {
    const open = () => showStory(el.dataset.story);
    el.addEventListener('click', open);
    el.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); } });
  });
}
function renderBoard() {
  const cols = STATE.columns || {};
  const host = document.getElementById('boardview');
  const n = c => (cols[c] || []).length;
  const inFlight = n('Design') + n('Build') + n('Test');
  const summary =
    `${n('Done')} done &middot; ` +
    (inFlight ? `${inFlight} in flight` : 'nothing in flight') + ' &middot; ' +
    (n('Blocked') ? `<strong>${n('Blocked')} BLOCKED</strong>` : 'nothing blocked');
  host.innerHTML = `<div class="bsummary">${summary}</div><div class="bcols">` +
    COLS.map(c => {
      const items = cols[c] || [];
      if (!items.length)
        return `<div class="bcol empty"><h3><span>${c}</span><span>0</span></h3></div>`;
      return `<div class="bcol"><h3><span>${c}</span><span>${items.length}</span></h3>` +
             items.map(cardHtml).join('') + '</div>';
    }).join('') + '</div>';
  wireCards(host);
}
const riskPill = r => r ? `<span class="pill ${String(r).toLowerCase() === 'high' ? 'pill-hi' : ''}">${esc(r)} risk</span>` : '';
function renderBacklog() {
  const items = STATE.backlog_items || [];
  const host = document.getElementById('backlogview');
  const h2 = document.querySelector('#screen-backlog h2');
  if (h2) h2.textContent = `Backlog · ${items.length}`;
  host.innerHTML = items.length ? items.map((i, ix) => i.kind === 'story'
      ? `<div class="lrow"><span class="lid">${esc(i.id)}</span>
           <span>${esc(i.title)}</span>
           <span class="pill">${esc(i.points)} pts</span>
           ${riskPill(i.risk)}
           <span class="pill">${esc(i.status)}</span></div>`
      : `<div class="lrow idea"><span class="lid">#${ix + 1}</span>
           <span>${esc(i.title)}</span>
           ${i.intent ? `<span class="lint">${esc(i.intent)}</span>` : ''}
           ${i.points ? `<span class="pill">${esc(i.points)} pts</span>` : ''}</div>`
    ).join('') : '<div class="lint">Backlog is empty.</div>';
}
function goalRows(goal) {
  if (!goal) return '<p class="lint">No sprint goal recorded.</p>';
  // Goal: ... Method: ... Metric: ... -> three skimmable labelled rows
  const parts = String(goal).split(/(?=Method:|Metric:)/);
  return '<div class="goalrows">' + parts.map(p => {
    const m = p.match(/^(Goal|Method|Metric):\\s*([^]*)$/);
    return m ? `<div class="goalrow"><b>${m[1]}</b><span>${esc(m[2].trim())}</span></div>`
             : `<div class="goalrow"><b>Goal</b><span>${esc(p.trim())}</span></div>`;
  }).join('') + '</div>';
}
function renderSprint() {
  const p = STATE.points || {}, s = STATE.stories || {};
  const acts = STATE.activity || [];
  document.getElementById('sprintview').innerHTML =
    `<div class="kpirow">
       <div class="kpibox"><div class="k">Sprint</div><div class="v">${esc(STATE.sprint || '-')}</div></div>
       <div class="kpibox"><div class="k">Points</div><div class="v">${p.done ?? 0}/${p.total ?? 0}</div></div>
       <div class="kpibox"><div class="k">Stories</div><div class="v">${s.done ?? 0}/${s.total ?? 0}</div></div>
       <div class="kpibox"><div class="k">Shipped</div><div class="v">${(STATE.release||{}).shipped ?? 0}</div></div>
     </div>
     ${goalRows(STATE.goal)}
     <h3 style="font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:var(--dim);margin:1rem 0 .2rem">Latest activity</h3>
     <ul class="actfeed">` +
    (acts.length ? acts.map(a =>
      `<li><span class="aw">${esc(a.when)}</span>
         <span><strong>${esc(a.story || '')}</strong> ${esc(a.desc)}
         ${a.name && a.name !== '?' ? '&mdash; ' + esc(a.name) : ''}</span></li>`).join('')
      : '<li class="lint">No activity recorded.</li>') + '</ul>';
}
function showStory(id) {
  const st = (STATE.story_detail || []).find(s => s.id === id);
  const host = document.getElementById('storyview');
  if (!st) { host.innerHTML = '<div class="lint">Story not found in the current state.</div>'; }
  else {
    const done = st.tasks.filter(t => t.done).length;
    host.innerHTML =
      `<div class="kpirow">
         <div class="kpibox"><div class="k">${esc(st.id)}</div><div class="v">${esc(st.points)} pts</div></div>
         <div class="kpibox"><div class="k">Status</div><div class="v" style="font-size:1rem">${esc(st.status)}</div></div>
         <div class="kpibox"><div class="k">Column</div><div class="v" style="font-size:1rem">${esc(st.column)}</div></div>
         <div class="kpibox"><div class="k">Risk</div><div class="v" style="font-size:1rem">${esc(st.risk)}</div></div>
       </div>
       <h3 style="margin:.2rem 0 .4rem">${esc(st.title)}</h3>
       <p class="lint">${st.holder ? 'Held by ' + esc(st.holder) + ' &middot; ' : ''}repo ${esc(st.repo)} &middot; sprint ${esc(st.sprint || '-')}</p>
       <h3 style="font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:var(--dim);margin:1rem 0 .2rem">Tasks ${done}/${st.tasks.length}</h3>
       <ul class="tasklist">` +
      (st.tasks.length ? st.tasks.map(t =>
        `<li><span class="tick ${t.done ? 'on' : ''}"></span>
           ${t.kind ? `<span class="pill">${esc(t.kind)}</span>` : ''}
           <span>${esc(t.label)}</span></li>`).join('')
        : '<li class="lint">No task breakdown recorded.</li>') + '</ul>';
  }
  try { sessionStorage.setItem('office.story', id); } catch {}
  showScreen('story');
}

// hotspots hug the painted objects: measured from the real bounding boxes so
// they can never drift off-target or overlap each other
function placeHotspots() {
  const svg = document.getElementById('stage');
  const layer = document.getElementById('hotspots');
  if (!svg || !layer) return;
  layer.innerHTML = '';
  const vb = svg.viewBox.baseVal, sr = svg.getBoundingClientRect();
  if (!sr.width) return;
  const sx = vb.width / sr.width, sy = vb.height / sr.height;
  const HS = {board: 'Open the sprint board', backlog: 'Open the backlog',
              sprint: 'Sprint summary', ask: 'Ask the crew'};
  // per-side trims [left, top, right, bottom] (fractions of w/h): wall art
  // bboxes reach down to where crew sit, so the BOTTOM is trimmed hard to
  // keep zones off faces; the skewed board also loses its empty corners.
  const TRIM = {board: [0.08, 0.12, 0.08, 0.34], sprint: [0.05, 0.05, 0.05, 0.34],
                backlog: [0.05, 0.1, 0.05, 0.1], ask: [0.08, 0.18, 0.08, 0.12]};
  // crew heads sit IN FRONT of the wall art, so head discs are clipped OUT of
  // every zone (even-odd) — a face never tints and never triggers a click
  const heads = CREW.map(c => { const [hx, hy] = iso(c.x, c.y);
    return {cx: hx - 2, cy: hy - 90, r: 19}; });
  const headCut = (x, y, w, h) => heads
    .filter(o => o.cx + o.r > x && o.cx - o.r < x + w && o.cy + o.r > y && o.cy - o.r < y + h)
    .map(o => `M ${o.cx + o.r} ${o.cy} A ${o.r} ${o.r} 0 1 0 ${o.cx - o.r} ${o.cy} ` +
              `A ${o.r} ${o.r} 0 1 0 ${o.cx + o.r} ${o.cy} Z`).join(' ');
  let clipSeq = 0;
  let defs = svg.querySelector('#hs-defs');
  if (!defs) { defs = svgEl('defs', {id: 'hs-defs'}); svg.appendChild(defs); }
  defs.innerHTML = '';
  const targets = [...document.querySelectorAll('#stage [data-hs]')]
    .sort((a, b) => (a.dataset.hs === 'board') - (b.dataset.hs === 'board'));
  targets.forEach(t => {                      // board sorts last = on top
    const screen = t.dataset.hs, label = HS[screen];
    if (!label) return;
    const b = t.getBoundingClientRect();
    const [fl, ft, fr, fb] = TRIM[screen] || [0, 0, 0, 0];
    const r = svgEl('rect', {
      class: 'hotspot', rx: 10, tabindex: 0, role: 'button', 'data-screen': screen,
      x: (vb.x + (b.left - sr.left + b.width * fl) * sx).toFixed(0),
      y: (vb.y + (b.top - sr.top + b.height * ft) * sy).toFixed(0),
      width: (b.width * (1 - fl - fr) * sx).toFixed(0),
      height: (b.height * (1 - ft - fb) * sy).toFixed(0)});
    const rx = +r.getAttribute('x'), ry = +r.getAttribute('y'),
          rw = +r.getAttribute('width'), rh = +r.getAttribute('height');
    const cut = headCut(rx, ry, rw, rh);
    if (cut) {
      const cp = svgEl('clipPath', {id: 'hs-clip-' + (++clipSeq)});
      const p = svgEl('path', {'clip-rule': 'evenodd',
        d: `M ${rx} ${ry} h ${rw} v ${rh} h ${-rw} Z ` + cut});
      cp.appendChild(p); defs.appendChild(cp);
      r.setAttribute('clip-path', `url(#hs-clip-${clipSeq})`);
    }
    const ti = svgEl('title'); ti.textContent = label; r.appendChild(ti);
    const go = () => showScreen(screen);
    r.addEventListener('click', go);
    r.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } });
    layer.appendChild(r);
  });
}
placeHotspots();
addEventListener('resize', placeHotspots);

// restore the screen the viewer was on before the last (auto-)reload
(() => {
  let saved = null, story = null;
  try { saved = sessionStorage.getItem('office.screen');
        story = sessionStorage.getItem('office.story'); } catch {}
  if (saved === 'story' && story) showStory(story);
  else if (saved && saved !== 'office' && document.getElementById('screen-' + saved))
    showScreen(saved);
})();

// ---- self-refresh: the page reloads itself on an interval and therefore
// picks up whatever state was last published, with no connector involved.
// Reload is skipped while the tab is hidden or the viewer is mid-interaction,
// so it never yanks the page out from under a click.
const REFRESH_MS = 120000, IDLE_GUARD_MS = 15000;
let autoRefresh = true, lastTouch = Date.now();
['pointerdown', 'keydown', 'wheel'].forEach(ev =>
  addEventListener(ev, () => { lastTouch = Date.now(); }, {passive: true}));

const freshEl = document.getElementById('freshness');
function renderFreshness() {
  if (!freshEl) return;
  const gen = freshEl.dataset.generated;
  if (!gen) { freshEl.textContent = ''; return; }
  const mins = Math.max(0, Math.round((Date.now() - new Date(gen).getTime()) / 60000));
  const word = mins < 1 ? 'just now' : (mins < 60 ? mins + 'm ago'
             : Math.round(mins / 60) + 'h ago');
  freshEl.textContent = 'state ' + word;
  freshEl.classList.toggle('stale', mins > 90);
}
renderFreshness();
setInterval(renderFreshness, 30000);

setInterval(() => {
  if (!autoRefresh) return;
  if (document.visibilityState !== 'visible') return;
  if (Date.now() - lastTouch < IDLE_GUARD_MS) return;
  location.reload();
}, REFRESH_MS);

document.getElementById('autoref').onclick = e => {
  autoRefresh = !autoRefresh;
  e.target.textContent = 'Auto-refresh ' + (autoRefresh ? 'on' : 'off');
  e.target.setAttribute('aria-pressed', String(autoRefresh));
};
document.getElementById('refnow').onclick = () => location.reload();

// ---- request desk: a click MUTATES the served document, so it persists as
// the viewer and reaches the delivery session. Never executes anything here.
const PHASE_WORDS = {
  groom: 'Groom the backlog', plan: 'Plan the next sprint',
  run: 'Get the sprint moving', status: 'Give me a status',
  retro: 'Hold a retro', showcase: 'Open the showcase',
  unblock: 'Something is blocked - help'
};
const reqlog = document.getElementById('reqlog');
function stamp() {
  const d = new Date();
  const p = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}
function logRequest(phase, wording) {
  const empty = reqlog.querySelector('.reqempty');
  if (empty) empty.remove();
  const li = document.createElement('li');
  li.setAttribute('data-phase', phase);
  li.setAttribute('data-requested-at', new Date().toISOString());
  const mk = (cls, txt) => { const s = document.createElement('span');
    s.className = cls; s.textContent = txt; return s; };
  li.appendChild(mk('when', stamp()));
  li.appendChild(mk('who', wording));       // textContent: viewer input stays text
  li.appendChild(mk('state', 'requested · waiting for the crew'));
  reqlog.appendChild(li);
}
document.querySelectorAll('.reqbtn[data-phase]').forEach(b => {
  b.addEventListener('click', () =>
    logRequest(b.dataset.phase, PHASE_WORDS[b.dataset.phase] || b.dataset.phase));
});
const reqText = document.getElementById('reqtext');
const sendFree = () => {
  const v = (reqText.value || '').trim();
  if (!v) return;
  logRequest('custom', v);
  reqText.value = '';
};
document.getElementById('reqsend').addEventListener('click', sendFree);
reqText.addEventListener('keydown', e => { if (e.key === 'Enter') sendFree(); });
"""
    office_engine = (office_engine.replace("__CREW__", crew_js)
                     .replace("__TYPE__", type_js)
                     .replace("__STATE__", state_json))

    delivery_name = esc((state or {}).get("delivery", "arrangement"))
    generated_at = esc((state or {}).get("generated_at", ""))
    seed_log = '<li class="reqempty">No requests yet.</li>'
    if state:
        ptsd = state.get("points", {})
        stc = state.get("stories", {})
        sub_line = (f'{esc(state.get("delivery",""))} &middot; sprint '
                    f'{esc(state.get("sprint") or "-")} &middot; '
                    f'{stc.get("done",0)}/{stc.get("total",0)} stories &middot; '
                    f'{ptsd.get("done",0):g}/{ptsd.get("total",0):g} pts')
        goal_txt = (state.get("goal") or "").split("Method:")[0].replace("Goal:", "").strip()
        goal_short = (goal_txt if len(goal_txt) <= 120
                      else goal_txt[:120].rsplit(" ", 1)[0] + "…")
        status_html = (f'<span class="chip-live">LIVE</span>'
                       f'<span id="freshness" class="freshness" '
                       f'title="state generated {generated_at}" '
                       f'data-generated="{generated_at}">checking…</span>'
                       f'<span class="goal-inline" title="{esc(goal_txt)}">{esc(goal_short)}</span>')
    else:
        sub_line = "complete office &middot; approved kit v2 &middot; ambient layer only"
        status_html = ""

    fonts = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600'
             '&family=Fira+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">')
    controls_css = (
        ".chip-live{background:#15803D;color:#fff;font-size:.62rem;font-weight:700;"
        "letter-spacing:.08em;border-radius:999px;padding:.14rem .55rem;margin-left:.4rem}"
        ".goal-inline{font-size:.76rem;color:var(--dim);margin-left:.5rem}"
        ".controls{display:flex;gap:.5rem;align-items:center;margin:.6rem 0 .2rem;flex-wrap:wrap}"
        ".controls button{font-size:.78rem;padding:.35rem .85rem;border-radius:999px;cursor:pointer;"
        "border:1px solid var(--panel-border);background:var(--panel);color:var(--ink);font-weight:600}"
        ".controls button:hover{background:var(--badge-chip)}"
        ".legendline{font-size:.7rem;color:var(--dim);margin-top:.4rem;max-width:100ch}"
        ".reqdesk{background:var(--panel);border:1px solid var(--panel-border);border-radius:16px;"
        "padding:1rem 1.2rem;margin-top:.9rem;box-shadow:0 1px 3px rgba(58,48,36,.07)}"
        ".reqdesk h2{font-size:.74rem;text-transform:uppercase;letter-spacing:.11em;color:var(--dim);"
        "margin:0 0 .5rem;display:flex;align-items:center;gap:.5rem}"
        ".reqdesk h2::before{content:'';width:.6rem;height:.6rem;border-radius:3px;background:var(--terra)}"
        ".reqhint{font-size:.78rem;color:var(--dim);max-width:86ch;margin:0 0 .7rem;line-height:1.5}"
        ".reqbtns{display:flex;flex-wrap:wrap;gap:.45rem}"
        ".reqbtn{font-size:.78rem;padding:.4rem .9rem;border-radius:999px;cursor:pointer;font-weight:600;"
        "border:1px solid var(--panel-border);background:var(--badge-chip);color:var(--ink)}"
        ".reqbtn:hover{background:var(--panel);border-color:var(--terra)}"
        ".reqbtn:focus-visible{outline:2px solid var(--terra);outline-offset:2px}"
        ".reqlog{list-style:none;margin:.8rem 0 0;padding:0;display:flex;flex-direction:column;gap:.35rem}"
        ".reqlog li{font-size:.78rem;display:flex;gap:.55rem;align-items:baseline;"
        "border-left:3px solid var(--terra);padding:.28rem .6rem;background:var(--badge-chip);border-radius:0 8px 8px 0}"
        ".reqlog .when{font-family:'Fira Code',monospace;font-size:.68rem;color:var(--dim)}"
        ".reqlog .who{font-weight:600}"
        ".reqlog .state{margin-left:auto;font-size:.66rem;color:var(--dim);font-family:'Fira Code',monospace}"
        ".reqnote{font-size:.74rem;color:var(--ink);margin:.8rem 0 0;max-width:86ch;line-height:1.5;"
        "border-left:3px solid var(--terra);background:var(--badge-chip);padding:.45rem .7rem;border-radius:0 8px 8px 0}"
        ".reqempty{font-size:.76rem;color:var(--dim);font-style:italic}"
        ".reqfree{display:flex;gap:.45rem;margin-top:.6rem}"
        ".reqfree input{flex:1;max-width:46ch;font-size:.78rem;font-family:inherit;padding:.4rem .7rem;"
        "border-radius:999px;border:1px solid var(--panel-border);background:var(--bg);color:var(--ink)}"
        ".reqfree input:focus-visible{outline:2px solid var(--terra);outline-offset:1px}"
        ".ctl-gap{flex:1}"
        ".ghostbtn{background:transparent;border:1px solid var(--panel-border);color:var(--dim);"
        "font-size:.7rem;padding:.28rem .7rem;border-radius:999px;cursor:pointer}"
        ".ghostbtn:hover{color:var(--ink);border-color:var(--terra)}"
        ".ghostbtn[aria-pressed=\"false\"]{opacity:.55;text-decoration:line-through}"
        ".bsummary{font-size:.82rem;margin-bottom:.7rem;color:var(--ink)}"
        ".bsummary strong{color:#BE123C}"
        ".bcols{display:flex;gap:.6rem;overflow-x:auto;align-items:flex-start}"
        ".bcol{flex:1 1 0;min-width:170px}"
        ".bcol.empty{flex:0 0 auto;min-width:86px;min-height:auto;opacity:.65}"
        ".bcol h3{gap:.5rem}"
        ".bcol.empty h3{border-bottom-width:1px;margin-bottom:0;padding-bottom:.2rem}"
        ".goalrows{display:flex;flex-direction:column;gap:.35rem;max-width:96ch}"
        ".goalrow{display:flex;gap:.7rem;font-size:.8rem;line-height:1.5}"
        ".goalrow b{flex:0 0 3.6rem;font-size:.66rem;text-transform:uppercase;letter-spacing:.09em;"
        "color:var(--terra);padding-top:.15rem}"
        ".pill-hi{background:var(--terra);color:#fff}"
        ".tasklist li span:last-child{line-height:1.5;max-width:100ch}"
        "@media (prefers-color-scheme: dark){:root:not([data-theme=\"light\"]) #stage{--board-bg:#403A2F}}"
        ":root[data-theme=\"dark\"] #stage{--board-bg:#403A2F}"
        ".freshness{font-size:.7rem;color:var(--dim);font-family:'Fira Code',monospace;margin-left:.2rem}"
        ".freshness.stale{color:var(--terra);font-weight:600}"
        ".screennav{display:flex;gap:.4rem;flex-wrap:wrap;margin:.2rem 0 .1rem}"
        ".navbtn{font-size:.8rem;font-weight:600;padding:.42rem 1rem;border-radius:999px;cursor:pointer;"
        "border:1px solid var(--panel-border);background:var(--panel);color:var(--dim)}"
        ".navbtn:hover{color:var(--ink);border-color:var(--terra)}"
        ".navbtn.is-on{background:var(--terra);border-color:var(--terra);color:#fff}"
        ".navbtn:focus-visible{outline:2px solid var(--terra);outline-offset:2px}"
        ".hotspot{cursor:pointer;fill:transparent}"
        ".hotspot:hover{fill:var(--terra);fill-opacity:.10}"
        ".hotspot:focus-visible{outline:none;fill:var(--terra);fill-opacity:.18}"
        ".boardview{display:block}"
        ".bcol{background:var(--bg);border:1px solid var(--panel-border);border-radius:12px;padding:.5rem;min-height:110px}"
        ".bcol h3{font-size:.7rem;text-transform:uppercase;letter-spacing:.07em;margin:.1rem 0 .5rem;"
        "display:flex;justify-content:space-between;color:var(--dim);padding-bottom:.35rem;border-bottom:2px solid var(--card-edge)}"
        ".scard{background:var(--panel);border:1px solid var(--panel-border);border-left-width:3px;border-radius:9px;"
        "padding:.45rem .55rem;margin-bottom:.45rem;cursor:pointer;font-size:.8rem}"
        ".scard:hover{border-color:var(--terra)}"
        ".scard .sid{font-family:'Fira Code',monospace;font-size:.68rem;color:var(--terra);font-weight:600}"
        ".scard .stitle{line-height:1.35;margin:.1rem 0 .3rem}"
        ".pill{display:inline-block;font-size:.64rem;border-radius:999px;padding:.06rem .45rem;"
        "background:var(--badge-chip);color:var(--dim);margin-right:.25rem}"
        ".listview{display:flex;flex-direction:column;gap:.4rem}"
        ".lrow{display:flex;gap:.6rem;align-items:baseline;background:var(--bg);border:1px solid var(--panel-border);"
        "border-radius:10px;padding:.45rem .7rem;font-size:.82rem}"
        ".lrow.idea{border-style:dashed}"
        ".lrow .lid{font-family:'Fira Code',monospace;font-size:.68rem;color:var(--terra);font-weight:600;min-width:3.6rem}"
        ".lint{color:var(--dim);font-size:.76rem}"
        ".backbtn{font-size:.68rem;padding:.2rem .6rem;border-radius:999px;cursor:pointer;"
        "border:1px solid var(--panel-border);background:var(--panel);color:var(--ink);margin-right:.5rem}"
        ".kpirow{display:flex;flex-wrap:wrap;gap:.7rem;margin-bottom:.8rem}"
        ".kpibox{background:var(--bg);border:1px solid var(--panel-border);border-radius:12px;padding:.6rem .9rem;min-width:130px}"
        ".kpibox .k{font-size:.62rem;text-transform:uppercase;letter-spacing:.09em;color:var(--dim)}"
        ".kpibox .v{font-size:1.3rem;font-weight:600;font-family:'Fira Code',monospace}"
        ".tasklist{list-style:none;padding:0;margin:.5rem 0 0;display:flex;flex-direction:column;gap:.25rem}"
        ".tasklist li{font-size:.78rem;display:flex;gap:.5rem;align-items:baseline}"
        ".tick{width:.7rem;height:.7rem;border-radius:3px;border:1.5px solid var(--card-edge);flex:none}"
        ".tick.on{background:#15803D;border-color:#15803D}"
        ".actfeed{list-style:none;padding:0;margin:.5rem 0 0;display:flex;flex-direction:column;gap:.3rem}"
        ".actfeed li{font-size:.78rem;display:flex;gap:.6rem;align-items:baseline;border-bottom:1px dashed var(--panel-border);padding-bottom:.25rem}"
        ".actfeed .aw{font-family:'Fira Code',monospace;font-size:.66rem;color:var(--dim);min-width:5.2rem}")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sprint Office</title>{fonts}
<style>{theme_css()}{controls_css}</style></head>
<body>{defs_html}
<artifact-local><button class="themetoggle">theme</button></artifact-local>
<div class="wrap">
<h1>The Sprint Office</h1>
<div class="sub">{sub_line}</div>
<nav class="screennav"><artifact-local>
  <button class="navbtn is-on" data-screen="office">Office</button>
  <button class="navbtn" data-screen="board">Board</button>
  <button class="navbtn" data-screen="backlog">Backlog</button>
  <button class="navbtn" data-screen="sprint">Sprint</button>
  <button class="navbtn" data-screen="ask">Ask the crew</button>
</artifact-local></nav>
<div class="controls">{status_html}<span class="ctl-gap"></span><artifact-local><button id="ambient" class="ghostbtn" aria-pressed="true">Ambient on</button>
<button id="autoref" class="ghostbtn" aria-pressed="true">Auto-refresh on</button><button id="refnow" class="ghostbtn">Refresh now</button></artifact-local></div>
<section class="screen" id="screen-office">
<div class="sec scene">
<svg id="stage" width="1200" height="800" viewBox="-350 -155 830 555" role="img" aria-label="The Sprint Office: six crew at their stations with live sprint status; the wall board, backlog shelf, planning wall and showcase screen open their screens">
<defs>{SOFTBLUR}</defs>
{floor}{walls}{static_svg}{rim}<g id="actors"></g><g id="chips"></g>
<g id="hotspots"></g>
</svg>
</div>
</section>

<section class="screen" id="screen-board" hidden><div class="sec"><h2>Sprint board</h2>
  <div id="boardview" class="boardview"></div></div></section>

<section class="screen" id="screen-backlog" hidden><div class="sec"><h2>Backlog</h2>
  <div id="backlogview" class="listview"></div></div></section>

<section class="screen" id="screen-sprint" hidden><div class="sec"><h2>This sprint</h2>
  <div id="sprintview"></div></div></section>

<section class="screen" id="screen-story" hidden><div class="sec">
  <h2><button class="backbtn" data-screen="board">&larr; Board</button> Story</h2>
  <div id="storyview"></div></div></section>

<section class="screen" id="screen-ask" hidden>
<section class="reqdesk">
  <h2>Ask the crew</h2>
  <p class="reqhint">Tap what you want to happen next. Your request is saved on this page as you,
  with a timestamp, and reaches the delivery session — it is a <strong>request, not an
  execution</strong>: the crew still runs the phase properly, and nothing here can approve a
  release or push to production.</p>
  <div class="reqbtns">
    <button class="reqbtn" data-phase="groom">Groom the backlog</button>
    <button class="reqbtn" data-phase="plan">Plan the next sprint</button>
    <button class="reqbtn" data-phase="run">Get the sprint moving</button>
    <button class="reqbtn" data-phase="status">Give me a status</button>
    <button class="reqbtn" data-phase="retro">Hold a retro</button>
    <button class="reqbtn" data-phase="showcase">Open the showcase</button>
    <button class="reqbtn" data-phase="unblock">Something is blocked — help</button>
  </div>
  <div class="reqfree">
    <input id="reqtext" maxlength="300" placeholder="Or type your own request…">
    <button id="reqsend" class="reqbtn">Send</button>
  </div>
  <ol id="reqlog" class="reqlog" data-delivery="{delivery_name}">{seed_log}</ol>
  <p class="reqnote">Release approval is deliberately not a button. Going live needs your words,
  recorded verbatim in the showcase — that rule does not move.</p>
</section>
</section>
</div>
<script>{skin_js()}
{TOGGLE_JS}
{office_engine}</script>
</body></html>"""

# ------------------------------------------------------------------- main --
def _load_state(delivery: str, root: Path):
    """A delivery's office state, once sprint_office_state.py has built it.

    NEVER falls back to another delivery: rendering one delivery's office
    from another's state would silently show the wrong work.
    """
    f = root / "deliveries" / delivery / "office-state.json"
    try:
        return json.loads(f.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        print(f"warning: {f} not found — run sprint_office_state.py "
              f"{delivery} first; rendering the office without live state",
              file=sys.stderr)
        return None
    except (OSError, ValueError) as exc:
        print(f"warning: {f} unreadable ({exc}); rendering without live state",
              file=sys.stderr)
        return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Render a delivery's Sprint Office (or re-emit the asset kit)")
    ap.add_argument("--delivery", default=None,
                    help="render the office from this delivery's office-state.json")
    ap.add_argument("--root", default="sprint",
                    help="the PROJECT's sprint state directory (default: sprint)")
    ap.add_argument("--out", default=None,
                    help="where to write the office HTML "
                         "(default: <root>/deliveries/<delivery>/office.html)")
    ap.add_argument("--emit-kit", action="store_true",
                    help="also re-emit the design-system asset library and its preview "
                         "pages INTO THE PLUGIN — kit development only, not needed to run a sprint")
    args = ap.parse_args(argv)

    emits = {}

    if args.delivery:
        state = _load_state(args.delivery, Path(args.root))
        out = (Path(args.out) if args.out else
               Path(args.root) / "deliveries" / args.delivery / "office.html")
        out.parent.mkdir(parents=True, exist_ok=True)
        emits[out] = office_html(state)
    elif not args.emit_kit:
        ap.error("nothing to do: pass --delivery <name> to render an office, "
                 "or --emit-kit to rebuild the asset library")

    if args.emit_kit:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "preview").mkdir(exist_ok=True)
        emits.update({
            OUT / "characters.svg": f'<svg xmlns="http://www.w3.org/2000/svg">{characters_svg()}</svg>',
            OUT / "furniture.svg": f'<svg xmlns="http://www.w3.org/2000/svg">{furniture_svg()}</svg>',
            OUT / "sprintboard.svg": f'<svg xmlns="http://www.w3.org/2000/svg">{sprintboard_svg()}</svg>',
            OUT / "collab.svg": f'<svg xmlns="http://www.w3.org/2000/svg">{collab_svg()}</svg>',
            OUT / "environment.svg": f'<svg xmlns="http://www.w3.org/2000/svg">{environment_svg()}</svg>',
            OUT / "characters.css": char_css(),
            OUT / "rig.json": json.dumps({"rig": RIG, "moods": MOODS, "hair_f": HAIR_F,
                                          "hair_b": HAIR_B, "slots": BOARD_SLOTS}, indent=1),
            OUT / "preview" / "asset-kit-board.html": kit_board_html(),
            OUT / "preview" / "proof-scene.html": proof_scene_html(),
            OUT / "preview" / "motion-prototype.html": motion_prototype_html(),
            OUT / "preview" / "office.html": office_html(None),
        })

    for path, content in emits.items():
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"emitted {path} ({len(content):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
