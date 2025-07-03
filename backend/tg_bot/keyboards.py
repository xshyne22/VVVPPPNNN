from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🛒 Купить подписку')],
    [KeyboardButton(text='🕰️ Сколько осталось до окончания подписки')],
    [KeyboardButton(text='Удалить клиента')]
])

subscribes = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='1 month')],
    [KeyboardButton(text='🔙 Назад')]
])

gen = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🔄 Сгенерировать ключ')],
    [KeyboardButton(text='🔙 Назад к подпискам')]
])