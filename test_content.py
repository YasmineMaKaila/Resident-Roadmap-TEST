"""
Content fidelity: every hotspot card must match the source PDF word for word.

SOURCE below is transcribed from the JPEGs baked into the PDF's hidden
`<Topic> PNG_af_image` form-field appearances (kept in docs/hotspot-source-images/
as the evidence trail). Comparison ignores only punctuation style and whitespace,
so a changed, dropped or reworded phrase fails the test.

Known source misspellings — QUALIFIYING / VERIFIYING — are reproduced
deliberately and are asserted here so nobody "fixes" them by accident.
See docs/SOURCE-CONTENT-NOTES.md.
"""
from __future__ import annotations

import re
import unicodedata

import pytest

SOURCE = {
    "application-process": """
        APPLICATION PROCESS
        SAS takes ownership once an application is completed and in "Submitted" status.
        Teams should first troubleshoot. If the issue persists, please submit a support ticket
        through Help Desk.
        On average, applications take 3-5 business days. (If all required documentation is
        submitted and screening is complete on day one, a decision may be made sooner)*
        SAS takes ownership of resubmitted applications.
        Applications can be re-opened by SAS within 30 days of a denial.
    """,
    "leasing-process": """
        LEASING PROCESS & CHANGES
        Applicants may switch units twice upon request after starting an application.
        The SAS Specialist applies concessions using the Marketing Specials Tracker.
        Any details discussed with the prospect or resident with the Community Relations team
        need to be documented in the guest card notes.
        Modifications of move-in dates or lease details after handoff will be handled at the
        community level.
        SAS completes lease countersigning if the lease is ready for countersignature before
        handoff. After the handoff, the Community Relations team will handle countersigning.
    """,
    "documentation-requirements": """
        DOCUMENTATION REQUIREMENTS
        Specific documentation based on the applicant:
        Self-Employed Applicants: Provide Articles of Incorporation and documentation
        verifying income.
        Student Applicants: Provide a financial aid award letter or other supporting
        documentation that verifies enrollment and/or funding.
        International Applicants: Standard documentation requirements apply. Document
        translations and/or currency conversions may be required. Applicants must also provide
        a current, valid government-issued identification document.
        If an applicant's ID cannot be verified:
        Valid passports are accepted as an alternative form of identification.
        Temporary paper identification documents are not accepted.
    """,
    "special-programs": """
        SPECIAL PROGRAMS & VOUCHERS
        Housing vouchers are accepted where they are required by law or local regulations.
        A credit screening is still required for applicants who use vouchers, except in
        jurisdictions where laws prohibit it (e.g., Colorado).
        The timeline for voucher approvals and inspections varies depending on local housing
        authorities, inspection scheduling, and unit availability.
    """,
    "qualifying-income": """
        QUALIFIYING & VERIFIYING INCOME
        Unredacted documents include Valid Employment income, bank statements, work offer
        letters, financial aid, Social Security benefits, military housing allowances, and
        child maintenance or "support," are all Accepted forms of income.
        Two months of income documentation is the minimum requirement for bank statements.
        Business accounts require additional documentation*
        Any applicant who is between jobs, relocating, or does not have sufficient personal
        income can use an official offer letter, demonstrate sufficient assets, or qualify by
        adding a guarantor.
        Savings Accounts, Investments, and other liquid accounts are acceptable assets for
        demonstrating sufficient assets for income.
        Assets are calculated as:
        Applicant: 3x rent x lease term
        Guarantor: 5x rent x lease term
        Income vs. Assets
        Income is recurring monthly earnings. Assets are liquid funds available to be used to
        meet income qualification requirements.
    """,
    "concessions-pricing": """
        CONCESSIONS & PRICING
        Concessions should be applied as early as possible during the application process.
        Concession Errors should be corrected immediately and verified before lease execution.
        Welcome Home Letter and Lease Discrepancies: The Welcome Home Letter serves as the
        authoritative reference for payment amounts. Applicants should follow the amount listed
        in the Welcome Home Letter, even if discrepancies appear in the resident portal.
    """,
    "common-scenarios": """
        COMMON SCENARIOS & TROUBLESHOOTING
        Application Assistance: When an applicant is unable to complete an application,
        troubleshooting steps should be completed first. If the issue remains unresolved, a
        support ticket should be submitted.
        Pre-Screening Guidance: General qualification criteria may be shared with prospects
        before they submit an application.
        Incorrect Information: Discrepancies or incorrect information are reviewed and managed
        on a case-by-case basis, based on the nature of the issue.
        Duplicate Applications: Applicants should identify their preferred property. Duplicate
        applications will be canceled, and any applicable fees will be refunded.
    """,
    "resident-lease-management": """
        RESIDENT & LEASE MANAGEMENT
        Renter's Insurance Requirements: Residents must maintain renter's insurance that meets
        the following requirements:
        Minimum of $300,000 in liability coverage
        All leaseholders/residents are listed on the policy
        The correct interested party is identified on the policy
        Coverage is active on or before the lease start date
        Emotional Support Animals (ESAs) and Service Animals: Required documentation must be
        submitted and approved before move-in. Applicable pet fees are waived; however, the
        animal and associated accommodations must still be documented on the resident account.
        Pet Fees: Pet fees apply to animals that are not approved service animals or emotional
        support animals (ESAs).
    """,
    "rental-history": """
        RENTAL HISTORY, SCREENING, & CREDIT
        All credit inquiries are considered "Hard Pulls"
        Evictions, bankruptcies, and court judgments can impact decisions in multiple ways.
        Active/Filed bankruptcies: Denial
        Discharged (over 7 years): Typically not considered
        Dismissed: May result in conditional approval
        Evictions (within the last 7 years): Result in automatic denial unless the applicant can
        provide documentation showing the balance has been resolved and the item has been
        successfully disputed and updated with TransUnion.
        Other screening results are evaluated per established screening criteria.
        Can paid-in-full or dispute documentation be considered?
        Yes, but applicants may be required to submit documentation directly to TransUnion for
        verification.
        What criminal history results in denial?
        Criminal screening follows Cortland standards and internal screening guidelines.
    """,
}

