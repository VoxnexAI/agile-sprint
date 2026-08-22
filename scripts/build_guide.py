#!/usr/bin/env python3
"""Build docs/guide.html — the illustrated guide to Agile Sprint.

The visuals are NOT screenshots. The guide embeds the real generator output,
so the office on the page is the same living scene the skill publishes:
characters breathe, blink and type, and the theme button re-lights the room.
That also means the guide can never drift from the product — rebuild it and
it shows today's artwork.

Run: python scripts/build_guide.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sprint_office_kit as K  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs" / "guide.html"
# the live office is emitted beside the guide and embedded in an iframe: it is
# a whole application (ambient engine, screens, controls), so it runs as
# itself rather than being flattened into a still picture
OFFICE_DEMO = OUT.with_name("office-demo.html")

ROLES = [
    ("po", "Product Owner", "You", "swept", "s2", "#5D4632",
     "Priorities, answers, and the only go-live approval."),
    ("sm", "Scrum Master", "Crew", "bob", "s1", "#332F36",
     "Plans and orchestrates. Never builds, never marks work done."),
    ("ba", "Business Analyst", "Crew", "crop", "s3", "#2F2B33",
     "Interviews you in plain business English and writes the stories."),
    ("techba", "Technical BA", "Crew", "bun", "s2", "#332F36",
     "Turns a story into a technical design - and may reject it."),
    ("dev", "Developer", "Crew", "curls", "s4", "#332F36",
     "Builds it, dark by default. Never tests their own work."),
    ("tester", "Tester", "Crew", "short", "s1", "#5D4632",
     "Blind, on a different model. The ONLY one who can call it done."),
]


def cast_row() -> str:
    """The six crew, standing — built from the same rig the office uses."""
    cells = []
    for role, title, kind, hair, skin, hairc, blurb in ROLES:
        fig = (f'<svg viewBox="-46 -132 92 150" width="104" height="170" '
               f'class="role-{role} skin-{skin} hairstyle" style="--hair:{hairc}" '
               f'data-hair="{hair}">{K.iuse("c2-f-stand")}</svg>')
        cells.append(
            f'<figure class="cast"><div class="castart">{fig}</div>'
            f'<figcaption><span class="tag tag-{kind.lower()}">{kind}</span>'
            f'<b>{K.esc(title)}</b><span class="blurb">{K.esc(blurb)}</span>'
            f'</figcaption></figure>')
    return "".join(cells)


def flow_diagram() -> str:
    steps = [("Backlog", "backlog"), ("Groomed", "todo"), ("Design", "design"),
             ("Build", "build"), ("Test", "test"), ("Done", "done"),
             ("Shipped", "done")]
    out = []
    for i, (label, key) in enumerate(steps):
        out.append(f'<span class="step" style="--c:{K.STATUS[key]}">{label}</span>')
        if i < len(steps) - 1:
            out.append('<span class="arrow">&rarr;</span>')
    return "".join(out)


GUIDE_CSS = """
body{padding:0 1.4rem 5rem}
.wrap{max-width:1180px;margin:0 auto}
header.hero{padding:3.2rem 0 1.4rem;text-align:center}
h1{font-size:2.6rem;margin:0 0 .5rem;letter-spacing:-.02em}
.tagline{font-size:1.05rem;color:var(--dim);max-width:62ch;margin:0 auto 1.2rem;line-height:1.6}
h2{font-size:1.3rem;margin:2.6rem 0 .3rem;letter-spacing:-.01em;display:flex;align-items:center;gap:.6rem}
h2::before{content:'';width:.62rem;height:.62rem;border-radius:3px;background:var(--terra);flex:none}
h3{font-size:.95rem;margin:0 0 .35rem}
p,ul{max-width:76ch;line-height:1.65}
.lede{color:var(--dim);max-width:76ch;margin:.1rem 0 1rem;line-height:1.65}
code{font-family:'Fira Code',monospace;font-size:.88em;background:var(--badge-chip);padding:.1em .38em;border-radius:5px}
pre{background:var(--panel);border:1px solid var(--panel-border);border-radius:12px;
  padding:.85rem 1rem;overflow-x:auto;font-family:'Fira Code',monospace;font-size:.8rem;line-height:1.6}
pre code{background:none;padding:0}
.card{background:var(--panel);border:1px solid var(--panel-border);border-radius:16px;
  padding:1rem 1.2rem;box-shadow:0 1px 3px rgba(58,48,36,.07)}
.stage-wrap{display:flex;justify-content:center;overflow-x:auto;background:var(--panel);
  border:1px solid var(--panel-border);border-radius:18px;padding:.5rem;margin:.9rem 0}
.office-frame{background:var(--panel);border:1px solid var(--panel-border);border-radius:18px;
  padding:.4rem;margin:.9rem 0;box-shadow:0 2px 10px rgba(58,48,36,.10)}
