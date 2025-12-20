from sqlmodel import Session, select
from database import engine
from models import Article, Paragraph
from crawler.shanbay import fetch_shanbay_articles
import requests

def refresh_article(article_slug):
    with Session(engine) as session:
        # Find article
        article = session.exec(select(Article).where(Article.source_url.contains(article_slug))).first()
        if article:
            print(f"Deleting article {article.id} to re-fetch...")
            # Delete dependents
            paras = session.exec(select(Paragraph).where(Paragraph.article_id == article.id)).all()
            for p in paras:
                session.delete(p)
            session.delete(article)
            session.commit()
            print("Deleted successfully. Now re-running crawler...")
    
    # Run a limited fetch - this is a bit hacky as fetch_shanbay_articles fetches multiple
    # But for a single test it works if it's recent.
    fetch_shanbay_articles()

if __name__ == "__main__":
    import sys
    slug = sys.argv[1] if len(sys.argv) > 1 else "ocige"
    refresh_article(slug)
