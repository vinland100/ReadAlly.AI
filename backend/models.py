from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum

class DifficultyLevel(str, Enum):
    HIGH_SCHOOL = "High School"
    CET_4 = "CET-4"
    CET_6 = "CET-6"
    IELTS = "IELTS"
    TEM_8 = "TEM-8"
    UNKNOWN = "Unknown"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    nickname: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Article(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    source_url: Optional[str] = None
    cover_image: Optional[str] = None
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.UNKNOWN)
    word_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    paragraphs: List["Paragraph"] = Relationship(back_populates="article")

class Paragraph(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="article.id")
    order_index: int
    content: str

    article: Article = Relationship(back_populates="paragraphs")
    annotations: List["VocabularyAnnotation"] = Relationship(back_populates="paragraph")

class VocabularyAnnotation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paragraph_id: int = Field(foreign_key="paragraph.id")
    word: str
    type: str # idiom, phrase, word, slang
    definition: str
    context_example: Optional[str] = None

    paragraph: Paragraph = Relationship(back_populates="annotations")
