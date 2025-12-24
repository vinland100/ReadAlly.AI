import os
import sys
import json
import logging
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
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def reanalyze_article(title: str):
    logger.info(f"🚀 Starting Vocabulary Re-analysis for article: {title}")
    
    with Session(engine) as session:
        article = session.exec(select(Article).where(Article.title == title)).first()
        
        if not article:
            logger.error(f"❌ Article not found: {title}")
            return
            
        logger.info(f"📄 Found Article: {article.title} (ID: {article.id})")
        
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
                logger.info(f"   - Analyzing paragraph {p.order_index}...")
                new_analysis = AIService.analyze_vocabulary(p.content, level)
                
                if new_analysis:
                    p.analysis = json.dumps(new_analysis, ensure_ascii=False)
                    session.add(p)
                    updates_count += 1
                else:
                    logger.warning(f"   - Analysis result empty for paragraph {p.order_index}")
                    
            except Exception as e:
                logger.error(f"   ❌ Error analyzing paragraph {p.id}: {e}")
        
        session.commit()
        logger.info(f"   ✅ Updated {updates_count}/{len(paragraphs)} paragraphs.")
        
    logger.info("\n🎉 Re-analysis Complete!")

if __name__ == "__main__":
    target_title = "Scientists Uncover the Story of Donkey Domestication"
    reanalyze_article(target_title)
