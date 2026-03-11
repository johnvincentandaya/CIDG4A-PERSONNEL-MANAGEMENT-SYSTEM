import os
from pathlib import Path
from typing import Tuple

def ensure_upload_folders():
    Path("uploads/form_201").mkdir(parents=True, exist_ok=True)
    Path("uploads/bmi").mkdir(parents=True, exist_ok=True)

def personnel_folder_name(first_name: str, last_name: str) -> str:
    name = f"{first_name}_{last_name}".replace(' ', '_')
    return f"FORM201_{name}"

def bmi_folder_name(first_name: str, last_name: str) -> str:
    name = f"{first_name}_{last_name}".replace(' ', '_')
    return f"BMI_{name}"

def save_upload_file(uploaded, dest_path: str) -> str:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, 'wb') as buffer:
        buffer.write(uploaded.read())
    return dest_path
