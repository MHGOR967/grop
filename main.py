import asyncio
import threading
from datetime import datetime, timezone
from flask import Flask
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import InputPeerUser, UserStatusOffline, UserStatusLastMonth, UserStatusEmpty
from telethon.errors import FloodWaitError, AuthKeyUnregisteredError, UserDeactivatedError

app = Flask(__name__)

@app.route('/')
def home():
    return "Fokhm Error-Tracking Bot is running 24/7!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

account_2 = {
    "name": "الحساب الثاني",
    "api_id": 31810940,
    "api_hash": "b7e3840acf3bb4203d1cfbcc7e1161c1",
    "session": "1BJWap1sBu6yRTcqEiyyIzE56J8aNRfbll8Cn81MmOyG6gDb3pJb_A2unFs1r0PbCQ97BDfsTPP3R7ta8Q_DXR7CEa7W5-32PmdV4GBtPYWOKJv154bZoguhVvRtA2444Jqhwzvym5VlYXVU4rL7ecCVyQ6C1t12jrGAcT09ySSh07PXeQGdAoJVGxRxAnJHdfbWfOC76HtKBYIDlIYTGTrCU0nlDo6TIKJIX9nPZ9-b86XaaCp0BPnb9rt1qPvmOUi41h_sKsJ9WSLmnRP1tfOOOcUr7JMWuTVwzGzC2rfo_kufh0pAtHngAzufeK2RbMdpPliRhOvd5GuM0i_hDbCS-9X_mxgE=",
    "delay": 35
}

target_group = "@da7k16"
report_target = "@hackWahm"

async def run_single_bot_with_error_reporting(acc):
    client = TelegramClient(StringSession(acc['session']), acc['api_id'], acc['api_hash'])
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            # إذا الجلسة سجلت خروج أو انلغت
            await client.send_message(report_target, f"🚨 **تنبيه خطأ حرّج في {acc['name']}**\n❌ الجلسة غير صالحة أو تم تسجیل الخروج منها من التيليجرام!")
            return

        me = await client.get_me()
        print(f"🚀 [{acc['name']}] تم الاتصال بنجاح باسم: {me.first_name}")
        
        entity = await client.get_entity(target_group)
        
        result = await client(GetContactsRequest(hash=0))
        now = datetime.now(timezone.utc)
        target_users = [u for u in result.users if not (u.bot or u.deleted) and 
                        (isinstance(u.status, (UserStatusLastMonth, UserStatusEmpty)) or 
                        (isinstance(u.status, UserStatusOffline) and (now - u.status.was_online).days >= 25))]
        
        if not target_users:
            await client.send_message(report_target, f"⚠️ **تنبيه {acc['name']}**: لا يوجد أعضاء مطابقين لشروط الفلترة (أكثر من 25 يوم).")
            await client.disconnect()
            return

        status_msg = await client.send_message(report_target, f"🤖 تقرير {acc['name']}: بدأ في إضافة الأعضاء المنقطعين ({len(target_users)} عضو)...")
        
        success_added = 0
        for user in target_users:
            try:
                if not user.access_hash:
                    continue
                await client(InviteToChannelRequest(channel=entity, users=[InputPeerUser(user.id, user.access_hash)]))
                success_added += 1
                await status_msg.edit(
                    f"🤖 **تقرير {acc['name']} (نشط)**\n"
                    f"📊 تم إضافة: {success_added} من أصل {len(target_users)}"
                )
                await asyncio.sleep(acc['delay'])
                
            except FloodWaitError as e:
                # إرسال تنبيه في حال الحظر المؤقت
                await client.send_message(report_target, f"⏳ **تنبيه حظر مؤقت (FloodWait)**\n👤 الحساب: {acc['name']}\n⏱️ سيتم الانتظار لمدة {e.seconds} ثانية بسبب ضغط التيليجرام.")
                await asyncio.sleep(e.seconds)
            except (AuthKeyUnregisteredError, UserDeactivatedError):
                await client.send_message(report_target, f"🚨 **خطأ فادح في {acc['name']}**\n❌ تم حظر الحساب أو تعطيل الجلسة نهائياً من التيليجرام!")
                break
            except Exception as err:
                # أي خطأ برمجي أو استثناء آخر يرسله لك مباشرة
                print(f"خطأ غير متوقع: {err}")
                continue
        
        await status_msg.edit(f"🏁 **انتهت مهمة {acc['name']}**\n✅ إجمالي المضافين: {success_added} عضو.")
        await client.disconnect()
        
    except Exception as e:
        # لو صار خطأ بالاتصال الأساسي يرسله لـ @hackwahn
        try:
            temp_client = TelegramClient(StringSession(acc['session']), acc['api_id'], acc['api_hash'])
            await temp_client.connect()
            await temp_client.send_message(report_target, f"🚨 **خطأ رئيسي في تشغيل {acc['name']}**\n`{str(e)}`")
            await temp_client.disconnect()
        except:
            pass

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(run_single_bot_with_error_reporting(account_2))
