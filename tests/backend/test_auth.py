"""
Tests for Phase 2 API Key Authentication.
"""

import pytest
from fastapi import FastAPI, Depends, Request
from fastapi.testclient import TestClient

from backend.core.auth import require_api_key
from backend.core.config import get_settings
from backend.core.exceptions import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)

@app.get("/protected")
async def protected_route(api_key: str = Depends(require_api_key)):
    return {"message": "Success", "key": api_key}


client = TestClient(app)


def test_auth_disabled_when_no_key_configured(monkeypatch):
    """When API_KEY is empty in config, auth should be bypassed."""
    settings = get_settings()
    monkeypatch.setattr(settings, "api_key", "")
    
    response = client.get("/protected")
    assert response.status_code == 200
    assert response.json()["key"] is None


def test_auth_success_with_valid_key(monkeypatch):
    """When API_KEY is configured, requests with the matching header succeed."""
    settings = get_settings()
    monkeypatch.setattr(settings, "api_key", "secret123")
    
    response = client.get("/protected", headers={"X-API-Key": "secret123"})
    assert response.status_code == 200
    assert response.json()["key"] == "secret123"


def test_auth_fails_with_invalid_key(monkeypatch):
    """When API_KEY is configured, wrong keys return 401."""
    settings = get_settings()
    monkeypatch.setattr(settings, "api_key", "secret123")
    
    response = client.get("/protected", headers={"X-API-Key": "wrongkey"})
    assert response.status_code == 401
    assert response.json()["error"] == "authentication_error"


def test_auth_fails_when_header_missing(monkeypatch):
    """When API_KEY is configured, missing header returns 401."""
    settings = get_settings()
    monkeypatch.setattr(settings, "api_key", "secret123")
    
    response = client.get("/protected")
    assert response.status_code == 401
    assert response.json()["error"] == "authentication_error"
