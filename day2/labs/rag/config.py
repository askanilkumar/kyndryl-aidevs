"""Settings. The OpenAI key goes in the .env file (see .env.example). No key? The labs still run in OFFLINE mode."""
import os
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(HERE, ".env"))
# key saved by set_key.py lives in your home folder, OUTSIDE the repo, so it can never be pushed to GitHub
load_dotenv(os.path.join(os.path.expanduser("~"), ".askrag.env"))

KB_DIR = os.path.join(HERE, "kb")
UPLOAD_DIR = os.path.join(HERE, "sample_uploads")
CACHE_DIR = os.path.join(HERE, ".cache")
EVAL_FILE = os.path.join(HERE, "evals", "runs.json")

CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4.1-mini")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
# optional: point chat to another OpenAI-compatible endpoint (for example the class LiteLLM gateway)
CHAT_BASE_URL = os.getenv("CHAT_BASE_URL") or None
CHAT_API_KEY = os.getenv("CHAT_API_KEY") or None

# USD per 1M tokens: (input, output). Check the OpenAI pricing page and edit if needed.
PRICES = {
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-5-mini": (0.25, 2.00),
    "text-embedding-3-small": (0.02, 0.0),
}
