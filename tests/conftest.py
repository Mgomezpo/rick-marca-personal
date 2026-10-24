"""
Pytest configuration and environment initialization.
Ensures hermetic test environment: fast in-memory database and deterministic execution.
"""
import os
import pytest

# Enforce test environment before importing any application modules
os.environ["APP_ENV"] = "test"
os.environ["MOCK_LLM"] = "true"
