import telebot
import requests
import json
import os

from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

TOKEN = os.environ.get("TOKEN")
API_KEY = "tgnum5980"

FORCE_CHANNELS = [
    "@elite_v0rt3x",
    "@knoxJAVA",
    "@louis_g0d"
]

OWNER_ID = 5456735328  # your telegram user id

START_CREDITS = 3
REF_BONUS = 1

bot = telebot.TeleBot(BOT_TOKEN)

DB_FILE = "users.json"

def load_users():
    if not os.path.exists(DB_FILE):
        return {}

    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

users = load_users()


def add_user(user_id):
    user_id = str(user_id)

    if user_id not in users:
        users[user_id] = {
            "credits": 3,
            "referred_by": None
        }

        save_users(users)

def search_username(username):
    url = f"https://anon-tg-info.vercel.app/tg2num/user?key=tgnum5980&q={username}"

    try:
        r = requests.get(url, timeout=15)
        return r.json()
    except:
        return None
    
def has_credit(user_id):
    user_id = str(user_id)

    return users.get(user_id, {}).get("credits", 0) > 0


def get_credits(user_id):
    user_id = str(user_id)

    return users.get(user_id, {}).get("credits", 0)


def deduct_credit(user_id):
    user_id = str(user_id)

    if user_id not in users:
        return

    users[user_id]["credits"] -= 1
    save_users(users)


def add_credit(user_id, amount=1):
    user_id = str(user_id)

    if user_id not in users:
        add_user(user_id)

    users[user_id]["credits"] += amount
    save_users(users)

def process_referral(new_user, referrer):
    new_user = str(new_user)
    referrer = str(referrer)

    if new_user == referrer:
        return

    if users[new_user]["referred_by"] is not None:
        return

    users[new_user]["referred_by"] = referrer

    if referrer in users:
        users[referrer]["credits"] += 1

    save_users(users)


def is_joined(user_id):

    for channel in FORCE_CHANNELS:

        try:
            member = bot.get_chat_member(
                channel,
                user_id
            )

            if member.status in ["left", "kicked"]:
                return False

        except:
            return False

    return True


from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    kb = InlineKeyboardMarkup(row_width=1)

    kb.add(
        InlineKeyboardButton(
            "💳 Credits",
            callback_data="credits"
        )
    )

    kb.add(
        InlineKeyboardButton(
            "🎁 Referral",
            callback_data="ref"
        )
    )

    kb.add(
        InlineKeyboardButton(
            "👤 Account",
            callback_data="account"
        )
    )

    

    return kb



def join_menu():
    kb = InlineKeyboardMarkup(row_width=1)

    for channel in FORCE_CHANNELS:
        kb.add(
            InlineKeyboardButton(
                f"📢 Join {channel}",
                url=f"https://t.me/{channel.replace('@','')}"
            )
        )

    kb.add(
        InlineKeyboardButton(
            "✅ Verify",
            callback_data="verify_join"
        )
    )

    return kb






@bot.message_handler(commands=['credit'])
def give_credit(message):

    if message.from_user.id != OWNER_ID:
        return

    try:
        args = message.text.split()

        target_id = str(args[1])
        amount = int(args[2])

        if target_id not in users:
            add_user(target_id)

        add_credit(target_id, amount)

        bot.reply_to(
            message,
            f"✅ Added {amount} credit(s) to {target_id}"
        )

        try:
            bot.send_message(
                target_id,
                f"🎁 Admin added {amount} credit(s).\n\n💳 Total Credits: {get_credits(target_id)}"
            )
        except:
            pass

    except:
        bot.reply_to(
            message,
            "Usage:\n/credit USER_ID AMOUNT"
        )


@bot.message_handler(commands=['stats'])
def stats(message):

    if message.from_user.id != OWNER_ID:
        return

    bot.reply_to(
        message,
        f"""
👥 Users: {len(users)}

💾 Database: users.json
"""
    )


