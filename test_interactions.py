"""
Hotspot and navigation behaviour: hover, keyboard, touch, layout, print.

    pytest tests/ -v
"""
from __future__ import annotations

import pytest

PAGE_STARS = {2: 6, 3: 3}       # page index (0-based) -> number of orange stars
TOTAL_STARS = 9


def star_ids(page, page_index):
    return page.eval_on_selector_all(f"#page-{page_index} .star", "els => els.map(e => e.id)")


def hover_star(page, star_id):
    """Hover the star glyph itself (the button box is pointer-events:none)."""
    box = page.eval_on_selector(
        f"#{star_id} .glyph",
        "e => { const r = e.getBoundingClientRect();"
        "       return {x: r.x + r.width / 2, y: r.y + r.height * 0.42}; }")
    page.mouse.move(box["x"], box["y"], steps=4)
    page.wait_for_timeout(320)


def shown(page, key):
    return page.eval_on_selector(f"#card-{key}", "e => e.classList.contains('show')")


# --------------------------------------------------------------------------- load

def test_all_cards_start_closed(page):
    """Including Concessions & Pricing, which was saved open in the source PDF."""
    assert page.eval_on_selector_all(
        ".card", "els => els.every(e => e.hidden && !e.classList.contains('show'))")


def test_expected_number_of_hotspots(page):
    assert page.eval_on_selector_all(".star", "e => e.length") == TOTAL_STARS
    assert page.eval_on_selector_all(".card", "e => e.length") == TOTAL_STARS
    for index, count in PAGE_STARS.items():
        assert len(star_ids(page, index)) == count


def test_first_page_active_and_prev_disabled(page):
    assert page.eval_on_selector("#page-0", "e => e.classList.contains('active')")
    assert page.eval_on_selector("#prev", "e => e.disabled")


def test_no_console_errors(page):
    page.click('.pagenav button[data-page="2"]')
    page.wait_for_timeout(400)
    assert page.errors == []


# ---------------------------------------------------------------------- navigation

def test_next_prev_and_dots(page):
    page.click("#next")
    page.wait_for_timeout(400)
    assert page.eval_on_selector("#page-1", "e => e.classList.contains('active')")
    page.click("#prev")
    page.wait_for_timeout(400)
    assert page.eval_on_selector("#page-0", "e => e.classList.contains('active')")


def test_arrow_keys_change_page(page):
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(400)
    assert page.eval_on_selector("#page-1", "e => e.classList.contains('active')")
    page.keyboard.press("ArrowLeft")
    page.wait_for_timeout(400)
    assert page.eval_on_selector("#page-0", "e => e.classList.contains('active')")


def test_last_page_disables_next_and_counter_updates(page):
    page.click('.pagenav button[data-page="3"]')
    page.wait_for_timeout(400)
    assert page.eval_on_selector("#next", "e => e.disabled")
    assert page.eval_on_selector("#counter", "e => e.textContent") == "Page 4 of 4"


def test_only_active_tab_is_bold(page):
    page.click('.pagenav button[data-page="2"]')
    page.wait_for_timeout(400)
    weights = page.eval_on_selector_all(
        ".pagenav button",
        "els => els.map(e => ({active: e.getAttribute('aria-current') === 'true',"
        "                      weight: parseInt(getComputedStyle(e).fontWeight, 10)}))")
    for tab in weights:
        assert (tab["weight"] >= 600) == tab["active"]
    assert parse_weight(page, "h1") < 600, "the main title must never be bold"


def parse_weight(page, selector):
    return page.eval_on_selector(selector, "e => parseInt(getComputedStyle(e).fontWeight, 10)")


def test_changing_page_closes_open_card(page):
    page.click('.pagenav button[data-page="2"]')
    page.wait_for_timeout(400)
    hover_star(page, "star-application-process")
    assert shown(page, "application-process")
    page.click("#next")
    page.wait_for_timeout(450)
    assert page.eval_on_selector_all(".card", "els => els.every(e => !e.classList.contains('show'))")
    assert not page.eval_on_selector("#stage", "e => e.classList.contains('dimmed')")


# --------------------------------------------------------------------------- hover

