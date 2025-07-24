import os
import re
import requests
import time
import urllib3
from bs4 import BeautifulSoup
from sqlalchemy.orm import sessionmaker
from models.Posts import NewsPost, init_db

DB_URL = os.getenv('DB_URL', 'mysql+pymysql://user:password@localhost/news_db')
CHECK_INTERVAL = os.getenv('CHECK_INTERVAL', 60)


class NewsParser:
    def __init__(self):
        urllib3.disable_warnings()
        self.engine = init_db(DB_URL)
        self.Session = sessionmaker(bind=self.engine)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
        }

    def get_or_create_news(self, session, title, url, content, source, source_type='site'):
        existing_news = session.query(NewsPost).filter(NewsPost.url == url).first()
        if existing_news:
            return False

        news = NewsPost(
            title=title,
            url=url,
            content=content,
            source=source,
            source_type=source_type,
        )
        session.add(news)
        session.commit()
        return True

    def parse_sledcom_page(self, session):
        url = 'https://volgograd.sledcom.ru/'
        try:
            response = requests.get(url, verify=False, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            latest_news_block = soup.find('div', class_='bl-item clearfix')
            if latest_news_block:
                titles = latest_news_block.find_all('a')
                title = titles[1].text.strip()
                news_url = 'https://volgograd.sledcom.ru' + titles[1]['href']
                content = self.parse_sledcom_content(news_url)

                if self.get_or_create_news(session, title, news_url, content, 'sledcom', 'site'):
                    print(f"[SLEDCOM] Добавлена новая новость: {title}.")
                else:
                    print("[SLEDCOM] Новых новостей нет.")

        except Exception as e:
            print(f"[SLEDCOM] Ошибка при парсинге: {e}.")

    def parse_sledcom_content(self, url):
        try:
            response = requests.get(url, verify=False, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            article = soup.find('article')
            paragraphs = article.find_all('p')
            return ' '.join(p.get_text(strip=True) for p in paragraphs)
        except:
            return ""

    def parse_mvd_page(self, session):
        url = 'https://34.xn--b1aew.xn--p1ai/новости'
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            latest_news_block = soup.find('div', class_='sl-item-title')
            if latest_news_block:
                title = latest_news_block.find('a').text.strip()
                news_url = 'https://34.xn--b1aew.xn--p1ai' + latest_news_block.find('a')['href']
                content = self.parse_mvd_content(news_url)

                if self.get_or_create_news(session, title, news_url, content, 'mvd', 'site'):
                    print(f"[MVD] Добавлена новая новость: {title}.")
                else:
                    print("[MVD] Новых новостей нет.")

        except Exception as e:
            print(f"[MVD] Ошибка при парсинге: {e}.")

    def parse_mvd_content(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            article = soup.find('div', class_='article')
            paragraphs = article.find_all('p')
            return ' '.join(p.get_text(strip=True) for p in paragraphs)
        except:
            return ""

    def parse_volgadmin_page(self, session):
        url = 'https://www.volgadmin.ru/d/list/news/admvlg'
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            latest_news_block = soup.find('div', class_='news_item')
            if latest_news_block:
                titles = latest_news_block.find_all('a')
                title = titles[1].text.strip()
                news_url = 'https://www.volgadmin.ru/d' + titles[1]['href']
                content = self.parse_volgadmin_content(news_url)

                if self.get_or_create_news(session, title, news_url, content, 'volgadmin', 'site'):
                    print(f"[VOLGADMIN] Добавлена новая новость: {title}.")
                else:
                    print("[VOLGADMIN] Новых новостей нет.")

        except Exception as e:
            print(f"[VOLGADMIN] Ошибка при парсинге: {e}.")

    def parse_volgadmin_content(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            article = soup.find('div', class_='rightcol')
            paragraphs = article.find_all('p')
            return ' '.join(p.get_text(strip=True) for p in paragraphs)
        except:
            return ""

    def parse_volgograd_news_page(self, session):
        url = 'https://www.volgograd.ru/news/'
        try:
            response = requests.get(url, headers=self.headers, verify=False)
            soup = BeautifulSoup(response.text, 'html.parser')

            latest_news_block = soup.find('div', class_='col-md-12 news-item')
            if latest_news_block:
                title = latest_news_block.find('a').text.strip()
                news_url = 'https://www.volgograd.ru' + latest_news_block.find('a')['href']
                content = self.parse_volgograd_news_content(news_url)

                if self.get_or_create_news(session, title, news_url, content, 'volgograd.ru', 'site'):
                    print(f"[VOLGOGRAD.RU] Добавлена новая новость: {title}.")
                else:
                    print("[VOLGOGRAD.RU] Новых новостей нет.")

        except Exception as e:
            print(f"[VOLGOGRAD.RU] Ошибка при парсинге: {e}.")

    def parse_volgograd_news_content(self, url):
        try:
            response = requests.get(url, headers=self.headers, verify=False)
            soup = BeautifulSoup(response.text, 'html.parser')
            article = soup.find('div', class_='news-detail')
            paragraphs = article.find_all('p')
            return ' '.join(p.get_text(strip=True) for p in paragraphs)
        except:
            return ""

    def parse_genproc_page(self, session):
        url = 'https://epp.genproc.gov.ru/web/proc_34'
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            latest_news_block = soup.find('div', class_='feeds-main-page-portlet__list_item')
            if latest_news_block:
                title = latest_news_block.find('a', class_='feeds-main-page-portlet__list_text').text.strip()
                news_url = latest_news_block.find('a', class_='feeds-main-page-portlet__list_text')['href']
                content = self.parse_genproc_content(news_url)

                if self.get_or_create_news(session, title, news_url, content, 'genproc', 'site'):
                    print(f"[GENPROC] Добавлена новая новость: {title}.")
                else:
                    print("[GENPROC] Новых новостей нет.")

        except Exception as e:
            print(f"[GENPROC] Ошибка при парсинге: {e}.")

    def parse_genproc_content(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            article_text = soup.find('div', class_='feeds-page__article_text')
            paragraphs = article_text.find_all('p')
            return ' '.join(p.get_text(strip=True) for p in paragraphs)
        except:
            return ""

    def parse_vesti_page(self, session):
        url = 'https://www.vesti.ru/search?q=волгоград&type=news&sort=date'
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            latest_news_block = soup.find('div', class_='list__item')
            if latest_news_block:
                title = latest_news_block.find('h3', class_='list__title').text.strip()
                news_url = 'https://www.vesti.ru' + latest_news_block.find('a', href=True)['href']
                content = self.parse_vesti_content(news_url)

                if self.get_or_create_news(session, title, news_url, content, 'vesti', 'site'):
                    print(f"[VESTI] Добавлена новая новость: {title}.")
                else:
                    print("[VESTI] Новых новостей нет.")

        except Exception as e:
            print(f"[VESTI] Ошибка при парсинге: {e}.")

    def parse_vesti_content(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            article = soup.find('div', class_='js-mediator-article')
            paragraphs = article.find_all('p')
            return ' '.join(p.get_text(strip=True) for p in paragraphs)
        except:
            return ""

    def parse_tass_page(self, session):
        url = 'https://tass.ru/tag/volgogradskaya-oblast'
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            latest_news_block = soup.find('a', class_='tass_pkg_link-v5WdK')
            if not latest_news_block:
                print("[TASS] Новостей не найдено")
                return

            title_element = latest_news_block.find('span', class_='tass_pkg_title-xVUT1')
            if not title_element:
                print("[TASS] Не удалось извлечь заголовок")
                return

            title = title_element.text.strip()
            news_url = 'https://tass.ru' + latest_news_block['href']

            raw_content = self.parse_tass_content(news_url)
            if not raw_content:
                print("[TASS] Не удалось получить контент новости")
                return

            cleaned_content = self.clean_tass_text(raw_content)

            if self.get_or_create_news(session, title, news_url, cleaned_content, 'tass', 'site'):
                print(f"[TASS] Добавлена новость: {title}")
            else:
                print("[TASS] Новых новостей нет.")

        except requests.exceptions.RequestException as e:
            print(f"[TASS] Ошибка сети: {e}")
        except Exception as e:
            print(f"[TASS] Ошибка парсинга: {e}")

    def parse_tass_content(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            article = soup.find('article')
            if not article:
                return ""

            paragraphs = article.find_all('p')
            content = '\n'.join(p.get_text(strip=True) for p in paragraphs if p.text.strip())

            return content if content else ""

        except requests.exceptions.RequestException as e:
            print(f"[TASS] Ошибка загрузки контента: {e}")
            return ""
        except Exception as e:
            print(f"[TASS] Ошибка обработки контента: {e}")
            return ""

    def clean_tass_text(self, text):
        patterns = [
            r"^[А-ЯЁ]+, \d{1,2} [а-яё]+\. /ТАСС/\.",
            r"^[А-ЯЁ]+, \d{1,2} [а-яё]+\. — /ТАСС/",
            r"^/ТАСС/\.",
        ]

        if not text:
            return text

        for pattern in patterns:
            text = re.sub(pattern, "", text).strip()

        return text

    def run(self):
        session = self.Session()
        print(f"Парсер новостных сайтов запущен. Ожидание новых записей.\nИспользуйте Ctrl+C для остановки.")
        try:
            i = 0
            while True:
                i += 1
                print(f"Итерация {i}:")
                self.parse_sledcom_page(session)
                self.parse_mvd_page(session)
                self.parse_volgadmin_page(session)
                self.parse_volgograd_news_page(session)
                self.parse_genproc_page(session)
                self.parse_vesti_page(session)
                self.parse_tass_page(session)

                time.sleep(int(CHECK_INTERVAL))
        except KeyboardInterrupt:
            print("Работа парсера завершена.")
        finally:
            session.close()


if __name__ == '__main__':
    parser = NewsParser()
    parser.run()
