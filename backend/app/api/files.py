from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..utils import safe_resolve_upload_path

router = APIRouter()


@router.get("/{stored_path:path}")
def get_uploaded_file(stored_path: str):
    try:
        file_path = safe_resolve_upload_path(stored_path)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=str(file_path), filename=file_path.name)
