#!/usr/bin/env python3
"""Convenience executable for MockSieve."""
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from mocksieve.cli import main

if __name__ == "__main__":
    sys.exit(main())
