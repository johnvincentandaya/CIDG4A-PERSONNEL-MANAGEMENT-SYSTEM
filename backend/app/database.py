import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/app -> backend
DEFAULT_SQLITE_PATH = BASE_DIR / "cidg_dev.db"
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_SQLITE_PATH}"

# Prefer DATABASE_URL from environment, but fall back to local SQLite file.
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

engine_kwargs = {"echo": False}
if DATABASE_URL.startswith("sqlite"):
    # Needed for SQLite when used across threads (e.g., FastAPI dependencies)
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    from . import models

    Base.metadata.create_all(bind=engine)
