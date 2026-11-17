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
from scraper import FetchError, scrape

st.set_page_config(page_title="ScrapeMaster 4.0", page_icon="🕷️")
st.title("ScrapeMaster 4.0")
st.caption("Scrape a page (or a short run of paginated pages), extract the fields you name, export the results.")

url = st.text_input("URL to scrape", placeholder="https://example.com/listings")

fields = st_tags(
    label="Fields to extract",
    text="Press enter to add a field",
    value=list(DEFAULT_FIELD_TAGS),
    key="fields",
)

col1, col2 = st.columns(2)
with col1:
    provider = st.selectbox("LLM provider", PROVIDERS, format_func=lambda p: PROVIDER_LABELS[p])
with col2:
    max_pages = st.number_input(
        "Pages to follow (via detected pagination)",
        min_value=MAX_PAGES_RANGE[0],
        max_value=MAX_PAGES_RANGE[1],
        value=1,
    )

if st.button("Scrape", type="primary", disabled=not (url and fields)):
    try:
        llm_client = LLMClient.for_provider(provider)
    except MissingAPIKeyError as exc:
        st.warning(str(exc))
    else:
        try:
            with st.spinner(f"Scraping up to {max_pages} page(s)..."):
                results = scrape(url, fields, llm_client, max_pages=int(max_pages))
        except FetchError as exc:
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
