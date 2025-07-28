from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint, Boolean
from db.database import Base

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_msg_id = Column(Integer, nullable=False)
    source = Column(String(255), nullable=False)
    date = Column(DateTime, nullable=False)
    title = Column(String(255))
    summary = Column(Text)
    text = Column(Text)
    media_file = Column(Text)
    refactoredTitle = Column(String(255))
    refactoredText = Column(Text)
    resume = Column(Text)
    tags = Column(String(255))
    is_telegram = Column(Boolean)

    __table_args__ = (
        UniqueConstraint('telegram_msg_id', 'source', name='uix_msg_source'),
    )
