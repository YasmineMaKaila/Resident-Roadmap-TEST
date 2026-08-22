# The Resident Roadmap — Source Content Notes for Review

Everything below was found in the source PDF (`The_Resident_Roadmap_Final_July2026`). **All original wording, spelling, capitalisation and bold emphasis has been reproduced exactly as-is in the interactive file.** Nothing in this list has been changed. These are flagged only so you can decide what to correct in the master document.

Verified: all nine hotspot cards in the interactive version match the source text character-for-character (automated comparison against the text baked into the PDF's hidden `*_PNG_af_image` form-field appearances).

---

## A. Spelling — visible to the reader

| # | Where | Source reads | Suggested |
|---|---|---|---|
| A1 | Hotspot card title, page 3 | **QUALIFIYING & VERIFIYING INCOME** | QUALIFY**ING** & VERIFY**ING** INCOME — two misspellings in the same heading |

This is the only visible misspelling found. It appears in the card's own artwork, so it is reproduced verbatim.

## B. Spelling — internal PDF field names only (not visible to readers)

These are the AcroForm field names inside the PDF. They never display, but they'd be worth fixing in the master file so the fields stay searchable and consistent.

| # | Field name in PDF | Should be |
|---|---|---|
| B1 | `Learn More: Consessions & Pricing` | Con**c**essions |
| B2 | `Documentation Requierments PNG_af_image` | Requi**re**ments |
| B3 | `Learn More: Common Scenarios & Trouble Shooting` | Troubleshooting (one word, as the visible card title has it) |

The visible card titles are all spelled correctly — only the field names are affected.

## C. Grammar and sentence construction

| # | Where | Issue |
|---|---|---|
| C1 | Qualifiying & Verifiying Income, bullet 1 | Subject/verb disagreement. Reads: "**Unredacted** documents include Valid Employment income, bank statements, … and child maintenance or "support," are all Accepted forms of income." Two main verbs ("include" … "are"). Suggested: "Unredacted documents **including** valid employment income, bank statements, work offer letters, financial aid, Social Security benefits, military housing allowances, and child maintenance or "support" are all accepted forms of income." |
| C2 | Qualifiying & Verifiying Income | Mid-sentence capitals on "Valid Employment income" and "Accepted forms" — inconsistent with the rest of the card. |
| C3 | Rental History, Screening, & Credit | The last four bullets are actually two question-and-answer pairs, but they're formatted as four parallel bullets: "Can paid-in-full or dispute documentation be considered?" / "Yes, but applicants may be required to submit documentation directly to TransUnion for verification." and "What criminal history results in denial?" / "Criminal screening follows Cortland standards and internal screening guidelines." Recommend restructuring as Q&A rather than a flat bullet list. |
| C4 | Rental History, Screening, & Credit | "Evictions, bankruptcies, and court judgments can impact decisions in multiple ways." sits centred in the middle of the bullet list. It reads as an introduction to the four bullets that follow, so it probably wants to be a lead-in line rather than a centred interruption. |
| C5 | Rental History, Screening, & Credit | Inconsistent leading spaces before three bullets in the source (" Discharged…", " Dismissed…", " Evictions…") — they sit slightly indented relative to the first bullet. |
| C6 | Smooth Sailing (pages 1 and 4) | "Resident Services will now take over admin responsibilities, etc" — no terminal punctuation and "etc" is unpunctuated. Suggested: "…take over administrative responsibilities, etc." |
| C7 | Following Up (pages 1 and 2) | "…set up any additional tours at the prospect's request" — no closing full stop, unlike the neighbouring blocks. |
| C8 | Applying (pages 1 and 3) | "Quick and Easy Online process." uses title case mid-sentence; "Applicants upload documents & submit payments securely" has no closing full stop. |
| C9 | Get Ready to Move! (pages 1 and 4) | The list mixes noun phrases with an instruction: "Digital lease packet / Welcome packet / **Download** Cortland Connect". The third item is an imperative while the first two are things received. |
| C10 | The Approval (pages 1 and 3) | "The Resident is Approved!" — mid-sentence capitals on "Resident" and "Approved", used inconsistently elsewhere in the document. |

## D. Inconsistencies between pages (same copy, different treatment)

| # | Issue |
|---|---|
| D1 | **The Beginning** — page 1 reads "Details are gathered on the **Prospect**" (capital P); page 2 reads "on the **prospect**" (lowercase). |
| D2 | **The Beginning** — on page 2 the sentence "Details are gathered on the prospect to ensure a successful touring experience." is **bold**; on page 1 the same sentence is not bold. |
| D3 | Apostrophe style is mixed: Documentation Requirements uses a straight apostrophe ("applicant's") while Resident & Lease Management uses a typographic one ("Renter's"). |

## E. Missing footnote text

| # | Issue |
|---|---|
| E1 | Two hotspot cards carry an asterisk footnote marker with no footnote anywhere in the document: Application Process — "…a decision may be made sooner)**\***" and Qualifiying & Verifiying Income — "*Business accounts require additional documentation***\***". The reader has nothing to refer to. |

## F. One point possibly worth a compliance check (not a language issue)

| # | Issue |
|---|---|
| F1 | Special Programs & Vouchers states "Housing vouchers are accepted **where they are required by law or local regulations**." Source-of-income protection rules vary by jurisdiction, so this may be worth confirming with legal before wider circulation. Reproduced verbatim. |

---

## G. Notes on the conversion itself

These are decisions made while converting, for transparency — no source content was affected.

1. **The four roadmap pages are the PDF's own vector artwork**, extracted as SVG. Every curve, colour segment, line-art icon, text setting and the Cortland logo are the original vectors, so they stay razor-sharp at any zoom and print cleanly. Nothing was redrawn or substituted.
2. **Typography.** Because the artwork is vector, all roadmap text is genuine TT Norms Pro (as outlines from the PDF). TT Norms Pro is a licensed font that cannot be embedded as a webfont, so the surrounding interface and the hotspot card text use TT Norms Pro if it is installed on the viewer's machine and otherwise fall back to the closest available geometric sans (Avenir Next → Nunito Sans → Segoe UI → system sans).
3. **The orange stars are live SVG**, not part of the background image. They were measured from the PDF's own star geometry (position, size and the exact five-point form) so they sit precisely where the PDF puts them, and they can carry hover, focus and tap states.
4. **The "Concessions & Pricing" card was saved open in the source PDF.** It has been removed from the artwork; all nine cards now start closed on every page, as requested.
5. **Card placement.** Each card's position and column layout was computed against the actual artwork to cover as little text, icon work and as few other stars as possible. The pages are dense enough that a legible card cannot avoid the journey path entirely, so opening a card also fades the artwork slightly — this keeps the card easy to read and makes the overlap read as a deliberate focus state rather than a collision. The star you're pointing at always stays fully visible.
6. **Phone layout.** At phone widths a 16:9 landscape page is only ~210 px tall, so the roadmap's own text is too small to read. On phones the page therefore also lists that page's sections as full-size, colour-coded text beneath the roadmap (exact source wording), and hotspot cards open as a bottom sheet so the star stays visible. Desktop and tablet are unchanged.
7. **Colours** use the palette exactly as specified: navy `#013D7F`, magenta `#C6007E`, lime `#A6D04E`, teal `#0092BD`, orange `#FE7002`, white background. (For reference, the values sampled from the PDF artwork itself are within one or two levels per channel of these — visually identical.)
8. **Fully self-contained.** The HTML file makes zero external requests: artwork, icons, logo and all behaviour are embedded. It works offline, from a local file, from a shared drive or from a web server.

---

## H. Interface update (second revision)

Layout and chrome only — no roadmap content, wording, artwork, icon or hotspot behaviour was changed. All nine hotspot cards still match the PDF source character-for-character, and the star positions were re-verified against the PDF after the resize (all six page-3 stars align to within 0.06% of the page, i.e. sub-pixel).

**Header**
- Blue banner removed; the header now sits on the page background.
- Title is `THE RESIDENT ROADMAP` in regular weight, `#002D72`, all caps. "CORTLAND" removed from the title.
- Brand label added upper-right: `CORTLAND` (regular, caps, `#002D72`) • dot (`#002D72`, balanced spacing) • `Interactive Education` (title case, regular, `#A9C23F`).

**Navigation tabs**
- The in-banner buttons became tabs sitting directly on top of the document, upper-right. Names and order unchanged.
- Inactive: `#002D72` background, white text, regular weight. Active: `#8FAD15` background, `#002D72` text, bold — and the active tab is the only bold text in the header. The main title stays regular at all times.
- The title aligns to the document's left edge and the tabs to its right edge at every screen size (verified to 0 px at 14 viewport sizes).

**Document size**
- The document is now sized from the space actually available: a script measures the real header/controls height and the document takes the rest, keeping an exact 16:9 ratio with a small, equal 8 px gap above and below the whole block. Nothing is stretched, cropped or clipped.
- At 1920×1080 the document is 1561×878; at 1600×950 it is 1330×748.

**Bottom controls**
- Previous and Next are combined into one centred navy pill with the lime circular house-and-heart badge between them, matching the supplied reference.
- The four progress dots sit immediately to the right of the pill, and the page count to the right of the dots — all on one row, all regular weight.
- The active page is shown by the lime (`#8FAD15`) enlarged dot, not by bold text.
- On phones the same row stays intact with tighter spacing.

**Verified after the change:** 0 failures across the full interaction suite (hover, Tab, Enter, Space, Escape, tap, close button, one-card-at-a-time), the content suite (all nine cards exact), and an overlap/clipping audit at 14 viewport sizes from 2560×1440 to 360×740 — no overlaps, no clipping, no horizontal scrolling. Print still produces four clean landscape sheets.
