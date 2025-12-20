import sys
import os
import sqlite3
import json
import time

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select, create_engine, text
from models import Paragraph, Article, DifficultyLevel
from ai_service import AIService
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = "sqlite:///./readally.db"
engine = create_engine(DATABASE_URL)

def add_column_if_not_exists(cursor, table_name, column_name, column_type):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]
    if column_name not in columns:
        print(f"Adding column {column_name} to {table_name}...")
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
    else:
        print(f"Column {column_name} already exists in {table_name}.")

def migrate_schema():
    print("--- Migrating Schema ---")
    conn = sqlite3.connect("./readally.db")
    cursor = conn.cursor()

    # 1. Add 'analysis' column to Paragraph
    add_column_if_not_exists(cursor, "paragraph", "analysis", "TEXT")
    
    # 2. Add 'translation' and 'syntax' columns if they were missing (just in case)
    # The user's code showed them as fields, but good to be safe.
    
    conn.commit()
    conn.close()
    print("Schema migration complete.")

def backfill_analysis():
    print("--- Backfilling Analysis Data ---")
    with Session(engine) as session:
        # Fetch all paragraphs that need analysis (or ALL of them if --force)
        # For now, let's re-analyze everything as requested "regardless of cost"
        statement = select(Paragraph, Article).join(Article)
        results = session.exec(statement).all()
        
        total = len(results)
        print(f"Found {total} paragraphs to process.")
        
        for i, (paragraph, article) in enumerate(results):
            print(f"[{i+1}/{total}] Processing Paragraph {paragraph.id} (Article: {article.title})...")
            
            # Determine difficulty level (default to Initial if unknown)
            level = article.difficulty.value if article.difficulty else "Initial"
            
            try:
                # Call AI Service
                analysis_result = AIService.analyze_vocabulary(paragraph.content, level)
                
                # Verify result is a list
                if isinstance(analysis_result, list):
                    paragraph.analysis = json.dumps(analysis_result, ensure_ascii=False)
                    session.add(paragraph)
                    session.commit()
                    print(f"  -> Success: {len(analysis_result)} tokens.")
                else:
                    print(f"  -> Error: AI returned invalid format: {type(analysis_result)}")
                
                # Determine sleep to avoid rate limits if necessary
                # time.sleep(0.5) 
                
            except Exception as e:
                print(f"  -> Exception: {e}")
                session.rollback()

    print("Backfill complete.")

def drop_old_table():
    print("--- Dropping Old Table ---")
    conn = sqlite3.connect("./readally.db")
    cursor = conn.cursor()
    try:
        cursor.execute("DROP TABLE IF EXISTS vocabularyannotation")
        conn.commit()
        print("Dropped vocabularyannotation table.")
    except Exception as e:
        print(f"Error dropping table: {e}")
    conn.close()

if __name__ == "__main__":
    print("Starting Migration V2...")
    migrate_schema()
    backfill_analysis()
    drop_old_table()
    print("Migration V2 Finished Successfully.")
