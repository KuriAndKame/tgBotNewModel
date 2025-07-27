from flask import Flask, render_template, jsonify, request
import pymysql
from config import DB_CONFIG

app = Flask(__name__)


def get_db_connection():
    return pymysql.connect(**DB_CONFIG)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/posts')
def index_posts():
    return render_template('index_1.html')


@app.route('/news/<int:news_id>')
def news_detail(news_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM news WHERE id=%s"
            cursor.execute(sql, (news_id,))
            news_item = cursor.fetchone()
    finally:
        conn.close()

    return render_template('news_detail.html', news=news_item)

@app.route('/news_posts/<int:news_id>')
def news_detail_posts(news_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM news_posts WHERE id=%s"
            cursor.execute(sql, (news_id,))
            news_item = cursor.fetchone()
    finally:
        conn.close()

    return render_template('news_detail_1.html', news=news_item)

@app.route('/get_news')
def get_news():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, title, summary, text, refactoredTitle, resume FROM news ORDER BY date DESC"
            cursor.execute(sql)
            news_list = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(news_list)

@app.route('/get_news_posts')
def get_news_posts():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, refactoredTitle, resume FROM news_posts ORDER BY id DESC"
            cursor.execute(sql)
            news_list = cursor.fetchall()
    finally:
        conn.close()

    return jsonify(news_list)

if __name__ == '__main__':
    app.run(debug=True)