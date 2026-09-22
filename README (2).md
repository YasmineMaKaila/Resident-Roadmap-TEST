# The Resident Roadmap — Interactive

An interactive conversion of Cortland's four-page *Resident Roadmap* PDF: the same
artwork, the same words, plus nine "Learn More" hotspots that were previously
locked inside the PDF's form fields.

**One file, no dependencies, no build step to view.** Open `index.html` in any
modern browser — from disk, a shared drive, an intranet or GitHub Pages. It makes
zero external requests, so it works offline.

> ⚠️ Internal Cortland material. Read [`NOTICE.md`](NOTICE.md) before making this
> repository or its Pages site public.

![The full Resident Roadmap overview](docs/screenshots/01-overview.png)

---

## Contents

- [What it does](#what-it-does)
- [Viewing it](#viewing-it)
- [How it was built](#how-it-was-built)
- [Repository layout](#repository-layout)
- [Rebuilding](#rebuilding)
- [Tests](#tests)
- [Accessibility](#accessibility)
- [Printing](#printing)
- [Browser support](#browser-support)
- [Before you share this](#before-you-share-this)

---

## What it does

All four pages of the source PDF, in order, with tab and Previous/Next navigation:

| # | Page |
|---|------|
| 1 | Full Resident Roadmap overview |
| 2 | The Beginning · Touring · Following Up |
| 3 | Applying · Application Communication · The Approval |
| 4 | Get Ready to Move · Welcome Home · Smooth Sailing |

The nine orange stars on pages 3 and 4 are live hotspots. Hover, focus or tap one
and its information card opens beside it; the artwork fades back so the card stays
easy to read.

| Hotspot | Page |
|---|---|
| Application Process · Leasing Process & Changes · Documentation Requirements | 3 |
| Special Programs & Vouchers · Qualifiying & Verifiying Income · Concessions & Pricing | 3 |
| Common Scenarios & Troubleshooting · Resident & Lease Management · Rental History, Screening, & Credit | 4 |

<sub>"Qualifiying & Verifiying" is misspelled **in the source PDF** and is reproduced
verbatim. See [`docs/SOURCE-CONTENT-NOTES.md`](docs/SOURCE-CONTENT-NOTES.md).</sub>

![An information card open on page 3](docs/screenshots/02-hotspot-card.png)

Every card starts closed on every page — including Concessions & Pricing, which was
saved in an open state in the original PDF.

---

## Viewing it

**Locally** — download `index.html` and double-click it. That is the whole product.

**GitHub Pages** — the `deploy to github pages` workflow publishes it on every push
to `main`. Enable it once under **Settings → Pages → Build and deployment →
Source: GitHub Actions**. The URL will be:

```
https://<org-or-user>.github.io/<repo-name>/
```

**Anywhere else** — copy `index.html` to any web server, SharePoint library or
file share. It is a single static file with nothing to configure.

---

## How it was built

Four decisions are worth knowing, because they are why it looks and behaves the way
it does.

**1. The pages are the PDF's own vectors, not screenshots.** Each page was exported
to SVG, so the journey path, its colour segments, the line-art icons, the type and
the Cortland logo are all the original vector artwork. Nothing was redrawn or
rasterised, and it stays sharp at any zoom and in print. A pixel comparison against
the source PDF shows differences only in 1-px anti-aliasing halos.

**2. The hotspot copy came out of the PDF's form fields.** The nine cards were not
text objects — they were JPEGs baked into hidden AcroForm widget appearances named
`<Topic> PNG_af_image`, shown and hidden by mouse-enter/mouse-exit actions on the
matching `Learn More: <Topic>` fields. Those images were extracted (they are kept in
[`docs/hotspot-source-images/`](docs/hotspot-source-images) as the evidence trail),
transcribed, and are asserted character-for-character by
[`tests/test_content.py`](tests/test_content.py).

**3. The orange stars are live SVG, not part of the background.** They also lived in
the widget appearances, so exporting a clean page removed them — which is what we
wanted. Their geometry was measured from the PDF and they are re-drawn as real SVG
buttons, so they can carry hover, focus and tap states. They land within 0.06% of
the page (sub-pixel) of where the PDF put them.

**4. Card placement is computed, not eyeballed.** A legible card is 26–44% of the
page wide and these pages are dense, so a card cannot avoid the artwork entirely.
[`src/optimize_cards.py`](src/optimize_cards.py) scores every candidate position
against the actual rendered artwork — covering the flat journey ribbon is free,
covering text or icons is expensive, covering another star is forbidden — and tries
three card widths per hotspot. Because some overlap is unavoidable, opening a card
also fades the artwork, which keeps the card readable and makes the overlap read as
a deliberate focus state. The star you are pointing at always stays visible.

The optimiser writes a visual audit so its choices can be checked by eye:

![Computed card placement, page 3](docs/screenshots/placement-page3.png)

---

## Repository layout

```
index.html                     the deliverable — self-contained, also what Pages serves
src/
  template.html                authoring source: markup, CSS, JS, card copy, star geometry
  build.py                     template + artwork -> index.html
  extract_from_pdf.py          re-extract artwork, hotspot images and star geometry from the PDF
  optimize_cards.py            choose each card's position and column layout
  assets/pages/page[1-4].svg   vector artwork lifted from the PDF
  data/card-placement.json     computed {px, py, cols} per hotspot
  data/card-variants.json      measured card sizes (optimiser input, for reference)
tests/
  conftest.py                  shared Playwright fixtures
  test_interactions.py         hover, keyboard, touch, responsive layout, print
  test_content.py              card copy vs the PDF, emphasis, palette hexes
  requirements.txt             build + test toolchain
docs/
  SOURCE-CONTENT-NOTES.md      source errors and conversion decisions — read this
  hotspot-source-images/       the nine card JPEGs pulled from the PDF
  print-sample.pdf             what Ctrl/Cmd-P produces
  screenshots/
.github/workflows/
  test.yml                     build, staleness check, full suite, self-containment check
  deploy-pages.yml             publish index.html to GitHub Pages
```

`index.html` is generated, but it **is committed on purpose** — it is the product and
what GitHub Pages serves. CI fails if it drifts out of sync with `src/`.

---

## Rebuilding

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r tests/requirements.txt
python -m playwright install chromium

python src/build.py          # src/template.html -> index.html
```

To change wording, styling or behaviour, edit `src/template.html` and rebuild —
never edit `index.html` directly, as the next build overwrites it.

To re-run the card placement optimiser (needed only if card copy or sizing changes):

```bash
python src/build.py && python src/optimize_cards.py && python src/build.py
```

The double build is deliberate: the optimiser measures the real rendered card sizes
from `index.html`, then the second build bakes its answer back in.

If the master PDF is ever reissued:

```bash
python src/extract_from_pdf.py /path/to/The_Resident_Roadmap_Final_July2026.pdf
```

That refreshes the page artwork, the hotspot images and the measured star geometry.
Card copy and star coordinates live in `src/template.html` and must be updated there
to match — the tests will tell you if they disagree.

---

## Tests

```bash
pytest tests/ -v
```

Roughly 90 checks across two files, all headless Chromium:

- all nine cards closed on load, one open at a time, none clipped
- hover opens, stays open across the gap to the card, closes when the pointer leaves both
- Tab reaches every star and opens its card; Enter and Space toggle; Escape closes and
  returns focus to the star; `aria-expanded` tracks state
- tap opens and the close button dismisses, on tablet and phone
- every card lands inside the document and clear of its own star, at every size
- 14 viewports from 2560×1440 to 360×740: exact 16:9 document, no overlap between
  title, brand label, tabs, document, nav control and dots, no horizontal scrolling
- card copy matches the PDF word for word; bold and italic emphasis intact; the source
  misspellings are asserted as *still present*, so nobody "fixes" them by accident
- the palette hexes are exactly `#002D72`, `#8FAD15`, `#A9C23F`
- print media hides the interface and shows four clean pages

Test against another build without touching the repo:

```bash
ROADMAP_HTML=/path/to/other.html pytest tests/ -v
```

---

## Accessibility

- Fully keyboard operable: Tab to each star, Enter/Space to open, Escape to close,
  arrow keys to change page, and a skip link to the document.
- Stars are real `<button>`s with `aria-expanded` and `aria-controls`; cards are
  labelled `role="dialog"` with a labelled close button.
- Because the artwork is vector *outlines*, its text is not machine-readable. Each
  page therefore carries a screen-reader transcript of its own copy, verbatim.
- On phones that transcript becomes visible, colour-coded body text — at a 16:9
  landscape page scaled to a 390 px screen the artwork's own type is only a few
  pixels tall, so the readable text is the point.
- Visible focus rings throughout; `prefers-reduced-motion` disables transitions.

| Desktop, keyboard focus | Phone | Phone, card open |
|---|---|---|
| ![Keyboard focus state](docs/screenshots/03-keyboard-focus.png) | ![Phone layout](docs/screenshots/04-phone.png) | ![Phone bottom sheet](docs/screenshots/05-phone-sheet.png) |

---

## Printing

Ctrl/Cmd-P gives four clean landscape sheets, one page each, with the interface,
stars and cards suppressed. Sample: [`docs/print-sample.pdf`](docs/print-sample.pdf).
Choose landscape and enable background graphics.

---

## Browser support

Current Chrome, Edge, Safari and Firefox on desktop, iOS and Android.

It leans on `aspect-ratio`, CSS container queries, `dvh` units and `:focus-visible`
— all baseline in browsers from 2023 onward. It will **not** render correctly in
Internet Explorer. If a card ever renders at the wrong size, the container-query
fallback is a two-column card, which is still perfectly readable.

---

## Before you share this

1. Read [`docs/SOURCE-CONTENT-NOTES.md`](docs/SOURCE-CONTENT-NOTES.md). The
   information cards reproduce the source PDF exactly, errors included — a visible
   misspelling in a card heading, a subject/verb disagreement in the income card,
   two asterisk footnotes with no footnote text anywhere, and one voucher statement
   that may deserve a legal read.
2. Read [`NOTICE.md`](NOTICE.md). This is Cortland brand and policy content, and
   GitHub Pages is a public URL.
