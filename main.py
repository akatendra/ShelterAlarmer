"""
Чтобы работал getpass() пускать из терминала командой:
python main.py

 Доступные чаты, группы и каналы:
 КОРАБЕЛИ — ID: -1002123586827

 ПН | Преступности.НЕТ — ID: -1001144849043
################################################################################
 Вариант 1: Просто запустить через PowerShell

Открой PowerShell (Windows + R → powershell) и бахни:

python "G:\Python_projects\Shelter_Alarmer\main.py"

Что произойдёт:

    Скрипт запустится и будет работать, пока окно не закроешь или не словишь ошибку/вылет.

 Вариант 2: Запуск с логом и фоновым режимом

Если хочешь пустить в фоне и видеть логи, то делаем так:

Start-Process powershell -ArgumentList "python 'G:\Python_projects\Shelter_Alarmer\main.py'" -NoNewWindow

Или если хочешь писать всё в лог:

python "G:\Python_projects\Shelter_Alarmer\main.py" > G:\Python_projects\Shelter_Alarmer\output.log 2>&1

 Вариант 3: Автозапуск при старте системы (по-взрослому)

    Создай .bat файл, например run_trivoga.bat:

@echo off
python "G:\Python_projects\Shelter_Alarmer\main.py"

    Кинь его в автозагрузку:

shell:startup

(да, прямо вставь в адресную строку Проводника)
 Подсказка:

Если хочешь закрыть скрипт — в PowerShell жми Ctrl+C.
Но если всё запускается в фоне, придётся убить процесс python.exe — руками или через Task Manager.

################################################################################
 Как запустить бот правильно (ручной запуск)
1. Подключись к серверу:

ssh root@IP_СЕРВЕРА

2. Перейди в папку проекта:

cd /opt/zavodskij_alarmer

3. Активируй виртуальное окружение:

source venv/bin/activate

Терминал станет таким:

(venv) root@yourserver:/opt/zavodskij_alarmer#

4. Запусти скрипт:

python main.py

5. Просто выйди из venv, если ты в нём:
deactivate
################################################################################
 Минимальный набор команд для запуска в фоне без логов:

cd /opt/zavodskij_alarmer
source venv/bin/activate
nohup python main.py & disown

 Объяснение:
Команда	Что делает
cd /opt/zavodskij_alarmer	Перейти в папку с ботом
source venv/bin/activate	Активировать виртуальное окружение
nohup python main.py &	Запускает скрипт в фоне, не останавливается при выходе
disown (дополнительно)	Отвязывает процесс от текущего сеанса SSH (опционально)
Если хочешь вообще ничего не писать в файл, можешь перенаправить в "никуда":

nohup python main.py > /dev/null 2>&1 &

 Проверка: работает ли бот?

    Посмотри список фоновых процессов:

ps aux | grep python

Убедись, что бот работает:

    Он присылает сообщения в Telegram-группу?

    Никаких ошибок нет?

################################################################################
 1. Как остановить работающий бот
Шаг 1. Найди процесс:

ps aux | grep python

Ты увидишь что-то вроде:

root     12345  0.1  ... python main.py

Где 12345 — это PID (номер процесса)
Шаг 2. Убей процесс:

kill 12345

Если не сработает (редко), используй жёстко:

kill -9 12345

 2. Как перезапустить

cd /opt/zavodskij_alarmer
source venv/bin/activate
nohup python main.py > /dev/null 2>&1 &

(либо в лог, если хочешь: > log.txt 2>&1 &)
 3. Как сделать alias — запуск одной короткой командой
Шаг 1. Открой .bashrc:

nano ~/.bashrc

Шаг 2. В самый низ добавь:

alias startbot='cd /opt/zavodskij_alarmer && source venv/bin/activate && nohup python main.py > /dev/null 2>&1 &'
alias stopbot="ps aux | grep 'python main.py' | grep -v grep | awk '{print \$2}' | xargs kill"

Шаг 3. Применить изменения:

source ~/.bashrc

 Теперь ты можешь использовать:
Команда	Что делает
startbot	Запускает бота в фоне
stopbot	Убивает процесс с ботом

################################################################################
 Команды управления ботом:

Команды:
Перезапуск (если изменил код):
systemctl restart zavodskij_alarmer
Остановить бота:
systemctl stop zavodskij_alarmer
Запустить снова:
systemctl start zavodskij_alarmer
Посмотреть статус:
systemctl status zavodskij_alarmer

Смотреть вывод systemd в реальном времени (Когда сервис был запущен / Когда остановлен).
Выводит живой лог (в реальном времени) от systemd-сервиса zavodskij_alarmer.
journalctl -u zavodskij_alarmer -f

Если у тебя включён лог в файл
tail -f /opt/zavodskij_alarmer/worklog.log

"""
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from telethon import TelegramClient, events, errors
from config import TELEGRAM_BOT_API_TOKEN, TELEGRAM_API_ID, TELEGRAM_API_HASH, PHONE_NUMBER, ALERT_GROUP_ID, MY_CHAT_ID
from getpass import getpass
import asyncio
from collections import defaultdict

