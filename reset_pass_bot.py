import os
import random
import string
import uuid
import json
import requests
from datetime import datetime

# ==================== INSTAGRAM RESET CLASS ====================
class InstagramResetTool:
    def __init__(self):
        self.colors = {
            'primary': '\x1b[38;5;208m',
            'accent': '\x1b[1;31m',
            'warning': '\x1b[1;33m',
            'neutral': '\x1b[2;36m',
            'reset': '\x1b[1;37m',
        }

    def generate_instagram_password(self):
        words = ['hello', 'insta', 'random', 'python', 'absceb', 'summer', 'winter', 'autumn', 'spring', 'monsoon', 'cool', 'new', 'user', 'alpha', 'beta', 'gamma', 'star', 'moon', 'sun', 'earth', 'mars', 'venus']
        formats = [lambda w, n: f"{w}{n}!", lambda w, n: f"{w}{n}#", lambda w, n: f"{w}{n}@",
                   lambda w, n: f"{w}{n}$", lambda w, n: f"{w}{n}_", lambda w, n: f"{w}@{n}",
                   lambda w, n: f"{w}_{n}", lambda w, n: f"{w}{n}", lambda w, n: f"{w[:2]}_{n[:2]}@",
                   lambda w, n: f"{w}{n}&"]
        
        word = random.choice(words)
        numbers = ''.join(str(random.randint(0, 9)) for _ in range(3))
        fmt = random.choice(formats)
        password = fmt(word, numbers)
        while len(password) < 6:
            password += str(random.randint(0, 9))
        return password

    def generate_device_info(self):
        ANDROID_ID = f"android-{''.join(random.choices(string.hexdigits.lower(), k=16))}"
        USER_AGENT = f"Instagram 394.0.0.46.81 Android ({random.choice(['28/9','29/10','30/11','31/12'])}; {random.choice(['240dpi','320dpi','480dpi'])}; {random.choice(['720x1280','1080x1920','1440x2560'])}; {random.choice(['samsung','xiaomi','huawei','oneplus','google'])}; {random.choice(['SM-G975F','Mi-9T','P30-Pro','ONEPLUS-A6003','Pixel-4'])}; intel; en_US; {random.randint(100000000,999999999)})"
        WATERFALL_ID = str(uuid.uuid4())
        timestamp = int(datetime.now().timestamp())
        PASSWORD = f'#PWD_INSTAGRAM:0:{timestamp}:{self.generate_instagram_password()}'
        return ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD

    def make_headers(self, mid="", user_agent=""):
        return {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Bloks-Version-Id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "X-Mid": mid,
            "User-Agent": user_agent,
            "Content-Length": "9481"
        }

    def reset_instagram_password(self, reset_link):
        try:
            ANDROID_ID, USER_AGENT, WATERFALL_ID, PASSWORD = self.generate_device_info()
            uidb36 = reset_link.split("uidb36=")[1].split("&token=")[0]
            token = reset_link.split("&token=")[1].split(":")[0]

            url = "https://i.instagram.com/api/v1/accounts/password_reset/"
            data = {"source": "one_click_login_email", "uidb36": uidb36, "device_id": ANDROID_ID, "token": token, "waterfall_id": WATERFALL_ID}

            r = requests.post(url, headers=self.make_headers(user_agent=USER_AGENT), data=data)

            if "user_id" not in r.text:
                return {"success": False, "error": f"Reset request failed: {r.text[:150]}"}

            mid = r.headers.get("Ig-Set-X-Mid")
            resp = r.json()
            user_id = resp.get("user_id")
            cni = resp.get("cni")
            nonce_code = resp.get("nonce_code")
            challenge_context = resp.get("challenge_context")

            url2 = "https://i.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/"
            data2 = {
                "user_id": str(user_id), "cni": str(cni), "nonce_code": str(nonce_code),
                "bk_client_context": '{"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"}',
                "challenge_context": str(challenge_context), "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd", "get_challenge": "true"
            }
            r2 = requests.post(url2, headers=self.make_headers(mid, USER_AGENT), data=data2).text

            try:
                challenge_context_final = r2.replace('\\', '').split(f'(bk.action.i64.Const, {cni}), "')[1].split('", (bk.action.bool.Const, false)))')[0]
            except:
                challenge_context_final = challenge_context

            data3 = {
                "is_caa": "False", "cni": str(cni), "challenge_context": challenge_context_final,
                "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
                "enc_new_password1": PASSWORD, "enc_new_password2": PASSWORD
            }

            requests.post(url2, headers=self.make_headers(mid, USER_AGENT), data=data3)
            new_password = PASSWORD.split(":")[-1]

            return {"success": True, "password": new_password, "user_id": user_id}

        except Exception as e:
            return {"success": False, "error": str(e)}


# ==================== TELEGRAM BOT USING YOUR TOKEN ====================
tool = InstagramResetTool()

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")

if not os.getenv("OWNER_ID"):
    raise ValueError("OWNER_ID not set")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_message(chat_id, text):
    requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})

def main():
    print("🚀 Instagram Password Reset Bot is now running...")
    offset = 0

    while True:
        try:
            response = requests.get(f"{BASE_URL}/getUpdates?offset={offset}&timeout=30").json()
            
            if response.get("ok"):
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    message = update.get("message")
                    if not message:
                        continue

                    chat_id = message["chat"]["id"]
                    text = message.get("text", "").strip()

                    # Start command
                    if text == "/start":
                        send_message(chat_id, 
                            "🔐 <b>Instagram Password Reset Bot</b>\n\n"
                                     
                            "Wait 2min befor sending reset link its work better "
                            
                            "Send me the password reset link you received in your email.\n"
                            "<i>Example: https://www.instagram.com/accounts/password/reset/confirm/...</i>"
                        )
                        continue

                    # Check if it's a reset link
                    if "instagram.com/accounts/password/reset/confirm/" in text:
                        send_message(chat_id, "⏳ Processing your reset link... Please wait.")

                        result = tool.reset_instagram_password(text)

                        if result.get("success"):
                            new_pass = result["password"]
                            user_id = result["user_id"]

                            # Send to the user who requested

                            # Notify you (owner)
                            notify = f"""
≿━━━━━🔰 𝐑ᴇsᴇᴛ 𝐃ᴏɴᴇ 🔰━━━━━≾
<blockquote>
👤 <b>User ID: {user_id} ➤</b></blockquote>

🔑 New Password: {new_pass}

≿━━━━━🔰 𝐑ᴇsᴇᴛ 𝐃ᴏɴᴇ 🔰━━━━━≾
<blockquote>
🎗️ By :- @kn0x_g0d || @elite_v0rt3x</blockquote>
≿━━━━━🔰 𝐑ᴇsᴇᴛ 𝐃ᴏɴᴇ 🔰━━━━━≾
"""
                            send_message(chat_id, notify)

                        else:
                            send_message(chat_id, f"❌ <b>Reset Failed</b>\n\nError: {result.get('error', 'Unknown error')[:250]}")

        except Exception as e:
            print(f"Error: {e}")
            continue

if __name__ == "__main__":
    main()
