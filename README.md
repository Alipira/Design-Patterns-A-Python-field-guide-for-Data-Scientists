# Design Patterns — A Python Field Guide

The 23 Gang of Four design patterns, each taught the way a senior architect
would: the problem first, then the classic solution, then the Pythonic
shortcut, real standard-library sightings, and the cases where the honest
answer is "don't." Every lesson ends with an exercise.

A static site — no build step or server required to read it. Just open
`index.html`.

## Read it

**Online:** once GitHub Pages is enabled (see below), the guide lives at
`https://<your-username>.github.io/<repo-name>/`.

**Offline:** clone or download the repo and open `index.html` in any browser.
Works from `file://` — no internet needed. Respects your system's dark mode,
tracks your progress in the browser, and supports ← / → arrow-key navigation
between lessons.

## Enable GitHub Pages

1. Push this repo to GitHub (see below).
2. On GitHub: **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to *Deploy from a branch*.
4. Choose branch **`main`** and folder **`/ (root)`**, then **Save**.
5. Wait ~1 minute; your site appears at the URL shown on that page.

The `.nojekyll` file tells Pages to serve the files as-is rather than running
them through Jekyll.

## Project structure

    index.html            Pattern map, learning order, progress tracker
    <pattern>.html        One page per pattern (23 total)
    style.css             Shared styles (light + dark)
    app.js                Syntax highlighting, progress, keyboard nav
    build.py              Regenerates every HTML page
    content_*.py          Lesson content, one module per pattern category

## Editing

The HTML pages are generated. To change a lesson, edit the relevant
`content_*.py` file and rebuild:

    python3 build.py

The build script syntax-checks every Python snippet and validates all internal
links before writing the pages, so a green build means the site is consistent.

## Credits

Patterns from *Design Patterns: Elements of Reusable Object-Oriented Software*
(Gamma, Helm, Johnson & Vlissides, 1994). Examples and commentary are original,
written for Python.
