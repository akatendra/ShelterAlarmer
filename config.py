import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем значения
TELEGRAM_BOT_API_TOKEN = os.getenv('TELEGRAM_BOT_API_TOKEN')
TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID'))  # Преобразуем API_ID в число, так как он должен быть integer
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')

ALERT_GROUP_ID = int(os.getenv("ALERT_GROUP_ID"))  # ✅ Супергруппа, в которую будем писать сообщения об тревогах для Заводского района
MY_CHAT_ID = int(os.getenv('MY_CHAT_ID')) # Кому посылаются сообщения о том, что бот работает

# Исключенные из рассылки пользователи
EXCLUDED_USERS = [user.strip() for user in os.getenv("EXCLUDED_USERS", "").split(",") if user]


# Проверяем, что значения загружены
if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
    raise ValueError("Не найдены TELEGRAM_API_ID или TELEGRAM_API_HASH в файле .env")
