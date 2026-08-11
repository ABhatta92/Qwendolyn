from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QWENDOLYN_ROOT = PROJECT_ROOT / "qwendolyn"

WORKSPACE = PROJECT_ROOT / "workspace"
FILES = WORKSPACE / "files"
CACHE = WORKSPACE / "cache"
DB = WORKSPACE / "db"
VECTOR_STORE = WORKSPACE / "vector_store"
SCRIPTS = WORKSPACE / "scripts"
WEB = WORKSPACE / "web"
TEMP = WORKSPACE / "temp"
LOGS = PROJECT_ROOT / "logs"
AGENT_ROOT = PROJECT_ROOT / "qwendolyn" / "agent"

for path in (WORKSPACE, FILES, CACHE, DB, WEB, VECTOR_STORE, LOGS, SCRIPTS, TEMP, AGENT_ROOT):
    path.mkdir(parents=True, exist_ok=True)