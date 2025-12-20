from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlmodel import Session, select
from typing import List, Optional
from database import get_session
from models import Article, Paragraph, DifficultyLevel
from ai_service import AIService
from auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/articles", response_model=List[Article])
def get_articles(
    difficulty: Optional[DifficultyLevel] = None,
    session: Session = Depends(get_session)
):
    query = select(Article)
    if difficulty:
        query = query.where(Article.difficulty == difficulty)
    query = query.order_by(Article.published_at.desc())
    return session.exec(query).all()

@router.get("/articles/{article_id}/page/{page_num}")
def get_article_page(
    article_id: str,
    page_num: int,
    session: Session = Depends(get_session)
):
    # Pagination: 20 paragraphs per page
    limit = 20
    offset = (page_num - 1) * limit

    # Try to fetch by ID first
    article = None
    try:
        aid = int(article_id)
        article = session.get(Article, aid)
    except ValueError:
        # It's a string, try to find by slug
        article = session.exec(select(Article).where(Article.source_url.contains(article_id))).first()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    paragraphs = session.exec(
        select(Paragraph)
        .where(Paragraph.article_id == article.id)
        .order_by(Paragraph.order_index)
        .offset(offset)
        .limit(limit)
    ).all()

    if not paragraphs:
        return {"article": article, "paragraphs": [], "has_next": False}

    # Check if we need to generate analysis
    # We check each paragraph for the 'analysis' field.
    
    analyzed_paragraphs = []
    
    for p in paragraphs:
        if not p.analysis:
            # Generate Full Analysis
            try:
                # Use article difficulty or default
                level = article.difficulty.value if article.difficulty else "Initial"
                analysis_json = AIService.analyze_vocabulary(p.content, level)
                
                if isinstance(analysis_json, list):
                     p.analysis = json.dumps(analysis_json, ensure_ascii=False)
                     session.add(p)
                     # We commit immediately or batch? Commit per paragraph is safer for now.
                     session.commit()
                     session.refresh(p)
                else:
                     logger.error(f"Invalid analysis format for paragraph {p.id}")
            except Exception as e:
                logger.error(f"Analysis failed for paragraph {p.id}: {e}")
                # Continue without crashing, render plain text on frontend is better than 500
        
        # Prepare response
        analyzed_paragraphs.append({
            "id": p.id,
            "content": p.content,
            "image_url": p.image_url,
            "order_index": p.order_index,
            "audio_path": p.audio_path,
            "analysis": json.loads(p.analysis) if p.analysis else []
        })

    total_paras_count = session.exec(select(Paragraph).where(Paragraph.article_id == article.id)).all()
    has_next = (offset + limit) < len(total_paras_count)

    return {
        "article": article,
        "page": page_num,
        "paragraphs": analyzed_paragraphs,
        "has_next": has_next
    }

    return {
        "article": article,
        "page": page_num,
        "paragraphs": analyzed_paragraphs,
        "has_next": has_next
    }

@router.post("/analyze/translation")
def analyze_translation(
    paragraph_text: str,
    session: Session = Depends(get_session)
):
    p = session.exec(select(Paragraph).where(Paragraph.content == paragraph_text)).first()
    
    if p and p.translation:
        return {"translation": json.loads(p.translation)}
    
    # Fallback to on-demand if missing (should not happen in eager mode)
    return {"translation": AIService.translate_paragraph(paragraph_text)}

@router.post("/analyze/syntax")
def analyze_syntax(
    paragraph_text: str,
    session: Session = Depends(get_session)
):
    p = session.exec(select(Paragraph).where(Paragraph.content == paragraph_text)).first()
    
    if p and p.syntax:
        return {"syntax": json.loads(p.syntax)}
        
    return {"syntax": AIService.analyze_syntax(paragraph_text)}

import json
import os

@router.get("/tts/paragraph")
def get_paragraph_tts(
    text: str,
    session: Session = Depends(get_session)
):
    p = session.exec(select(Paragraph).where(Paragraph.content == text)).first()
    
    if p and p.audio_path:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        abs_path = os.path.join(base_dir, p.audio_path)
        
        if os.path.exists(abs_path):
            with open(abs_path, "rb") as f:
                return Response(content=f.read(), media_type="audio/mpeg")
    
    # If audio_path is missing or file does not exist, return 404
    raise HTTPException(status_code=404, detail="Audio file not found. Pre-generation required.")

@router.get("/tts/{paragraph_id}")
def get_tts_by_id(
    paragraph_id: int,
    session: Session = Depends(get_session)
):
    p = session.get(Paragraph, paragraph_id)
    if not p:
        raise HTTPException(status_code=404, detail="Paragraph not found")
        
    if not p.audio_path:
         raise HTTPException(status_code=404, detail="Audio not generated for this paragraph")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    abs_path = os.path.join(base_dir, p.audio_path)
    
    if os.path.exists(abs_path):
        with open(abs_path, "rb") as f:
            return Response(content=f.read(), media_type="audio/mpeg")

    raise HTTPException(status_code=404, detail="Audio file missing on server")
