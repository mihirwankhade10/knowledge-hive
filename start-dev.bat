@echo off
echo ==========================================
echo Starting KnowledgeHive Development Swarm
echo ==========================================

:: 1. Start all Docker infrastructure in detached (background) mode
echo.
echo [1/3] Starting Docker services (Qdrant, Neo4j, Redis, Celery, Prometheus)...
docker compose up -d qdrant neo4j redis celery_worker prometheus

:: 2. Start the FastAPI Backend in a new command prompt window
echo.
echo [2/3] Starting FastAPI Backend in a new window...
start "KnowledgeHive Backend" cmd /k "call venv\Scripts\activate && uvicorn backend.main:app --reload --port 8000"

:: 3. Start the React Frontend in a new command prompt window
echo.
echo [3/3] Starting Vite Frontend in a new window...
start "KnowledgeHive Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================
echo Done! Backend and Frontend terminals have been opened.
echo ==========================================
pause
