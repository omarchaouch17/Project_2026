"""Loaded by pytest before all tests: tests NEVER use the real database (Neon/PostgreSQL)."""
import os

os.environ.pop("DATABASE_URL", None)
