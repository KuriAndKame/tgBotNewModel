import json
import os
from collections import defaultdict
from datetime import datetime
from telethon.tl.functions.messages import GetHistoryRequest
from db.database import SessionLocal
from models.News import News
from scraper.utils import extract_title_and_summary

with open("data/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

MEDIA_DIR = config.get("media_dir", "data/media")
os.makedirs(MEDIA_DIR, exist_ok=True)

async def fetch_new_messages(client, channel_name):
    session = SessionLocal()
    try:
        entity = await client.get_entity(channel_name)
        history = await client(GetHistoryRequest(
            peer=entity,
            limit=50,
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))

        messages = sorted(history.messages, key=lambda x: x.id)
        grouped = defaultdict(list)

        for msg in messages:
            if not msg.date or (not msg.message and not msg.media):
                continue
            dt_key = msg.date.replace(microsecond=0)
            grouped[dt_key].append(msg)

        for dt, msgs in grouped.items():
            #exists = session.query(News).filter_by(date=dt, source=channel_name).first()
            exists = session.query(News).filter_by(telegram_msg_id=msgs[0].id, source=channel_name).first()
            if exists:
                continue

            text = None
            media_files = []

            for msg in msgs:
                if not text and msg.message:
                    text = msg.message

                if msg.media:
                    try:
                        date_folder = msg.date.strftime("%Y-%m-%d")
                        filename = f"{channel_name}_{date_folder}_{msg.id}"
                        id_folder = str(msg.id)
                        save_dir = os.path.join(MEDIA_DIR, date_folder, channel_name, id_folder)
                        #file=os.path.join(MEDIA_DIR, filename)
                        file_path = await client.download_media(
                            msg,
                            file=save_dir
                        )
                        if file_path:
                            media_files.append(os.path.abspath(file_path))
                    except Exception as e:
                        print(f"[{channel_name}] Ошибка при загрузке медиа: {e}")

            if not text and not media_files:
                continue

            title, summary = extract_title_and_summary(text)

            news = News(
                telegram_msg_id=msgs[0].id,
                source=channel_name,
                date=dt,
                title=title,
                summary=summary,
                text=text,
                media_file=";".join(media_files) if media_files else None,
                is_telegram = True
            )

            session.add(news)

        session.commit()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Обновлено: {channel_name}")

    except Exception as e:
        print(f"[{channel_name}] Ошибка: {e}")
        session.rollback()
    finally:
        session.close()
