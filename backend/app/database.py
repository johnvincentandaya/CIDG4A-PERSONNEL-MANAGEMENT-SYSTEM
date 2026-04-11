import os
from pathlib import Path
from sqlalchemy import create_engine, text
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


def _is_expected_migration_error(err: Exception) -> bool:
    message = str(err).lower()
    return (
        'duplicate column name' in message
        or 'already exists' in message
        or 'no such table' in message
    )


def _handle_migration_error(err: Exception, step: str):
    if not _is_expected_migration_error(err):
        print(f"Migration warning ({step}): {err}")


def init_db():
    from . import models

    Base.metadata.create_all(bind=engine)


def migrate_db():
    """Add missing columns to existing tables for migration."""
    with engine.connect() as conn:
        # Check if bmi_records table exists and add missing columns
        try:
            # Add created_at column to bmi_records if it doesn't exist
            conn.execute(text("""
                ALTER TABLE bmi_records ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """))
            conn.commit()
        except Exception as e:
            _handle_migration_error(e, "add bmi_records.created_at")
        
        try:
            # Add updated_at column to bmi_records if it doesn't exist
            conn.execute(text("""
                ALTER TABLE bmi_records ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """))
            conn.commit()
        except Exception as e:
            _handle_migration_error(e, "add bmi_records.updated_at")
        
        try:
            # Add personnel_id column to bmi_records if it doesn't exist
            conn.execute(text("""
                ALTER TABLE bmi_records ADD COLUMN personnel_id INTEGER REFERENCES personnel(id)
            """))
            conn.commit()
        except Exception as e:
            _handle_migration_error(e, "add bmi_records.personnel_id")
        
        # Ensure indexes exist for performance
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bmi_personnel_id ON bmi_records(personnel_id)
            """))
            conn.commit()
        except Exception as e:
            _handle_migration_error(e, "create idx_bmi_personnel_id")
        
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_bmi_date_taken ON bmi_records(date_taken)
            """))
            conn.commit()
        except Exception as e:
            _handle_migration_error(e, "create idx_bmi_date_taken")

        # Ensure personnel table has required Form201 columns
        try:
            conn.execute(text('ALTER TABLE personnel ADD COLUMN badge_number VARCHAR'))
            conn.commit()
        except Exception as e:
            _handle_migration_error(e, "add personnel.badge_number")
        try:
            conn.execute(text('ALTER TABLE personnel ADD COLUMN qlf VARCHAR'))
            conn.commit()
        except Exception as e:
            _handle_migration_error(e, "add personnel.qlf")
        try:
            conn.execute(text('ALTER TABLE personnel ADD COLUMN date_of_reassignment TIMESTAMP'))
            conn.commit()
        except Exception as e:
            _handle_migration_error(e, "add personnel.date_of_reassignment")
        try:
            conn.execute(text('ALTER TABLE personnel ADD COLUMN designation VARCHAR'))
            conn.commit()
        except Exception as e:
            _handle_migration_error(e, "add personnel.designation")
        try:
            conn.execute(text('ALTER TABLE personnel ADD COLUMN date_of_designation TIMESTAMP'))
            conn.commit()
        except Exception as e:
            _handle_migration_error(e, "add personnel.date_of_designation")
        try:
            conn.execute(text('ALTER TABLE personnel ADD COLUMN highest_eligibility VARCHAR'))
            conn.commit()
        except Exception as e:
            _handle_migration_error(e, "add personnel.highest_eligibility")
        try:
            conn.execute(text('ALTER TABLE personnel ADD COLUMN contact_number VARCHAR'))
            conn.commit()
        except Exception as e:
            _handle_migration_error(e, "add personnel.contact_number")
        try:
            conn.execute(text('ALTER TABLE personnel ADD COLUMN birthdate TIMESTAMP'))
            conn.commit()
        except Exception as e:
            _handle_migration_error(e, "add personnel.birthdate")
        try:
            conn.execute(text('ALTER TABLE personnel ADD COLUMN religion VARCHAR'))
            conn.commit()
        except Exception as e:
            _handle_migration_error(e, "add personnel.religion")
        try:
            conn.execute(text('ALTER TABLE personnel ADD COLUMN section VARCHAR'))
            conn.commit()
        except Exception as e:
            _handle_migration_error(e, "add personnel.section")
