"""
Tests for Phase 2 Rate Limiting (slowapi).
"""

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.rate_limit import limiter

import uuid

# Add a test route with a very low limit to easily trigger 429
@app.get("/dummy-rate-limit/{test_id}")
@limiter.limit("1/minute")
async def dummy_rate_limit_route(request: Request, test_id: str):
    return {"status": "ok"}

client = TestClient(app, raise_server_exceptions=False)

def test_rate_limit_exceeded_format():
    """Trigger a rate limit manually to verify the ErrorResponse format."""
    test_id = str(uuid.uuid4())
    # First request should succeed
    resp1 = client.get(f"/dummy-rate-limit/{test_id}")
    assert resp1.status_code == 200

    # Second request should fail with 429
    resp2 = client.get(f"/dummy-rate-limit/{test_id}")
    assert resp2.status_code == 429
    
    data = resp2.json()
    assert data["error"] == "rate_limit_exceeded"
    assert "Rate limit exceeded" in data["message"]
    assert "request_id" in data
