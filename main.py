import asyncio
import threading
from datetime import datetime, timezone
from flask import Flask
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.functions.channels import InviteToChannelRequest, GetFullChannelRequest
from telethon.tl.types import InputPeerUser, UserStatusOffline, UserStatusLastMonth, UserStatusEmpty
from telethon.errors import FloodWaitError, AuthKeyUnregisteredError, UserDeactivatedError

app = Flask(__name__)

@app.route('/')
def home():
    return "Fokhm Smart Bot is running 24/7!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

account_2 = {
    "name": "الحساب الثاني",
    "api_id": 31810940,
    "api_hash": "b7e3840acf3bb4203d1cfbcc7e1161c1",
    "session": "1BJWap1sBu6yRTcqEiyyIzE56J8aNRfbll8Cn81MmOyG6gDb3pJb_A2unFs1r0PbCQ97BDfsTPP3R7ta8Q_DXR7CEa7W5-32PmdV4GBtPYWOKJv154bZoguhVvRtA2444Jqhwzvym5VlYXVU4rL7ecCVyQ6C1t12jrGAcT09ySSh07PXeQGdAoJVGxRxAnJHdfbWfOC76HtKBYIDlIYTGTrCU0nlDo6TIKJIX9nPZ9-b86XaaCp0BPnb9rt1qPvmOUi41h_sKsJ9WSLmnRP1tfOOOcUr7JMWuTVwzGzC2rfo_kufh0pAtHngAzufeK2RbMdpPliRhOvd5GuM0i_hDbCS-9X_mxgE=",
    "delay": 30  # فاصل زمني 30 ثانية لكل عضو
}

target_group = "@da7k16"
report_target = "@hackWahm"

async def run_smart_bot(acc):
    client = TelegramClient(StringSession(acc['session']), acc['api_id'], acc['api_hash'])
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            await client.send_message(report_target, f"🚨 **خطأ في {acc['name']}**\n❌ الجلسة غير صالحة أو تم تسجيل الخروج منها!")
            return

        me = await client.get_me()
        print(f"🚀 [{acc['name']}] تم الاتصال بنجاح باسم: {me.first_name}")
        
        entity = await client.get_entity(target_group)
        
        # 1. جلب عدد الأعضاء الحالي في القروب وأسماؤهم/أIDs لتجنب تكرار الإضافة
        full_chat = await client(GetFullChannelRequest(channel=entity))
        initial_participants_count = full_chat.full_chat.participants_count
        
        print("🔍 جاري جلب أعضاء القروب الحاليين لتجنب تكرارهم...")
        group_participants = set()
        async for user in client.iter_participants(entity):
            group_participants.add(user.id)
        
        # 2. سحب جهات الاتصال وفلترة المنقطعين (أكثر من 25 يوم)
        result = await client(GetContactsRequest(hash=0))
        now = datetime.now(timezone.utc)
        
        raw_targets = [u for u in result.users if not (u.bot or u.deleted) and 
                       (isinstance(u.status, (UserStatusLastMonth, UserStatusEmpty)) or 
                       (isinstance(u.status, UserStatusOffline) and (now - u.status.was_online).days >= 25))]
        
        # 3. استبعاد أي شخص موجود مسبقاً في القروب
        target_users = [u for u in raw_targets if u.id not in group_participants]
        
        total_targets = len(target_users)
        print(filter_msg := f"🎯 إجمالي المستهدفين الجدد (غير الموجودين بالقروب ومنقطعين > 25 يوم): {total_targets} عضو.")
        
        if total_targets == 0:
            await client.send_message(report_target, f"⚠️ **تنبيه {acc['name']}**: لايوجد أعضاء جدد مطابقين للشروط (كلهم بالقروب أو متصلين حديثاً).")
            await client.disconnect()
            return

        status_msg = await client.send_message(
            report_target, 
            f"🤖 **تقرير تشغيل {acc['name']} (الذكي)**\n"
            f"👥 أعضاء القروب حالياً: {initial_participants_count}\n"
            f"🎯 الباقي للإضافة: {total_targets} عضو\n"
            f"⏳ جاري بدء الإضافات..."
        )
        
        success_added = 0
        current_group_count = initial_participants_count
        
        for idx, user in enumerate(target_users, 1):
            try:
                if not user.access_hash:
                    continue
                
                await client(InviteToChannelRequest(channel=entity, users=[InputPeerUser(user.id, user.access_hash)]))
                success_added += 1
                current_group_count += 1
                remaining = total_targets - success_added
                
                # تعديل الرسالة بالمعلومات الدقيقة (كم صار، كم باقي، كم عدد القروب)
                await status_msg.edit(
                    f"🤖 **تقرير {acc['name']} (نشط)**\n"
                    f"📊 تم إضافة: {success_added} من {total_targets}\n"
                    f"⏳ المتبقي للإضافة: {remaining} عضو\n"
                    f"👥 عدد القروب الآن: {current_group_count}"
                )
                
                await asyncio.sleep(acc['delay'])
                
            except FloodWaitError as e:
                await client.send_message(report_target, f"⏳ **تنبيه حظر مؤقت (FloodWait)**\n⏱️ انتظار {e.seconds} ثانية...")
                await asyncio.sleep(e.seconds)
            except (AuthKeyUnregisteredError, UserDeactivatedError):
                await client.send_message(report_target, f"🚨 **خطأ حرّج**: تم حظر الحساب أو تعطيل جلسته!")
                break
            except Exception:
                continue
        
        await status_msg.edit(
            f"🏁 **انتهت مهمة {acc['name']} بنجاح**\n"
            f"✅ إجمالي من تم إضافتهم: {success_added} عضو.\n"
            f"👥 إجمالي أعضاء القروب النهائي: {current_group_count}"
        )
        await client.disconnect()
        
    except Exception as e:
        print(f"خطأ رئيسي: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(run_smart_bot(account_2))
