import requests
from time import time, sleep
from bs4 import BeautifulSoup
import pymysql
from pymysql import Error
from config import DB_CONFIG, MODEL_CONFIG, PROMPT_FILE

def import_quotes_to_text(text, quotes):
    for key in quotes:
        text = text.replace(key, "«" + quotes[key][1:][:-1] + "»")
    while '"' in text:
        text = text.replace('"', "«", 1)
        text = text.replace('"', "»", 1)
    text = text.replace("« ", "«")
    text = text.replace(" »", "»")
    return text


def export_quote_from_text(text):
    quotes = {}
    k = 1  # номер цитаты (под цитатой понимаем текст в кавычках длинной более 30 символов)
    i = 0
    while i < len(text):
        if text[i] == '"':
            for j in range(i + 1, len(text)):
                if text[j] == '"':
                    break
            if j + 1 - i > 30:
                quote = text[i:j + 1]
                quotes[f"<<{k}>>"] = quote
                text = text[:i] + f"<<{k}>>" + text[j + 1:]
                k += 1
            else:
                i = j
        i += 1
    return text, quotes


def get_text_from_txt(filename):
    text = ""
    with open(filename, encoding="utf-8") as file:
        for line in file:
            text += line
    return text


def text_to_file(text, filename):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(text)


def chat_with_model(messages, temperature=MODEL_CONFIG['temperature'], max_tokens=MODEL_CONFIG['max_tokens']):
    url = MODEL_CONFIG['url']
    data = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except:
        return "Произошла ошибка при запросе к модели"


def process_one_news(text, promt, max_tokens, temperature=MODEL_CONFIG['temperature']):
    try:
        new_text, quotes = export_quote_from_text(text)
        history = [
            {"role": "system", "content": promt},
            {"role": "user", "content": new_text}
        ]
        response = chat_with_model(history, temperature, max_tokens)
        text = import_quotes_to_text(response, quotes)
        return text
    except Exception as e:
        return f"Ошибка при обработке запроса: {e}"


def update_news_in_db(promt, max_tokens_per_request, temperature):
    # Обработка таблицы news
    try:
        # Подключение к базе данных
        connection = pymysql.connect(**DB_CONFIG)

        with connection.cursor() as cursor:
            # SQL запрос для выборки данных
            query = """SELECT id, title, summary, text FROM news WHERE refactoredText is null;"""

            cursor.execute(query)

            # Получаем все строки
            news_records = cursor.fetchall()

            for record in news_records:
                print(f"Начало обработки новости {record['id']}")
                all_text = record['title'] + "\n" + record['summary'] + "\n" + record['text']
                response = process_one_news(all_text, promt=promt, max_tokens=max_tokens_per_request,
                                            temperature=temperature)
                soup = BeautifulSoup(response, 'html.parser')
                header = soup.find('header').get_text(strip=True)
                news = soup.find('rewritten').get_text(strip=True).replace("\n\n", "\n").replace("\n\n", "\n").replace(
                    "\n\n", "\n")
                summary = soup.find('summary').get_text(strip=True)
                tags = soup.find('tags').get_text(strip=True).replace("; ", ";")
                #print(header)
                #print(news)
                #print(summary)
                #print(tags)

                # SQL запрос для обновления данных
                update_query = """UPDATE news
                SET refactoredTitle = %s,
                    refactoredText = %s,
                    resume = %s,
                    tags = %s
                WHERE id = %s;"""
                cursor.execute(update_query, (header, news, summary, tags, record['id']))
                connection.commit()

            if len(news_records) > 0:
                return True
            else:
                None
    except Error as e:
        print("Ошибка при работе с MySQL:", e)
    finally:
        # Закрываем соединение
        if connection and connection.open:
            connection.close()
            print("Соединение с MySQL закрыто")

    # Обработка таблицы news_posts
    try:
        # Подключение к базе данных
        connection = pymysql.connect(**DB_CONFIG)

        with connection.cursor() as cursor:
            # SQL запрос для выборки данных
            query = """SELECT id, title, content FROM news_posts WHERE refactoredText is null;"""

            cursor.execute(query)

            # Получаем все строки
            news_records = cursor.fetchall()

            for record in news_records:
                print(f"Начало обработки новости {record['id']}")
                all_text = record['title'] + "\n" + record['content']
                response = process_one_news(all_text, promt=promt, max_tokens=max_tokens_per_request,
                                            temperature=temperature)
                soup = BeautifulSoup(response, 'html.parser')
                header = soup.find('header').get_text(strip=True)
                news = soup.find('rewritten').get_text(strip=True).replace("\n\n", "\n").replace("\n\n", "\n").replace(
                    "\n\n", "\n")
                summary = soup.find('summary').get_text(strip=True)
                tags = soup.find('tags').get_text(strip=True).replace("; ", ";")
                #print(header)
                #print(news)
                #print(summary)
                #print(tags)

                # SQL запрос для обновления данных
                update_query = """UPDATE news_posts
                SET refactoredTitle = %s,
                    refactoredText = %s,
                    resume = %s,
                    tags = %s
                WHERE id = %s;"""
                cursor.execute(update_query, (header, news, summary, tags, record['id']))
                connection.commit()

            if len(news_records) > 0:
                return True
            else:
                return False
    except Error as e:
        print("Ошибка при работе с MySQL:", e)
    finally:
        # Закрываем соединение
        if connection and connection.open:
            connection.close()
            print("Соединение с MySQL закрыто")


if __name__ == "__main__":
    max_tokens_per_request = MODEL_CONFIG['max_tokens_per_request']
    temperature = MODEL_CONFIG['temperature']
    promt = get_text_from_txt(PROMPT_FILE)

    # Запуск бесконечного цикла запросов на обработку новостей
    while True:
        do_pause = not update_news_in_db(promt=promt, max_tokens_per_request=max_tokens_per_request, temperature=temperature)
        if do_pause:  # Если не нашлось новостей, то отдыхаем минуту
            print("Спим")
            sleep(60)