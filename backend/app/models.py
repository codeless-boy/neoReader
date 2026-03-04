from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum

class BookStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"

class ProcessingStage(str, Enum):
    INIT = "init"
    ENCODING = "encoding"
    CHAPTER_PARSING = "parsing"
    COMPLETED = "completed"

class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    author: Optional[str] = None
    path: str
    file_size: int
    encoding: Optional[str] = None
    added_at: datetime = Field(default_factory=datetime.now)
    cover_path: Optional[str] = None
    description: Optional[str] = None

    # Status fields
    status: BookStatus = Field(default=BookStatus.PENDING)
    processing_stage: ProcessingStage = Field(default=ProcessingStage.INIT)
    error_message: Optional[str] = None
    failed_stage: Optional[ProcessingStage] = None

    # Relationship
    chapters: List["Chapter"] = Relationship(back_populates="book", sa_relationship_kwargs={"cascade": "all, delete"})

class Chapter(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    book_id: int = Field(foreign_key="book.id")
    title: str
    start_offset: int
    end_offset: Optional[int] = None
    ordering: int

    # Relationship
    book: Optional[Book] = Relationship(back_populates="chapters")

class SystemSetting(SQLModel, table=True):
    key: str = Field(primary_key=True)
    category: str
    group: str
    label: str
    value: str
    field_type: str  # text, number, boolean, select, readonly
    options: Optional[str] = None  # JSON string for select options
    description: Optional[str] = None
    sort_order: int = 0
