import os
from pathlib import Path
import re
from typing import Optional, Tuple

# Project root is one level above `backend/`
PROJECT_ROOT = Path(__file__).resolve().parents[2]

def get_uploads_dir() -> Path:
    # Allow override for deployment (e.g. Docker volume)
    env_dir = os.getenv("UPLOADS_DIR")
    if env_dir:
        return Path(env_dir).resolve()
    return PROJECT_ROOT / "uploads"

def uploads_rel(*parts: str) -> str:
    # Path stored in DB / returned to frontend (portable)
    p = Path("uploads").joinpath(*parts)
    return p.as_posix()

def uploads_abs(*parts: str) -> Path:
    # Path used for writing files on disk
    return get_uploads_dir().joinpath(*parts)


_SAFE_COMPONENT_RE = re.compile(r"[^A-Za-z0-9_-]+")


def safe_path_component(value: Optional[str], fallback: str = "UNKNOWN") -> str:
    """Return a filesystem-safe single path component.

    This prevents path traversal (e.g. '../') and removes path separators.
    """
    raw = (value or "").strip()
    if not raw:
        return fallback

    # Replace spaces and drop any remaining unsafe characters.
    cleaned = raw.replace(" ", "_")
    cleaned = cleaned.replace("/", "_").replace("\\", "_")
    cleaned = _SAFE_COMPONENT_RE.sub("_", cleaned)
    cleaned = cleaned.strip("._")
    cleaned = cleaned.replace("..", "_")

    if not cleaned or cleaned in {".", ".."}:
        return fallback
    return cleaned


def safe_resolve_upload_path(stored_path: str) -> Path:
    """Resolve a stored path (typically starting with 'uploads/...') to an absolute path.

    Raises ValueError if the resolved path would escape the uploads directory.
    """
    if not stored_path:
        raise ValueError("Empty path")

    normalized = str(stored_path).replace("\\", "/")
    idx = normalized.lower().find("uploads/")
    rel = normalized[idx + len("uploads/"):] if idx >= 0 else normalized.lstrip("/")
    rel_parts = [p for p in rel.split("/") if p and p not in {".", ".."}]

    uploads_root = get_uploads_dir().resolve()
    candidate = uploads_root.joinpath(*rel_parts).resolve()
    try:
        candidate.relative_to(uploads_root)
    except Exception as e:
        raise ValueError("Invalid upload path") from e
    return candidate

def ensure_upload_folders():
    uploads_abs("form_201").mkdir(parents=True, exist_ok=True)
    uploads_abs("bmi").mkdir(parents=True, exist_ok=True)
    # create unit folders for known units to ensure structure
    units = ['RHQ','CAVITE','LAGUNA','BATANGAS','RIZAL','QUEZON']
    for u in units:
        uploads_abs('form_201', u).mkdir(parents=True, exist_ok=True)
        uploads_abs('bmi', u).mkdir(parents=True, exist_ok=True)

def personnel_folder_name(first_name: str, last_name: str) -> str:
    # Use required format: FORM201_<First>_<Last>
    first = safe_path_component(first_name, "FIRST")
    last = safe_path_component(last_name, "LAST")
    return f"FORM201_{first}_{last}"

def bmi_folder_name(first_name: str, last_name: str, middle_initial: Optional[str] = None) -> str:
    # Use required format: BMI_<First>_<MI>_<Last> when MI is provided
    first = safe_path_component(first_name, "FIRST")
    last = safe_path_component(last_name, "LAST")
    mi = safe_path_component(middle_initial, "MI") if middle_initial else ''
    if mi:
        return f"BMI_{first}_{mi}_{last}"
    return f"BMI_{first}_{last}"

def save_upload_file(uploaded, dest_path: str) -> str:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, 'wb') as buffer:
        buffer.write(uploaded.read())
    return dest_path
