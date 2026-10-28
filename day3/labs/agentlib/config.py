"""Settings for Day 3. Values come from .env (copy .env.example to .env)."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:  # dotenv is optional
    pass

ROOT = Path(__file__).resolve().parent.parent

# --- Model (your Day 1 gateway). Leave blank to run OFFLINE with the stand-in model.
GATEWAY_BASE_URL = os.getenv("GATEWAY_BASE_URL", "").strip()
GATEWAY_KEY = os.getenv("GATEWAY_KEY", "").strip()
CHAT_MODEL = os.getenv("CHAT_MODEL", "chat-llm").strip()

# --- Memory rules (the numbers every team must choose on purpose)
MAX_MESSAGES = int(os.getenv("MAX_MESSAGES", "12"))        # short-term window
TTL_SHORT = int(os.getenv("TTL_SHORT", "1800"))            # 30 min chat history
TTL_PROFILE = int(os.getenv("TTL_PROFILE", str(30 * 24 * 3600)))  # 30 days facts

# --- Agent safety limits
MAX_STEPS = int(os.getenv("MAX_STEPS", "6"))
BUDGET_USD = float(os.getenv("BUDGET_USD", "0.05"))        # per question

# --- Where the in-memory Redis saves its snapshot so memory survives a restart
SNAPSHOT = Path(os.getenv("REDIS_SNAPSHOT", str(ROOT / "redis_snapshot.json")))

# EXAMPLE prices, USD per 1M tokens (input, output). Put your real gateway prices here.
PRICES = {
    "chat-llm": (0.60, 2.50),
    "chat-llm-b": (0.30, 1.20),
    "local-small": (0.05, 0.10),
    "offline-standin": (0.60, 2.50),   # priced like chat-llm so the cost numbers feel real
}


def online() -> bool:
    return bool(GATEWAY_BASE_URL and GATEWAY_KEY)
