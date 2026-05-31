# 🐝 KnowledgeHive

**Enterprise Knowledge Swarm powered by Multi-Agent AI**

KnowledgeHive is an AI-powered enterprise knowledge platform that uses a swarm of specialized agents to ingest, understand, organize, retrieve, validate, and explain enterprise knowledge.

## ✨ Features

- **📄 Document Upload** — Upload PDF, DOCX, and TXT files
- **🧠 Intelligent Chunking** — Recursive text splitting with overlap
- **🔢 Vector Embeddings** — Semantic embeddings via Sentence Transformers
- **🕸️ Knowledge Graphs** — Entity/relationship extraction stored in Neo4j
- **🔍 Hybrid Retrieval** — Vector search (Qdrant) + graph traversal (Neo4j)
- **✅ Evidence Validation** — LLM-powered relevance scoring and confidence
- **💬 Cited Answers** — Answers with source citations and confidence scores
- **🐝 Agent Flow Visualization** — Real-time agent execution pipeline view

## 🏗️ Architecture

```
                    ┌─────────────┐
                    │   Frontend  │
                    │  React+Vite │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   FastAPI   │
                    │   Backend   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
    ┌─────────▼──┐  ┌──────▼─────┐  ┌──▼──────────┐
    │  Ingestion │  │  Retrieval │  │  Validation  │
    │   Agent    │  │   Agent    │  │   Agent      │
    └─────┬──────┘  └──────┬─────┘  └──┬───────────┘
          │                │            │
    ┌─────▼──┐      ┌──────▼─────┐  ┌──▼──────────┐
    │  Graph │      │  Response  │  │  LLM Layer   │
    │  Agent │      │   Agent    │  │ (OpenRouter)  │
    └────┬───┘      └────────────┘  └──────────────┘
         │
  ┌──────┴──────┐     ┌───────────┐
  │   Qdrant    │     │   Neo4j   │
  │  (Vectors)  │     │  (Graph)  │
  └─────────────┘     └───────────┘
```

### Agent Swarm

| Agent | Responsibility |
|-------|---------------|
| **Ingestion Agent** | Parse → Chunk → Embed → Store in Qdrant |
| **Graph Agent** | Extract entities & relationships → Store in Neo4j |
| **Retrieval Agent** | Semantic search + graph traversal → Merged context |
| **Validation Agent** | Score evidence → Rank sources → Confidence score |
| **Response Agent** | Generate cited answer from validated context |

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose

### 1. Clone & Setup

```bash
git clone https://github.com/your-org/knowledge-hive.git
cd knowledge-hive

# Create environment file
cp .env.example .env
# Edit .env with your OPENROUTER_API_KEY
```

### 2. Start Infrastructure (Docker)

```bash
docker compose up -d qdrant neo4j
```

### 3. Backend Setup

```bash
# Create virtual environment
py -3.11 -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run backend
uvicorn backend.main:app --reload --port 8000
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 5. Open the App

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## 🐳 Docker Compose (Full Stack)

```bash
docker compose up --build
```

This starts all services: Backend, Frontend, Qdrant, and Neo4j.

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload` | Upload a document (PDF/DOCX/TXT) |
| `POST` | `/api/query` | Ask a question |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/stats` | Knowledge base statistics |

## 🧪 Testing

```bash
# Run all backend tests
python -m pytest tests/backend/ -v

# Run with coverage
python -m pytest tests/backend/ -v --cov=backend --cov-report=term
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------:|
| **Backend** | FastAPI, Pydantic, Uvicorn |
| **Frontend** | React, Vite, Chakra UI |
| **LLM** | OpenRouter (Azure OpenAI/OpenAI ready) |
| **Embeddings** | Sentence Transformers |
| **Vector DB** | Qdrant |
| **Graph DB** | Neo4j Community |
| **Cache** | Redis 7 |
| **Task Queue** | Celery + Redis |
| **Real-time** | WebSocket (FastAPI native) |
| **Containerization** | Docker, Docker Compose |

## 📋 Project Structure

