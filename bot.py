import asyncio
import re
from telethon import TelegramClient, events
from aiohttp import web

# معلومات حساب تيليجرام
api_id = 22707838
api_hash = '7822c50291a41745fa5e0d63f21bbfb6'
session_name = 'my_session'

# معرف المستخدم المسموح له بالتفاعل مع البوت
allowed_chat_ids = {141117417}  # ← معرفك الشخصي

# تعريف القنوات والصيغ والبوتات
channels_config = {
    "ichancy_saw": {
        "username": "ichancy_saw",
        "regex": r"\b[a-zA-Z0-9]{8,12}\b",
        "bot": "@ichancy_saw_bot"
    },
    "VIP_bot": {
        "username": "vip_ichancy_bot",
        "regex": r"\b[a-zA-Z0-9]{5,}\b",
        "bot": "@vip_ichancy_bot"
    },
    "captain_ichancy": {
        "username": "captain_ichancy",
        "regex": r"\b[a-zA-Z0-9]{6,12}\b",
        "bot": "@ichancy_captain_bot",
        "pick_third": True
    },
}

# تهيئة العميل
client = TelegramClient(session_name, api_id, api_hash)
selected_channels = set()
monitoring_active = False

# /start - إرسال التعليمات
@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.chat_id not in allowed_chat_ids:
        return
    await event.respond(
        "مرحباً! أرسل أسماء القنوات التي تريد مراقبتها، مفصولة بفاصلة.\n"
        "مثال:\n"
        "ichancy_saw, captain_ichancy\n\n"
        "ثم أرسل كلمة 's' لبدء المراقبة، أو 'st' لإيقافها."
    )

# استقبال أوامر المستخدم
@client.on(events.NewMessage)
async def handle_user_commands(event):
    global selected_channels, monitoring_active

    if event.chat_id not in allowed_chat_ids:
        return

    message = event.raw_text.strip()

    if message.startswith('/'):
        return

    if message.lower() == "s":
        if not selected_channels:
            await event.respond("الرجاء اختيار القنوات أولاً.")
            return
        monitoring_active = True
        await event.respond("تم تفعيل المراقبة.")

    elif message.lower() == "st":
        selected_channels.clear()
        monitoring_active = False
        await event.respond("تم إيقاف المراقبة.")

    else:
        possible_channels = [name.strip() for name in message.split(',')]
        if all(name in channels_config for name in possible_channels):
            selected_channels = set(possible_channels)
            await event.respond(f"تم اختيار القنوات: {', '.join(selected_channels)}")
        else:
            await event.respond("بعض القنوات غير صحيحة، تأكد من كتابتها بشكل دقيق.")

# مراقبة القنوات والبوتات
@client.on(events.NewMessage)
async def monitor_handler(event):
    global monitoring_active
    if not monitoring_active:
        return

    for channel_name in selected_channels:
        config = channels_config[channel_name]
        allowed_sources = {config["username"], config["bot"].lstrip("@")}

        if event.chat.username not in allowed_sources:
            continue

        match = re.findall(config["regex"], event.message.message)
        if match:
            if config.get("pick_third") and len(match) >= 3:
                code = match[2]
            else:
                code = match[0]

            bot_username = config["bot"]

            # إرسال /start للبوت
            await client.send_message(bot_username, '/start')
            await asyncio.sleep(2)

            # الضغط على زر "كود هدية"
            async for message in client.iter_messages(bot_username, limit=5):
                if message.buttons:
                    for row in message.buttons:
                        for button in row:
                            if "كود هدية" in button.text:
                                await button.click()
                                await asyncio.sleep(2)
                                await client.send_message(bot_username, code)
                                print(f"أُرسل الكود: {code} إلى {bot_username} بعد الضغط على زر كود هدية")
                                break
                    break
            break

# Web service للتأكد أن السيرفر شغال
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get("/", handle)

# تشغيل البوت والسيرفر
async def start_all():
    await client.start()
    print("Bot is running...")
    client_loop = asyncio.create_task(client.run_until_disconnected())

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8081)
    await site.start()
    print("Web server is running on http://0.0.0.0:8081")
    await client_loop

if __name__ == "__main__":
    asyncio.run(start_all())
