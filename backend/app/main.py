"""QualiScope API entrypoint.

Middleware order (outermost first):
    CORS -> RequestId -> Auth -> RateLimit(quota) -> Audit -> routes -> error handlers
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.database import init_db
from app.config.settings import settings
from app.middlewares.audit_logger import AuditMiddleware
from app.middlewares.auth import AuthMiddleware
from app.middlewares.error_handler import RequestIdMiddleware, install_error_handlers
from app.middlewares.quota import RateLimitMiddleware
from app.routes import audit, auth, dataset, health, issue, profile, rule, run
from app.utils import storage
from app.utils.logger import log_event


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    storage.ensure_dirs()
    if settings.SEED_DEMO:
        try:
            from scripts.seed_demo import run_seed

            result = run_seed()
            log_event(
                "SEED_DEMO_FINISHED",
                datasets=result.get("datasets"),
                rules=result.get("rules"),
                runs=result.get("runs"),
                issues=result.get("issues"),
            )
        except Exception as exc:  # seed must never block startup
            log_event("SEED_DEMO_FAILED", error=f"{type(exc).__name__}: {exc}")
    yield


app = FastAPI(
    title="QualiScope API",
    description="数据质量剖析与规则治理平台 — 明川银行数据治理组",
    version="1.0.0",
    lifespan=lifespan,
)

install_error_handlers(app)

# added first => innermost
app.add_middleware(AuditMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(RequestIdMiddleware)
# added last => outermost (preflight is answered before auth)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(dataset.router)
app.include_router(profile.router)
app.include_router(rule.router)
app.include_router(run.router)
app.include_router(issue.router)
app.include_router(audit.router)


@app.get("/")
def index() -> dict:
    return {
        "service": "qualiscope-backend",
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/auth/login",
            "/datasets",
            "/datasets/{id}/profile",
            "/rules",
            "/runs",
            "/issues",
            "/audit/recent",
        ],
    }
