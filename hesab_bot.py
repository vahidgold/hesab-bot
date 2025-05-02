import logging
import pandas as pd
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters

# توکن ربات
TOKEN = "7701298788:AAEhZyqha5fu8YVsK7A0n5C1yQ0lFMgWbAw"

# مرحله‌ها
NAME, AMOUNT, BANK, DATE, CONFIRM = range(5)

# شروع گفتگو
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("نام برداشت‌کننده را وارد کن:")
    return NAME

# دریافت نام برداشت‌کننده
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text
    await update.message.reply_text("مبلغ برداشت را وارد کن:")
    return AMOUNT

# دریافت مبلغ
async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["amount"] = update.message.text
    await update.message.reply_text("نام بانک مبدا را وارد کن:")
    return BANK

# دریافت نام بانک
async def get_bank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["bank"] = update.message.text
    await update.message.reply_text("تاریخ برداشت را وارد کن (مثلاً 1403/02/12):")
    return DATE

# دریافت تاریخ و نمایش اطلاعات
async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["date"] = update.message.text

    # استخراج اطلاعات
    name = context.user_data["name"]
    amount = context.user_data["amount"]
    bank = context.user_data["bank"]
    date = context.user_data["date"]

    # نمایش اطلاعات برای تایید
    confirmation_text = f"آیا اطلاعات صحیح است؟\n\n" \
                        f"برداشت‌کننده: {name}\n" \
                        f"مبلغ: {amount}\n" \
                        f"بانک: {bank}\n" \
                        f"تاریخ: {date}"

    # دکمه‌ها برای تایید یا اصلاح
    keyboard = [
        [
            InlineKeyboardButton("اصلاح", callback_data='edit'),
            InlineKeyboardButton("تایید", callback_data='confirm')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(confirmation_text, reply_markup=reply_markup)
    return CONFIRM

# پردازش تایید یا اصلاح
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # اطلاعات از کاربر
    name = context.user_data["name"]
    amount = context.user_data["amount"]
    bank = context.user_data["bank"]
    date = context.user_data["date"]

    if query.data == "edit":
        await query.edit_message_text("مراحلی که باید اصلاح کنید:\n1. نام برداشت‌کننده\n2. مبلغ\n3. بانک\n4. تاریخ")
        return NAME
    elif query.data == "confirm":
        # ذخیره اطلاعات در فایل اکسل
        filename = f"{bank}.xlsx"
        new_data = pd.DataFrame([{"نام": name, "مبلغ": amount, "بانک": bank, "تاریخ": date}])

        try:
            existing = pd.read_excel(filename)
            df = pd.concat([existing, new_data], ignore_index=True)
        except FileNotFoundError:
            df = new_data

        df = df.sort_values(by="تاریخ", ascending=False)
        df.to_excel(filename, index=False)

        # ارسال فایل اکسل به کاربر
        with open(filename, "rb") as file:
            await query.edit_message_text("اطلاعات تایید شد. فایل به‌روز شده ارسال می‌شود.")
            await query.message.reply_document(InputFile(file), caption="فایل به‌روز شده‌ی برداشت‌ها:")

        return ConversationHandler.END

# لغو عملیات
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END

# راه‌اندازی ربات
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            BANK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bank)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_confirmation)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()
