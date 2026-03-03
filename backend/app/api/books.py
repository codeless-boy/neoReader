from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlmodel import Session, select
from typing import List
import logging
from ..database import get_session
from ..models import Book, Chapter, BookStatus, ProcessingStage
from ..utils.file_handler import save_upload_file, delete_file
from ..services.processor import BookProcessor
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()
book_processor = BookProcessor()

@router.post("/upload", response_model=Book)
async def upload_book(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    logger.info(f"收到上传请求: {file.filename}")
    
    if not file.filename.endswith(".txt"):
        logger.warning(f"上传了无效文件类型: {file.filename}")
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
    
    # Save file
    try:
        file_path, file_size = await save_upload_file(file)
        logger.info(f"文件保存成功: {file_path} ({file_size} 字节)")
    except Exception as e:
        logger.error(f"保存文件 {file.filename} 失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create Book entry (Status: PENDING)
    book = Book(
        title=Path(file.filename).stem,
        path=file_path,
        file_size=file_size,
        cover_path="",
        encoding="",
        status=BookStatus.PENDING,
        processing_stage=ProcessingStage.INIT
    )
    
    session.add(book)
    session.commit()
    session.refresh(book)
    logger.info(f"创建书籍条目: ID={book.id}, 标题='{book.title}'")
    
    # Trigger background processing
    logger.info(f"触发书籍 {book.id} 的后台处理")
    background_tasks.add_task(book_processor.run, book.id)
    
    return book

@router.get("/", response_model=List[Book])
def get_books(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    logger.debug(f"获取书籍列表: skip={skip}, limit={limit}")
    # Sort by added_at desc
    books = session.exec(select(Book).order_by(Book.added_at.desc()).offset(skip).limit(limit)).all()
    logger.debug(f"检索到 {len(books)} 本书")
    return books

@router.get("/{book_id}", response_model=Book)
def get_book(book_id: int, session: Session = Depends(get_session)):
    logger.debug(f"获取书籍详情: {book_id}")
    book = session.get(Book, book_id)
    if not book:
        logger.warning(f"未找到书籍: {book_id}")
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.delete("/{book_id}")
def delete_book(book_id: int, session: Session = Depends(get_session)):
    logger.info(f"请求删除书籍: {book_id}")
    book = session.get(Book, book_id)
    if not book:
        logger.warning(f"未找到要删除的书籍: {book_id}")
        raise HTTPException(status_code=404, detail="Book not found")
    
    session.delete(book)
    session.commit()
    logger.info(f"从数据库删除书籍: {book_id}")

    # Delete file
    try:
        delete_file(book.path)
        logger.info(f"已删除书籍 {book_id} 的文件: {book.path}")
    except Exception as e:
        logger.error(f"删除文件 {book.path} 失败: {str(e)}", exc_info=True)
        # File deletion failure should not rollback DB transaction as DB is already committed
        # We just log the error
    
    return {"ok": True}

@router.get("/{book_id}/chapters", response_model=List[Chapter])
def get_chapters(book_id: int, session: Session = Depends(get_session)):
    logger.debug(f"获取书籍章节: {book_id}")
    chapters = session.exec(
        select(Chapter).where(Chapter.book_id == book_id).order_by(Chapter.ordering)
    ).all()
    logger.debug(f"检索到书籍 {book_id} 的 {len(chapters)} 个章节")
    return chapters
