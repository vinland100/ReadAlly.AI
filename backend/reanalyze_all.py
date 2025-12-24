import os
import sys
import json
import logging
import time
from sqlmodel import Session, select, create_engine
from dotenv import load_dotenv

# Ensure we can import from local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Article, Paragraph
from ai_service import AIService
from log_conf import setup_logging

# Setup Logging
setup_logging()
logger = logging.getLogger(__name__)

# Load env vars
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./readally.db")
# Add check_same_thread=False for SQLite
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def reanalyze_all():
    logger.info("🚀 Starting Global Vocabulary Re-analysis...")
    
    with Session(engine) as session:
        # 1. Get All Articles
        articles = session.exec(select(Article)).all()
        logger.info(f"Found {len(articles)} articles in total.")
        
        for idx, article in enumerate(articles):
            logger.info(f"\n📄 [{idx+1}/{len(articles)}] Processing: {article.title} (ID: {article.id})")
            
            # 2. Get Paragraphs for this article
            paragraphs = session.exec(select(Paragraph).where(Paragraph.article_id == article.id).order_by(Paragraph.order_index)).all()
            
            level = article.difficulty.value if article.difficulty else "Advanced"
            logger.info(f"   - Difficulty Level: {level}")
            logger.info(f"   - Paragraphs: {len(paragraphs)}")
            
            updates_count = 0
            
            for p in paragraphs:
                if not p.content.strip():
                    continue
                
                try:
                    # Force re-analysis with new prompt logic
                    # We add a small delay to avoid rate limits if necessary, though Dashscope is usually fast.
                    new_analysis = AIService.analyze_vocabulary(p.content, level)
                    
                    if new_analysis:
                        p.analysis = json.dumps(new_analysis, ensure_ascii=False)
                        session.add(p)
                        updates_count += 1
                        print(".", end="", flush=True) # visual progress
                    else:
                        print("x", end="", flush=True)
                        
                except Exception as e:
                    logger.error(f"   ❌ Error analyzing paragraph {p.id}: {e}")
            
            print("") # Newline after dots
            
            # Commit per article to save progress incrementally
            session.commit()
            logger.info(f"   ✅ Updated {updates_count}/{len(paragraphs)} paragraphs.")
            
            # Optional: Sleep briefly between articles
            time.sleep(1)

    logger.info("\n🎉 Global Re-analysis Complete!")

if __name__ == "__main__":
    reanalyze_all()
