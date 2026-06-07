import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from backend.services.llm_service import OpenRouterProvider
from backend.core.config import get_settings
from fastapi.testclient import TestClient
from backend.main import app

async def test_langfuse():
    print("Testing Langfuse Tracing...")
    settings = get_settings()

    provider = OpenRouterProvider(
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_model,
        base_url=settings.openrouter_base_url
    )
    
    print("Making LLM call to generate a trace...")
    try:
        # We use a very low max_tokens to make it fast
        resp = await provider.generate("What is 2+2? Answer in one word.", temperature=0.1, max_tokens=10)
        print(f"[OK] LLM Response: {resp}")
    except Exception as e:
        print(f"[WARN] LLM Call Failed (expected if API key is invalid): {e}")
    
    # Ensure Langfuse flushes traces to the cloud before exiting
    try:
        from langfuse import Langfuse
        Langfuse().flush()
        print("[OK] Langfuse trace flushed.")
    except Exception as e:
        print(f"[FAIL] Langfuse flush failed: {e}")

def test_prometheus():
    print("\nTesting Prometheus Metrics Endpoint...")
    client = TestClient(app)
    response = client.get("/api/metrics")
    if response.status_code == 200:
        print("[OK] /api/metrics returned 200 OK")
        content = response.text
        if "agent_execution_duration_seconds" in content or "http_requests_total" in content:
            print("[OK] Prometheus metrics format is valid and contains expected metrics.")
        else:
            print("[WARN] Metrics format might be missing some keys.")
    else:
        print(f"[FAIL] /api/metrics failed with status code {response.status_code}")

if __name__ == "__main__":
    test_prometheus()
    asyncio.run(test_langfuse())