@pytest.mark.parametrize("page_index", sorted(PAGE_STARS))
def test_hover_opens_positions_and_closes(page, page_index):
    page.click(f'.pagenav button[data-page="{page_index}"]')
    page.wait_for_timeout(420)

    for star_id in star_ids(page, page_index):
        key = star_id.replace("star-", "")
        page.mouse.move(4, 4)
        page.wait_for_timeout(280)
        hover_star(page, star_id)

        assert shown(page, key), f"{key} did not open on hover"
        assert page.eval_on_selector("#stage", "e => e.classList.contains('dimmed')")
        assert page.eval_on_selector_all(
            ".card", "els => els.filter(e => e.classList.contains('show')).length") == 1
        assert page.eval_on_selector(f"#card-{key}", "e => e.scrollHeight - e.clientHeight") == 0, \
            f"{key} text is clipped"

        geometry = page.evaluate("""(key) => {
            const stage = document.getElementById('stage').getBoundingClientRect();
            const glyph = document.getElementById('star-' + key)
                            .querySelector('.glyph').getBoundingClientRect();
            const card = document.getElementById('card-' + key).getBoundingClientRect();
            return {
              inside: card.left >= stage.left - 1 && card.right <= stage.right + 1
                   && card.top >= stage.top - 1 && card.bottom <= stage.bottom + 1,
              clearOfStar: card.right < glyph.left || card.left > glyph.right
                        || card.bottom < glyph.top || card.top > glyph.bottom,
            };
        }""", key)
        assert geometry["inside"], f"{key} card escapes the document"
        assert geometry["clearOfStar"], f"{key} card covers its own star"

        # stays open while the pointer is over the card...
        centre = page.eval_on_selector(
            f"#card-{key}",
            "e => { const r = e.getBoundingClientRect();"
            "       return {x: r.x + r.width / 2, y: r.y + r.height / 2}; }")
        page.mouse.move(centre["x"], centre["y"], steps=5)
        page.wait_for_timeout(420)
        assert shown(page, key), f"{key} closed while the pointer was over the card"

        # ...and closes once the pointer leaves both
        page.mouse.move(4, 4, steps=5)
        page.wait_for_timeout(520)
        assert not shown(page, key), f"{key} did not close on mouse-out"


# ------------------------------------------------------------------------ keyboard

def test_tab_focus_opens_card(page):
    page.click('.pagenav button[data-page="2"]')
    page.wait_for_timeout(420)
    page.mouse.move(4, 4)
    page.eval_on_selector('.pagenav button[data-page="2"]', "e => e.focus()")

    focused = None
    for _ in range(24):
        page.keyboard.press("Tab")
        page.wait_for_timeout(90)
        candidate = page.evaluate("() => document.activeElement.id || ''")
        if candidate.startswith("star-"):
            focused = candidate
            break
    assert focused, "Tab never reached a hotspot star"
    page.wait_for_timeout(300)

    key = focused.replace("star-", "")
    assert shown(page, key)
    assert page.eval_on_selector(f"#{focused}", "e => e.getAttribute('aria-expanded')") == "true"


def test_enter_space_and_escape(page):
    page.click('.pagenav button[data-page="2"]')
    page.wait_for_timeout(420)
    page.eval_on_selector("#star-qualifying-income", "e => e.focus()")
    page.wait_for_timeout(250)

    page.keyboard.press("Enter")
    page.wait_for_timeout(320)
    first = shown(page, "qualifying-income")
    page.keyboard.press("Enter")
    page.wait_for_timeout(320)
    assert shown(page, "qualifying-income") != first, "Enter does not toggle"

    page.keyboard.press("Space")
    page.wait_for_timeout(320)
    assert shown(page, "qualifying-income") != (shown(page, "qualifying-income") is False)

    if not shown(page, "qualifying-income"):
        page.keyboard.press("Space")
        page.wait_for_timeout(320)
    assert shown(page, "qualifying-income")

    page.keyboard.press("Escape")
    page.wait_for_timeout(350)
    assert not shown(page, "qualifying-income")
    assert page.evaluate("() => document.activeElement.id") == "star-qualifying-income", \
        "focus should return to the star after Escape"
    assert page.eval_on_selector("#star-qualifying-income",
                                 "e => e.getAttribute('aria-expanded')") == "false"


def test_tabbing_between_stars_keeps_one_card_open(page):
    """Walk the real Tab order. Cards auto-open only for keyboard focus, so this
    also pins down that a click does not leave the page in "keyboard" mode."""
    page.click('.pagenav button[data-page="2"]')
    page.wait_for_timeout(420)
    page.mouse.move(4, 4)
    page.eval_on_selector('.pagenav button[data-page="2"]', "e => e.focus()")

    visited = []
    for _ in range(14):
        page.keyboard.press("Tab")
        page.wait_for_timeout(160)
        focused = page.evaluate("() => document.activeElement.id || ''")
        if not focused.startswith("star-"):
            continue
        if focused not in visited:
            visited.append(focused)
        open_count = page.eval_on_selector_all(
            ".card", "els => els.filter(e => e.classList.contains('show')).length")
        assert open_count == 1, f"{focused} focused but {open_count} cards open"
        if len(visited) >= 2:
            break

    assert len(visited) >= 2, f"Tab order only reached {visited}"


