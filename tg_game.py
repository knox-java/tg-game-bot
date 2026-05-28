from unittest.mock import call

import telebot
import json
import random
import time
import threading
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import html
import pymysql


TOKEN = os.environ.get("TOKEN")

ADMIN_IDS = [
    str(x)
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x
]


DATA_FILE = "Game_tg.json"

bot = telebot.TeleBot(TOKEN)

telebot.apihelper.CONNECT_TIMEOUT = 30
telebot.apihelper.READ_TIMEOUT = 30


# =========================================
# MYSQL CONNECTION
# =========================================



from urllib.parse import urlparse

mysql_url = os.getenv("MYSQL_URL")

url = urlparse(mysql_url)

db = pymysql.connect(

    host=url.hostname,
    user=url.username,
    password=url.password,
    database=url.path[1:],
    port=url.port,

    autocommit=True,
    cursorclass=pymysql.cursors.DictCursor

)


cursor = db.cursor()

cursor.execute("SELECT VERSION()")
print(cursor.fetchone())

print("✅ MYSQL CONNECTED")


def save_user(chat_id, uid, data):

    sql = """
    INSERT INTO users (
        chat_id,
        user_id,
        name,
        money,
        bank,
        xp,
        level,
        zone,
        weapon,
        armor,
        hunger
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)

    ON DUPLICATE KEY UPDATE

    name=%s,
    money=%s,
    bank=%s,
    xp=%s,
    level=%s,
    zone=%s,
    weapon=%s,
    armor=%s,
    hunger=%s
    """

    values = (
        chat_id,
        uid,
        data["name"],
        data["money"],
        data["bank"],
        data["xp"],
        data["level"],
        data["zone"],
        data["weapon"],
        int(data["armor"]),
        data["hunger"],

        data["name"],
        data["money"],
        data["bank"],
        data["xp"],
        data["level"],
        data["zone"],
        data["weapon"],
        int(data["armor"]),
        data["hunger"]
    )

    cursor.execute(sql, values)

# ===== DATA =====
users, missions, trades, gangs = {}, {}, {}, {}
jail, dead, shield = {}, {}, {}
kill_cd = {}
rob_cd = {}

daily_cd = {}
invites = {}
mission_cd = {}
banned = {}
admin_cd = {}
job_owner = {}
coin_cd = {}
give_cd = {}
group_data = {}
duel_cd = {}
pending_duels = {}
fish_cd = {}
withdraw_input = {}
rps_games = {}
spin_cd = {}
slot_games = {}
military_cd = {}
rps_cd = {}
slot_cd = {}   # cooldown only
mines_games = {}
mines_cd = {}
button_cd = {}
candy_games = {}
candy_cd = {}

# ===== LOAD/SAVE =====
def load():
    global users, missions, trades, gangs
    global jail, dead, shield
    global daily_cd, kill_cd, rob_cd, invites, mission_cd
    global banned
    global job_owner
    global group_data

    try:
        # 🔥 1. Ensure file exists (CRITICAL FIX)
        if not os.path.exists(DATA_FILE):
            print("⚠️ Data file not found, creating new...")
            with open(DATA_FILE, "w") as f:
                json.dump({}, f)

        # 🔥 2. Load file safely
        with open(DATA_FILE) as f:
            d = json.load(f)

            users = d.get("users", {})
            missions = d.get("missions", {})
            trades = d.get("trades", {})
            gangs = d.get("gangs", {})
            jail = d.get("jail", {})
            dead = d.get("dead", {})
            shield = d.get("shield", {})
            daily_cd = d.get("daily_cd", {})
            kill_cd = d.get("kill_cd", {})
            rob_cd = d.get("rob_cd", {})
            invites = d.get("invites", {})
            mission_cd = d.get("mission_cd", {})
            banned = d.get("banned", {})
            job_owner = d.get("job_owner", {})
            group_data = d.get("group_data", {})

            # 🔥 3. Type safety (important)
            if not isinstance(users, dict): users = {}
            if not isinstance(missions, dict): missions = {}
            if not isinstance(trades, dict): trades = {}
            if not isinstance(gangs, dict): gangs = {}
            if not isinstance(jail, dict): jail = {}
            if not isinstance(dead, dict): dead = {}
            if not isinstance(shield, dict): shield = {}
            if not isinstance(daily_cd, dict): daily_cd = {}
            if not isinstance(kill_cd, dict): kill_cd = {}
            if not isinstance(rob_cd, dict): rob_cd = {}
            if not isinstance(invites, dict): invites = {}
            if not isinstance(mission_cd, dict): mission_cd = {}
            if not isinstance(banned, dict): banned = {}
            if not isinstance(job_owner, dict): job_owner = {}
            if not isinstance(group_data, dict): group_data = {}

        print("✅ Data loaded successfully")

    except Exception as e:
        print("❌ Load error:", e)

        # 🔥 fallback reset (safe)
        users, missions, trades, gangs = {}, {}, {}, {}
        jail, dead, shield = {}, {}, {}
        daily_cd, kill_cd, rob_cd, invites, mission_cd = {}, {}, {}, {}, {}
        banned = {}




def ensure_chat(chat_id):
    chat_id = str(chat_id)

    users.setdefault(chat_id, {})
    missions.setdefault(chat_id, {})
    trades.setdefault(chat_id, {})
    gangs.setdefault(chat_id, {})

    jail.setdefault(chat_id, {})
    dead.setdefault(chat_id, {})
    shield.setdefault(chat_id, {})

    kill_cd.setdefault(chat_id, {})
    rob_cd.setdefault(chat_id, {})

    daily_cd.setdefault(chat_id, {})
    invites.setdefault(chat_id, {})
    mission_cd.setdefault(chat_id, {})
    banned.setdefault(chat_id, {})
    job_owner.setdefault(chat_id, {})

    return chat_id



def save():
    try:

        temp = DATA_FILE + ".tmp"

        with open(temp, "w") as f:

            json.dump({
                "users": users,
                "missions": missions,
                "trades": trades,
                "gangs": gangs,
                "jail": jail,
                "dead": dead,
                "shield": shield,
                "daily_cd": daily_cd,
                "kill_cd": kill_cd,
                "rob_cd": rob_cd,
                "invites": invites,
                "mission_cd": mission_cd,
                "banned": banned,
                "job_owner": job_owner,
                "group_data": group_data
            }, f)

        os.replace(temp, DATA_FILE)

    except Exception as e:
        print("Save error:", e)


def safe_edit(chat_id, msg_id, text, **kwargs):

    try:

        bot.edit_message_text(
            text,
            chat_id,
            msg_id,
            **kwargs
        )

    except Exception as e:

        print("Edit error:", e)
# ===== CONFIG =====
WEAPONS = {
    "knife": {"price": 800, "rate": 0.6, "risk": 0.1},
    "pistol": {"price": 2000, "rate": 0.65, "risk": 0.2},
    "ak47": {"price": 5000, "rate": 0.75, "risk": 0.3},
    "shotgun": {"price": 8000, "rate": 0.8, "risk": 0.4},
    "Kar98k": {"price" : 15000, "rate":0.85, "risk": 0.6},
    "rpg": {"price": 20000, "rate": 1.0, "risk": 0.7},
    
}


ARMOR = {
    "basic": {"price": 3000, "reduce": 0.2},
    "Medium ": {"price": 7000, "reduce": 0.35},
    "High": {"price": 15000, "reduce": 0.5},
    "Advance": {"price": 25000, "reduce": 0.65},
    
}

BREAKER_WEAPONS = {
    "Katana": {"price" : 10000, "rate":0.3, "risk": 0.2},
    "Desert Eagle": {"price" : 25000, "rate":0.5, "risk": 0.6},
    "AWM": {"price" : 35000, "rate":0.75, "risk": 0.7},
    "breaker": {"price": 70000, "rate": 0.85, "risk": 0.85}

}

ZONES = {
    "slums": {"risk": 0.2, "reward": (200, 800)},
    "city": {"risk": 0.4, "reward": (500, 1500)},
    "bank": {"risk": 0.6, "reward": (1000, 3000)},
    "military": {"risk": 0.85, "reward": (2500, 6000)},
    "harbor": {"risk": 0.5, "reward": (800, 2500)},
    "casino": {"risk": 0.7, "reward": (1500, 5000)},

    # 🔥 NEW ZONES
    "arena": {"risk": 0.9, "reward": (3000, 7000)},
    "food": {"risk": 0.1, "reward": (100, 400)},
    "market": {"risk": 0.3, "reward": (400, 1200)},
    "police": {"risk": 0.2, "reward": (200, 600)},
    "mountain": {"risk": 0.75, "reward": (2000, 5500)},
    "garden": {"risk": 0.1, "reward": (50, 300)},
}

CONNECTIONS = {
    "slums": ["city","bank"],
    "city": ["slums", "bank", "casino", "market", "garden","harbor","arena","mountain"],
    "bank": ["city","garden","slums"],
    "casino": ["city", "arena"],
    "arena": ["casino","city"],
    "market": ["city", "food", "police"],
    "food": ["market","city"],
    "police": ["market","harbor"],
    "harbor": ["city", "military","food"],
    "military": ["harbor", "mountain"],
    "mountain": ["military","city"],
    "garden": ["city","bank","arena"]
}

FOODS = {
    "bread": {"price": 100, "heal": 10},
    "burger": {"price": 300, "heal": 25},
    "pizza": {"price": 600, "heal": 50},
    "shawarma": {"price": 800, "heal": 60},
    "biryani": {"price": 1000, "heal": 80},
    "feast": {"price": 1300, "heal": 100}
}

JOB_INFO = {
    "smith": "🔫 Earn from weapon sales",
    "armor": "🛡 Earn from armor purchases",
    "protect": "🛡 Earn from protection shields",
    "bank": "💰 Earn from deposits",
    "police": "🚔 Arrest criminals & earn fines",
    "military": "🪖 Complete missions",
    "harbor": "🌊 Earn from fishing",
    "casino": "🎰 Earn from games",
    "food": "🍗 Earn from food sales",
    "breaker": "💥 Earn from breaker weapons"
}

CANDIES = [
    "🍎",
    "🍇",
    "🍋",
    "🍒",
    "🍉"
]

# ===== USER =====
def get_user(user, chat_id):
    chat_id = str(chat_id)
    uid = str(user.id)

    name = user.first_name or user.username or "Unknown"

    # 🔥 ensure all systems exist
    users.setdefault(chat_id, {})
    missions.setdefault(chat_id, {})
    trades.setdefault(chat_id, {})
    gangs.setdefault(chat_id, {})

    jail.setdefault(chat_id, {})
    dead.setdefault(chat_id, {})
    shield.setdefault(chat_id, {})

    kill_cd.setdefault(chat_id, {})
    rob_cd.setdefault(chat_id, {})

    daily_cd.setdefault(chat_id, {})
    invites.setdefault(chat_id, {})

    # 👤 create user if not exists
    if uid not in users[chat_id]:
        users[chat_id][uid] = {
            "name": name,
            "money": 3000,
            "bank": 0,
            "xp": 0,
            "level": 1,
            "zone": "slums",
            "weapon": None,
            "armor": False,
            "gang": None,

            # 🍗 survival
            "hunger": 100,
            "inventory": [],
            "last_hunger": time.time(),

            # ⚔️ ARENA STATS
            "stats": {
                "strength": 5,
                "muscles": 5,
                "stamina": 5,
                "experience": 0,
                "power": 5
            },

            # 🔥 DUEL STATS (NEW)
            "duel": {
                "wins": 0,
                "losses": 0,
                "total": 0
            },

            "crime": {
                "caught": 0
            }
        }
        save()
        save_user(chat_id, uid, users[chat_id][uid])

    u = users[chat_id][uid]

    # 🔄 update name
    u["name"] = name

    # 🔥 ensure fields for old users
    u.setdefault("hunger", 100)
    u.setdefault("inventory", [])
    u.setdefault("last_hunger", time.time())
    u.setdefault("crime", {"caught": 0})

    # 🔥 ensure stats for old users
    u.setdefault("stats", {
        "strength": 5,
        "muscles": 5,
        "stamina": 5,
        "experience": 0,
        "power": 5
    })

    # 🔥 ensure duel stats for old users (IMPORTANT)
    u.setdefault("duel", {
        "wins": 0,
        "losses": 0,
        "total": 0
    })

    return u







# ===== START / HELP =====
@bot.message_handler(
    commands=['startgame','helpgame'],
    chat_types=['private','group','supergroup']
)
def help_cmd(msg):

    bot.send_message(
        msg.chat.id,
        """
<b>🎮 RPG GAME COMMANDS</b>

<blockquote>
🧠 <b>Missions & Survival</b>

/mission - Get mission  
/do - Complete mission  
/revive - Revive yourself  
/status - Quick profile  
/panel - Full profile  
/stat - PvP stats  
</blockquote>

<blockquote>
🗺️ <b>World & Travel</b>

/map - View world map  
/travel &lt;zone&gt; - Travel zones  
</blockquote>

<blockquote>
⚔️ <b>Combat</b>

/kill (reply) - Attack player  
/rob (reply) - Rob player  
/duel (reply) - Duel player  
/arena - Arena fights  
/upgrade &lt;stat&gt; - Upgrade stats  
</blockquote>

<blockquote>
🛡️ <b>Defense & Protection</b>

/protect - Buy protection shield  
</blockquote>

<blockquote>
💰 <b>Economy & Bank</b>

/daily - Daily reward  
/deposit - Deposit to bank  
/withdraw - Withdraw money  
/give (reply) - Send money  
/accept - Accept transfer  
/decline - Decline transfer  
</blockquote>

<blockquote>
🛒 <b>Shop & Hunger</b>

/shop - Weapons & armor  
/food - Food shop  
/eat &lt;item&gt; - Restore hunger  
</blockquote>

<blockquote>
🎰 <b>Casino Games</b>

/slot &lt;amt&gt; - Slot machine  
/rps &lt;amt&gt; - Rock Paper Scissors  
/spin &lt;amt&gt; - Lucky wheel  
/coin heads/tails &lt;amt&gt;  
/color red/black/green &lt;amt&gt;  
/mines &lt;amt&gt; - Mines casino  
/candy &lt;amt&gt; - Candy Crush  
</blockquote>

<blockquote>
🍬 <b>Candy Crush</b>

/candy &lt;amt&gt; - Start candy game  
Swap nearby candies to match 3  
Earn rewards before moves end  
</blockquote>

<blockquote>
💣 <b>Mines</b>

/mines &lt;amt&gt; - Start mines game  
Avoid bombs and collect rewards  
</blockquote>

<blockquote>
🌊 <b>Jobs & Work</b>

/fish - Fishing job  
/myjob - Your current job  
/alljob - View jobs  
</blockquote>

<blockquote>
🚔 <b>Police</b>

/arrest (reply) - Arrest criminals  
</blockquote>

<blockquote>
🪖 <b>Military</b>

/military - Military missions  
</blockquote>

<blockquote>
👥 <b>Gangs</b>

/creategang &lt;name&gt;  
/joingang &lt;name&gt;  
/ganginvite (reply)  
/acceptgang  
</blockquote>

<blockquote>
👑 <b>Admin Commands</b>

/admin  
/ban (reply)  
/unban (reply)  
/broadcast  
/broadcastpvt  
/setjob (reply)  
/removejob  
</blockquote>

<blockquote>
🔥 <b>Tips</b>

• Eat food to survive  
• Use shields before combat  
• Casino games can make or lose money  
• Mines & Candy are high-risk games  
• Upgrade stats for stronger PvP  
</blockquote>

""",
        parse_mode="HTML"
    )