# Set up logging
import logging.config

logging.config.fileConfig("logging.ini", disable_existing_loggers=False)
logger = logging.getLogger(__name__)
logging.getLogger('telethon').setLevel(logging.WARNING)

SESSION_NAME = "zavodskij_listener"
BOT_SESSION_NAME = "alertbot"

# Канал откуда берем информацию об атаке на Заводский район
MONITORING_CHANNELL_ID = -1002123586827
MONITORING_CHANNEL_NAME = 'КОРАБЕЛИ'  # For reference
# MONITORING_CHANNELL_ID = -1001144849043  # ПН | Преступности.НЕТ | Для проверки

async def init_client():
    try:
        logger.info("Creating Telegram client...")
        client = TelegramClient(SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)

        logger.info("Connecting to Telegram...")
        await client.connect()

        if not await client.is_user_authorized():
            logger.info("Not authorized, requesting code...")
            await client.send_code_request(PHONE_NUMBER)

            code = input("Enter the code from Telegram: ").strip()
            if not code:
                raise ValueError("Code can't be empty!")

            try:
                await client.sign_in(PHONE_NUMBER, code)
            except errors.SessionPasswordNeededError:
                password = getpass("2FA enabled. Enter your password: ").strip()
                if not password:
                    raise ValueError("Password can't be empty!")
                await client.sign_in(password=password)

        logger.info("Authorization successful ")
        me = await client.get_me()
        logger.info(f"Logged in as {me.first_name} (@{me.username or me.phone})")

        return client

    except errors.PhoneCodeInvalidError:
        logger.error(" Invalid code entered!")
        raise
    except errors.PasswordHashInvalidError:
        logger.error(" Invalid 2FA password!")
        raise
    except Exception as e:
        logger.error(f" Unexpected error: {e}")
        raise


async def init_bot():
    try:
        logger.info("Creating Telegram bot client...")
        bot = TelegramClient(BOT_SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)

        logger.info("Starting bot...")
        await bot.start(bot_token=TELEGRAM_BOT_API_TOKEN)

        logger.info("Bot client connected ")
        return bot

    except Exception as e:
        logger.error(f" Unexpected error: {e}")
        raise


async def heartbeat(bot, chat_id):
    while True:
        # Используем киевское время для heartbeat (автоматический учет летнего/зимнего времени)
        kyiv_tz = ZoneInfo('Europe/Kyiv')
        now = datetime.now(kyiv_tz).strftime("%d-%m-%Y | %H:%M:%S")
        msg = f"🟢 {now} — Бот на службе (Киевское время)"
        await bot.send_message(chat_id, msg)
        await asyncio.sleep(3600)  # раз в час


