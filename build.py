#!/usr/bin/env python3
"""Generates the GoF Field Guide: index.html + one page per pattern.
Syntax-checks every Python snippet and validates internal links."""

import html
import re
import sys
import textwrap
from pathlib import Path

from content_creational import PATTERNS as CREATIONAL
from content_structural import PATTERNS as STRUCTURAL
from content_behavioral import PATTERNS as BEHAVIORAL

OUT = Path(__file__).parent
ALL = {p["slug"]: p for p in CREATIONAL + STRUCTURAL + BEHAVIORAL}

# Recommended course order (tier 1 -> 3), drives numbering and prev/next.
COURSE = [
    "strategy", "observer", "factory-method", "singleton", "builder",
    "adapter", "decorator", "facade",
    "command", "template-method", "composite", "state", "proxy",
    "chain-of-responsibility",
    "abstract-factory", "prototype", "bridge", "flyweight", "mediator",
    "memento", "iterator", "visitor", "interpreter",
]
PRIORITY = set(COURSE[:8])
TIERS = [
    ("The everyday eight", "These cover most real-world code. Learn these first.", COURSE[:8]),
    ("The workhorses", "Powerful but situational. Learn once the first eight feel natural.", COURSE[8:14]),
    ("Recognition level", "You mostly need to spot these in other people's code.", COURSE[14:]),
]

CAT_LABEL = {"creational": "Creational", "structural": "Structural", "behavioral": "Behavioral"}

