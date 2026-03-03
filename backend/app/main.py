from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .database import create_db_and_tables
from .api import books, reader
from .core.logger import setup_logging, RequestLoggingMiddleware
from contextlib import asynccontextmanager
import logging

# Setup logging globally
setup_logging()
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("正在启动应用...")
    create_db_and_tables()
    logger.info("数据库初始化完成。")
    yield
    logger.info("应用正在关闭。")

app = FastAPI(lifespan=lifespan)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

# Include routers
app.include_router(books.router, prefix="/api/books", tags=["books"])
app.include_router(reader.router, prefix="/api/reader", tags=["reader"])

@app.get("/")
def read_root():
    logger.info("访问了根端点")
    return {"message": "Welcome to NeoReader API"}
