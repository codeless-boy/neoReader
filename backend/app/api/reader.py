from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from ..database import get_session
from ..models import Book
import aiofiles
import os

router = APIRouter()

@router.get("/{book_id}/content")
async def get_book_content(
    book_id: int,
    start: int = Query(0, ge=0),
    limit: int = Query(10000, le=100000), # Limit max 100KB per request
    session: Session = Depends(get_session)
):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if not os.path.exists(book.path):
        raise HTTPException(status_code=404, detail="File not found on server")
        
    file_size = os.path.getsize(book.path)
    if start >= file_size:
        return {"content": "", "has_more": False, "total_size": file_size}
        
    encoding = book.encoding or 'utf-8'
    
    try:
        async with aiofiles.open(book.path, 'rb') as f:
            await f.seek(start)
            chunk = await f.read(limit)
            
        # Decode content
        # If chunk ends in middle of a multibyte character, it might fail.
        # However, for simple implementation, we can use 'replace' or try to align.
        # A better approach is to read slightly more and decode, or just handle errors.
        # For 'utf-8', 'ignore' or 'replace' is safe for display.
        content = chunk.decode(encoding, errors='replace')
        
        has_more = (start + len(chunk)) < file_size
        
        return {
            "content": content,
            "has_more": has_more,
            "total_size": file_size,
            "encoding": encoding
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
