
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
from models import Article, Paragraph, DifficultyLevel
from ai_service import AIService

# China Standard Time
# China Standard Time
CN_TZ = timezone(timedelta(hours=8))

static_dir = os.getenv("STATIC_DIR", "static")
if not os.path.isabs(static_dir):
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), static_dir)
    
AUDIO_DIR = os.path.join(static_dir, "audio")

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

# Logging is configured in main.py via log_conf
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
        # 1. Extract images
        img_full_pattern = re.compile(r'<img.*?>.*?</img>', re.DOTALL)
        img_tags = img_full_pattern.findall(para_content)
        for img_tag in img_tags:
            url_match = re.search(r'<url>(.*?)</url>', img_tag, re.DOTALL)
            if url_match:
                img_url = url_match.group(1).strip()
                if img_url:
                    parseds.append({'type': 'image', 'content': img_url})
        
        # 2. Strip image tags to avoid picking up their descriptions (CDATA) as text
        text_para_content = img_full_pattern.sub('', para_content)
        
        # 3. Extract text sentences
        cdata_pattern = re.compile(r'<!\[CDATA\[(.*?)\]\]>')
        sentences = cdata_pattern.findall(text_para_content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if sentences:
            para_text = " ".join(sentences).strip()
            if para_text:
                parseds.append({'type': 'text', 'content': para_text})
    return parseds

def import_json_string(data):
    if isinstance(data, str): return data
    return json.dumps(data, ensure_ascii=False)

def retry_with_backoff(func, *args, max_retries=3, initial_delay=2, backoff_factor=2, **kwargs):
    """
    Executes a function with a retry mechanism and exponential backoff.
    """
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"在 {max_retries} 次尝试后失败。最后一次错误: {e}")
                raise e
            logger.warning(f"第 {attempt + 1} 次尝试失败: {e}。将在 {delay} 秒后重试...")
            time.sleep(delay)
            delay *= backoff_factor
            
