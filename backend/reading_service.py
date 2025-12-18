from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlmodel import Session, select
from typing import List, Optional
from database import get_session
from models import Article, Paragraph, VocabularyAnnotation, DifficultyLevel
from ai_service import AIService
from auth import get_current_user

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

    # Check if we need to generate vocabulary annotations for this batch
    # Heuristic: Check the first paragraph. If it has no annotations, assume the batch needs analysis.
    # A robust implementation would check all or flag the page as analyzed.
    # For now, we check if any annotation exists for these paragraphs.

    # We combine text for analysis to save tokens/calls
    # But we need to map back to paragraphs.
    # The prompt asks for "exact word/phrase".

    # Optimization: Check if *any* annotations exist for these paragraph IDs.
    para_ids = [p.id for p in paragraphs]
    existing_annotations = session.exec(select(VocabularyAnnotation).where(VocabularyAnnotation.paragraph_id.in_(para_ids))).all()

    if not existing_annotations:
        # Generate Analysis
        full_page_text = "\n\n".join([p.content for p in paragraphs])
        analysis_json = AIService.analyze_vocabulary(full_page_text, article.difficulty.value)

        # Map annotations back to paragraphs
        # This is tricky because the AI returns a list of words. We need to find which paragraph contains the word.
        # We will iterate through paragraphs and assign.

        new_annotations = []
        for item in analysis_json:
            word = item.get("word")
            for p in paragraphs:
                if word and word in p.content:
                    # Create annotation
                    annotation = VocabularyAnnotation(
                        paragraph_id=p.id,
                        word=word,
                        type=item.get("type", "word"),
                        definition=item.get("definition", ""),
                        context_example=item.get("context_example", "")
                    )
                    session.add(annotation)
                    new_annotations.append(annotation)
                    # Break to avoid adding same word to multiple paragraphs if it appears multiple times?
                    # Maybe better to add to the first occurrence or all.
                    # For simplicity, first occurrence in this page.
                    break
        session.commit()
        # Refetch with annotations
        # Or just append locally if we eagerly loaded (we didn't).

        # Re-querying to get relationships populated if needed, or just relying on lazy load

    # Construct response with annotations embedded
    result_paragraphs = []
    for p in paragraphs:
        p_annotations = session.exec(select(VocabularyAnnotation).where(VocabularyAnnotation.paragraph_id == p.id)).all()
        result_paragraphs.append({
            "id": p.id,
            "content": p.content,
            "image_url": p.image_url,
            "order_index": p.order_index,
            "audio_path": p.audio_path,
            "annotations": p_annotations
        })

    total_paras_count = session.exec(select(Paragraph).where(Paragraph.article_id == article.id)).all()
    has_next = (offset + limit) < len(total_paras_count)

    return {
        "article": article,
        "page": page_num,
        "paragraphs": result_paragraphs,
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
