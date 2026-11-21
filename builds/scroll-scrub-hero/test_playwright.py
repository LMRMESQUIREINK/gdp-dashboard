"""
Drives the real built page with a real Chromium browser (this sandbox's
pre-installed Playwright build), running most of scrub-pipeline.md's own
Phase 9 self-test checklist against this implementation: the video
loads and scrubs, the flick test on the caption bands, reduced motion
toggled live in both directions, the page staying complete when the
video is missing, screenshots at desktop and phone widths, and a console
check. This is the "prove it, don't assume it" step the spec itself
calls for, run for real rather than described.

Run with:
    python3 test_playwright.py
"""
from __future__ import annotations

import http.server
import json
import socketserver
import sys
import threading
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
PORT = 8999
socketserver.TCPServer.allow_reuse_address = True

failures: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"ok   - {name}")
    else:
        msg = f"FAIL - {name}" + (f" ({detail})" if detail else "")
        print(msg)
        failures.append(msg)


def serve():
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(HERE), **kw)
    with socketserver.TCPServer(("127.0.0.1", PORT), handler) as httpd:
        httpd.serve_forever()


def main() -> int:
    server_thread = threading.Thread(target=serve, daemon=True)
    server_thread.start()
    time.sleep(0.3)

    url = f"http://127.0.0.1:{PORT}/index.html"

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")

        # ---------- Desktop: scrub + flick test + console + screenshots ----------
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.add_init_script("window.__SCRUB_HERO_VIDEO_URL_OVERRIDE__ = 'assets/hero-scrub-test.webm';")
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: console_errors.append(str(exc)))
        page.goto(url)
        page.wait_for_selector(".hero-stage.video-ready", timeout=10000)
        check("hero video reaches video-ready (Blob loaded, canplay fired)", True)

        band_opacity = lambda n: float(page.eval_on_selector(f"#band{n}", "el => getComputedStyle(el).opacity"))

        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.3)
        check("band 0 visible at scroll top", band_opacity(0) > 0.5, f"got {band_opacity(0)}")

        total_scroll = page.evaluate("document.getElementById('heroWrap').offsetHeight - window.innerHeight")
        page.evaluate(f"window.scrollTo(0, {total_scroll} * 0.98)")
        time.sleep(0.4)
        check("band 2 visible near scroll bottom", band_opacity(2) > 0.5, f"got {band_opacity(2)}")

        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.3)

        # Flick test, replicating scrub-pipeline.md's own harness exactly.
        max_opacity = {0: 0.0, 1: 0.0, 2: 0.0}
        for step, count in ((120, 12), (240, 8), (360, 6)):
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.2)
            for _ in range(count):
                page.evaluate(f"window.scrollBy(0, {step})")
                time.sleep(0.12)
                for n in (0, 1, 2):
                    op = band_opacity(n)
                    max_opacity[n] = max(max_opacity[n], op)
        for n in (0, 1, 2):
            check(f"flick test: band {n} reaches full visibility at some flick size", max_opacity[n] > 0.9, f"max observed {max_opacity[n]:.2f}")

        screenshot_dir = HERE / "review" / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.3)
        page.screenshot(path=str(screenshot_dir / "desktop-hero-top.png"))
        page.evaluate(f"window.scrollTo(0, {total_scroll} * 0.5)")
        time.sleep(0.3)
        page.screenshot(path=str(screenshot_dir / "desktop-hero-mid.png"))
        page.evaluate(f"window.scrollTo(0, {total_scroll} + 600)")
        time.sleep(0.3)
        page.screenshot(path=str(screenshot_dir / "desktop-below-fold.png"))
        check("desktop screenshots captured", True)

        # ---------- The one interactive moment ----------
        page.wait_for_selector("#pullBtn")
        page.eval_on_selector("#pullBtn", "el => el.scrollIntoView({block: 'center'})")
        time.sleep(0.3)
        box = page.eval_on_selector("#pullBtn", "el => { const r = el.getBoundingClientRect(); return {x: r.x + r.width/2, y: r.y + r.height/2}; }")
        page.mouse.move(box["x"], box["y"])
        page.mouse.down()
        time.sleep(0.4)
        mid_pull = page.eval_on_selector("#pullBtn", "el => el.style.getPropertyValue('--pull')")
        page.mouse.up()
        time.sleep(0.05)
        just_released = page.eval_on_selector("#pullBtn", "el => el.style.getPropertyValue('--pull')")
        time.sleep(0.6)
        eased_back = page.eval_on_selector("#pullBtn", "el => el.style.getPropertyValue('--pull')")
        check("press-and-hold builds progress while held", float(mid_pull) > 0.2, f"mid-hold pull={mid_pull}")
        check("releasing early eases progress back down, never snaps to zero instantly", float(eased_back) < float(just_released), f"{just_released} -> {eased_back}")

        # Hold to completion.
        page.mouse.move(box["x"], box["y"])
        page.mouse.down()
        time.sleep(1.4)
        page.mouse.up()
        result_text = page.eval_on_selector("#pullResult", "el => el.textContent")
        check("completing the hold lights up a real completion state", "pulled" in result_text.lower(), f"got {result_text!r}")

        check("desktop: zero console errors", len(console_errors) == 0, str(console_errors))
        page.close()

        # ---------- Reduced motion, toggled live, both directions ----------
        page2 = browser.new_page(viewport={"width": 1440, "height": 900})
        page2.emulate_media(reduced_motion="reduce")
        page2.goto(url)
        time.sleep(0.5)
        is_scrub_on = page2.evaluate("window.__scrubHeroTest__.isScrubOn()")
        check("reduced-motion-from-the-start: scrub starts disabled", is_scrub_on is False)

        page2.emulate_media(reduced_motion="no-preference")
        time.sleep(0.5)
        is_scrub_on_after = page2.evaluate("window.__scrubHeroTest__.isScrubOn()")
        check("flipping reduced motion OFF mid-session re-arms the scrub", is_scrub_on_after is True)

        page2.emulate_media(reduced_motion="reduce")
        time.sleep(0.5)
        pinned_opacity = float(page2.eval_on_selector("#band2", "el => getComputedStyle(el).opacity"))
        check("flipping reduced motion ON mid-session pins bands to their final state", pinned_opacity == 1.0, f"got {pinned_opacity}")
        page2.close()

        # ---------- Complete without the video ----------
        page3 = browser.new_page(viewport={"width": 1440, "height": 900})
        page3.add_init_script("window.__SCRUB_HERO_VIDEO_URL_OVERRIDE__ = 'assets/hero-scrub-test.webm';")
        page3.route("**/hero-scrub-test.webm", lambda route: route.abort())
        page3.goto(url)
        time.sleep(1.0)
        has_failed_class = page3.eval_on_selector(".hero-stage", "el => el.classList.contains('video-failed')")
        poster_visible = page3.eval_on_selector(".poster", "el => getComputedStyle(el).opacity !== '0'")
        cta_reachable = page3.eval_on_selector("a[href='#menu']", "el => !!el") if page3.query_selector("a[href='#menu']") else False
        check("video-missing: page marks itself video-failed instead of hanging", has_failed_class)
        check("video-missing: poster stays visible as the complete fallback", poster_visible)
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        page3.screenshot(path=str(screenshot_dir / "desktop-video-missing.png"))
        page3.close()

        # ---------- Mobile: static-hero gate ----------
        page4 = browser.new_page(viewport={"width": 375, "height": 812}, has_touch=True, is_mobile=True)
        page4.goto(url)
        time.sleep(0.5)
        is_scrub_on_mobile = page4.evaluate("window.__scrubHeroTest__.isScrubOn()")
        check("phone width (375px) falls into the static-hero gate, scrub disabled", is_scrub_on_mobile is False)

        static_hero_visible = page4.eval_on_selector("#staticHero", "el => getComputedStyle(el).display !== 'none'")
        bands_hidden = page4.eval_on_selector("#band0", "el => getComputedStyle(el).display === 'none'")
        static_hero_text = page4.eval_on_selector("#staticHero h1", "el => el.textContent")
        check("mobile: the single composed static-hero block is shown (not the three scroll bands)", static_hero_visible, f"display check failed, text={static_hero_text!r}")
        check("mobile: the scroll bands are hidden, not stacked/cramped into the hero box", bands_hidden)

        # Scroll-segmented real-position captures, not a single stitched
        # full_page=True shot: this project has already hit a real
        # Chromium bug where a sticky-positioned element bleeds bottom-
        # of-page content into the top of a stitched full-page capture
        # (documented in /builds/prop-firm-dashboard's sales-page work).
        # .hero-stage is only un-stickied by CSS once a gate matches, so
        # segmented capture is the safe method regardless.
        page4.screenshot(path=str(screenshot_dir / "mobile-static-hero-top.png"))
        page_height = page4.evaluate("document.body.scrollHeight")
        page4.evaluate(f"window.scrollTo(0, {page_height})")
        time.sleep(0.3)
        page4.screenshot(path=str(screenshot_dir / "mobile-static-hero-bottom.png"))
        page4.close()

        browser.close()

    print(f"\nscreenshots written to {screenshot_dir}")
    if failures:
        print(f"\n{len(failures)} check(s) failed:")
        for f in failures:
            print(" ", f)
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
