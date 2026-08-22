# Sprint Office — Shared Visual Rules (NORMATIVE for every asset)

Art direction (PO-approved 2026-08-21; REFINED per PO feedback same day): clean
flat-isometric, Monument-Valley-inspired geometry, soft shadows, WARM ARCHITECTURAL surfaces,
premium SaaS feel. LIGHT MODE IS THE PRIMARY IDENTITY — cream and warm neutral architecture,
controlled teal and dusty-blue accents, muted terracotta warmth in human/collaboration spaces.
Dark mode is a thoughtful warm-dark interpretation of the SAME world, never the driver.
Original design; no external art assets.

## 0. How coherence is enforced
Every asset is EMITTED BY `scripts/sprint_office_kit.py` from shared helpers — one projection
function, one shade formula, one shadow function, one palette table. Never hand-edit the emitted
`.svg` files; change the generator and re-emit. That is the mechanical guarantee that the office
is one world, not stitched illustrations.

## 1. Isometric system
- Projection: 2:1 pixel isometric. World axes → screen: X=(+1u, +0.5u), Y=(−1u, +0.5u),
  Z=(0, −1u). Unit **u = 32px**. Floor tile = one world unit square → 64×32px diamond.
- ONE camera. No mixed angles, no vanishing points, no rotation of the grid.
- Characters are TRUE ¾-isometric figures (rig v2): drawn in three-quarter view with
  dimensional two-tone shading, jointed limbs (shoulder/elbow/wrist, hip/knee/ankle) and a
  visible near/far side. TWO drawn bases — front-¾ and rear-¾ — each horizontally mirrored,
  giving FOUR facings (SW, SE, NW, NE) so characters can walk every iso direction and sit
  facing their desks (rear view), belonging IN the room rather than pasted onto it.

## 2. Light and shadow
- ONE light source: upper-left of screen (world NW), elevation ~45°.
- Solid shading: top face = base lightened 8%; left face = base; right face = base darkened
  14%. Furniture corners soften via same-colour round-joined strokes. Characters use two-tone
  dimensional shading: near side lit (base), far side shaded (base −16%), one soft head
  highlight.
- Shadows: SOFT — blurred ellipse (gaussian blur ~2.5px) under every grounded object, warm ink
  at 13% (dark: black 30%), offset +6/+3 SE. Wall-mounted objects cast none. Character shadows
  travel with the character during motion.

## 3. Palette
### WARM architecture (v2 — light is the primary identity; dark = warm interpretation)
- Page bg `#F7F4ED` → `#211E19` · panel `#FFFDF8` → `#2A2620` · border `#E8E0D0` → `#3D372E`
- Ink `#322D24` → `#F0EAE0` · dim `#7C7365` → `#A89D8C`
- Floor A `#EFE8D9` → `#2B2721` · B `#E7DFCC` → `#262219`
- Wall front `#F7F2E7` → `#332E26` · side `#EDE5D5` → `#2C2721` · wood oak `#D9BB8E` → `#6B5A42`
- Accents: teal `#3E8E85` · dusty blue `#6C87B8` · DECORATIVE terracotta `#A96B58` (muted;
  human/collaboration spaces ONLY: retro area, meeting, PO nook, soft furnishings) · gold `#C9A227`
### Role colours (garments — restrained, identity also carried by cut + accessory + hair)
- PO `#3A4A66` + gold · SM `#A96B58` (the warm human-glue role) · BA `#3E8E85`
- TechBA `#7D5F9E` · Dev `#5C77AE` · Tester `#6B8A70` · dark theme: each ~+18% light
### 3b. WARMTH vs STATUS
Decorative terracotta (`#A96B58`, dusty rose-brown) is visually distinct from the operational
Test/Warning oranges (`#B45309`/`#D97706`, vivid). Terracotta NEVER appears on tickets, beacons,
stamps or any workflow indicator.
### Status colours (objects ONLY — identical to the sprint board)
- todo `#64748B` · design `#0E7490` · build `#1E40AF` · test `#B45309`
- blocked `#BE123C` · done `#15803D` · shipped = done + gold ribbon `#C9A227`
- warning `#D97706` · destructive `#DC2626`
### 3a. THE SEPARATION RULE
Status colours appear on OBJECTS (tickets, beacons, stamps, markers) and NEVER on clothing.
Role colours appear on CHARACTERS and their personal items and NEVER as status signals.
### Skin & hair (swappable variants, not identities)
- Skin: S1 `#F4CDA9` · S2 `#E0A97C` · S3 `#B07B4C` · S4 `#7A5233`
- Hair: H1 `#2C2A33` · H2 `#5B4433` · H3 `#8C6D4F` · H4 `#C7CDD8` · H5 `#B5502E`

