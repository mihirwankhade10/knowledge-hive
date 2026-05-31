import asyncio
import httpx
import websockets
import json
import time
import subprocess
import os

# Create dummy document
with open("test_doc.txt", "w") as f:
    f.write("Machine learning is a subset of artificial intelligence. It focuses on building systems that learn from data. Neural networks are a key technology in modern ML.")

async def test_integration():
    print("--- Starting Integration Test ---")
    
    # 1. Start Celery worker in background
    print("Starting Celery worker...")
    env = os.environ.copy()
    
    f_celery = open("celery.log", "w")
    celery_process = subprocess.Popen(
        ["venv\\Scripts\\celery.exe", "-A", "backend.worker.celery_app", "worker", "--loglevel=info", "--pool=solo"],
        stdout=f_celery,
        stderr=subprocess.STDOUT,
        env=env
    )
    
    # 2. Start Uvicorn in background
    print("Starting Uvicorn backend...")
    f_uvicorn = open("uvicorn.log", "w")
    uvicorn_process = subprocess.Popen(
        ["venv\\Scripts\\uvicorn.exe", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=f_uvicorn,
        stderr=subprocess.STDOUT,
        env=env
    )
    
    try:
        # Wait for backend to start
        print("Waiting for backend to start (10s)...")
        await asyncio.sleep(10)
        
        async with httpx.AsyncClient() as client:
            # Check health
            print("Checking health...")
            health_res = await client.get("http://127.0.0.1:8000/api/health")
            print(f"Health: {health_res.json()}")
            
            # 3. Upload file
            print("Uploading document...")
            with open("test_doc.txt", "rb") as f:
                res = await client.post(
                    "http://127.0.0.1:8000/api/upload",
                    files={"file": ("test_doc.txt", f, "text/plain")}
                )
            
            assert res.status_code == 202, f"Expected 202, got {res.status_code}"
            data = res.json()
            task_id = data["task_id"]
            print(f"Upload returned task_id: {task_id}")
            
            # 4. Connect to WS for task tracking
            print("Connecting to WebSocket...")
            ws_url = f"ws://127.0.0.1:8000/ws/task/{task_id}"
            completed = False
            
            try:
                async with websockets.connect(ws_url) as ws:
                    while not completed:
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=30.0)
                            payload = json.loads(msg)
                            status = payload.get("status")
                            step = payload.get("step")
                            prog = payload.get("progress")
                            print(f"WS Update -> status: {status}, step: {step}, progress: {prog}%")
                            if status in ("COMPLETED", "FAILED"):
                                completed = True
                                if status == "COMPLETED":
                                    print("Task successfully completed via WebSocket!")
                                else:
                                    print(f"Task failed: {payload.get('error')}")
                        except asyncio.TimeoutError:
                            print("WS timeout, waiting...")
                        except websockets.exceptions.ConnectionClosed:
                            print("WS closed unexpectedly, falling back to polling...")
                            break
            except Exception as e:
                print(f"WS connection failed: {e}, falling back to polling...")
                
            # Fallback to polling if WS didn't finish
            while not completed:
                print("Polling task status...")
                res = await client.get(f"http://127.0.0.1:8000/api/upload/status/{task_id}")
                data = res.json()
                status = data.get("status")
                print(f"Poll Update -> status: {status}, step: {data.get('step')}, progress: {data.get('progress')}%")
                if status in ("COMPLETED", "FAILED"):
                    completed = True
                    if status == "COMPLETED":
                        print("Task successfully completed via Polling!")
                    else:
                        print(f"Task failed: {data.get('error')}")
                else:
                    await asyncio.sleep(5)
            
            # 5. Wait a bit for DB indexing
            await asyncio.sleep(2)
            
            # 6. Test Query + caching
            question = "What is machine learning?"
            print(f"Querying: {question}")
            
            start_time = time.time()
            q_res = await client.post("http://127.0.0.1:8000/api/query", json={"question": question})
            q_data = q_res.json()
            q_time_1 = time.time() - start_time
            print(f"First query completed in {q_time_1:.2f}s")
            
            start_time = time.time()
            q_res2 = await client.post("http://127.0.0.1:8000/api/query", json={"question": question})
            q_data2 = q_res2.json()
            q_time_2 = time.time() - start_time
            print(f"Second query (identical) completed in {q_time_2:.2f}s")
            
            if q_time_2 < q_time_1 * 0.5:
                print("Cache hit was significantly faster! Phase 3 caching is working.")
            else:
                print("Cache hit might not have triggered properly or network is noisy.")

    finally:
        # Cleanup
        print("Shutting down processes...")
        uvicorn_process.terminate()
        celery_process.terminate()
        uvicorn_process.wait(timeout=5)
        celery_process.wait(timeout=5)
        f_celery.close()
        f_uvicorn.close()
        if os.path.exists("test_doc.txt"):
            os.remove("test_doc.txt")
        print("Integration test complete.")

if __name__ == "__main__":
    asyncio.run(test_integration())
