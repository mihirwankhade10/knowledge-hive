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
|-------|-----------|
| **Backend** | FastAPI, Pydantic, Uvicorn |
| **Frontend** | React, Vite, Chakra UI |
| **LLM** | OpenRouter (Azure OpenAI/OpenAI ready) |
| **Embeddings** | Sentence Transformers |
| **Vector DB** | Qdrant |
| **Graph DB** | Neo4j Community |
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

## 📈 Roadmap

- [x] **Phase 1**: Working MVP (upload, query, agent flow)
- [ ] **Phase 2**: Architecture hardening (logging, error handling)
- [ ] **Phase 3**: Scalability (Redis, Celery, background jobs)
- [ ] **Phase 4**: Observability (Langfuse, metrics, tracing)
- [ ] **Phase 5**: Production (K8s, horizontal scaling)

## 📄 License

MIT
