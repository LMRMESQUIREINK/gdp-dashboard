"""One-off manual visual check of steps 5 (beat map, absolute-positioned
CSS) and 7 (export/JSON view) -- not part of the automated assertions,
just a second look-at-it-with-eyes pass per the screenshot-before-done
rule, since DOM-text assertions can't catch a visually broken beat-map
bar."""
import http.server
import os
import socketserver
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STANDALONE_DIR = os.path.join(HERE, "..", "standalone")
SCREENSHOT_DIR = os.path.join(HERE, "..", "review", "screenshots")

try:
    chromium_mod = __import__("playwright.sync_api", fromlist=["sync_playwright"])
except ImportError:
    chromium_mod = __import__("playwright_core.sync_api", fromlist=["sync_playwright"])
sync_playwright = chromium_mod.sync_playwright

PORT = 8936


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STANDALONE_DIR, **kwargs)

    def log_message(self, *args):
        pass


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


server = ReusableTCPServer(("127.0.0.1", PORT), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
time.sleep(0.3)

chrome_path = os.environ.get("CHROME_PATH")
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=chrome_path) if chrome_path else p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 1100})
    page.goto(f"http://127.0.0.1:{PORT}/index.html")
    page.wait_for_selector("#suite-grid .suite-card")

    page.click("#btn-to-2")
    page.locator("#hook-list .pick-card").first.click()
    page.click("#btn-to-3")
    page.click("#btn-to-4")
    page.click("#btn-to-5")
    page.wait_for_selector("#panel-5:visible")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step5-music.png"), full_page=True)

    page.click("#btn-to-6")
    page.click("#btn-to-export")
    page.wait_for_selector("#panel-7:visible")
    page.screenshot(path=os.path.join(SCREENSHOT_DIR, "step7-export.png"), full_page=True)

    browser.close()

server.shutdown()
print("wrote step5-music.png and step7-export.png")
