import os
import subprocess
import sys
import time

import pytest
import requests
from playwright.sync_api import Page, expect


def _wait_for_server(url: str, timeout: float = 20.0) -> None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code < 500:
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError(f"Server did not start in {timeout} seconds")


@pytest.fixture(scope="session")
def app_server():
    # Start the Flask app in a subprocess for E2E tests.
    env = os.environ.copy()
    env["FLASK_ENV"] = "development"
    #Start server
    proc = subprocess.Popen([sys.executable, "app.py"], env=env)
    base_url = "http://localhost:5000"
    try:
        _wait_for_server(f"{base_url}/catalog")
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_add_and_borrow_book(page: Page, app_server: str):
    base_url = app_server
    timestamp = int(time.time())
    unique_isbn = f"978{timestamp:010d}"[-13:]
    book_title = f"E2E Book {timestamp}"
    author = "E2E Author"
    patron_id = "123456"

    # Add a book
    page.goto(f"{base_url}/add_book")
    page.fill("#title", book_title)
    page.fill("#author", author)
    page.fill("#isbn", unique_isbn)
    page.fill("#total_copies", "2")
    page.get_by_role("button", name="Add Book to Catalog").click()

    # Verify book in catalog
    page.wait_for_url(f"{base_url}/catalog")
    row = page.locator("tbody tr", has_text=book_title)
    expect(row).to_contain_text(unique_isbn)

    # Borrow  book
    row.locator("input[name='patron_id']").fill(patron_id)
    row.get_by_role("button", name="Borrow").click()

    #Verify confirmation message
    page.wait_for_url(f"{base_url}/catalog")
    flash = page.locator(".flash-success")
    expect(flash).to_contain_text("Successfully borrowed")
