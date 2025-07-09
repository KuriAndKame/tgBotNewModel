# Telegram & RSS Parser

**Telegram & RSS Parser** — это Python-проект для мониторинга новостей из Telegram-каналов и RSS-лент. Парсеры сохраняют новые записи в формате JSON и позволяют автоматизировать сбор информации из разных источников.
## Установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/Forevermorre/parser4vgtrk.git
cd parser4vgtrk
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл **.env** с данными для авторизации в Telegram:
```bash
python DotEnvCreate.py
```
Или создайте **.env** вручную:
```
API_ID=ваш_api_id
API_HASH=ваш_api_hash
PHONE_NUMBER=ваш_номер_телефона
TELEGRAM_PASSWORD=ваш_пароль_для_2FA
```
(Вам потребуются **API ID** и **API HASH** с my.telegram.org)

4. Настройка источников

**data/channels.txt** — список Telegram-каналов. Примеры:
```
https://t.me/parser4vgtrk
https://t.me/parser4vgtrk2
```
**data/sites.txt** — список RSS-лент. Примеры:
```
https://lenta.ru/rss/news
https://www.kommersant.ru/RSS/news.xml
https://ria.ru/export/rss2/archive/index.xml
```

5. Запуск

**Telegram-парсер**
```bash
python TelegramParser.py
```
При первом запуске потребуется ввести код подтверждения из Telegram и, при необходимости, пароль 2FA.

**RSS-парсер**
```bash
python RSSParser.py
```

6. Результаты

**output/telegram.json** — список сообщений из Telegram.

**output/rss.json** — список записей из RSS-лент.
