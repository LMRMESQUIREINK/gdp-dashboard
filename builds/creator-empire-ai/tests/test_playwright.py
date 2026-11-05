"""Real end-to-end test: serves standalone/ locally, drives the full
7-step flagship workflow in a real browser, and screenshots it at
desktop and mobile widths. Run with: python3 tests/test_playwright.py
"""
import http.server
import os
import socketserver
import threading
import time
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STANDALONE_DIR = os.path.join(HERE, "..", "standalone")
SCREENSHOT_DIR = os.path.join(HERE, "..", "review", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

try:
    chromium_mod = __import__("playwright.sync_api", fromlist=["sync_playwright"])
except ImportError:
    chromium_mod = __import__("playwright_core.sync_api", fromlist=["sync_playwright"])
sync_playwright = chromium_mod.sync_playwright

LAUNCH_KWARGS = {}
if os.environ.get("CHROME_PATH"):
    LAUNCH_KWARGS["executable_path"] = os.environ["CHROME_PATH"]

PORT = 8934
checks_passed = 0
checks_failed = 0


def check(cond, label):
    global checks_passed, checks_failed
    if cond:
        checks_passed += 1
        print(f"  pass  {label}")
    else:
        checks_failed += 1
        print(f"  FAIL  {label}")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STANDALONE_DIR, **kwargs)

    def log_message(self, *args):
        pass


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def start_server():
    server = ReusableTCPServer(("127.0.0.1", PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def main():
    server = start_server()
    time.sleep(0.3)
    console_errors = []

    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(**LAUNCH_KWARGS)
            except Exception as exc:
                print(f"Could not launch Chromium: {exc}")
                print("If this is a path issue, set CHROME_PATH to a chromium binary and re-run.")
                sys.exit(2)

            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.goto(f"http://127.0.0.1:{PORT}/index.html")
            page.wait_for_selector("#suite-grid .suite-card")

            # --- suite library renders honestly (6 live / 18 total) ---
            live_tags = page.locator(".status-live").count()
            planned_tags = page.locator(".status-planned").count()
            check(live_tags == 6, f"exactly 6 apps tagged LIVE in the rendered library (got {live_tags})")
            check(planned_tags == 12, f"exactly 12 apps tagged PLANNED (got {planned_tags})")

            # --- step 1: basics (defaults already filled in) ---
            check(page.locator("#panel-1").is_visible(), "step 1 panel is visible on load")
            page.click("#btn-to-2")
            page.wait_for_selector("#panel-2:visible")

            # --- step 2: hooks ---
            hook_cards = page.locator("#hook-list .pick-card")
            check(hook_cards.count() == 5, f"5 hook options rendered (got {hook_cards.count()})")
            check(page.locator("#btn-to-3").is_disabled(), "Next is disabled before a hook is picked")
            hook_cards.first.click()
            check(not page.locator("#btn-to-3").is_disabled(), "Next enables once a hook is picked")
            selected_hook_text = page.locator("#hook-list .pick-card.selected p").inner_text()
            page.click("#btn-to-3")
            page.wait_for_selector("#panel-3:visible")

            # --- step 3: script ---
            script_parts = page.locator("#script-parts .script-part")
            check(script_parts.count() == 7, f"7 script parts rendered (got {script_parts.count()})")
            # text_content(), not inner_text(): .part-name is CSS text-transform:uppercase,
            # which inner_text() reflects (post-render) but text_content() does not -- a
            # harness/measurement distinction, not a bug in the generated data itself.
            part_names = page.locator("#script-parts .part-name").all_text_contents()
            expected = ["Hook", "Problem", "Agitate", "Solution / Demo", "Proof", "Offer", "CTA"]
            check(part_names == expected, f"script parts are in the documented order (got {part_names})")
            hook_in_script = page.locator("#script-parts textarea").first.input_value()
            check(hook_in_script == selected_hook_text, "the script's Hook part matches the hook picked in step 2")
            page.click("#btn-to-4")
            page.wait_for_selector("#panel-4:visible")

            # --- step 4: storyboard ---
            scenes = page.locator("#storyboard .scene-card")
            check(scenes.count() >= 4, f"storyboard has at least 4 scenes for the 40s default (got {scenes.count()})")
            first_time = page.locator("#storyboard .scene-time").first.inner_text()
            check(first_time.startswith("00"), f"storyboard's first scene starts at 00s (got {first_time})")
            last_time = page.locator("#storyboard .scene-time").last.inner_text()
            check("40" in last_time, f"storyboard's last scene ends at the 40s default duration (got {last_time})")
            page.click("#btn-to-5")
            page.wait_for_selector("#panel-5:visible")

            # --- step 5: music / beat map ---
            page.select_option("#f-genre-intro", "Lo-fi")
            page.select_option("#f-genre-drop", "EDM")
            # Range inputs can't be Locator.fill()'d (not a text/select control) --
            # set .value via the DOM directly and fire the same "input" event the
            # real slider drag would dispatch.
            page.evaluate("document.getElementById('f-transition-pct').value = '50'")
            page.locator("#f-transition-pct").dispatch_event("input")
            page.wait_for_timeout(100)
            beat_label = page.locator("#f-transition-pct-out").inner_text()
            check("20s" in beat_label, f"50% of the 40s default duration computes to a 20s transition (got {beat_label!r})")
            drop_seg_text = page.locator(".beat-seg.drop").inner_text()
            check("EDM" in drop_seg_text, f"beat map reflects the chosen drop genre (got {drop_seg_text})")
            page.click("#btn-to-6")
            page.wait_for_selector("#panel-6:visible")

            # --- step 6: ads ---
            ad_cards = page.locator("#ad-list .pick-card")
            check(ad_cards.count() == 3, f"3 ad creatives rendered (got {ad_cards.count()})")
            page.click("#btn-to-export")
            page.wait_for_selector("#panel-7:visible")

            # --- step 7: export ---
            json_text = page.locator("#json-view").inner_text()
            check("project_id" in json_text, "exported JSON contains project_id")
            check("Goli Nutrition" in json_text, "exported JSON contains the real brand entered in step 1")
            check('"edition": "standalone"' in json_text, "exported JSON correctly tags itself as the standalone edition")
            check(selected_hook_text in json_text, "exported JSON contains the exact hook text selected earlier")

            with page.expect_download() as dl_info:
                page.click("#btn-export-json")
            download = dl_info.value
            check(download.suggested_filename == "campaign.json", "JSON export downloads as campaign.json")

            with page.expect_download() as dl_info2:
                page.click("#btn-export-md")
            download2 = dl_info2.value
            check(download2.suggested_filename == "campaign-brief.md", "Markdown export downloads as campaign-brief.md")

            # --- localStorage save ---
            page.once("dialog", lambda d: d.accept())
            page.click("#btn-save-local")
            page.wait_for_timeout(100)
            saved = page.evaluate("JSON.parse(localStorage.getItem('creator-empire-projects') || '[]').length")
            check(saved == 1, f"one project saved to localStorage (got {saved})")

            # --- screenshots + layout checks (desktop) ---
            page.goto(f"http://127.0.0.1:{PORT}/index.html")
            page.wait_for_selector("#suite-grid .suite-card")
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "desktop-1280.png"), full_page=True)

            scroll_w = page.evaluate("Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)")
            check(scroll_w <= 1280 + 1, f"no horizontal overflow at 1280px (scrollWidth={scroll_w})")

            # --- mobile ---
            page.set_viewport_size({"width": 375, "height": 800})
            page.wait_for_timeout(100)
            page.screenshot(path=os.path.join(SCREENSHOT_DIR, "mobile-375.png"), full_page=True)
            scroll_w_m = page.evaluate("Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)")
            check(scroll_w_m <= 375 + 1, f"no horizontal overflow at 375px (scrollWidth={scroll_w_m})")

            check(len(console_errors) == 0, f"zero console errors across the whole run (got {console_errors})")

            browser.close()
    finally:
        server.shutdown()

    print(f"\n{checks_passed} passed, {checks_failed} failed")
    sys.exit(1 if checks_failed else 0)


if __name__ == "__main__":
    main()
