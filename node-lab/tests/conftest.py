import sys
from pathlib import Path

# The package is not installed; tests import it (and their own helpers) from
# the repo checkout.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
