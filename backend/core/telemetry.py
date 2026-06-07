"""
KnowledgeHive - OpenTelemetry Configuration

Sets up distributed tracing across FastAPI, sending spans to Prometheus/OTLP.
Phase 4: Observability
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

def setup_telemetry(app):
    """Initialize OpenTelemetry and instrument the FastAPI app."""
    resource = Resource(attributes={
        SERVICE_NAME: "knowledgehive-backend"
    })
    
    provider = TracerProvider(resource=resource)
    
    # In a real production setup, use OTLPSpanExporter to send traces to Jaeger/Tempo
    # We comment this out to prevent OpenTelemetry from flooding your console with JSON traces.
    # If you want to see console trace outputs, uncomment the lines below:
    # processor = BatchSpanProcessor(ConsoleSpanExporter())
    # provider.add_span_processor(processor)
    
    trace.set_tracer_provider(provider)
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    return provider