GLYPHS = {
    "factory-method": '<rect x="3" y="9" width="8" height="8" rx="1.5"/><path d="M11 13h4.5"/><path d="M14.3 10.8 16.5 13l-2.2 2.2"/><circle cx="19.3" cy="13" r="2.3"/>',
    "abstract-factory": '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5" stroke-dasharray="2.5 2"/><rect x="13" y="13" width="7" height="7" rx="1.5" stroke-dasharray="2.5 2"/>',
    "singleton": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="2.6" fill="currentColor" stroke="none"/>',
    "builder": '<path d="M4 20h5v-5h5v-5h5V5"/><path d="M17.2 7.2 19 5l1.8 2.2"/>',
    "prototype": '<rect x="9" y="9" width="11" height="11" rx="2" stroke-dasharray="3 2"/><rect x="4" y="4" width="11" height="11" rx="2"/>',
    "adapter": '<rect x="3" y="8" width="7" height="8" rx="1.5"/><circle cx="18.5" cy="12" r="3.4"/><path d="M10 12h1.6l1.4-2 1.6 4 1.2-2h1.3"/>',
    "bridge": '<path d="M4 18V6"/><path d="M20 18V6"/><path d="M4 10h16"/><path d="M4 14.5h16" stroke-dasharray="3 2.2"/>',
    "composite": '<circle cx="12" cy="5.5" r="2.3"/><circle cx="6" cy="17.5" r="2.3"/><circle cx="18" cy="17.5" r="2.3"/><path d="M10.9 7.4 7 15.6M13.1 7.4 17 15.6"/>',
    "decorator": '<rect x="3.5" y="3.5" width="17" height="17" rx="3"/><rect x="7" y="7" width="10" height="10" rx="2"/><rect x="10.3" y="10.3" width="3.4" height="3.4" rx="0.8" fill="currentColor" stroke="none"/>',
    "facade": '<rect x="9" y="4" width="6" height="6" rx="1" stroke-dasharray="2.5 2"/><rect x="15.5" y="7" width="5.5" height="6" rx="1" stroke-dasharray="2.5 2"/><rect x="3" y="9" width="10.5" height="11" rx="1.5"/>',
    "flyweight": '<circle cx="7" cy="12" r="3" fill="currentColor" stroke="none"/><circle cx="17" cy="5.5" r="2.1"/><circle cx="19" cy="12" r="2.1"/><circle cx="17" cy="18.5" r="2.1"/><path d="M9.6 10.7 15 6.7M10 12h6.8M9.6 13.3 15 17.3"/>',
    "proxy": '<rect x="11" y="7" width="9.5" height="10" rx="2" stroke-dasharray="3 2"/><rect x="3.5" y="7" width="9.5" height="10" rx="2"/>',
    "chain-of-responsibility": '<rect x="2.5" y="9" width="5" height="6" rx="1"/><rect x="9.5" y="9" width="5" height="6" rx="1"/><rect x="16.5" y="9" width="5" height="6" rx="1"/><path d="M7.5 12h2M14.5 12h2"/>',
    "command": '<rect x="4" y="4" width="13" height="13" rx="2"/><path d="M9 8.3v4.4l3.8-2.2z" fill="currentColor" stroke="none"/><path d="M18.5 20H9.5"/><path d="M11.6 18 9.4 20l2.2 2"/>',
    "interpreter": '<path d="M12 3.2 15 6.2 12 9.2 9 6.2z"/><path d="M10.8 8.6 6.8 13.6M13.2 8.6 17.2 13.6"/><rect x="4" y="14" width="5.2" height="5.2" rx="1"/><rect x="14.8" y="14" width="5.2" height="5.2" rx="1"/>',
    "iterator": '<circle cx="4.5" cy="16" r="1.7" fill="currentColor" stroke="none"/><circle cx="10" cy="16" r="1.7"/><circle cx="15.5" cy="16" r="1.7"/><circle cx="21" cy="16" r="1.7"/><path d="M4.5 12.5C8 6 16 6 19.6 10.6"/><path d="M19.9 7.6l-.1 3.1-3-.6"/>',
    "mediator": '<circle cx="12" cy="12" r="2.7"/><circle cx="12" cy="3.6" r="1.6" fill="currentColor" stroke="none"/><circle cx="20.4" cy="12" r="1.6" fill="currentColor" stroke="none"/><circle cx="12" cy="20.4" r="1.6" fill="currentColor" stroke="none"/><circle cx="3.6" cy="12" r="1.6" fill="currentColor" stroke="none"/><path d="M12 5.5v3.6M18.5 12h-3.6M12 18.5v-3.6M5.5 12h3.6"/>',
    "memento": '<rect x="4" y="4.5" width="13" height="15" rx="2"/><path d="M7 9h7M7 12.5h7M7 16h4"/><path d="M21.3 7a3.2 3.2 0 1 1-1.1-2.4"/><path d="M20.6 2.7l.2 2.1-2.1.2"/>',
    "observer": '<circle cx="5" cy="12" r="2.6" fill="currentColor" stroke="none"/><path d="M7.5 10.7 16.2 5.7M7.9 12h8.3M7.5 13.3 16.2 18.3"/><circle cx="18.4" cy="5" r="1.9"/><circle cx="18.4" cy="12" r="1.9"/><circle cx="18.4" cy="19" r="1.9"/>',
    "state": '<circle cx="6.5" cy="12" r="3.4"/><circle cx="17.5" cy="12" r="3.4"/><path d="M9.2 9C11 7 13 7 14.8 9"/><path d="M12.9 7.1 15 8.9l-2.5.8"/><path d="M14.8 15C13 17 11 17 9.2 15"/><path d="M11.1 16.9 9 15.1l2.5-.8"/>',
    "strategy": '<rect x="3" y="8" width="9" height="8" rx="1.5"/><path d="M12 12h3.5"/><rect x="16.8" y="4" width="4.4" height="4.4" rx="1" stroke-dasharray="2.4 2"/><rect x="16.8" y="9.8" width="4.4" height="4.4" rx="1"/><rect x="16.8" y="15.6" width="4.4" height="4.4" rx="1" stroke-dasharray="2.4 2"/>',
    "template-method": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M7.5 9h9"/><path d="M7.5 13h9" stroke-dasharray="2.5 2.2"/><path d="M7.5 17h9"/>',
    "visitor": '<rect x="3" y="14.5" width="5" height="5" rx="1"/><rect x="9.5" y="14.5" width="5" height="5" rx="1"/><rect x="16" y="14.5" width="5" height="5" rx="1"/><path d="M4.5 11c3.5-5.5 11.5-5.5 15 0" stroke-dasharray="2.5 2.2"/><circle cx="12" cy="6.4" r="1.8" fill="currentColor" stroke="none"/>',
}