.office-frame iframe{width:100%;height:760px;border:0;border-radius:14px;display:block;background:var(--bg)}
@media (max-width:900px){.office-frame iframe{height:560px}}
.castrow{display:flex;gap:.5rem;flex-wrap:wrap;justify-content:center;margin:.9rem 0}
figure.cast{flex:1 1 165px;max-width:190px;margin:0;background:var(--panel);
  border:1px solid var(--panel-border);border-radius:14px;padding:.7rem .6rem;text-align:center}
.castart{background:var(--bg);border-radius:10px;margin-bottom:.4rem}
figure.cast b{display:block;font-size:.86rem;margin:.25rem 0 .2rem}
.blurb{display:block;font-size:.74rem;color:var(--dim);line-height:1.45}
.tag{display:inline-block;font-size:.6rem;font-weight:700;letter-spacing:.09em;
  text-transform:uppercase;border-radius:999px;padding:.1rem .5rem}
.tag-you{background:var(--terra);color:#fff}
.tag-crew{background:var(--badge-chip);color:var(--dim)}
.flow{display:flex;flex-wrap:wrap;align-items:center;gap:.35rem;margin:.6rem 0 1rem}
.step{font-size:.74rem;font-weight:600;border-radius:999px;padding:.2rem .7rem;color:#fff;background:var(--c)}
.arrow{color:var(--dim);font-size:.8rem}
table{border-collapse:collapse;font-size:.83rem;width:100%;margin:.6rem 0;min-width:520px}
th{text-align:left;background:var(--badge-chip);font-weight:600}
th,td{border:1px solid var(--panel-border);padding:.42rem .6rem;vertical-align:top;line-height:1.5}
.tablewrap{overflow-x:auto}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:.8rem;margin:.6rem 0}
.note{border-left:3px solid var(--terra);background:var(--badge-chip);
  border-radius:0 10px 10px 0;padding:.6rem .85rem;font-size:.85rem;margin:.9rem 0;max-width:76ch;line-height:1.6}
.themetoggle{position:fixed;top:.9rem;right:.9rem;font-size:.7rem;padding:.32rem .75rem;
  border-radius:999px;border:1px solid var(--panel-border);background:var(--panel);
  color:var(--ink);cursor:pointer;z-index:9}
.hint{font-size:.76rem;color:var(--dim);text-align:center;margin:.2rem 0 0}
footer{margin-top:3rem;padding-top:1.2rem;border-top:1px solid var(--panel-border);
  font-size:.8rem;color:var(--dim);line-height:1.6}
li{margin:.22rem 0}
"""


def build() -> str:
    fonts = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600'
             '&family=Fira+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">')
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agile Sprint — how it works</title>{fonts}
<style>{K.theme_css()}{GUIDE_CSS}</style></head>
<body>{K.all_defs()}
<button class="themetoggle">theme</button>
<div class="wrap">

<header class="hero">
  <h1>Agile Sprint</h1>
  <p class="tagline">A full agile delivery crew, inside Claude Code. You are the Product Owner.
  They groom, plan, build and test — and nothing ships without your say-so.</p>
</header>

<div class="office-frame">
  <iframe src="office-demo.html" title="A live Sprint Office" loading="eager"></iframe>
</div>
<p class="hint">That office is <b>running</b>, not a screenshot — the crew are breathing, blinking
and typing, and the tabs above them really work. Click into it and have a look around.</p>

<h2>Meet the room</h2>
<p class="lede">Everything in it is driven by your actual sprint files, so nothing on the page can
disagree with the work:</p>
<div class="stage-wrap">{K.scene_svg()}</div>
<p class="hint">The same scene, held still — desks with status beacons, the board on the wall,
the backlog shelf by the door, and the showcase screen by the meeting table.</p>

<h2>The idea in one minute</h2>
<p class="lede">You talk to a Business Analyst in plain English. Stories get written, estimated
independently, and frozen before anyone builds. A developer builds; a <b>different model</b>,
given only the story and its frozen acceptance criteria, decides whether it passes. Work becomes
"done" one way only — by that blind tester saying so.</p>
<div class="flow">{flow_diagram()}</div>
<p class="lede">Every one of those moves is written to an event log, so the board and the office
are never someone's summary of the work — they are the work.</p>

<h2>Who you are working with</h2>
<p class="lede">Six roles. One of them is you, and the crew's names are yours to choose.</p>
<div class="castrow">{cast_row()}</div>
<div class="note"><b>You are always the Product Owner.</b> The tool never stores a person as PO —
it reads whoever is running the sprint. Approval to go live belongs to the delivery's owner, and
can never be clicked: only said, and recorded word for word.</div>

<h2>Naming your crew</h2>
<p class="lede">On first run the skill asks how you want them named:</p>
<div class="grid2">
  <div class="card"><h3>Name them yourself</h3>
    <p class="lede">Give any or all of the five names. Anything you leave out is filled in for
    you, so you never end up with a blank seat.</p></div>
  <div class="card"><h3>Let the system pick</h3>
    <p class="lede">A cast is drawn for you. Each name arrives with its own character — hair,
    colouring, everything — so the person on the board always looks the way the name reads.</p></div>
</div>
<pre><code>python scripts/sprint_crew.py --root sprint --random
python scripts/sprint_crew.py --root sprint --names "SM=Alex,BA=Sam,Dev=Kim"</code></pre>
<p class="lede">Want your own names without changing them for teammates? The <code>crew</code>
phase writes a personal override only you see.</p>

<h2>Getting started</h2>
<pre><code>/plugin marketplace add VoxnexAI/agile-sprint
/plugin install agile-sprint@agile-sprint</code></pre>
<p class="lede">Then, in any repo:</p>
<div class="tablewrap"><table>
<tr><th>Command</th><th>What happens</th></tr>
<tr><td><code>/agile-sprint:sprint</code></td><td>Lists your deliveries and asks which one</td></tr>
<tr><td><code>… &lt;delivery&gt; office</code></td><td><b>The visual way in</b> — publishes the office and hands you the link</td></tr>
<tr><td><code>… &lt;delivery&gt; groom</code></td><td>The BA interviews you and turns ideas into stories</td></tr>
<tr><td><code>… &lt;delivery&gt; plan</code></td><td>Pulls the smallest set that achieves one goal</td></tr>
<tr><td><code>… &lt;delivery&gt; run</code></td><td>Design → build → blind test, story by story</td></tr>
<tr><td><code>… &lt;delivery&gt; showcase</code></td><td>The go-live gate. Your words are recorded verbatim</td></tr>
<tr><td><code>… &lt;delivery&gt; retro</code></td><td>What worked, what didn't, and the velocity line</td></tr>
<tr><td><code>… crew</code></td><td>Rename the crew, just for you</td></tr>
</table></div>

<h2>The office is the app</h2>
<p class="lede">The scene above is the home screen of a small application. The board on the wall,
the shelf by the door and the showcase screen are all clickable, and so is every card:</p>
<ul>
  <li><b>Board</b> — your real columns and cards; click one for its task checklist</li>
  <li><b>Backlog</b> — groomed stories and raw ideas, with risk called out</li>
  <li><b>Sprint</b> — points, the goal, and a timestamped activity feed</li>
  <li><b>Ask the crew</b> — tap what you want next; it is saved on the page as you, and picked up
      next session</li>
</ul>
<div class="note">A tap is a <b>request, not an execution</b>. The crew still run the phase
properly, every gate still applies, and release approval is deliberately not a button.</div>

<h2>What the crew will not do</h2>
<div class="tablewrap"><table>
<tr><th>Rule</th><th>Why it exists</th></tr>
<tr><td>Nobody verifies their own work</td><td>The tester is a fresh, blind session on a different model, and never sees the developer's reasoning</td></tr>
<tr><td>The BA never answers for you</td><td>An open question halts the story rather than being guessed</td></tr>
<tr><td>Acceptance criteria freeze at planning</td><td>Later changes are logged as scope changes and shown at showcase — never silently</td></tr>
<tr><td>Defects are never hidden</td><td>Serious ones block the sprint; anything deferred is listed with your quote accepting it</td></tr>
<tr><td>Your project's own gates are binding</td><td>Type checks, migrations, deploy rules — whatever <code>sprint/RAILS.md</code> says must actually run and pass</td></tr>
</table></div>

<h2>Where things live</h2>
<div class="tablewrap"><table>
<tr><th>What</th><th>Where</th><th>Why</th></tr>
<tr><td>The engine — laws, phases, renderers</td><td>this plugin</td><td>Generic and reusable; updating it never touches your project</td></tr>
<tr><td>Your gates — <code>sprint/RAILS.md</code></td><td>your project</td><td>Every project's rules differ</td></tr>
<tr><td>Delivery state — stories, sprints, events</td><td>your project</td><td>It is your record, and belongs in your history</td></tr>
</table></div>
<p class="lede">Plain files, all of it. Any session picks up where the last one stopped by reading
them — nothing important lives only in a conversation.</p>

<footer>Agile Sprint · the office above is generated by the same code that publishes your sprint
office, so this page always shows the current artwork.</footer>
</div>
<script>{K.skin_js()}
{K.TOGGLE_JS}</script>
</body></html>"""


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    office = K.office_html(None)          # the demo office: no project state
    OFFICE_DEMO.write_text(office, encoding="utf-8", newline="\n")
    print(f"emitted {OFFICE_DEMO} ({len(office):,} bytes)")
    html = build()
    OUT.write_text(html, encoding="utf-8", newline="\n")
    print(f"emitted {OUT} ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