```
knowledge-hive/
├── backend/
│   ├── agents/          # AI Agent classes
│   ├── api/             # FastAPI routes
│   ├── core/            # Config, DI
│   ├── models/          # Pydantic models
│   ├── services/        # LLM, Embedding, Qdrant, Neo4j
│   ├── utils/           # Parsers, chunking, prompts
│   └── main.py          # App entry point
├── frontend/
│   └── src/
│       ├── components/  # React components
│       ├── pages/       # Dashboard, Chat, AgentFlow
│       └── services/    # API client
├── tests/
│   └── backend/         # pytest tests
├── docker/              # Dockerfiles
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## 🏗️ Architecture Decisions

To ensure all team members align on the design, here are the core architecture decisions:

| Decision | Choice | Rationale |
|---|---|---|
| **Agent pattern** | Custom Python classes with `BaseAgent` ABC | Simple, testable, easy to swap for AutoGen/LangGraph later |
| **LLM abstraction** | `LLMProvider` protocol + `OpenRouterProvider` | Provider pattern allows swapping OpenAI/Azure later |
| **Embedding abstraction** | `EmbeddingProvider` protocol + `SentenceTransformerProvider` | Same pattern, locally run for MVP |
| **Vector store abstraction** | `VectorStore` protocol + `QdrantVectorStore` | Qdrant via `qdrant-client` |
| **Graph store abstraction** | `GraphStore` protocol + `Neo4jGraphStore` | Neo4j via `neo4j` driver |
| **Dependency injection** | FastAPI `Depends()` + `dependencies.py` | Lightweight, framework-native |
| **Async** | Full async FastAPI, Qdrant client, Neo4j driver | Production-ready from day one |
| **Frontend state** | TanStack Query for server state, React Context for UI state | Industry standard, minimal boilerplate |
| **Chunking** | Recursive text splitter (custom) | No heavy LangChain dependency in MVP |

## 📈 Detailed Implementation Plan & Roadmap

This project is built in phases to ensure a stable, scalable architecture. Below is the detailed implementation plan so all team members can follow the agreed-upon structure.

### Phase 1: Working MVP (✅ Completed)
The foundation of the KnowledgeHive swarm.
- [x] **Project Setup**: Git, Docker (`docker-compose.yml`, multi-stage Dockerfiles), Environment Variables, and `requirements.txt`.
- [x] **Backend Core**: FastAPI app with CORS, DI `dependencies.py`, and Pydantic `config.py`.
- [x] **Backend Models & Utils**: Document & Query schemas, Recursive text chunker (512 tokens), PDF/DOCX parsers.
- [x] **Backend Services**: LLM (`OpenRouterProvider`), Embeddings (`SentenceTransformerProvider`), Qdrant VectorStore, Neo4j GraphStore.
- [x] **Agent Swarm Implementation**: 
  - `IngestionAgent`: Parse -> Chunk -> Embed -> Qdrant
  - `GraphAgent`: Extract Entities/Relationships -> Neo4j
  - `RetrievalAgent`: Vector Search + Graph Traversal
  - `ValidationAgent`: LLM Relevance Scoring
  - `ResponseAgent`: Answer Generation with Citations
- [x] **API Routes**: `/api/upload`, `/api/query`, `/api/health`
- [x] **Frontend MVP**: Vite + React + Chakra UI setup. Created Dashboard (stats, upload), Chat (answers, citations), and AgentFlow (visual pipeline).
- [x] **Tests**: Pytest suite for parsers, chunking, agents, and API endpoints.

### Phase 2: Architecture Hardening (✅ Completed)
- [x] Centralized structured logging (JSON structured logs via python-json-logger)
- [x] Global exception handlers in FastAPI for standardized error responses
- [x] Input validation hardening (file size limits, MIME-type verification, filename sanitization)
- [x] Rate limiting on API endpoints (slowapi)
- [x] Basic Authentication/Authorization layer (API key)

### Phase 3: Scalability (✅ Completed)
- [x] Redis integration for caching LLM responses and query results (with configurable TTLs)
- [x] Celery + Redis for background document ingestion (async upload with task tracking)
- [x] WebSocket for real-time Agent Status updates (`/ws/task/{id}`, `/ws/query`)
- [x] Redis-backed rate limiting (persists across restarts)
- [x] Cache-aware LLM service (identical prompts return instantly)
- [x] Frontend WebSocket integration (live upload progress, live agent step indicators)
- [x] Graceful fallback to synchronous mode when Celery is unavailable

### Phase 4: Observability
- [ ] Integrate Langfuse for LLM prompt tracing and cost monitoring
- [ ] Export Prometheus metrics (Qdrant/Neo4j query times, Agent durations)
- [ ] OpenTelemetry for distributed tracing across the backend

### Phase 5: Production
- [ ] Kubernetes (K8s) deployment manifests (Deployments, Services, Ingress)
- [ ] Horizontal Pod Autoscaling (HPA) for backend API and Celery workers
- [ ] Migration from local SentenceTransformers to a dedicated Embedding API (or Triton Inference Server)
- [ ] CI/CD pipelines (GitHub Actions) for automated testing and Docker publishing

## 📄 License

MIT
