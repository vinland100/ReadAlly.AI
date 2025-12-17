from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlmodel import Session, select
from typing import Optional
import requests
from bs4 import BeautifulSoup
import pypdf
import io
from database import get_session
from models import Article, Paragraph, DifficultyLevel
from ai_service import AIService

router = APIRouter()

def clean_text(text):
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return '\n'.join(chunk for chunk in chunks if chunk)

def split_into_paragraphs(text):
    # Simple split by double newline or filter empty lines
    paras = [p.strip() for p in text.split('\n') if p.strip()]
    return paras

@router.post("/ingest/url")
def ingest_url(url: str, session: Session = Depends(get_session)):
    try:
        # Simple scraping
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.content, 'html.parser')

        # Try to find main content
        # Heuristic: look for <article>, or the div with most p tags
        article_body = soup.find('article')
        if not article_body:
            # Fallback: look for generic content
            article_body = soup.find('main') or soup.body

        paragraphs = [p.get_text() for p in article_body.find_all('p')]
        full_text = "\n".join(paragraphs)

        if not full_text:
            raise HTTPException(status_code=400, detail="Could not extract text from URL")

        title = soup.title.string if soup.title else url

        # Process
        return process_ingestion(title, full_text, url, session)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@router.post("/ingest/pdf")
async def ingest_pdf(file: UploadFile = File(...), session: Session = Depends(get_session)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    content = await file.read()
    pdf_file = io.BytesIO(content)

    try:
        reader = pypdf.PdfReader(pdf_file)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"

        return process_ingestion(file.filename, full_text, None, session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")

def process_ingestion(title: str, full_text: str, source_url: Optional[str], session: Session):
    # 1. Classify Difficulty
    difficulty_str = AIService.classify_difficulty(full_text)
    try:
        difficulty = DifficultyLevel(difficulty_str)
    except:
        difficulty = DifficultyLevel.UNKNOWN

    # 2. Create Article
    article = Article(
        title=title,
        source_url=source_url,
        difficulty=difficulty,
        word_count=len(full_text.split())
    )
    session.add(article)
    session.commit()
    session.refresh(article)

    # 3. Create Paragraphs
    raw_paras = split_into_paragraphs(full_text)

    # Filter out very short paragraphs (nav links etc)
    valid_paras = [p for p in raw_paras if len(p.split()) > 5]

    for idx, content in enumerate(valid_paras):
        para = Paragraph(article_id=article.id, order_index=idx, content=content)
        session.add(para)

    session.commit()

    return {"id": article.id, "title": article.title, "difficulty": difficulty, "paragraphs_count": len(valid_paras)}
