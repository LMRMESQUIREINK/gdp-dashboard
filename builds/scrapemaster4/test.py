"""Real, run tests for every file this build actually wrote.

No real API key, no live network: a local http.server fixture serves real
HTML over loopback (so fetch_html/clean_html_to_text/pagination_detector
exercise real HTTP, not a mock), and api_management's provider calls are
exercised through LLMClient's injectable call_fn (the same "mocked client"
convention this project's other builds use for a live model/API dependency
that can't be reached from this sandbox).
"""

import http.server
import tempfile
import threading
import time
from pathlib import Path

import api_management as apim
import pagination_detector as pg
import scraper

PASS = 0
FAIL = 0


def run(name, fn):
    global PASS, FAIL
    try:
        fn()
        print(f"PASS  {name}")
        PASS += 1
    except AssertionError as e:
        print(f"FAIL  {name}: {e}")
        FAIL += 1


# --- A real local HTTP fixture server ---------------------------------------

FIXTURE_DIR = Path(tempfile.mkdtemp(prefix="scrapemaster_test_"))

ARTICLE_HTML = """
<html><head><title>Widget Co</title></head>
<body>
<nav><a href="/">Home</a><a href="/about">About</a></nav>
<article>
  <h1>Super Widget</h1>
  <p>Price: $19.99</p>
  <p>The Super Widget is our best-selling gadget, built to last.</p>
</article>
<footer>Copyright 2026 Widget Co. All rights reserved.</footer>
</body></html>
"""

PAGE1_HTML = """
<html><body>
<div class="listing"><h2>Item One</h2></div>
<div class="listing"><h2>Item Two</h2></div>
<a rel="next" href="/page2.html">Next &rarr;</a>
</body></html>
"""

PAGE2_HTML = """
<html><body>
<div class="listing"><h2>Item Three</h2></div>
</body></html>
"""

TEXT_NEXT_HTML = """
<html><body>
<p>Some content.</p>
<a href="/older.html">Older posts</a>
</body></html>
"""

NO_NEXT_HTML = """<html><body><p>Last page, nothing more here.</p></body></html>"""

(FIXTURE_DIR / "article.html").write_text(ARTICLE_HTML)
(FIXTURE_DIR / "page1.html").write_text(PAGE1_HTML)
(FIXTURE_DIR / "page2.html").write_text(PAGE2_HTML)
(FIXTURE_DIR / "text_next.html").write_text(TEXT_NEXT_HTML)
(FIXTURE_DIR / "no_next.html").write_text(NO_NEXT_HTML)


class _Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FIXTURE_DIR), **kwargs)

    def log_message(self, *args):
        pass


_server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
_port = _server.server_address[1]
_thread = threading.Thread(target=_server.serve_forever, daemon=True)
_thread.start()
time.sleep(0.2)

BASE_URL = f"http://127.0.0.1:{_port}"


# --- scraper.fetch_html -------------------------------------------------------

def test_fetch_html_real_local_request():
    html = scraper.fetch_html(f"{BASE_URL}/article.html")
    assert "Super Widget" in html


def test_fetch_html_raises_fetch_error_on_404_after_retries():
    try:
        scraper.fetch_html(f"{BASE_URL}/does-not-exist.html", max_retries=1, retry_delay=0)
        raise AssertionError("expected FetchError")
    except scraper.FetchError:
        pass


# --- scraper.clean_html_to_text ----------------------------------------------

def test_clean_html_to_text_strips_nav_and_footer_keeps_article():
    text = scraper.clean_html_to_text(ARTICLE_HTML)
    assert "Super Widget" in text
    assert "best-selling" in text
    assert "Copyright 2026" not in text
    assert "About" not in text


# --- pagination_detector -----------------------------------------------------

def test_detect_next_page_via_rel_next_resolves_relative_url():
    url = pg.detect_next_page_url(f"{BASE_URL}/page1.html", PAGE1_HTML)
    assert url == f"{BASE_URL}/page2.html"


def test_detect_next_page_via_link_text():
    url = pg.detect_next_page_url(f"{BASE_URL}/text_next.html", TEXT_NEXT_HTML)
    assert url == f"{BASE_URL}/older.html"


def test_detect_next_page_returns_none_when_no_next_link():
    url = pg.detect_next_page_url(f"{BASE_URL}/no_next.html", NO_NEXT_HTML)
    assert url is None


# --- api_management -----------------------------------------------------------

def test_load_api_key_missing_raises_plain_english_error():
    try:
        apim.load_api_key("openai", env={})
        raise AssertionError("expected MissingAPIKeyError")
    except apim.MissingAPIKeyError as e:
        assert "OPENAI_API_KEY" in str(e)


def test_load_api_key_placeholder_is_rejected():
    try:
        apim.load_api_key("groq", env={"GROQ_API_KEY": "your_api_key_here"})
        raise AssertionError("expected MissingAPIKeyError")
    except apim.MissingAPIKeyError:
        pass


def test_load_api_key_real_looking_key_is_accepted():
    key = apim.load_api_key("gemini", env={"GEMINI_API_KEY": "AIzaSyFakeButRealShaped123"})
    assert key == "AIzaSyFakeButRealShaped123"


