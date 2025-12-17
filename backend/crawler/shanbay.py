import requests
import re
import datetime
from sqlmodel import Session, select
from database import engine
from models import Article, Paragraph, DifficultyLevel

# Mapping from Shanbay 'grade_info' or 'sbay_level' to our DifficultyLevel
# Shanbay: 初阶 (高考), 中阶 (四级), 中高阶 (六级/考研), 高阶 (雅思/托福/专四)
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

def clean_xml_content(xml_text):
    """
    Parses Shanbay's XML content format.
    Example: <sent id="..."><![CDATA[Hello World]]></sent>
    Returns a list of paragraph strings.
    """
    if not xml_text:
        return []
    
    # We want to preserve paragraph structure.
    # Shanbay uses <para> tags to denote paragraphs.
    # content looks like: <article_content ...><para ...><sent ...><![CDATA[...]]></sent><sent ...>...</sent></para>...</article_content>
    
    paragraphs = []
    
    # Simple regex approach: find all <para>...</para> blocks first (optional, but good for structure)
    # However, simple CDATA extraction might be enough if we just want text.
    # But to separate paragraphs, we should split by <para>.
    
    para_pattern = re.compile(r'<para.*?>(.*?)</para>', re.DOTALL)
    para_matches = para_pattern.findall(xml_text)
    
    if not para_matches:
        # Fallback if no para tags found, just extract all CDATA
        cdata_pattern = re.compile(r'<!\[CDATA\[(.*?)\]\]>')
        all_text = " ".join(cdata_pattern.findall(xml_text))
        if all_text.strip():
            return [all_text.strip()]
        return []

    for para_content in para_matches:
        # Extract CDATA content within the paragraph
        cdata_pattern = re.compile(r'<!\[CDATA\[(.*?)\]\]>')
        sentences = cdata_pattern.findall(para_content)
        para_text = " ".join(sentences).strip()
        if para_text:
            paragraphs.append(para_text)
            
    return paragraphs


def fetch_shanbay_articles():
    print(f"[{datetime.datetime.now()}] Starting Shanbay crawl...")
    list_url = "https://apiv3.shanbay.com/news/retrieve/articles"
    params = {"ipp": 6, "page": 1} # Fetch 6 articles
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(list_url, params=params, headers=headers)
        if resp.status_code != 200:
            print(f"Failed to fetch list: {resp.status_code}")
            return
        
        articles_data = resp.json().get('objects', [])
        print(f"Found {len(articles_data)} articles.")

        for item in articles_data:
            article_id = item.get('id')
            
            # 1. Check if article exists (Quick DB read)
            exists = False
            with Session(engine) as session:
                existing = session.exec(select(Article).where(Article.source_url.contains(article_id))).first()
                if existing:
                    exists = True
            
            if exists:
                print(f"Article {article_id} already exists. Skipping.")
                continue

            # 2. Fetch details (Network call - slow, no DB lock)
            detail_url = f"https://apiv3.shanbay.com/news/articles/{article_id}"
            try:
                detail_resp = requests.get(detail_url, headers=headers)
                if detail_resp.status_code != 200:
                    print(f"Failed to fetch detail for {article_id}")
                    continue
                detail = detail_resp.json()
            except Exception as e:
                print(f"Error fetching detail for {article_id}: {e}")
                continue

            # Extract fields
            title_en = detail.get('title_en', 'No Title')
            
            # Determine difficulty
            grade_info = detail.get('grade_info')
            sbay_level_name = detail.get('sbay_level', {}).get('name')
            
            difficulty = DifficultyLevel.UNKNOWN
            if grade_info and grade_info in GRADE_MAP:
                difficulty = GRADE_MAP[grade_info]
            elif sbay_level_name and sbay_level_name in GRADE_MAP:
                difficulty = GRADE_MAP[sbay_level_name]
            
            # Cover image
            thumbnail_urls = detail.get('thumbnail_urls', [])
            cover_image = thumbnail_urls[0] if thumbnail_urls else None

            # Content parsing
            raw_content = detail.get('content', '')
            para_texts = clean_xml_content(raw_content)
            
            if not para_texts:
                print(f"No content found for {article_id}. Skipping.")
                continue

            word_count = sum(len(p.split()) for p in para_texts)
            
            # 3. Save to DB (Quick DB write)
            with Session(engine) as session:
                # Double check existence just in case
                existing_check = session.exec(select(Article).where(Article.source_url.contains(article_id))).first()
                if existing_check:
                    continue

                new_article = Article(
                    title=title_en,
                    source_url=f"https://web.shanbay.com/reading/web-news/articles/{article_id}",
                    cover_image=cover_image,
                    difficulty=difficulty,
                    word_count=word_count,
                    created_at=datetime.datetime.utcnow()
                )
                session.add(new_article)
                session.commit()
                session.refresh(new_article)

                # Create Paragraphs
                for idx, text in enumerate(para_texts):
                    new_para = Paragraph(
                        article_id=new_article.id,
                        order_index=idx,
                        content=text
                    )
                    session.add(new_para)
                
                session.commit()
                print(f"Saved article: {title_en} ({difficulty})")

    except Exception as e:
        print(f"Crawler failed: {e}")