def svg(slug, size):
    return (f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" '
            f'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{GLYPHS[slug]}</svg>')


def code_block(code):
    return f'<pre><code>{html.escape(textwrap.dedent(code).strip("\n"))}</code></pre>'


def check_code(code, where):
    try:
        compile(textwrap.dedent(code), where, "exec")
    except SyntaxError as e:
        print(f"  SYNTAX ERROR in {where}: line {e.lineno}: {e.msg}")
        return False
    return True


def nav_links(i):
    prev_a = next_a = ""
    if i > 0:
        p = ALL[COURSE[i - 1]]
        prev_a = f'<a rel="prev" href="{p["slug"]}.html"><span class="dir">&larr; previous</span>{p["name"]}</a>'
    if i < len(COURSE) - 1:
        n = ALL[COURSE[i + 1]]
        next_a = f'<a rel="next" href="{n["slug"]}.html" style="text-align:right"><span class="dir">next &rarr;</span>{n["name"]}</a>'
    return prev_a, next_a


def render_page(slug, i):
    p = ALL[slug]
    cat = p["category"]
    num = f"{i + 1:02d}"
    ok = True

    body = []
    demo_done = False
    for sec in p["sections"]:
        if sec == "DEMO":
            if p.get("demo"):
                body.append(f'<div class="demo"><span class="label">Try it — live demo</span>{p["demo"]["html"]}</div>')
                demo_done = True
            continue
        heading, prose, code = sec
        if heading:
            body.append(f"<h2>{heading}</h2>")
        if prose:
            body.append(prose)
        if code:
            ok &= check_code(code, f"{slug} / {heading or 'section'}")
            body.append(code_block(code))
    if p.get("demo") and not demo_done:
        body.append(f'<div class="demo"><span class="label">Try it — live demo</span>{p["demo"]["html"]}</div>')

    body.append(f'<div class="box"><span class="label">In the wild</span>{p["wild"]}</div>')
    body.append(f'<div class="box"><span class="label">When not to use it</span>{p["avoid"]}</div>')

    ex = p["exercise"]
    ex_html = [f'<div class="box exercise"><span class="label">Exercise {num}</span>{ex["text"]}']
    if ex.get("code"):
        ok &= check_code(ex["code"], f"{slug} / exercise")
        ex_html.append(code_block(ex["code"]))
    if ex.get("hint"):
        ex_html.append(f'<details><summary>Hint</summary>{ex["hint"]}</details>')
    ex_html.append("</div>")
    body.append("".join(ex_html))

    prev_a, next_a = nav_links(i)
    start = " &middot; Start here" if slug in PRIORITY else ""
    demo_js = f'<script>{p["demo"]["js"]}</script>' if p.get("demo") else ""

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{p["name"]} &middot; GoF Field Guide</title>
<link rel="stylesheet" href="style.css">
</head>
<body style="--cat: var(--{cat})">
<nav class="topnav">
  <div class="crumb"><a href="index.html">GoF field guide</a> &middot; {CAT_LABEL[cat]} &middot; <b>{p["name"]}</b></div>
  <div class="pn">{'<a rel="prev" href="' + ALL[COURSE[i-1]]["slug"] + '.html">&larr; ' + ALL[COURSE[i-1]]["name"] + '</a>' if i > 0 else ''}{'<a rel="next" href="' + ALL[COURSE[i+1]]["slug"] + '.html">' + ALL[COURSE[i+1]]["name"] + ' &rarr;</a>' if i < len(COURSE)-1 else ''}</div>
</nav>
<main>
<header class="card">
  <span class="kicker">Pattern {num} / 23 &middot; {CAT_LABEL[cat]}{start}</span>
  <h1>{p["name"]}</h1>
  <div class="glyph">{svg(slug, 64)}</div>
  <p class="intent">{p["intent"]}</p>