@bot.message_handler(commands=['start'])
def start(message):

    user_id = str(message.from_user.id)

    add_user(user_id)

    args = message.text.split()

    if len(args) > 1:

        ref = args[1]

        if ref.startswith("ref_"):

            referrer = ref.replace("ref_", "")

            process_referral(
                user_id,
                referrer
            )

    if not is_joined(user_id):

        bot.reply_to(
            message,
            "🔒 Join all channels first to use this bot.",
            reply_markup=join_menu()
        )

        return

    bot.reply_to(
        message,
        f"""
        👋 Welcome!

        💳 Credits: {get_credits(user_id)}

        📖 Commands:
        /search @username
        /account
        /menu
        /help
        """,
        reply_markup=main_menu()
    )



@bot.message_handler(commands=['help'])
def help_cmd(message):

    text = """
📖 Available Commands

/start - Start the bot

/menu - Show main menu

/help - Show this help message

/search @username - Search Telegram username

/account - Show your account details

🎁 Referral System:
Invite friends using your referral link and earn credits.

💳 Credits:
• New users get 3 credits
• Successful search = -1 credit
• No result = No credit deducted
"""

    bot.reply_to(
        message,
        text,
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['menu'])
def menu_cmd(message):

    user_id = str(message.from_user.id)

    if not is_joined(user_id):

        bot.reply_to(
            message,
            "🔒 Join all required channels first.",
            reply_markup=join_menu()
        )

        return

    bot.reply_to(
        message,
        "🏠 Main Menu",
        reply_markup=main_menu()
    )

@bot.message_handler(commands=['account'])
def account_cmd(message):

    user_id = str(message.from_user.id)

    text = f"""
👤 User ID: {user_id}

💳 Credits: {get_credits(user_id)}

🎁 Referral Link:
https://t.me/{bot.get_me().username}?start=ref_{user_id}
"""

    bot.reply_to(message, text)



@bot.message_handler(commands=['search'])
def lookup(message):

    try:
        username = message.text.split()[1]
    except:
        bot.reply_to(
            message,
            "Usage:\n/search @username"
        )
        return

    user_id = message.from_user.id

    if not is_joined(user_id):
        bot.reply_to(
            message,
            "❌ Join all required channels first."
        )
        return

    if not has_credit(user_id):
        bot.reply_to(
            message,
            "❌ You have no credits left."
        )
        return

    data = search_username(username)

    print(data)

    if not data:
        bot.reply_to(
            message,
            "❌ API Error."
        )
        return

    response = data.get("response", {})
    params = response.get("parameters", {})

    if not params.get("success"):
        bot.reply_to(
            message,
            "❌ No data found.\nNo credit deducted."
        )
        return

    deduct_credit(user_id)

    credits = get_credits(user_id)

    result = response.get("data", [])

    if not result:
        bot.reply_to(
            message,
            "❌ No data found."
        )
        return

    result = result[0]

    uid = result.get("user_id", "N/A")
    number = result.get("number", "Hidden")
    country = result.get("country", "N/A")
    country_code = result.get("country_code", "N/A")

    text = f"""
👤 Username: {username}

🆔 User ID: {uid}

📱 Number: {number}

🌍 Country: {country}

☎️ Country Code: {country_code}

💳 Remaining Credits: {credits}
"""

    bot.reply_to(
        message,
        text,
        reply_markup=main_menu()
    )

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):


    if call.data == "verify_join":

        user_id = str(call.from_user.id)

        if not is_joined(user_id):

            bot.answer_callback_query(
                call.id,
                "❌ Join all required channels first.",
                show_alert=True
            )

            return

        bot.edit_message_text(
            f"👋 Welcome!\n\n💳 Credits: {get_credits(user_id)}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=main_menu()
        )

        return

    user_id = str(call.from_user.id)

    if call.data == "credits":

        bot.answer_callback_query(
            call.id,
            f"Credits: {get_credits(user_id)}",
            show_alert=True
        )

    elif call.data == "account":

        text = f"""
👤 ID: {user_id}

💳 Credits: {get_credits(user_id)}
"""

        bot.send_message(
            call.message.chat.id,
            text
        )

    elif call.data == "ref":

        bot_username = bot.get_me().username

        link = (
            f"https://t.me/{bot_username}"
            f"?start=ref_{user_id}"
        )

        bot.send_message(
            call.message.chat.id,
            f"🎁 Referral Link:\n\n{link}"
        )


print("Bot Started...")
bot.infinity_polling(skip_pending=True)
