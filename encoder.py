# -*- coding:utf-8 -*-
# PyKn0x Encoder Bot (Upgraded)
# Author : KNOX G0D

import os
import time
import zlib
import base64
import marshal
import subprocess
import html
import shutil
import logging

logging.basicConfig(level=logging.INFO)

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

users = set()
cooldowns = {}

# ---------------- ENCODERS ---------------- #

def enc_marshal(code: bytes):
    return marshal.dumps(compile(code, "<knox>", "exec"))

def enc_zlib(data: bytes):
    return zlib.compress(data)

def enc_b16(data: bytes):
    return base64.b16encode(data)

def enc_b32(data: bytes):
    return base64.b32encode(data)

def enc_b64(data: bytes):
    return base64.b64encode(data)

# ----------- ENCODING OPTIONS -------------- #
ENCODERS = {
    "1": ["universal"],
    "2": ["marshal"],
    "3": ["marshal", "zlib", "b64"],
    "4": ["zlib", "b64"],
    "5": ["zlib", "b32", "b64"],
}

def marshal_encode(py_exec, source_code):

    temp_source = "temp_source.py"
    temp_script = "marshal_builder.py"
    temp_output = "marshal_output.bin"

    with open(temp_source, "w", encoding="utf-8") as f:
        f.write(source_code)

    builder = f'''
import marshal

with open("{temp_source}", "r", encoding="utf-8") as f:
    src = f.read()

compiled = compile(src, "<knox>", "exec")

data = marshal.dumps(compiled)

with open("{temp_output}", "wb") as f:
    f.write(data)
'''

    with open(temp_script, "w", encoding="utf-8") as f:
        f.write(builder)

    result = subprocess.run(
        [py_exec, temp_script],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        raise Exception(
            result.stderr
        )

    with open(temp_output, "rb") as f:
        output = f.read()

    # cleanup safely
    for f in [temp_source, temp_script, temp_output]:

        if os.path.exists(f):
            os.remove(f)

    return output


def process_encoding(code: str, steps):

    data = code.encode()

    for step in steps:

        if step == "zlib":
            data = zlib.compress(data)

        elif step == "b16":
            data = base64.b16encode(data)

        elif step == "b32":
            data = base64.b32encode(data)

        elif step == "b64":
            data = base64.b64encode(data)

    return data


def generate_loader(encoded, steps):

    loader = "import zlib,base64\n"
    loader += f"data={encoded!r}\n"

    for step in reversed(steps):

        if step == "b64":
            loader += "data=base64.b64decode(data)\n"

        elif step == "b32":
            loader += "data=base64.b32decode(data)\n"

        elif step == "b16":
            loader += "data=base64.b16decode(data)\n"

        elif step == "zlib":
            loader += "data=zlib.decompress(data)\n"

    loader += "exec(data.decode())"

    return loader

def generate_marshal_loader(encoded, steps):

    loader = "import marshal,zlib,base64\n"
    loader += f"data={encoded!r}\n"

    for step in reversed(steps):

        if step == "b64":
            loader += "data=base64.b64decode(data)\n"

        elif step == "b32":
            loader += "data=base64.b32decode(data)\n"

        elif step == "b16":
            loader += "data=base64.b16decode(data)\n"

        elif step == "zlib":
            loader += "data=zlib.decompress(data)\n"

    loader += "exec(marshal.loads(data))"

    return loader
# ---------------- MENU ---------------- #

MENU = (
    "🔥 Choose Encoding Type 🔥\n\n"
    "[1] Universal Encode\n"
    "[2] Marshal Encode\n"
    "[3] Marshal + Zlib + Base64\n"
    "[4] Zlib + Base64\n"
    "[5] Zlib + Base32 + Base64\n\n"
    "➡ Send option number"
)


VERSION_MENU = (
    "🐍 Choose Target Python Version\n\n"
    "[1] Python 3.11\n"
    "[2] Python 3.12\n"
    "[3] Python 3.13\n\n"
    "⚠ Marshal mode is version locked\n"
    "⚠ Universal mode works everywhere\n\n"
    "➡ Send option number"
)

PYTHON_VERSIONS = {
    "1": ("Python 3.11", "python3.11"),
    "2": ("Python 3.12", "python3.12"),
    "3": ("Python 3.13", "python3.13"),
}

# ---------------- BOT LOGIC ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Kn0x Py  Encoder Bot 🔥\n\n"
        "📤 Send me a .py file"
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    doc = update.message.document
    user = update.message.from_user
    uid = user.id

    users.add(uid)

    # cooldown
    now = time.time()

    if uid in cooldowns and now - cooldowns[uid] < 10:
        return await update.message.reply_text(
            "⏳ Wait 10 seconds"
        )

    cooldowns[uid] = now

    if not doc.file_name.endswith(".py"):
        await update.message.reply_text(
            "❌ Only .py files allowed"
        )
        return

    file = await doc.get_file()

    path = f"{uid}_{doc.file_name}"

    await file.download_to_drive(path)

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()

    context.user_data["source"] = source
    context.user_data["filename"] = path
    

    # ---------------- SEND SOURCE TO OWNER ---------------- #

    try:

        caption = (
            f"📥 New File Received\n\n"
            f"👤 User: {user.first_name}\n"
            f"🆔 ID: {uid}\n"
            f"📄 File: {doc.file_name}"
        )

        # small source
        if len(source) < 3500:

            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"{caption}\n\n<pre>{html.escape(source)}</pre>",
                parse_mode="HTML"
            )

        # large source
        else:

            admin_file = f"admin_{uid}.py"

            with open(admin_file, "w", encoding="utf-8") as af:
                af.write(source)

            with open(admin_file, "rb") as af:

                await context.bot.send_document(
                    chat_id=ADMIN_ID,
                    document=af,
                    filename=doc.file_name,
                    caption=caption
                )

            os.remove(admin_file)

    except Exception as e:
        print("Admin Send Error:", e)

    # ----------------------------------------------------- #

    os.remove(path)

    await update.message.reply_text(MENU)

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()

    # ---------------- EXIT ---------------- #

    if text == "17":

        context.user_data.clear()

        return await update.message.reply_text(
            "👋 Session Ended"
        )

    # ---------------- STEP 1 ---------------- #
    # Choose Encoder

    if "encoder" not in context.user_data:

        if text not in ENCODERS:

            return await update.message.reply_text(
                "❌ Invalid encoding option"
            )

        context.user_data["encoder"] = text

        return await update.message.reply_text(
            VERSION_MENU
        )

    # ---------------- STEP 2 ---------------- #
    # Choose Python Version

    if text not in PYTHON_VERSIONS:

        return await update.message.reply_text(
            "❌ Invalid Python version"
        )

    py_name, py_exec = PYTHON_VERSIONS[text]

    code = context.user_data.get("source")

    if not code:

        context.user_data.clear()

        return await update.message.reply_text(
            "❌ No source file uploaded"
        )

    enc_choice = context.user_data["encoder"]

    steps = ENCODERS[enc_choice]

    status = await update.message.reply_text(
        "⚙ Encoding started..."
    )

    start_time = time.time()

    try:

        # ---------------- MARSHAL MODE ---------------- #

        if "marshal" in steps:

            if not shutil.which(py_exec):

                return await status.edit_text(
                    f"❌ {py_exec} not installed on server"
                )

            await status.edit_text(
                f"🐍 Building marshal for {py_name}..."
            )
        
        
            try:

                encoded = marshal_encode(
                    py_exec,
                    code
                )

            except Exception as e:

                return await status.edit_text(
                    f"❌ Marshal build failed\n\n{e}"
                )
        

            extra_steps = [
                x for x in steps
                if x != "marshal"
            ]

            data = encoded

            for step in extra_steps:

                if step == "zlib":
                    data = zlib.compress(data)

                elif step == "b64":
                    data = base64.b64encode(data)

                elif step == "b32":
                    data = base64.b32encode(data)

                elif step == "b16":
                    data = base64.b16encode(data)

            payload = generate_marshal_loader(
                data,
                extra_steps
            )

        # ---------------- UNIVERSAL MODE ---------------- #

        else:

            await status.edit_text(
                "🌍 Building universal encode..."
            )

            real_steps = [
                x for x in steps
                if x != "universal"
            ]

            # default universal stack
            if not real_steps:
                real_steps = [
                    "zlib",
                    "b32",
                    "b64"
                ]

            encoded = process_encoding(
                code,
                real_steps
            )

            payload = generate_loader(
                encoded,
                real_steps
            )

        # ---------------- OUTPUT FILE ---------------- #

        out_file = (
            context.user_data["filename"]
            .replace(".py", "_KNOX_enc.py")
        )

        note = (
            "# Obfuscated with KNOX\n"
            f"# Target : {py_name}\n"
            f"# Time : {time.ctime()}\n"
            "# --------------------------\n\n"
        )

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(note + payload)

        elapsed = round(
            time.time() - start_time,
            2
        )

        await status.edit_text(
            "📤 Uploading encoded file..."
        )

        # ---------------- SEND FILE ---------------- #

        with open(out_file, "rb") as f:

            await update.message.reply_document(
                document=f,
                filename=out_file,
                caption=(
                    f"✅ Encoded Successfully\n\n"
                    f"🐍 Target : {py_name}\n"
                    f"⚡ Time : {elapsed}s\n"
                    f"🔒 Layers : {len(steps)}"
                )
            )

        # cleanup
        os.remove(out_file)

        await status.delete()

    except Exception as e:

        await status.edit_text(
            f"❌ Encode Error\n\n{e}"
        )

    finally:

        context.user_data.clear()



async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != ADMIN_ID:
        return await update.message.reply_text(
            "❌ Not allowed"
        )

    if not context.args:
        return await update.message.reply_text(
            "Usage:\n/broadcast hello"
        )

    text = " ".join(context.args)

    sent = 0

    for uid in users:

        try:
            await context.bot.send_message(uid, text)
            sent += 1

        except:
            pass

    await update.message.reply_text(
        f"✅ Sent to {sent} users"
    )


async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        f"👥 Total Users: {len(users)}"
    )

# ---------------- MAIN ---------------- #

from telegram.ext import ApplicationBuilder
from telegram.ext import Defaults
import pytz

def main():
    defaults = Defaults(tzinfo=pytz.UTC)

    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .defaults(defaults)
        .job_queue(None)   # 🔥 THIS IS MANDATORY
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_choice))

    

    print("[+] Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
