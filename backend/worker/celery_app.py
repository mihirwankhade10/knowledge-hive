"""
KnowledgeHive - Celery Application

Configures the Celery app with Redis as broker and result backend.
Tasks are defined in backend.worker.tasks.

Phase 3: Scalability
"""

import os
import sys

# Ensure the project root is on the Python path so Celery workers
# can import backend.* modules when started from the project root.
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from celery import Celery
from backend.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "knowledgehive",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["backend.worker.tasks"],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Task tracking
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # Result expiry (keep results for 1 hour)
    result_expires=3600,

    # Don't hijack the root logger (we have our own logging)
    worker_hijack_root_logger=False,

    # Timezone
    timezone="UTC",
    enable_utc=True,
)
