import os
import re
import threading
import requests
from flask import Flask
import pyzmail
from imapclient import IMAPClient
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# Telegram Bot Token (Replace this with your actual token)
TOKEN = os.getenv("TELEGRAM_TOKEN", "8139032073:AAHwEsOYmN9t5lXMROkZNKPvNLyAeiXfDQQ")

# Account details for fetching verification codes
ACCOUNTS = {
    'steam': {
        'email': 'hamaittisali@gmail.com',
        'password': 'vjkg ilrn jxyp ocyb',
        'sender': 'noreply@steampowered.com'
    },
    'rockstar': {
        'email': 'itsklox@gmail.com',
        'password': 'fros isfi gxux siuu',
        'sender': 'noreply@rockstargames.com'
    },
    'ubisoft': {
        'email': 'hamaarizgar@gmail.com',
        'password': 'woes zpne kwga xeqd',
        'sender': 'AccountSupport@ubi.com'
    }
}

# Flask app to keep the bot alive (useful on Replit or Heroku)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

def keep_alive():
    threading.Thread(target=run).start()

# ✅ PIN Protection System
PIN_CODE = "BM323"
verified_users = {}

def start(update, context):
    user_id = update.message.chat_id

    # ✅ Send an Imgur image before asking for the PIN
    image_url = "https://imgur.com/a/kCxQJTS"  # Replace with your actual Imgur direct image URL
    update.message.reply_photo(photo=image_url, caption="🔑 الرجاء إدخال رقم التعريف الشخصي للمتابعة:")

    # Ask for the PIN
    update.message.reply_text("🔑 الرجاء إدخال رقم التعريف الشخصي للمتابعة:")

def verify_pin(update, context):
    user_id = update.message.chat_id
    pin_entered = update.message.text.strip()

    if pin_entered == PIN_CODE:
        verified_users[user_id] = True  # Mark the user as verified

        # ✅ Send another Imgur image after PIN verification
        image_url = "https://imgur.com/a/kCxQJTS"  # Replace with another Imgur direct image URL if needed
        update.message.reply_photo(photo=image_url, caption="✅ رقم التعريف الشخصي صحيح! يمكنك الآن تحديد حساب.")

        show_account_menu(update)
    else:
        update.message.reply_text("❌ رقم التعريف الشخصي غير صحيح! يرجى المحاولة مرة أخرى. "
                                  "إذا كنت بحاجة إلى المساعدة، تواصل مع الحساب الرسمي Kurdsell.com "
                                  "أو عبر واتساب: +964 777 777 444 6415.")

def show_account_menu(update):
    keyboard = [
        [InlineKeyboardButton('🎮 Steam Account', callback_data='steam')],
        [InlineKeyboardButton('⭐ Rockstar Account', callback_data='rockstar')],
        [InlineKeyboardButton('🎯 Ubisoft Account', callback_data='ubisoft')]
    ]
    update.message.reply_text(
        'أختار منصة الحساب المشترك🔗🎮:',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def button(update, context):
    query = update.callback_query
    query.answer()

    account = query.data
    account_info = ACCOUNTS.get(account)
    if not account_info:
        query.message.reply_text("❌ تم تحديد حساب غير صالح.")
        return

    query.message.reply_text(f'⏳ إحضار رمز التحقق لـ {account.title()}...')

    try:
        with IMAPClient('imap.gmail.com') as client:
            client.login(account_info['email'], account_info['password'])
            client.select_folder('INBOX')

            all_uids = client.search(['FROM', account_info['sender']])
            uids = all_uids[-10:] if len(all_uids) > 10 else all_uids

            if uids:
                for uid in reversed(uids):  # Process latest emails first
                    raw_message = client.fetch([uid], ['BODY[]', 'ENVELOPE'])
                    message = pyzmail.PyzMessage.factory(raw_message[uid][b'BODY[]'])
                    email_subject = raw_message[uid][b'ENVELOPE'].subject.decode(errors='ignore').lower()

                    # ✅ Debugging: Print email subjects
                    print(f"Processing Email Subject: {email_subject}")

                    # ✅ Accept Steam and Rockstar verification codes
                    accepted_subjects = [
                        "your steam account: access from new computer",
                        "your rockstar games verification code",
                        "login code",
                        "verification code",
                        "steam guard",
                        "steam login",
                        "access code"
                    ]

                    if any(keyword in email_subject for keyword in accepted_subjects):
                        text = ""

                        # ✅ Read both text and HTML parts of the email
                        if message.text_part:
                            text += message.text_part.get_payload().decode(errors='ignore')
                        if message.html_part:
                            text += message.html_part.get_payload().decode(errors='ignore')

                        # ✅ Debugging: Print full email content
                        print(f"Email Content:\n{text}")

                        # ✅ Extract verification codes (5-8 characters)
                        code_match = re.search(r'\b[A-Z0-9]{5,8}\b', text)

                        if code_match:
                            verification_code = code_match.group(0)
                            query.message.reply_text(
                                f'🔑 رمز التحقق لمنصة {account.title()}:\n👉 {verification_code}'
                            )
                            return

                query.message.reply_text("⚠️ لم يتم العثور على رمز تسجيل الدخول.")
            else:
                query.message.reply_text("📭 لم يتم العثور على رسائل بريد إلكتروني جديدة.")

    except Exception as e:
        query.message.reply_text(f'❌ خطأ في جلب رسائل البريد الإلكتروني: {e}')

def main():
    keep_alive()

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, verify_pin))  # Handles PIN verification
    dp.add_handler(CallbackQueryHandler(button))  # Handles account selection

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
