from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import secrets
from starlette.middleware.sessions import SessionMiddleware
from app.api.personnel import router as personnel_router
from app.api.bmi import router as bmi_router
from app.api.auth import router as auth_router
from app.api.files import router as files_router
from app.database import init_db, migrate_db
from app.security import require_auth


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


def run_migrations():
    """Add missing columns to existing tables for migration."""
    # Create tables first (idempotent)
    try:
        init_db()
    except Exception as e:
        _handle_migration_error(e, "init_db")

    # Apply additive migrations (idempotent / best-effort)
    try:
        migrate_db()
    except Exception as e:
        _handle_migration_error(e, "migrate_db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run migrations on startup
    run_migrations()
    yield


app = FastAPI(title="CIDG RFU4A Personnel System API", lifespan=lifespan)

# Signed-cookie sessions for auth
session_secret = os.getenv("SESSION_SECRET") or os.getenv("SECRET_KEY")
if not session_secret:
    # Falls back to a per-process random key (sessions reset on restart)
    session_secret = secrets.token_urlsafe(32)
app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    session_cookie="cidg_session",
    same_site="lax",
    https_only=False,
)

# Configure CORS FIRST - must be added before routes for proper middleware chain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth")
app.include_router(files_router, prefix="/api/files", dependencies=[Depends(require_auth)])
app.include_router(personnel_router, prefix="/api/personnel", dependencies=[Depends(require_auth)])
app.include_router(bmi_router, prefix="/api/bmi", dependencies=[Depends(require_auth)])

@app.get("/")
def root():
    return {"message": "CIDG RFU4A Personnel System API running"}