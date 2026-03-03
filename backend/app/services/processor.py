from sqlmodel import Session, select
from ..database import engine
from ..models import Book, BookStatus, ProcessingStage, Chapter
from ..utils.file_handler import detect_encoding, convert_to_utf8
from ..utils.chapter_parser import ChapterExtractor
import os
import traceback

class BookProcessor:
    def __init__(self):
        # Define the processing chain
        self.handlers = [
            (ProcessingStage.ENCODING, self.handle_encoding),
            (ProcessingStage.CHAPTER_PARSING, self.handle_chapters),
        ]

    async def run(self, book_id: int):
        """Execute the processing chain for a given book."""
        with Session(engine) as session:
            book = session.get(Book, book_id)
            if not book:
                return
            
            # Start processing
            book.status = BookStatus.PROCESSING
            book.processing_stage = ProcessingStage.INIT
            session.add(book)
            session.commit()
            session.refresh(book)
            
            try:
                for stage, handler in self.handlers:
                    # Update current stage
                    book.processing_stage = stage
                    session.add(book)
                    session.commit()
                    
                    # Execute handler
                    await handler(book, session)
                    session.refresh(book)
                
                # All stages completed successfully
                book.status = BookStatus.SUCCESS
                book.processing_stage = ProcessingStage.COMPLETED
                session.add(book)
                session.commit()
                
            except Exception as e:
                # Handle failure
                error_msg = str(e)
                print(f"Error processing book {book_id}: {error_msg}")
                traceback.print_exc()
                
                book.status = BookStatus.FAILED
                book.failed_stage = book.processing_stage
                book.error_message = error_msg
                session.add(book)
                session.commit()

    async def handle_encoding(self, book: Book, session: Session):
        """Detect encoding and convert to UTF-8."""
        # Detect encoding
        encoding = await detect_encoding(book.path)
        
        # Convert to UTF-8 if needed
        try:
            # Note: convert_to_utf8 might change the file in place
            # We assume it returns the path (same as input if in place)
            await convert_to_utf8(book.path, encoding)
            
            # Update book info
            book.encoding = 'utf-8'
            book.file_size = os.path.getsize(book.path)
            session.add(book)
            session.commit()
        except Exception as e:
            raise Exception(f"Encoding conversion failed: {str(e)}")

    async def handle_chapters(self, book: Book, session: Session):
        """Parse chapters from the text file."""
        # Parse chapters
        try:
            chapter_list = await ChapterExtractor.parse(book.path, book.encoding or 'utf-8')
            
            # Save chapters to DB
            for index, (title, start_offset) in enumerate(chapter_list):
                chapter = Chapter(
                    book_id=book.id,
                    title=title,
                    start_offset=start_offset,
                    ordering=index
                )
                session.add(chapter)
            
            session.commit()
        except Exception as e:
            raise Exception(f"Chapter parsing failed: {str(e)}")
