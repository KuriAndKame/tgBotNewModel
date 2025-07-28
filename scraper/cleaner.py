import os
import pytz
import json
from datetime import datetime
from db.database import SessionLocal
from models.News import News

with open("data/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

MEDIA_DIR = config.get("media_dir", "data/media")

def remove_empty_dirs(path):
    if not os.path.isdir(path):
        return
    for root, dirs, files in os.walk(path, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    print(f"Удалена пустая папка: {dir_path}")
            except Exception as e:
                print(f"Ошибка при удалении папки {dir_path}: {e}")

def clean_old_news():
    session = SessionLocal()
    try:
        msk = pytz.timezone("Europe/Moscow")
        today_start_msk = datetime.now(msk).replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_utc = today_start_msk.astimezone(pytz.utc)

        old_records = session.query(News).filter(News.date < today_start_utc, News.refactoredText.isnot(None)).all()
        print(f"[Очистка] Найдено старых записей до {today_start_utc} (МСК: {today_start_msk}): {len(old_records)}")

        for rec in old_records:
            if rec.media_file:
                media_files = rec.media_file.split(";")
                for mf in media_files:
                    try:
                        if os.path.exists(mf):
                            os.remove(mf)
                            print(f"Удалён файл: {mf}")
                        else:
                            print(f"Файл не найден, пропускаем: {mf}")
                    except Exception as e:
                        print(f"Ошибка при удалении файла {mf}: {e}")

        deleted = session.query(News).filter(News.date < today_start_utc, News.refactoredText.isnot(None)).delete(synchronize_session=False)
        session.commit()
        print(f"[Очистка] Удалено записей: {deleted}")

        # Удаляем пустые папки с датами
        for entry in os.listdir(MEDIA_DIR):
            entry_path = os.path.join(MEDIA_DIR, entry)
            if os.path.isdir(entry_path):
                try:
                    folder_date = datetime.strptime(entry, "%Y-%m-%d").replace(tzinfo=msk)
                    if folder_date < today_start_msk:
                        remove_empty_dirs(entry_path)
                        if not os.listdir(entry_path):
                            os.rmdir(entry_path)
                            print(f"Удалена пустая папка даты: {entry_path}")
                except ValueError:
                    pass

    except Exception as e:
        session.rollback()
        print(f"[Очистка] Ошибка при удалении: {e}")
    finally:
        session.close()
