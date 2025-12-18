from sqlmodel import Session, text
from database import engine

def add_avatar_column():
    with Session(engine) as session:
        try:
            session.exec(text("ALTER TABLE user ADD COLUMN avatar_seed VARCHAR DEFAULT 'Cookie'"))
            session.commit()
            print("Column avatar_seed added successfully.")
        except Exception as e:
            print(f"Error or column already exists: {e}")

if __name__ == "__main__":
    add_avatar_column()
