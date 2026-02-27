"""Pytest fixtures for backend tests."""

import os

os.environ.setdefault("SECRET_KEY", "test-secret-for-e2e")
os.environ.setdefault("DEV_SKIP_EMAIL", "true")
os.environ.setdefault("TESTING", "1")

import pytest

pytest_plugins = ["pytest_asyncio"]