async def get_group_name(client, group_id):
    try:
        group = await client.get_entity(group_id)
        return group.title
    except Exception as e:
        logger.error(f"Не удалось получить имя группы: {e}")
        return "Неизвестно"


async def list_groups(client):
    """
    Дает список доступных чатов, на которые подписан реципиент
    :param client:
    :return:
    """
    logger.info("#" * 120)
    logger.info("\n Доступные чаты, группы и каналы:\n")

    # Асинхронный итератор — работаем с ним через async for
    async for dialog in client.iter_dialogs():
        if dialog.is_group or dialog.is_channel:
            logger.info(f" {dialog.name} — ID: {dialog.id}")

    logger.info("\n Детальная информация:\n")

    # Список — обычный for
    for dialog in await client.get_dialogs():
        entity = dialog.entity
        logger.info(f"{dialog.name} — ID: {entity.id} — Type: {type(entity)} — Username: {getattr(entity, 'username', None)}")

    logger.info("#" * 120)


async def monitor_group(client, bot, keywords, monitoring_group_id, excluded_keywords=None, ballistika_keywords=None):
    """
    Функция мониторинга группы на тревожное слово
    :param client:
    :param bot:
    :param keywords:
    :param monitoring_group_id:
    :param excluded_keywords: список исключаемых ключевых слов
    :return:
    """
    
    # Логируем время установки обработчика
    setup_time = datetime.now(ZoneInfo('Europe/Kyiv'))
    logger.info(f"[SETUP] 📡 Устанавливаем обработчик событий в: {setup_time.strftime('%H:%M:%S.%f')[:-3]} (Киевское время)")
    if excluded_keywords is None:
        excluded_keywords = []
    if ballistika_keywords is None:
        ballistika_keywords = []

    album_messages = defaultdict(list)

    @client.on(events.NewMessage(chats=monitoring_group_id))
    async def handler(event):
        # КРИТИЧЕСКИ ВАЖНО: логируем СРАЗУ при входе в обработчик
        entry_time = datetime.now(ZoneInfo('Europe/Kyiv'))
        logger.info(f"[HANDLER_ENTRY] 🚀 ВХОД В ОБРАБОТЧИК: {entry_time.strftime('%H:%M:%S.%f')[:-3]} (Киевское время)")
        
        # Детальное логирование времени для диагностики задержек
        kyiv_tz = ZoneInfo('Europe/Kyiv')  # Автоматический учет летнего/зимнего времени
        handler_start_time = datetime.now(kyiv_tz)
        message = event.message
        
        # Конвертируем UTC время сообщения в киевское время
        message_time_kyiv = message.date.replace(tzinfo=timezone.utc).astimezone(kyiv_tz)
        
        logger.info(f"[TIMING] ⏰ Обработчик запущен в: {handler_start_time.strftime('%H:%M:%S.%f')[:-3]} (Киевское время)")
        logger.info(f"[TIMING] 📅 Время сообщения в Telegram: {message.date} (UTC) = {message_time_kyiv.strftime('%Y-%m-%d %H:%M:%S')} (Киевское время)")
        logger.info(f"[TIMING] ⏱️ Разница: {(handler_start_time - message_time_kyiv).total_seconds():.2f} секунд")

        # Пропускаем служебные сообщения (типа join/leave/etc)
        if not hasattr(message, 'message') and not message.grouped_id:
            logger.info("[DEBUG] Служебное сообщение, игнорируем")
            return

        grouped_id = message.grouped_id

        if grouped_id:
            album_messages[grouped_id].append(message)
            if message.message:  # появился текст — обрабатываем только эту часть
                logger.info(f"[DEBUG] Последнее сообщение в альбоме с текстом. Обрабатываем grouped_id={grouped_id}")
                text = message.message

                if not text.strip():
                    logger.info("[DEBUG] Текст в альбоме пустой, не обрабатываем")
                    return

                # Поиск тревожного слова
                keyword_check_time = datetime.now(kyiv_tz)
                logger.info(f"[TIMING] 🔍 Начало проверки ключевых слов: {keyword_check_time.strftime('%H:%M:%S.%f')[:-3]} (Киевское время)")
                
                alert_triggered = False
                
                if contains_any_keyword(text, keywords):
                    logger.info(f"⚠️ Найдено ключевое слово из списка {keywords} в сообщении (альбом). Проверяем исключения...")
                    alert_triggered = True
                elif ballistika_keywords and contains_all_keywords(text, ballistika_keywords):
                    logger.info(f"⚠️ Найдены ВСЕ ключевые слова {ballistika_keywords} в сообщении (альбом). Проверяем исключения...")
                    alert_triggered = True
                
                if alert_triggered:
                    for excluded_keyword in excluded_keywords:
                        if contains_keyword(text, excluded_keyword):
                            logger.info(f"⚠️ Найдено исключаемое слово '{excluded_keyword}' — тревога не отправляется.")
                            return

                    logger.warning("🔴 ТРИВОГА!!! Отправляем сообщение из альбома!")
                    alert_send_time = datetime.now(kyiv_tz)
                    logger.info(f"[TIMING] 📤 Начало отправки алерта: {alert_send_time.strftime('%H:%M:%S.%f')[:-3]} (Киевское время)")
                    
                    await send_alert(bot, ALERT_GROUP_ID, text)
                    
                    alert_sent_time = datetime.now(kyiv_tz)
                    logger.info(f"[TIMING] ✅ Алерт отправлен: {alert_sent_time.strftime('%H:%M:%S.%f')[:-3]} (Киевское время)")
                    logger.info(f"[TIMING] ⏱️ Время отправки алерта: {(alert_sent_time - alert_send_time).total_seconds():.3f} секунд")
                    logger.info("📨 Тревожное сообщение отправлено")

                # Логируем
                sender = await event.get_sender()
                sender_name = getattr(sender, 'first_name', None) or getattr(sender, 'title', None) or "Unknown"
                logger.info("#" * 120)
                logger.info(f"\n📥 Альбомное сообщение:\n👤 От: {sender_name}\n💬 Сообщение:\n{text}")

                # Очистка буфера
                del album_messages[grouped_id]

        else:
            # Обычное сообщение (не альбом)
            text = message.message or getattr(message, 'text', '')
            if not text.strip():
                logger.info("[DEBUG] Пустое одиночное сообщение, не обрабатываем")
                return

            # Логирование времени для обычных сообщений
            keyword_check_time = datetime.now(kyiv_tz)
            logger.info(f"[TIMING] 🔍 Начало проверки ключевых слов (обычное сообщение): {keyword_check_time.strftime('%H:%M:%S.%f')[:-3]} (Киевское время). Я пишу логи по Киевскому времени. А время в ТГ по UTC, поэтому выше показана корректная разница!")
            
            alert_triggered = False
            
            if contains_any_keyword(text, keywords):
                logger.info(f"⚠️ Найдено ключевое слово из списка {keywords} в обычном сообщении. Проверяем исключения...")
                alert_triggered = True
            elif ballistika_keywords and contains_all_keywords(text, ballistika_keywords):
                logger.info(f"⚠️ Найдены ВСЕ ключевые слова {ballistika_keywords} в обычном сообщении. Проверяем исключения...")
                alert_triggered = True
            
            if alert_triggered:
                for excluded_keyword in excluded_keywords:
                    if contains_keyword(text, excluded_keyword):
                        logger.info(f"⚠️ Найдено исключаемое слово '{excluded_keyword}' — тревога не отправляется.")
                        return

                logger.warning("🔴 ТРИВОГА!!! Отправляем обычное сообщение!")
                alert_send_time = datetime.now(kyiv_tz)
                logger.info(f"[TIMING] 📤 Начало отправки алерта (обычное сообщение): {alert_send_time.strftime('%H:%M:%S.%f')[:-3]} (Киевское время)")
                
                await send_alert(bot, ALERT_GROUP_ID, text)
                
                alert_sent_time = datetime.now(kyiv_tz)
                logger.info(f"[TIMING] ✅ Алерт отправлен (обычное сообщение): {alert_sent_time.strftime('%H:%M:%S.%f')[:-3]} (Киевское время)")
                logger.info(f"[TIMING] ⏱️ Время отправки алерта: {(alert_sent_time - alert_send_time).total_seconds():.3f} секунд")
                logger.info("📨 Тревожное сообщение отправлено")

            # Лог
            sender = await event.get_sender()
            sender_name = getattr(sender, 'first_name', None) or getattr(sender, 'title', None) or "Unknown"
            logger.info("#" * 120)
            logger.info(f"\n📥 Одиночное сообщение:\n👤 От: {sender_name}\n💬 Сообщение:\n{text}")

    monitoring_group_name = await get_group_name(client, monitoring_group_id)
    logger.info(f"\n Слушаем сообщения из группы {monitoring_group_name} с ID {monitoring_group_id}... (нажми Ctrl+C чтобы остановить)")


