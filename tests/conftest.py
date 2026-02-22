"""Shared pytest configuration for scaffold tests."""

from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OVERRIDE = os.environ.get("PYCIE_SRC")
SRC = Path(OVERRIDE).expanduser().resolve() if OVERRIDE else ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
