"""Shared constants for the Streamlit UI -- kept separate from streamlit_app.py
so the provider/model list and default field examples have one place to live,
matching what an empty `assets.py` in the original scaffold was clearly meant
to hold."""

from api_management import PROVIDER_DEFAULT_MODELS

PROVIDERS = list(PROVIDER_DEFAULT_MODELS.keys())

PROVIDER_LABELS = {
    "openai": "OpenAI",
    "groq": "Groq",
    "gemini": "Google Gemini",
}

DEFAULT_FIELD_TAGS = ["title", "price", "description"]

MAX_PAGES_RANGE = (1, 20)
