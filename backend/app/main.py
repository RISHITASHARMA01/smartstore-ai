import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .routers import auth as auth_router
from .routers import products as products_router
from .routers import suppliers as suppliers_router
from .routers import purchase_orders as po_router
from .routers.ai import router as ai_router
from .routers.forecast import router as forecast_router
from .routers.invoices import router as invoices_router
from .routers.dashboard import router as dashboard_router
from .routers.reports import router as reports_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Warn if secret key is still the default
_secret = os.getenv("SECRET_KEY", "")
if not _secret or _secret in ("your-secret-key-here", "changeme-in-production-generate-with-openssl-rand-hex-32"):
    logger.warning("⚠️  SECRET_KEY is not set or is using the default value. Set a strong secret in .env.")

# Rate limiter — keyed by client IP
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(title="SmartStore AI", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


app.include_router(auth_router.router)
app.include_router(products_router.router)
app.include_router(suppliers_router.router)
app.include_router(po_router.router)
app.include_router(ai_router, prefix="/ai", tags=["ai"])
app.include_router(forecast_router, tags=["forecast"])
app.include_router(invoices_router, prefix="/invoices", tags=["invoices"])
app.include_router(dashboard_router)
app.include_router(reports_router)


@app.get("/")
def root():
    return {"message": "SmartStore AI is running"}
