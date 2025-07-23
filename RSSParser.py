import os
import json
import asyncio
import aiohttp
import feedparser
from datetime import datetime, timezone
from urllib.parse import urlparse
from sqlalchemy.orm import sessionmaker
from models.Posts import RSSPost, init_db

INPUT_SITES_FILE = 'data/sites.txt'
OUTPUT_FILE = 'output/rss.json'
DB_URL = os.getenv('DB_URL', 'mysql+pymysql://user:password@localhost/news_db')
CHECK_INTERVAL = os.getenv('CHECK_INTERVAL', 60)


class RSSParser:
    def __init__(self):
        self.initialize_files()
        self.start_time = datetime.now(timezone.utc)
        self.session = None

        self.engine = init_db(DB_URL)
        self.Session = sessionmaker(bind=self.engine)

    def initialize_files(self):
        if not os.path.exists(INPUT_SITES_FILE):
            with open(INPUT_SITES_FILE, 'w'):
                print(f"Создан пустой файл {INPUT_SITES_FILE}. Добавьте в него RSS-ленты.")

        if not os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as file:
                json.dump([], file)

    def get_sites(self):
        with open(INPUT_SITES_FILE, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file if line.strip() and not line.startswith('#')]

    def get_domain_name(self, url):
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '').split('.')[0].upper()

    async def fetch_feed(self, url):
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.text()
                    return feedparser.parse(data)
        except Exception as e:
            print(f"Ошибка при загрузке {url}: {str(e)}.")
        return None

    def is_new_entry(self, entry):
        date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']
        pub_date = next((entry.get(f) for f in date_fields if f in entry), None)

        if not pub_date:
            return False

        entry_time = datetime(*pub_date[:6], tzinfo=timezone.utc)
        return entry_time > self.start_time

    def process_entry(self, entry, source_url):
        if not self.is_new_entry(entry):
            return None

        entry_id = entry.get('id', entry.get('link', ''))
        if not entry_id:
            return None

        date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']
        pub_date = next((entry.get(f) for f in date_fields if f in entry), None)
        date = datetime(*pub_date[:6]).isoformat() if pub_date else datetime.now().isoformat()

        return {
            'date': date,
            'source': source_url,
            'title': entry.get('title', 'Без заголовка'),
            'summary': entry.get('summary', ''),
            'link': entry.get('link', ''),
            'rss_id': entry_id,
            'source_type': 'rss'
        }

    def save_news_item(self, news_item, source_url):
        try:
            with open(OUTPUT_FILE, 'r+', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = []

                if not any(item.get('rss_id') == news_item['rss_id'] for item in data):
                    data.append(news_item)
                    file.seek(0)
                    json.dump(data, file, ensure_ascii=False, indent=2)
                    file.truncate()

                    domain = self.get_domain_name(source_url)
                    print(f"[{domain}] {news_item['title']}")
            self.save_to_db(news_item, source_url)
        except Exception as e:
            print(f"Ошибка при сохранении в файл: {str(e)}.")

    def save_to_db(self, news_item, source_url):
        try:
            session = self.Session()

            existing_post = session.query(RSSPost).filter_by(
                rss_id=news_item['rss_id']
            ).first()

            if not existing_post:
                post = RSSPost(
                    date=datetime.fromisoformat(news_item['date']),
                    source=news_item['source'],
                    title=news_item['title'],
                    summary=news_item['summary'],
                    link=news_item['link'],
                    rss_id=news_item['rss_id'],
                    source_type=news_item.get('source_type', 'rss')
                )
                session.add(post)
                session.commit()

                # domain = self.get_domain_name(source_url)
                # print(f"Новость с сайта {domain} сохранена в базу данных.")
        except Exception as e:
            print(f"Ошибка при сохранении в БД: {str(e)}.")
            session.rollback()
        finally:
            session.close()

    async def check_feeds(self):
        sites = self.get_sites()
        if not sites:
            print(f"Добавьте RSS-ленты в {INPUT_SITES_FILE}.")
            return False

        print(f"Проверяем {len(sites)} RSS-лент на новые записи.")
        tasks = [self.fetch_feed(url) for url in sites]
        results = await asyncio.gather(*tasks)

        new_items = 0
        for feed, url in zip(results, sites):
            if feed and feed.entries:
                for entry in feed.entries:
                    news_item = self.process_entry(entry, url)
                    if news_item:
                        self.save_news_item(news_item, url)
                        new_items += 1

        print(f"Найдено {new_items} новых записей после {self.start_time}.")
        return True

    async def run(self):
        print(f"RSS-парсер запущен в {self.start_time}. Ожидание новых записей.\nИспользуйте Ctrl+C для остановки.")
        async with aiohttp.ClientSession() as self.session:
            while True:
                try:
                    await self.check_feeds()
                    await asyncio.sleep(int(CHECK_INTERVAL))
                except KeyboardInterrupt:
                    print("\nЗавершение работы RSS-парсера.")
                    break
                except Exception as e:
                    print(f"Ошибка в основном цикле: {str(e)}.")
                    await asyncio.sleep(int(CHECK_INTERVAL) / 2)
        self.engine.dispose()


if __name__ == '__main__':
    parser = RSSParser()
    try:
        asyncio.run(parser.run())
    except KeyboardInterrupt:
        print("Работа парсера завершена.")
