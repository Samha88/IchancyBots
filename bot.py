import asyncio
import re
import json
from telethon import TelegramClient, events
from aiohttp import web

# تحميل إعدادات القنوات من ملف خارجي
with open('channels_config.json', 'r') as f:
    channels_config = json.load(f)

# معلومات حساب تيليجرام
api_id = 22707838
api_hash = '7822c50291a41745fa5e0d63f21bbfb6'
session_name = 'my_session'

# معرف المستخدم المسموح له بالتفاعل مع البوت
allowed_chat_ids = {141117417}  # ← معرفك الشخصي

# تهيئة العميل
client = TelegramClient(session_name, api_id, api_hash)
selected_channels = set()
monitoring_active = False

async def handle_user_commands(event):
    global selected_channels, monitoring_active

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

async def monitor_handler(event):
    if not monitoring_active:
        return

    sender_username = getattr(event.chat, 'username', None)
    if not sender_username:
        return

    for channel_name in selected_channels:
        config = channels_config[channel_name]
        if sender_username != config["username"] and sender_username != config["bot"].lstrip('@'):
            continue

        match = re.findall(config["regex"], event.raw_text)
        if match:
            code = match[2] if config.get("pick_third") and len(match) >= 3 else match[0]
            try:
                await client.send_message(config["bot"], code)
                print(f"أُرسل الكود: {code} إلى {config['bot']}")
            except Exception as e:
                print(f"خطأ عند إرسال الكود إلى {config['bot']}: {e}")
            break

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.chat_id not in allowed_chat_ids:
        return
    await event.respond(
        "مرحباً! أرسل أسماء القنوات التي تريد مراقبتها، مفصولة بفاصلة.\n"
        "مثال:\n"
        "ichancy_saw, ichancyTheKing\n\n"
        "ثم أرسل كلمة 's' لبدء المراقبة، أو 'st' لإيقافها."
    )

@client.on(events.NewMessage)
async def unified_handler(event):
    if event.chat_id in allowed_chat_ids:
        await handle_user_commands(event)
    elif monitoring_active:
        await monitor_handler(event)

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
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("Web server is running on http://0.0.0.0:8080")
    await client_loop

if __name__ == "__main__":
    asyncio.run(start_all())