def test_truncate_text_limits_length_via_fallback_path():
    # The real tiktoken encoding download is blocked by this sandbox's
    # egress proxy (openaipublic.blob.core.windows.net), confirmed directly
    # -- so this exercises the documented approximate-truncation fallback,
    # not the exact-tiktoken path, which is unverified from here.
    long_text = "word " * 5000
    truncated = apim.truncate_text(long_text, max_tokens=10)
    assert len(truncated) <= 10 * apim._APPROX_CHARS_PER_TOKEN
    assert len(truncated) < len(long_text)


def test_truncate_text_leaves_short_text_untouched():
    short = "just a few words"
    assert apim.truncate_text(short, max_tokens=1000) == short


def test_llm_client_extract_with_mocked_call_parses_json():
    def fake_call(model, prompt):
        assert "title" in prompt and "price" in prompt
        return '{"title": "Super Widget", "price": "$19.99"}'

    client = apim.LLMClient(provider="openai", model="gpt-4o-mini", call_fn=fake_call)
    result = client.extract("some page text", ["title", "price"])
    assert result == {"title": "Super Widget", "price": "$19.99"}


def test_llm_client_extract_strips_markdown_code_fence():
    def fake_call(model, prompt):
        return '```json\n{"title": "X"}\n```'

    client = apim.LLMClient(provider="openai", model="gpt-4o-mini", call_fn=fake_call)
    result = client.extract("text", ["title"])
    assert result == {"title": "X"}


def test_llm_client_extract_missing_field_defaults_to_empty_string():
    def fake_call(model, prompt):
        return '{"title": "X"}'

    client = apim.LLMClient(provider="openai", model="gpt-4o-mini", call_fn=fake_call)
    result = client.extract("text", ["title", "price"])
    assert result == {"title": "X", "price": ""}


def test_llm_client_extract_raises_on_non_json_response():
    def fake_call(model, prompt):
        return "Sure! Here's your data: title is Super Widget."

    client = apim.LLMClient(provider="openai", model="gpt-4o-mini", call_fn=fake_call)
    try:
        client.extract("text", ["title"])
        raise AssertionError("expected ExtractionError")
    except apim.ExtractionError:
        pass


# --- scraper.scrape end-to-end, real HTTP + mocked LLM -----------------------

def test_scrape_single_page_against_real_local_server():
    def fake_call(model, prompt):
        return '{"title": "Super Widget", "price": "$19.99"}'

    client = apim.LLMClient(provider="openai", model="m", call_fn=fake_call)
    results = scraper.scrape(f"{BASE_URL}/article.html", ["title", "price"], client, max_pages=1)
    assert len(results) == 1
    assert results[0].fields == {"title": "Super Widget", "price": "$19.99"}
    assert results[0].url == f"{BASE_URL}/article.html"


def test_scrape_follows_real_pagination_up_to_max_pages():
    calls = []

    def fake_call(model, prompt):
        calls.append(prompt)
        return '{"item": "x"}'

    client = apim.LLMClient(provider="openai", model="m", call_fn=fake_call)
    results = scraper.scrape(f"{BASE_URL}/page1.html", ["item"], client, max_pages=2)
    assert len(results) == 2
    assert results[0].url == f"{BASE_URL}/page1.html"
    assert results[1].url == f"{BASE_URL}/page2.html"
    assert len(calls) == 2


def test_scrape_stops_at_max_pages_even_if_more_pagination_exists():
    def fake_call(model, prompt):
        return '{"item": "x"}'

    client = apim.LLMClient(provider="openai", model="m", call_fn=fake_call)
    results = scraper.scrape(f"{BASE_URL}/page1.html", ["item"], client, max_pages=1)
    assert len(results) == 1
    assert results[0].url == f"{BASE_URL}/page1.html"


def test_scrape_stops_naturally_when_no_next_page_found():
    def fake_call(model, prompt):
        return '{"item": "x"}'

    client = apim.LLMClient(provider="openai", model="m", call_fn=fake_call)
    results = scraper.scrape(f"{BASE_URL}/no_next.html", ["item"], client, max_pages=5)
    assert len(results) == 1


TESTS = [
    test_fetch_html_real_local_request,
    test_fetch_html_raises_fetch_error_on_404_after_retries,
    test_clean_html_to_text_strips_nav_and_footer_keeps_article,
    test_detect_next_page_via_rel_next_resolves_relative_url,
    test_detect_next_page_via_link_text,
    test_detect_next_page_returns_none_when_no_next_link,
    test_load_api_key_missing_raises_plain_english_error,
    test_load_api_key_placeholder_is_rejected,
    test_load_api_key_real_looking_key_is_accepted,
    test_truncate_text_limits_length_via_fallback_path,
    test_truncate_text_leaves_short_text_untouched,
    test_llm_client_extract_with_mocked_call_parses_json,
    test_llm_client_extract_strips_markdown_code_fence,
    test_llm_client_extract_missing_field_defaults_to_empty_string,
    test_llm_client_extract_raises_on_non_json_response,
    test_scrape_single_page_against_real_local_server,
    test_scrape_follows_real_pagination_up_to_max_pages,
    test_scrape_stops_at_max_pages_even_if_more_pagination_exists,
    test_scrape_stops_naturally_when_no_next_page_found,
]

if __name__ == "__main__":
    for t in TESTS:
        run(t.__name__, t)
    print(f"\n{PASS}/{PASS + FAIL} passed")
    _server.shutdown()
    if FAIL:
        raise SystemExit(1)
