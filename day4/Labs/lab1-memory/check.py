"""Run:  python check.py           -> runs all Lab 1 tests
       python check.py 1b          -> runs only Lab 1B tests, etc.
"""
import subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
tgt = sys.argv[1] if len(sys.argv) > 1 else ""
args = [sys.executable, "-m", "pytest", str(HERE / "tests"), "-v"]
if tgt:
    args += ["-k", tgt]
sys.exit(subprocess.call(args))
