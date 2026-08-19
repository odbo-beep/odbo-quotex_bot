import os
import json
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DATA_FILE = "results.json"


def load_data():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 محلل الشموع 1M\n\n"
        "أرسل صورة الشارت وسأقوم بتسجيلها للتحليل والمحاكاة.\n\n"
        "بعد النتيجة استعمل:\n"
        "/success = نجح التوقع\n"
        "/loss = خسر التوقع\n"
        "/stats = الإحصائيات"
    )


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]

    os.makedirs("charts", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"charts/chart_{timestamp}.jpg"

    telegram_file = await context.bot.get_file(photo.file_id)
    await telegram_file.download_to_drive(filename)

    data = load_data()

    record = {
        "id": len(data) + 1,
        "timeframe": "1M",
        "image": filename,
        "time": datetime.now().isoformat(),
        "prediction": "pending",
        "result": "pending",
        "reasons": []
    }

    data.append(record)
    save_data(data)

    await update.message.reply_text(
        "📸 تم استلام الشارت.\n\n"
        "⏱️ الفريم: 1M\n"
        "🔎 الحالة: في انتظار محرك تحليل الصورة.\n\n"
        "بعد إضافة محرك الرؤية سيقوم بتحليل:\n"
        "🕯️ حركة الشموع\n"
        "📈 RSI\n"
        "📊 MACD\n"
        "📉 Aroon\n"
        "〽️ Stochastic\n"
        "📐 Moving Average\n"
        "🔺 Fractal / ZigZag\n\n"
        "وسيشرح أسباب التحليل بدل إعطاء نتيجة بلا تفسير."
    )


def set_result(result):
    data = load_data()

    for record in reversed(data):
        if record["result"] == "pending":
            record["result"] = result
            save_data(data)
            return True

    return False


async def success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if set_result("success"):
        await update.message.reply_text(
            "✅ تم تسجيل النتيجة: نجح التوقع."
        )
    else:
        await update.message.reply_text(
            "لا توجد نتيجة معلقة."
        )


async def loss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if set_result("loss"):
        await update.message.reply_text(
            "❌ تم تسجيل النتيجة: خسر التوقع."
        )
    else:
        await update.message.reply_text(
            "لا توجد نتيجة معلقة."
        )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()

    success_count = sum(
        x["result"] == "success" for x in data
    )

    loss_count = sum(
        x["result"] == "loss" for x in data
    )

    total = success_count + loss_count

    accuracy = (
        success_count / total * 100
        if total > 0
        else 0
    )

    await update.message.reply_text(
        "📊 إحصائيات المحاكاة\n\n"
        f"✅ نجحت: {success_count}\n"
        f"❌ خسرت: {loss_count}\n"
        f"🎯 النسبة: {accuracy:.2f}%"
    )


def main():
    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN غير موجود."
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("success", success)
    )

    app.add_handler(
        CommandHandler("loss", loss)
    )

    app.add_handler(
        CommandHandler("stats", stats)
    )

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            receive_photo
        )
    )

    print("Bot started...")

    app.run_polling()


if __name__ == "__main__":
    main()
