"""Settings for AskNova. No keys here: keys come from the app sidebar or OS env vars."""
from pathlib import Path

LABS_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = LABS_DIR / "prompts"
LOG_FILE = LABS_DIR / "logs" / "requests.jsonl"
RELEASES_FILE = LABS_DIR / "releases.json"

# Price per 1 million tokens in USD (input, output). EXAMPLE values - check the OpenAI pricing page.
PRICES = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4.1-mini": (0.40, 1.60),
    "offline": (0.0, 0.0),
}
DEFAULT_MODEL = "gpt-4o-mini"

MAX_STEPS = 5          # the agent stops after 5 LLM calls (loop guard, from Day 4)
EVAL_GATE = 0.80       # 80% of eval cases must pass before a release


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    p_in, p_out = PRICES.get(model, PRICES[DEFAULT_MODEL])
    return (tokens_in * p_in + tokens_out * p_out) / 1_000_000