def get_money_rank(money):
    if money < 20000:
        return "Middle"
    elif money < 75000:
        return "Upper"
    elif money < 500000:
        return "Rich"
    elif money < 1000000:
        return "👑 King"
    else:
        return "🔥 Emperor"



def get_duel_rank(wins):
    if wins < 5:
        return "🥉 Bronze"
    elif wins < 15:
        return "🥈 Silver"
    elif wins < 30:
        return "🥇 Gold"
    elif wins < 75:
        return "💠 Platinum"
    elif wins < 150:
        return "🔥 Master"
    elif wins < 300:
        return "⚡ Elite"
    elif wins < 400:
        return "🏆 Champion"
    elif wins < 1000:
        return "👑 Elite Champion"
    else:
        return "⚔️ Fighter"





def reduce_hunger(chat_id, uid, amount):

    chat_id = str(chat_id)
    uid = str(uid)

    if chat_id not in users:
        return

    if uid not in users[chat_id]:
        return

    u = users[chat_id][uid]

    u["hunger"] = max(0, u.get("hunger", 100) - amount)

    # 💀 starvation death
    if u["hunger"] <= 0:

        dead.setdefault(chat_id, {})
        dead[chat_id][uid] = True

    save()








def generate_candy_board():

    board = []

    for y in range(5):

        row = []

        for x in range(5):

            row.append(
                random.choice(CANDIES)
            )

        board.append(row)

    return board


def draw_candy_board(uid, board):

    kb = InlineKeyboardMarkup(row_width=5)

    for y in range(5):

        buttons = []

        for x in range(5):

            buttons.append(
                InlineKeyboardButton(
                    board[y][x],
                    callback_data=f"candy_{uid}_{x}_{y}"
                )
            )

        kb.row(*buttons)

    return kb








