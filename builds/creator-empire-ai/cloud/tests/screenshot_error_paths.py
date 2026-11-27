"""Drives the real login form and the wizard's hook-generation step
against the running app (no live Supabase configured in this sandbox)
to confirm the configuration-error path is a real, visible message --
not a crash or a silent no-op. Second eyes-on pass, not an assertion
suite."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(HERE, "..", "..", "review", "screenshots", "cloud")

try:
    chromium_mod = __import__("playwright.sync_api", fromlist=["sync_playwright"])
except ImportError:
    chromium_mod = __import__("playwright_core.sync_api", fromlist=["sync_playwright"])
sync_playwright = chromium_mod.sync_playwright

BASE = "http://localhost:3417"
chrome_path = os.environ.get("CHROME_PATH")
page_errors = []

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chrome_path) if chrome_path else p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.on("pageerror", lambda exc: page_errors.append(str(exc)))

    page.goto(BASE + "/login")
    page.fill("input[type=email]", "test@example.com")
    page.fill("input[type=password]", "testpassword123")
    page.click("button[type=submit]")
    page.wait_for_selector(".error-banner", timeout=5000)
    error_text = page.locator(".error-banner").inner_text()
    print(f"login error banner: {error_text!r}")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "login-error-state.png"), full_page=True)

    page.goto(BASE + "/campaign/new")
    page.click("button:has-text('Generate hooks')")
    page.wait_for_selector(".error-banner", timeout=5000)
    hooks_error_text = page.locator(".error-banner").inner_text()
    print(f"hooks error banner: {hooks_error_text!r}")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "wizard-hooks-error-state.png"), full_page=True)

    browser.close()

if page_errors:
    print(f"UNCAUGHT PAGE ERRORS: {page_errors}")
    sys.exit(1)
print("No uncaught page errors -- both configuration errors surfaced as real UI, not crashes.")
