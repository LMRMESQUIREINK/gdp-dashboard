"""ScrapeMaster 4.0's Streamlit UI -- the file the scaffold's own leftover
"streamlit run streamlit_app.py" (saved as a 0-byte filename rather than run)
was clearly meant to launch.
"""

from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st
from streamlit_tags import st_tags

from api_management import LLMClient, MissingAPIKeyError
from assets import DEFAULT_FIELD_TAGS, MAX_PAGES_RANGE, PROVIDER_LABELS, PROVIDERS
from scraper import FetchError, SeleniumUnavailableError, batch_scrape, preview_page, scrape

st.set_page_config(page_title="ScrapeMaster 4.0", page_icon="🕷️")
st.title("ScrapeMaster 4.0")
st.caption("Scrape a page (or a short run of paginated pages), extract the fields you name, export the results.")

batch_mode = st.toggle("Batch mode (multiple URLs, one field set, one sheet)")

if batch_mode:
    urls_text = st.text_area(
        "URLs to scrape (one per line)",
        placeholder="https://example.com/listings/1\nhttps://example.com/listings/2",
        height=120,
    )
    urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
else:
    url = st.text_input("URL to scrape", placeholder="https://example.com/listings")
    urls = [url] if url else []

fields = st_tags(
    label="Fields to extract",
    text="Press enter to add a field",
    value=list(DEFAULT_FIELD_TAGS),
    key="fields",
)

col1, col2, col3 = st.columns(3)
with col1:
    provider = st.selectbox("LLM provider", PROVIDERS, format_func=lambda p: PROVIDER_LABELS[p])
with col2:
    max_pages = st.number_input(
        "Pages to follow (via detected pagination)",
        min_value=MAX_PAGES_RANGE[0],
        max_value=MAX_PAGES_RANGE[1],
        value=1,
    )
with col3:
    use_selenium = st.checkbox("Browser rendering", help="Fetch via a real browser instead of a plain HTTP request, for JS-heavy sites.")

if fields:
    st.caption("Output columns for this run:")
    st.dataframe(pd.DataFrame([{"url": "...", "scraped_at": "...", **{f: "" for f in fields}}]), width="stretch")

preview_col, scrape_col = st.columns(2)
with preview_col:
    if st.button("Preview page", disabled=batch_mode or not urls):
        try:
            with st.spinner("Fetching and cleaning the page..."):
                snippet = preview_page(urls[0], use_selenium=use_selenium)
        except (FetchError, SeleniumUnavailableError) as exc:
            st.error(str(exc))
        else:
            st.text_area(
                "Cleaned page text (check your requested fields actually appear here before scraping)",
                snippet,
                height=200,
            )

with scrape_col:
    run_scrape = st.button("Scrape", type="primary", disabled=not (urls and fields))

if run_scrape:
    try:
        llm_client = LLMClient.for_provider(provider)
    except MissingAPIKeyError as exc:
        st.warning(str(exc))
    else:
        try:
            with st.spinner(f"Scraping {len(urls)} URL(s), up to {max_pages} page(s) each..."):
                if batch_mode:
                    results = batch_scrape(urls, fields, llm_client, max_pages=int(max_pages), use_selenium=use_selenium)
                else:
                    results = scrape(urls[0], fields, llm_client, max_pages=int(max_pages), use_selenium=use_selenium)
        except (FetchError, SeleniumUnavailableError) as exc:
            st.error(str(exc))
        else:
            if not results:
                st.info("No pages were scraped.")
            else:
                rows = [{"url": r.url, "scraped_at": r.scraped_at, **r.fields} for r in results]
                df = pd.DataFrame(rows)
                st.session_state["results_df"] = df

if "results_df" in st.session_state:
    df = st.session_state["results_df"]
    st.dataframe(df, width="stretch")

    csv_col, xlsx_col = st.columns(2)
    with csv_col:
        st.download_button(
            "Download CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="scrapemaster_results.csv",
            mime="text/csv",
        )
    with xlsx_col:
        buffer = BytesIO()
        df.to_excel(buffer, index=False, engine="openpyxl")
        st.download_button(
            "Download Excel",
            buffer.getvalue(),
            file_name="scrapemaster_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
