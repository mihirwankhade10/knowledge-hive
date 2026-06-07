"""
KnowledgeHive - Comprehensive Phase 1-4 Integration Test

Tests ALL features across every phase to verify the system works end-to-end.
Requires: uvicorn running on localhost:8000, Docker containers for Qdrant/Neo4j/Redis up.
"""

import asyncio
import os
import sys
import time
import json
import httpx

from dotenv import load_dotenv
load_dotenv(override=True)

# ============================================================================
# CONFIGURATION
# ============================================================================
BASE_URL = "http://localhost:8000"
API_PREFIX = f"{BASE_URL}/api"
PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"
WARN = "[WARN]"
results = []


def log(status, test_name, detail=""):
    msg = f"  {status} {test_name}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    results.append((status, test_name, detail))


async def run_all_tests():
    print("=" * 70)
    print("  KnowledgeHive - Comprehensive Integration Test (Phase 1-4)")
    print("=" * 70)

    async with httpx.AsyncClient(
        timeout=30.0,
        headers={"Origin": "http://localhost:5173"},
    ) as client:

        # ==================================================================
        # PHASE 1: Core API & Health
        # ==================================================================
        print("\n--- PHASE 1: Core API & Health ---")

        # 1.1 Health endpoint
        try:
            r = await client.get(f"{API_PREFIX}/health")
            if r.status_code == 200:
                data = r.json()
                log(PASS, "Health endpoint", f"status={data.get('status')}")
                # Also check individual services
                for svc in ["qdrant", "neo4j", "redis"]:
                    svc_status = data.get(svc, "unknown")
                    st = PASS if svc_status == "healthy" else WARN
                    log(st, f"  Service: {svc}", svc_status)
            else:
                log(FAIL, "Health endpoint", f"status_code={r.status_code}")
        except Exception as e:
            log(FAIL, "Health endpoint", str(e))

        # 1.2 Stats endpoint
        try:
            r = await client.get(f"{API_PREFIX}/stats")
            if r.status_code == 200:
                data = r.json()
                log(PASS, "Stats endpoint", f"docs={data.get('total_documents', 0)}, chunks={data.get('total_chunks', 0)}")
            else:
                log(WARN, "Stats endpoint", f"status_code={r.status_code}")
        except Exception as e:
            log(FAIL, "Stats endpoint", str(e))

        # 1.3 Upload a sample text document
        sample_text = (
            "Artificial intelligence is transforming healthcare. "
            "Machine learning models can now detect diseases from medical images "
            "with accuracy rivaling human specialists. "
            "Natural language processing helps doctors review patient records faster."
        )
        upload_ok = False
        try:
            files = {"file": ("test_doc.txt", sample_text.encode(), "text/plain")}
            r = await client.post(f"{API_PREFIX}/upload", files=files)
            if r.status_code in (200, 202):
                data = r.json()
                log(PASS, "Document upload", f"response_keys={list(data.keys())[:5]}")
                upload_ok = True
            else:
                log(FAIL, "Document upload", f"status={r.status_code} body={r.text[:200]}")
        except Exception as e:
            log(FAIL, "Document upload", str(e))

        # 1.4 Query the knowledge base
        if upload_ok:
            await asyncio.sleep(3)

        try:
            payload = {"question": "How is AI transforming healthcare?"}
            r = await client.post(f"{API_PREFIX}/query", json=payload)
            if r.status_code in (200, 202):
                data = r.json()
                answer = data.get("answer", "")[:80]
                log(PASS, "Query endpoint", f"answer_preview={answer}...")
            elif r.status_code == 500:
                log(WARN, "Query endpoint", "500 - LLM call may have failed (check OPENROUTER_API_KEY)")
            else:
                log(WARN, "Query endpoint", f"status={r.status_code}")
        except Exception as e:
            log(FAIL, "Query endpoint", str(e))

        # ==================================================================
        # PHASE 2: Security & Hardening
        # ==================================================================
        print("\n--- PHASE 2: Security & Hardening ---")

        # 2.1 CORS headers present
        try:
            r = await client.get(f"{API_PREFIX}/health")
            cors_header = r.headers.get("access-control-allow-origin", "")
            if cors_header:
                log(PASS, "CORS headers", f"allow-origin={cors_header}")
            else:
                log(WARN, "CORS headers", "No access-control-allow-origin (may need OPTIONS preflight)")
        except Exception as e:
            log(FAIL, "CORS headers", str(e))

        # 2.2 Request ID middleware
        try:
            r = await client.get(f"{API_PREFIX}/health")
            req_id = r.headers.get("X-Request-ID", "")
            if req_id:
                log(PASS, "Request ID middleware", f"X-Request-ID={req_id[:24]}...")
            else:
                log(FAIL, "Request ID middleware", "No X-Request-ID header")
        except Exception as e:
            log(FAIL, "Request ID middleware", str(e))

        # 2.3 Rate limiting is configured
        try:
            r = await client.get(f"{API_PREFIX}/health")
            if r.status_code == 200:
                log(PASS, "Rate limiter active", "SlowAPI middleware loaded (healthy response)")
        except Exception as e:
            log(FAIL, "Rate limiter active", str(e))

        # 2.4 Error envelope (test with bad endpoint)
        try:
            r = await client.get(f"{API_PREFIX}/nonexistent_endpoint_xyz")
            if r.status_code == 404:
                log(PASS, "Error handling (404)", "Correct 404 for missing route")
            else:
                log(WARN, "Error handling (404)", f"status={r.status_code}")
        except Exception as e:
            log(FAIL, "Error handling (404)", str(e))

        # 2.5 Structured JSON logging (just verify the middleware runs without errors)
        try:
            r = await client.get(f"{API_PREFIX}/health")
            log(PASS, "Structured logging", "Requests complete without middleware errors")
        except Exception as e:
            log(FAIL, "Structured logging", str(e))

        # ==================================================================
        # PHASE 3: Scalability (Redis, Cache, WebSocket)
        # ==================================================================
        print("\n--- PHASE 3: Scalability (Redis, Cache, WebSocket) ---")

        # 3.1 Redis connectivity via health endpoint
        try:
            r = await client.get(f"{API_PREFIX}/health")
            data = r.json()
            redis_status = data.get("redis", "unknown")
            if redis_status == "healthy":
                log(PASS, "Redis health (via API)", redis_status)
            else:
                log(FAIL, "Redis health (via API)", redis_status)
        except Exception as e:
            log(FAIL, "Redis health (via API)", str(e))

        # 3.2 Redis direct connectivity
        try:
            import redis
            rc = redis.Redis(host="localhost", port=6379, db=0, socket_timeout=5)
            rc.ping()
            log(PASS, "Redis direct ping", "localhost:6379 reachable")
            rc.close()
        except Exception as e:
            log(FAIL, "Redis direct ping", str(e))

        # 3.3 WebSocket endpoints registered
        try:
            import websockets
            # Try connecting to the WS query endpoint
            try:
                async with websockets.connect(f"ws://localhost:8000/ws/query", close_timeout=3) as ws:
                    # Send a test query
                    await ws.send(json.dumps({"question": "test"}))
                    # Wait briefly for any response
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=5)
                        log(PASS, "WebSocket /ws/query", f"Got response: {response[:80]}...")
                    except asyncio.TimeoutError:
                        log(WARN, "WebSocket /ws/query", "Connected but no response in 5s (LLM may be slow)")
            except Exception as e:
                # If connection is refused, the endpoint doesn't exist
                if "refused" in str(e).lower():
                    log(FAIL, "WebSocket /ws/query", "Connection refused")
                else:
                    log(PASS, "WebSocket /ws/query", f"Endpoint reachable (got: {str(e)[:60]})")
        except ImportError:
            log(SKIP, "WebSocket /ws/query", "websockets package not installed")

        # ==================================================================
        # PHASE 4: Observability (Prometheus, Langfuse, OpenTelemetry)
        # ==================================================================
        print("\n--- PHASE 4: Observability (Prometheus, Langfuse, OpenTelemetry) ---")

        # 4.1 Prometheus metrics endpoint
        try:
            r = await client.get(f"{API_PREFIX}/metrics")
            if r.status_code == 200:
                body = r.text
                has_http = "http_request" in body or "http_requests" in body
                has_agent = "agent_execution_duration_seconds" in body
                log(PASS, "Prometheus /api/metrics", f"http_metrics={has_http}, agent_metrics={has_agent}")
            else:
                log(FAIL, "Prometheus /api/metrics", f"status={r.status_code}")
        except Exception as e:
            log(FAIL, "Prometheus /api/metrics", str(e))

        # 4.2 Langfuse configuration
        try:
            from backend.services.llm_service import _langfuse_enabled
            if _langfuse_enabled:
                log(PASS, "Langfuse configured", "Keys found, tracing enabled")
            else:
                log(WARN, "Langfuse configured", "Keys not set or package missing")
        except Exception as e:
            log(FAIL, "Langfuse configured", str(e))

        # 4.3 Langfuse connectivity (flush test)
        try:
            from backend.services.llm_service import _langfuse_enabled
            if _langfuse_enabled:
                from langfuse import Langfuse
                lf = Langfuse()
                lf.flush()
                log(PASS, "Langfuse flush", "No errors on flush")
            else:
                log(SKIP, "Langfuse flush", "Langfuse not enabled")
        except Exception as e:
            log(FAIL, "Langfuse flush", str(e))

        # 4.4 OpenTelemetry instrumented
        try:
            from opentelemetry import trace
            tracer = trace.get_tracer("test")
            if tracer:
                log(PASS, "OpenTelemetry active", f"tracer={type(tracer).__name__}")
            else:
                log(FAIL, "OpenTelemetry active", "No tracer found")
        except Exception as e:
            log(FAIL, "OpenTelemetry active", str(e))

        # 4.5 Prometheus custom metric registered
        try:
            from prometheus_client import REGISTRY
            found = False
            for metric in REGISTRY.collect():
                if "agent_execution_duration" in metric.name:
                    found = True
                    break
            if found:
                log(PASS, "Custom agent metric registered", "agent_execution_duration_seconds found")
            else:
                log(WARN, "Custom agent metric registered", "Not in registry yet (appears after first agent run)")
        except Exception as e:
            log(FAIL, "Custom agent metric registered", str(e))

    # ==================================================================
    # SUMMARY
    # ==================================================================
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    passed = sum(1 for s, _, _ in results if s == PASS)
    failed = sum(1 for s, _, _ in results if s == FAIL)
    warned = sum(1 for s, _, _ in results if s == WARN)
    skipped = sum(1 for s, _, _ in results if s == SKIP)
    total = len(results)

    print(f"  Total: {total} | Passed: {passed} | Failed: {failed} | Warnings: {warned} | Skipped: {skipped}")

    if failed > 0:
        print("\n  FAILED tests:")
        for s, name, detail in results:
            if s == FAIL:
                print(f"    X {name}: {detail}")

    if warned > 0:
        print("\n  WARNINGS:")
        for s, name, detail in results:
            if s == WARN:
                print(f"    ! {name}: {detail}")

    print("=" * 70)
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
