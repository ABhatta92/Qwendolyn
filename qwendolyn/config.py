from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

WORKSPACE = PROJECT_ROOT / "workspace"
FILES = WORKSPACE / "files"
CACHE = WORKSPACE / "cache"
DB = WORKSPACE / "db"
SESSIONS = WORKSPACE / "sessions"
VECTOR_STORE = WORKSPACE / "vector_store"
LOGS = PROJECT_ROOT / "logs"

for path in (WORKSPACE, FILES, CACHE, DB, SESSIONS, VECTOR_STORE, LOGS):
    path.mkdir(parents=True, exist_ok=True)