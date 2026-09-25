import json
from pathlib import Path

# Single source of truth shared with the backend: <repo>/shared/tags.json.
TAGS_FILE = Path(__file__).resolve().parents[3] / "shared" / "tags.json"

TAG_GROUPS: dict[str, list[str]] = json.loads(TAGS_FILE.read_text(encoding="utf-8"))
ALLOWED_TAGS: frozenset[str] = frozenset(tag for tags in TAG_GROUPS.values() for tag in tags)
