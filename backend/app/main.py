
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
import app.models

from app.routers.master_data import router as master_data_router
from app.routers.scheduling import router as scheduling_router
from app.routers.operations import router as operations_router


app = FastAPI(
    title="YottaFlex Manufacturing API",
    description="Manufacturing production scheduling platform",
    version="1.0.0",
)

# Allow the React development server to communicate with FastAPI.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_database_tables():
    Base.metadata.create_all(bind=engine)


app.include_router(master_data_router)
app.include_router(scheduling_router)
app.include_router(operations_router)


@app.get("/")
def home():
    return {
        "message": "YottaFlex Manufacturing API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
