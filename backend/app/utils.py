import os
from pathlib import Path
from typing import Tuple

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
    name = f"{first_name}_{last_name}".replace(' ', '_')
    return f"FORM201_{name}"

def bmi_folder_name(first_name: str, last_name: str) -> str:
    # Use required format: BMI_<First>_<Last>
    name = f"{first_name}_{last_name}".replace(' ', '_')
    return f"BMI_{name}"

def save_upload_file(uploaded, dest_path: str) -> str:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, 'wb') as buffer:
        buffer.write(uploaded.read())
    return dest_path
