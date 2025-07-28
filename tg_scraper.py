import asyncio
import json
import datetime
import pytz  
from telethon import TelegramClient
from scraper.fetcher import fetch_new_messages
from db.database import Base, engine
from models.News import News
from scraper.cleaner import clean_old_news


async def schedule_daily_cleanup(test_mode=False):
    msk = pytz.timezone("Europe/Moscow")

    if test_mode:
        print("[Очистка] Тестовый запуск очистки...")
        clean_old_news()
        return

    while True:
        now = datetime.datetime.now(msk)
        next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run += datetime.timedelta(days=1)

        sleep_seconds = (next_run - now).total_seconds()
        print(f"[Очистка] Следующая очистка в {next_run.strftime('%Y-%m-%d %H:%M:%S')} МСК (через {int(sleep_seconds)} сек)")
        await asyncio.sleep(sleep_seconds)

        clean_old_news()


# Загрузка конфигурации
with open("data/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

TEST_CLEANUP = False
API_ID = config["api_id"]
API_HASH = config["api_hash"]
PHONE = config["phone"]

# Загрузка каналов
with open("data/channels.txt", "r", encoding="utf-8") as f:
    CHANNELS = [line.strip() for line in f if line.strip()]

# Загрузка тикрейта
with open("data/Tick.txt", "r", encoding="utf-8") as f:
    TICK = float(f.readline().strip())

async def main():
    Base.metadata.create_all(bind=engine)

    client = TelegramClient('session_multi', API_ID, API_HASH)
    await client.start(phone=PHONE)

    asyncio.create_task(schedule_daily_cleanup(test_mode=TEST_CLEANUP))

    
    if TEST_CLEANUP:
        print("[Тест] Очистка завершена. Выход из программы.")
        return

    while True:
        print(f"Парсер запущен. Проверка каждые {TICK} секунд...")
        tasks = [fetch_new_messages(client, ch) for ch in CHANNELS]
        await asyncio.gather(*tasks)
        await asyncio.sleep(TICK)

if __name__ == "__main__":
    asyncio.run(main())
