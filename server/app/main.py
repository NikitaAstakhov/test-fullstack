import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from databases import Database

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:password@postgres:5432/postgres"
)
OTLP_ENDPOINT = os.getenv("OTLP_ENDPOINT", "http://jaeger:4318/v1/traces")


ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
ALLOWED_METHODS = ["GET", "POST", "OPTIONS"]
ALLOWED_HEADERS = ["*"]

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

database = Database(DATABASE_URL)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


resource = Resource(
    attributes={"service.name": "test-app", "service.version": "0.1.0"}
)
provider = TracerProvider(resource=resource)

otlp_exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT)
span_processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(span_processor)

trace.set_tracer_provider(provider)

app = FastAPI(title="TestFull FastAPI Service")

FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=ALLOWED_HOSTS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_HEADERS,
    allow_credentials=True
)

from app.views import router as submission_router
app.include_router(submission_router, prefix="")

from db.manager import run_alembic_migrations, run_seed_if_needed


@app.on_event("startup")
async def startup():
    await database.connect()
    logger.info("Database connected.")

    try:
        await run_alembic_migrations(alembic_ini_path="alembic.ini")
    except Exception as e:
        logger.error(f"Error running Alembic migrations: {e}")
        raise

    try:
        await run_seed_if_needed(
            database_url=DATABASE_URL,
            target_count=2_000_000,
            batch_size=1_000,
            threshold=100_000,
            max_workers=None
        )
    except Exception as e:
        logger.error(f"Error running async seeder: {e}")
        raise

    logger.info("Startup complete.")


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    logger.info("Database disconnected.")


@app.get("/health")
async def health():
    try:
        await database.fetch_one("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "detail": str(e)}
