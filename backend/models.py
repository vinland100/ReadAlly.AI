from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum

class DifficultyLevel(str, Enum):
    INITIAL = "Initial" # 初阶 (高考)
    INTERMEDIATE = "Intermediate" # 中阶 (四级)
    UPPER_INTERMEDIATE = "Upper Intermediate" # 中高阶 (六级/考研)
    ADVANCED = "Advanced" # 高阶 (雅思/托福/专四)
    UNKNOWN = "Unknown"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    nickname: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Stats
    words_read_today: int = Field(default=0)
    current_streak: int = Field(default=0)
    last_read_date: Optional[datetime] = None
    avatar_seed: str = Field(default="Cookie")

class Article(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    source_url: Optional[str] = None
    cover_image: Optional[str] = None
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.UNKNOWN)
    word_count: int = 0
    published_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Eager Processing Fields
    full_audio_path: Optional[str] = None # Relative path to full audio

    paragraphs: List["Paragraph"] = Relationship(back_populates="article", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class Paragraph(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="article.id")
    order_index: int
    content: str
    image_url: Optional[str] = None

    # Eager Processing Fields
    translation: Optional[str] = None  # JSON string
    syntax: Optional[str] = None       # JSON string
    audio_path: Optional[str] = None   # Relative path to static audio

    article: Article = Relationship(back_populates="paragraphs")
    annotations: List["VocabularyAnnotation"] = Relationship(back_populates="paragraph", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class VocabularyAnnotation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    paragraph_id: int = Field(foreign_key="paragraph.id")
    word: str
    type: str # idiom, phrase, word, slang
    definition: str
    context_example: Optional[str] = None

    paragraph: Paragraph = Relationship(back_populates="annotations")