# Phrases that must survive in each page's artwork transcript.
PAGE_PHRASES = {
    0: ["THE BEGINNING", "TOURING", "FOLLOWING UP", "APPLYING", "APPLICATION COMMUNICATION",
        "THE APPROVAL", "GET READY TO MOVE", "WELCOME HOME", "SMOOTH SAILING",
        "The Leasing HUB", "self-tour option", "handled by SAS", "Welcome Home Letter",
        "Digital lease packet", "Welcome packet", "Download Cortland", "Resident Services"],
    1: ["THE BEGINNING", "TOURING", "FOLLOWING UP", "The Leasing HUB", "self-tour option"],
    2: ["APPLYING", "APPLICATION COMMUNICATION", "THE APPROVAL", "handled by SAS",
        "Welcome Home Letter"],
    3: ["GET READY TO MOVE", "WELCOME HOME", "SMOOTH SAILING", "Digital lease packet",
        "Resident Services"],
}

EXPECTED_BOLD = {
    "application-process": ["SAS takes ownership", "30 days of a denial."],
    "leasing-process": ["twice upon request", "Marketing Specials Tracker"],
    "documentation-requirements": ["Self-Employed Applicants:", "not accepted."],
    "special-programs": ["Housing vouchers are accepted"],
    "qualifying-income": ["Unredacted", "Two months of income", "Assets are calculated as:"],
    "resident-lease-management": ["Renter's Insurance Requirements:"],
    "rental-history": ['"Hard Pulls"'],
}


def normalise(text: str) -> str:
    """Collapse everything that is punctuation or layout, keep the words."""
    text = unicodedata.normalize("NFKD", text)
    for a, b in [("‘", "'"), ("’", "'"), ("“", '"'), ("”", '"'),
                 ("–", "-"), ("—", "-"), ("×", "x"), (" ", " ")]:
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9]+", " ", text)).strip().lower()