</header>
{"".join(body)}
<p class="review">Done with the exercise? Bring your solution back to Claude for a code review, or ask for a deeper dive on anything here. Tip: use &larr; and &rarr; keys to move between lessons.</p>
<div class="footnav">{prev_a or "<span></span>"}{next_a or "<span></span>"}</div>
</main>
<script src="app.js"></script>
{demo_js}
</body>
</html>"""
    (OUT / f"{slug}.html").write_text(page, encoding="utf-8")
    return ok


def render_index():
    cols = []
    subs = {"creational": "How objects get made &middot; 5 patterns",
            "structural": "How objects fit together &middot; 7 patterns",
            "behavioral": "How objects communicate &middot; 11 patterns"}
    for cat, group in (("creational", CREATIONAL), ("structural", STRUCTURAL), ("behavioral", BEHAVIORAL)):
        chips = []
        for p in sorted(group, key=lambda q: COURSE.index(q["slug"])):
            n = COURSE.index(p["slug"]) + 1
            prio = " priority" if p["slug"] in PRIORITY else ""
            chips.append(
                f'<div class="chip{prio}">'
                f'<a class="chip-link" href="{p["slug"]}.html">'
                f'<span class="num">{n:02d}</span><span class="glyph">{svg(p["slug"], 22)}</span>'
                f'<span class="chip-name">{p["name"]}</span></a>'
                f'<input type="checkbox" data-slug="{p["slug"]}" '
                f'aria-label="Mark {p["name"]} as studied" title="Mark as studied"></div>')
        cols.append(f'<div class="col {cat}"><h2>{CAT_LABEL[cat]}</h2>'
                    f'<p class="sub">{subs[cat]}</p>{"".join(chips)}</div>')

    tiers = []
    for title, blurb, slugs in TIERS:
        links = ", ".join(f'<a href="{s}.html" style="--cat: var(--{ALL[s]["category"]})">{ALL[s]["name"]}</a>' for s in slugs)
        tiers.append(f"<p><strong>{title}.</strong> {blurb}<br>{links}</p>")

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Design Patterns &middot; A Python Field Guide</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<main>
<header class="hero">
  <p class="eyebrow">Gang of Four &middot; 23 patterns &middot; Python edition</p>
  <h1>Design Patterns<br>A Python field guide</h1>
  <p>The 23 classic patterns from <em>Design Patterns: Elements of Reusable
  Object-Oriented Software</em> (Gamma, Helm, Johnson &amp; Vlissides, 1994) &mdash;
  each taught the way a senior architect would: the problem first, then the classic
  solution, then the Pythonic shortcut, real-world sightings, and the cases where
  the honest answer is &ldquo;don&rsquo;t&rdquo;. Every lesson ends with an exercise.
  Work offline, then bring your solutions back to Claude for review.</p>
  <p class="legend">
    <span><span class="dot" style="background: var(--creational)"></span>Creational</span>
    <span><span class="dot" style="background: var(--structural)"></span>Structural</span>
    <span><span class="dot" style="background: var(--behavioral)"></span>Behavioral</span>
    <span>Colored left edge = start here</span>
    <span class="progress" id="progress-count"></span>
  </p>
</header>
<div class="map">{"".join(cols)}</div>
<section class="order">
  <h2>Suggested order</h2>
  <p>Numbers on the cards above follow this path &mdash; frequency of real-world use,
  not book order. Checkboxes track your progress (stored in this browser only).</p>
  {"".join(tiers)}
</section>
</main>
<script src="app.js"></script>
</body>
</html>"""
    (OUT / "index.html").write_text(page, encoding="utf-8")


def check_links():
    ok = True
    for f in OUT.glob("*.html"):
        for href in re.findall(r'href="([^"#]+)"', f.read_text(encoding="utf-8")):
            if href.startswith(("http", "mailto")):
                continue
            if not (OUT / href).exists():
                print(f"  BROKEN LINK in {f.name}: {href}")
                ok = False
    return ok


def main():
    assert len(COURSE) == 23 and set(COURSE) == set(ALL), "course/pattern mismatch"
    all_ok = True
    for i, slug in enumerate(COURSE):
        all_ok &= render_page(slug, i)
    render_index()
    all_ok &= check_links()
    n = len(list(OUT.glob("*.html")))
    print(f"Built {n} HTML pages. {'All checks passed.' if all_ok else 'PROBLEMS FOUND (see above).'}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
