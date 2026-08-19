import os
import json
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

DATA_FILE = "results.json"


def load_results():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_results(results):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 محلل الشموع التجريبي جاهز.\n\n"
        "أرسل صورة الشموع، وسنسجلها للتحليل والمحاكاة.\n\n"
        "الأوامر:\n"
        "/stats - إحصائيات النتائج\n"
        "/success - تسجيل آخر توقع: نجح\n"
        "/loss - تسجيل آخر توقع: خسر"
    )


async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]

    file = await context.bot.get_file(photo.file_id)

    os.makedirs("images", exist_ok=True)

    filename = f"images/{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jpg"

    await file.download_to_drive(filename)

    results = load_results()

    record = {
        "image": filename,
        "time": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "analysis": {
            "timeframe": "1M / 5M",
            "direction": "pending",
            "reasons": []
        }
    }

    results.append(record)
    save_results(results)

    await update.message.reply_text(
        "📸 تم استلام الصورة وتسجيلها.\n\n"
        "حاليًا التوقع في وضع الانتظار لأننا لم نربط بعد نموذج تحليل الصورة.\n\n"
        "بعد ربط نموذج الرؤية، سيقوم النظام بتحليل:\n"
        "🕯️ الشموع\n"
        "📈 RSI\n"
        "📊 MACD\n"
        "📉 Aroon\n"
        "〽️ Stochastic\n"
        "📐 Moving Average\n"
        "🔺 Fractal / ZigZag\n"
        "⏱️ توافق 1M مع 5M"
    )


def update_last(status):
    results = load_results()

    for record in reversed(results):
        if record["status"] == "pending":
            record["status"] = status
            save_results(results)
            return True

    return False


async def success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update_last("success"):
        await update.message.reply_text(
            "✅ تم تسجيل آخر توقع كـ «نجح».\n"
            "سيتم استعمال النتيجة في إحصائيات النموذج."
        )
    else:
        await update.message.reply_text("لا يوجد توقع معلّق.")


async def loss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update_last("loss"):
        await update.message.reply_text(
            "❌ تم تسجيل آخر توقع كـ «خسر».\n"
            "سيتم استعمال النتيجة في إحصائيات النموذج."
        )
    else:
        await update.message.reply_text("لا يوجد توقع معلّق.")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = load_results()

    success_count = sum(r["status"] == "success" for r in results)
    loss_count = sum(r["status"] == "loss" for r in results)

    total = success_count + loss_count

    if total:
        accuracy = (success_count / total) * 100
    else:
        accuracy = 0

    await update.message.reply_text(
        f"📊 إحصائيات المحاكاة\n\n"
        f"✅ نجحت: {success_count}\n"
        f"❌ خسرت: {loss_count}\n"
        f"🎯 الدقة: {accuracy:.2f}%"
    )


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN غير موجود في متغيرات البيئة."
        )

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("success", success))
    app.add_handler(CommandHandler("loss", loss))

    app.add_handler(
        MessageHandler(filters.PHOTO, receive_image)
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
