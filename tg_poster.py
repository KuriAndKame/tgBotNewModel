import os
import datetime
import asyncio
import mysql.connector
from dotenv import load_dotenv
from telethon import TelegramClient

# ====================
# === Загрузка .env ===
# ====================
load_dotenv()

# -- Обязательные параметры --
API_ID       = int(os.getenv('API_ID'))
API_HASH     = os.getenv('API_HASH')
SESSION_NAME = os.getenv('SESSION_NAME', 'autopost_session')
PHONE        = os.getenv('PHONE', '')

# -- Параметры устройства --
client_kwargs = {}
for key, env_key in [
    ('device_model',     'DEVICE_MODEL'),
    ('system_version',   'SYSTEM_VERSION'),
    ('app_version',      'APP_VERSION'),
    ('lang_code',        'LANG_CODE'),
    ('system_lang_code', 'SYSTEM_LANG_CODE')
]:
    val = os.getenv(env_key)
    if val:
        client_kwargs[key] = val

# -- MySQL настройки --
DB_HOST        = os.getenv('DB_HOST', 'localhost')
DB_USER        = os.getenv('DB_USER', 'root')
DB_PASSWORD    = os.getenv('DB_PASSWORD', 'root')
DB_NAME        = os.getenv('DB_NAME', 'telegram_news')
DB_TABLE       = os.getenv('DB_TABLE', 'news')
DB_POSTS_TABLE = os.getenv('DB_POSTS_TABLE', 'news_posts')

# -- Канал и интервалы --
CHANNEL        = os.getenv('CHANNEL')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 300))
SCHEDULE_DELAY = int(os.getenv('SCHEDULE_DELAY', 3600))
POST_DELAY     = int(os.getenv('POST_DELAY', 5))
RETRY_DELAY    = int(os.getenv('RETRY_DELAY', 5))

# ====================
# === Работа с БД ===
# ====================

def get_unsent_news(conn):
    out = []
    for table in (DB_TABLE, DB_POSTS_TABLE):
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM `{table}` WHERE tg_sent = 0 and refactoredTitle is not null and refactoredText is not null")
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            row['_table'] = table
            if table == DB_POSTS_TABLE:
                row['text'] = row.get('content', '')
                row['media_file'] = None
            out.append(row)
    return out

async def mark_sent(conn, table, item_id):
    cursor = conn.cursor()
    cursor.execute(f"UPDATE `{table}` SET tg_sent = 1 WHERE id = %s", (item_id,))
    conn.commit()
    cursor.close()

# ====================
# === Отправка в Telegram ===
# ====================
async def schedule_post(client, item):
    peer = await client.get_entity(CHANNEL)
    send_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=SCHEDULE_DELAY)
    title = item.get('refactoredTitle') or item.get('title', '')
    text = item.get('refactoredText') or item.get('text', '')
    caption = (
        f"<b>{title}</b>\n\n"
        f"{text}\n\n"
        "📰 <a href='https://t.me/volgograd_24'>Подписаться</a> | "
        "<a href='https://volgograd-trv.ru/'>Перейти на сайт</a>"
    )
    media = item.get('media_file') or ''
    media_list = []
    if media:
        if isinstance(media, str):
            media_list = [m.strip() for m in media.split(';') if m.strip()]
        elif isinstance(media, (list, tuple)):
            media_list = media
    if media_list:
        result = await client.send_file(
            peer,
            media_list,
            caption=caption,
            parse_mode='html',
            schedule=send_time
        )
        return result[-1].id if isinstance(result, list) else result.id
    else:
        msg = await client.send_message(
            peer,
            caption,
            parse_mode='html',
            schedule=send_time
        )
        return msg.id

# ====================
# === Основная логика ===
# ====================
async def run_autopost():
    while True:
        try:
            # Запускаем Telegram-клиент
            async with TelegramClient(
                SESSION_NAME,
                API_ID,
                API_HASH,
                connection_retries=5,
                retry_delay=2,
                request_retries=3,
                timeout=10,
                auto_reconnect=True,
                **client_kwargs
            ) as client:
                print('[TG] Клиент запущен, начало автопостинга...')
                while True:
                    # Открываем новое соединение к БД для каждой итерации
                    print('[DB] Подключаемся и получаем неподанные новости...')
                    db_conn = mysql.connector.connect(
                        host=DB_HOST,
                        user=DB_USER,
                        password=DB_PASSWORD,
                        database=DB_NAME
                    )
                    unsent = get_unsent_news(db_conn)
                    print(f'[DB] Найдено записей: {len(unsent)}')
                    if unsent:
                        for item in unsent:
                            try:
                                tg_id = await schedule_post(client, item)
                                await mark_sent(db_conn, item['_table'], item['id'])
                                print(f"[TG] Запланировано сообщение ID={tg_id} для записи ID={item['id']} из {item['_table']}")
                                await asyncio.sleep(POST_DELAY)
                            except Exception as e:
                                print(f"[TG] Ошибка при отправке записи ID={item['id']}: {e}")
                    db_conn.close()
                    await asyncio.sleep(CHECK_INTERVAL)
        except Exception as e:
            print(f"[TG] Сбой клиента: {e}. Перезапуск через {RETRY_DELAY} сек...")
            await asyncio.sleep(RETRY_DELAY)

if __name__ == '__main__':
    asyncio.run(run_autopost())
