import os
from pathlib import Path
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "app.db"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
EXPORTS_DIR = Path(os.environ.get("EXPORTS_DIR", REPO_ROOT / "exports"))
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
