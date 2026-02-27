from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from database import create_db_and_tables, get_session
from models import User, Article, Paragraph, ReadingRecord
from auth import get_password_hash, verify_password, create_access_token, get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

import reading_service
import uvicorn
import os
import random

from apscheduler.schedulers.background import BackgroundScheduler
from crawler.shanbay import fetch_shanbay_articles
import asyncio
from log_conf import setup_logging
import logging

# Setup Logging with CST
setup_logging()
logger = logging.getLogger(__name__)

# China Standard Time
CN_TZ = timezone(timedelta(hours=8))

app = FastAPI(title="ReadAlly.AI Backend")

scheduler = BackgroundScheduler()


app.include_router(reading_service.router, prefix="/api", tags=["Reading"])

# CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserCreate(BaseModel):
    email: str
    password: str
    nickname: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    
    # Schedule Shanbay crawler at 10:00 AM daily
    scheduler.add_job(fetch_shanbay_articles, 'cron', hour=10, minute=0, timezone=CN_TZ)
    scheduler.start()
    print("调度器已启动。扇贝爬虫设置为每日上午 10:00 运行。")
    logger.info("系统启动成功，正在监听请求...")

@app.post("/register", response_model=Token)
def register(user_in: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.email == user_in.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(user_in.password)
    
    # 10 random seeds for new users
    avatar_seeds = ["Cookie", "Cinnamon", "Muffin", "Peanut", "Lulu", "Ginger", "Pepper", "Sugar", "Bear", "Zoe"]
    random_seed = random.choice(avatar_seeds)
    
    new_user = User(
        email=user_in.email, 
        hashed_password=hashed_pw, 
        nickname=user_in.nickname or "Reader",
        avatar_seed=random_seed
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    access_token = create_access_token(data={"sub": new_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar_seed: Optional[str] = None

@app.patch("/users/me", response_model=User)
def update_user_me(user_update: UserUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if user_update.nickname is not None:
        current_user.nickname = user_update.nickname
    if user_update.avatar_seed is not None:
        current_user.avatar_seed = user_update.avatar_seed
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user

@app.get("/users/me/stats")
def get_user_stats(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    now_cn = datetime.now(CN_TZ)
    today_cn = now_cn.date()
    
    # If last_read_date is not today, reset words_read_today? 
    # Actually, we should check if it's been more than a day since last_read_date for the streak,
    # but for "words read today", we just check if it's today.
    
    words_today = current_user.words_read_today
    if current_user.last_read_date:
        # last_read_date is saved in UTC, convert to CN_TZ
        lrd_utc = current_user.last_read_date.replace(tzinfo=timezone.utc)
        last_date_cn = lrd_utc.astimezone(CN_TZ).date()
        if last_date_cn < today_cn:
            words_today = 0
            current_user.words_read_today = 0
            session.add(current_user)
            session.commit()
            session.refresh(current_user)

    return {
        "wordsRead": current_user.words_read_today,
        "streak": current_user.current_streak
    }

@app.post("/users/me/record-reading")
def record_reading(article_id: int, word_count: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    now_cn = datetime.now(CN_TZ)
    today_cn = now_cn.date()
    today_str = today_cn.strftime("%Y-%m-%d")
    
    # Reset words if it's a new day
    if current_user.last_read_date:
        lrd_utc = current_user.last_read_date.replace(tzinfo=timezone.utc)
        last_date_cn = lrd_utc.astimezone(CN_TZ).date()
        
        if last_date_cn < today_cn:
            # New day!
            if last_date_cn == today_cn - timedelta(days=1):
                # Consecutive day, increment streak
                current_user.current_streak += 1
            else:
                # Streak broken (more than 1 day gap) or already read today (handled by else)
                current_user.current_streak = 1
            
            current_user.words_read_today = word_count
        else:
            # Same day
            current_user.words_read_today += word_count
    else:
        # First time reading
        current_user.current_streak = 1
        current_user.words_read_today = word_count
    
    # Save as naive UTC in DB
    current_user.last_read_date = datetime.utcnow()
    session.add(current_user)

    # Handle ReadingRecord
    record = session.exec(select(ReadingRecord).where(
        ReadingRecord.user_id == current_user.id,
        ReadingRecord.date == today_str
    )).first()

    if record:
        record.words_read += word_count
    else:
        record = ReadingRecord(user_id=current_user.id, date=today_str, words_read=word_count)
    session.add(record)

    session.commit()
    
    return {"message": "Reading recorded", "words_today": current_user.words_read_today, "streak": current_user.current_streak}

@app.get("/users/me/reading-records")
def get_reading_records(year: int, month: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    month_prefix = f"{year}-{month:02d}-"
    records = session.exec(select(ReadingRecord).where(
        ReadingRecord.user_id == current_user.id,
        ReadingRecord.date.startswith(month_prefix)
    )).all()
    return records
class PasswordChange(BaseModel):
    old_password: str
    new_password: str

@app.post("/users/me/password")
def change_password(password_data: PasswordChange, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    session.add(current_user)
    session.commit()
    return {"message": "Password updated successfully"}

from fastapi.staticfiles import StaticFiles

STATIC_DIR = os.getenv("STATIC_DIR", "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
