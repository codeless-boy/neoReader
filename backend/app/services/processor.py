from sqlmodel import Session, select
from ..database import engine
from ..models import Book, BookStatus, ProcessingStage, Chapter
from ..utils.file_handler import detect_encoding, convert_to_utf8
from ..utils.chapter_parser import ChapterExtractor
import os
import logging

logger = logging.getLogger(__name__)

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
                logger.warning(f"未找到要处理的书籍: {book_id}")
                return
            
            # Start processing
            logger.info(f"开始处理书籍: {book_id}")
            book.status = BookStatus.PROCESSING
            book.processing_stage = ProcessingStage.INIT
            session.add(book)
            session.commit()
            session.refresh(book)
            
            try:
                for stage, handler in self.handlers:
                    # Update current stage
                    logger.info(f"开始书籍 {book_id} 的 {stage} 阶段")
                    book.processing_stage = stage
                    session.add(book)
                    session.commit()
                    
                    # Execute handler
                    await handler(book, session)
                    session.refresh(book)
                    logger.info(f"完成书籍 {book_id} 的 {stage} 阶段")
                
                # All stages completed successfully
                book.status = BookStatus.SUCCESS
                book.processing_stage = ProcessingStage.COMPLETED
                session.add(book)
                session.commit()
                logger.info(f"书籍处理成功完成: {book_id}")
                
            except Exception as e:
                # Handle failure
                error_msg = str(e)
                logger.error(f"处理书籍 {book_id} 出错: {error_msg}", exc_info=True)
                
                book.status = BookStatus.FAILED
                book.failed_stage = book.processing_stage
                book.error_message = error_msg
                session.add(book)
                session.commit()

    async def handle_encoding(self, book: Book, session: Session):
        """Detect encoding and convert to UTF-8."""
        logger.debug(f"处理书籍 {book.id} 的编码")
        # Detect encoding
        encoding = await detect_encoding(book.path)
        logger.info(f"检测到书籍 {book.id} 编码为 {encoding}")
        
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
            logger.info(f"已将书籍 {book.id} 转换为 UTF-8")
        except Exception as e:
            logger.error(f"书籍 {book.id} 编码转换失败: {str(e)}", exc_info=True)
            raise Exception(f"Encoding conversion failed: {str(e)}")

    async def handle_chapters(self, book: Book, session: Session):
        """Parse chapters from the text file."""
        logger.debug(f"处理书籍 {book.id} 的章节解析")
        # Parse chapters
        try:
            chapter_list = await ChapterExtractor.parse(book.path, book.encoding or 'utf-8')
            logger.info(f"解析出书籍 {book.id} 的 {len(chapter_list)} 个章节")
            
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
            logger.info(f"书籍 {book.id} 章节已保存到数据库")
        except Exception as e:
            logger.error(f"书籍 {book.id} 章节解析失败: {str(e)}", exc_info=True)
            raise Exception(f"Chapter parsing failed: {str(e)}")
