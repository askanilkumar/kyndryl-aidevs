"""Thin runner so the command is nicer: `python run_agent.py "..."`."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import agent  # noqa: F401
if __name__ == "__main__":
    agent.main()
