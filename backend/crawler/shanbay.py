
import requests
import re
import json
import time
import os
import shutil
import logging
from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from database import engine
from models import Article, Paragraph, DifficultyLevel, VocabularyAnnotation
from ai_service import AIService

# China Standard Time
CN_TZ = timezone(timedelta(hours=8))
AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "audio")

# Mapping from Shanbay 'grade_info' or 'sbay_level' to our DifficultyLevel
GRADE_MAP = {
    "高考": DifficultyLevel.INITIAL,
    "初阶": DifficultyLevel.INITIAL,
    "四级": DifficultyLevel.INTERMEDIATE,
    "中阶": DifficultyLevel.INTERMEDIATE,
    "六级": DifficultyLevel.UPPER_INTERMEDIATE,
    "考研": DifficultyLevel.UPPER_INTERMEDIATE,
    "中高阶": DifficultyLevel.UPPER_INTERMEDIATE,
    "雅思": DifficultyLevel.ADVANCED,
    "托福": DifficultyLevel.ADVANCED,
    "专四": DifficultyLevel.ADVANCED,
    "高阶": DifficultyLevel.ADVANCED
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_xml_content(request_xml_text):
    if not request_xml_text: return []
    xml_text = request_xml_text
    parseds = []
    
    para_pattern = re.compile(r'<para.*?>(.*?)</para>', re.DOTALL)
    para_matches = para_pattern.findall(xml_text)
    
    if not para_matches:
        cdata_pattern = re.compile(r'<!\[CDATA\[(.*?)\]\]>')
        all_text = " ".join(cdata_pattern.findall(xml_text))
        if all_text.strip():
            return [{'type': 'text', 'content': all_text.strip()}]
        return []

    for para_content in para_matches:
        img_pattern = re.compile(r'<img><url>(.*?)</url>', re.DOTALL)
        imgs = img_pattern.findall(para_content)
        for img_url in imgs:
            if img_url.strip():
                parseds.append({'type': 'image', 'content': img_url.strip()})
        
        cdata_pattern = re.compile(r'<!\[CDATA\[(.*?)\]\]>')
        sentences = cdata_pattern.findall(para_content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if sentences:
            para_text = " ".join(sentences).strip()
            if para_text:
                parseds.append({'type': 'text', 'content': para_text})
    return parseds

def import_json_string(data):
    if isinstance(data, str): return data
    return json.dumps(data, ensure_ascii=False)

def process_article_eagerly(session: Session, article: Article):
    logger.info(f"Processing article eager pipeline: {article.title}")
    
    article_audio_dir = os.path.join(AUDIO_DIR, str(article.id))
    os.makedirs(article_audio_dir, exist_ok=True)
    
    paragraphs = session.exec(select(Paragraph).where(Paragraph.article_id == article.id).order_by(Paragraph.order_index)).all()
    
    for p in paragraphs:
        if not p.content.strip(): continue

        # 1. Translation
        if not p.translation:
            try:
                trans_res = AIService.translate_paragraph(p.content)
                p.translation = import_json_string(trans_res)
                session.add(p)
                session.commit()
            except Exception as e:
                logger.error(f"Translation failed for {p.id}: {e}")
            time.sleep(0.5)

        # 2. Syntax
        if not p.syntax:
            try:
                syntax_res = AIService.analyze_syntax(p.content)
                p.syntax = import_json_string(syntax_res)
                session.add(p)
                session.commit()
            except Exception as e:
                logger.error(f"Syntax failed for {p.id}: {e}")
            time.sleep(0.5)

        # 3. Audio
        # Naming convention: static/audio/{article_id}/{article_id}_{order_index}.mp3
        filename = f"{article.id}_{p.order_index}.mp3"
        p_audio_path = os.path.join(article_audio_dir, filename)
        rel_path = f"static/audio/{article.id}/{filename}"
        
        if not p.audio_path or not os.path.exists(p_audio_path):
             try:
                 audio_bytes = AIService.generate_tts(p.content)
                 if audio_bytes:
                     with open(p_audio_path, "wb") as f:
                         f.write(audio_bytes)
                     p.audio_path = rel_path
                     session.add(p)
                     session.commit()
                 else:
                     logger.error(f"Failed to generate TTS for paragraph {p.id}")
             except Exception as e:
                 logger.error(f"TTS failed for {p.id}: {e}")
             time.sleep(0.5)

    # 4. Vocabulary (Batched by 20 to match pagination)
    # We re-fetch all paragraphs to be safe
    all_paras = session.exec(select(Paragraph).where(Paragraph.article_id == article.id).order_by(Paragraph.order_index)).all()
    
    # Check if any annotations exist to avoid re-running (simple check)
    # If first paragraph has no annotations, we might assume we need to run or run partial.
    # But for eager processing, let's just loop and check batches.
    
    batch_size = 20
    for i in range(0, len(all_paras), batch_size):
        batch = all_paras[i:i+batch_size]
        batch_ids = [p.id for p in batch]
        
        # Check if this batch has annotations
        existing = session.exec(select(VocabularyAnnotation).where(VocabularyAnnotation.paragraph_id.in_(batch_ids))).first()
        if existing:
            continue

        logger.info(f"  - Analyzing vocabulary for batch {i//batch_size + 1}")
        batch_text = "\n\n".join([p.content for p in batch if p.content])
        if not batch_text.strip(): continue
        
        try:
            analysis_json = AIService.analyze_vocabulary(batch_text, article.difficulty.value)
            
            for item in analysis_json:
                word = item.get("word")
                if not word: continue
                # Find which paragraph contains this word
                for p in batch:
                    if p.content and word.lower() in p.content.lower():
                        annotation = VocabularyAnnotation(
                            paragraph_id=p.id,
                            word=word,
                            type=item.get("type", "word"),
                            definition=item.get("definition", ""),
                            context_example=item.get("context_example", "")
                        )
                        session.add(annotation)
                        break # Attach to first occurrence in batch
            session.commit()
        except Exception as e:
            logger.error(f"Vocab analysis failed for batch {i}: {e}")
        time.sleep(1)

def fetch_shanbay_articles():
    now_cn = datetime.now(CN_TZ)
    print(f"[{now_cn}] Starting Shanbay crawl...")
    list_url = "https://apiv3.shanbay.com/news/retrieve/articles"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Retention Policy: Last 3 days ONLY (Today, Yesterday, Day Before)
    today_cn = now_cn.date()
    cutoff_date = today_cn - timedelta(days=2) 
    print(f"Retention Policy: Keeping articles from {cutoff_date} onwards.")

    # 1. Cleanup Old Data First (Delete anything older than cutoff)
    try:
        with Session(engine) as session:
            # Cutoff datetime at start of day
            cutoff_dt = datetime.combine(cutoff_date, datetime.min.time()).replace(tzinfo=CN_TZ)
            print(f"Cleaning up articles older than {cutoff_dt}")
            
            statement = select(Article).where((Article.published_at < cutoff_dt) | (Article.published_at == None))
            articles_to_delete = session.exec(statement).all()
            
            if articles_to_delete:
                for art in articles_to_delete:
                    # Cleanup audio directory
                    try:
                        audio_path = os.path.join(AUDIO_DIR, str(art.id))
                        if os.path.exists(audio_path):
                            shutil.rmtree(audio_path)
                    except Exception as e:
                        logger.error(f"Failed to delete audio dir for {art.id}: {e}")

                    session.delete(art)
                
                session.commit()
                print(f"Cleanup: Deleted {len(articles_to_delete)} old articles.")
            else:
                print("Cleanup: No old articles found.")
    except Exception as e:
        print(f"Cleanup failed: {e}")


    # 2. Fetch New Articles
    page = 1
    
    with Session(engine) as session:
        while True:
            logger.info(f"Fetching page {page}...")
            try:
                resp = requests.get(list_url, params={"ipp": 10, "page": page}, headers=headers)
                if resp.status_code != 200: break
                articles_data = resp.json().get('objects', [])
                if not articles_data: break
            except Exception as e:
                logger.error(f"Network error: {e}")
                break
            
            # Check dates
            page_too_old = False
            for item in articles_data:
                item_date_str = item.get('date')
                if item_date_str:
                    try:
                        item_date = datetime.strptime(item_date_str, "%Y-%m-%d").date()
                        if item_date < cutoff_date:
                            logger.info(f"Page contains articles older than {cutoff_date}. Stopping crawl.")
                            return
                    except: pass
            
            for item in articles_data:
                article_id = item.get('id')
                
                existing = session.exec(select(Article).where(Article.source_url.contains(article_id))).first()
                if existing:
                    # Already exists, we check if processed just in case.
                    if not existing.paragraphs or not existing.paragraphs[0].translation:
                         process_article_eagerly(session, existing)
                    continue
                
                # Fetch details
                try:
                    detail_resp = requests.get(f"https://apiv3.shanbay.com/news/articles/{article_id}", headers=headers)
                    if detail_resp.status_code != 200: continue
                    detail = detail_resp.json()
                except: continue
                
                title_en = detail.get('title_en', 'No Title')
                published_at_str = detail.get('published_at')
                published_at = datetime.now(CN_TZ)
                if published_at_str:
                    try:
                        dt_naive = datetime.strptime(published_at_str, "%Y-%m-%d %H:%M:%S")
                        published_at = dt_naive.replace(tzinfo=CN_TZ)
                    except: pass
                
                if published_at.date() < cutoff_date:
                    logger.info("Article too old. Stopping.")
                    return

                # Difficulty
                grade_info = detail.get('grade_info')
                sbay_level_name = detail.get('sbay_level', {}).get('name')
                difficulty = DifficultyLevel.UNKNOWN
                if grade_info and grade_info in GRADE_MAP: difficulty = GRADE_MAP[grade_info]
                elif sbay_level_name and sbay_level_name in GRADE_MAP: difficulty = GRADE_MAP[sbay_level_name]

                # Parse content
                para_items = clean_xml_content(detail.get('content', ''))
                word_count = sum(len(p['content'].split()) for p in para_items if p['type'] == 'text')
                
                # Save Article
                article = Article(
                    title=title_en,
                    source_url=f"https://web.shanbay.com/reading/web-news/articles/{article_id}",
                    cover_image=detail.get('thumbnail_urls', [None])[0],
                    difficulty=difficulty,
                    word_count=word_count,
                    published_at=published_at,
                    created_at=datetime.now(CN_TZ)
                )
                session.add(article)
                session.commit()
                session.refresh(article)
                
                # Save Paragraphs
                for idx, p_item in enumerate(para_items):
                    p = Paragraph(
                        article_id=article.id,
                        order_index=idx + 1,
                        content=p_item['content'] if p_item['type'] == 'text' else "",
                        image_url=p_item['content'] if p_item['type'] == 'image' else None
                    )
                    session.add(p)
                session.commit()
                session.refresh(article)
                
                # Eager Process
                process_article_eagerly(session, article)
                
                time.sleep(1) # Rate limit

            page += 1
            if page > 5: break # Safety - 3 days fit in 3-5 pages usually

            time.sleep(1)
