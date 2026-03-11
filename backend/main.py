from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
from app.api.personnel import router as personnel_router
from app.api.bmi import router as bmi_router

app = FastAPI(title="CIDG RFU4A Personnel System API")

# mount uploads so frontend can access files (use project-level uploads folder)
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / 'uploads'
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

app.include_router(personnel_router, prefix="/api/personnel")
app.include_router(bmi_router, prefix="/api/bmi")

# add CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "CIDG RFU4A Personnel System API running"}