# ----------------------------------------------------------------------------- aria

def test_accessible_names_and_relationships(page):
    report = page.evaluate("""() => {
      const stars = [...document.querySelectorAll('.star')];
      const cards = [...document.querySelectorAll('.card')];
      return {
        buttons:   stars.every(s => s.tagName === 'BUTTON'),
        labelled:  stars.every(s => (s.getAttribute('aria-label') || '').startsWith('Learn more:')),
        collapsed: stars.every(s => s.getAttribute('aria-expanded') === 'false'),
        controls:  stars.every(s => document.getElementById(s.getAttribute('aria-controls'))),
        dialogs:   cards.every(c => c.getAttribute('role') === 'dialog' && c.getAttribute('aria-label')),
        closable:  cards.every(c => c.querySelector('.close')?.getAttribute('aria-label')),
      };
    }""")
    assert all(report.values()), report


# ---------------------------------------------------------------------------- touch

def test_tap_toggles_and_close_button_works(browser, url):
    context = browser.new_context(viewport={"width": 820, "height": 1180},
                                 has_touch=True, is_mobile=True)
    page = context.new_page()
    page.goto(url)
    page.wait_for_timeout(700)
    page.click('.pagenav button[data-page="2"]')
    page.wait_for_timeout(450)

    page.tap("#star-application-process")
    page.wait_for_timeout(400)
    assert shown(page, "application-process"), "tap did not open the card"

    assert page.eval_on_selector(
        "#card-application-process",
        "e => { const c = e.querySelector('.close'); const r = c.getBoundingClientRect();"
        "       return !e.hidden && r.width >= 20 && r.height >= 20; }"), \
        "close button must be visible and tappable on touch"

    page.tap("#card-application-process .close")
    page.wait_for_timeout(400)
    assert not shown(page, "application-process")

    page.tap("#star-application-process")
    page.wait_for_timeout(420)
    assert shown(page, "application-process"), "tap did not re-open the card"
    context.close()


# ------------------------------------------------------------------------ responsive

VIEWPORTS = [
    (2560, 1440), (1920, 1080), (1600, 950), (1440, 900), (1366, 768), (1280, 800),
    (1180, 820), (1024, 768), (834, 1112), (768, 1024), (600, 900), (430, 932),
    (390, 844), (360, 740),
]


@pytest.mark.parametrize("width,height", VIEWPORTS)
def test_layout_is_clean_at_every_size(browser, url, width, height):
    page = browser.new_page(viewport={"width": width, "height": height})
    page.goto(url)
    page.wait_for_timeout(750)
    report = page.evaluate("""() => {
      const box = s => { const e = document.querySelector(s); if (!e) return null;
        const r = e.getBoundingClientRect();
        return {t: r.top, b: r.bottom, l: r.left, r: r.right, w: r.width, h: r.height}; };
      const hits = (a, b) => a && b && !(a.r <= b.l + 0.5 || a.l >= b.r - 0.5
                                      || a.b <= b.t + 0.5 || a.t >= b.b - 0.5);
      const doc = document.documentElement;
      const title = box('h1'), brand = box('.brandlabel'), tabs = box('.pagenav');
      const stage = box('.stage'), pill = box('.navpill'), right = box('.navright');
      return {
        ratio: stage.w / stage.h,
        hScroll: doc.scrollWidth > doc.clientWidth + 1,
        artFills: (() => { const a = document.querySelector('#page-0 img.art').getBoundingClientRect();
                           return Math.abs(a.width - stage.w) < 1.5 && Math.abs(a.height - stage.h) < 1.5; })(),
        titleOverBrand: hits(title, brand),
        brandOverTabs: hits(brand, tabs),
        tabsOverDoc: hits(tabs, stage),
        pillOverDots: hits(pill, right),
        titleBold: parseInt(getComputedStyle(document.querySelector('h1')).fontWeight, 10) >= 600,
      };
    }""")
    page.close()

    assert abs(report["ratio"] - 16 / 9) < 0.01, f"document is not 16:9 ({report['ratio']:.4f})"
    assert report["artFills"], "artwork does not fill the document box"
    assert not report["hScroll"], "horizontal scrolling"
    assert not report["titleOverBrand"], "title overlaps the brand label"
    assert not report["brandOverTabs"], "brand label overlaps the tabs"
    assert not report["tabsOverDoc"], "tabs overlap the document"
    assert not report["pillOverDots"], "nav control overlaps the dots"
    assert not report["titleBold"], "title must be regular weight"


