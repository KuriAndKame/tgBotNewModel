import os
import json
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from models.Posts import TelegramPost, init_db

load_dotenv()

API_ID = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
PHONE_NUMBER = os.getenv('PHONE_NUMBER', '')
TELEGRAM_PASSWORD = os.getenv('TELEGRAM_PASSWORD', '')
DB_URL = os.getenv('DB_URL', 'mysql+pymysql://user:password@localhost/news_db')

INPUT_CHANNELS_FILE = 'data/channels.txt'
OUTPUT_FILE = 'output/telegram.json'
SESSION_FILE = 'sessions/TelegramParser.session'


class TelegramParser:
    def __init__(self):
        self.client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
        self.initialize_files()
        self.processed_messages = set()
        self.shutdown = False

        self.engine = init_db(DB_URL)
        self.Session = sessionmaker(bind=self.engine)

    def initialize_files(self):
        if not os.path.exists(INPUT_CHANNELS_FILE):
            with open(INPUT_CHANNELS_FILE, 'w'):
                pass

        if not os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as file:
                json.dump([], file)

    def get_channels(self):
        with open(INPUT_CHANNELS_FILE, 'r', encoding='utf-8') as file:
            channels = []
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    if line.startswith('https://t.me/'):
                        line = line[13:]
                    elif line.startswith('t.me/'):
                        line = line[5:]
                    channels.append(line)
        return channels

    async def authenticate(self):
        try:
            await self.client.start(
                phone=PHONE_NUMBER,
                password=TELEGRAM_PASSWORD if TELEGRAM_PASSWORD else None
            )
            print("Успешная авторизация в Telegram.")
            return True
        except SessionPasswordNeededError:
            print("Требуется двухфакторная аутентификация.")
            password = input("Введите ваш облачный пароль Telegram: ")
            try:
                await self.client.start(
                    phone=PHONE_NUMBER,
                    password=password
                )
                return True
            except Exception as e:
                print(f"Ошибка авторизации: {e}.")
                return False
        except Exception as e:
            print(f"Ошибка подключения: {e}.")
            return False

    async def process_message(self, message, channel):
        if not message.text:
            return

        message_id = f"{channel.id}_{message.id}"
        if message_id in self.processed_messages:
            return None

        news_item = {
            'date': message.date.isoformat(),
            'channel_id': channel.id,
            'channel_name': channel.title,
            'message_id': message.id,
            'text': message.text,
            'url': f"https://t.me/c/{channel.id}/{message.id}"
        }

        self.save_to_json(news_item)
        self.save_to_db(news_item)
        print(f"[{channel.title}] Новое сообщение: {message.text}")

        self.processed_messages.add(message_id)
        return news_item

    def save_to_db(self, news_item):
        try:
            session = self.Session()

            existing_post = session.query(TelegramPost).filter_by(
                channel_id=news_item['channel_id'],
                message_id=news_item['message_id']
            ).first()

            if not existing_post:
                post = TelegramPost(
                    date=datetime.fromisoformat(news_item['date']),
                    channel_id=news_item['channel_id'],
                    channel_name=news_item['channel_name'],
                    message_id=news_item['message_id'],
                    text=news_item['text'],
                    url=news_item['url']
                )
                session.add(post)
                session.commit()

                # print(f"Новость с канала {news_item['channel_name']} сохранена в базу данных.")
        except Exception as e:
            print(f"Ошибка при сохранении в базу данных: {e}")
            session.rollback()
        finally:
            session.close()

    def save_to_json(self, news_item):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []

        if not any(item['message_id'] == news_item['message_id'] and
                   item['channel_id'] == news_item['channel_id'] for item in data):
            data.append(news_item)

            with open(OUTPUT_FILE, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)

    async def load_processed_messages(self):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.processed_messages = {f"{item['channel_id']}_{item['message_id']}" for item in data}
        except (FileNotFoundError, json.JSONDecodeError):
            self.processed_messages = set()

    async def run(self):
        if not await self.authenticate():
            return

        await self.load_processed_messages()

        channels = self.get_channels()
        if not channels:
            print(f"Добавьте каналы в файл {INPUT_CHANNELS_FILE}.")
            return

        print(f"Мониторинг каналов: {', '.join(channels)}.")

        @self.client.on(events.NewMessage())
        async def handler(event):
            if event.is_channel:
                try:
                    channel = await event.get_chat()
                    channel_username = getattr(channel, 'username', None)

                    if (channel_username in channels or
                            f"-100{channel.id}" in channels or
                            str(channel.id) in channels):
                        message_id = f"{channel.id}_{event.message.id}"
                        if message_id not in self.processed_messages:
                            await self.process_message(event.message, channel)
                except Exception as e:
                    print(f"Ошибка обработки сообщения: {e}.")

        print("Парсер запущен. Ожидание новых сообщений. Используйте Ctrl+C для остановки.")
        await self.client.run_until_disconnected()


async def main():
    parser = TelegramParser()
    try:
        await parser.run()
    except KeyboardInterrupt:
        print("\nЗавершение работы телеграм-парсера.")
    except Exception as e:
        print(f"Критическая ошибка: {e}.")
    finally:
        if not parser.shutdown:
            await parser.client.disconnect()
        parser.engine.dispose()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Работа парсера завершена.")