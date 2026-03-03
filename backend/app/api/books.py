from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlmodel import Session, select
from typing import List
from ..database import get_session
from ..models import Book, Chapter, BookStatus, ProcessingStage
from ..utils.file_handler import save_upload_file, delete_file
from ..services.processor import BookProcessor
from pathlib import Path

router = APIRouter()
book_processor = BookProcessor()

@router.post("/upload", response_model=Book)
async def upload_book(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    if not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
    
    # Save file
    try:
        file_path, file_size = await save_upload_file(file)
    except Exception as e:
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
    
    # Trigger background processing
    background_tasks.add_task(book_processor.run, book.id)
    
    return book

@router.get("/", response_model=List[Book])
def get_books(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    # Sort by added_at desc
    books = session.exec(select(Book).order_by(Book.added_at.desc()).offset(skip).limit(limit)).all()
    return books

@router.get("/{book_id}", response_model=Book)
def get_book(book_id: int, session: Session = Depends(get_session)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.delete("/{book_id}")
def delete_book(book_id: int, session: Session = Depends(get_session)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Delete file
    delete_file(book.path)
    
    session.delete(book)
    session.commit()
    return {"ok": True}

@router.get("/{book_id}/chapters", response_model=List[Chapter])
def get_chapters(book_id: int, session: Session = Depends(get_session)):
    chapters = session.exec(
        select(Chapter).where(Chapter.book_id == book_id).order_by(Chapter.ordering)
    ).all()
    return chapters
