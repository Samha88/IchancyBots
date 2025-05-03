import asyncio
import re
import json
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from aiohttp import web

# تحميل الإعدادات
try:
    with open('channels_config.json', 'r') as f:
        channels_config = json.load(f)
except Exception as e:
    print(f"خطأ في تحميل الإعدادات: {e}")
    exit()

# معلومات الحساب
api_id = 22707838
api_hash = '7822c50291a41745fa5e0d63f21bbfb6'
session_name = 'my_session'

# الصلاحيات
allowed_chat_ids = {141117417}  # ← ضع معرفك هنا

# تهيئة العميل
client = TelegramClient(session_name, api_id, api_hash)
selected_channels = set()
monitoring_active = False

# معالجة الأوامر
async def handle_user_commands(event):
    global selected_channels, monitoring_active

    msg = event.raw_text.strip().lower()
    
    if msg == 's':
        if not selected_channels:
            await event.respond("❌ الرجاء اختيار القنوات أولاً!")
            return
            
        monitoring_active = True
        await event.respond("✅ تم تفعيل المراقبة بنجاح!")
        
    elif msg == 'st':
        selected_channels.clear()
        monitoring_active = False
        await event.respond("⏹ تم إيقاف المراقبة!")
        
    elif ',' in event.raw_text:
        channels = [name.strip() for name in event.raw_text.split(',')]
        valid = []
        invalid = []
        
        for name in channels:
            if name in channels_config:
                valid.append(name)
            else:
                invalid.append(name)
                
        if invalid:
            await event.respond(f"❌ قنوات غير صحيحة: {', '.join(invalid)}")
            
        if valid:
            selected_channels = set(valid)
            await event.respond(f"📡 القنوات المختارة: {', '.join(valid)}")

# معالجة المراقبة
async def monitor_handler(event):
    if not monitoring_active:
        return

    sender_id = event.chat_id
    
    for channel in selected_channels:
        config = channels_config.get(channel)
        if not config:
            continue
            
        try:
            config_id = int(config["chat_id"])
            config_bot = config["bot"].strip().lower()
            regex_pattern = config["regex"]
            pick_third = config.get("pick_third", False)
        except Exception as e:
            print(f"خطأ في إعدادات {channel}: {e}")
            continue

        if sender_id != config_id:
            continue

        try:
            matches = re.findall(regex_pattern, event.raw_text, re.IGNORECASE)
            if not matches:
                continue
                
            # اختيار الكود
            code = matches[2] if (pick_third and len(matches)>=3) else matches[0]
            
            # الإرسال المباشر
            await client.send_message(config_bot, code)
            print(f"✓ تم إرسال {code} → {config_bot}")
            await asyncio.sleep(1)
            
        except FloodWaitError as e:
            print(f"⏳ انتظر {e.seconds} ثانية بسبب FloodWait")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"🔥 خطأ في {channel}: {str(e)}")

# أوامر البوت
@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.chat_id not in allowed_chat_ids:
        return
        
    await event.respond(
        "مرحباً بكم في بوت المراقبة الذكية!\n\n"
        "📌 كيفية الاستخدام:\n"
        "1. أرسل أسماء القنوات (مفصولة بفاصلة)\n"
        "2. أرسل 's' للبدء\n"
        "3. أرسل 'st' للإيقاف\n\n"
        "مثال:\nichancy_malaki, captain_ichancy"
    )

# توجيه الرسائل
@client.on(events.NewMessage)
async def main_handler(event):
    if event.chat_id in allowed_chat_ids:
        await handle_user_commands(event)
    elif monitoring_active:
        await monitor_handler(event)

# تشغيل السيرفر
async def web_server():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Bot Active!"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 8080).start()

# بدء التشغيل
async def start():
    await client.start()
    await web_server()
    print("Bot is Running...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(start())
