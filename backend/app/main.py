from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import products as products_router

app = FastAPI(title="SmartStore AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router.router)


@app.get("/")
def root():
    return {"message": "SmartStore AI is running"}
