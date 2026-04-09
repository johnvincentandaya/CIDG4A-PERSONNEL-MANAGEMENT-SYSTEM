from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager
import os
from app.api.personnel import router as personnel_router
from app.api.bmi import router as bmi_router
from sqlalchemy import create_engine, text
from app.database import migrate_db


def run_migrations():
    """Add missing columns to existing tables for migration."""
    BASE_DIR = Path(__file__).resolve().parent.parent
    db_path = BASE_DIR / "cidg_dev.db"
    
    if not db_path.exists():
        return
    
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    
    with engine.connect() as conn:
        # Check if bmi_records table exists and add missing columns
        try:
            conn.execute(text("""
                ALTER TABLE bmi_records ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """))
            conn.commit()
            print("Migration: Added created_at column to bmi_records")
        except Exception as e:
            pass  # Column might already exist
        
        try:
            conn.execute(text("""
                ALTER TABLE bmi_records ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """))
            conn.commit()
            print("Migration: Added updated_at column to bmi_records")
        except Exception as e:
            pass  # Column might already exist
        
        try:
            conn.execute(text("""
                ALTER TABLE bmi_records ADD COLUMN personnel_id INTEGER REFERENCES personnel(id)
            """))
            conn.commit()
            print("Migration: Added personnel_id column to bmi_records")
        except Exception as e:
            pass  # Column might already exist
        
        # Ensure indexes exist for performance
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bmi_personnel_id ON bmi_records(personnel_id)
            """))
            conn.commit()
        except Exception:
            pass
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bmi_date_taken ON bmi_records(date_taken)
            """))
            conn.commit()
        except Exception:
            pass
    
    engine.dispose()
    try:
        # apply higher-level migrations for new personnel columns
        migrate_db()
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run migrations on startup
    run_migrations()
    yield


app = FastAPI(title="CIDG RFU4A Personnel System API", lifespan=lifespan)

# Configure CORS FIRST - must be added before routes for proper middleware chain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount uploads so frontend can access files (use project-level uploads folder)
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / 'uploads'
os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

app.include_router(personnel_router, prefix="/api/personnel")
app.include_router(bmi_router, prefix="/api/bmi")

@app.get("/")
def root():
    return {"message": "CIDG RFU4A Personnel System API running"}