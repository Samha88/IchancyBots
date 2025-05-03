import asyncio
import re
import json
from telethon import TelegramClient, events
from aiohttp import web

# معلومات حساب تيليجرام
api_id = 22707838
api_hash = '7822c50291a41745fa5e0d63f21bbfb6'
session_name = 'my_session'

# المستخدم المسموح له
allowed_chat_ids = {141117417}

# تحميل إعدادات القنوات من ملف خارجي
with open('config.json', 'r') as f:
    channels_config = json.load(f)

client = TelegramClient(session_name, api_id, api_hash)
selected_channels = set()
monitoring_active = False

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.chat_id not in allowed_chat_ids:
        return
    await event.respond(
        "مرحباً! أرسل أسماء القنوات أو البوتات التي تريد مراقبتها، مفصولة بفاصلة.\n"
        "مثال:\n"
        "ichancy_saw, captain_ichancy\n\n"
        "ثم أرسل 's' لبدء المراقبة، أو 'st' لإيقافها."
    )

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

@client.on(events.NewMessage)
async def monitor_handler(event):
    global monitoring_active
    if not monitoring_active:
        return

    for channel_name in selected_channels:
        config = channels_config[channel_name]
        if event.chat.username != config["username"]:
            continue

        match = re.findall(config["regex"], event.message.message)
        if match:
            if config.get("pick_third") and len(match) >= 3:
                code = match[2]
            else:
                code = match[0]

            bot_username = config["bot"]

            await client.send_message(bot_username, '/start')
            await asyncio.sleep(2)

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

async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get("/", handle)

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
