import asyncio
import json
from telethon import TelegramClient
from scraper.fetcher import fetch_new_messages
from db.database import Base, engine
from models.News import News

# Загрузка конфигурации
with open("data/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

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
    Base.metadata.create_all(bind=engine)  # создаем таблицы

    client = TelegramClient('session_multi', API_ID, API_HASH)
    await client.start(phone=PHONE)


    while True:
        print(f"Парсер запущен. Проверка каждые {TICK} секунд...")
        tasks = [fetch_new_messages(client, ch) for ch in CHANNELS]
        await asyncio.gather(*tasks)
        await asyncio.sleep(TICK)

if __name__ == "__main__":
    asyncio.run(main())
