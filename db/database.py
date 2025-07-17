from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import json

# Загружаем конфиг
with open("data/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

DATABASE_URL = config.get("db_url")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
    future=True
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