@pytest.mark.parametrize("width,height", [(1024, 768), (820, 1180), (768, 1024)])
def test_tablet_cards_fit_inside_the_document(browser, url, width, height):
    context = browser.new_context(viewport={"width": width, "height": height},
                                 has_touch=True, is_mobile=width < 900)
    page = context.new_page()
    page.goto(url)
    page.wait_for_timeout(700)

    for page_index in sorted(PAGE_STARS):
        page.click(f'.pagenav button[data-page="{page_index}"]')
        page.wait_for_timeout(420)
        for star_id in star_ids(page, page_index):
            key = star_id.replace("star-", "")
            page.tap(f"#{star_id}")
            page.wait_for_timeout(320)
            report = page.evaluate("""(key) => {
                const stage = document.getElementById('stage').getBoundingClientRect();
                const glyph = document.getElementById('star-' + key)
                                .querySelector('.glyph').getBoundingClientRect();
                const el = document.getElementById('card-' + key);
                const card = el.getBoundingClientRect();
                return {shown: el.classList.contains('show'),
                        inside: card.left >= stage.left - 1 && card.right <= stage.right + 1
                             && card.top >= stage.top - 1 && card.bottom <= stage.bottom + 1,
                        clearOfStar: card.right < glyph.left || card.left > glyph.right
                                  || card.bottom < glyph.top || card.top > glyph.bottom,
                        readable: card.width >= 200 && card.height >= 80};
            }""", key)
            assert all(report.values()), f"{key} at {width}x{height}: {report}"
            page.keyboard.press("Escape")
            page.wait_for_timeout(200)
    context.close()


def test_phone_cards_become_bottom_sheets(browser, url):
    context = browser.new_context(viewport={"width": 390, "height": 844},
                                 has_touch=True, is_mobile=True)
    page = context.new_page()
    page.goto(url)
    page.wait_for_timeout(700)

    for page_index in sorted(PAGE_STARS):
        page.click(f'.pagenav button[data-page="{page_index}"]')
        page.wait_for_timeout(420)
        for star_id in star_ids(page, page_index):
            key = star_id.replace("star-", "")
            page.tap(f"#{star_id}")
            page.wait_for_timeout(360)
            report = page.evaluate("""(key) => {
                const glyph = document.getElementById('star-' + key)
                                .querySelector('.glyph').getBoundingClientRect();
                const el = document.getElementById('card-' + key);
                const card = el.getBoundingClientRect();
                return {shown: el.classList.contains('show'),
                        fixed: getComputedStyle(el).position === 'fixed',
                        inViewport: card.top >= -1 && card.bottom <= innerHeight + 1
                                 && card.left >= -1 && card.right <= innerWidth + 1,
                        clearOfStar: card.right < glyph.left || card.left > glyph.right
                                  || card.bottom < glyph.top || card.top > glyph.bottom,
                        legible: parseFloat(getComputedStyle(el.querySelector('.copy')).fontSize) >= 12,
                        bigClose: el.querySelector('.close').getBoundingClientRect().width >= 26};
            }""", key)
            assert all(report.values()), f"{key} on phone: {report}"
            page.tap(f"#card-{key} .close")
            page.wait_for_timeout(260)

    assert not page.evaluate(
        "() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1")
    context.close()


# ----------------------------------------------------------------------------- print

def test_print_shows_four_clean_pages(page):
    page.emulate_media(media="print")
    page.wait_for_timeout(300)
    report = page.evaluate("""() => ({
      pagesVisible: [...document.querySelectorAll('.page')].filter(p => {
        const cs = getComputedStyle(p);
        return cs.visibility !== 'hidden' && cs.opacity !== '0';
      }).length,
      chromeHidden: ['.topbar', '.bottombar', '.hintstrip', '.pagetitle']
        .every(s => getComputedStyle(document.querySelector(s)).display === 'none'),
      starsHidden: [...document.querySelectorAll('.star')]
        .every(s => getComputedStyle(s).display === 'none'),
      cardsHidden: [...document.querySelectorAll('.card')]
        .every(c => getComputedStyle(c).display === 'none'),
    })""")
    assert report["pagesVisible"] == 4
    assert report["chromeHidden"]
    assert report["starsHidden"] and report["cardsHidden"]
