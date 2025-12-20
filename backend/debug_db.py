from sqlmodel import Session, select, create_engine
from models import Article, Paragraph
from database import engine

def check_article():
    with Session(engine) as session:
        # Try to find the article by paragraph content
        search_term = "happiness beyond the big 3-0"
        
        paragraphs = session.exec(select(Paragraph).where(Paragraph.content.contains(search_term))).all()
        
        if not paragraphs:
            print(f"No paragraphs found containing '{search_term}'")
            # List all articles to see what we have
            all_articles = session.exec(select(Article)).limit(5).all()
            print("First 5 articles in DB:")
            for a in all_articles:
                print(f"- {a.title}")
            return

        print(f"Found {len(paragraphs)} paragraph(s).")
        
        for p in paragraphs:
            print(f"Article ID: {p.article_id}")
            print(f"Paragraph ID: {p.id}")
            print(f"Analysis present? {'YES' if p.analysis else 'NO'}")
            if p.analysis:
                print(f"  Sample: {p.analysis[:300]}...")
            else:
                print(f"  Content: {p.content[:100]}...")

if __name__ == "__main__":
    check_article()
