import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["REDIS_SNAPSHOT"] = str(Path(tempfile.gettempdir()) / "day3_pytest_snapshot.json")
