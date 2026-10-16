from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .routes import router

# create the web app
app = FastAPI(title=settings.app_name, version="1.0.0", description="Report and claim lost items on campus.")
# let the frontend call this api from any web address
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
# add all the item routes
app.include_router(router)

# prometheus metrics for each route
# it counts requests and records how long they take and which status codes they return
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


# home route that shows basic info about the service
@app.get("/")
def root():
    return {"service": settings.app_name, "version": "1.0.0", "environment": settings.environment, "docs": "/docs"}


@app.get("/health")
def health():
    """liveness check that says the app is running"""
    return {"status": "UP"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    """readiness check that says the database answers so the app can take traffic"""
    db.execute(text("SELECT 1"))
    return {"status": "READY"}
