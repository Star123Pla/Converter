import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN = "8205557147:AAFYGuFUR_fJNn0NhE2xBZIW_ZCDM0D5q5A"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ----------- FSM -----------
class ConvertState(StatesGroup):
    choosing_from = State()
    choosing_to = State()
    entering_amount = State()


# ----------- Главное меню -----------
def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="💱 Конвертировать валюту", callback_data="convert")
    kb.adjust(1)
    return kb.as_markup()


# ----------- Валюты -----------
POPULAR_CURRENCIES = [
    "USD", "EUR", "RUB", "TON", "BTC", "ETH"
]


def currency_keyboard(prefix):
    kb = InlineKeyboardBuilder()
    for cur in POPULAR_CURRENCIES:
        kb.button(text=cur, callback_data=f"{prefix}_{cur}")
    kb.button(text="⬅️ В главное меню", callback_data="back_main")
    kb.adjust(3)
    return kb.as_markup()


# ----------- Старт -----------
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🚀 Главное меню:", reply_markup=main_menu())


# ----------- Назад в меню -----------
@dp.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🚀 Главное меню:", reply_markup=main_menu())
    await callback.answer()


# ----------- Начало конвертации -----------
@dp.callback_query(F.data == "convert")
async def choose_from(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ConvertState.choosing_from)
    await callback.message.edit_text("Выбери валюту ИЗ:", reply_markup=currency_keyboard("from"))
    await callback.answer()


# ----------- Выбор FROM -----------
@dp.callback_query(ConvertState.choosing_from, F.data.startswith("from_"))
async def choose_to(callback: CallbackQuery, state: FSMContext):
    from_currency = callback.data.split("_")[1]
    await state.update_data(from_currency=from_currency)
    await state.set_state(ConvertState.choosing_to)

    await callback.message.edit_text(
        f"Конвертируем из {from_currency}\n\nВыбери валюту В:",
        reply_markup=currency_keyboard("to")
    )
    await callback.answer()


# ----------- Выбор TO -----------
@dp.callback_query(ConvertState.choosing_to, F.data.startswith("to_"))
async def enter_amount(callback: CallbackQuery, state: FSMContext):
    to_currency = callback.data.split("_")[1]
    await state.update_data(to_currency=to_currency)
    await state.set_state(ConvertState.entering_amount)

    await callback.message.edit_text(
        "Введите сумму (можно 1.7 или 1,7):",
        reply_markup=currency_keyboard("cancel")
    )
    await callback.answer()


# ----------- Парсинг числа -----------
def parse_amount(text):
    try:
        text = text.replace(",", ".")
        value = float(text)
        if value <= 0:
            return None
        return value
    except ValueError:
        return None


# ----------- Получение курса -----------
async def get_rate(from_cur, to_cur):
    url = f"https://api.exchangerate.host/convert?from={from_cur}&to={to_cur}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return data["result"]


# ----------- Ввод суммы -----------
@dp.message(ConvertState.entering_amount)
async def convert_currency(message: Message, state: FSMContext):
    amount = parse_amount(message.text)

    if amount is None:
        await message.answer("❌ Введи корректное число.")
        return

    data = await state.get_data()
    from_currency = data["from_currency"]
    to_currency = data["to_currency"]

    rate = await get_rate(from_currency, to_currency)

    if rate is None:
        await message.answer("Ошибка получения курса.")
        return

    result = amount * rate

    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ В главное меню", callback_data="back_main")
    kb.adjust(1)

    await message.answer(
        f"💱 Результат:\n\n"
        f"{amount} {from_currency} = {round(result, 4)} {to_currency}",
        reply_markup=kb.as_markup()
    )

    await state.clear()


# ----------- Запуск -----------
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
