import requests
from time import time, sleep
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error


def get_text_from_txt(filename):
    text = ""
    with open(filename, encoding="utf-8") as file:
        for line in file:
            text += line
    return text

def text_to_file(text, filename):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(text)

def chat_with_model(messages, temperature=0.7, max_tokens=6000):
    url = "http://localhost:1234/v1/chat/completions"
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

def process_one_news(text, promt, max_tokens, temperature=0.7):
    try:
        history = [
            {"role": "system", "content": promt},
            {"role": "user", "content": text}
        ]
        response = chat_with_model(history, temperature, max_tokens)
        return response
    except Exception as e:
        return f"Ошибка при обработке запроса: {e}"

def update_news_in_db(promt, max_tokens_per_request, temperature):
    try:
        # Подключение к базе данных (желательно вынескти в файл конфигураций)
        connection = mysql.connector.connect(
            host='localhost',
            database='news_db',
            user='user',
            password='password'
        )

        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)

            # SQL запрос для выборки данных
            query = """SELECT id, title, summary, text FROM news WHERE refactoredText is null;"""
            
            cursor.execute(query)
            
            # Получаем все строки
            news_records = cursor.fetchall()
            
            for record in news_records:
                print(f"Начало обработки новости {record["id"]}")
                all_text = record['title'] + "\n" + record['summary'] + "\n" + record['text']
                response = process_one_news(all_text, promt=promt, max_tokens=max_tokens_per_request, temperature=temperature)
                soup = BeautifulSoup(response, 'html.parser')
                header = soup.find('header').get_text(strip=True)
                news = soup.find('rewritten').get_text(strip=True).replace("\n\n", "\n").replace("\n\n", "\n").replace("\n\n", "\n")
                summary = soup.find('summary').get_text(strip=True)
                tags = soup.find('tags').get_text(strip=True).replace("; ", ";")
                print(header)
                print(news)
                print(summary)
                print(tags)

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
                return False

    except Error as e:
        print("Ошибка при работе с MySQL:", e)
    finally:
        # Закрываем соединение
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Соединение с MySQL закрыто")

if __name__ == "__main__":
    max_tokens_per_request = 6000
    temperature = 0.4
    promt = get_text_from_txt("promt.txt")

    # Запуск бесконечного цикла запросов на обработку новостей
    while True:
        do_pause = not update_news_in_db(promt=promt, max_tokens_per_request=max_tokens_per_request, temperature=temperature)
        if do_pause: # Если не нашлось новостей, то отдыхаем минуту
            print("Спим")
            sleep(60)


"""
if __name__ == "__main__":
    start_time = time()

    # Настройки (желательно вынескти в файл конфигураций)
    start_file = 1
    end_file = 1
    max_tokens_per_request = 6000
    temperature = 0.7
    
    promt = get_text_from_txt("promt.txt")
    
    for i in range(start_file, end_file + 1):
        text = get_text_from_txt(f"test{i}.txt")
        response = process_one_news(text, promt=promt, max_tokens=max_tokens_per_request, temperature=temperature)
        soup = BeautifulSoup(response, 'html.parser')
        header = soup.find('header').get_text(strip=True)
        news = soup.find('rewritten').get_text(strip=True).replace("\n\n", "\n").replace("\n\n", "\n").replace("\n\n", "\n")
        summary = soup.find('summary').get_text(strip=True)
        tags = soup.find('tags').get_text(strip=True).replace("; ", ";")

        print("Заголовок:", header)
        print("\nНовость:", news)
        print("\nКраткая выжимка:", summary)
        print("\nТеги:", tags)
        text_to_file(response, f"deepseek_response{i}.txt")

    end_time = time()
    print(f"Все файлы обработаны! Затраченное время: {end_time - start_time}")
"""