def card_text(page, key: str) -> str:
    """innerText of a hidden card, rendered off-screen so block breaks survive."""
    raw = page.eval_on_selector(f"#card-{key}", """e => {
        const previous = {hidden: e.hidden, style: e.style.cssText};
        e.hidden = false;
        e.style.cssText = previous.style +
          ';position:fixed;left:-10000px;top:0;width:600px;opacity:1;visibility:visible;' +
          'pointer-events:none;max-height:none;overflow:visible;';
        const text = e.innerText;
        e.style.cssText = previous.style;
        e.hidden = previous.hidden;
        return text;
    }""")
    return re.sub(r"^\s*×\s*", "", raw)      # drop the close button glyph


@pytest.mark.parametrize("key", sorted(SOURCE))
def test_card_matches_the_pdf_exactly(page, key):
    assert normalise(card_text(page, key)) == normalise(SOURCE[key])


@pytest.mark.parametrize("page_index", sorted(PAGE_PHRASES))
def test_page_artwork_copy_is_available_to_screen_readers(page, page_index):
    transcript = normalise(page.eval_on_selector(
        f"#tr-{page_index}",
        "e => [...e.querySelectorAll('h2,h3,p')].map(n => n.textContent).join(' \\n ')"))
    missing = [p for p in PAGE_PHRASES[page_index] if normalise(p) not in transcript]
    assert not missing, f"page {page_index + 1} transcript missing: {missing}"


@pytest.mark.parametrize("key", sorted(EXPECTED_BOLD))
def test_bold_emphasis_preserved(page, key):
    runs = [normalise(t) for t in page.eval_on_selector_all(
        f"#card-{key} .copy strong", "els => els.map(e => e.innerText)")]
    missing = [p for p in EXPECTED_BOLD[key] if normalise(p) not in runs]
    assert not missing, f"{key} lost bold emphasis on: {missing}"


def test_italic_note_preserved(page):
    italics = page.eval_on_selector_all(
        "#card-qualifying-income .copy em", "els => els.map(e => e.innerText)")
    assert any("business accounts require additional documentation" in normalise(t)
               for t in italics)


def test_source_misspellings_are_reproduced_not_corrected(page):
    """The PDF heading reads QUALIFIYING & VERIFIYING; we must not silently fix it."""
    heading = page.eval_on_selector("#card-qualifying-income h2", "e => e.textContent")
    assert "QUALIFIYING" in heading.upper()
    assert "VERIFIYING" in heading.upper()


def test_brand_label_and_title_wording(page):
    assert normalise(page.eval_on_selector("h1", "e => e.textContent")) == "the resident roadmap"
    label = page.eval_on_selector(".brandlabel", "e => e.textContent")
    assert "Cortland" in label and "Interactive Education" in label


def test_palette_uses_the_specified_hexes(page):
    colours = page.evaluate("""() => {
      const rgb = v => v.trim();
      const root = getComputedStyle(document.documentElement);
      const active = document.querySelector('.pagenav button[aria-current="true"]');
      return {
        title: getComputedStyle(document.querySelector('h1')).color,
        activeTabBg: getComputedStyle(active).backgroundColor,
        activeTabFg: getComputedStyle(active).color,
        pill: getComputedStyle(document.querySelector('.navpill')).backgroundColor,
        badge: getComputedStyle(document.querySelector('.navbadge')).backgroundColor,
        edu: getComputedStyle(document.querySelector('.bl-edu')).color,
      };
    }""")
    assert colours["title"] == "rgb(0, 45, 114)"          # #002D72
    assert colours["pill"] == "rgb(0, 45, 114)"           # #002D72
    assert colours["activeTabBg"] == "rgb(143, 173, 21)"  # #8FAD15
    assert colours["activeTabFg"] == "rgb(0, 45, 114)"    # #002D72
    assert colours["badge"] == "rgb(143, 173, 21)"        # #8FAD15
    assert colours["edu"] == "rgb(169, 194, 63)"          # #A9C23F
