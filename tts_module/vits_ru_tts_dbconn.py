from transformers import VitsModel, AutoTokenizer, set_seed
import torch
import scipy
from ruaccent import RUAccent
import os
import time
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import re

# ========== НАСТРОЙКИ ========== #
OUTPUT_DIR = "output_audio"  # Папка для аудиофайлов
DEVICE = 'cpu'  # 'cpu' or 'cuda'
SPEAKER = 0  # 0 - женский, 1 - мужской
CHECK_INTERVAL = 5  # Проверять новые записи каждые N секунд

# Настройки базы данных
DATABASE_URL = "mysql+mysqlconnector://username:password@localhost/database_name"
# =============================== #

Base = declarative_base()


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_msg_id = Column(Integer, nullable=False)
    source = Column(String(255), nullable=False)
    date = Column(DateTime, nullable=False)
    title = Column(String(255))
    summary = Column(Text)
    text = Column(Text)
    media_file = Column(Text)
    refactoredTitle = Column(String(255))
    refactoredText = Column(Text)
    resume = Column(Text)
    tags = Column(String(255))


def clean_filename(filename):
    """Очищает строку для использования в имени файла"""
    return re.sub(r'[\\/*?:"<>|]', "_", filename)


# Инициализация базы данных
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Создаем папку для аудио, если ее нет
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Настройка путей к моделям
os.environ["RUACCENT_CACHE_DIR"] = "./ruaccent_models"
os.environ["TRANSFORMERS_CACHE"] = "./transformers_models"

# Загрузка моделей
set_seed(555)  # Фиксируем сид для воспроизводимости

print("Загружаю TTS модель...")
model = VitsModel.from_pretrained("./local_tts_model").to(DEVICE)
tokenizer = AutoTokenizer.from_pretrained("./local_tts_model")
model.eval()

print("Загружаю акцентуатор...")
accentizer = RUAccent()
accentizer.load(omograph_model_size='turbo', use_dictionary=True, device=DEVICE)


def get_unprocessed_news(session):
    """Получает необработанные новости из базы данных"""
    try:
        # Ищем записи с refactoredText, но без media_file
        query = session.query(News).filter(
            News.refactoredText.isnot(None),
            News.refactoredText != '',
            News.media_file.is_(None)
        )
        return query.all()
    except Exception as e:
        print(f"Ошибка при получении новостей: {e}")
        return []


def process_news_item(news_item):
    """Обрабатывает одну новость и создает аудиофайл"""
    try:
        text = news_item.refactoredText.strip()
        if not text:
            print(f"Новость ID {news_item.id} имеет пустой refactoredText, пропускаю")
            return False

        # Обработка текста
        processed_text = accentizer.process_all(text)

        # Синтез речи
        inputs = tokenizer(processed_text, return_tensors="pt")

        with torch.no_grad():
            output = model(**inputs.to(DEVICE), speaker_id=SPEAKER).waveform
            output = output.detach().cpu().numpy()

        # Генерация имени файла
        if news_item.refactoredTitle:
            base_name = clean_filename(news_item.refactoredTitle)[:50]
            audio_filename = f"{base_name}_{news_item.id}.wav"
        else:
            audio_filename = f"news_{news_item.id}.wav"

        output_path = os.path.join(OUTPUT_DIR, audio_filename)

        # Сохраняем аудио
        scipy.io.wavfile.write(output_path, rate=model.config.sampling_rate, data=output[0])
        print(f"Аудио сохранено как: {output_path}")

        return True

    except Exception as e:
        print(f"Ошибка при обработке новости ID {news_item.id}: {str(e)}")
        return False


def main_loop():
    """Основной цикл обработки"""
    processed_ids = set()
    session = Session()

    print(f"\nСлужба TTS запущена. Проверяю базу данных каждые {CHECK_INTERVAL} сек...")
    print(f"Готовые аудиофайлы сохраняются в '{OUTPUT_DIR}'")
    print("Для остановки нажмите Ctrl+C\n")

    try:
        while True:
            try:
                # Получаем необработанные новости
                unprocessed_news = get_unprocessed_news(session)

                for news_item in unprocessed_news:
                    if news_item.id not in processed_ids:
                        if process_news_item(news_item):
                            processed_ids.add(news_item.id)

                time.sleep(CHECK_INTERVAL)

            except Exception as e:
                print(f"Ошибка в основном цикле: {e}")
                time.sleep(10)  # Пауза при ошибке

    except KeyboardInterrupt:
        print("\nОстановлено пользователем")
    finally:
        session.close()


if __name__ == "__main__":
    main_loop()