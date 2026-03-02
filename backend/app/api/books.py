from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from typing import List
from ..database import get_session
from ..models import Book
from ..utils.file_handler import save_upload_file, detect_encoding, delete_file
from pathlib import Path

router = APIRouter()

@router.post("/upload", response_model=Book)
async def upload_book(
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
    
    # Detect encoding
    encoding = await detect_encoding(file_path)
    
    # Create Book entry
    book = Book(
        title=Path(file.filename).stem,
        path=file_path,
        file_size=file_size,
        encoding=encoding,
        cover_path="" # No cover for TXT
    )
    
    session.add(book)
    session.commit()
    session.refresh(book)
    
    return book

@router.get("/", response_model=List[Book])
def get_books(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    books = session.exec(select(Book).offset(skip).limit(limit)).all()
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
