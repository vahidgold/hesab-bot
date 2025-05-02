import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
import pandas as pd
from datetime import datetime
import os

# 🔐 توکن ربات
TOKEN = '7701298788:AAEhZyqha5fu8YVsK7A0n5C1yQ0lFMgWbAw'

# مراحل گفتگو
AMOUNT, BANK, DATE = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 سلام! لطفاً مبلغ برداشت را وارد کن:")
    return AMOUNT

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["amount"] = update.message.text
    await update.message.reply_text("🏦 نام بانک مبدأ را وارد کن:")
    return BANK

async def get_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bank"] = update.message.text.strip()
    await update.message.reply_text("📅 تاریخ را وارد کن (مثلاً 1403/02/12 یا 2025-05-02):")
    return DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = context.user_data["amount"]
    bank = context.user_data["bank"]
    date_input = update.message.text.strip()

    try:
        if "/" in date_input:
            date = datetime.strptime(date_input, "%Y/%m/%d")
        else:
            date = datetime.strptime(date_input, "%Y-%m-%d")
    except:
        await update.message.reply_text("❌ تاریخ نامعتبره. لطفاً با فرمت صحیح وارد کن.")
        return DATE

    filename = "transactions.xlsx"
    sheet_name = bank

    new_row = {
        "تاریخ": date.strftime("%Y-%m-%d"),
        "مبلغ": amount,
        "بانک": bank
    }

    if os.path.exists(filename):
        with pd.ExcelWriter(filename, engine="openpyxl", mode="a", if_sheet_exists="overlay") as writer:
            try:
                df_existing = pd.read_excel(filename, sheet_name=sheet_name)
            except:
                df_existing = pd.DataFrame(columns=["تاریخ", "مبلغ", "بانک"])

            df_new = pd.concat([df_existing, pd.DataFrame([new_row])], ignore_index=True)
            df_new = df_new.sort_values(by="تاریخ")
            df_new.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        df = pd.DataFrame([new_row])
        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    await update.message.reply_text("✅ اطلاعات ذخیره شد.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد.")
    return ConversationHandler.END

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            BANK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bank)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    print("🤖 Bot is running...")
    app.run_polling()