def contains_keyword(text: str, keyword: str) -> bool:
    return keyword.lower() in text.lower()


def contains_any_keyword(text: str, keywords: list[str]) -> bool:
    """Проверяет, содержит ли текст любое из ключевых слов из списка"""
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


def contains_all_keywords(text: str, keywords: list[str]) -> bool:
    """Проверяет, содержит ли текст ВСЕ ключевые слова из списка"""
    text_lower = text.lower()
    return all(keyword.lower() in text_lower for keyword in keywords)


async def send_alert(bot, alert_group_id, alert_text):
    """
    Отправляет тревожное сообщение в группу.
    """
    text = f"\n\n{alert_text}"
    await bot.send_message(alert_group_id, text, silent=False)


async def main():
    start_time = datetime.now(ZoneInfo('Europe/Kyiv'))
    logger.info(f"[MAIN] 🏁 Запуск основной функции: {start_time.strftime('%H:%M:%S.%f')[:-3]} (Киевское время)")
    
    client = await init_client()
    client_ready_time = datetime.now(ZoneInfo('Europe/Kyiv'))
    logger.info(f"[MAIN] 📱 Клиент готов: {client_ready_time.strftime('%H:%M:%S.%f')[:-3]} (Киевское время)")

    bot = await init_bot()
    bot_ready_time = datetime.now(ZoneInfo('Europe/Kyiv'))
    logger.info(f"[MAIN] 🤖 Бот готов: {bot_ready_time.strftime('%H:%M:%S.%f')[:-3]} (Киевское время)")

    # Тут создаем задачу для периодического пинга
    asyncio.create_task(heartbeat(bot, MY_CHAT_ID))

    # await list_groups(client)  # Список всех доступных чатов

    # Запускаем слушателя
    monitor_start_time = datetime.now(ZoneInfo('Europe/Kyiv'))
    logger.info(f"[MAIN] 👂 Запуск мониторинга: {monitor_start_time.strftime('%H:%M:%S.%f')[:-3]} (Киевское время)")
    await monitor_group(client, bot, KEYWORDS, MONITORING_CHANNELL_ID, EXCLUDED_KEYWORDS, BALLISTIKA_KEYWORDS)

    logger.info(f"[MAIN] 🔄 Переход в режим ожидания событий...")
    await client.run_until_disconnected()


if __name__ == '__main__':
    KEYWORDS = ["заводс", "центральний"]
    EXCLUDED_KEYWORDS = ["кумпол", "нічого нема"]
    BALLISTIKA_KEYWORDS = ["Миколаїв", "балістика"]

    logger.info("Program starting...")

    try:
        asyncio.run(main())

    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        logger.info("Program finished")