def process_article_eagerly(session: Session, article: Article):
    logger.info(f"正在进行文章积极处理流程: {article.title}")
    
    article_audio_dir = os.path.join(AUDIO_DIR, str(article.id))
    os.makedirs(article_audio_dir, exist_ok=True)
    
    paragraphs = session.exec(select(Paragraph).where(Paragraph.article_id == article.id).order_by(Paragraph.order_index)).all()
    
    for p in paragraphs:
        if not p.content.strip(): continue

        # 1. Translation
        if not p.translation:
            try:
                trans_res = retry_with_backoff(AIService.translate_paragraph, p.content)
                p.translation = import_json_string(trans_res)
                session.add(p)
                session.commit()
            except Exception as e:
                logger.error(f"段落 {p.id} 翻译失败: {e}")
            time.sleep(0.5)

        # 2. Syntax
        if not p.syntax:
            try:
                syntax_res = retry_with_backoff(AIService.analyze_syntax, p.content)
                p.syntax = import_json_string(syntax_res)
                session.add(p)
                session.commit()
            except Exception as e:
                logger.error(f"段落 {p.id} 句法分析失败: {e}")
            time.sleep(0.5)

        # 3. Audio
        # Naming convention: static/audio/{article_id}/{article_id}_{order_index}.mp3
        filename = f"{article.id}_{p.order_index}.mp3"
        p_audio_path = os.path.join(article_audio_dir, filename)
        rel_path = f"static/audio/{article.id}/{filename}"
        
        if not p.audio_path or not os.path.exists(p_audio_path):
             try:
                 audio_bytes = retry_with_backoff(AIService.generate_tts, p.content)
                 if audio_bytes:
                     with open(p_audio_path, "wb") as f:
                         f.write(audio_bytes)
                     p.audio_path = rel_path
                     session.add(p)
                     session.commit()
                 else:
                     logger.error(f"段落 {p.id} 生成 TTS 失败")
             except Exception as e:
                 logger.error(f"段落 {p.id} TTS 失败: {e}")
             time.sleep(0.5)

    # 4. Vocabulary (Batched by 20 to match pagination)
    all_paras = session.exec(select(Paragraph).where(Paragraph.article_id == article.id).order_by(Paragraph.order_index)).all()
    
    batch_size = 20
    for i in range(0, len(all_paras), batch_size):
        batch = all_paras[i:i+batch_size]
        
        # Check if already has analysis
        if all(p.analysis for p in batch):
            continue

        logger.info(f"  - 正在分析第 {i//batch_size + 1} 批词汇")
        
        for p in batch:
            if not p.analysis and p.content.strip():
                try:
                    analysis_json = retry_with_backoff(AIService.analyze_vocabulary, p.content, article.difficulty.value)
                    if isinstance(analysis_json, list):
                        p.analysis = import_json_string(analysis_json)
                        session.add(p)
                except Exception as e:
                    logger.error(f"段落 {p.id} 词汇分析失败: {e}")
                time.sleep(0.5)
        
        session.commit()
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
    logger.info("Phase 1: 开始清理旧文章")
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
                        logger.error(f"删除文章 {art.id} 的音视频目录失败: {e}")

                    session.delete(art)
                
                session.commit()
                print(f"Cleanup: Deleted {len(articles_to_delete)} old articles.")
            else:
                print("Cleanup: No old articles found.")
    except Exception as e:
        print(f"Cleanup failed: {e}")


    # 2. Fetch New Articles
    logger.info("Phase 2: 开始爬取新文章")
    page = 1
    
    with Session(engine) as session:
        while True:
            logger.info(f"正在抓取第 {page} 页...")
            try:
                resp = requests.get(list_url, params={"ipp": 10, "page": page}, headers=headers)
                if resp.status_code != 200: break
                articles_data = resp.json().get('objects', [])
                if not articles_data: break
            except Exception as e:
                logger.error(f"网络错误: {e}")
                break
            
            # Check dates
            for item in articles_data:
                item_date_str = item.get('date')
                if item_date_str:
                    try:
                        item_date = datetime.strptime(item_date_str, "%Y-%m-%d").date()
                        if item_date < cutoff_date:
                            logger.info(f"页面包含早于 {cutoff_date} 的文章。停止爬取。")
                            return
                    except: pass
            
            for item in articles_data:
                article_id = item.get('id')
                
                existing = session.exec(select(Article).where(Article.source_url.contains(article_id))).first()
                if existing:
                    # Skip discovery as it's already in DB. 
                    # Processing will be handled in the second pass.
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
                    logger.info("文章太旧。停止。")
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
                
                # Skip Eager Process here to avoid blocking discovery.
                # Processing will be handled in the second pass.
                # process_article_eagerly(session, article)
                
                time.sleep(1) # Rate limit

            page += 1
            if page > 5: break # Safety - 3 days fit in 3-5 pages usually

            time.sleep(1)

    # 3. Phase 2: Sequential Processing Pass
    # After discovering all new articles, we iterate through recent articles to process them.
    logger.info("Phase 3: 开始调用文章 AI 顺序处理每一篇文章")
    with Session(engine) as session:
        # Re-calculate cutoff for identifying recent articles to process
        cutoff_dt = datetime.combine(cutoff_date, datetime.min.time()).replace(tzinfo=CN_TZ)
        recent_articles = session.exec(select(Article).where(Article.published_at >= cutoff_dt)).all()
        
        for art in recent_articles:
            # Re-fetch or check paragraphs to ensure we have the latest state
            # Using the user's original check mechanism as requested
            if not art.paragraphs or not art.paragraphs[0].translation:
                try:
                    process_article_eagerly(session, art)
                except Exception as e:
                    logger.error(f"文章 {art.id} 顺序处理失败: {e}")

    logger.info("扇贝文章爬取和处理任务完成。")
