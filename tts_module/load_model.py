from transformers import VitsModel, AutoTokenizer
from ruaccent import RUAccent
import os

# Указываем, где хранить модели (чтобы не качать каждый раз)
os.environ["RUACCENT_CACHE_DIR"] = "./ruaccent_models"  # Папка для RUAccent
os.environ["TRANSFORMERS_CACHE"] = "./transformers_models"  # Папка для Hugging Face

# Загружаем модель TTS и сохраняем локально
model_name = "utrobinmv/tts_ru_free_hf_vits_high_multispeaker"
model = VitsModel.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

model.save_pretrained("./local_tts_model")  # Сохраняем модель VitsModel
tokenizer.save_pretrained("./local_tts_model")  # Сохраняем токенизатор

# Загружаем модель акцентуатора (она автоматически сохранится в RUACCENT_CACHE_DIR)
accentizer = RUAccent()
accentizer.load(omograph_model_size='turbo', use_dictionary=True)
print("Модели успешно загружены и сохранены локально!")