@bot.message_handler(commands=['military'])
def military_mission(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 💀 dead check
    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 📍 zone check
    if u["zone"] != "military":
        return bot.send_message(msg.chat.id, "🪖 Go to MILITARY base")

    job_owner.setdefault(chat_id, {})

    owner = job_owner[chat_id].get("military")

    # ❌ no one owns job
    if not owner:
        return bot.send_message(msg.chat.id, "❌ No military officer assigned")

    # ❌ not the owner
    if owner != uid:
        return bot.send_message(msg.chat.id, "🚫 Only the military officer can do missions")

    # ⏳ cooldown
    military_cd.setdefault(chat_id, {})
    now = time.time()

    if uid in military_cd[chat_id] and now - military_cd[chat_id][uid] < 60:
        left = int(60 - (now - military_cd[chat_id][uid]))
        return bot.send_message(msg.chat.id, f"⏳ Wait {left}s before next mission")

    military_cd[chat_id][uid] = now

    # 🎯 success system (LOW RISK)
    success_rate = 0.9

    if random.random() > success_rate:
        loss = random.randint(50, 150)
        u["money"] = max(0, u["money"] - loss)

        save()

        return bot.send_message(
            msg.chat.id,
            f"❌ Mission failed\n💸 Lost: {loss}"
        )

    # 💰 reward
    reward = random.randint(300, 1500)
    u["money"] += reward

    # 💼 pay job system
    pay_job(chat_id, "military", reward // 4)

    save()

    bot.send_message(
        msg.chat.id,
        f"🪖 Mission completed!\n💰 Earned: {reward}"
    )






@bot.message_handler(commands=['alljob'])
def all_jobs(msg):
    chat_id = ensure_chat(msg.chat.id)

    job_owner.setdefault(chat_id, {})
    chat_users = users.get(chat_id, {})

    ALL_JOBS = [
        "smith","armor","protect","bank",
        "police","military","harbor","casino","food","breaker"
    ]

    text = "💼 <b>JOB LIST</b>\n\n"

    for job in ALL_JOBS:
        owner_id = job_owner[chat_id].get(job)
        info = JOB_INFO.get(job, "No description")

        if owner_id and owner_id in chat_users:
            name = html.escape(chat_users[owner_id]["name"])
            text += f"🔹 <b>{job.title()}</b>\n👤 {name}\n📌 {info}\n\n"
        else:
            text += f"🔹 <b>{job.title()}</b>\n❌ Available\n📌 {info}\n\n"

    bot.send_message(msg.chat.id, text, parse_mode="HTML")




@bot.message_handler(commands=['food'])
def food_shop(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    if check_dead_block(msg, uid):
        return

    kb = InlineKeyboardMarkup()

    for f, data in FOODS.items():
        kb.add(
            InlineKeyboardButton(
                f"{f} 🍗 +{data['heal']} 💰{data['price']}",
                callback_data=f"buyfood{f}"
            )
        )

    bot.send_message(msg.chat.id, "🍗 Food Shop:", reply_markup=kb)






@bot.message_handler(commands=['eat'])
def eat(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    if check_dead_block(msg, uid):
        return

    parts = msg.text.split()
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /eat item")

    item = parts[1].lower()

    u = get_user(msg.from_user, msg.chat.id)

    if item not in u.get("inventory", []):
        return bot.send_message(msg.chat.id, "❌ You don't have that food")

    heal = FOODS[item]["heal"]

    u["hunger"] = min(100, u["hunger"] + heal)
    u["inventory"].remove(item)

    save()

    bot.send_message(
        msg.chat.id,
        f"🍗 Ate {item}\n❤️ Hunger: {u['hunger']}/100"
    )






def is_admin(user_id, chat_id):
    chat_id = str(chat_id)
    user_id = str(user_id)

    if chat_id not in group_data:
        return False

    data = group_data[chat_id]

    return user_id == data["owner"] or user_id in data["admins"]





@bot.message_handler(commands=['addadmin'])
def add_admin(msg):
    chat_id = str(msg.chat.id)
    uid = str(msg.from_user.id)

    if chat_id not in group_data:
        return

    if group_data[chat_id]["owner"] != uid:
        return bot.send_message(chat_id, "❌ Only owner can add admin")

    if not msg.reply_to_message:
        return bot.send_message(chat_id, "Reply to user")

    target = str(msg.reply_to_message.from_user.id)

    if target not in group_data[chat_id]["admins"]:
        group_data[chat_id]["admins"].append(target)

    save()
    bot.send_message(chat_id, "✅ Admin added")





@bot.message_handler(commands=['removeadmin'])
def remove_admin(msg):
    chat_id = str(msg.chat.id)
    uid = str(msg.from_user.id)

    if chat_id not in group_data:
        return

    if group_data[chat_id]["owner"] != uid:
        return bot.send_message(chat_id, "❌ Only owner can remove admin")

    if not msg.reply_to_message:
        return bot.send_message(chat_id, "Reply to user")

    target = str(msg.reply_to_message.from_user.id)

    # ❌ cannot remove owner
    if target == group_data[chat_id]["owner"]:
        return bot.send_message(chat_id, "❌ Cannot remove owner")

    if target in group_data[chat_id]["admins"]:
        group_data[chat_id]["admins"].remove(target)

    save()
    bot.send_message(chat_id, "❌ Admin removed")




@bot.message_handler(commands=['mygroups'])
def mygroups(msg):
    if msg.chat.type != "private":
        return

    uid = str(msg.from_user.id)

    my_groups = []

    for gid, data in group_data.items():
        if data["owner"] == uid:
            try:
                chat = bot.get_chat(int(gid))
                my_groups.append(chat.title)
            except:
                pass

    if not my_groups:
        return bot.send_message(msg.chat.id, "❌ You don’t own any groups")

    text = "📋 <b>Your Groups:</b>\n\n"
    for g in my_groups:
        text += f"• {g}\n"

    bot.send_message(msg.chat.id, text, parse_mode="HTML")






@bot.message_handler(commands=['owner'])
def claim(msg):
    chat_id = str(msg.chat.id)
    uid = str(msg.from_user.id)

    if msg.chat.type == "private":
        return

    # 🔐 ONLY telegram admins can claim
    try:
        admins = bot.get_chat_administrators(msg.chat.id)
        admin_ids = [str(a.user.id) for a in admins]

        if uid not in admin_ids:
            return  # ❌ silent block (no hint)

    except:
        return

    # 🔒 already claimed → only telegram admin can override
    if chat_id in group_data:
        if group_data[chat_id]["owner"] != uid:
            return  # ❌ silent (no info leak)

    group_data[chat_id] = {
        "owner": uid,
        "admins": []
    }

    save()
    bot.send_message(msg.chat.id, "👑 Bot owner set")






@bot.message_handler(commands=['admin'])
def admin_panel(msg):
    if msg.from_user.is_bot:
        return

    admin_id = str(msg.from_user.id)
    now = time.time()

    # 🔥 cooldown
    if admin_id in admin_cd and now - admin_cd[admin_id] < 2:
        return

    admin_cd[admin_id] = now

    if not is_admin(msg.from_user.id, msg.chat.id):
        return bot.send_message(msg.chat.id, "❌ Not authorized")

    bot.send_message(msg.chat.id, """
👑 ADMIN PANEL

/ban (reply)
/unban (reply)
/broadcast <msg>
/broadcastpvt <msg>

Use carefully ⚠️
""")
    



@bot.message_handler(commands=['ban'])
def ban_user(msg):
    if msg.from_user.is_bot:
        return

    admin_id = str(msg.from_user.id)
    now = time.time()

    # 🔥 cooldown (admin)
    if admin_id in admin_cd and now - admin_cd[admin_id] < 2:
        return
    admin_cd[admin_id] = now

    # 🔒 admin check
    if not is_admin(msg.from_user.id, msg.chat.id):
        return bot.send_message(msg.chat.id, "❌ Not allowed")

    # 🔁 must reply
    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to user")

    chat_id = str(msg.chat.id)
    target_id = str(msg.reply_to_message.from_user.id)

    # 🔒 protect owner (ADD HERE)
    if target_id == group_data.get(chat_id, {}).get("owner"):
        return  # silent block

    # ❌ cannot ban yourself
    if target_id == admin_id:
        return bot.send_message(msg.chat.id, "❌ Can't ban yourself")

    # 🚫 already banned
    banned.setdefault(chat_id, {})
    if target_id in banned[chat_id]:
        return bot.send_message(msg.chat.id, "⚠️ Already banned")

    # 🚫 apply ban
    banned[chat_id][target_id] = True

    save()
    bot.send_message(msg.chat.id, "🚫 User banned")


@bot.message_handler(commands=['unban'])
def unban_user(msg):
    if msg.from_user.is_bot:
        return

    admin_id = str(msg.from_user.id)
    now = time.time()

    # 🔥 cooldown (admin)
    if admin_id in admin_cd and now - admin_cd[admin_id] < 2:
        return

    admin_cd[admin_id] = now

    if not is_admin(msg.from_user.id, msg.chat.id):
        return bot.send_message(msg.chat.id, "❌ Not allowed")

    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to user")

    chat_id = str(msg.chat.id)
    target_id = str(msg.reply_to_message.from_user.id)

    banned.setdefault(chat_id, {})
    banned[chat_id].pop(target_id, None)

    save()
    bot.send_message(msg.chat.id, "✅ User unbanned")



@bot.message_handler(commands=['broadcast'])
def broadcast(msg):
    if msg.from_user.is_bot:
        return

    admin_id = str(msg.from_user.id)
    now = time.time()

    # 🔥 ONLY BOT OWNER ALLOWED
    if admin_id not in ADMIN_IDS:
        return bot.send_message(msg.chat.id, "🚫 Only bot owner can use this")

    # ⏳ cooldown (optional)
    if admin_id in admin_cd and now - admin_cd[admin_id] < 2:
        return

    admin_cd[admin_id] = now

    # 🔥 message parsing
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /broadcast message")

    text = parts[1].strip()

    count = 0

    # 📢 send to all chats
    for chat_id in list(users.keys()):
        try:
            bot.send_message(chat_id, text, parse_mode="HTML")
            count += 1
            time.sleep(0.05)  # anti rate limit
        except:
            pass

    bot.send_message(msg.chat.id, f"📢 Sent to {count} chats")


@bot.message_handler(commands=['broadcastpvt'])
def broadcast_pvt(msg):
    if msg.from_user.is_bot:
        return

    admin_id = str(msg.from_user.id)
    now = time.time()

    # 🔥 ONLY BOT OWNER
    if admin_id not in ADMIN_IDS:
        return bot.send_message(msg.chat.id, "🚫 Only bot owner can use this")

    # ⏳ cooldown
    if admin_id in admin_cd and now - admin_cd[admin_id] < 2:
        return
    admin_cd[admin_id] = now 

    # 🔥 safer text parsing
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /broadcastpvt message")

    text = parts[1].strip()

    sent = 0
    failed = 0
    sent_users = set()  # 🔥 prevent duplicates

    for chat_id in list(users.keys()):
        for user_id in users[chat_id]:

            # 🚫 skip duplicates
            if user_id in sent_users:
                continue
            sent_users.add(user_id)

            try:
                bot.send_message(int(user_id), text, parse_mode="HTML")
                sent += 1
                time.sleep(0.03)  # anti rate limit
            except:
                failed += 1

    bot.send_message(
        msg.chat.id,
        f"📩 Broadcast Complete\n✅ Sent: {sent}\n❌ Failed: {failed}"
    )



@bot.message_handler(commands=['deposit'])
def deposit(msg):
    print("\n====== DEPOSIT START ======")

    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    print("CHAT_ID:", chat_id, "| TYPE:", type(chat_id))
    print("USER_ID:", uid)

    u = get_user(msg.from_user, msg.chat.id)

    # 💀 dead check
    if check_dead_block(msg, uid):
        print("❌ USER DEAD")
        return

    parts = msg.text.split()
    print("INPUT:", parts)

    if len(parts) < 2:
        print("❌ NO AMOUNT")
        return bot.send_message(msg.chat.id, "Usage: /deposit amount")

    try:
        amt = int(parts[1])
        print("AMOUNT:", amt)
    except:
        print("❌ INVALID AMOUNT FORMAT")
        return bot.send_message(msg.chat.id, "Invalid amount")

    # 🔒 minimum deposit
    if amt < 100:
        print("❌ BELOW MINIMUM")
        return bot.send_message(msg.chat.id, "❌ Minimum deposit is 100")

    if u["money"] < amt:
        print("❌ NOT ENOUGH MONEY")
        return bot.send_message(msg.chat.id, "❌ Not enough cash")

    # 💸 tax
    tax = max(1, int(amt * 0.01))
    final = amt - tax

    print("TAX:", tax)
    print("FINAL DEPOSIT:", final)

    # 💰 apply transaction
    u["money"] -= amt
    u["bank"] += final

    print("USER MONEY AFTER:", u["money"])
    print("USER BANK AFTER:", u["bank"])

    # 🔥 CHECK JOB OWNER BEFORE PAY
    print("JOB_OWNER DATA:", job_owner.get(chat_id))
    print("BANK OWNER:", job_owner.get(chat_id, {}).get("bank"))

    # 🏦 pay job
    print("➡️ CALLING pay_job()")
    pay_job(chat_id, "bank", tax)

    save()

    print("====== DEPOSIT END ======\n")

    bot.send_message(
        msg.chat.id,
        f"🏦 Deposited: {final}\n💸 Fee: {tax} (1%)\n📉 Min deposit: 100"
    ) 








@bot.message_handler(commands=['give'])
def give(msg):
    chat_id = ensure_chat(msg.chat.id)
    sender = str(msg.from_user.id)

    # 💀 dead / banned check
    if check_dead_block(msg, sender):
        return

    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to user")

    if msg.reply_to_message.from_user.is_bot:
        return bot.send_message(msg.chat.id, "🤖 Can't send to bots")

    parts = msg.text.split()
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /give amount")

    try:
        amt = int(parts[1])
    except:
        return bot.send_message(msg.chat.id, "Invalid amount")

    # 🔒 VALIDATION
    if amt <= 0:
        return bot.send_message(msg.chat.id, "❌ Amount must be positive")

    if amt > 1_000_000:
        return bot.send_message(msg.chat.id, "❌ Max limit is 1,000,000")

    receiver = str(msg.reply_to_message.from_user.id)

    if sender == receiver:
        return bot.send_message(msg.chat.id, "❌ Can't send to yourself")

    u1 = get_user(msg.from_user, msg.chat.id)

    if u1["money"] < amt:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    # ⏳ COOLDOWN
    give_cd.setdefault(chat_id, {})
    now = time.time()

    if sender in give_cd[chat_id] and now - give_cd[chat_id][sender] < 5:
        return bot.send_message(msg.chat.id, "⏳ Wait before sending again")

    give_cd[chat_id][sender] = now

    # 🔥 TRADE SYSTEM SAFETY
    trades.setdefault(chat_id, {})

    # ❌ sender already has pending
    if sender in trades[chat_id]:
        return bot.send_message(msg.chat.id, "❌ You already have a pending transfer")

    # ❌ receiver already has pending
    for t in trades[chat_id].values():
        if t["to"] == receiver:
            return bot.send_message(msg.chat.id, "❌ User already has a pending request")

    # ✅ store trade
    trades[chat_id][sender] = {
        "to": receiver,
        "amount": amt
    }

    bot.send_message(
        msg.chat.id,
        f"💸 Transfer request sent!\nAmount: {amt}\nUse /accept or /decline"
    )
    

@bot.message_handler(commands=['accept'])
def accept(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 🚫 ONLY block banned (NOT dead)
    if uid in banned.get(chat_id, {}):
        return bot.send_message(msg.chat.id, "🚫 You are banned from this game")

    trades.setdefault(chat_id, {})
    dead.setdefault(chat_id, {})

    now = time.time()

    for sender, t in list(trades[chat_id].items()):

        # ✅ only accept your own incoming trade
        if t.get("to") != uid:
            continue

        amt = t.get("amount", 0)

        # ⏳ expiry check
        if "expires" in t and now > t["expires"]:
            del trades[chat_id][sender]
            continue

        # ❌ invalid users safety
        if sender not in users.get(chat_id, {}) or uid not in users.get(chat_id, {}):
            del trades[chat_id][sender]
            return bot.send_message(msg.chat.id, "❌ Invalid users")

        u1 = users[chat_id][sender]
        u2 = users[chat_id][uid]

        # ❌ prevent dead sender exploit
        if sender in dead[chat_id]:
            del trades[chat_id][sender]
            return bot.send_message(msg.chat.id, "❌ Sender is dead, trade cancelled")

        # ❌ sanity checks
        if amt <= 0:
            del trades[chat_id][sender]
            return bot.send_message(msg.chat.id, "❌ Invalid amount")

        if u1["money"] < amt:
            del trades[chat_id][sender]
            return bot.send_message(msg.chat.id, "❌ Sender has no money")

        # 💰 transfer
        u1["money"] -= amt
        u2["money"] += amt

        # 💥 bankruptcy check
        check_bankrupt(chat_id, sender)
        check_bankrupt(chat_id, uid)

        # 🧹 cleanup
        del trades[chat_id][sender]
        save()

        # 💀 optional message if receiver is dead
        if uid in dead[chat_id]:
            return bot.send_message(
                msg.chat.id,
                f"💰 Transfer received (while dead)\nFrom: {u1['name']}\nAmount: {amt}"
            )

        return bot.send_message(
            msg.chat.id,
            f"💰 Transfer received!\nFrom: {u1['name']}\nAmount: {amt}"
        )

    bot.send_message(msg.chat.id, "❌ No pending transfer")





@bot.message_handler(commands=['decline'])
def decline(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 💀 dead / banned check
    if check_dead_block(msg, uid):
        return

    trades.setdefault(chat_id, {})
    now = time.time()

    for sender, t in list(trades[chat_id].items()):
        # only decline your own incoming trade
        if t.get("to") != uid:
            continue

        # 🔥 remove expired trades automatically
        if "expires" in t and now > t["expires"]:
            del trades[chat_id][sender]
            continue

        # 🧹 delete trade
        del trades[chat_id][sender]

        # optional: show sender name safely
        sender_name = users.get(chat_id, {}).get(sender, {}).get("name", "Unknown")

        save()

        return bot.send_message(
            msg.chat.id,
            f"❌ Transfer declined\nFrom: {sender_name}"
        )

    bot.send_message(msg.chat.id, "❌ No pending request")



@bot.message_handler(commands=['map'])
def map_cmd(msg):
    uid = str(msg.from_user.id)
    u = get_user(msg.from_user, msg.chat.id)

    current = u["zone"]
    paths = CONNECTIONS.get(current, [])

    caption = f"""
🗺️ GAME MAP

📍 You are at: {current.upper()}
➡️ You can go to: {", ".join(paths)}

Use: /travel <zone>
"""

    try:
        with open("map.jpg", "rb") as photo:
            bot.send_photo(msg.chat.id, photo, caption=caption)
    except:
        bot.send_message(msg.chat.id, caption + "\n\n⚠️ Map image not found")




@bot.message_handler(commands=['travel'])
def travel(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 

    if check_dead_block(msg, uid):
        return

    parts = msg.text.split()

    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /travel zone")

    zone = parts[1].lower()

    if zone not in ZONES:
        return bot.send_message(msg.chat.id, "❌ Invalid location\nUse /map")

    u = get_user(msg.from_user, msg.chat.id)
    current = u["zone"]

    # 🔥 NEW: CONNECTION CHECK
    if zone not in CONNECTIONS.get(current, []):
        return bot.send_message(
            msg.chat.id,
            f"❌ You can't go directly from {current} to {zone}\nUse /map"
        )

    # already there
    if current == zone:
        return bot.send_message(msg.chat.id, f"📍 You are already in {zone}")

    # move
    u["zone"] = zone
    reduce_hunger(chat_id, uid, 2)
    save()

    bot.send_message(msg.chat.id, f"🗺️ Traveled from {current} → {zone}")




def number_pad(action):
    kb = InlineKeyboardMarkup(row_width=3)

    nums = ["1","2","3","4","5","6","7","8","9"]  # 🔥 removed 0

    for i in range(0,9,3):
        kb.row(
            InlineKeyboardButton(nums[i], callback_data=f"{action}_{nums[i]}"),
            InlineKeyboardButton(nums[i+1], callback_data=f"{action}_{nums[i+1]}"),
            InlineKeyboardButton(nums[i+2], callback_data=f"{action}_{nums[i+2]}")
        )

    kb.row(
        InlineKeyboardButton("❌", callback_data=f"{action}_clear"),
        InlineKeyboardButton("0", callback_data=f"{action}_0"),
        InlineKeyboardButton("✔️", callback_data=f"{action}_ok")
    )

    return kb

@bot.message_handler(commands=['withdraw'])
def withdraw(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # ❌ removed dead block

    withdraw_input[uid] = ""

    bot.send_message(
        msg.chat.id,
        "💸 Enter amount to withdraw:\n\n0",
        reply_markup=number_pad("wd")
    )

def add_xp(chat_id, uid, amt):
    u = users[chat_id][uid]
    u["xp"] += amt
    if u["xp"] >= u["level"] * 100:
        u["xp"] = 0
        u["level"] += 1



@bot.callback_query_handler(func=lambda c: c.data.startswith("wd_"))
def withdraw_cb(call):
    uid = str(call.from_user.id)
    chat_id = str(call.message.chat.id)

    withdraw_input.setdefault(uid, "")
    action = call.data.split("_")[1]

    if action == "clear":
        withdraw_input[uid] = ""

    elif action == "ok":
        if withdraw_input[uid] == "":
            return bot.answer_callback_query(call.id, "Enter amount")

        if withdraw_input[uid] == "0":
            return bot.answer_callback_query(call.id, "Invalid amount")

        amt = int(withdraw_input[uid])
        u = get_user(call.from_user, chat_id)

        if u["bank"] < amt:
            return bot.answer_callback_query(call.id, "Not enough bank")

        if amt <= 0:
            return bot.answer_callback_query(call.id, "Invalid amount")

        u["bank"] -= amt
        u["money"] += amt

        withdraw_input[uid] = ""
        save()

        bot.answer_callback_query(call.id, "Withdrawn")

        safe_edit(
            call.message.chat.id,
            call.message.message_id,
            f"💸 Withdrawn: {amt}"
        )

    else:
        if len(withdraw_input[uid]) >= 9:
            return bot.answer_callback_query(call.id, "Max 9 digits")

        if withdraw_input[uid] == "0":
            withdraw_input[uid] = action
        else:
            withdraw_input[uid] += action

    current = withdraw_input[uid] if withdraw_input[uid] else "0"

    safe_edit(
        call.message.chat.id,
        call.message.message_id,
        f"💸 Enter amount to withdraw:\n\n{current}",
        reply_markup=number_pad("wd")
    )

    bot.answer_callback_query(call.id)










@bot.message_handler(commands=['daily','reward'])
def daily(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 

    # 🔥 ensure dict
    daily_cd.setdefault(chat_id, {})

    # 💀 dead check
    if check_dead_block(msg, uid):
        return

    now = time.time()

    # ⏳ cooldown (24h)
    if uid in daily_cd[chat_id] and now - daily_cd[chat_id][uid] < 86400:
        left = int(86400 - (now - daily_cd[chat_id][uid]))

        hours = left // 3600
        minutes = (left % 3600) // 60

        return bot.send_message(
            msg.chat.id,
            f"⏳ Come back in {hours}h {minutes}m"
        )

    u = get_user(msg.from_user, msg.chat.id)

    reward = 3000
    u["money"] += reward

    # 🔥 FIX: store per chat
    daily_cd[chat_id][uid] = now

    save()

    bot.send_message(
        msg.chat.id,
        f"🎁 Daily reward claimed!\n💰 +{reward}"
    )









def check_bankrupt(chat_id, uid):
    u = users[chat_id][uid]
    total = u["money"] + u.get("bank", 0)

    if total <= -100000:
        users[chat_id][uid].update({
            "money": 3000,
            "bank": 0,
            "xp": 0,
            "level": 1,
            "zone": "slums",
            "weapon": None,
            "armor": False,
            "gang": None,
            "hunger": 100,
            "inventory": [],
            "stats": {
                "strength": 5,
                "muscles": 5,
                "stamina": 5,
                "experience": 0,
                "power": 5
            }
        })
        return True
    return False




@bot.message_handler(commands=['setjob'])
def set_job(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 🔒 admin check
    if not is_admin(msg.from_user.id, msg.chat.id):
        return bot.send_message(msg.chat.id, "🚫 Only admin can assign jobs")

    # 🔁 must reply
    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to user")

    parts = msg.text.split()
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /setjob jobname")

    job = parts[1].lower().strip()
    target_user = msg.reply_to_message.from_user
    target_id = str(target_user.id)

    VALID_JOBS = [
        "smith", "armor", "protect", "bank",
        "police", "military", "harbor", "casino", "food",
        "breaker"
    ]

    if job not in VALID_JOBS:
        return bot.send_message(msg.chat.id, "❌ Invalid job")

    job_owner.setdefault(chat_id, {})

    # 🔥 FIX: REGISTER USER BEFORE ASSIGNING JOB
    get_user(target_user, msg.chat.id)

    # 🔁 overwrite check
    old = job_owner[chat_id].get(job)
    job_owner[chat_id][job] = target_id

    save()

    if old and old != target_id:
        bot.send_message(
            msg.chat.id,
            f"🔁 {job.title()} reassigned to {target_user.first_name}"
        )
    else:
        bot.send_message(
            msg.chat.id,
            f"👑 {job.title()} assigned to {target_user.first_name}"
        )





def pay_job(chat_id, job, amount):
    print("\n====== PAY_JOB START ======")

    chat_id = str(chat_id)
    print("CHAT_ID:", chat_id, "| TYPE:", type(chat_id))

    # ❌ invalid amount
    if not isinstance(amount, (int, float)) or amount <= 0:
        print("❌ INVALID AMOUNT:", amount)
        return

    # 🔒 normalize job
    job = str(job).lower().strip()
    print("JOB:", job)

    # 📦 get owner
    print("JOB_OWNER FULL:", job_owner.get(chat_id))
    owner = job_owner.get(chat_id, {}).get(job)

    if not owner:
        print("❌ NO OWNER FOUND FOR JOB:", job)
        print("====== PAY_JOB END ======\n")
        return

    print("OWNER:", owner)

    users.setdefault(chat_id, {})
    chat_users = users[chat_id]

    print("USERS KEYS:", list(chat_users.keys()))

    # ❌ DO NOT CREATE USER HERE
    user = chat_users.get(owner)
    if not user:
        print("❌ OWNER NOT REGISTERED IN USERS → PAYMENT SKIPPED")
        print("====== PAY_JOB END ======\n")
        return

    # 💰 payout
    before = user.get("money", 0)
    user["money"] = before + int(amount)

    print(f"✅ MONEY ADDED: {amount}")
    print(f"BEFORE: {before} → AFTER: {user['money']}")

    print("====== PAY_JOB END ======\n")


@bot.message_handler(commands=['joblist'])
def joblist(msg):
    chat_id = ensure_chat(msg.chat.id)

    jobs = job_owner.get(chat_id, {})

    if not jobs:
        return bot.send_message(msg.chat.id, "❌ No jobs assigned")

    text = "👑 JOB LIST\n\n"

    for job, uid in jobs.items():
        user = users.get(chat_id, {}).get(uid)

        if user:
            name = user["name"]
        else:
            name = "Unknown"

        text += f"🔹 {job} → {name}\n"

    bot.send_message(msg.chat.id, text)




@bot.message_handler(commands=['removejob'])
def removejob(msg):
    if not is_admin(msg.from_user.id, msg.chat.id):
        return bot.send_message(msg.chat.id, "❌ Not allowed")

    parts = msg.text.split()
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /removejob job")

    job = parts[1].lower()
    chat_id = ensure_chat(msg.chat.id)

    if job not in job_owner.get(chat_id, {}):
        return bot.send_message(msg.chat.id, "❌ Job not assigned")

    del job_owner[chat_id][job]
    save()

    bot.send_message(msg.chat.id, f"❌ {job} removed")



@bot.message_handler(commands=['myjob'])
def myjob(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    jobs = job_owner.get(chat_id, {})

    found = []

    for job, owner in jobs.items():
        if owner == uid:
            found.append(job)

    if not found:
        return bot.send_message(msg.chat.id, "❌ You have no job")

    bot.send_message(msg.chat.id, f"💼 Your job(s): {', '.join(found)}")





# ===== MISSIONS =====
@bot.message_handler(commands=['mission'], chat_types=['private','group','supergroup'])
def mission(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id)

    if check_dead_block(msg, uid):
        return

    mission_cd.setdefault(chat_id, {})

    now = time.time()

    # ⏳ 2 min cooldown (120 sec)
    if uid in mission_cd[chat_id] and now - mission_cd[chat_id][uid] < 120:
        left = int(120 - (now - mission_cd[chat_id][uid]))
        return bot.send_message(msg.chat.id, f"⏳ Wait {left}s before new mission")

    u = get_user(msg.from_user, msg.chat.id)

    z = ZONES[u["zone"]]

    m = {
        "reward": random.randint(*z["reward"]),
        "risk": z["risk"]
    }

    missions.setdefault(chat_id, {})
    missions[chat_id][uid] = m

    # ✅ set cooldown
    mission_cd[chat_id][uid] = now

    save()

    bot.send_message(msg.chat.id, f"🧠 Reward {m['reward']} | Risk {m['risk']}")

@bot.message_handler(commands=['do'], chat_types=['private','group','supergroup'])
def do(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 

    if check_dead_block(msg, uid):
        return

    # 🔥 FIX: per chat missions
    if chat_id not in missions or uid not in missions[chat_id]:
        return bot.send_message(msg.chat.id, "No mission")

    m = missions[chat_id][uid]

    # 🔥 get user properly
    u = get_user(msg.from_user, msg.chat.id)

    if random.random() > m["risk"]:
        u["money"] += m["reward"]
        add_xp(chat_id, uid, 30)
        bot.send_message(msg.chat.id, f"✅ +{m['reward']}")
    else:
        loss = int(m["reward"] * 0.3)
        u["money"] -= loss
        bot.send_message(msg.chat.id, f"❌ -{loss}")

    # 🔥 delete mission properly
    del missions[chat_id][uid]

    save()

# ===== SHOP =====
@bot.message_handler(commands=['shop'])
def shop(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 

    if check_dead_block(msg, uid):
        return

    kb = InlineKeyboardMarkup()

    kb.add(InlineKeyboardButton("🔫 Weapons", callback_data="shop_weapons"))
    kb.add(InlineKeyboardButton("💥 Breakers", callback_data="shop_breakers"))
    kb.add(InlineKeyboardButton("🛡 Armor", callback_data="shop_armor"))
    kb.add(InlineKeyboardButton("🛡 Protect", callback_data="shop_protect"))

    bot.send_message(msg.chat.id, "🛒 Shop Categories:", reply_markup=kb)

@bot.callback_query_handler(
    func=lambda c:
    not c.data.startswith("mine_")
    and not c.data.startswith("candy_")
    and not c.data.startswith("minecollect_")
)
def cb(call):
    uid = str(call.from_user.id)
    chat_id = str(call.message.chat.id)

    now = time.time()

    if uid in button_cd:

        if now - button_cd[uid] < 0.7:

            return bot.answer_callback_query(
                call.id,
                "Slow down"
            )

    button_cd[uid] = now


    if call.data == "done":
        return bot.answer_callback_query(
            call.id,
            "Game finished"
        )

    if call.data.startswith("wd_"):
        return 
    
    # 💀 dead check (AFTER withdraw)
    # 💀 block only dangerous actions
    BLOCK_WHEN_DEAD = [
        "buy_",
        "buybreaker_",
        "protect_",
        "fight_",
        "rpsbot_",
        "slotspin_"
    ]

    if any(call.data.startswith(x) for x in BLOCK_WHEN_DEAD):
        if chat_id in dead and uid in dead[chat_id]:
            bot.answer_callback_query(call.id, "💀 You are dead")
            return

    u = get_user(call.from_user, call.message.chat.id)

    # =========================
    # 🛒 SHOP CATEGORY MENUS
    # =========================
    if call.data == "shop_weapons":
        kb = InlineKeyboardMarkup()
        for w, data in WEAPONS.items():
            kb.add(InlineKeyboardButton(f"{w} 💰{data['price']}", callback_data=f"buy_{w}"))
        kb.add(InlineKeyboardButton("⬅ Back", callback_data="shop_main"))
        safe_edit(
            chat_id,
            call.message.message_id,
            "🔫 Weapons:",
            reply_markup=kb
        )
        return

    if call.data == "shop_breakers":
        kb = InlineKeyboardMarkup()
        for w, data in BREAKER_WEAPONS.items():
            kb.add(InlineKeyboardButton(f"{w} 💥 💰{data['price']}", callback_data=f"buybreaker_{w}"))
        kb.add(InlineKeyboardButton("⬅ Back", callback_data="shop_main"))
        safe_edit(
            chat_id,
            call.message.message_id,
            "💥 Breakers:",
            reply_markup=kb
        )
        return

    if call.data == "shop_armor":
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🛡 Armor 💰3000", callback_data="buy_armor"))
        kb.add(InlineKeyboardButton("⬅ Back", callback_data="shop_main"))
        safe_edit(
            chat_id,
            call.message.message_id,
            "🛡 Armor:",
            reply_markup=kb
        )
        return

    if call.data == "shop_protect":
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🛡 5 min 💰2000", callback_data="protect_300"))
        kb.add(InlineKeyboardButton("🛡 10 min 💰4000", callback_data="protect_600"))
        kb.add(InlineKeyboardButton("🛡 15 min 💰6000", callback_data="protect_900"))
        kb.add(InlineKeyboardButton("⬅ Back", callback_data="shop_main"))
        safe_edit(
            chat_id,
            call.message.message_id,
            "🛡 Protection:",
            reply_markup=kb
        )
        return

    if call.data == "shop_main":
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔫 Weapons", callback_data="shop_weapons"))
        kb.add(InlineKeyboardButton("💥 Breakers", callback_data="shop_breakers"))
        kb.add(InlineKeyboardButton("🛡 Armor", callback_data="shop_armor"))
        kb.add(InlineKeyboardButton("🛡 Protect", callback_data="shop_protect"))
        safe_edit(
            chat_id,
            call.message.message_id,
            "🛒 Shop Categories:",
            reply_markup=kb
        )
        return


    # =========================
    # 🛡️ PROTECTION SYSTEM
    # =========================
    if call.data.startswith("protect_"):
        try:
            duration = int(call.data.split("_")[1])
        except:
            return bot.answer_callback_query(call.id, "Invalid")

        prices = {300: 2000, 600: 4000, 900: 6000}
        price = prices.get(duration)

        if not price:
            return bot.answer_callback_query(call.id, "Invalid option")

        shield.setdefault(chat_id, {})

        if uid in shield[chat_id]:
            left = int(shield[chat_id][uid] - time.time())
            if left > 0:
                return bot.answer_callback_query(call.id, "Already protected")
            else:
                del shield[chat_id][uid]

        if u["money"] < price:
            return bot.answer_callback_query(call.id, "❌ Not enough money")

        u["money"] -= price
        pay_job(chat_id, "protect", price)

        shield[chat_id][uid] = time.time() + duration

        save()
        bot.answer_callback_query(call.id, "🛡️ Protection activated!")
        return


    # =========================
    # 💥 BREAKER WEAPONS
    # =========================
    if call.data.startswith("buybreaker_"):
        item = call.data.split("_")[1]

        if item in BREAKER_WEAPONS:
            price = BREAKER_WEAPONS[item]["price"]

            if u["money"] >= price:
                u["money"] -= price
                pay_job(chat_id, "breaker", price)

                u["weapon"] = item
                save()

                bot.answer_callback_query(call.id, f"💥 {item} equipped")
            else:
                bot.answer_callback_query(call.id, "❌ Not enough money")

        return


    # =========================
    # 🛒 NORMAL SHOP
    # =========================
    if call.data.startswith("buy_"):
        item = call.data.split("_")[1]

        # 🛡️ ARMOR
        if item == "armor":
            if u["money"] >= ARMOR["price"]:
                u["money"] -= ARMOR["price"]
                pay_job(chat_id, "armor", ARMOR["price"])

                u["armor"] = True
                save()

                bot.answer_callback_query(call.id, "🛡️ Armor purchased")
            else:
                bot.answer_callback_query(call.id, "❌ Not enough money")
            return

        # 🔫 WEAPONS
        if item in WEAPONS:
            price = WEAPONS[item]["price"]

            if u["money"] >= price:
                u["money"] -= price
                pay_job(chat_id, "smith", price)

                u["weapon"] = item
                save()

                bot.answer_callback_query(call.id, f"🔫 {item} equipped")
            else:
                bot.answer_callback_query(call.id, "❌ Not enough money")

        return
    
    # =========================
    # 🍗 FOOD SYSTEM (FINAL FIXED)
    # =========================
    if call.data.startswith("buyfood"):
        item = call.data.replace("buyfood", "", 1)

        if item not in FOODS:
            return bot.answer_callback_query(call.id, "❌ Invalid food")

        price = FOODS[item]["price"]

    # 🎒 inventory check FIRST
        u.setdefault("inventory", [])
        if len(u["inventory"]) >= 20:
            return bot.answer_callback_query(call.id, "🎒 Inventory full")

        if u["money"] < price:
            return bot.answer_callback_query(call.id, "❌ Not enough money")

    # 💰 deduct
        u["money"] -= price

    # 💼 pay seller
        pay_job(chat_id, "food", price)

    # 🎒 add item
        u["inventory"].append(item)

        save()
        bot.answer_callback_query(call.id, f"🍗 Bought {item}")

        return
    


    

    # =========================
    # ⚔️ ARENA FIGHT (FINAL FIXED)
    # =========================
    if call.data.startswith("fight_"):
        try:
            _, uid1, uid2 = call.data.split("_")

            chat_id = str(call.message.chat.id)
            uid = str(call.from_user.id)

        # ❌ only target can click
            if uid != uid2:
                return bot.answer_callback_query(call.id, "❌ Not your duel")

        # 💀 dead check
            if uid1 in dead.get(chat_id, {}) or uid2 in dead.get(chat_id, {}):
                return bot.answer_callback_query(call.id, "💀 Player dead")

            attacker = users[chat_id][uid1]
            defender = users[chat_id][uid2]

            attacker.setdefault("duel", {"wins":0,"losses":0,"total":0})
            defender.setdefault("duel", {"wins":0,"losses":0,"total":0})

            s1 = attacker["stats"]
            s2 = defender["stats"]

            p1 = s1["strength"] + s1["muscles"] + s1["power"] + random.randint(0, 10)
            p2 = s2["strength"] + s2["muscles"] + s2["power"] + random.randint(0, 10)

            if p1 > p2:
                winner, loser = attacker, defender
            else:
                winner, loser = defender, attacker

            reward = random.randint(1000, 3000)

            winner["money"] += reward
            winner["stats"]["experience"] += 5
            loser["stats"]["experience"] += 2

            winner["duel"]["wins"] += 1
            loser["duel"]["losses"] += 1
            winner["duel"]["total"] += 1
            loser["duel"]["total"] += 1

            reduce_hunger(chat_id, uid1, 6)
            reduce_hunger(chat_id, uid2, 6)

            duel_cd.setdefault(chat_id, {})
            duel_cd[chat_id][uid1] = time.time()
            duel_cd[chat_id][uid2] = time.time()

            save()

            bot.answer_callback_query(call.id)

            safe_edit(
                call.message.chat.id,
                call.message.message_id,
                f"""
            ⚔️ <b>FIGHT RESULT</b>

            🏆 Winner: <b>{html.escape(winner['name'])}</b>
            💰 Reward: {reward}
            """,
                parse_mode="HTML"
            )
        except Exception as e:
            print("FIGHT ERROR:", e)
            bot.answer_callback_query(call.id, "⚠️ Error")
            return
    

    #=============================
    #rps
    #=============================
    if call.data.startswith("rpsbot_"):
        _, uid, move = call.data.split("_")
        chat_id = str(call.message.chat.id)

        key = f"{chat_id}_{uid}_bot"

        if key not in rps_games:
            return bot.answer_callback_query(call.id, "Expired")

        game = rps_games[key]

    # ⏳ timeout
        if time.time() - game["time"] > 30:
        # refund on timeout
            users[chat_id][uid]["money"] += game["amt"]
            del rps_games[key]
            return bot.answer_callback_query(call.id, "⏳ Expired (refunded)")

        bot_move = random.choice(["rock", "paper", "scissors"])
        u = users[chat_id][uid]
        amt = game["amt"]

        def win(a, b):
            return (a == "rock" and b == "scissors") or \
                   (a == "paper" and b == "rock") or \
                   (a == "scissors" and b == "paper")

    # 🎮 RESULT LOGIC (BET ALREADY LOCKED)
        if move == bot_move:
            u["money"] += amt  # refund
            result = "🤝 Draw (bet refunded)"

        elif win(move, bot_move):
            u["money"] += amt * 2  # win 2x
            result = f"🏆 You win {amt*2}!"

        else:
        # lose → no refund (already deducted)
            result = f"❌ You lost {amt}"

    # 💼 casino earnings (optional, you can reduce if needed)
        pay_job(chat_id, "casino", amt)

        del rps_games[key]
        save()

        bot.answer_callback_query(call.id)

        safe_edit(
            call.message.chat.id,
            call.message.message_id,
            f"🎰 <b>RPS vs Bot</b>\n\n"
            f"👤 You: {move}\n"
            f"🤖 Bot: {bot_move}\n\n"
            f"{result}",
            parse_mode="HTML"
        )

        return
    
    #=========================================
    #slot game 
    #=========================================
    if call.data.startswith("slotspin_"):
        _, uid = call.data.split("_")
        chat_id = str(call.message.chat.id)
        clicker = str(call.from_user.id)

    # ❌ only owner can click
        if clicker != uid:
            return bot.answer_callback_query(call.id, "Not your game")

        key = f"{chat_id}_{uid}"

        if key not in slot_games:
            return bot.answer_callback_query(call.id, "Game expired")

        game = slot_games[key]

    # ⏳ timeout (30s)
        if time.time() - game["time"] > 30:
            users[chat_id][uid]["money"] += game["bet"]  # refund
            del slot_games[key]
            return bot.answer_callback_query(call.id, "⏳ Expired (refunded)")

        bet = game["bet"]
        u = users[chat_id][uid]

    # 🎰 spin result
        r1 = random.choice(SLOT_SYMBOLS)
        r2 = random.choice(SLOT_SYMBOLS)
        r3 = random.choice(SLOT_SYMBOLS)

        result = f"{r1} | {r2} | {r3}"

        win = 0

        if r1 == r2 == r3:
            win = bet * 5
        elif r1 == r2 or r2 == r3 or r1 == r3:
            win = bet * 2

        u["money"] += win

    # 💼 casino job
        pay_job(chat_id, "casino", bet // 5)

        del slot_games[key]
        save()

        bot.answer_callback_query(call.id)

        if win > 0:
            text = f"🎰 {result}\n💰 You won {win}!"
        else:
            text = f"🎰 {result}\n💀 You lost {bet}"

        safe_edit(
            
            call.message.chat.id,
            call.message.message_id,
            text
        )

        return



    







@bot.callback_query_handler(
    func=lambda c:
    c.data.startswith("mine_")
    or c.data.startswith("minecollect_")
)
def mines_callback(call):

    chat_id = str(call.message.chat.id)
    
    clicker = str(call.from_user.id)

    uid = clicker

    now = time.time()

    if uid in button_cd:

        if now - button_cd[uid] < 0.7:

            return bot.answer_callback_query(
                call.id,
                "Slow down"
            )

    button_cd[uid] = now

    # =========================
    # 💰 COLLECT
    # =========================
    if call.data.startswith("minecollect_"):

        owner_uid = call.data.split("_")[1]

        # 🔒 only owner
        if clicker != owner_uid:
            return bot.answer_callback_query(
                call.id,
                "❌ Not your game"
            )

        key = f"{chat_id}_{owner_uid}"

        if key not in mines_games:
            return bot.answer_callback_query(
                call.id,
                "Game expired"
            )

        game = mines_games[key]

        # ⏳ timeout
        if time.time() - game["time"] > 120:

            users[chat_id][owner_uid]["money"] += game["bet"]

            del mines_games[key]

            save()

            safe_edit(
                chat_id,
                call.message.message_id,
                "⏳ Mines game expired (refunded)"
            )

            return bot.answer_callback_query(
                call.id,
                "Expired"
            )

        if key not in mines_games:
            return

        reward = int(game["reward"])

        users[chat_id][owner_uid]["money"] += game["bet"]

        game["ended"] = True

        del mines_games[key]
        save()

        return safe_edit(
            
            chat_id,
            call.message.message_id,
            f"💰 You collected {reward}!",
        )

    # =========================
    # 🎯 BOX CLICK
    # =========================

    try:
        _, owner_uid, pos = call.data.split("_")
        pos = int(pos)

    except:
        return

    # 🔒 only owner
    if clicker != owner_uid:
        return bot.answer_callback_query(
            call.id,
            "❌ Not your game"
        )

    key = f"{chat_id}_{owner_uid}"

    if key not in mines_games:
        return bot.answer_callback_query(
            call.id,
            "Game expired"
        )

    game = mines_games[key]

    # ⏳ timeout
    if time.time() - game["time"] > 120:

        users[chat_id][owner_uid]["money"] += game["bet"]
        del mines_games[key]

        save()

        return bot.answer_callback_query(
            call.id,
            "⏳ Game expired (refunded)"
        )

    cell = game["board"][pos]

    # ❌ already opened
    if cell["opened"]:
        return bot.answer_callback_query(
            call.id,
            "Already opened"
        )

    cell["opened"] = True

    # =========================
    # 💣 BOMB
    # =========================

    if cell["type"] == "bomb":

        kb = InlineKeyboardMarkup(row_width=4)

        buttons = []

        # reveal board
        for i, c in enumerate(game["board"]):

            if c["type"] == "bomb":

                emoji = "💣"

            elif c["opened"]:

                emoji = "💰"

            else:

                emoji = "⬜"

            buttons.append(

                InlineKeyboardButton(
                    emoji,
                    callback_data="done"
                )
            )

        kb.add(*buttons)

        # ❌ END GAME
        del mines_games[key]

        save()

        safe_edit(
            chat_id,
            call.message.message_id,
            f"💣 BOOM!\n\n"
            f"❌ You lost {game['bet']}",
            reply_markup=kb
        )

        return

    # =========================
    # 💰 SAFE
    # =========================

    reduce_hunger(chat_id, owner_uid, 1)

    multi = cell["value"]

    gain = int(game["bet"] * multi)

    game["reward"] = int(game["reward"] + gain * 0.8)

    game["safe_hits"] += 1

    # 🏆 max safe auto collect
    if game["safe_hits"] >= 13:

        reward = int(game["reward"])

        if key not in mines_games:
            return

        users[chat_id][owner_uid]["money"] += reward

        game["ended"] = True

        del mines_games[key]

        save()

        safe_edit(
            chat_id,
            call.message.message_id,
            f"🏆 PERFECT GAME!\n\n"
            f"💰 Won {reward}"
        )

        return

    # =========================
    # 🎮 REDRAW BOARD
    # =========================

    kb = InlineKeyboardMarkup(row_width=4)

    buttons = []

    for i, c in enumerate(game["board"]):

        # 💣 opened bomb
        if c["opened"] and c["type"] == "bomb":

            emoji = "💣"

        # 💰 opened safe
        elif c["opened"]:

            emoji = "💰"

        # ⬜ closed
        else:

            emoji = "⬜"

        buttons.append(

            InlineKeyboardButton(
                emoji,
                callback_data=f"mine_{owner_uid}_{i}"
            )
        )

    # ✅ proper 4x4 layout
    kb.add(*buttons)

    # =========================
    # 💰 COLLECT BUTTON
    # =========================

    kb.add(

        InlineKeyboardButton(
            f"💰 Collect {game['reward']}",
            callback_data=f"minecollect_{owner_uid}"
        )
    )

    save()

    # =========================
    # 🔔 POPUP REWARD
    # =========================

    bot.answer_callback_query(
        call.id,
        f"💰 +{gain}"
    )

    # =========================
    # ✨ GAME UI
    # =========================

    safe_edit(
        chat_id,
        call.message.message_id,
        f"💣 MINES GAME\n\n"
        f"💰 Current Reward: {game['reward']}\n"
        f"✅ Safe Picks: {game['safe_hits']}\n"
        f"💥 Bombs Left: {game.get('bombs', 5)}",
        reply_markup=kb
    )

    return












@bot.message_handler(commands=['kill'])
def kill(msg):
    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to target")

    uid = str(msg.from_user.id)
    tgt_id = str(msg.reply_to_message.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 
    tgt_user = msg.reply_to_message.from_user

    # 🚫 block bots
    if tgt_user.is_bot:
        return bot.send_message(msg.chat.id, "🤖 You can't attack bots")

    if check_dead_block(msg, uid):
        return

    if uid == tgt_id:
        return bot.send_message(msg.chat.id, "❌ You can't kill yourself")
    
    

    now = time.time()

    # 🔥 ensure dicts exist
    dead.setdefault(chat_id, {})
    jail.setdefault(chat_id, {})
    shield.setdefault(chat_id, {})
    kill_cd.setdefault(chat_id, {})

    # 💀 target dead check
    if tgt_id in dead[chat_id]:
        return bot.send_message(
            msg.chat.id,
            f"💀 {tgt_user.first_name} is already dead!"
        )

    # 🔁 cooldown
    if uid in kill_cd[chat_id] and now - kill_cd[chat_id][uid] < 600:
        left = int(600 - (now - kill_cd[chat_id][uid]))
        return bot.send_message(msg.chat.id, f"⏳ Wait {left}s")

    
    
    # 🔥 FIX: user per chat
    atk = get_user(msg.from_user, msg.chat.id)


    # 🛡️ shield check
    if tgt_id in shield[chat_id]:
        if time.time() < shield[chat_id][tgt_id]:

            if atk.get("weapon") == "breaker" and random.random() < 0.6:
                del shield[chat_id][tgt_id]
                bot.send_message(msg.chat.id, "💥 Shield destroyed!")
            else:
                return bot.send_message(msg.chat.id, "🛡️ Target is protected")
        else:
            del shield[chat_id][tgt_id]

    tgt = get_user(msg.reply_to_message.from_user, msg.chat.id)

    if atk.get("gang") and atk["gang"] == tgt.get("gang"):
        return bot.send_message(msg.chat.id, "👥 You can't attack your gang member")

    base = 0.6   # upgraded
    risk = 0.15

    if atk["weapon"]:
        w = WEAPONS[atk["weapon"]]
        base = min(1.0, w["rate"] + 0.1)
        risk += w["risk"]

    if tgt["armor"]:
        base -= ARMOR["reduce"]

    # 🍗 hunger penalty
    if atk["hunger"] < 30:
        base -= 0.1

    base = max(0.1, min(base, 1.0))

    # ⚔️ result
    if random.random() < base:
        loot = min(1500, tgt["money"])
        tgt["money"] -= loot
        atk["money"] += loot

        # 💀 mark dead (per chat)
        dead[chat_id][tgt_id] = True

        bot.send_message(
            msg.chat.id,
            f"💀 {tgt['name']} is DEAD!\nUse /revive\n💰 {atk['name']} looted {loot}"
        )
    else:
        bot.send_message(msg.chat.id, "❌ Kill failed")

    # 🚔 arrest
    if random.random() < risk:
        jail[chat_id][uid] = now

        users[chat_id][uid].setdefault("crime", {"caught": 0})
        users[chat_id][uid]["crime"]["caught"] += 1

        bot.send_message(msg.chat.id, "🚔 Police caught you!")

    # ⏱️ cooldown
    kill_cd[chat_id][uid] = now

    reduce_hunger(chat_id, uid, 8)

    save()


def is_dead(chat_id, uid):
    chat_id = str(chat_id)
    uid = str(uid)

    return chat_id in dead and uid in dead[chat_id]


def check_dead_block(msg, uid, action=None, silent=False):
    chat_id = ensure_chat(msg.chat.id)

    if uid in banned.get(chat_id, {}):
        if not silent:
            bot.send_message(msg.chat.id, "🚫 You are banned from this game")
        return True

    # allow some actions when dead
    if action in ["withdraw", "revive", "status"]:
        return False

    if is_dead(chat_id, uid):
        if not silent:
            bot.send_message(
                msg.chat.id,
                "💀 You are DEAD!\nOnly allowed: /revive /withdraw /status"
            )
        return True

    return False







@bot.message_handler(commands=['protect'])
def protect(msg):
    chat_id = ensure_chat(msg.chat.id) 
    uid = str(msg.from_user.id)

    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    shield.setdefault(chat_id, {})

    # ❌ already protected
    if uid in shield[chat_id]:
        left = int(shield[chat_id][uid] - time.time())
        if left > 0:
            return bot.send_message(
                msg.chat.id,
                f"🛡️ Already protected for {left}s"
            )
        else:
            del shield[chat_id][uid]

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🛡️ 5 min - 💰2000", callback_data="protect_300"),
        InlineKeyboardButton("🛡️ 10 min - 💰4000", callback_data="protect_600"),
        InlineKeyboardButton("🛡️ 15 min - 💰6000", callback_data="protect_900")
    )

    bot.send_message(msg.chat.id, "🛡️ Choose protection:", reply_markup=kb)








@bot.message_handler(commands=['rob'])
def rob(msg):
    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to target")

    uid = str(msg.from_user.id)
    tgt_id = str(msg.reply_to_message.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 
    tgt_user = msg.reply_to_message.from_user

    # 🚫 block bots
    if tgt_user.is_bot:
        return bot.send_message(msg.chat.id, "🤖 You can't rob bots")

    if check_dead_block(msg, uid):
        return

    if uid == tgt_id:
        return bot.send_message(msg.chat.id, "❌ You can't rob yourself")


    
    now = time.time()

    # 🔥 ensure dicts exist
    dead.setdefault(chat_id, {})
    jail.setdefault(chat_id, {})
    rob_cd.setdefault(chat_id, {})

    # 🛡️ shield check (ADD THIS)
    shield.setdefault(chat_id, {})


    # 💀 target dead check
    if tgt_id in dead[chat_id]:
        return bot.send_message(msg.chat.id, "💀 Target is dead")

    # 🚔 jail check
    if uid in jail[chat_id] and now - jail[chat_id][uid] < 120:
        left = int(120 - (now - jail[chat_id][uid]))
        return bot.send_message(msg.chat.id, f"🚔 You're jailed for {left}s")

    # ⏳ cooldown (2 min)
    if uid in rob_cd[chat_id] and now - rob_cd[chat_id][uid] < 120:
        left = int(120 - (now - rob_cd[chat_id][uid]))
        return bot.send_message(msg.chat.id, f"⏳ Wait {left}s")

    # 🔥 FIX: user per chat
    atk = get_user(msg.from_user, msg.chat.id)
    tgt = get_user(msg.reply_to_message.from_user, msg.chat.id)



    if tgt_id in shield[chat_id]:
        if time.time() < shield[chat_id][tgt_id]:

            if atk.get("weapon") == "breaker" and random.random() < 0.5:
                del shield[chat_id][tgt_id]
                bot.send_message(msg.chat.id, "💥 Shield broken!")
            else:
                return bot.send_message(msg.chat.id, "🛡️ Target is protected")

    if atk.get("gang") and atk["gang"] == tgt.get("gang"):
        return bot.send_message(msg.chat.id, "👥 You can't attack your gang member")

    if tgt["money"] <= 0:
        return bot.send_message(msg.chat.id, "💸 Target is broke")

    # 🎲 success chance
    success = 0.7

    if atk["weapon"]:
        success += 0.1

    if tgt["armor"]:
        success -= 0.2

    if atk.get("level", 1) > tgt.get("level", 1):
        success += 0.05

    success = max(0.2, min(success, 0.9))

    if random.random() < success:
        if tgt["money"] < 100:
            amt = tgt["money"]
        else:
            amt = random.randint(100, min(1000, tgt["money"]))

        tgt["money"] -= amt
        atk["money"] += amt

        bot.send_message(msg.chat.id, f"💰 Rob success! +{amt}")
    else:
        jail[chat_id][uid] = now

        users[chat_id][uid].setdefault("crime", {"caught": 0})
        users[chat_id][uid]["crime"]["caught"] += 1

        bot.send_message(msg.chat.id, "🚔 Caught by police!")

    # ⏱️ cooldown
    rob_cd[chat_id][uid] = now

    reduce_hunger(chat_id, uid, 5)

    save()



@bot.message_handler(commands=['arrest'])
def arrest(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 💀 dead / banned check
    if check_dead_block(msg, uid):
        return

    # 🔒 must reply
    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to target")

    target = str(msg.reply_to_message.from_user.id)

    # 🚔 check police job
    if job_owner.get(chat_id, {}).get("police") != uid:
        return bot.send_message(msg.chat.id, "🚫 You are not police")

    if target not in users.get(chat_id, {}):
        return bot.send_message(msg.chat.id, "❌ Invalid target")

    u = users[chat_id][target]

    # 🔥 ensure crime exists
    u.setdefault("crime", {"caught": 0})

    # ❌ not criminal
    if u["crime"]["caught"] < 5:
        return bot.send_message(msg.chat.id, "❌ Target is not criminal")

    # 🚔 arrest
    jail.setdefault(chat_id, {})
    jail[chat_id][target] = time.time()

    fine = 2000

    # 💰 fine system
    if u["money"] >= fine:
        u["money"] -= fine
    else:
        u["money"] = 0

    # 💼 pay police
    pay_job(chat_id, "police", fine)

    save()

    bot.send_message(
        msg.chat.id,
        f"🚔 {u['name']} arrested!\n💸 Fine: {fine}"
    )

def is_criminal(u):
    return u.get("crime", {}).get("caught", 0) >= 5


















@bot.message_handler(commands=['revive'])
def revive(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 

    dead.setdefault(chat_id, {})
    shield.setdefault(chat_id, {})

    # ❌ not dead
    if uid not in dead[chat_id]:
        return bot.send_message(msg.chat.id, "❌ You're not dead")

    u = get_user(msg.from_user, msg.chat.id)

    revive_cost = 1000  # 🔥 NEW PRICE (change here anytime)

    # 💸 not enough money
    if u["money"] < revive_cost:
        return bot.send_message(msg.chat.id, f"💸 Need {revive_cost}")

    # 💰 deduct correct amount
    u["money"] -= revive_cost

    # 💀 remove death
    dead[chat_id].pop(uid, None)

    # 🍗 restore hunger
    u["hunger"] = 100

    # 🛡️ protection
    shield[chat_id][uid] = time.time() + 300

    save()

    bot.send_message(
        msg.chat.id,
        f"❤️ Revived!\n💸 Cost: {revive_cost}\n🍗 Hunger: 100/100\n🛡️ 5 min protection"
    )



@bot.message_handler(commands=['panel'])
def panel(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id)

    u = get_user(msg.from_user, msg.chat.id)

    # 🔥 ensure dicts
    dead.setdefault(chat_id, {})
    shield.setdefault(chat_id, {})
    jail.setdefault(chat_id, {})

    # 🔒 safe duel init
    u.setdefault("duel", {"wins": 0, "losses": 0, "total": 0})

    now = time.time()

    # 💰 money
    wallet = u.get("money", 0)
    bank = u.get("bank", 0)
    total = wallet + bank

    # 💎 ranks
    rank = get_money_rank(total)
    duel_rank = get_duel_rank(u["duel"]["wins"])

    # ⚔️ duel stats
    wins = u["duel"]["wins"]
    losses = u["duel"]["losses"]
    total_fights = u["duel"]["total"]
    winrate = round((wins / total_fights) * 100, 2) if total_fights > 0 else 0

    # 🚨 crime
    crime = u.get("crime", {}).get("caught", 0)

    # =========================
    # 📊 MAIN PANEL
    # =========================
    text = f"""
📊 <b>PLAYER PANEL</b>

👤 <b>{u['name']}</b>

💎 Rank: <b>{rank}</b>
⚔️ Duel Rank: <b>{duel_rank}</b>

💰 Wallet: {wallet}
🏦 Bank: {bank}
💼 Total: <b>{total}</b>

🏆 Level: {u.get('level', 1)}
🗺️ Zone: {u.get('zone', 'Unknown')}

⚔️ Weapon: {u.get('weapon', 'None')}
🛡️ Armor: {u.get('armor', False)}
👥 Gang: {u.get('gang', 'None')}

🍗 Hunger: {u.get('hunger',100)}/100
"""

    # =========================
    # ⚔️ DUEL STATS
    # =========================
    text += f"""
<blockquote>
⚔️ Duel Stats
• Fights: {total_fights}
• Wins: {wins}
• Losses: {losses}
• Win Rate: {winrate}%
</blockquote>
"""

    # =========================
    # 🚨 CRIME
    # =========================
    if crime >= 5:
        text += f"\n🚨 <b>CRIMINAL</b> ({crime})"
    elif crime > 0:
        text += f"\n⚠️ Crime: {crime}/5"

    # =========================
    # 📉 STATUS EFFECTS
    # =========================
    if uid in dead[chat_id]:
        text += "\n💀 <b>Status:</b> DEAD"

    # 🛡️ shield
    if uid in shield[chat_id]:
        left = int(shield[chat_id][uid] - now)
        if left > 0:
            text += f"\n🛡️ Protection: {left}s"
        else:
            del shield[chat_id][uid]

    # 🚔 jail
    if uid in jail[chat_id]:
        left = int(120 - (now - jail[chat_id][uid]))
        if left > 0:
            text += f"\n🚔 Jail: {left}s"

    bot.send_message(msg.chat.id, text, parse_mode="HTML")






@bot.message_handler(commands=['status'])
def status(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id)

    u = get_user(msg.from_user, msg.chat.id)

    # 🔥 ensure dicts
    kill_cd.setdefault(chat_id, {})
    rob_cd.setdefault(chat_id, {})
    jail.setdefault(chat_id, {})
    shield.setdefault(chat_id, {})
    dead.setdefault(chat_id, {})

    now = time.time()

    # 💰 totals
    wallet = u.get("money", 0)
    bank = u.get("bank", 0)
    total = wallet + bank

    # 💎 ranks
    rank = get_money_rank(total)
    duel_rank = get_duel_rank(u.get("duel", {}).get("wins", 0))

    # 🚨 crime
    crime = u.get("crime", {}).get("caught", 0)

    # =========================
    # 🧾 BASE PROFILE
    # =========================
    txt = f"""
👤 <b>{u['name']}</b>

💎 Rank: <b>{rank}</b>
⚔️ Duel Rank: <b>{duel_rank}</b>

💰 Wallet: {wallet}
🏦 Bank: {bank}
💼 Total: {total}

⚔️ Weapon: {u.get('weapon', 'None')}
🛡️ Armor: {u.get('armor', False)}
👥 Gang: {u.get('gang', 'None')}

🍗 Hunger: {u.get('hunger',100)}/100
"""

    # =========================
    # 🚨 CRIME STATUS
    # =========================
    if crime >= 5:
        txt += f"\n🚨 <b>Criminal Level:</b> {crime}"
    elif crime > 0:
        txt += f"\n⚠️ Crime: {crime}/5"

    # =========================
    # 📊 STATUS EFFECTS
    # =========================
    if uid in dead[chat_id]:
        txt += "\n💀 <b>Status:</b> DEAD"

    # ⏳ kill cooldown
    if uid in kill_cd[chat_id]:
        left = int(600 - (now - kill_cd[chat_id][uid]))
        if left > 0:
            txt += f"\n⏳ Kill CD: {left}s"

    # 🦹 rob cooldown
    if uid in rob_cd[chat_id]:
        left = int(120 - (now - rob_cd[chat_id][uid]))
        if left > 0:
            txt += f"\n🦹 Rob CD: {left}s"

    # 🚔 jail
    if uid in jail[chat_id]:
        left = int(120 - (now - jail[chat_id][uid]))
        if left > 0:
            txt += f"\n🚔 Jail: {left}s"

    # 🛡️ shield
    if uid in shield[chat_id]:
        left = int(shield[chat_id][uid] - now)
        if left > 0:
            txt += f"\n🛡️ Protection: {left}s"
        else:
            del shield[chat_id][uid]

    bot.send_message(msg.chat.id, txt, parse_mode="HTML")




# ===== GANG =====
@bot.message_handler(commands=['creategang'])
def cg(msg):
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /creategang name")

    name = parts[1]
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 

    if check_dead_block(msg, uid):
        return

    gangs.setdefault(chat_id, {})

    if name in gangs[chat_id]:
        return bot.send_message(msg.chat.id, "❌ Gang already exists")

    gangs[chat_id][name] = [uid]

    u = get_user(msg.from_user, msg.chat.id)
    u["gang"] = name

    save()
    bot.send_message(msg.chat.id, f"👥 Gang '{name}' created!")

@bot.message_handler(commands=['joingang'])
def jg(msg):
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /joingang name")

    name = parts[1]
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 

    if check_dead_block(msg, uid):
        return

    if chat_id not in gangs or name not in gangs[chat_id]:
        return bot.send_message(msg.chat.id, "❌ Gang not found")

    gangs[chat_id][name].append(uid)

    u = get_user(msg.from_user, msg.chat.id)
    u["gang"] = name

    save()
    bot.send_message(msg.chat.id, f"👥 Joined {name}")


@bot.message_handler(commands=['ganginvite'])
def invite(msg):
    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to user to invite")

    uid = str(msg.from_user.id)
    tgt_id = str(msg.reply_to_message.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 

    u = get_user(msg.from_user, msg.chat.id)

    if not u["gang"]:
        return bot.send_message(msg.chat.id, "❌ You are not in a gang")

    gang = u["gang"]

    invites.setdefault(chat_id, {})
    invites[chat_id][tgt_id] = gang

    bot.send_message(
        msg.chat.id,
        f"📩 {msg.reply_to_message.from_user.first_name}, you are invited to join '{gang}'\nUse /acceptgang"
    )

@bot.message_handler(commands=['acceptgang'])
def acceptgang(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id) 

    if chat_id not in invites or uid not in invites[chat_id]:
        return bot.send_message(msg.chat.id, "❌ No invite")

    gang = invites[chat_id][uid]

    gangs.setdefault(chat_id, {})
    gangs[chat_id].setdefault(gang, [])

    gangs[chat_id][gang].append(uid)

    u = get_user(msg.from_user, msg.chat.id)
    u["gang"] = gang

    del invites[chat_id][uid]

    save()
    bot.send_message(msg.chat.id, f"👥 Joined {gang}")


#=============casino=====================







casino_cd = {}  # 🔥 add at top


@bot.message_handler(commands=['casino'])
def casino(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 💀 dead / banned check
    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 🗺️ ZONE RESTRICTION
    if u["zone"] != "casino":
        return bot.send_message(msg.chat.id, "🎰 Go to CASINO to play")

    parts = msg.text.split()
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /casino amount")

    # 🔢 safe parse
    try:
        amt = int(parts[1])
    except:
        return bot.send_message(msg.chat.id, "Invalid amount")

    # ❌ validation
    if amt <= 0:
        return bot.send_message(msg.chat.id, "❌ Amount must be positive")

    if amt > 50000:
        return bot.send_message(msg.chat.id, "❌ Max bet is 50,000")

    if u["money"] < amt:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    # ⏳ COOLDOWN (3 sec)
    casino_cd.setdefault(chat_id, {})
    now = time.time()

    if uid in casino_cd[chat_id] and now - casino_cd[chat_id][uid] < 3:
        return bot.send_message(msg.chat.id, "⏳ Slow down")

    casino_cd[chat_id][uid] = now

    # 🎲 GAME LOGIC
    win_chance = 0.45

    # 🔫 weapon bonus
    if u.get("weapon"):
        win_chance += 0.05

    # 🛡 armor reduces luck (balancing)
    if u.get("armor"):
        win_chance -= 0.05

    # 🍗 hunger penalty
    if u["hunger"] < 30:
        win_chance -= 0.1

    win_chance = max(0.2, min(win_chance, 0.7))

    roll = random.random()

    if roll < win_chance:
        profit = amt  # profit = same as bet
        u["money"] += profit

        bot.send_message(
            msg.chat.id,
            f"🎰 WIN!\n💰 Bet: {amt}\n📈 Profit: +{profit}"
        )
    else:
        u["money"] -= amt

        bot.send_message(
            msg.chat.id,
            f"💀 LOST!\n💸 Lost: {amt}"
        )

    # 💼 PAY CASINO OWNER
    pay_job(chat_id, "casino", amt)
    u["hunger"] = max(0, u["hunger"] - 2)

    # 💥 bankruptcy check
    check_bankrupt(chat_id, uid)

    save()



def create_mines_board(bombs=5):

    board = []

    # ✅ create 16 safe cells
    for i in range(16):

        board.append({

            "type": "safe",
            "opened": False,
            "value": round(
                random.uniform(0.2, 0.8),
                2
            )
        })

    # 💣 random bombs
    bomb_positions = random.sample(
        range(16),
        bombs
    )

    for pos in bomb_positions:

        board[pos] = {

            "type": "bomb",
            "opened": False
        }

    return board


@bot.message_handler(commands=['mines'])
def mines_game(msg):

    chat_id = str(msg.chat.id)
    uid = str(msg.from_user.id)

    mines_cd.setdefault(chat_id, {})

    now = time.time()

    # ⏳ cooldown
    if uid in mines_cd[chat_id]:

        if now - mines_cd[chat_id][uid] < 10:

            return bot.send_message(
                msg.chat.id,
                "⏳ Wait before playing again"
            )

    mines_cd[chat_id][uid] = now

    if check_dead_block(msg, uid):
        return

    parts = msg.text.split()

    if len(parts) < 2:

        return bot.send_message(
            msg.chat.id,
            "Usage: /mines amount"
        )

    try:
        bet = int(parts[1])

    except:

        return bot.send_message(
            msg.chat.id,
            "Invalid amount"
        )

    if bet <= 0:

        return bot.send_message(
            msg.chat.id,
            "Invalid amount"
        )

    u = get_user(msg.from_user, msg.chat.id)

    if u["money"] < bet:

        return bot.send_message(
            msg.chat.id,
            "❌ Not enough money"
        )

    key = f"{chat_id}_{uid}"

    # 🎮 already playing
    if key in mines_games:

        return bot.send_message(
            msg.chat.id,
            "❌ Finish current mines game first"
        )

    # 💸 deduct bet
    u["money"] -= bet

    # 💼 casino earnings
    pay_job(chat_id, "casino", bet // 10)

    bombs = 5

    if bet >= 10000:
        bombs = 6

    if bet >= 50000:
        bombs = 7

    board = create_mines_board(bombs)

    mines_games[key] = {
        
        "bombs": bombs,
        
        "time": time.time(),
        "bet": bet,
        "board": board,
        "reward": bet,
        "safe_hits": 0
    }

    save()

    # 🎮 board
    kb = InlineKeyboardMarkup(row_width=4)

    buttons = []

    for i in range(16):

        buttons.append(

            InlineKeyboardButton(
                "⬜",
                callback_data=f"mine_{uid}_{i}"
            )
        )

    kb.add(*buttons)

    # 💰 collect
    kb.add(

        InlineKeyboardButton(
            "💰 Collect",
            callback_data=f"minecollect_{uid}"
        )
    )

    bot.send_message(
        msg.chat.id,
        f"💣 MINES GAME\n\n"
        f"💰 Bet: {bet}\n"
        f"💥 Bombs: 3\n\n"
        f"Choose boxes carefully",
        reply_markup=kb
    )






@bot.message_handler(commands=['candy'])
def candy(msg):

    chat_id = str(msg.chat.id)
    uid = str(msg.from_user.id)

    candy_cd.setdefault(chat_id, {})

    now = time.time()

    # ⏳ cooldown
    if uid in candy_cd[chat_id]:

        if now - candy_cd[chat_id][uid] < 5:

            return bot.send_message(
                msg.chat.id,
                "⏳ Wait before playing again"
            )

    candy_cd[chat_id][uid] = now

    # 💀 dead check
    if check_dead_block(msg, uid):
        return

    parts = msg.text.split()

    if len(parts) < 2:

        return bot.send_message(
            msg.chat.id,
            "Usage: /candy amount"
        )

    try:
        amt = int(parts[1])

    except:

        return bot.send_message(
            msg.chat.id,
            "Invalid amount"
        )

    if amt <= 0:

        return bot.send_message(
            msg.chat.id,
            "Invalid amount"
        )

    u = get_user(msg.from_user, msg.chat.id)

    # 💸 enough money
    if u["money"] < amt:

        return bot.send_message(
            msg.chat.id,
            "❌ Not enough money"
        )

    key = f"{chat_id}_{uid}"

    # 🎮 already playing
    if key in candy_games:

        return bot.send_message(
            msg.chat.id,
            "❌ Finish current candy game first"
        )

    # 💰 deduct bet
    u["money"] -= amt

    # 💼 casino tax
    pay_job(
        chat_id,
        "casino",
        amt // 10
    )

    # 🍬 generate board
    board = generate_candy_board()

    candy_games[key] = {

        "board": board,
        "bet": amt,

        # ✅ starting reward
        "reward": amt,

        "selected": None,
        "moves": 15,
        "time": time.time()
    }

    # ⚡ async save
    threading.Thread(
        target=save,
        daemon=True
    ).start()

    kb = draw_candy_board(
        uid,
        board
    )

    # 💰 collect button
    kb.row(

        InlineKeyboardButton(
            f"💰 Collect {amt}",
            callback_data=f"candycollect_{uid}"
        )
    )

    bot.send_message(
        msg.chat.id,
        f"🍬 CANDY CRUSH\n\n"
        f"💰 Bet: {amt}\n"
        f"🎯 Moves: 15\n\n"
        f"💡 Match 3 candies to win\n"
        f"👆 Select first candy",
        reply_markup=kb
    )



@bot.callback_query_handler(
    func=lambda c:
    c.data.startswith("candy_")
    or c.data.startswith("candycollect_")
)
def candy_callback(call):

    uid = str(call.from_user.id)
    chat_id = str(call.message.chat.id)

    # ⚡ ultra fast anti spam
    now = time.time()

    if uid in button_cd:

        if now - button_cd[uid] < 0.08:

            return

    button_cd[uid] = now

    try:

        # =========================
        # 💰 COLLECT
        # =========================

        if call.data.startswith("candycollect_"):

            owner_uid = call.data.split("_")[1]

            if uid != owner_uid:

                return bot.answer_callback_query(
                    call.id,
                    "❌ Not your game"
                )

            key = f"{chat_id}_{owner_uid}"

            if key not in candy_games:

                return

            game = candy_games[key]

            total = game["reward"]

            users[chat_id][uid]["money"] += total

            del candy_games[key]

            save()

            # ⚡ instantly remove buttons
            bot.edit_message_reply_markup(
                chat_id,
                call.message.message_id,
                reply_markup=None
            )

            # ⚡ popup
            bot.answer_callback_query(
                call.id,
                f"💰 Collected {total}"
            )

            # ⚡ fast message
            bot.send_message(
                chat_id,
                f"🍬 CANDY CASHOUT\n\n"
                f"💰 Collected: {total}"
            )

            return

        # =========================
        # 🍬 NORMAL CLICK
        # =========================

        _, owner_uid, x, y = call.data.split("_")

        x = int(x)
        y = int(y)

    except:
        return

    # owner only
    if uid != owner_uid:

        return bot.answer_callback_query(
            call.id,
            "❌ Not your game"
        )

    key = f"{chat_id}_{uid}"

    if key not in candy_games:
        return

    game = candy_games[key]

    board = game["board"]

    # =========================
    # 🍬 FIRST SELECT
    # =========================

    if game["selected"] is None:

        game["selected"] = (x, y)

        return bot.answer_callback_query(
            call.id,
            "🍬 Selected"
        )

    x1, y1 = game["selected"]

    # =========================
    # ❌ NOT NEARBY
    # =========================

    if abs(x1 - x) + abs(y1 - y) != 1:

        game["selected"] = None

        return bot.answer_callback_query(
            call.id,
            "❌ Nearby only"
        )

    # =========================
    # 🔄 SWAP
    # =========================

    board[y1][x1], board[y][x] = \
    board[y][x], board[y1][x1]

    game["selected"] = None

    # =========================
    # ⚡ FAST MATCH CHECK
    # =========================

    matched = False

    # check affected row
    row = board[y]

    for i in range(3):

        if row[i] == row[i+1] == row[i+2]:

            matched = True

    # check affected column
    for yy in range(3):

        if (
            board[yy][x]
            ==
            board[yy+1][x]
            ==
            board[yy+2][x]
        ):

            matched = True

    # =========================
    # ❌ NO MATCH
    # =========================

    if not matched:

        # undo
        board[y1][x1], board[y][x] = \
        board[y][x], board[y1][x1]

        return bot.answer_callback_query(
            call.id,
            "❌ No match"
        )

    # =========================
    # 🎲 NEW CANDIES
    # =========================

    while True:

        c1 = random.choice(CANDIES)
        c2 = random.choice(CANDIES)

        if c1 != board[y1][x1] and c2 != board[y][x]:

            break

    board[y1][x1] = c1
    board[y][x] = c2

    # =========================
    # 💰 REWARD
    # =========================

    reward = random.randint(
        game["bet"] // 10,
        game["bet"] // 4
    )

    game["reward"] += reward

    game["moves"] -= 1

    bot.answer_callback_query(
        call.id,
        f"💰 +{reward}"
    )

    # =========================
    # 🏁 GAME OVER
    # =========================

    if game["moves"] <= 0:

        total = game["reward"]

        users[chat_id][uid]["money"] += total

        del candy_games[key]

        save()

        bot.edit_message_text(
            f"🏁 GAME OVER\n\n"
            f"💰 Won: {total}",
            chat_id,
            call.message.message_id
        )

        return

    # =========================
    # ⚡ FAST REDRAW
    # =========================

    kb = InlineKeyboardMarkup()

    for yy in range(5):

        kb.row(

            *[
                InlineKeyboardButton(
                    board[yy][xx],
                    callback_data=f"candy_{uid}_{xx}_{yy}"
                )

                for xx in range(5)
            ]
        )

    # 💰 collect button
    kb.row(

        InlineKeyboardButton(
            f"💰 Collect {game['reward']}",
            callback_data=f"candycollect_{uid}"
        )
    )

    # ⚡ ONLY UPDATE KEYBOARD
    bot.edit_message_reply_markup(
        chat_id,
        call.message.message_id,
        reply_markup=kb
    )








# 🔥 add at top
bet_cd = {}

@bot.message_handler(commands=['bet'])
def bet(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 🗺️ only in casino
    if u["zone"] != "casino":
        return bot.send_message(msg.chat.id, "🎰 Go to CASINO to play")

    parts = msg.text.split()
    if len(parts) < 3:
        return bot.send_message(msg.chat.id, "Usage: /bet number amount (1-10)")

    # 🔢 safe parse
    try:
        num = int(parts[1])
        amt = int(parts[2])
    except:
        return bot.send_message(msg.chat.id, "Invalid input")

    if num < 1 or num > 10:
        return bot.send_message(msg.chat.id, "Pick number 1-10")

    if amt <= 0:
        return bot.send_message(msg.chat.id, "❌ Amount must be positive")

    if amt > 30000:
        return bot.send_message(msg.chat.id, "❌ Max bet is 30,000")

    if u["money"] < amt:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    # ⏳ cooldown (3 sec)
    bet_cd.setdefault(chat_id, {})
    now = time.time()
    if uid in bet_cd[chat_id] and now - bet_cd[chat_id][uid] < 3:
        return bot.send_message(msg.chat.id, "⏳ Slow down")
    bet_cd[chat_id][uid] = now

    # 🎲 roll
    roll = random.randint(1, 10)

    if num == roll:
        win = amt * 4  # balanced (was 5x, too OP)
        u["money"] += win
        result = f"🎯 Correct! Number was {roll}\n💰 You won {win}"
    else:
        u["money"] -= amt
        result = f"❌ Wrong! Number was {roll}\n💸 You lost {amt}"

    pay_job(chat_id, "casino", amt)
    check_bankrupt(chat_id, uid)
    save()

    bot.send_message(msg.chat.id, result)





color_cd = {}

@bot.message_handler(commands=['color'])
def color_bet(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 🗺️ casino only
    if u["zone"] != "casino":
        return bot.send_message(msg.chat.id, "🎰 Go to CASINO")

    parts = msg.text.split()
    if len(parts) < 3:
        return bot.send_message(msg.chat.id, "Usage: /color red|black|green amount")

    choice = parts[1].lower()

    try:
        amt = int(parts[2])
    except:
        return bot.send_message(msg.chat.id, "Invalid amount")

    if choice not in ["red", "black", "green"]:
        return bot.send_message(msg.chat.id, "Choose red, black, or green")

    if amt <= 0 or amt > 50000:
        return bot.send_message(msg.chat.id, "Invalid bet amount")

    if u["money"] < amt:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    # ⏳ cooldown
    color_cd.setdefault(chat_id, {})
    now = time.time()
    if uid in color_cd[chat_id] and now - color_cd[chat_id][uid] < 3:
        return bot.send_message(msg.chat.id, "⏳ Wait a bit")
    color_cd[chat_id][uid] = now

    # 🎡 roll system
    roll = random.random()

    if roll < 0.45:
        result_color = "red"
    elif roll < 0.9:
        result_color = "black"
    else:
        result_color = "green"

    # 🎯 result
    if choice == result_color:
        if choice == "green":
            win = amt * 5
        else:
            win = amt * 2

        u["money"] += win
        msg_txt = f"🎨 Result: {result_color.upper()}\n💰 You won {win}"
    else:
        u["money"] -= amt
        msg_txt = f"🎨 Result: {result_color.upper()}\n💀 You lost {amt}"

    pay_job(chat_id, "casino", amt)
    check_bankrupt(chat_id, uid)
    save()

    bot.send_message(msg.chat.id, msg_txt)



@bot.message_handler(commands=['rps'])
def rps(msg):
    chat_id = str(msg.chat.id)
    uid = str(msg.from_user.id)

    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    if u.get("zone") != "casino":
        return bot.send_message(msg.chat.id, "🎰 Go to CASINO")

    parts = msg.text.split()

    if len(parts) < 2:
        return bot.send_message(
            msg.chat.id,
            "Usage:\n/rps amount (solo)\nReply /rps amount (vs user)"
        )

    try:
        amt = int(parts[1])
    except:
        return bot.send_message(msg.chat.id, "❌ Invalid amount")

    if amt <= 0 or amt > 100000:
        return bot.send_message(msg.chat.id, "❌ Invalid bet")

    if u["money"] < amt:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    # =========================
    # ⏳ COOLDOWN (60 sec)
    # =========================
    rps_cd.setdefault(chat_id, {})
    now = time.time()

    if uid in rps_cd[chat_id]:
        left = int(60 - (now - rps_cd[chat_id][uid]))
        if left > 0:
            return bot.send_message(msg.chat.id, f"⏳ Wait {left}s")

    rps_cd[chat_id][uid] = now

    # =========================
    # ❌ prevent multiple games
    # =========================
    key_check = f"{chat_id}_{uid}"
    for k in rps_games:
        if uid in k:
            return bot.send_message(msg.chat.id, "⏳ Finish current RPS first")

    # =========================
    # 🎯 USER VS USER
    # =========================
    if msg.reply_to_message and not msg.reply_to_message.from_user.is_bot:
        target = str(msg.reply_to_message.from_user.id)
        u2 = get_user(msg.reply_to_message.from_user, msg.chat.id)

        if uid == target:
            return bot.send_message(msg.chat.id, "❌ Can't play yourself")

        if u2["money"] < amt:
            return bot.send_message(msg.chat.id, "❌ Target doesn't have enough money")

        # 🔒 lock money
        u["money"] -= amt
        u2["money"] -= amt

        kb = InlineKeyboardMarkup()
        for move in ["rock", "paper", "scissors"]:
            kb.add(InlineKeyboardButton(move.capitalize(), callback_data=f"rps_{uid}_{target}_{move}"))

        bot.send_message(
            msg.chat.id,
            f"⚔️ <b>RPS DUEL</b>\n\n💰 Pot: {amt*2}\n⏳ 30s to choose",
            reply_markup=kb,
            parse_mode="HTML"
        )

        key = f"{chat_id}_{uid}_{target}"
        rps_games[key] = {
            "p1": uid,
            "p2": target,
            "amt": amt,
            "choices": {},
            "time": now
        }

        # ⏳ auto expire
        def expire():
            time.sleep(30)
            if key in rps_games:
                # refund both players
                users[chat_id][uid]["money"] += amt
                users[chat_id][target]["money"] += amt
                del rps_games[key]

        Thread(target=expire, daemon=True).start()

    # =========================
    # 🤖 BOT MODE (HARDER)
    # =========================
    else:
        u["money"] -= amt

        kb = InlineKeyboardMarkup()
        for move in ["rock", "paper", "scissors"]:
            kb.add(InlineKeyboardButton(move.capitalize(), callback_data=f"rpsbot_{uid}_{move}"))

        bot.send_message(
            msg.chat.id,
            f"🎰 <b>RPS vs BOT</b>\n\n💰 Bet: {amt}\n🏆 Win: {int(amt*1.8)}\n⏳ 30s",
            reply_markup=kb,
            parse_mode="HTML"
        )

        key = f"{chat_id}_{uid}_bot"
        rps_games[key] = {
            "p1": uid,
            "amt": amt,
            "time": now
        }

    save()

  # 🔥 add at top




SPIN_REWARDS = [
    ("💰 +100", 100),
    ("💰 +250", 250),
    ("💰 +500", 500),
    ("💀 -100", -100),
    ("💀 -250", -250),
    ("🎁 Jackpot +1000", 1000),
    ("😐 Nothing", 0)
]

@bot.message_handler(commands=['spin'])
def spin_wheel(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 💀 dead check
    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 🎰 casino only
    if u.get("zone") != "casino":
        return bot.send_message(msg.chat.id, "🎰 Go to CASINO")

    parts = msg.text.split()
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /spin amount")

    # 💰 amount
    try:
        amt = int(parts[1])
    except:
        return bot.send_message(msg.chat.id, "❌ Invalid amount")

    if amt <= 0:
        return bot.send_message(msg.chat.id, "❌ Amount must be positive")

    if amt > 100000:
        return bot.send_message(msg.chat.id, "❌ Max bet is 100,000")

    if u["money"] < amt:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    # =========================
    # ⏳ COOLDOWN (60 sec)
    # =========================
    spin_cd.setdefault(chat_id, {})
    now = time.time()

    if uid in spin_cd[chat_id]:
        elapsed = now - spin_cd[chat_id][uid]
        if elapsed < 60:
            left = int(60 - elapsed)
            return bot.send_message(msg.chat.id, f"⏳ Wait {left}s before spinning again")

    spin_cd[chat_id][uid] = now

    # =========================
    # 🔒 lock bet
    # =========================
    u["money"] -= amt

    # =========================
    # 🎡 spin result
    # =========================
    reward_text, value = random.choice(SPIN_REWARDS)

    # 💰 apply result
    final = value
    u["money"] += final

    # =========================
    # 💼 casino job earning
    # =========================
    if final > 0:
        pay_job(chat_id, "casino", final // 5)

    # =========================
    # 💥 bankruptcy check
    # =========================
    check_bankrupt(chat_id, uid)

    save()

    # =========================
    # 📩 output
    # =========================
    bot.send_message(
        msg.chat.id,
        f"""
🎡 <b>SPIN RESULT</b>

{reward_text}

💰 Bet: {amt}
📊 Result: {final}
""",
        parse_mode="HTML"
    )



# 🎰 symbols
SLOT_SYMBOLS = ["🍒", "🍋", "🍉", "🔔", "⭐", "💎"]

@bot.message_handler(commands=['slot'])
def slot_game(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 💀 dead check
    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 📍 zone check
    if u.get("zone") != "casino":
        return bot.send_message(msg.chat.id, "🎰 Go to CASINO")

    # =========================
    # ⏳ COOLDOWN (60 sec)
    # =========================
    slot_cd.setdefault(chat_id, {})
    now = time.time()

    if uid in slot_cd[chat_id]:
        elapsed = now - slot_cd[chat_id][uid]
        if elapsed < 60:
            left = int(60 - elapsed)
            return bot.send_message(msg.chat.id, f"⏳ Wait {left}s before playing again")

    # =========================
    # ❌ prevent multiple active games
    # =========================
    key = f"{chat_id}_{uid}"
    if key in slot_games:
        return bot.send_message(msg.chat.id, "⏳ Finish your previous slot first")

    # =========================
    # 💰 get bet
    # =========================
    parts = msg.text.split()
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /slot <amount>")

    try:
        bet = int(parts[1])
    except:
        return bot.send_message(msg.chat.id, "❌ Invalid amount")

    if bet <= 0:
        return bot.send_message(msg.chat.id, "❌ Bet must be positive")

    if bet > 100000:
        return bot.send_message(msg.chat.id, "❌ Max bet is 100,000")

    if u["money"] < bet:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    # 🔒 lock bet
    u["money"] -= bet

    # =========================
    # 🎮 store game
    # =========================
    slot_games[key] = {
        "bet": bet,
        "time": now
    }

    # ⏳ start cooldown
    slot_cd[chat_id][uid] = now

    # =========================
    # 🎯 UI (3x2 grid)
    # =========================
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("🍒", callback_data=f"slotspin_{uid}"),
        InlineKeyboardButton("🍋", callback_data=f"slotspin_{uid}"),
        InlineKeyboardButton("🍉", callback_data=f"slotspin_{uid}")
    )
    kb.add(
        InlineKeyboardButton("🔔", callback_data=f"slotspin_{uid}"),
        InlineKeyboardButton("⭐", callback_data=f"slotspin_{uid}"),
        InlineKeyboardButton("💎", callback_data=f"slotspin_{uid}")
    )

    bot.send_message(
        msg.chat.id,
        f"""
🎰 <b>SLOT MACHINE</b>

💰 Bet: {bet}

Tap any symbol to spin!
""",
        reply_markup=kb,
        parse_mode="HTML"
    )

    save()










@bot.message_handler(commands=['coin'])
def coin_flip(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    # 💀 dead check
    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 🎰 casino only
    if u.get("zone") != "casino":
        return bot.send_message(msg.chat.id, "🎰 Go to CASINO")

    parts = msg.text.split()
    if len(parts) < 3:
        return bot.send_message(msg.chat.id, "Usage: /coin heads|tails amount")

    choice = parts[1].lower()

    # 💰 amount parsing
    try:
        amt = int(parts[2])
    except:
        return bot.send_message(msg.chat.id, "❌ Invalid amount")

    # 🎯 validation
    if choice not in ["heads", "tails"]:
        return bot.send_message(msg.chat.id, "❌ Choose heads or tails")

    if amt <= 0:
        return bot.send_message(msg.chat.id, "❌ Amount must be positive")

    if amt > 50000:
        return bot.send_message(msg.chat.id, "❌ Max bet is 50,000")

    if u["money"] < amt:
        return bot.send_message(msg.chat.id, "❌ Not enough money")

    # =========================
    # ⏳ COOLDOWN (60 sec)
    # =========================
    coin_cd.setdefault(chat_id, {})
    now = time.time()

    if uid in coin_cd[chat_id]:
        elapsed = now - coin_cd[chat_id][uid]
        if elapsed < 60:
            left = int(60 - elapsed)
            return bot.send_message(msg.chat.id, f"⏳ Wait {left}s before flipping again")

    coin_cd[chat_id][uid] = now

    # =========================
    # 🎲 FLIP
    # =========================
    result = random.choice(["heads", "tails"])

    # =========================
    # 💰 RESULT LOGIC
    # =========================
    if choice == result:
        profit = amt
        u["money"] += profit
        outcome = f"🎉 You won +{profit}"
    else:
        u["money"] -= amt
        outcome = f"💀 You lost {amt}"

    # =========================
    # 💼 CASINO JOB EARNINGS
    # =========================
    pay_job(chat_id, "casino", amt)

    # =========================
    # 💥 BANKRUPT CHECK
    # =========================
    check_bankrupt(chat_id, uid)

    save()

    # =========================
    # 📩 FINAL MESSAGE
    # =========================
    bot.send_message(
        msg.chat.id,
        f"""
🪙 <b>COIN FLIP</b>

🎯 Your Choice: {choice.upper()}
🎲 Result: {result.upper()}

{outcome}
""",
        parse_mode="HTML"
    )






@bot.message_handler(commands=['fish'])
def fish(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id)

    # 💀 dead / banned check
    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 📍 zone check
    if u["zone"] != "harbor":
        return bot.send_message(msg.chat.id, "⚓ Go to HARBOR")

    # ⏳ COOLDOWN (30 sec)
    fish_cd.setdefault(chat_id, {})
    now = time.time()

    if uid in fish_cd[chat_id] and now - fish_cd[chat_id][uid] < 30:
        left = int(30 - (now - fish_cd[chat_id][uid]))
        return bot.send_message(msg.chat.id, f"⏳ Wait {left}s before fishing again")

    fish_cd[chat_id][uid] = now

    # 🍗 hunger check
    if u["hunger"] < 10:
        return bot.send_message(msg.chat.id, "🍗 Too hungry to fish! Eat first.")

    # 🎲 fail chance
    success_rate = 0.8

    if u["hunger"] < 30:
        success_rate -= 0.2  # weaker if hungry

    if random.random() > success_rate:
        u["hunger"] = max(0, u["hunger"] - 5)
        save()
        return bot.send_message(msg.chat.id, "❌ You failed to catch anything")

    # 💰 reward
    reward = random.randint(300, 1200)

# 💸 30% tax
    tax = int(reward * 0.3)
    final_reward = reward - tax

# 💰 user gets after tax
    u["money"] += final_reward

# 💼 give tax to harbor job owner (or system)
    pay_job(chat_id, "harbor", tax)

    save()

    bot.send_message(
        msg.chat.id,
        f"🐟 You caught fish!\n"
        f"💰 Earned: {final_reward}\n"
        f"💸 Tax: -{tax} (30%)\n"
        f"🍗 Hunger: -5"
    )











@bot.message_handler(commands=['upgrade'])
def upgrade(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    u = get_user(msg.from_user, msg.chat.id)

    parts = msg.text.split()
    if len(parts) < 2:
        return bot.send_message(msg.chat.id, "Usage: /upgrade strength")

    stat = parts[1].lower()

    if stat not in u["stats"]:
        return bot.send_message(msg.chat.id, "Invalid stat")

    cost = (u["stats"][stat] + 1) * 500

    if u["money"] < cost:
        return bot.send_message(msg.chat.id, f"Need {cost}")

    u["money"] -= cost
    u["stats"][stat] += 1

    save()

    bot.send_message(msg.chat.id, f"📈 {stat} upgraded to {u['stats'][stat]}")


# store pending duels
@bot.message_handler(commands=['duel'])
def duel(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    if check_dead_block(msg, uid):
        return

    if not msg.reply_to_message:
        return bot.send_message(msg.chat.id, "Reply to a user")

    if msg.reply_to_message.from_user.is_bot:
        return bot.send_message(msg.chat.id, "🤖 Can't duel bots")

    target = str(msg.reply_to_message.from_user.id)

    if uid == target:
        return bot.send_message(msg.chat.id, "❌ You can't duel yourself")

    # ⏳ cooldown
    duel_cd.setdefault(chat_id, {})
    now = time.time()

    if uid in duel_cd[chat_id] and now - duel_cd[chat_id][uid] < 60:
        left = int(60 - (now - duel_cd[chat_id][uid]))
        return bot.send_message(msg.chat.id, f"⏳ Wait {left}s before dueling again")

    u1 = get_user(msg.from_user, msg.chat.id)
    u2 = get_user(msg.reply_to_message.from_user, msg.chat.id)

    if is_dead(chat_id, target):
        return bot.send_message(msg.chat.id, "💀 Target is dead")

    if u1.get("gang") and u1["gang"] == u2.get("gang"):
        return bot.send_message(msg.chat.id, "👥 Can't duel gang member")

    duel_cd[chat_id][uid] = now

    text = f"""
⚔️ <b>DUEL REQUEST</b>

👤 <b>{u1['name']}</b>
STR: {u1['stats']['strength']} | MUS: {u1['stats']['muscles']}
STA: {u1['stats']['stamina']} | PWR: {u1['stats']['power']}

<b>VS</b>

👤 <b>{u2['name']}</b>
STR: {u2['stats']['strength']} | MUS: {u2['stats']['muscles']}
STA: {u2['stats']['stamina']} | PWR: {u2['stats']['power']}
"""

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("⚔️ Fight", callback_data=f"fight_{uid}_{target}")
    )

    bot.send_message(msg.chat.id, text, reply_markup=kb, parse_mode="HTML")

@bot.message_handler(commands=['stat'])
def duel_stats(msg):
    chat_id = ensure_chat(msg.chat.id)
    uid = str(msg.from_user.id)

    u = get_user(msg.from_user, msg.chat.id)

    import html
    name = html.escape(u['name'])

    # 🔥 ensure duel exists
    u.setdefault("duel", {"wins":0,"losses":0,"total":0})

    d = u["duel"]
    s = u["stats"]

    wins = d["wins"]
    losses = d["losses"]
    total = d["total"]

    # 🧠 fix total (use stored value, not wins+losses)
    total = total if total > 0 else wins + losses

    winrate = round((wins / total) * 100, 2) if total > 0 else 0

    # 🏆 duel rank
    duel_rank = get_duel_rank(wins)

    text = f"""
📊 <b>PLAYER STATS</b>

👤 <b>{name}</b>

<blockquote>
⚔️ Duel Stats
• Rank: {duel_rank}
• Total: {total}
• Wins: {wins}
• Losses: {losses}
• Win Rate: {winrate}%
</blockquote>

<blockquote>
💪 Power Stats
• Strength: {s['strength']}
• Muscles: {s['muscles']}
• Power: {s['power']}
• Stamina: {s['stamina']}
• EXP: {s['experience']}
</blockquote>

<blockquote>
🍗 Hunger: {u.get('hunger',100)}/100
💰 Money: {u['money']}
🏦 Bank: {u.get('bank',0)}
</blockquote>
"""

    bot.send_message(msg.chat.id, text, parse_mode="HTML")








@bot.message_handler(commands=['arena'])
def arena(msg):
    uid = str(msg.from_user.id)
    chat_id = ensure_chat(msg.chat.id)

    # 💀 dead check
    if check_dead_block(msg, uid):
        return

    u = get_user(msg.from_user, msg.chat.id)

    # 🗺️ zone check
    if u["zone"] != "arena":
        return bot.send_message(msg.chat.id, "⚔️ Go to ARENA")

    stats = u["stats"]

    # 🧠 power calculation
    power = (
        stats["strength"] +
        stats["muscles"] +
        stats["power"]
    )

    # 🎯 base chance (balanced)
    win_chance = 0.5 + (power / 100)

    # 🍗 hunger penalty
    if u["hunger"] < 30:
        win_chance -= 0.1

    # 🛡 armor bonus
    if u.get("armor"):
        win_chance += 0.05

    # 🔫 weapon bonus
    if u.get("weapon"):
        win_chance += 0.05

    # clamp
    win_chance = max(0.2, min(win_chance, 0.85))

    reward = random.randint(2000, 5000)

    if random.random() < win_chance:
        u["money"] += reward
        stats["experience"] += 5

        msg_txt = f"""
🏆 ARENA WIN

💰 +{reward}
📊 XP +5
🎯 Chance: {round(win_chance, 2)}
"""
    else:
        loss = int(reward * 0.4)
        u["money"] -= loss
        stats["experience"] += 2

        msg_txt = f"""
💀 ARENA LOSS

💸 -{loss}
📊 XP +2
🎯 Chance: {round(win_chance, 2)}
"""

    # 🍗 hunger drain
    u["hunger"] = max(0, u["hunger"] - 3)

    # 💥 bankruptcy check
    check_bankrupt(chat_id, uid)

    save()
    bot.send_message(msg.chat.id, msg_txt)

# ===== TOP =====
@bot.message_handler(commands=['top'])
def top(msg):
    chat_id = ensure_chat(msg.chat.id) 

    # 🔥 get users of THIS chat only
    chat_users = users.get(chat_id, {})

    if not chat_users:
        return bot.send_message(msg.chat.id, "No players yet")

    # 💰 sort by wallet + bank
    s = sorted(
        chat_users.values(),
        key=lambda x: x.get("money", 0) + x.get("bank", 0),
        reverse=True
    )

    txt = "🏆 TOP PLAYERS\n\n"

    for i, u in enumerate(s[:10], 1):
        total = u.get("money", 0) + u.get("bank", 0)
        txt += f"{i}. {u['name']} - 💰 {total} (💵 {u['money']} | 🏦 {u['bank']})\n"

    bot.send_message(msg.chat.id, txt)

# ===== ===== =====
def cleanup():

    while True:

        now = time.time()

        # mines
        for k, v in list(mines_games.items()):

            if now - v["time"] > 300:

                del mines_games[k]

        # slots
        for k, v in list(slot_games.items()):

            if now - v["time"] > 120:

                del slot_games[k]

        # rps
        for k, v in list(rps_games.items()):

            if now - v["time"] > 120:

                del rps_games[k]

        time.sleep(60)


threading.Thread(
    target=cleanup,
    daemon=True
).start()


if __name__ == "__main__":

    print("🤖 Bot started...")

    try:
        bot.remove_webhook()
    except:
        pass

    while True:
        try:
            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=60,
                skip_pending=True
            )

        except Exception as e:

            print("Error:", e)

            time.sleep(5)
