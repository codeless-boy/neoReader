from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

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
