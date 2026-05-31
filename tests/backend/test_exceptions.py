"""
Tests for Phase 2 global exception handlers and custom exceptions.
"""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from backend.core.exceptions import (
    register_exception_handlers,
    KnowledgeHiveError,
    UnsupportedFileTypeError,
    AuthenticationError,
)

# Setup a dummy app for testing handlers
app = FastAPI()
register_exception_handlers(app)

@app.get("/test-kh-error")
async def kh_error():
    raise KnowledgeHiveError(message="Custom base error", detail={"test": 123})

@app.get("/test-unsupported")
async def unsupported_error():
    raise UnsupportedFileTypeError(".exe", [".pdf", ".txt"])

@app.get("/test-auth")
async def auth_error():
    raise AuthenticationError()

@app.get("/test-unhandled")
async def unhandled_error():
    raise ValueError("This is a raw python error that should be caught by the 500 handler")


client = TestClient(app, raise_server_exceptions=False)


def test_base_knowledgehive_error():
    response = client.get("/test-kh-error")
    assert response.status_code == 500
    data = response.json()
    assert data["error"] == "internal_error"
    assert data["message"] == "Custom base error"
    assert data["detail"] == {"test": 123}
    assert "request_id" in data


def test_unsupported_file_type_error():
    response = client.get("/test-unsupported")
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "unsupported_file_type"
    assert ".exe" in data["message"]
    assert data["detail"]["extension"] == ".exe"


def test_authentication_error():
    response = client.get("/test-auth")
    assert response.status_code == 401
    data = response.json()
    assert data["error"] == "authentication_error"


def test_unhandled_exception_hides_internals():
    response = client.get("/test-unhandled")
    assert response.status_code == 500
    data = response.json()
    assert data["error"] == "internal_error"
    # Should not expose the ValueError message to the client
    assert "ValueError" not in data["message"]
    assert "An unexpected error occurred" in data["message"]
