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
    return "Fokhm Filtered Bot is running 24/7!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

account_2 = {
    "name": "الحساب الثاني",
    "api_id": 31810940,
    "api_hash": "b7e3840acf3bb4203d1cfbcc7e1161c1",
    "session": "1BJWap1sBu6yRTcqEiyyIzE56J8aNRfbll8Cn81MmOyG6gDb3pJb_A2unFs1r0PbCQ97BDfsTPP3R7ta8Q_DXR7CEa7W5-32PmdV4GBtPYWOKJv154bZoguhVvRtA2444Jqhwzvym5VlYXVU4rL7ecCVyQ6C1t12jrGAcT09ySSh07PXeQGdAoJVGxRxAnJHdfbWfOC76HtKBYIDlIYTGTrCU0nlDo6TIKJIX9nPZ9-b86XaaCp0BPnb9rt1qPvmOUi41h_sKsJ9WSLmnRP1tfOOOcUr7JMWuTVwzGzC2rfo_kufh0pAtHngAzufeK2RbMdpPliRhOvd5GuM0i_hDbCS-9X_mxgE=",
    "delay": 30  # فاصل زمني 30 ثانية لكل إضافة
}

target_group = "@da7k16"
report_target = "@hackWahm"

async def run_filtered_bot(acc):
    client = TelegramClient(StringSession(acc['session']), acc['api_id'], acc['api_hash'])
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            await client.send_message(report_target, f"🚨 **خطأ في {acc['name']}**\n❌ الجلسة غير صالحة أو تم تسجيل الخروج منها!")
            return

        me = await client.get_me()
        print(f"🚀 [{acc['name']}] تم الاتصال بنجاح باسم: {me.first_name}")
        
        entity = await client.get_entity(target_group)
        
        # جلب أعضاء القروب الحاليين بدقة وتخزين أيديهم
        print("🔍 جاري جلب أعضاء القروب الحاليين...")
        group_participants = set()
        async for user in client.iter_participants(entity):
            group_participants.add(user.id)
        
        total_in_group_count = len(group_participants)
        
        # جلب جهات الاتصال وفلترة المنقطعين (أكثر من 25 يوم)
        result = await client(GetContactsRequest(hash=0))
        now = datetime.now(timezone.utc)
        
        total_contacts_count = len(result.users)
        
        # فلترة المنقطعين فقط
        offline_targets = [u for u in result.users if not (u.bot or u.deleted) and 
                           (isinstance(u.status, (UserStatusLastMonth, UserStatusEmpty)) or 
                           (isinstance(u.status, UserStatusOffline) and (now - u.status.was_online).days >= 25))]
        
        total_offline_count = len(offline_targets)
        
        # استبعاد الموجودين في القروب مسبقاً نهائياً
        final_targets = [u for u in offline_targets if u.id not in group_participants]
        already_in_group_from_offline = total_offline_count - len(final_targets)
        
        print(f"🎯 إجمالي جهات الاتصال: {total_contacts_count}")
        print(f"🎯 المنقطعين أكثر من 25 يوم: {total_offline_count}")
        print(f"🎯 الموجودين مسبقاً بالقروب وتم استبعادهم: {already_in_group_from_offline}")
        print(f"🎯 الصافي للبدء بإضافتهم: {len(final_targets)}")
        
        if len(final_targets) == 0:
            await client.send_message(report_target, f"⚠️ **تنبيه {acc['name']}**: كل الأعضاء المنقطعين موجودين بالقروب أصلًا، لا يوجد أحد ليتم إضافته.")
            await client.disconnect()
            return

        # إرسال التقرير التفصيلي الأول لحسابك
        status_msg = await client.send_message(
            report_target, 
            f"🤖 **تقرير تشغيل {acc['name']} (المفلتر)**\n"
            f"👥 إجمالي أعضاء القروب الحاليين: {total_in_group_count}\n"
            f"📋 إجمالي جهات الاتصال: {total_contacts_count}\n"
            f"⏱️ منقطع > 25 يوم: {total_offline_count}\n"
            f"🚫 تم استبعادهم (موجودين بالقروب): {already_in_group_from_offline}\n"
            f"🎯 **الصافي للإضافة الجديدة:** {len(final_targets)} عضو\n"
            f"⏳ جاري بدء الإضافات بدقة..."
        )
        
        success_added = 0
        current_group_count = total_in_group_count
        total_to_add = len(final_targets)
        
        for idx, user in enumerate(final_targets, 1):
            try:
                if not user.access_hash:
                    continue
                
                await client(InviteToChannelRequest(channel=entity, users=[InputPeerUser(user.id, user.access_hash)]))
                success_added += 1
                current_group_count += 1
                remaining = total_to_add - success_added
                
                # تحديث الرسالة بالمعلومات الفورية
                await status_msg.edit(
                    f"🤖 **تقرير {acc['name']} (نشط ومفلتر)**\n"
                    f"📊 تم إضافة: {success_added} من أصل {total_to_add}\n"
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
            f"🏁 **انتهت مهمة {acc['name']} بنجاح التام**\n"
            f"✅ إجمالي من تمت إضافتهم: {success_added} عضو.\n"
            f"👥 إجمالي أعضاء القروب النهائي: {current_group_count}"
        )
        await client.disconnect()
        
    except Exception as e:
        print(f"خطأ رئيسي: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(run_filtered_bot(account_2))
