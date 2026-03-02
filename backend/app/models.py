from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

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
