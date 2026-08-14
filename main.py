import asyncio
import threading
from datetime import datetime, timezone
from flask import Flask
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.functions.channels import InviteToChannelRequest, GetFullChannelRequest
from telethon.tl.types import InputPeerUser, UserStatusOffline, UserStatusLastMonth, UserStatusEmpty
from telethon.errors import FloodWaitError

# --- إعداد سيرفر الـ Flask للحفاظ على المشروع شغال 24/7 على Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Fokhm Bot is running 24/7 successfully!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# --- بيانات الحسابات ---
accounts = [
    {
        "name": "الحساب الأول",
        "api_id": 31810940,
        "api_hash": "b7e3840acf3bb4203d1cfbcc7e1161c1",
        "session": "1BJWap1sBu13vh5kZYyhHRep5o1dDSE6aRzN5pTK8bN7qH6bHO5DjoLRCgZ04A-O8II1nTWGvIoztNqmx3lyO20uCdVLvaXocl4HrSxrM3uT1SXbeFZ_X7e-cvFkDNfK6gIeyVSC4RPNfBkUWPFKdxo18ezU5PNyfKG6v7gGtNl4QqwR-WMoZiEzLP1OwEfuMIkGc7_xfVVLDk9yOm2Yl8zt5ZBcdCBHWwSpRYOE9Ei0T_k4Y0rBr3JlrwEPCHFJsn-AF8B6ru7maTLGk1qHcEzBhRJiA_QCnEnDg1Rn1jp-KDsWAugYh7NES11WrHQjYR3L5tN6qpY9diHCP6mdvcFp_WF4SPd4="
    },
    {
        "name": "الحساب الثاني",
        "api_id": 31810940,
        "api_hash": "b7e3840acf3bb4203d1cfbcc7e1161c1",
        "session": "1BJWap1sBu6yRTcqEiyyIzE56J8aNRfbll8Cn81MmOyG6gDb3pJb_A2unFs1r0PbCQ97BDfsTPP3R7ta8Q_DXR7CEa7W5-32PmdV4GBtPYWOKJv154bZoguhVvRtA2444Jqhwzvym5VlYXVU4rL7ecCVyQ6C1t12jrGAcT09ySSh07PXeQGdAoJVGxRxAnJHdfbWfOC76HtKBYIDlIYTGTrCU0nlDo6TIKJIX9nPZ9-b86XaaCp0BPnb9rt1qPvmOUi41h_sKsJ9WSLmnRP1tfOOOcUr7JMWuTVwzGzC2rfo_kufh0pAtHngAzufeK2RbMdpPliRhOvd5GuM0i_hDbCS-9X_mxgE="
    }
]

target_group = "@da7k16"
report_target = "@hackWahm"

async def worker_bot(acc_data):
    try:
        client = TelegramClient(StringSession(acc_data['session']), acc_data['api_id'], acc_data['api_hash'])
        await client.connect()
        
        me = await client.get_me()
        print(f"✅ تم الاتصال بنجاح بـ {acc_data['name']} ({me.first_name})")
        
        entity = await client.get_entity(target_group)
        
        # سحب جهات الاتصال وفلترة المنقطعين (أكثر من 25 يوم)
        result = await client(GetContactsRequest(hash=0))
        now = datetime.now(timezone.utc)
        target_users = [u for u in result.users if not (u.bot or u.deleted) and 
                        (isinstance(u.status, (UserStatusLastMonth, UserStatusEmpty)) or 
                        (isinstance(u.status, UserStatusOffline) and (now - u.status.was_online).days >= 25))]
        
        print(f"🎯 {acc_data['name']} وجد {len(target_users)} عضو منقطع")
        
        if not target_users:
            return

        status_msg = await client.send_message(report_target, f"🤖 تقرير {acc_data['name']}: جاري البدء في إضافة الأعضاء المنقطعين...")
        
        success_added = 0
        for user in target_users:
            try:
                if not user.access_hash:
                    continue
                await client(InviteToChannelRequest(channel=entity, users=[InputPeerUser(user.id, user.access_hash)]))
                success_added += 1
                await status_msg.edit(f"🤖 **تقرير {acc_data['name']} (نشط)**\n📊 تم إضافة: {success_added} من أصل {len(target_users)}")
                await asyncio.sleep(40) # فاصل زمني آمن لتجنب الحظر
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception:
                continue
        
        await status_msg.edit(f"🏁 **انتهت مهمة {acc_data['name']} بنجاح**\n✅ إجمالي المضافين: {success_added} عضو.")
        await client.disconnect()
    except Exception as e:
        print(f"❌ خطأ في تشغيل {acc_data['name']}: {e}")

async def main():
    # تشغيل الحسابين بالتوازي
    await asyncio.gather(*(worker_bot(acc) for acc in accounts))

if __name__ == "__main__":
    # تشغيل سيرفر الـ Flask في الخلفية
    threading.Thread(target=run_flask, daemon=True).start()
    # تشغيل سكرات التليجرام
    asyncio.run(main())

eof
خطوات الرفع على Render:
 * ارفع هذين الملفين في مستودع جديد على GitHub.
 * في لوحة تحكم Render، أنشئ New Web Service واربط المستودع.
 * في خانة Build Command حط:
   pip install -r requirements.txt

 * في خانة Start Command حط:
   python main.py




