#!/usr/bin/env python3
"""
Re-extract the source assets from the original Resident Roadmap PDF.

    python src/extract_from_pdf.py path/to/The_Resident_Roadmap_Final_July2026.pdf

You only need this if the master PDF changes. The extracted assets are already
committed under src/assets/, so a normal build does not require the PDF (which is
deliberately not in this repo — see NOTICE.md).

What it does, and why
---------------------
1. The four pages are exported as SVG so the journey path, line-art icons, type
   and the Cortland logo stay as the original vectors — nothing is redrawn or
   rasterised.

2. The orange stars and the nine "Learn More" cards are NOT page content. They
   live in AcroForm widget appearance streams:
       "<Topic> PNG_af_image"     -> a JPEG of the rendered information card
       "Learn More: <Topic>"      -> the orange star, plus the card in its "on" state
   Deleting every widget therefore strips the stars too, which is what we want:
   the exported SVG is a clean page, and the app re-draws the stars as live SVG
   so they can carry hover / focus / tap states.

3. The star geometry is recovered by rendering the page with only the star
   appearances visible and measuring the orange blobs, so the live stars land
   exactly where the PDF put them.

4. The card JPEGs are written out as the evidence trail for the transcribed copy
   (docs/hotspot-source-images/).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
PAGES_OUT = SRC / "assets" / "pages"
CARDS_OUT = ROOT / "docs" / "hotspot-source-images"
STARS_OUT = SRC / "data" / "star-geometry.json"

PAGE_W, PAGE_H = 1440.0, 810.0          # the PDF's own page box, in points
ORANGE_MIN_AREA = 3000                   # ignore anti-aliasing specks


def export_clean_pages(doc) -> None:
    """Every widget removed -> page artwork only, as SVG with text as outlines."""
    import pymupdf as fitz  # noqa: F401  (imported for the side-effect of being installed)

    PAGES_OUT.mkdir(parents=True, exist_ok=True)
    for page in doc:
        for widget in list(page.widgets() or []):
            page.delete_widget(widget)
        annot = page.first_annot
        while annot:
            annot = page.delete_annot(annot)

    for index, page in enumerate(doc, start=1):
        # text_as_path keeps TT Norms Pro as outlines: pixel-faithful and no font
        # licensing problem, at the cost of the text not being selectable.
        svg = page.get_svg_image(text_as_path=True)
        out = PAGES_OUT / f"page{index}.svg"
        out.write_text(svg, encoding="utf-8")
        print(f"  page {index}: {out.relative_to(ROOT)}  ({len(svg) / 1024:.0f} KB)")


def export_card_images(doc) -> None:
    """Pull the JPEG baked into each hidden *_PNG_af_image widget appearance."""
    import pypdf

    CARDS_OUT.mkdir(parents=True, exist_ok=True)
    reader = pypdf.PdfReader(str(doc))

    def first_image(resources):
        resources = resources.get_object()
        xobjects = resources.get("/XObject")
        if not xobjects:
            return None
        for value in xobjects.get_object().values():
            obj = value.get_object()
            if obj.get("/Subtype") == "/Form":
                found = first_image(obj.get("/Resources"))
                if found is not None:
                    return found
            elif obj.get("/Subtype") == "/Image":
                return obj
        return None

    count = 0
    for page in reader.pages:
        annots = page.get("/Annots")
        if not annots:
            continue
        for ref in annots.get_object():
            obj = ref.get_object()
            name = str(obj.get("/T") or "")
            if "PNG_af_image" not in name:
                continue
            appearance = obj.get("/AP")
            if not appearance or "/N" not in appearance:
                continue
            image = first_image(appearance["/N"].get_object().get("/Resources"))
            if image is None:
                continue
            stem = (name.replace(" PNG_af_image", "")
                        .replace(" ", "_").replace("&", "and").replace(",", "").replace("/", "-"))
            target = CARDS_OUT / f"{stem}.jpg"
            target.write_bytes(image.get_data())
            count += 1
            print(f"  card: {target.relative_to(ROOT)}")
    print(f"  {count} hotspot card images written")


def measure_stars(pdf_path: Path) -> dict:
    """Render each page with only the star appearances visible, then measure them."""
    import numpy as np
    import pymupdf as fitz
    from PIL import Image
    from scipy import ndimage

    doc = fitz.open(str(pdf_path))
    scale = 2.0
    geometry: dict[str, list[dict]] = {}

    for index, page in enumerate(doc, start=1):
        widgets = list(page.widgets() or [])
        if not widgets:
            continue

        # Hide the card artwork; keep the "Learn More" widgets, which draw the stars.
        for widget in widgets:
            if "PNG_af_image" in widget.field_name:
                widget.field_display = 1  # hidden
                widget.update()

        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        arr = np.asarray(Image.frombytes("RGB", (pix.width, pix.height), pix.samples), dtype=int)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        mask = (r > 200) & (g > 60) & (g < 160) & (b < 80)      # the #FF6F01 stars
        labels, _ = ndimage.label(mask)

        found = []
        for label, box in enumerate(ndimage.find_objects(labels), start=1):
            if (labels[box] == label).sum() < ORANGE_MIN_AREA:
                continue
            ys, xs = box
            found.append({
                "cx": round((xs.start + xs.stop) / 2 / pix.width * 100, 3),
                "cy": round((ys.start + ys.stop) / 2 / pix.height * 100, 3),
                "w": round((xs.stop - xs.start) / pix.width * 100, 3),
                "h": round((ys.stop - ys.start) / pix.height * 100, 3),
            })

        # Match each star to the "Learn More" widget centred on it.
        named = []
        for widget in widgets:
            if not widget.field_name.startswith("Learn More"):
                continue
            rect = widget.rect
            wx = (rect.x0 + rect.x1) / 2 / PAGE_W * 100
            wy = (rect.y0 + rect.y1) / 2 / PAGE_H * 100
            nearest = min(found, key=lambda s: (s["cx"] - wx) ** 2 + (s["cy"] - wy) ** 2)
            named.append({"field": widget.field_name, **nearest})

        if named:
            geometry[f"page{index}"] = named
            print(f"  page {index}: {len(named)} stars measured")

    return geometry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf", type=Path, help="the original Resident Roadmap PDF")
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"error: {args.pdf} not found", file=sys.stderr)
        return 1

    try:
        import pymupdf  # noqa: F401
        import pypdf  # noqa: F401
        import numpy  # noqa: F401
        import scipy  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError as exc:
        print(f"error: {exc}. Install with: pip install -r tests/requirements.txt", file=sys.stderr)
        return 1

    import pymupdf as fitz

    print("star geometry")
    stars = measure_stars(args.pdf)
    STARS_OUT.parent.mkdir(parents=True, exist_ok=True)
    STARS_OUT.write_text(json.dumps(stars, indent=2) + "\n", encoding="utf-8")
    print(f"  -> {STARS_OUT.relative_to(ROOT)}")

    print("hotspot card images")
    export_card_images(args.pdf)

    print("clean page artwork")
    export_clean_pages(fitz.open(str(args.pdf)))

    print("\nDone. Star geometry in src/template.html must match star-geometry.json;\n"
          "if the PDF's stars moved, update the PAGES array in the template, then run:\n"
          "  python src/optimize_cards.py && python src/build.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
