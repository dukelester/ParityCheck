"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import reports, auth, environments, drifts, workspaces, ignore_rules, alerts
from app.core.config import settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI( 
    title="ParityCheck API",
    description="Environment drift detection SaaS",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["workspaces"])
app.include_router(environments.router, prefix="/api/v1/environments", tags=["environments"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(drifts.router, prefix="/api/v1/drifts", tags=["drifts"])
app.include_router(ignore_rules.router, prefix="/api/v1/ignore-rules", tags=["ignore-rules"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
