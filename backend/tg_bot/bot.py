from datetime import time, datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import asyncio
import logging
from adapters.auth import login_to_xui
from adapters.inbounds import get_inbound, get_inbounds, add_client, delete_client
from settings import bot_token, domain_xui
from urllib.parse import quote
import json
import keyboards as kb
from utils.vless import generate_vless_url

# Инициализация бота
bot = Bot(token=bot_token)
dp = Dispatcher()



@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        '🔐 Добро пожаловать в VP333N бот!\n\n'
        'Я помогу вам получить доступ к приватному VPN сервису:\n'
        '• 🚀 Генерация персональных VPN-ключей\n'
        '• ⏳ Автоматическое создание подписок\n'
        '• 🔄 Управление вашими подключениями\n'
        '• 📡 Стабильные сервера с высокой скоростью\n\n'
        'Выберите действие:',
        reply_markup=kb.main
    )

@dp.message(lambda message: message.text == '🛒 Купить подписку')
async def subscribes(message: types.Message):
    await message.answer(
        '📅 Выберите срок подписки:\n\n'
        '• 1 месяц - идеально для тестирования\n'
        '• 3 месяца - выгодный вариант\n',
        reply_markup=kb.subscribes
    )


@dp.message(lambda message: message.text == 'Удалить клиента')
async def delete_client_handler(message: types.Message):
    try:
        # 1. Авторизация
        session_cookie = await login_to_xui()
        if not session_cookie:
            await message.answer("Ошибка авторизации в панели XUI")
            return

        # 2. Получаем список inbounds
        inbounds = await get_inbounds(session_cookie)
        if not inbounds.get("obj") or not inbounds["obj"]:
            await message.answer("Нет доступных inbounds")
            return

        # 3. Ищем клиента во всех inbounds
        user_email = f"user_{message.from_user.id}@vp333nbot"
        deleted = False

        for inbound in inbounds["obj"]:
            inbound_id = inbound["id"]
            delete_result = await delete_client(session_cookie, inbound_id, user_email)
            if delete_result.get("success"):
                deleted = True
                break

        if deleted:
            await message.answer("✅ Клиент успешно удалён", reply_markup=kb.main)
        else:
            await message.answer("❌ Клиент не найден или уже удалён", reply_markup=kb.main)

    except Exception as e:
        logging.error(f"Ошибка при удалении клиента: {str(e)}")
        await message.answer("⚠️ Произошла ошибка при удалении клиента", reply_markup=kb.main)

@dp.message(lambda message: message.text == '🔙 Назад')
async def subscribes(message: types.Message):
    await message.answer(
        '⬅️ Возвращаемся в главное меню\n'
        'Выберите нужный раздел:'
        ,
        reply_markup=kb.main
    )

@dp.message(lambda message: message.text == '1 month')
async def subscribes(message: types.Message):
    await message.answer(
        '🎉 Вы выбрали подписку на 1 месяц!\n\n'
        'Скорость: без ограничений\n\n'
        'Нажмите "Сгенерировать ключ" для активации',
        reply_markup=kb.gen
    )

@dp.message(lambda message: message.text == '🔙 Назад к подпискам')
async def subscribes(message: types.Message):
    await message.answer(
        '↩️ Возврат к выбору подписки\n'
        'Какой срок вас интересует?'
        ,
        reply_markup=kb.subscribes
    )


@dp.message(lambda message: message.text == '🕰️ Сколько осталось до окончания подписки')
async def check_subscription(message: types.Message):

    session_cookie = await login_to_xui()
    if not session_cookie:
        await message.answer("Ошибка авторизации в панели XUI")
        return

    inbounds = await get_inbounds(session_cookie)
    if not inbounds.get("obj") or not inbounds["obj"]:
        await message.answer("Нет доступных inbounds")
        return

    user_email = f"user_{message.from_user.id}@vp333nbot"
    found = False

    for inbound in inbounds["obj"]:
        inbound_id = inbound["id"]
        inbound_details = await get_inbound(session_cookie, inbound_id)

        if not inbound_details.get("obj"):
            continue

        settings = json.loads(inbound_details["obj"]["settings"])
        clients = settings.get("clients", [])

        for client in clients:
            if client["email"] == user_email:
                expiry_time = client.get("expiryTime", 0)
                found = True
                break

        if found:
            break

    if not found:
        await message.answer("Подписка не найдена")
        return

    if expiry_time == 0:
        await message.answer("Ваша подписка бессрочная")
        return

    expiry_datetime = datetime.fromtimestamp(expiry_time / 1000)
    time_left = expiry_datetime - datetime.now()

    if time_left.total_seconds() <= 0:
        await message.answer("Ваша подписка истекла")
        return

    days = time_left.days
    hours, remainder = divmod(time_left.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if days > 0:
        time_str = f"{days} дней, {hours} часов"
    else:
        time_str = f"{hours} часов, {minutes} минут"

    expiry_date_str = expiry_datetime.strftime("%d.%m.%Y в %H:%M")

    await message.answer(
        f"⏳ До окончания подписки:\n\n"
        f"• До окончания: {time_str}\n"
        f"• Дата окончания: {expiry_date_str}\n\n"
        f"Чтобы продлить подписку, выберите '🛒 Купить подписку'",
        reply_markup=kb.main
    )


@dp.message(lambda message: message.text == '🔄 Сгенерировать ключ')
async def generate_key_handler(message: types.Message):

    
    # 1. Авторизация в XUI
    session_cookie = await login_to_xui()
    if not session_cookie:
        await message.answer("Ошибка авторизации в панели XUI")
        return

    # 2. Получаем список inbounds
    inbounds = await get_inbounds(session_cookie)

    # 3. Выбираем первый подходящий inbound
    if not inbounds.get("obj") or not inbounds["obj"]:
        await message.answer("Нет доступных inbounds")
        return

    inbound_id = inbounds["obj"][0]["id"]

    user_email = f"user_{message.from_user.id}@vp333nbot"
    add_result = await add_client(session_cookie, inbound_id, user_email, expiry_days=30)

    if not add_result.get("success"):
        await message.answer("Ошибка при создании нового клиента")
        return

    # 4. Получаем полную информацию о inbound
    inbound = await get_inbound(session_cookie, inbound_id)

    # 5. Генерируем URL
    vless_url = generate_vless_url(inbound["obj"], domain_xui)

    # 6. Отправляем пользователю
    await message.answer(
        f"Ваша конфигурация:\n\n"
        f"`{vless_url}`\n\n"
        f"Используйте этот ключ в поддерживаемых клиентах.",
        parse_mode="Markdown"
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    print("run bot . . .")
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот остановлен')