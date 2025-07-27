import pymysql.cursors

DB_CONFIG = {
    'host': 'localhost',
    'user': 'user',
    'password': 'password',
    'database': 'news_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}