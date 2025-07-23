import asyncio

from telethon import TelegramClient, events
from config import TELEGRAM_BOT_API_TOKEN, TELEGRAM_API_ID, TELEGRAM_API_HASH


# Создаем TelegramClient (название сессии + api_id и api_hash можно быть любыми, не используются при токене)
bot = TelegramClient(
    "bot_session",
    api_id=TELEGRAM_API_ID,
    api_hash=TELEGRAM_API_HASH
)

@bot.on(events.NewMessage)
async def handler(event):
    sender = await event.get_sender()
    chat_id = event.chat_id
    name = getattr(sender, 'first_name', '❓')

    print(f"📨 Сообщение от {name} (chat_id: {chat_id})")
    await event.reply(f"👋 Привет, {name}!\nТвой chat_id: `{chat_id}`")

async def main():
    await bot.start(bot_token=TELEGRAM_BOT_API_TOKEN)
    print("✅ Бот запущен. Напиши ему что-нибудь в Telegram.")
    await bot.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⛔ Завершено пользователем")