## 4. Dimensions (standard, in px at 1×)
- Character (rig v2): height ~100 standing (~3.7 heads), head 25×27, jointed limbs
  (shoulder/elbow/wrist, hip/knee/ankle as round-capped stroke capsules — real elbows/knees).
  Bases: front-¾ (facing SW) and rear-¾ (facing NE); mirrors give SE/NW. Faces: two eyes
  (far eye smaller — ¾ depth), brows + small mouth with restrained expressions
  (neutral/smile/focus/concern), near ear, blink lids for ambient.
- Desk: footprint 2×1 tiles (128×64 diamond), height 40. Chair: 1×1 tile, seat height 24.
- Monitor: 34×22 screen on 8px stand. Laptop 28×18. Sprint board: 4×0.25 tiles, height 88.
- Tickets: story card 36×24, task card 28×18, corner radius 3. Icons: 16×16 grid.
- Status beacon: 8px sphere on 14px stem.

## 5. Edges, radius, depth
- NO outlines/strokes on solids — edges are made by the three-face shade contrast.
  Permitted strokes: 1.5px ink at 12% for micro-details (keyboard keys, checklist lines).
- Corner radius: furniture 3px on top-face corners; tickets 3px; characters' parts 4px
  (soft, never balloon-round).
- Elevation: objects never float; everything grounds to a tile with its shadow. Stacking order
  = painter's algorithm by (worldX + worldY), emitted back-to-front.

## 6. Line-weight & spacing
- Micro-detail stroke: 1.5px, ink 12%. Focus ring (interactive, later): 2px `#1E40AF`
  light / `#8AACFF` dark, 2px offset.
- Spacing: office composed on the tile grid only; minimum 1 empty tile between furniture
  groups; board wall clearance 1 tile.

## 7. Typography & icons
- UI text: Fira Sans; data/ids: Fira Code (identical to the sprint board).
- In-scene labels: 10–11px Fira Sans Medium, ink colour, never rotated into iso.
- Name chips: rendered by the interface OVER the art (SVG `<text>` in the label layer) —
  NEVER baked into artwork (roles are dynamic; `/sprint crew` renames must cost nothing).
- Icons: 16×16, 1.5px stroke, round caps — check, cross, bug, flame (risk), lock (frozen),
  question (PO decision), flag (shipped), folder, magnifier.

## 8. Accessibility (binding)
- Status is NEVER colour-alone: every status pairs colour + icon + ticket/posture treatment
  (blocked = rose + lock icon + crossed-arms pose + desk beacon, etc.).
- Both themes emitted for every asset (CSS vars; bare `:root` = light, media+data-theme dark).
- Contrast: in-scene labels ≥ 4.5:1 against their chip background.
- Reduced motion: all future animation behind `prefers-reduced-motion`; poses are static art.
- Characters/objects that become interactive get focusable wrappers + focus ring (rule 6).

## 9. Motion layers (PO rule, 2026-08-21 — supersedes "nothing moves without an event")
TWO strictly separated layers:
- **Ambient motion** (non-semantic office life, restrained): breathing, occasional blinking,
  typing while a role is actively working, coffee steam, soft monitor activity, small chair or
  body adjustments, very subtle environmental motion. Ambient motion NEVER moves cards, changes
  statuses, or implies a workflow transition. No wandering, no game-like busywork.
- **Workflow motion** (semantic, event-driven only): walking to the board, moving a ticket,
  hand-offs, delivering defect evidence, going to the PO area, gathering for showcase/retro.
  Every workflow motion corresponds to a real events.jsonl line — motion is evidence.
Characters PHYSICALLY WALK isometric paths between locations (real walk cycle, facing changes,
painter re-layering, shadow carried) — never faded out and re-faded elsewhere. Sit↔stand are
tweened joint transitions. All motion honours prefers-reduced-motion (freeze ambient; workflow
becomes stepped keyframes).

## 10. What "premium, not childish" means here (reviewer checklist)
Muted saturation (no primary-crayon fills) · consistent 3-head proportion (not chibi) ·
restrained faces (eyes + brows + small mouth; expressions subtle, no grins) · restrained accessories (one per role) ·
generous negative space · soft unified shadows · zero clip-art, zero emoji in artwork.
