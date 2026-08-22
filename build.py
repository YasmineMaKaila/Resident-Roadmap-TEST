#!/usr/bin/env python3
"""
Build the single, self-contained interactive file.

    python src/build.py

Reads  src/template.html
       src/assets/pages/page[1-4].svg     (vector artwork lifted from the PDF)
       src/data/card-placement.json       (per-hotspot card position + layout)
Writes index.html                          (repo root — this is what GitHub Pages serves)

The output has no external references: the artwork is inlined as base64 SVG data
URIs, and all CSS/JS is inline. It runs from a file:// path, a shared drive or a
web server with no build step and no network access.
"""
from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent

TEMPLATE = SRC / "template.html"
PAGES = [SRC / "assets" / "pages" / f"page{i}.svg" for i in range(1, 5)]
PLACEMENT = SRC / "data" / "card-placement.json"
OUTPUT = ROOT / "index.html"


def data_uri(path: Path) -> str:
    """Inline an SVG file as a base64 data URI."""
    return "data:image/svg+xml;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def main() -> int:
    missing = [p for p in [TEMPLATE, *PAGES] if not p.exists()]
    if missing:
        for p in missing:
            print(f"error: missing required input {p.relative_to(ROOT)}", file=sys.stderr)
        return 1

    html = TEMPLATE.read_text(encoding="utf-8")

    for index, svg in enumerate(PAGES, start=1):
        html = html.replace(f"__P{index}__", data_uri(svg))

    plan = json.loads(PLACEMENT.read_text(encoding="utf-8")) if PLACEMENT.exists() else {}
    positions = {k: {"px": v["px"], "py": v["py"]} for k, v in plan.items() if "px" in v}
    layouts = {k: v.get("cols", 2) for k, v in plan.items()}

    html = html.replace("__CARDPOS__", json.dumps(positions, separators=(",", ":")))
    html = html.replace("__CARDLAYOUT__", json.dumps(layouts, separators=(",", ":")))

    leftovers = [token for token in ("__P1__", "__P2__", "__P3__", "__P4__",
                                    "__CARDPOS__", "__CARDLAYOUT__") if token in html]
    if leftovers:
        print(f"error: unreplaced placeholders {leftovers}", file=sys.stderr)
        return 1

    OUTPUT.write_text(html, encoding="utf-8")
    print(f"built {OUTPUT.relative_to(ROOT)}  ({len(html) / 1024:.0f} KB, "
          f"{len(positions)} hotspots, 0 external requests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
