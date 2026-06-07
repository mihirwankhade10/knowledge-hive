import asyncio
import time
import requests
import json
import websockets
import os
import sys

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/query"

# Use the same API key if it's set in the env
API_KEY = os.getenv("API_KEY", "dev-secret-key-123")
HEADERS = {"X-API-Key": API_KEY}

def print_step(msg):
    print(f"\n[{time.strftime('%H:%M:%S')}] \033[94mINFO\033[0m: {msg}")

def print_success(msg):
    print(f"[{time.strftime('%H:%M:%S')}] \033[92mSUCCESS\033[0m: {msg}")

def print_error(msg):
    print(f"[{time.strftime('%H:%M:%S')}] \033[91mERROR\033[0m: {msg}")

async def test_websocket_query(question: str):
    print_step(f"Testing WebSocket Query: '{question}'")
    start = time.perf_counter()
    
    try:
        # Build WS URL with auth query param as frontend does
        auth_ws_url = f"{WS_URL}?api_key={API_KEY}"
        async with websockets.connect(auth_ws_url) as ws:
            # Send question
            await ws.send(json.dumps({"question": question}))
            
            # Wait for response
            while True:
                response = await ws.recv()
                data = json.loads(response)
                
                if data.get("type") == "agent_step":
                    # Ignore streaming intermediate steps for the test output
                    continue
                elif data.get("type") == "result":
                    end = time.perf_counter()
                    duration = end - start
                    print_success(f"WebSocket query answered in {duration:.2f}s")
                    print(f"Answer: {data.get('answer')[:100]}...")
                    print(f"Sources: {len(data.get('sources', []))}")
                    print(f"Confidence: {data.get('confidence', 0.0)}")
                    return True, duration
                elif data.get("type") == "error":
                    end = time.perf_counter()
                    duration = end - start
                    print_error(f"WebSocket returned error: {data.get('message')}")
                    return False, duration
    except Exception as e:
        print_error(f"WebSocket connection failed: {e}")
        return False, 0.0

def test_prometheus_metrics():
    print_step("Checking Prometheus /api/metrics endpoint")
    try:
        response = requests.get(f"{BASE_URL}/api/metrics", timeout=5)
        if response.status_code == 200:
            content = response.text
            if "http_requests_total" in content:
                print_success("Prometheus metrics successfully exposed and contain http_requests_total.")
                return True
            else:
                print_error("Prometheus metrics missing expected http_requests_total.")
                return False
        else:
            print_error(f"Metrics endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Metrics endpoint failed: {e}")
        return False

def test_health():
    print_step("Checking Health /api/health endpoint")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print_success(f"Health check passed: {response.json()}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False

async def run_all_tests():
    print_step("Starting End-to-End Tests for Knowledge Hive Phase 4")
    
    # 1. Health
    if not test_health():
        sys.exit(1)
        
    # 2. WebSocket Query (cold start)
    success1, dur1 = await test_websocket_query("What is machine learning?")
    
    # 3. WebSocket Query (cached - should be very fast)
    success2, dur2 = await test_websocket_query("What is machine learning?")
    
    if success1 and success2:
        if dur2 < dur1 * 0.1: # Cache should be at least 10x faster
            print_success(f"Caching verified! Cold: {dur1:.2f}s, Cached: {dur2:.2f}s")
        else:
            print_step(f"Cache time check: Cold {dur1:.2f}s, Cached {dur2:.2f}s (Ensure Redis is working)")

    # 4. Prometheus Metrics
    test_prometheus_metrics()
    
    print_step("End-to-End Tests Complete.")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
