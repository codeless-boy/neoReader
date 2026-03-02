from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .database import create_db_and_tables
from .api import books, reader
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Include routers
app.include_router(books.router, prefix="/api/books", tags=["books"])
app.include_router(reader.router, prefix="/api/reader", tags=["reader"])

@app.get("/")
def read_root():
    return {"message": "Welcome to NeoReader API"}
