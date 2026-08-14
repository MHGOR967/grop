import asyncio
import threading
from datetime import datetime, timezone
from flask import Flask
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import InputPeerUser, UserStatusOffline, UserStatusLastMonth, UserStatusEmpty
from telethon.errors import FloodWaitError

app = Flask(__name__)

@app.route('/')
def home():
    return "Fokhm Bot Alternating Add is running 24/7!"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

accounts_data = [
    {
        "name": "الحساب الأول",
        "api_id": 31810940,
        "api_hash": "b7e3840acf3bb4203d1cfbcc7e1161c1",
        "session": "1BJWap1sBu13vh5kZYyhHRep5o1dDSE6aRzN5pTK8bN7qH6bHO5DjoLRCgZ04A-O8II1nTWGvIoztNqmx3lyO20uCdVLvaXocl4HrSxrM3uT1SXbeFZ_X7e-cvFkDNfK6gIeyVSC4RPNfBkUWPFKdxo18ezU5PNyfKG6v7gGtNl4QqwR-WMoZiEzLP1OwEfuMIkGc7_xfVVLDk9yOm2Yl8zt5ZBcdCBHWwSpRYOE9Ei0T_k4Y0rBr3JlrwEPCHFJsn-AF8B6ru7maTLGk1qHcEzBhRJiA_QCnEnDg1Rn1jp-KDsWAugYh7NES11WrHQjYR3L5tN6qpY9diHCP6mdvcFp_WF4SPd4=",
        "delay": 35  # ينتظر 35 ثانية بعد إضافته
    },
    {
        "name": "الحساب الثاني",
        "api_id": 31810940,
        "api_hash": "b7e3840acf3bb4203d1cfbcc7e1161c1",
        "session": "1BJWap1sBu6yRTcqEiyyIzE56J8aNRfbll8Cn81MmOyG6gDb3pJb_A2unFs1r0PbCQ97BDfsTPP3R7ta8Q_DXR7CEa7W5-32PmdV4GBtPYWOKJv154bZoguhVvRtA2444Jqhwzvym5VlYXVU4rL7ecCVyQ6C1t12jrGAcT09ySSh07PXeQGdAoJVGxRxAnJHdfbWfOC76HtKBYIDlIYTGTrCU0nlDo6TIKJIX9nPZ9-b86XaaCp0BPnb9rt1qPvmOUi41h_sKsJ9WSLmnRP1tfOOOcUr7JMWuTVwzGzC2rfo_kufh0pAtHngAzufeK2RbMdpPliRhOvd5GuM0i_hDbCS-9X_mxgE=",
        "delay": 20  # ينتظر 20 ثانية بعد إضافته
    }
]

target_group = "@da7k16"
report_target = "@hackWahm"

async def prepare_client(acc):
    client = TelegramClient(StringSession(acc['session']), acc['api_id'], acc['api_hash'])
    await client.connect()
    me = await client.get_me()
    entity = await client.get_entity(target_group)
    
    # فلترة المنقطعين (أكثر من 25 يوم)
    result = await client(GetContactsRequest(hash=0))
    now = datetime.now(timezone.utc)
    target_users = [u for u in result.users if not (u.bot or u.deleted) and 
                    (isinstance(u.status, (UserStatusLastMonth, UserStatusEmpty)) or 
                    (isinstance(u.status, UserStatusOffline) and (now - u.status.was_online).days >= 25))]
    
    status_msg = await client.send_message(report_target, f"🤖 تقرير {acc['name']} (بالتناوب): جاهز ويحتوي على {len(target_users)} عضو مستهدف.")
    return client, entity, target_users, status_msg

async def main():
    clients = []
    
    # تجهيز الحسابين واللستات الخاصة بهم
    for acc in accounts_data:
        client, entity, target_users, status_msg = await prepare_client(acc)
        clients.append({
            "name": acc['name'],
            "client": client,
            "entity": entity,
            "users": target_users,
            "msg": status_msg,
            "delay": acc['delay'],
            "index": 0,
            "success": 0
        })

    # حلقة التناوب المستمرة (واحد يضيف، ينتظر، ثم الثاني يضيف، وهكذا)
    active = True
    while active:
        active = False
        for item in clients:
            idx = item["index"]
            users = item["users"]
            
            if idx < len(users):
                active = True
                user = users[idx]
                item["index"] += 1
                
                try:
                    if user.access_hash:
                        await item["client"](InviteToChannelRequest(channel=item["entity"], users=[InputPeerUser(user.id, user.access_hash)]))
                        item["success"] += 1
                        await item["msg"].edit(
                            f"🤖 **تقرير {item['name']} (بالتناوب نشط)**\n"
                            f"📊 تم إضافة: {item['success']} من أصل {len(users)}"
                        )
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                except Exception:
                    pass
                
                # الانتظار الخاص بكل حساب (الأول 35 ثانية، الثاني 20 ثانية) قبل الانتقال للحساب التالي
                await asyncio.sleep(item["delay"])

    # إغلاق الجلسات عند انتهاء الجميع
    for item in clients:
        await item["msg"].edit(f"🏁 **انتهت مهمة {item['name']} بالتناوب**\n✅ الإجمالي: {item['success']} عضو.")
        await item["client"].disconnect()

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
