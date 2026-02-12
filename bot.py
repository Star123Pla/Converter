import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8205557147:AAFYGuFUR_fJNn0NhE2xBZIW_ZCDM0D5q5A"

# Храним состояние пользователя
user_state = {}

# Курсы крипты через CoinGecko
def get_crypto_price(crypto, vs):
    url = "https://api.coingecko.com/api/v3/simple/price"
    ids_map = {
        "TON": "the-open-network",
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "USDT": "tether",
    }
    params = {
        "ids": ids_map[crypto],
        "vs_currencies": vs.lower(),
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data[ids_map[crypto]][vs.lower()]

# Курсы фиата
def get_fiat_rate(base, target):
    url = f"https://open.er-api.com/v6/latest/{base}"
    response = requests.get(url)
    data = response.json()
    return data["rates"][target]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💱 Выбрать валюты", callback_data="choose")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери действие:", reply_markup=reply_markup)

async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    currencies = ["RUB", "USD", "EUR", "TON", "BTC", "ETH", "USDT"]

    keyboard = []
    for c in currencies:
        keyboard.append([InlineKeyboardButton(c, callback_data=f"from_{c}")])

    await query.edit_message_text(
        "Выбери из какой валюты конвертировать:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def from_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    from_cur = query.data.split("_")[1]
    user_state[query.from_user.id] = {"from": from_cur}

    currencies = ["RUB", "USD", "EUR", "TON", "BTC", "ETH", "USDT"]

    keyboard = []
    for c in currencies:
        if c != from_cur:
            keyboard.append([InlineKeyboardButton(c, callback_data=f"to_{c}")])

    await query.edit_message_text(
        f"Конвертировать из {from_cur} во что?",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def to_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    to_cur = query.data.split("_")[1]
    user_state[query.from_user.id]["to"] = to_cur

    await query.edit_message_text(
        f"Введи сумму в {user_state[query.from_user.id]['from']}:"
    )

async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in user_state:
        return

    try:
        amount = float(update.message.text.replace(",", "."))
        from_cur = user_state[user_id]["from"]
        to_cur = user_state[user_id]["to"]

        # Определяем тип конвертации
        if from_cur in ["TON", "BTC", "ETH", "USDT"]:
            rate = get_crypto_price(from_cur, to_cur)
        elif to_cur in ["TON", "BTC", "ETH", "USDT"]:
            rate = 1 / get_crypto_price(to_cur, from_cur)
        else:
            rate = get_fiat_rate(from_cur, to_cur)

        result = amount * rate

        await update.message.reply_text(
            f"💰 {amount} {from_cur} ≈ {result:.4f} {to_cur}"
        )

    except:
        await update.message.reply_text("❌ Введи корректное число.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(choose, pattern="choose"))
    app.add_handler(CallbackQueryHandler(from_currency, pattern="from_"))
    app.add_handler(CallbackQueryHandler(to_currency, pattern="to_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, convert))

    print("Бот запущен...")
    app.run_polling()


