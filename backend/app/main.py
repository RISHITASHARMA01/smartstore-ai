import os
import uuid
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Query

# Load .env from project root once at startup so os.getenv() works everywhere
load_dotenv(Path(__file__).parents[2] / ".env")
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from .rate_limit import limiter
from .websocket_manager import manager
from .auth.utils import decode_token

from .routers import auth as auth_router
from .routers import products as products_router
from .routers import suppliers as suppliers_router
from .routers import purchase_orders as po_router
from .routers.admin import router as admin_router
from .routers.ai import router as ai_router
from .routers.forecast import router as forecast_router
from .routers.invoices import router as invoices_router
from .routers.dashboard import router as dashboard_router
from .routers.reports import router as reports_router
from .routers.recommendations import router as recommendations_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Startup validation ────────────────────────────────────────────────────────
_WEAK_SECRETS = {"", "changeme", "secret", "your-secret-key-here",
                 "changeme-in-production-generate-with-openssl-rand-hex-32"}

_secret = os.getenv("SECRET_KEY", "")
if not _secret or _secret in _WEAK_SECRETS:
    logger.warning("⚠️  SECRET_KEY is not set or is using the default value. "
                   "Generate one with: openssl rand -hex 32")

if not os.getenv("DATABASE_URL"):
    logger.warning("⚠️  DATABASE_URL is not set. Backend will fail to connect.")

if not os.getenv("GEMINI_API_KEY"):
    logger.warning("⚠️  GEMINI_API_KEY is not set. AI features will not work.")

# ── Rate limiter ──────────────────────────────────────────────────────────────

app = FastAPI(title="SmartStore AI", version="1.0.0", redirect_slashes=False)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:3000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


# ── Security headers + request ID + access log ───────────────────────────────
@app.middleware("http")
async def security_and_logging(request: Request, call_next):
    # Assign a unique ID to every request for log correlation
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start = time.perf_counter()

    response = await call_next(request)

    duration_ms = round((time.perf_counter() - start) * 1000)

    # Security headers
    response.headers["X-Content-Type-Options"]  = "nosniff"
    response.headers["X-Frame-Options"]         = "DENY"
    response.headers["X-XSS-Protection"]        = "1; mode=block"
    response.headers["Referrer-Policy"]         = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]      = "camera=(), microphone=(), geolocation=()"
    response.headers["X-Request-ID"]            = request_id
    # HSTS — only meaningful over HTTPS; safe to send always
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    # CSP — blocks inline scripts/styles injected by XSS
    api_origin = os.getenv("API_URL", "")
    request_origin = f"{request.url.scheme}://{request.url.hostname}:{request.url.port}"
    connect_src = " ".join(filter(None, {api_origin, request_origin}))
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data: blob: https://fastapi.tiangolo.com; "
        f"connect-src 'self' {connect_src} https://generativelanguage.googleapis.com; "
        "font-src 'self' data:; "
        "frame-ancestors 'none';"
    )

    # Access log: method path status duration user-ip
    logger.info(
        "%s %s %s %dms [%s] req=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request.client.host if request.client else "-",
        request_id,
    )

    return response


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(products_router.router)
app.include_router(suppliers_router.router)
app.include_router(po_router.router)
app.include_router(admin_router)
app.include_router(ai_router, prefix="/ai", tags=["ai"])
app.include_router(forecast_router, tags=["forecast"])
app.include_router(invoices_router, prefix="/invoices", tags=["invoices"])
app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(recommendations_router)


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=4001)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/")
def root():
    return {"message": "SmartStore AI is running"}


@app.get("/health")
def health():
    return {"status": "ok"}
