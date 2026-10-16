from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .routes import router

app = FastAPI(title=settings.app_name, version="1.0.0", description="Report and claim lost items on campus.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

# Prometheus metrics: request count, latency histogram and status codes per route
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


@app.get("/")
def root():
    return {"service": settings.app_name, "version": "1.0.0", "environment": settings.environment, "docs": "/docs"}


@app.get("/health")
def health():
    """Liveness: the process is up."""
    return {"status": "UP"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    """Readiness: the database answers, so we can serve traffic."""
    db.execute(text("SELECT 1"))
    return {"status": "READY"}
