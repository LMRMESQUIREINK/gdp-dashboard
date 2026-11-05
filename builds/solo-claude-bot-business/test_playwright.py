"""Real-Chromium UI tests for Solo Claude Bot Business, per this
project's standing screenshot-before-done rule. Serves the app over a
real local HTTP server (not file://), drives it with Playwright, and
screenshots desktop + mobile widths.

Run with: python3 test_playwright.py
"""
import http.server
import socketserver
import threading
import time
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8753

passed = 0
failed = 0


def check(cond, name, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"ok   - {name}")
    else:
        failed += 1
        print(f"FAIL - {name}" + (f" ({detail})" if detail else ""))


def serve():
    os.chdir(HERE)
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), handler) as httpd:
        httpd.serve_forever()


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        try:
            from playwright_core.sync_api import sync_playwright  # type: ignore
        except ImportError:
            print("Neither 'playwright' nor 'playwright-core' is installed.")
            print(f"\n{passed} passed, {failed} failed (static pass only -- no browser phase run).")
            sys.exit(1 if failed else 0)

    server_thread = threading.Thread(target=serve, daemon=True)
    server_thread.start()
    time.sleep(0.4)

    launch_kwargs = {}
    chrome_path = os.environ.get("CHROME_PATH", "/opt/pw-browsers/chromium")
    if chrome_path:
        launch_kwargs["executable_path"] = chrome_path

    review_dir = os.path.join(HERE, "review", "screenshots")
    os.makedirs(review_dir, exist_ok=True)

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(**launch_kwargs)
        except Exception as e:
            print("Could not launch Chromium:", e)
            print(f"\n{passed} passed, {failed} failed (browser launch failed).")
            sys.exit(1)

        try:
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda err: console_errors.append(str(err)))
            page.goto(f"http://127.0.0.1:{PORT}/index.html")
            page.wait_for_selector("#sec-offer")

            # Title/branding: zero "Grok" mentions anywhere on the real
            # rendered page, per the user's explicit rebrand instruction.
            body_text = page.inner_text("body")
            check("grok" not in body_text.lower(), "zero 'Grok'/'GrokBot' mentions anywhere on the rendered page")
            check("Solo Claude Bot Business" in body_text, "the real product name renders on the page")

            # --- Offer Calculator: drive it with the source's own real numbers ---
            page.fill("#niche-baseline", "200")
            page.evaluate("document.getElementById('multiplier').value = 15; document.getElementById('multiplier').dispatchEvent(new Event('input'))")
            page.fill("#upfront-ratio", str(25000 / 3000))
            page.fill("#hours-per-month", "250")
            page.wait_for_timeout(100)

            monthly_text = page.inner_text("#result-monthly")
            upfront_text = page.inner_text("#result-upfront")
            hourly_text = page.inner_text("#result-hourly")
            check(monthly_text.replace(",", "") == "$3,000".replace(",", ""), "offer calculator: $200 baseline x 15 = real $3,000/mo from the source", monthly_text)
            check(upfront_text.replace(",", "") == "$25,000".replace(",", ""), "offer calculator: reproduces the source's real $25,000 upfront figure exactly", upfront_text)
            check(hourly_text == "$12.00", "offer calculator: reproduces the source's own $12/hr figure ONLY when 250hrs is explicitly entered", hourly_text)
            basis_text = page.inner_text("#result-hourly-basis")
            check("250" in basis_text, "the hours assumption is always visibly labeled next to the rate", basis_text)

            # --- Client Pipeline: add real contacts, change status, track referrals ---
            page.fill("#new-contact-name", "Dana (dental clinic owner)")
            page.click("#add-contact-form button[type=submit]")
            page.wait_for_timeout(50)
            rows = page.query_selector_all(".contact-row")
            check(len(rows) == 1, "a contact is added and rendered", f"rows={len(rows)}")

            page.select_option(".contact-row .contact-status", "case-study")
            page.fill(".contact-row .contact-referrals", "2")
            page.wait_for_timeout(50)
            progress_text = page.inner_text("#call-goal-progress")
            check("1 / 50" in progress_text, "call-goal progress reflects the real contact count", progress_text)
            referrals_text = page.inner_text("#total-referrals")
            check("2 / 3" in referrals_text, "referral progress: 1 case study started = goal of 3, 2 logged so far", referrals_text)

            # Empty-name submission is rejected with a visible error, not silently ignored.
            page.fill("#new-contact-name", "   ")
            page.click("#add-contact-form button[type=submit]")
            page.wait_for_timeout(50)
            err_text = page.inner_text("#contact-error")
            check(len(err_text) > 0, "submitting a blank contact name shows a real error", err_text)
            rows_after = page.query_selector_all(".contact-row")
            check(len(rows_after) == 1, "a blank-name submission does not add a phantom contact", f"rows={len(rows_after)}")

            # Remove the contact and confirm the list updates.
            page.click(".contact-row .contact-remove")
            page.wait_for_timeout(50)
            rows_final = page.query_selector_all(".contact-row")
            check(len(rows_final) == 0, "removing a contact updates the rendered list")

            # --- Build Checklist: the 4 real stack categories, none pre-filled with a vendor name ---
            for cat in ["compute", "email", "phone", "connectors"]:
                val = page.input_value(f"#stack-{cat}-tool")
                check(val == "", f"stack category '{cat}' starts with no vendor name pre-filled", repr(val))

            page.check("#research-done")
            page.check("#design-done")
            for cat in ["compute", "email", "phone", "connectors"]:
                page.fill(f"#stack-{cat}-tool", f"my-{cat}-tool")
                page.check(f"#stack-{cat}-docs")
            page.check("#build-done")
            page.wait_for_timeout(50)
            checklist_progress = page.inner_text("#checklist-progress")
            check("4 / 4" in checklist_progress, "checklist reaches 4/4 once all real steps are completed", checklist_progress)

            # --- Persistence: reload the page, confirm state survived ---
            page.reload()
            page.wait_for_selector("#sec-offer")
            page.wait_for_timeout(100)
            reloaded_monthly = page.inner_text("#result-monthly")
            check(reloaded_monthly.replace(",", "") == "$3,000".replace(",", ""), "offer inputs survive a real page reload (localStorage)", reloaded_monthly)
            reloaded_checklist = page.inner_text("#checklist-progress")
            check("4 / 4" in reloaded_checklist, "checklist state survives a real page reload", reloaded_checklist)

            check(len(console_errors) == 0, "zero console errors on desktop render", str(console_errors))

            page.screenshot(path=os.path.join(review_dir, "desktop-1280.png"), full_page=True)

            # --- Mobile: no horizontal overflow, zero console errors ---
            page_m = browser.new_page(viewport={"width": 375, "height": 800})
            console_errors_m = []
            page_m.on("console", lambda msg: console_errors_m.append(msg.text) if msg.type == "error" else None)
            page_m.goto(f"http://127.0.0.1:{PORT}/index.html")
            page_m.wait_for_selector("#sec-offer")
            overflow = page_m.evaluate(
                "Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - document.documentElement.clientWidth"
            )
            check(overflow <= 1, "no horizontal overflow at 375px viewport", f"overflow={overflow}px")
            check(len(console_errors_m) == 0, "zero console errors on mobile render", str(console_errors_m))
            page_m.screenshot(path=os.path.join(review_dir, "mobile-375.png"), full_page=True)
            page_m.close()

            page.close()
        finally:
            browser.close()

    print(f"\n{passed} passed, {failed} failed.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
