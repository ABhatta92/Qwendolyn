from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

WORKSPACE = PROJECT_ROOT / "workspace"
FILES = WORKSPACE / "files"
CACHE = WORKSPACE / "cache"
DB = WORKSPACE / "db"
VECTOR_STORE = WORKSPACE / "vector_store"
SCRIPTS = WORKSPACE / "scripts"
WEB = WORKSPACE / "web"
LOGS = PROJECT_ROOT / "logs"

for path in (WORKSPACE, FILES, CACHE, DB, WEB, VECTOR_STORE, LOGS, SCRIPTS):
    path.mkdir(parents=True, exist_ok=True)