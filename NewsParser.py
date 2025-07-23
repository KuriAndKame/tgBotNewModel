import os
import requests
import time
import urllib3
from bs4 import BeautifulSoup
from sqlalchemy.orm import sessionmaker
from models.Posts import NewsPost, init_db

DB_URL = os.getenv('DB_URL', 'mysql+pymysql://user:password@localhost/news_db')
CHECK_INTERVAL = os.getenv('CHECK_INTERVAL', 60)

urllib3.disable_warnings()
engine = init_db(DB_URL)
Session = sessionmaker(bind=engine)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
}


def get_or_create_news(session, title, url, content, source, source_type='site'):
    existing_news = session.query(NewsPost).filter(NewsPost.url == url).first()
    if existing_news:
        return False

    news = NewsPost(
        title=title,
        url=url,
        content=content,
        source=source,
        source_type=source_type,
        is_parsed=False
    )
    session.add(news)
    session.commit()
    return True


def parse_sledcom_page(session):
    url = 'https://volgograd.sledcom.ru/'
    try:
        response = requests.get(url, verify=False, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        latest_news_block = soup.find('div', class_='bl-item clearfix')
        if latest_news_block:
            titles = latest_news_block.find_all('a')
            title = titles[1].text.strip()
            news_url = 'https://volgograd.sledcom.ru' + titles[1]['href']
            content = parse_sledcom_content(news_url)

            if get_or_create_news(session, title, news_url, content, 'sledcom', 'site'):
                print(f"[SLEDCOM] Добавлена новая новость: {title}.")
            else:
                print("[SLEDCOM] Новых новостей нет.")

    except Exception as e:
        print(f"[SLEDCOM] Ошибка при парсинге: {e}.")


def parse_sledcom_content(url):
    try:
        response = requests.get(url, verify=False, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        article = soup.find('article')
        paragraphs = article.find_all('p')
        return ' '.join(p.get_text(strip=True) for p in paragraphs)
    except:
        return ""


def parse_mvd_page(session):
    url = 'https://34.xn--b1aew.xn--p1ai/новости'
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        latest_news_block = soup.find('div', class_='sl-item-title')
        if latest_news_block:
            title = latest_news_block.find('a').text.strip()
            news_url = 'https://34.xn--b1aew.xn--p1ai' + latest_news_block.find('a')['href']
            content = parse_mvd_content(news_url)

            if get_or_create_news(session, title, news_url, content, 'mvd', 'site'):
                print(f"[MVD] Добавлена новая новость: {title}.")
            else:
                print("[MVD] Новых новостей нет.")

    except Exception as e:
        print(f"[MVD] Ошибка при парсинге: {e}.")


def parse_mvd_content(url):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        article = soup.find('div', class_='article')
        paragraphs = article.find_all('p')
        return ' '.join(p.get_text(strip=True) for p in paragraphs)
    except:
        return ""


def parse_volgadmin_page(session):
    url = 'https://www.volgadmin.ru/d/list/news/admvlg'
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        latest_news_block = soup.find('div', class_='news_item')
        if latest_news_block:
            titles = latest_news_block.find_all('a')
            title = titles[1].text.strip()
            news_url = 'https://www.volgadmin.ru/d' + titles[1]['href']
            content = parse_volgadmin_content(news_url)

            if get_or_create_news(session, title, news_url, content, 'volgadmin', 'site'):
                print(f"[VOLGADMIN] Добавлена новая новость: {title}.")
            else:
                print("[VOLGADMIN] Новых новостей нет.")

    except Exception as e:
        print(f"[VOLGADMIN] Ошибка при парсинге: {e}.")


def parse_volgadmin_content(url):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        article = soup.find('div', class_='rightcol')
        paragraphs = article.find_all('p')
        return ' '.join(p.get_text(strip=True) for p in paragraphs)
    except:
        return ""


def parse_volgograd_news_page(session):
    url = 'https://www.volgograd.ru/news/'
    try:
        response = requests.get(url, headers=headers, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')

        latest_news_block = soup.find('div', class_='col-md-12 news-item')
        if latest_news_block:
            title = latest_news_block.find('a').text.strip()
            news_url = 'https://www.volgograd.ru' + latest_news_block.find('a')['href']
            content = parse_volgograd_news_content(news_url)

            if get_or_create_news(session, title, news_url, content, 'volgograd.ru', 'site'):
                print(f"[VOLGOGRAD.RU] Добавлена новая новость: {title}.")
            else:
                print("[VOLGOGRAD.RU] Новых новостей нет.")

    except Exception as e:
        print(f"[VOLGOGRAD.RU] Ошибка при парсинге: {e}.")


def parse_volgograd_news_content(url):
    try:
        response = requests.get(url, headers=headers, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        article = soup.find('div', class_='news-detail')
        paragraphs = article.find_all('p')
        return ' '.join(p.get_text(strip=True) for p in paragraphs)
    except:
        return ""


def parse_genproc_page(session):
    url = 'https://epp.genproc.gov.ru/web/proc_34'
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        latest_news_block = soup.find('div', class_='feeds-main-page-portlet__list_item')
        if latest_news_block:
            title = latest_news_block.find('a', class_='feeds-main-page-portlet__list_text').text.strip()
            news_url = latest_news_block.find('a', class_='feeds-main-page-portlet__list_text')['href']
            content = parse_genproc_content(news_url)

            if get_or_create_news(session, title, news_url, content, 'genproc', 'site'):
                print(f"[GENPROC] Добавлена новая новость: {title}.")
            else:
                print("[GENPROC] Новых новостей нет.")

    except Exception as e:
        print(f"[GENPROC] Ошибка при парсинге: {e}.")


def parse_genproc_content(url):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        article_text = soup.find('div', class_='feeds-page__article_text')
        paragraphs = article_text.find_all('p')
        return ' '.join(p.get_text(strip=True) for p in paragraphs)
    except:
        return ""


def parse_vesti_page(session):
    url = 'https://www.vesti.ru/search?q=волгоград&type=news&sort=date'
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        latest_news_block = soup.find('div', class_='list__item')
        if latest_news_block:
            title = latest_news_block.find('h3', class_='list__title').text.strip()
            news_url = 'https://www.vesti.ru' + latest_news_block.find('a', href=True)['href']
            content = parse_vesti_content(news_url)

            if get_or_create_news(session, title, news_url, content, 'vesti', 'site'):
                print(f"[VESTI] Добавлена новая новость: {title}.")
            else:
                print("[VESTI] Новых новостей нет.")

    except Exception as e:
        print(f"[VESTI] Ошибка при парсинге: {e}.")


def parse_vesti_content(url):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        article = soup.find('div', class_='js-mediator-article')
        paragraphs = article.find_all('p')
        return ' '.join(p.get_text(strip=True) for p in paragraphs)
    except:
        return ""


if __name__ == '__main__':
    session = Session()
    print(f"Парсер новостных сайтов запущен. Ожидание новых записей.\nИспользуйте Ctrl+C для остановки.")
    try:
        i = 0
        while True:
            i += 1
            print(f"Итерация {i}:")
            parse_sledcom_page(session)
            parse_mvd_page(session)
            parse_volgadmin_page(session)
            parse_volgograd_news_page(session)
            parse_genproc_page(session)
            parse_vesti_page(session)
            time.sleep(int(CHECK_INTERVAL))
    except KeyboardInterrupt:
        print("Работа парсера завершена.")
    finally:
        session.close()
