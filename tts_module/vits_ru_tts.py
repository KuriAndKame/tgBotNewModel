from transformers import VitsModel, AutoTokenizer, set_seed
import torch
import scipy
from ruaccent import RUAccent
import os
import time
from pathlib import Path

# ========== НАСТРОЙКИ ========== #
INPUT_DIR = "input_txt"  # Папка с текстовыми файлами
OUTPUT_DIR = "output_audio"  # Папка для аудиофайлов
DEVICE = 'cpu'  # 'cpu' or 'cuda'
SPEAKER = 0  # 0 - женский, 1 - мужской
CHECK_INTERVAL = 5  # Проверять новые файлы каждые N секунд
# =============================== #

# Создаем папки, если их нет
os.makedirs(INPUT_DIR, exist_ok=True)
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


def process_file(txt_path):
    """Обрабатывает один текстовый файл"""
    try:
        # Читаем текст из файла
        with open(txt_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()

        if not text:
            print(f"Файл {txt_path} пуст, пропускаю")
            return False



        # Обработка текста
        text = accentizer.process_all(text)


        # Синтез речи
        inputs = tokenizer(text, return_tensors="pt")

        with torch.no_grad():
            output = model(**inputs.to(DEVICE), speaker_id=SPEAKER).waveform
            output = output.detach().cpu().numpy()

        # Сохраняем аудио
        base_name = os.path.splitext(os.path.basename(txt_path))[0]
        output_path = os.path.join(OUTPUT_DIR, f"{base_name}.wav")

        scipy.io.wavfile.write(output_path, rate=model.config.sampling_rate, data=output[0])
        print(f"Аудио сохранено как: {output_path}")

        return True

    except Exception as e:
        print(f"Ошибка при обработке файла {txt_path}: {str(e)}")
        return False


def main_loop():
    """Основной цикл обработки"""
    processed_files = set()

    print(f"\nСлужба TTS запущена. Проверяю папку '{INPUT_DIR}' каждые {CHECK_INTERVAL} сек...")
    print(f"Готовые аудиофайлы сохраняются в '{OUTPUT_DIR}'")
    print("Для остановки нажмите Ctrl+C\n")

    try:
        while True:
            # Получаем список txt-файлов
            txt_files = list(Path(INPUT_DIR).glob("*.txt"))

            for txt_file in txt_files:
                if str(txt_file) not in processed_files:
                    if process_file(str(txt_file)):
                        processed_files.add(str(txt_file))

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\nОстановлено пользователем")


if __name__ == "__main__":
    main_loop()