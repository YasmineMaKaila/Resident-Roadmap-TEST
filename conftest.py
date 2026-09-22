"""Shared fixtures: one browser for the whole session, one URL for the built file."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def built_file() -> Path:
    """The file under test. Override with ROADMAP_HTML to test another build."""
    override = os.environ.get("ROADMAP_HTML")
    return Path(override).resolve() if override else ROOT / "index.html"


@pytest.fixture(scope="session")
def url() -> str:
    target = built_file()
    if not target.exists():
        pytest.skip(f"{target} not built — run `python src/build.py` first")
    return target.as_uri()


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance):
    browser = playwright_instance.chromium.launch(args=["--no-sandbox"])
    yield browser
    browser.close()


@pytest.fixture
def page(browser, url):
    """A desktop page with the roadmap loaded, and console errors captured."""
    page = browser.new_page(viewport={"width": 1600, "height": 950})
    page.errors = []
    page.on("pageerror", lambda e: page.errors.append(str(e)))
    page.on("console", lambda m: page.errors.append(m.text) if m.type == "error" else None)
    page.goto(url)
    page.wait_for_timeout(700)
    yield page
    page.close()
