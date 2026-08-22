#!/usr/bin/env python3
"""
Choose where each hotspot card opens, and how many columns it uses.

    python src/build.py && python src/optimize_cards.py && python src/build.py

Why this exists
---------------
A legible information card is 26-44% of the page wide. Pages 3 and 4 are dense,
so a card cannot avoid the artwork entirely. Rather than eyeballing nine
positions, this scores every candidate placement against the *actual rendered
artwork* and picks the least damaging one:

  * covering the journey ribbon costs nothing (it is flat colour)
  * covering text, line-art icons or the logo is heavily penalised
  * covering another star is effectively forbidden (it would block that hotspot)
  * the card must stay adjacent to its own star, and never cover it —
    adjacency is weighted heavily, so a near-tie in coverage never wins by
    parking the card halfway across the page

Each card is tried in three layout widths (1, 2 and 3 -> 26cqw / 33cqw / 44cqw),
because a wider, shorter card often fits a gap that a narrow, tall one cannot.

Outputs src/data/card-placement.json  -> {id: {px, py, cols}}  (percent of page)
        src/data/card-variants.json   -> measured card sizes, for reference
        docs/screenshots/placement-page[34].png -> visual audit of the result

Star geometry is read straight out of src/template.html so there is only ever one
source of truth for where the stars are.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
TEMPLATE = SRC / "template.html"
INDEX = ROOT / "index.html"
PLACEMENT_OUT = SRC / "data" / "card-placement.json"
VARIANTS_OUT = SRC / "data" / "card-variants.json"
AUDIT_DIR = ROOT / "docs" / "screenshots"

REF_W, REF_H = 1440, 810        # reference render size (the PDF's page box)
MEASURE_VIEWPORT = (1600, 950)  # card sizes are measured here (tightest common case)

W_DETAIL = 30.0     # per-pixel cost of covering text / icons / logo
W_RIBBON = 0.0      # covering the flat journey path is acceptable
W_STAR = 4000.0     # never cover another hotspot's star
W_GAP = 120.0       # per-pixel cost of drifting away from the star it belongs to
W_DIST = 1.4        # mild pull towards the star's centre, to break ties
GAP_MAX_FRACTION = 0.045   # a card may sit at most this far from its star
DETAIL_MAX_SIDE = 120   # a component this small is a glyph or icon stroke
DETAIL_MAX_FILL = 0.30  # ...or this hollow, i.e. an outline rather than a solid


def star_geometry() -> dict[int, dict[str, dict]]:
    """Parse the PAGES array in template.html for star ids and geometry."""
    text = TEMPLATE.read_text(encoding="utf-8")
    chunks = re.split(r'art:"__P(\d)__"', text)
    pattern = re.compile(
        r'id:"([a-z0-9-]+)"\s*,\s*\n\s*cx:\s*([\d.]+)\s*,\s*cy:\s*([\d.]+)\s*,'
        r'\s*w:\s*([\d.]+)\s*,\s*h:\s*([\d.]+)\s*,')
    pages: dict[int, dict[str, dict]] = {}
    for i in range(1, len(chunks), 2):
        page_no = int(chunks[i])
        found = {m.group(1): {"cx": float(m.group(2)), "cy": float(m.group(3)),
                              "w": float(m.group(4)), "h": float(m.group(5))}
                 for m in pattern.finditer(chunks[i + 1])}
        if found:
            pages[page_no] = found
    if not pages:
        raise SystemExit("error: no star geometry found in src/template.html")
    return pages


def measure_variants(playwright) -> dict:
    """Render index.html and record each card's size in each layout width."""
    browser = playwright.chromium.launch(args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": MEASURE_VIEWPORT[0], "height": MEASURE_VIEWPORT[1]})
    page.goto(INDEX.as_uri())
    page.wait_for_timeout(800)
    result = page.evaluate("""() => {
      const stage = document.getElementById('stage').getBoundingClientRect();
      const out = {stage: {w: stage.width, h: stage.height}, variants: {}};
      document.querySelectorAll('.card').forEach(card => {
        const id = card.id.replace('card-', '');
        out.variants[id] = {};
        [1, 2, 3].forEach(cols => {
          card.dataset.cols = String(cols);
          card.hidden = false;
          card.style.left = '0px';
          card.style.top = '0px';
          void card.offsetHeight;
          out.variants[id][cols] = {
            wpct: card.offsetWidth / stage.width * 100,
            hpct: card.offsetHeight / stage.height * 100,
          };
          card.hidden = true;
        });
      });
      return out;
    }""")
    browser.close()
    return result


def render_page(playwright, page_no: int) -> "numpy.ndarray":
    import numpy as np
    from PIL import Image
    svg = SRC / "assets" / "pages" / f"page{page_no}.svg"
    browser = playwright.chromium.launch(args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": REF_W, "height": REF_H}, device_scale_factor=1)
    page.goto(svg.as_uri())
    page.wait_for_timeout(400)
    shot = page.screenshot()
    browser.close()
    import io
    return np.asarray(Image.open(io.BytesIO(shot)).convert("RGB"), dtype=int)


def weight_map(arr, stars: dict[str, dict]):
    """Classify every non-white pixel as ribbon (free) or detail (expensive)."""
    import numpy as np
    from scipy import ndimage

    non_white = arr.sum(axis=2) < 735
    labels, count = ndimage.label(non_white)
    areas = ndimage.sum(non_white, labels, range(1, count + 1))
    lut = np.zeros(count + 1, dtype=np.float32)
    for i, box in enumerate(ndimage.find_objects(labels), start=1):
        ys, xs = box
        bw, bh = xs.stop - xs.start, ys.stop - ys.start
        fill = areas[i - 1] / max(1, bw * bh)
        is_detail = max(bw, bh) <= DETAIL_MAX_SIDE or fill < DETAIL_MAX_FILL
        lut[i] = W_DETAIL if is_detail else W_RIBBON
    weights = lut[labels]
    detail = weights >= W_DETAIL

    height, width = arr.shape[:2]
    for star in stars.values():
        x0 = int((star["cx"] - star["w"] / 2) / 100 * width)
        x1 = int((star["cx"] + star["w"] / 2) / 100 * width)
        y0 = int((star["cy"] - star["h"] / 2) / 100 * height)
        y1 = int((star["cy"] + star["h"] / 2) / 100 * height)
        weights[max(0, y0):y1, max(0, x0):x1] = W_STAR
    return weights, detail


def integral(a):
    import numpy as np
    return np.pad(a.astype(np.float64), ((1, 0), (1, 0))).cumsum(0).cumsum(1)


def area_sum(table, x0, y0, x1, y1):
    return table[y1, x1] - table[y0, x1] - table[y1, x0] + table[y0, x0]


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
        import numpy  # noqa: F401
        import scipy  # noqa: F401
        from PIL import Image, ImageDraw
    except ImportError as exc:
        print(f"error: {exc}. Install with: pip install -r tests/requirements.txt", file=sys.stderr)
        return 1

    if not INDEX.exists():
        print("error: index.html not found — run `python src/build.py` first.", file=sys.stderr)
        return 1

    geometry = star_geometry()
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    plan: dict[str, dict] = {}

    with sync_playwright() as playwright:
        measured = measure_variants(playwright)
        VARIANTS_OUT.write_text(json.dumps(measured, indent=1) + "\n", encoding="utf-8")
        variants = measured["variants"]
        print(f"card sizes measured at {MEASURE_VIEWPORT[0]}x{MEASURE_VIEWPORT[1]}"
              f" (stage {measured['stage']['w']:.0f}x{measured['stage']['h']:.0f})")

        for page_no, stars in sorted(geometry.items()):
            arr = render_page(playwright, page_no)
            height, width = arr.shape[:2]
            weights, detail = weight_map(arr, stars)
            table, detail_table = integral(weights), integral(detail)
            print(f"page {page_no}: {int(detail.sum())} detail px")

            audit = Image.fromarray(arr.astype("uint8"))
            draw = ImageDraw.Draw(audit)

            for key, star in stars.items():
                if key not in variants:
                    print(f"  warning: no measured card for '{key}', skipped")
                    continue
                scx, scy = star["cx"] / 100 * width, star["cy"] / 100 * height
                sw, sh = star["w"] / 100 * width, star["h"] / 100 * height
                sx0, sy0, sx1, sy1 = scx - sw / 2, scy - sh / 2, scx + sw / 2, scy + sh / 2
                margin, pad = int(0.008 * width), 0.005 * width
                gap_max = GAP_MAX_FRACTION * width

                best = None
                for cols in (1, 2, 3):
                    variant = variants[key][str(cols)]
                    cw = int(round(variant["wpct"] / 100 * width))
                    ch = int(round(variant["hpct"] / 100 * height))
                    if cw > width - 2 * margin or ch > height - 2 * margin:
                        continue
                    for y0 in range(margin, height - ch - margin + 1, 2):
                        for x0 in range(margin, width - cw - margin + 1, 2):
                            x1, y1 = x0 + cw, y0 + ch
                            if not (x1 < sx0 - pad or x0 > sx1 + pad
                                    or y1 < sy0 - pad or y0 > sy1 + pad):
                                continue        # would cover its own star
                            gx = max(sx0 - x1, x0 - sx1, 0.0)
                            gy = max(sy0 - y1, y0 - sy1, 0.0)
                            gap = (gx * gx + gy * gy) ** 0.5
                            if gap > gap_max:
                                continue        # too far from its star
                            cost = area_sum(table, x0, y0, x1, y1)
                            dist = ((x0 + cw / 2 - scx) ** 2 + (y0 + ch / 2 - scy) ** 2) ** 0.5
                            score = cost + W_GAP * gap + W_DIST * dist
                            if best is None or score < best[0]:
                                best = (score, cols, x0, y0, cw, ch, gap)

                if best is None:
                    print(f"  warning: no valid placement for '{key}'")
                    continue
                _, cols, x0, y0, cw, ch, gap = best
                covered = area_sum(detail_table, x0, y0, x0 + cw, y0 + ch)
                plan[key] = {"px": round(x0 / width * 100, 3),
                             "py": round(y0 / height * 100, 3),
                             "cols": cols}
                print(f"  {key:30s} {cols}col at ({plan[key]['px']:6.2f}%,{plan[key]['py']:6.2f}%) "
                      f"detail covered={covered:6.0f}px gap={gap:4.1f}px")
                draw.rectangle([x0, y0, x0 + cw, y0 + ch], outline=(0, 45, 114), width=4)
                draw.rectangle([sx0, sy0, sx1, sy1], outline=(254, 112, 2), width=3)

            audit.save(AUDIT_DIR / f"placement-page{page_no}.png")

    PLACEMENT_OUT.write_text(json.dumps(plan, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {PLACEMENT_OUT.relative_to(ROOT)} — now run `python src/build.py`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
