from fastapi import FastAPI
import sys
sys.path.append("E:\\repo\\pip_packages")
from fastapi.staticfiles import StaticFiles
from .database import create_db_and_tables, engine
from sqlmodel import Session
from .api import books, reader, settings, llm
from .api.settings import init_settings
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
    with Session(engine) as session:
        init_settings(session)
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
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(llm.router, prefix="/api/llm", tags=["llm"])

@app.get("/")
def read_root():
    logger.info("访问了根端点")
    return {"message": "Welcome to NeoReader API"}
