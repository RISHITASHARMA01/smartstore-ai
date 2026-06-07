from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth as auth_router
from .routers import products as products_router
from .routers import suppliers as suppliers_router
from .routers import purchase_orders as po_router
from .routers.ai import router as ai_router
from .routers.forecast import router as forecast_router

app = FastAPI(title="SmartStore AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(products_router.router)
app.include_router(suppliers_router.router)
app.include_router(po_router.router)
app.include_router(ai_router, prefix="/ai", tags=["ai"])
app.include_router(forecast_router, tags=["forecast"])


@app.get("/")
def root():
    return {"message": "SmartStore AI is running"}
