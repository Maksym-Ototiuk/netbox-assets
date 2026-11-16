"""
End-to-end tests: follow docs/cable-assembly-profiles.md in a running NetBox.

They need a fresh NetBox with netbox-assets installed, the devices of
e2e/seed.py and a superuser. The test files run in order (01, 02, 03) and
build on each other. Environment:

    NETBOX_URL       default http://127.0.0.1:8000
    NETBOX_USERNAME  default admin
    NETBOX_PASSWORD  default admin
"""

import os
from pathlib import Path

import pytest
from nbui import NetBoxUI
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get('NETBOX_URL', 'http://127.0.0.1:8000').rstrip('/')
ARTIFACTS = Path(__file__).resolve().parent / 'artifacts'


@pytest.fixture(scope='session')
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture(scope='session')
def page(browser):
    context = browser.new_context(
        base_url=BASE_URL, viewport={'width': 1280, 'height': 900}, color_scheme='light'
    )
    page = context.new_page()
    page.set_default_timeout(20000)
    page.goto('/login/')
    page.fill('input[name=username]', os.environ.get('NETBOX_USERNAME', 'admin'))
    page.fill('input[name=password]', os.environ.get('NETBOX_PASSWORD', 'admin'))
    page.click('button[type=submit]')
    page.wait_for_load_state('networkidle')
    assert '/login/' not in page.url, 'Cannot log in to NetBox'
    yield page
    context.close()


@pytest.fixture(scope='session')
def nb(page):
    return NetBoxUI(page)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Save a screenshot of the page when a test fails (uploaded by CI)."""
    outcome = yield
    report = outcome.get_result()
    if report.when == 'call' and report.failed and 'page' in item.funcargs:
        ARTIFACTS.mkdir(exist_ok=True)
        page = item.funcargs['page']
        page.screenshot(path=str(ARTIFACTS / f'{item.name}.png'), full_page=True)
        (ARTIFACTS / f'{item.name}.url.txt').write_text(page.url)
