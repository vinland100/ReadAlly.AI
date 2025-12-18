from sqlmodel import Session, select
from database import engine
from models import Paragraph, Article

def check_images():
    with Session(engine) as session:
        art = session.exec(select(Article).where(Article.source_url.contains("ocige"))).first()
        if art:
            print(f"Article: {art.title}, ID: {art.id}")
            paras = session.exec(select(Paragraph).where(Paragraph.article_id == art.id)).all()
            for p in paras:
                if p.image_url:
                    print(f"Para {p.order_index} has image: {p.image_url}")
        else:
            print("Article not found")

if __name__ == "__main__":
    check_images()
