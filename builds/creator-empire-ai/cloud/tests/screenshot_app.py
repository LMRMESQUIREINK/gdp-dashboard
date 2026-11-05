"""Screenshots the real Next.js app (already running via `next start`
on :3417) at desktop and mobile widths, per the mandatory screenshot-
before-done rule. Not an automated assertion suite -- a second,
eyes-on look at pages built this round, same as
../tests/screenshot_later_steps.py for the standalone edition."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(HERE, "..", "..", "review", "screenshots", "cloud")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

try:
    chromium_mod = __import__("playwright.sync_api", fromlist=["sync_playwright"])
except ImportError:
    chromium_mod = __import__("playwright_core.sync_api", fromlist=["sync_playwright"])
sync_playwright = chromium_mod.sync_playwright

BASE = "http://localhost:3417"
chrome_path = os.environ.get("CHROME_PATH")

console_errors = {}

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chrome_path) if chrome_path else p.chromium.launch()

    for name, path, viewport in [
        ("home-desktop", "/", {"width": 1280, "height": 900}),
        ("home-mobile", "/", {"width": 375, "height": 800}),
        ("login-desktop", "/login", {"width": 1280, "height": 900}),
        ("wizard-step1-desktop", "/campaign/new", {"width": 1280, "height": 1000}),
        ("wizard-step1-mobile", "/campaign/new", {"width": 375, "height": 1100}),
    ]:
        page = browser.new_page(viewport=viewport)
        errs = []
        page.on("console", lambda msg, e=errs: e.append(msg.text) if msg.type == "error" else None)
        page.goto(BASE + path)
        page.wait_for_timeout(300)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{name}.png"), full_page=True)
        console_errors[name] = errs
        page.close()

    browser.close()

print("Screenshots written to", SCREENSHOT_DIR)
any_errors = False
for name, errs in console_errors.items():
    status = "CLEAN" if not errs else f"ERRORS: {errs}"
    print(f"  {name}: {status}")
    if errs:
        any_errors = True
sys.exit(1 if any_errors else 0)
