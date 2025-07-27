# Конфигурации БД
DB_CONFIG = {
    'host': 'localhost',
    'database': 'news_db',
    'user': 'user',
    'password': 'password',
    'cursorclass': 'pymysql.cursors.DictCursor'
}

# Конфиругации модели
MODEL_CONFIG = {
    'url': "http://localhost:1234/v1/chat/completions",
    'temperature': 0.4,
    'max_tokens': 6000,
    'max_tokens_per_request': 6000
}

# Файл с промтом
PROMPT_FILE = "promt.txt"