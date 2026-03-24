# app package - export app from main at parent level
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from main import app

__all__ = ["app"]
