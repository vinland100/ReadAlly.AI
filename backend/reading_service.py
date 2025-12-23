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
    if not p:
         raise HTTPException(status_code=404, detail="Paragraph not found")

    return _get_or_generate_audio(p, session)

@router.get("/tts/{paragraph_id}")
def get_tts_by_id(
    paragraph_id: int,
    session: Session = Depends(get_session)
):
    p = session.get(Paragraph, paragraph_id)
    if not p:
        raise HTTPException(status_code=404, detail="Paragraph not found")
        
    return _get_or_generate_audio(p, session)

def _get_or_generate_audio(p: Paragraph, session: Session):
    """
    Helper to check if audio exists, and if not, generate it immediately.
    """
    # 1. Resolve Static Directory
    static_dir = os.getenv("STATIC_DIR", "static")
    if not os.path.isabs(static_dir):
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), static_dir)
    
    # 2. Determine Expected File Path
    # Naming convention: static/audio/{article_id}/{article_id}_{order_index}.mp3
    # We match what the crawler does: 
    #   article_audio_dir = os.path.join(AUDIO_DIR, str(article.id))
    #   filename = f"{article.id}_{p.order_index}.mp3"
    
    audio_relative_dir = os.path.join("audio", str(p.article_id))
    filename = f"{p.article_id}_{p.order_index}.mp3"
    
    # Absolute path for file operations
    audio_dir_abs = os.path.join(static_dir, audio_relative_dir)
    audio_file_abs = os.path.join(audio_dir_abs, filename)
    
    # DB stored relative path example: static/audio/123/123_1.mp3
    # We want to be consistent with how we store it.
    # But wait, the crawler stores "static/audio/..." 
    # Let's standardize on storing "static/audio/{article_id}/{filename}" for db persistence compatibility
    
    # 3. Check if file exists
    if os.path.exists(audio_file_abs):
        with open(audio_file_abs, "rb") as f:
            return Response(content=f.read(), media_type="audio/mpeg")
            
    # 4. Not found? GENERATE IT.
    logger.info(f"Audio missing for paragraph {p.id}. Generating on-demand...")
    
    try:
        audio_bytes = AIService.generate_tts(p.content)
        if audio_bytes:
            # Ensure dir exists
            os.makedirs(audio_dir_abs, exist_ok=True)
            
            # Save file
            with open(audio_file_abs, "wb") as f:
                f.write(audio_bytes)
            
            # Update DB (if path wasn't set or was wrong)
            # The DB path conventionally includes "static/" prefix in this codebase unfortunately
            rel_path_for_db = os.path.join("static", "audio", str(p.article_id), filename)
            p.audio_path = rel_path_for_db
            session.add(p)
            session.commit()
            session.refresh(p)
            
            return Response(content=audio_bytes, media_type="audio/mpeg")
        else:
            raise HTTPException(status_code=500, detail="Failed to generate audio from AI service")
            
    except Exception as e:
        logger.error(f"On-demand TTS generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS Generation failed: {str(e)}")
