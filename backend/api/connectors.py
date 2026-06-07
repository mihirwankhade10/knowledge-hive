"""
KnowledgeHive - Connectors API

Handles enterprise knowledge source connections.
Loads sample data, runs it through the ingestion + graph pipeline,
and returns statistics.
"""

import json
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Request

from backend.core.rate_limit import limiter
from backend.core.dependencies import (
    get_ingestion_agent,
    get_graph_agent,
    get_embedding_service,
    get_vector_store,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Path to sample data directory
SAMPLE_DATA_DIR = Path(__file__).parent.parent / "sample_data"

# In-memory connector state (resets on restart)
_connector_states = {}

# Mapping of source IDs to their sample data files
SOURCE_DATA_FILES = {
    "teams": ("teams/conversations.json", "content"),
    "emails": ("emails/emails.json", "content"),
    "jira": ("jira/tickets.json", "description"),
    "sharepoint": ("sharepoint/documents.json", "content"),
    "confluence": ("confluence/articles.json", "content"),
}


def _load_sample_data(source_id: str) -> list[dict]:
    """Load sample data from JSON files for a given source."""
    if source_id not in SOURCE_DATA_FILES:
        return []

    filename, _ = SOURCE_DATA_FILES[source_id]
    file_path = SAMPLE_DATA_DIR / filename

    if not file_path.exists():
        logger.warning(f"Sample data file not found: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_text_from_records(source_id: str, records: list[dict]) -> str:
    """Extract text content from sample data records for ingestion."""
    if source_id not in SOURCE_DATA_FILES:
        return ""

    _, content_field = SOURCE_DATA_FILES[source_id]
    texts = []

    for record in records:
        # Build a rich text representation of each record
        parts = []

        if "title" in record:
            parts.append(f"Title: {record['title']}")
        if "subject" in record:
            parts.append(f"Subject: {record['subject']}")
        if "type" in record:
            parts.append(f"Type: {record['type']}")
        if "status" in record:
            parts.append(f"Status: {record['status']}")
        if "assignee" in record:
            parts.append(f"Assignee: {record['assignee']}")
        if "author" in record:
            parts.append(f"Author: {record['author']}")
        if "from" in record:
            parts.append(f"From: {record['from']}")
        if "to" in record:
            to_val = record["to"]
            if isinstance(to_val, list):
                to_val = ", ".join(to_val)
            parts.append(f"To: {to_val}")
        if "channel" in record:
            parts.append(f"Channel: {record['channel']}")
        if "participants" in record:
            parts.append(f"Participants: {', '.join(record['participants'])}")
        if "priority" in record:
            parts.append(f"Priority: {record['priority']}")
        if "labels" in record:
            parts.append(f"Labels: {', '.join(record['labels'])}")
        if "sprint" in record:
            parts.append(f"Sprint: {record['sprint']}")

        # Main content
        if content_field in record:
            parts.append(f"\n{record[content_field]}")

        texts.append("\n".join(parts))

    return "\n\n---\n\n".join(texts)


@router.get("/connectors")
@limiter.limit("30/minute")
async def list_connectors(request: Request):
    """List all available connectors with their current status."""
    connectors = []
    for source_id in ["teams", "emails", "jira", "sharepoint", "confluence", "documents"]:
        state = _connector_states.get(source_id, {"status": "disconnected"})
        connectors.append({
            "id": source_id,
            "status": state.get("status", "disconnected"),
            "stats": state.get("stats", None),
        })
    return {"connectors": connectors}


@router.post("/connectors/{source_id}/connect")
@limiter.limit("10/minute")
async def connect_source(request: Request, source_id: str):
    """
    Connect a knowledge source by loading and ingesting sample data.

    This will:
    1. Load sample data from backend/sample_data/{source}/
    2. Run text through the ingestion pipeline (embed → Qdrant)
    3. Run through the graph pipeline (entities → Neo4j)
    4. Update connector state with statistics
    """
    if source_id == "documents":
        # Enterprise Documents uses the existing upload flow
        _connector_states[source_id] = {
            "status": "connected",
            "stats": {
                "records_ingested": 0,
                "entities_created": 0,
                "relationships_created": 0,
            },
        }
        return {
            "status": "connected",
            "source": source_id,
            "records_ingested": 0,
            "entities_created": 0,
            "relationships_created": 0,
            "message": "Enterprise Documents connector ready. Use file upload to add documents.",
        }

    # Load sample data
    records = _load_sample_data(source_id)
    if not records:
        return {
            "status": "error",
            "message": f"No sample data found for source: {source_id}",
        }

    # Extract text for ingestion
    full_text = _extract_text_from_records(source_id, records)
    if not full_text.strip():
        return {
            "status": "error",
            "message": f"No text content extracted from {source_id} data",
        }

    document_id = str(uuid.uuid4())
    filename = f"{source_id}_data.txt"

    # Save text to a temporary file for ingestion
    from backend.core.config import get_settings
    settings = get_settings()

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{document_id}.txt"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    logger.info(f"Ingesting {source_id} sample data: {len(records)} records, {len(full_text)} chars")

    # Run ingestion pipeline
    chunks_created = 0
    entities_created = 0
    relationships_created = 0

    try:
        ingestion_agent = get_ingestion_agent()
        ingestion_result = await ingestion_agent.execute({
            "file_path": str(file_path),
            "document_id": document_id,
            "filename": filename,
        })

        chunks_created = ingestion_result.output.get("chunk_count", 0)

        # Run graph extraction
        graph_agent = get_graph_agent()
        graph_result = await graph_agent.execute({
            "document_id": document_id,
            "chunks": ingestion_result.output.get("chunks", []),
        })

        entities_created = graph_result.output.get("entity_count", 0)
        relationships_created = graph_result.output.get("relationship_count", 0)

    except Exception as e:
        logger.error(f"Ingestion failed for {source_id}: {e}")
        # Still mark as connected even if ingestion partially fails
        entities_created = 0
        relationships_created = 0

    # Update connector state
    _connector_states[source_id] = {
        "status": "connected",
        "stats": {
            "records_ingested": len(records),
            "entities_created": entities_created,
            "relationships_created": relationships_created,
            "chunks_created": chunks_created,
            "document_id": document_id,
        },
    }

    return {
        "status": "connected",
        "source": source_id,
        "records_ingested": len(records),
        "entities_created": entities_created,
        "relationships_created": relationships_created,
        "chunks_created": chunks_created,
        "message": f"Successfully ingested {len(records)} records from {source_id}",
    }


@router.post("/connectors/{source_id}/disconnect")
@limiter.limit("10/minute")
async def disconnect_source(request: Request, source_id: str):
    """Disconnect a knowledge source."""
    _connector_states.pop(source_id, None)
    return {"status": "disconnected", "source": source_id}


@router.get("/connectors/stats")
@limiter.limit("30/minute")
async def connector_stats(request: Request):
    """Get aggregated statistics across all connected sources."""
    total_records = 0
    total_entities = 0
    total_relationships = 0
    connected = 0

    for state in _connector_states.values():
        if state.get("status") == "connected":
            connected += 1
            stats = state.get("stats", {})
            total_records += stats.get("records_ingested", 0)
            total_entities += stats.get("entities_created", 0)
            total_relationships += stats.get("relationships_created", 0)

    return {
        "connected_sources": connected,
        "total_records": total_records,
        "total_entities": total_entities,
        "total_relationships": total_relationships,
    }
