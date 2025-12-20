import sys
import os
from sqlmodel import Session, select, text

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine
from models import Article, Paragraph
from crawler.shanbay import fetch_shanbay_articles

def clear_db():
    print("Clearing database...")
    with Session(engine) as session:
        session.exec(text("DELETE FROM paragraph"))
        session.exec(text("DELETE FROM article"))
        session.commit()
    print("Database cleared.")

if __name__ == "__main__":
    clear_db()
    print("Re-fetching articles...")
    fetch_shanbay_articles()
    print("Done.")
