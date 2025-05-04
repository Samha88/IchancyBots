import asyncio
import re
import json
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from aiohttp import web

# تحميل الإعدادات مع طباعة تأكيد
try:
    with open('channels_config.json', 'r') as f:
        channels_config = json.load(f)
    print("✓ تم تحميل ملف الإعدادات بنجاح")
except Exception as e:
    print(f"✖ خطأ في تحميل الإعدادات: {str(e)}")
    exit()

# معلومات الحساب
api_id = 22707838
api_hash = '7822c50291a41745fa5e0d63f21bbfb6'
session_name = 'my_session'

# الصلاحيات
allowed_chat_ids = {141117417}  # ← تأكد من صحة هذا الرقم

# تهيئة العميل
client = TelegramClient(session_name, api_id, api_hash)
selected_channels = set()
monitoring_active = False

# معالجة الأوامر مع تفاصيل التصحيح
async def handle_user_commands(event):
    global selected_channels, monitoring_active

    msg = event.raw_text.strip().lower()
    print(f"↻ تم استقبال أمر: '{msg}' من المستخدم {event.chat_id}")

    if msg == 's':
        if not selected_channels:
            print("✖ محاولة بدء المراقبة بدون قنوات محددة")
            await event.respond("❌ الرجاء اختيار القنوات أولاً!")
            return
            
        monitoring_active = True
        print(f"✓ بدء المراقبة على القنوات: {selected_channels}")
        await event.respond("✅ تم تفعيل المراقبة بنجاح!")
        
    elif msg == 'st':
        selected_channels.clear()
        monitoring_active = False
        print("⏹ توقف المراقبة")
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
            print(f"✖ قنوات غير صحيحة: {invalid}")
            await event.respond(f"❌ قنوات غير صحيحة: {', '.join(invalid)}")
            
        if valid:
            selected_channels = set(valid)
            print(f"✓ تحديد القنوات الجديد: {valid}")
            await event.respond(f"📡 القنوات المختارة: {', '.join(valid)}")

# معالجة المراقبة مع تفاصيل التصحيح
async def monitor_handler(event):
    if not monitoring_active:
        return

    sender_id = event.chat_id
    print(f"\n↻ رسالة واردة من ID: {sender_id}")
    print(f"📝 محتوى الرسالة: {event.raw_text[:50]}...")  # طباعة أول 50 حرف فقط

    for channel in selected_channels:
        print(f"\n🔎 جارِ فحص القناة: {channel}")
        
        config = channels_config.get(channel)
        if not config:
            print(f"✖ إعدادات غير موجودة للقناة {channel}")
            continue
            
        try:
            config_id = int(config["chat_id"])
            config_bot = config["bot"].strip().lower()
            regex_pattern = config["regex"]
            pick_third = config.get("pick_third", False)
            print(f"⚙ إعدادات القناة: ID={config_id}, Bot={config_bot}, PickThird={pick_third}")
        except Exception as e:
            print(f"✖ خطأ في إعدادات {channel}: {str(e)}")
            continue

        if sender_id != config_id:
            print(f"✖ ID المرسل ({sender_id}) لا يتطابق مع ID القناة ({config_id})")
            continue

        try:
            print(f"🔍 تطبيق الـ regex: {regex_pattern}")
            matches = re.findall(regex_pattern, event.raw_text, re.IGNORECASE)
            print(f"🔢 عدد التطابقات: {len(matches)}")
            
            if not matches:
                print("✖ لا توجد تطابقات")
                continue
                
            # اختيار الكود
            code = matches[2] if (pick_third and len(matches)>=3) else matches[0]
            print(f"⚡ الكود المستخرج: {code}")
            
            # محاولة الإرسال
            print(f"🚀 محاولة إرسال إلى {config_bot}")
            await client.send_message(config_bot, code)
            print(f"✓ تم الإرسال بنجاح إلى {config_bot}")
            await asyncio.sleep(1)
            
        except FloodWaitError as e:
            print(f"⏳ FloodWait: مطلوب انتظار {e.seconds} ثانية")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"✖ فشل الإرسال: {str(e)}")

# أوامر البوت
@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.chat_id not in allowed_chat_ids:
        print(f"✖ محاولة وصول غير مصرح بها من ID: {event.chat_id}")
        return
        
    print(f"✓ تشغيل البوت من قبل المستخدم {event.chat_id}")
    await event.respond(
        "مرحباً بكم في بوت المراقبة الذكية!\n\n"
        "📌 كيفية الاستخدام:\n"
        "1. أرسل أسماء القنوات (مفصولة بفاصلة)\n"
        "2. أرسل 's' للبدء\n"
        "3. أرسل 'st' للإيقاف\n\n"
        "مثال:\nichancy
