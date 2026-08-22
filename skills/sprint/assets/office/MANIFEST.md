# Sprint Office — Asset Manifest

Generator: `scripts/sprint_office_kit.py` (single source of truth — never hand-edit emitted
files; change the generator and re-run). Rules: `STYLE.md` (normative). State mapping:
`STATE-MATRIX.md` (normative). Previews: `preview/asset-kit-board.html`,
`preview/proof-scene.html` (self-contained; Google Fonts only external reference).

## How assets are consumed
Each `.svg` file is a `<defs>` library of `<symbol>`s meant to be INLINED into a page (CSP-safe
for artifacts). Two usage rules, both enforced by generator helpers:
1. **Identity `<use>` sizing** — always emit `<use href="#id" x y width height>` equal to the
   symbol's viewBox (`iuse()` helper). A bare `<use>` on a symbol stretches to the viewport.
2. **Painter's order** — scene items sort by world `(x + y)` before emission (back-to-front).

Characters are skinned at runtime by ~30 lines of JS (`skinChars()` in the previews): it clones
the pose symbol per character and injects the role's garment overlay, accessory, and hair shape,
because `<use>` cannot vary a symbol's inner content. Role/skin/hair/status come from CSS
classes (`role-dev skin-s2 hair-h1`, `status-build`) defined in `characters.css`.

## v2 (2026-08-21, PO refinement round)
- **Rig v2**: jointed 3/4 characters (shoulder/elbow/wrist, hip/knee/ankle as round-cap stroke
  capsules), front-3/4 AND rear-3/4 bases, mirrored to four facings; faces with eyes/brows/mouth
  and restrained moods (neutral/smile/focus/concern); necks, ears, dimensional two-tone shading.
  Symbols: `c2-f-<pose>` (all poses) and `c2-r-<pose>` (stand/walkA/walkB/sit/type/carry).
- **rig.json**: the pose joint tables + moods + hair paths + board slot coordinates — the motion
  engine consumes this SAME data (single source; the prototype's JS renderer mirrors the Python
  draw order — keep both in sync when editing the rig).
- **Motion prototype**: `preview/motion-prototype.html` — procedural walk cycle (joint lerp
  between walkA/walkB), sit<->stand tweens, facing-from-velocity, painter re-layering per frame,
  carried tickets riding the wrist, board-slot card moves in the skewed plane, PASS and FAIL
  scenarios with captions, Replay/Pause/speed(0.5-2x)/Ambient-toggle controls,
  prefers-reduced-motion stepped mode. Ambient layer per STYLE.md section 9.
- **Warm palette v2** is normative (STYLE.md section 3); decorative terracotta never signals
  status (rule 3b).

## characters.svg (+ characters.css)
| Item | Ids | Notes |
|---|---|---|
| Pose symbols (one rig) | `pose-standing, -sitting, -typing, -reading, -thinking, -walking, -talking, -pointing, -carrying, -atboard, -handoff, -testing, -review-result, -blocked, -alarmed, -celebrating, -presenting` | 17 poses; viewBox `-52 -108 104 116`; origin at feet-centre; height 96 (3 heads); facing ¾-left, mirror with `scale(-1,1)` |
| Hair variants | `hair-crop, -bob, -bun, -curls, -swept, -short` | injected into `.part-head .hair`; colour via `hair-h1…h5` class |
| Role skins | classes `role-po, -sm, -ba, -techba, -dev, -tester` | garment + trouser vars per role, dark-theme override included |
| Skin tones | classes `skin-s1…s4` | palette variants, not identities |
| Handheld props | baked per pose: folder (carrying), ticket (atboard/handoff), sheet (reading/review), magnifier (testing) | ticket edge colour follows `status-*` class |
| Accessories | PO gold lanyard+tie · SM headset · TechBA glasses · Tester collar band · (BA/Dev garment-only) | injected via `skinChars()` |
| Garment styles | blazer (PO) · hoodie (Dev) · cardigan (others) | overlay paths, injected |

**Animation readiness:** parts carry stable classes (`part-head`, `part-torso`, `part-legs`,
`part-arm-l/r`); poses are transform recipes over the same parts, so tweening between poses =
interpolating those transforms (or cross-fading pose symbols ≤200ms). Walk cycles = alternating
`pose-walking` with its mirror. All motion must respect `prefers-reduced-motion`.
**Limitation:** legs have three configurations (stand/walk/sit) as distinct shapes — a
mid-transition between leg configs should cross-fade, not morph.

## furniture.svg
`desk` (2×1 tiles, h40) · `chair` (back on the FAR side so seated characters read in front) ·
`monitor` (screen faces viewer — deliberate stylisation) · `laptop` · `keyboard` · `mouse` ·
`desk-lamp` · `mug` (steam path has class `steam` for later animation) · `papers` ·
`desk-plant` · `beacon` (orb fill = `var(--status)`; put `status-*` on the wrapper).
Desk-top items sit at z≈41px: place with `translate(0,-41)` on a desk tile.

## sprintboard.svg
`sprint-board` (six columns incl. Blocked, matches the real board's column model) ·
`story-card` 36×24 · `task-card` + typed `task-card-build/-test/-bug` 28×18 (kind chip) ·
`ac-checklist` · `stamp-pass` / `stamp-fail` · `evidence-folder` · `release-marker` ·
`shipped-ribbon` · `blocked-chain` · `risk-flame` · icons `icon-check, -cross, -bug, -lock,
-question, -flag, -folder, -magnifier, -pencil, -hammer` (16×16, stroke = currentColor).
Cards are flat UI objects (billboard style) by design — legibility over projection.

## collab.svg
`meeting-table` · `planning-wall` · `showcase-screen` (gold approval seal on screen) ·
`decision-tray` (PO inbox; gold = decision colour) · `handoff-ticket` (motion lines) ·
`retro-rug`.

## environment.svg
`floor-2x2` (tile A/B checker) · `wall-x` / `wall-y` · `stairs` · `doorway` · `divider` ·
`shelf` · `plant-large` · `floor-lamp` · `window` (wall-mounted) · `art-frame` · `wall-clock`.
Walls are h110 iso boxes; wall-mounted symbols position against a wall's inner face and cast no
shadow (STYLE.md §2).

## Scale rules
1 world tile = 64×32px. Character 96px. Desk h40+top. Board h~92 at scale 1 (use `scale(0.8)`
against a wall). Never rescale one element without its group — scale whole scenes, not pieces.

## Known limitations (declared, not hidden)
- Characters are 2.5D billboards on the iso floor (Monument Valley convention, STYLE.md §1) —
  they do not rotate to 4 facings; mirroring gives 2.
- Monitor/laptop screens face the viewer even when a character logically faces them (accepted
  stylisation for legibility).
- `skinChars()` is required wherever characters render; without JS a character shows base rig
  + colours but no hair/accessory/garment overlay (acceptable degraded state).
- Emitted SVG uses CSS variables — the host page must include the palette vars
  (`theme_css()`/`characters.css`) for correct colour in both themes.
