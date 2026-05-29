import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post('http://localhost:8000/api/query', json={'question': 'who is mohit?', 'history': []}, timeout=30.0)
            print(f"Status: {r.status_code}")
            print(f"Response: {r.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
