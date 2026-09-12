"""Shared HTTP client config for talking to backend/.

One place for the base URL and the timeout so loader.py and mock_backend.py
don't each redeclare them. Override the URL with the BACKEND_URL env var
(e.g. when the backend runs somewhere other than localhost:8000).
"""
from __future__ import annotations

import os

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT_SECONDS = 10


class BackendUnavailableError(RuntimeError):
    """Raised when the backend can't be reached or returns an error."""
