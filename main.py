from cachetools import TTLCache
from concurrent.futures import ThreadPoolExecutor
from mysql.connector import pooling
import time
import requests
import mysql.connector
from datetime import datetime
import re
import threading
import os
from dotenv import load_dotenv


# --- Configuration ---
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PLUS_API_TOKEN = os.getenv("PLUS_API_TOKEN")
ECO_API_TOKEN = os.getenv("ECO_API_TOKEN")

url = f"https://tapi.bale.ai/bot{BOT_TOKEN}/"
PLUS_API_URL = "https://billapi.saapa.ir/api/ebills/GetBranchData"
ECO_API_URL = f"https://Api.BrsApi.ir/Tsetmc/AllSymbols.php?key={ECO_API_TOKEN}"


VIDEO_FILE_ID_BARGHAPP = "729844006:-1772778552087404798:0:74d2d6c270bf5f3a"
VIDEO_FILE_ID_BARGHAPP_PLUS = "729844006:-4959229794132156669:1:331a1e8fd9e9a453c6a8c17c7598b7d822b5230a7b97b0b8220dbf5ee590e009"
VIDEO_FILE_ID_BILL_ANALISYS = "979506434:-7685644890619699455:0:d3c347137c95d2066ba40647ee2f36711c6a2f3cfa2833b7"
VIDEO_FILE_ID_BARGHAPP_ECO = "979506434:6208782014560608003:0:9332c0020b754fae"
VIDEO_FILE_ID_BARGHAPP_PRO = "979506434:-8089179457806917886:0:ede5ddcc9f79721ad0a2a21dc4f0d69ce07238ba14ea2788"
PHOTO_FILE_ID_BARGHAPP_MICRO = "979506434:-8728860915684532477:0:86a008b634d5055158a593e0bf5872f9059984441def4b9c774c770bd4b5d8c0"
PHOTO_FILE_ID_BARGHAPP_PLUS = "979506434:6709060227557826306:0:15067b579ecb88e32282d227bf2ba552632d15e2fa6c4b8fe9c045c5e9ba11523c7b7805ace94705"
VIDEO_FILE_ID_BARGHAPP_MARKET = "729844006:-1136604059151032574:0:8850bf0d68f60f23"
VIDEO_FILE_ID_DARBAREH_BARGHAPP = "729844006:-1772778552087404798:0:74d2d6c270bf5f3a"
CHANNEL = "@barghapp"
executor = ThreadPoolExecutor(max_workers=32)

# # --PLUS API SESSION --
# app = FastAPI(title="BarghApp Dynamic API")
#
#
# # اطلاعات اتصال به دیتابیس
# DB_USER = "root"
# DB_PASSWORD = "1379Arta1380*"
# DB_HOST = "localhost"
# DB_PORT = "3306"
# DB_NAME = "barghappbot"
#
# DATABASE_URL = f"mysql+pymysql://{"root"}:{"1379Arta1380*"}@{"localhost"}:{"3306"}/{"barghappbot"}?charset=utf8mb4"
#
# engine = create_engine(DATABASE_URL, pool_pre_ping=True)
#
# # فقط این جدول‌ها مجاز هستند
# TABLE_MAP = {
#     "plus": "barghapp_plus"
#     # "eco": "barghapp-eco",
#     # "micro": "barghapp-micro",
#     # "market": "barghapp-market",
# }
#
# @app.get("/api/data/{table_key}")
# def get_table_data(
#     table_key: str,
#     limit: int = Query(20, ge=1, le=500),
#     offset: int = Query(0, ge=0)
# ):
#     # بررسی معتبر بودن نام جدول
#     if table_key not in TABLE_MAP:
#         raise HTTPException(status_code=400, detail="Invalid table name")
#
#     table_name = TABLE_MAP[table_key]
#
#     try:
#         with engine.connect() as conn:
#             query = text(f"SELECT * FROM `{table_name}` LIMIT :limit OFFSET :offset")
#             result = conn.execute(query, {"limit": limit, "offset": offset})
#
#             rows = result.mappings().all()
#
#             return {
#                 "success": True,
#                 "table": table_key,
#                 "real_table": table_name,
#                 "count": len(rows),
#                 "data": rows
#             }
#
#     except SQLAlchemyError as e:
#         raise HTTPException(status_code=500, detail=str(e))
#

# --ECO API SESSION --

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://brsapi.ir/",
    "Origin": "https://brsapi.ir"
})
# generating the pool
dbconfig = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}
connection_pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=32, **dbconfig)


def normalize_digits(text):
    if not text:
        return text

    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"
    table = str.maketrans(persian_digits, english_digits)
    return text.translate(table)


def log_message(message):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"

        print(formatted_message)

        with open("bot.log", "a", encoding="utf-8") as f:
            f.write(formatted_message + "\n")

    except Exception as e:
        print(f"LOG ERROR: {e}")


# --- data access ---

# تنظیمات برای توابعی که نیاز به اتصال مستقیم دارند (مثل initialize_database)
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

# ---------------- UTIL ----------------

def validate_bill_id(bill_id: str) -> bool:
    if not bill_id:
        return False

    # تبدیل اعداد فارسی به انگلیسی
    bill_id = normalize_digits(str(bill_id).strip())

    # فقط 13 رقم عددی
    return bool(re.fullmatch(r"\d{13}", bill_id))


def initialize_database():
    try:
        db_init = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        c = db_init.cursor()
        c.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}`;")
        c.execute(f"USE `{DB_CONFIG['database']}`;")

        # جدول کاربران (barghapp-users)
        c.execute("""
                  CREATE TABLE IF NOT EXISTS `BarghAppBot_users`
                  (
                      chat_id BIGINT PRIMARY KEY,
                      first_name VARCHAR (100),
                      last_name VARCHAR (100),
                      phone VARCHAR (30),
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                      );
                  """)
        # جدول کاربران پلاس (barghapp-plus)
        c.execute("""
                  CREATE TABLE IF NOT EXISTS barghapp_plus
                  (
                      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                      phone VARCHAR ( 30 ) NOT NULL,
                      bill_identifier VARCHAR (100) NOT NULL,
                      contract_demand FLOAT NULL,
                      customer_name VARCHAR (100) NULL,
                      request_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                      phone_query_count INT NOT NULL DEFAULT 1,
                      PRIMARY KEY
                      (phone,bill_identifier),
                      UNIQUE KEY uq_barghapp_plus_id(id)
                      );
                  """)
        # جدول کاربران مایکرو (barghapp-micro)
        c.execute("""
                  CREATE TABLE IF NOT EXISTS barghapp_micro
                  (
                      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
                      plant_type
                      VARCHAR (100) NOT NULL ,
                      first_name VARCHAR(150) NOT NULL,
                      phone VARCHAR(30) NOT NULL,
                      contor_number VARCHAR(100) DEFAULT NULL,
                      generation FLOAT DEFAULT NULL,
                      is_supported BOOLEAN NOT NULL DEFAULT FALSE,
                      support_organization VARCHAR (150) DEFAULT NULL,
                      contract_type VARCHAR (100) DEFAULT NULL,
                      price DECIMAL (12, 2) DEFAULT NULL,
                      didar_lead_id VARCHAR (100) DEFAULT NULL,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      PRIMARY KEY (id)
                      );
                  """)

        db_init.commit()
        c.close()
        db_init.close()
        log_message("✅ DB initialized.")
        return True
    except mysql.connector.Error as err:
        log_message(f"❌ DB init error: {err}")
        return False


# --- Global Variables ---

last_update_id = None
user_states = TTLCache(maxsize=10000, ttl=43200)
user_temp_data = TTLCache(maxsize=10000, ttl=43200)


def sync_to_didar_initial(full_name, phone):
    DIDAR_API_KEY = os.getenv("DIDAR_API_KEY")
    save_url = f"https://app.didar.me/api/contact/save?apikey={DIDAR_API_KEY}"

    search_url = f"https://app.didar.me/api/contact/PersonSearch?apikey={DIDAR_API_KEY}"

    # --- استانداردسازی شماره تلفن به فرمت: 09123456789 ---
    formatted_phone = str(phone).strip().replace("+", "")
    if formatted_phone.startswith("98"):
        formatted_phone = "0" + formatted_phone[2:]
    elif not formatted_phone.startswith("0"):
        formatted_phone = "0" + formatted_phone


    payload = {
        "Contact": {
            "FirstName": full_name,
            "LastName": "",
            "MobilePhone": formatted_phone
        }
    }

    try:
        response = requests.post(save_url, json=payload, headers={'Content-Type': 'application/json'})

        # حالت ۱: ذخیره موفقیت‌آمیز مخاطب جدید
        if response.status_code == 200:
            return response.json().get("Id")

        # حالت ۲: مخاطب تکراری است (خطای 400)
        if response.status_code == 400:
            log_message("Contact duplicate detected. Searching via PersonSearch...")

            # استفاده از ۱۰ رقم آخر شماره برای حل مشکل پیش‌شماره‌ها (مانند 9123456789)
            search_keyword = formatted_phone[-10:]
            log_message(f"Searching Didar with 10-digit keyword: {search_keyword}")

            search_payload = {
                "Criteria": {
                    "IsDeleted": 0,
                    "IsPinned": -1,
                    "IsVIP": -1,
                    "LeadType": -1,
                    "Keywords": search_keyword,
                    "Pin": -1,
                    "SortOrder": 1,
                    "SearchFromTime": "1930-01-01T00:00:00.000Z",
                    "SearchToTime": "9999-12-01T00:00:00.000Z",
                    "CustomFields": [],
                    "FilterId": None
                },
                "From": 0,
                "Limit": 30
            }

            res = requests.post(search_url, json=search_payload, headers={'Content-Type': 'application/json'})

            if res.status_code == 200:
                res_data = res.json()
                items = res_data.get("Response", {}).get("List", [])

                if items:
                    contact_id = items[0].get("Id")
                    log_message(f"✅ Successfully found duplicate contact ID: {contact_id}")
                    return contact_id
                else:
                    log_message(f"⚠️ Search API executed successfully for {search_keyword}, but List was empty.")
            else:
                log_message(f"Search API error: Status {res.status_code} - {res.text}")

            return None

    except Exception as e:
        log_message(f"Exception in sync_to_didar: {e}")
        return None


def create_deal_in_didar(contact_id, first_name, title=None, total_value=0, extra_fields=None, items=None):
    DIDAR_API_KEY = os.getenv("DIDAR_API_KEY")

    url = f"https://app.didar.me/api/deal/save_v2?apikey={DIDAR_API_KEY}"
    headers = {'Content-Type': 'application/json'}

    # استفاده از first_name برای عنوان معامله
    deal_title = title if title else f"{first_name} - API"

    payload = {
        "Deal": {
            "Title": deal_title,
            "PersonId": contact_id,
            "OwnerId": "482479e5-ee80-4ba0-a5f2-3211fc91a871",
            "PipelineStageId": "e98b59a1-f02d-4466-b49d-2ba14bd4ae6e",
            "ExpectedCloseDate": None,
            "SourceId": "c6ad5a3c-3530-468d-a545-8c8603bb9ef3",
            "TotalValue": total_value,
            "Field_9961_4_2": "ربات بله",
            "Fields": extra_fields if extra_fields is not None else {}
        },
        "DealItems": items if items is not None else []
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None



# --- HOME ELECTRICAL EQUIPMENTS --- (CATEGORIES AND DETAILS)

APPLIANCE_CATEGORIES = {
    "cat_kitchen": [
        "fridge_low", "fridge_high",
        "washing_machine_low", "washing_machine_high",
        "dishwasher_low", "dishwasher_high",
        "oven_low", "oven_high"
    ],

    "cat_climate": [
        "water_cooler_low", "water_cooler_high",
        "gas_cooler_low", "gas_cooler_high",
        "gas_super_heater_low",
        "electric_super_heater_low", "electric_super_heater_high"
    ],

    "cat_media": [
        "lights_low", "lights_high",
        "tv_low", "tv_high"
    ],

    "cat_other": [
        "water_pump_low", "water_pump_high",
        "others_low", "others_high"
    ]
}
APPLIANCE_DETAILS = {
    "fridge_low": ("یخچال فریزر کم‌مصرف", 25, 35),
    "fridge_high": ("یخچال فریزر پرمصرف", 50, 70),
    "washing_machine_low": ("ماشین لباسشویی کم‌مصرف", 10, 15),
    "washing_machine_high": ("ماشین لباسشویی پرمصرف", 25, 40),
    "tv_low": ("تلویزیون کم‌مصرف", 6, 12),
    "tv_high": ("تلویزیون پرمصرف", 20, 40),
    "lights_low": ("روشنایی خانه کم‌مصرف", 20, 40),
    "lights_high": ("روشنایی خانه پرمصرف", 60, 120),
    "water_cooler_low": ("کولر آبی کم‌مصرف", 50, 90),
    "water_cooler_high": ("کولر آبی پرمصرف", 120, 200),
    "gas_cooler_low": ("کولر گازی کم‌مصرف", 150, 300),
    "gas_cooler_high": ("کولر گازی پرمصرف", 350, 700),
    "water_pump_low": ("پمپ آب خانگی کم‌مصرف", 5, 10),
    "water_pump_high": ("پمپ آب خانگی پرمصرف", 15, 30),
    "gas_super_heater_low": ("آبگرمکن گازی (مصرف برق ناچیز)", 0, 0),
    "electric_super_heater_low": ("آبگرمکن برقی کم‌مصرف", 80, 120),
    "electric_super_heater_high": ("آبگرمکن برقی پرمصرف", 150, 250),
    "oven_low": ("فر و مایکروفر کم‌مصرف", 8, 15),
    "oven_high": ("فر و مایکروفر پرمصرف", 20, 40),
    "dishwasher_low": ("ماشین ظرفشویی کم‌مصرف", 20, 30),
    "dishwasher_high": ("ماشین ظرفشویی پرمصرف", 40, 60),
    "others_low": ("سایر لوازم کم‌مصرف", 10, 20),
    "others_high": ("سایر لوازم پرمصرف", 30, 60),

}


# --- Helper Functions ---


def send_delayed_sms(phone, message_text, delay_seconds=300):
    def worker():
        # ۱. اصلاح دقیق فرمت شماره موبایل
        formatted_phone = str(phone).strip().replace("+", "")
        if formatted_phone.startswith("0"):
            formatted_phone = "98" + formatted_phone[1:]
        elif not formatted_phone.startswith("98"):
            formatted_phone = "98" + formatted_phone

        url = "https://panel.asanak.com/webservice/v2rest/sendsms"
        payload = {
            'username': os.getenv("SMS_USERNAME"),
            'password': os.getenv("SMS_PASSWORD"),
            'source': os.getenv("SMS_SOURCE"),
            'message': message_text,
            'destination': formatted_phone
        }

        headers = {
            "Authorization": f"Bearer {os.getenv('SMS_BEARER_TOKEN')}"
        }

        try:
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            log_message(
                f"✅ SMS Worker Status for {formatted_phone}: HTTP {response.status_code} | Body: {response.text}")
        except Exception as e:
            log_message(f"❌ SMS Worker Exception for {formatted_phone}: {e}")

    # در صورت وجود تأخیر از Thread استفاده می‌شود، در غیر این صورت بلافاصله ارسال می‌گردد
    if delay_seconds > 0:
        threading.Timer(delay_seconds, worker).start()
        log_message(f"⏳ SMS scheduled for {phone} to be sent in {delay_seconds} seconds.")
    else:
        worker()
        log_message(f"📩 SMS triggered immediately for {phone}.")


def authenticate_and_get_token():
    auth_url = "https://billapi.saapa.ir/api/Users/authenticate"

    payload = {
        "username": "behpardaz",
        "password": "F>nP#R<WW&2tZhGX"
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            auth_url,
            json=payload,
            headers=headers,
            timeout=20
        )

        log_message(f"AUTH STATUS: {response.status_code}")
        log_message(f"AUTH RAW RESPONSE: {response.text}")

        if response.status_code != 200:
            log_message("❌ Authentication failed (HTTP error)")
            return None

        result = response.json()

        if result.get("status") != 200:
            log_message("❌ Authentication failed (API status)")
            return None

        token = result.get("data", {}).get("token")

        if not token:
            log_message("❌ Token not found in response")
            return None

        log_message(f"✅ API TOKEN RECEIVED: {token}")
        return token

    except Exception as e:
        log_message(f"❌ AUTH ERROR: {e}")
        return None


# ---------------- PLUS API ----------------
def check_bill_from_api(bill_id):
    bill_id = normalize_digits(bill_id)

    headers = {
        "Authorization": f"Bearer {PLUS_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"BILL_IDENTIFIER": bill_id}

    for attempt in range(3):
        try:
            log_message(f"Checking bill {bill_id} (attempt {attempt + 1})")
            resp = requests.post(PLUS_API_URL, headers=headers, json=payload, timeout=30)
            log_message(f"STATUS: {resp.status_code} BODY: {resp.text[:500]}")

            if resp.status_code == 400:
                log_message(f"INVALID BILL ID => {bill_id}")
                return "INVALID_BILL", None, None

            if resp.status_code != 200:
                time.sleep(2)
                continue

            result = resp.json()
            if result.get("status") != 200:
                return "SERVER_ERROR", None, None

            data = result.get("data")

            if not data:
                return "NOT_FOUND", None, None

            bill_identifier = data.get("bill_identifier")
            power = data.get("contract_demand")
            customer_name = data.get("customer_name")
            subscription_id = data.get("subscription_id")

            # تشخیص شناسه قبض نامعتبر
            if (
                    subscription_id == 0
                    and (power == 0 or power is None)
            ):
                log_message(f"INVALID BILL => {data}")
                return "NOT_FOUND", None, None

            if not bill_identifier or power is None:
                return "NOT_FOUND", None, None

            power = float(power)

            if power >= 150:
                return "OVER_150", power, customer_name
            else:
                return "UNDER_150", power, customer_name

        except requests.exceptions.Timeout:
            time.sleep(2)
        except Exception as e:
            log_message(f"API ERROR: {e}")
            return "SERVER_ERROR", None, None

    return "SERVER_ERROR", None, None


def get_govahei_price():
    # دریافت قیمت آخرین معامله گواهی صرفه جویی از API به تومان
    url_api = "https://api.brsapi.ir/Tsetmc/Symbol.php?key=YOUR-KEY=%D8%B5%D8%A8%D8%B1%D9%8205%D8%B9"
    try:
        response = requests.get(url_api, timeout=5)
        if response.status_code == 200:
            data = response.json()
            price_rial = data.get("pl", 0)
            if price_rial:
                # تبدیل ریال به تومان
                return int(price_rial) // 10
    except Exception as e:
        print(f"Error fetching API: {e}")

    return 3300  # مقدار پیش‌فرض در صورت خطا در شبکه یا ای‌پی‌آی

def get_enter_platform_keyboard(bill_id: str):
    bill_id = normalize_digits(bill_id)
    return {
        "inline_keyboard": [
            [{"text": "🔐 ورود به سامانه خرید برق", "url": "https://plus.barghapp.app"}],
            [{"text": "استعلام شناسه قبض دیگر", "callback_data": "buy_power"}],
            [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
        ]
    }


def upsert_plus_query(phone, bill_identifier, contract_demand, customer_name, db, cursor):
    bill_identifier = normalize_digits(str(bill_identifier))
    try:
        cursor.execute(
            """
            INSERT INTO barghapp_plus
            (phone, bill_identifier, contract_demand, customer_name, request_time, phone_query_count)
            VALUES (%s, %s, %s, %s, NOW(), 1) ON DUPLICATE KEY
            UPDATE
                contract_demand=VALUES(contract_demand), 
                customer_name=VALUES(customer_name), 
                request_time=NOW(), 
                phone_query_count=phone_query_count + 1
            """,
            (phone, bill_identifier, contract_demand, customer_name)
        )
        db.commit()
    except Exception as e:
        db.rollback()
        log_message(f"upsert_plus error: {e}")



def send_message(chat_id, text, reply_markup=None):
    """Sends a message to the specified chat_id."""
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        response = requests.post(url + "sendMessage", json=payload, timeout=10)
        log_message(response.text)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        log_message(f"❌ Failed to send message to {chat_id}: {e}")
        return None


def send_video(chat_id, video_file_id, caption, reply_markup=None):
    """Sends a video to the specified chat_id."""
    payload = {"chat_id": chat_id, "video": video_file_id, "caption": caption}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        response = requests.post(url + "sendVideo", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        log_message(f"❌ Failed to send video to {chat_id}: {e}")
        return None


def get_and_log_photo_id(message):
    """
    بررسی می‌کند که آیا پیام حاوی عکس است یا خیر.
    در صورت وجود عکس، آیدی بزرگترین سایز آن را لاگ کرده و برمی‌گرداند.
    """
    if "photo" in message:
        # عکس‌ها به صورت لیستی از سایزهای مختلف ارسال می‌شوند
        # آخرین ایندکس [-1] معمولاً بالاترین کیفیت و سایز اصلی است
        highest_quality_photo = message["photo"][-1]
        photo_file_id = highest_quality_photo["file_id"]

        # استفاده از تابع لاگ‌گیر خودتان
        log_message(f"PHOTO file_id: {photo_file_id}")

        return photo_file_id
    return None



def send_photo(chat_id, photo_file_id, caption="", reply_markup=None):
    """Sends a photo to the specified chat_id."""
    payload = {"chat_id": chat_id, "photo": photo_file_id, "caption": caption}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        response = requests.post(url + "sendPhoto", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        log_message(f"❌ Failed to send photo to {chat_id}: {e}")
        return None

def check_channel_membership(user_id):
    try:
        payload = {
            "chat_id": CHANNEL,
            "user_id": user_id
        }

        r = requests.post(
            url + "getChatMember",
            json=payload,
            timeout=10
        )

        print("CHANNEL RESPONSE:", r.text)

        data = r.json()

        if not data.get("ok"):
            return False

        status = data["result"]["status"]

        print("STATUS =", status)

        return status in ["member", "administrator", "creator"]

    except Exception as e:
        print("CHECK ERROR:", e)
        return False


def add_back_button(keyboard):
    keyboard["inline_keyboard"].append(
        [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
    )
    return keyboard


# --- Button Definitions ---

def get_contact_button():
    """Returns the keyboard markup for requesting contact."""
    return {
        "keyboard": [
            [
                {
                    "text": "📱 ارسال اتوماتیک شماره تلفن",
                    "request_contact": True
                }
            ]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True
    }


def get_service_keyboard():
    return {
        "inline_keyboard": [
            # [{"text": "تحلیل قبض رایگان", "callback_data": "bill_analysis"}],
            [{"text": "استعلام خرید برق مشترکین بالای 150KW", "callback_data": "buy_power"}],
            # [{"text": "خرید برق ویژه مشترکین بالای 1MW", "callback_data": "buy_power_IMW"}],
            [{"text": "جهت محاسبه افزایش درآمد کلیک کنید ", "callback_data": "power_plants"}],
            # [{"text": "کسب درآمد از طریق صرفه‌جویی", "callback_data": "eco_income"}],
            # [{"text": " فروش و تامین تجهیزات نیروگاهی", "callback_data": "equipment"}],
            # [{"text": "درباره برق‌آپ", "callback_data": "website"}]
        ]
    }


def get_join_channel_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "📢 عضویت در کانال", "url": "https://ble.ir/barghapp"}
            ],
            [
                {"text": "✅ بررسی عضویت", "callback_data": "check_join"}
            ]
        ]
    }


def save_user(chat_id, first_name, last_name, phone, db, cursor):
    try:
        cursor.execute(
            """
            INSERT INTO BarghAppBot_users (chat_id, first_name, last_name, phone)
            VALUES (%s, %s, %s, %s) ON DUPLICATE KEY
            UPDATE
                first_name=VALUES(first_name), 
                last_name=VALUES(last_name), 
                phone=VALUES(phone)
            """,
            (chat_id, first_name, last_name, phone)
        )
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        log_message(f"save_user error: {e}")
        return False


# --- Main Bot Loop ---

def handle_message(update):
    """Processes a single update from the Bale API."""

    #  دریافت کانکشن اختصاصی
    try:
        db = connection_pool.get_connection()
        cursor = db.cursor(buffered=True)
    except Exception as e:
        log_message(f"❌ DB Pool Exhausted or Error: {e}")
        return

    try:

        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text", "")

            # اگر فایل webm یا ویدیو ارسال شد
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]

            if "video" in message:
                video_file_id = message["video"]["file_id"]
                log_message(f"VIDEO file_id: {video_file_id}")
                send_message(chat_id, "✅ ویدیو دریافت شد")
                return

            if "photo" in message:
                # گرفتن آیدی عکس با استفاده از تابع یا مستقیماً
                photo_file_id = message["photo"][-1]["file_id"]
                log_message(f"PHOTO file_id: {photo_file_id}")

                # ارسال پیام تایید به کاربر (اختیاری)
                send_message(chat_id, "✅ عکس دریافت شد و شناسه آن در لاگ ذخیره شد.")
                return

        if "callback_query" in update:
            callback_query = update["callback_query"]
            chat_id = callback_query["message"]["chat"]["id"]
            data = callback_query["data"]

            if data == "bill_analysis":

                keyboard = add_back_button({
                    "inline_keyboard": [
                        [
                            {"text": "🔗 ورود به سامانه", "url": "http://bill-analysis.barghapp.com"}
                        ]
                    ]
                })

                send_video(
                    chat_id,
                    VIDEO_FILE_ID_BILL_ANALISYS,
                    caption="✅ تحلیل قبض برق شما به‌صورت کاملاً رایگان انجام می‌شود.\n👇 روی لینک زیر بزنید",
                    reply_markup=keyboard
                )
            elif data == "check_join":

                user_id = callback_query["from"]["id"]

                if check_channel_membership(user_id):

                    send_photo(
                        chat_id=chat_id,
                        photo_file_id=PHOTO_FILE_ID_BARGHAPP_MICRO,
                        caption=
                        f"⚡️ برق‌آپ ماکرو، سامانه هوشمند فروش برق با قیمتی بیشتر از دولت!\n\n"
                        f"☀️ مالکین محترم نیروگاه‌های خورشیدی (انشعابی و مقیاس کوچک):\n\n"
                        f"🧮 با استفاده از ماشین‌حساب هوشمند، می‌توانید میزان افزایش درآمد نیروگاه خود را محاسبه کنید. 📈💸",
                        reply_markup=get_service_keyboard()
                    )

                else:

                    send_message(
                        chat_id,
                        "❌ هنوز عضو کانال نشده‌اید.",
                        reply_markup=get_join_channel_keyboard()
                    )

                requests.post(
                    url + "answerCallbackQuery",
                    json={"callback_query_id": callback_query["id"]},
                    timeout=5
                )


            elif data == "buy_power":
                keyboard = {
                    "inline_keyboard": [
                        [{"text": "جهت استعلام شناسه قبض خود را وارد کنید ", "callback_data": ""}],
                        [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
                    ]
                }

                send_photo(

                    chat_id,
                    photo_file_id=PHOTO_FILE_ID_BARGHAPP_PLUS,
                    caption=(
                        ""
                        "اگر برق مصرفی مجموعه شما بالای 150 کیلوواته، برق‌آپ پلاس کمک می‌کنه برق موردنیازتون رو "
                        "هوشمندتر و به‌صرفه‌تر تأمین کنید.\n\n"
                        "درصورت تمایل به اطلاع از مشمول بودن یا نبودن برای خرید برق، "
                        "لطفاً *شناسه قبض ۱۳ رقمی خود را بدون فاصله و حروف و علامت ارسال کنید. *🔹👇"
                        ""
                        ""
                        ""
                        ""
                    )
                    , reply_markup=keyboard

                )

                # ذخیره state

                user_states[chat_id] = "waiting_buy_power_bill_id"

                requests.post(

                    url + "answerCallbackQuery",

                    json={"callback_query_id": callback_query["id"]},

                    timeout=5

                )
            elif data == "buy_power_2":

                keyboard = {
                    "inline_keyboard": [
                        [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
                    ]
                }

                send_message(
                    chat_id,
                    "درصورت تمایل به اطلاع از مشمول بودن یا نبودن برای خرید برق، "
                    "لطفاً شناسه قبض ۱۳ رقمی خود را بدون فاصله و حروف و علامت ارسال کنید.. 🔹👇",
                    reply_markup=keyboard
                )

                # ذخیره state

                user_states[chat_id] = "waiting_buy_power_bill_id"

                requests.post(

                    url + "answerCallbackQuery",

                    json={"callback_query_id": callback_query["id"]},

                    timeout=5

                )


            elif data == "buy_power_IMW":
                # ایجاد دکمه بازگشت به منوی اصلی
                keyboard = {
                    "inline_keyboard": [
                        [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
                    ]
                }

                # متن کپشن دلخواه شما
                caption_text = (
                    "⚡️ خرید برق ویژه مشترکین بالای 1 مگاوات (1MW)\n\n"
                    "برق‌آپ با ارائه راهکارهای هوشمند، به شما کمک می‌کند تا برق مورد نیاز مجموعه خود را "
                    "با بهترین قیمت و پایدارترین شرایط تامین کنید.\n\n"
                    "جهت دریافت مشاوره تخصصی و ثبت درخواست، با کارشناسان ما در ارتباط باشید."
                )

                # ارسال ویدیو همراه با کپشن و دکمه بازگشت
                send_video(
                    chat_id=chat_id,
                    video_file_id=VIDEO_FILE_ID_BARGHAPP_PLUS,
                    caption=caption_text,
                    reply_markup=keyboard
                )

                # بستن حالت لودینگ (ساعت شنی) دکمه
                requests.post(
                    url + "answerCallbackQuery",
                    json={"callback_query_id": callback_query["id"]},
                    timeout=5
                )

            elif data == "main_menu":

                # send_message(
                #     chat_id,
                #     "ابتدا با استفاده از دکمه زیر عضو کانال شوید 👇 و سپس روی دکمه بررسی عضویت بزنید تا منوی خدمات برای شما ارسال شود. ",
                #     reply_markup=get_join_channel_keyboard()
                # )
                # return

                caption_text = (
                    f"⚡️ برق‌آپ ماکرو، سامانه هوشمند فروش برق با قیمتی بیشتر از دولت!\n\n"
                    f"☀️ مالکین محترم نیروگاه‌های خورشیدی (انشعابی و مقیاس کوچک):\n\n"
                    f"🧮 با استفاده از ماشین‌حساب هوشمند برق‌آپ ماکرو، می‌توانید میزان افزایش درآمد نیروگاه خود را با نرخ برق‌آپ محاسبه کنید. 📈💸"
                )
                send_photo(
                    chat_id=chat_id,
                    photo_file_id=PHOTO_FILE_ID_BARGHAPP_MICRO,  # استفاده از متغیر عکس شما
                    caption=caption_text,
                    reply_markup=get_service_keyboard()
                )

                return

                # پاسخ به callback query (الزامی)

                requests.post(

                    url + "answerCallbackQuery",

                    json={"callback_query_id": callback_query["id"]},

                    timeout=5

                )


            elif data == "eco_income":

                # keyboard = add_back_button({
                #     "inline_keyboard": [
                #         [
                #             {"text": "🌐 ورود به سایت", "url": "https://eco.barghapp.com"},
                #             {"text": "🔐 ورود به سامانه", "url": "https://eco.barghapp.com"}
                #         ]
                #     ]
                # })

                send_video(
                    chat_id,
                    VIDEO_FILE_ID_BARGHAPP_ECO,
                    caption=(
                        "💰 معرفی برق‌آپ اکو\n\n"
                        "تولید، بهینه‌سازی و صرفه‌جویی برق\n\n"
                        "برق‌آپ اکو یک پلتفرم نوآور در مدیریت و بهینه‌سازی انرژی است "
                        "که با دانش فنی، تجربه اجرایی و راهکارهای هوشمند، به توسعه انرژی‌های پاک "
                        "و کاهش ناترازی شبکه برق کمک می‌کند. این مجموعه با تمرکز بر صرفه‌جویی، "
                        "بهره‌وری و ایجاد ارزش اقتصادی برای مشترکان، گامی مؤثر در توسعه پایدار کشور "
                        "برداشته است."
                    ),
                )
                keyboard = {
                    "inline_keyboard": [
                        [{"text": "صنعتی", "callback_data": "industrial"},
                         {"text": "خانگی", "callback_data": "home"}],
                        [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
                    ]
                }

                send_message(
                    chat_id,
                    "شما مصرف کننده صنعتی هستید یا مصرف کننده خانگی؟\n\n"
                    "لطفا نوع مصرف خود را از طریق دکمه های زیر مشخص کنید"
                    ,
                    reply_markup=keyboard
                )

                # پاسخ به callback (الزامی)

                requests.post(

                    url + "answerCallbackQuery",

                    json={"callback_query_id": callback_query["id"]},

                    timeout=5

                )



            elif data == "industrial":

                user_states[chat_id] = "waiting_industrial_usage"

                send_message(
                    chat_id,
                    "⚡ لطفا میزان مصرف ماهانه برق خود را وارد کنید (kWh):"
                )

                requests.post(
                    url + "answerCallbackQuery",
                    json={"callback_query_id": callback_query["id"]},
                    timeout=5
                )

            elif data == "home":

                keyboard = {
                    "inline_keyboard": [
                        [{"text": "🍳 لوازم آشپزخانه", "callback_data": "cat_kitchen"}],
                        [{"text": "❄️ گرمایشی و سرمایشی", "callback_data": "cat_climate"}],
                        [{"text": "💡 روشنایی و صوتی تصویری", "callback_data": "cat_media"}],
                        [{"text": "🔌 سایر لوازم برقی", "callback_data": "cat_other"}],
                        [{"text": "✅ اتمام و ثبت", "callback_data": "done_appliance"}],
                        [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
                    ]
                }

                user_states[chat_id] = "waiting_home_appliance"

                user_temp_data.setdefault(chat_id, {})
                user_temp_data[chat_id].setdefault("appliances", [])

                send_message(
                    chat_id,
                    "دسته لوازم برقی مورد نظر را انتخاب کنید:",
                    reply_markup=keyboard
                )

            elif data in APPLIANCE_CATEGORIES and user_states.get(chat_id) == "waiting_home_appliance":
                items = APPLIANCE_CATEGORIES[data]
                keyboard_rows = []

                for key in items:
                    # اصلاح اصلی: اطلاعات را از APPLIANCE_DETAILS بخوانید
                    if key in APPLIANCE_DETAILS:
                        name, min_u, max_u = APPLIANCE_DETAILS[key]
                        keyboard_rows.append([
                            {"text": f"{name} ({min_u}-{max_u} kWh)", "callback_data": key}
                        ])

                keyboard_rows.append([{"text": "⬅️ بازگشت به دسته‌بندی", "callback_data": "home"}])
                keyboard_rows.append([{"text": "✅ اتمام و ثبت", "callback_data": "done_appliance"}])

                keyboard = {"inline_keyboard": keyboard_rows}
                send_message(chat_id, "دستگاه مورد نظر را انتخاب کنید:", reply_markup=keyboard)



            elif data in APPLIANCE_DETAILS and user_states.get(chat_id) == "waiting_home_appliance":

                name, min_usage, max_usage = APPLIANCE_DETAILS[data]

                # اضافه کردن به لیست موقت کاربر

                if "appliances" not in user_temp_data[chat_id]:
                    user_temp_data[chat_id]["appliances"] = []

                user_temp_data[chat_id]["appliances"].append((name, min_usage, max_usage))

                # محاسبه مجموع

                total_min = sum(item[1] for item in user_temp_data[chat_id]["appliances"])

                total_max = sum(item[2] for item in user_temp_data[chat_id]["appliances"])

                send_message(

                    chat_id,

                    f"✅ «{name}» اضافه شد.\n"

                    f"⚡ مجموع مصرف فعلی: {total_min} تا {total_max} kWh\n\n"

                    "می‌توانید دستگاه دیگری از همین دسته انتخاب کنید یا به «دسته بندی ها» برگردید.\n"
                    "⚡ *نکته: تمامی لوازم خانگی با عمر بیشتر از 5 سال در دسته لوازم پر مصرف قرار میگیرند.*",

                    reply_markup={

                        "inline_keyboard": [

                            [{"text": "⬅️ بازگشت به دسته‌بندی‌ها", "callback_data": "home"}],

                            [{"text": "✅ اتمام و ثبت نهایی", "callback_data": "done_appliance"}]

                        ]

                    }

                )

                requests.post(
                    url + "answerCallbackQuery",
                    json={"callback_query_id": callback_query["id"]},
                    timeout=5
                )

            elif data == "add_appliance" and user_states.get(chat_id) == "waiting_home_appliance":

                keyboard = {
                    "inline_keyboard": [
                        [
                            {"text": "یخچال کم مصرف (10 kWh)", "callback_data": "fridge_low"},
                            {"text": "یخچال پر مصرف (20 kWh)", "callback_data": "fridge_high"}
                        ],
                        [
                            {"text": "لباسشویی کم مصرف (10 kWh)", "callback_data": "washing_machine_low"},
                            {"text": "لباسشویی پر مصرف (20 kWh)", "callback_data": "washing_machine_high"}
                        ],
                        [

                            {"text": "تلویزیون کم مصرف (10 kWh)", "callback_data": "tv_low"},

                            {"text": "تلویزیون پر مصرف (20 kWh)", "callback_data": "tv_high"}

                        ],
                        [

                            {"text": "روشنایی خانه کم مصرف (10 kWh)", "callback_data": "lights_low"},

                            {"text": "روشنایی خانه پر مصرف (20 kWh)", "callback_data": "lights_high"}

                        ],
                        [

                            {"text": "کولر آبی کم مصرف (10 kWh)", "callback_data": "water_cooler_low"},

                            {"text": "کولر آبی پر مصرف (20 kWh)", "callback_data": "water_cooler_high"}

                        ],
                        [

                            {"text": "کولر گازی کم مصرف (10 kWh)", "callback_data": "gas_cooler_low"},

                            {"text": "کولر گازی پر مصرف (20 kWh)", "callback_data": "gas_cooler_high"}

                        ],
                        [

                            {"text": "پمپ آب کم مصرف (10 kWh)", "callback_data": "water_pump_low"},

                            {"text": "پمپ آب پر مصرف (20 kWh)", "callback_data": "water_pump_high"}

                        ],
                        [

                            {"text": "آبگرمکن کم مصرف (10 kWh)", "callback_data": "electric_superheater_low"},

                            {"text": "آبگرمکن پر مصرف (20 kWh)", "callback_data": "electric_superheater_high"}

                        ],
                        [

                            {"text": "فر/مایکروفر کم مصرف (10 kWh)", "callback_data": "oven_low"},

                            {"text": "فر/مایکروفر پر مصرف (20 kWh)", "callback_data": "oven_high"}

                        ],
                        [

                            {"text": "ماشین ظرفشویی کم مصرف (10 kWh)", "callback_data": "dishwasher_low"},

                            {"text": "ماشین ظرفشویی پر مصرف (20 kWh)", "callback_data": "dishwasher_high"}

                        ],
                        [

                            {"text": "سایر لوازم کم مصرف (10 kWh)", "callback_data": "others_low"},

                            {"text": "سایر لوازم پر مصرف (20 kWh)", "callback_data": "others_high"}

                        ],
                        [
                            {"text": "➕ افزودن دستگاه دیگر", "callback_data": "add_appliance"},
                            {"text": "✅ اتمام و ثبت", "callback_data": "done_appliance"}
                        ],
                        [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
                    ]
                }

                send_message(
                    chat_id,
                    "دستگاه بعدی را انتخاب کنید یا روی «اتمام و ثبت» بزنید:",
                    reply_markup=keyboard
                )

                requests.post(
                    url + "answerCallbackQuery",
                    json={"callback_query_id": callback_query["id"]},
                    timeout=5
                )

            elif data == "done_appliance" and user_states.get(chat_id) == "waiting_home_appliance":

                appliances = user_temp_data.get(chat_id, {}).get("appliances", [])

                if not appliances:
                    send_message(chat_id, "هیچ دستگاهی انتخاب نشده است!")
                else:
                    total_min = sum(item[1] for item in appliances)
                    total_max = sum(item[2] for item in appliances)
                    # تعیین دسته مصرف
                    if total_min and total_max < 350:
                        category = "🏡 شما در دسته «خانه کم‌مصرف» قرار می‌گیرید."

                    elif total_min >= 350 and total_max < 600:
                        category = "🏠 شما در دسته «خانه معمولی» قرار می‌گیرید."

                    elif total_min >= 600:
                        category = "🔥 شما در دسته «خانه پرمصرف» قرار می‌گیرید."

                    elif total_min < 350 and total_max > 350 and total_max <= 600:
                        category = "⚡ مصرف شما بین «خانه کم‌مصرف» و «خانه معمولی» قرار دارد."

                    elif total_min < 600 and total_max > 600:
                        category = "⚡ مصرف شما بین «خانه معمولی» و «خانه پرمصرف» قرار دارد."

                    else:
                        category = "⚡ مصرف شما در مرز چند دسته مصرفی قرار دارد."

                    device_report = "\n".join([f"• {n}: {min_u}-{max_u} kWh" for n, min_u, max_u in appliances])

                    # ذخیره بازه نهایی در دیتای موقت کاربر
                    user_temp_data[chat_id]["total_range"] = (total_min, total_max)
                    user_states[chat_id] = "waiting_bill_cost"

                    send_message(
                        chat_id,
                        f"📋 لیست نهایی دستگاه‌های شما:\n\n"
                        f"{device_report}\n\n"
                        f"⚡ مجموع مصرف احتمالی: {total_min} تا {total_max} kWh\n"
                        f"📊 دسته مصرف شما: {category}\n\n"
                        f"💰 حالا لطفا میزان مصرف آخرین قبض برق خود را وارد کنید (KWh):"
                    )

                requests.post(
                    url + "answerCallbackQuery",
                    json={"callback_query_id": callback_query["id"]},
                    timeout=5
                )




            elif data == "power_plants":
                keyboard = {
                    "inline_keyboard": [
                        [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
                    ]
                }

                caption_text = (
                    "⚡ معرفی برق‌آپ ماکرو\n\n"
                    "برق‌آپ ماکرو، اولین سامانه هوشمند تجمیع و فروش برق نیروگاه‌ها در ایران\n\n"
                    "*لطفاً جهت شروع فرایند محاسبه افزایش درآمد، ابتدا نام و نام خانوادگی خود را به صورت کامل وارد کنید:*"
                )

                send_photo(
                    chat_id=chat_id,
                    reply_markup=keyboard,
                    photo_file_id=PHOTO_FILE_ID_BARGHAPP_MICRO,  # <-- آیدی عکس مربوط به این بخش را اینجا قرار دهید
                    caption=caption_text
                )

                # تغییر وضعیت کاربر برای دریافت نام

                user_states[chat_id] = "waiting_for_full_name"

                # بستن حالت لودینگ دکمه (ساعت شنی)

                requests.post(

                    url + "answerCallbackQuery",

                    json={"callback_query_id": callback_query["id"]},

                    timeout=5

                )



            elif data in ["Residential / Grid-tied Power Plant", "Medium-scale Solar Power Plant"]:

                plant_mapping = {

                    "Residential / Grid-tied Power Plant": "نیروگاه انشعابی / خانگی",

                    "Medium-scale Solar Power Plant": "نیروگاه خورشیدی مقیاس کوچک"

                }

                selected_plant = plant_mapping[data]

                # بستن حالت لودینگ

                requests.post(

                    url + "answerCallbackQuery",

                    json={"callback_query_id": callback_query["id"]},

                    timeout=5

                )

                try:

                    cursor.execute("SELECT phone FROM BarghAppBot_users WHERE chat_id=%s", (chat_id,))

                    user_record = cursor.fetchone()

                    phone = user_record[0] if user_record else "نامشخص"

                    # ثبت نوع نیروگاه در دیتابیس

                    cursor.execute("""

                                   UPDATE barghapp_micro

                                   SET plant_type = %s

                                   WHERE phone = %s ORDER BY id DESC LIMIT 1

                                   """, (selected_plant, phone))

                    db.commit()

                    # تفکیک مسیر بر اساس نوع نیروگاه
                    if selected_plant == "نیروگاه خورشیدی مقیاس کوچک":

                        user_states[chat_id] = "waiting_for_license_number"

                        keyboard_skip = {
                            "inline_keyboard": [
                                [{"text": "ادامه فرایند محاسبه بدون شماره پروانه بهره برداری",
                                  "callback_data": "skip_license"}]
                            ]
                        }

                        send_message(
                            chat_id,
                            f"✅ نوع نیروگاه شما ({selected_plant}) با موفقیت ثبت شد.\n\n"
                            "لطفاً *شماره پروانه بهره‌برداری* خود را بدون هیچ‌گونه فاصله، حروف یا علامت وارد کنید.\n"
                            "مثال : \n۱۴۱۴۱۴۱۴۱۴۱۴۱۴\n"
                            "*در صورتی که شماره پروانه بهره برداری خود را ندارید جهت ادامه فرایند محاسبه درآمد خود روی دکمه زیر کلیک کنید.*",
                            reply_markup=keyboard_skip
                        )

                    else:  # نیروگاه انشعابی / خانگی

                        user_states[chat_id] = "waiting_for_bill_id"

                        keyboard_skip = {
                            "inline_keyboard": [
                                [{"text": "ادامه فرایند محاسبه بدون شناسه قبض", "callback_data": "skip_bill"}]
                            ]
                        }

                        send_message(
                            chat_id,
                            f"✅ نوع نیروگاه شما ({selected_plant}) با موفقیت ثبت شد.\n\n"
                            "لطفاً *شناسه قبض برق* خود را بدون هیچ‌گونه فاصله، حروف یا علامت وارد کنید.\n"
                            "مثال : ۱۲۳۴۵۶۷۸۹۰۱۲۳\n"
                            "*در صورتی که شناسه قبض برق خود را ندارید جهت ادامه فرایند محاسبه درآمد خود روی دکمه زیر کلیک کنید.*",
                            reply_markup=keyboard_skip
                        )

                except Exception as e:
                    print(f"Database Error: {e}")
                    send_message(chat_id, "❌ خطایی در ثبت اطلاعات رخ داد. لطفا دوباره تلاش کنید.")

                    # پاسخ به callback (الزامی)
                requests.post(
                    url + "answerCallbackQuery",
                    json={"callback_query_id": callback_query["id"]},
                    timeout=5
                )

            elif data in ["skip_license", "skip_bill"]:

                # بستن حالت لودینگ
                requests.post(
                    url + "answerCallbackQuery",
                    json={"callback_query_id": callback_query["id"]},
                    timeout=5
                )

                try:
                    cursor.execute("SELECT phone FROM BarghAppBot_users WHERE chat_id=%s", (chat_id,))
                    user_record = cursor.fetchone()

                    if user_record:
                        phone = user_record[0]

                        # ذخیره عدد 0 به عنوان شماره کنتور/پروانه در دیتابیس
                        cursor.execute("""
                                       UPDATE barghapp_micro
                                       SET contor_number = %s
                                       WHERE phone = %s ORDER BY id DESC LIMIT 1
                                       """, ("0", phone))
                        db.commit()

                        # انتقال وضعیت کاربر به مرحله بعد
                        user_states[chat_id] = "waiting_for_generation"
                        send_message(
                            chat_id,
                            "✅ اطلاعات شما (بدون شناسه/شماره پروانه) با موفقیت ثبت شد.\n\n"
                            "⚡ لطفا *میزان تولید* نیروگاه خود را (بر حسب کیلووات) وارد کنید:"
                        )
                    else:
                        send_message(chat_id, "❌ خطایی رخ داد. لطفا از ابتدا شروع کنید.")
                        user_states.pop(chat_id, None)

                except Exception as e:
                    print(f"Database Error: {e}")
                    send_message(chat_id, "❌ خطایی در ارتباط با دیتابیس رخ داد. لطفا دوباره تلاش کنید.")

            elif data in ["support_yes", "support_no"] and user_states.get(chat_id) == "waiting_for_support_status":

                is_supported = True if data == "support_yes" else False

                requests.post(
                    url + "answerCallbackQuery",
                    json={"callback_query_id": callback_query["id"]},
                    timeout=5

                )

                try:

                    cursor.execute("SELECT phone FROM BarghAppBot_users WHERE chat_id=%s", (chat_id,))
                    user_record = cursor.fetchone()
                    if user_record:
                        phone = user_record[0]
                        cursor.execute("""
                                       UPDATE barghapp_micro
                                       SET is_supported = %s
                                       WHERE phone = %s ORDER BY id DESC LIMIT 1
                                       """, (is_supported, phone))
                        db.commit()


                        if is_supported:
                            user_states[chat_id] = "waiting_for_support_organization"
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "صندوق کارآفرینی امید", "callback_data": "org_omid"}],
                                    [{"text": "بنیاد شهید و امور ایثارگران", "callback_data": "org_shahid"}],
                                    [{"text": "کمیته امداد امام خمینی", "callback_data": "org_emdad"}],
                                    [{"text": "بنیاد مستضعفان", "callback_data": "org_mostazaf"}],
                                    [{"text": "بنیاد علوی", "callback_data": "org_alavi"}],
                                    [{"text": "بنیاد مسکن انقلاب اسلامی", "callback_data": "org_maskan"}],
                                    [{"text": "سایر نهادها", "callback_data": "org_other"}]
                                ]
                            }

                            send_message(
                                chat_id,
                                "لطفاً نام نهاد حمایتی خود را انتخاب کنید:",
                                reply_markup=keyboard
                            )

                        else:
                            user_states[chat_id] = "waiting_for_contract_type"
                            keyboard = {
                                "inline_keyboard": [
                                    [{"text": "🔘 فروش تضمینی سالانه", "callback_data": "contract_guaranteed"}],
                                    [{"text": "🔘 فروش در بورس انرژی", "callback_data": "contract_bourse"}]
                                ]
                            }

                            send_message(
                                chat_id,
                                "تمایل دارید برق تولیدی خود را به کدام روش به فروش برسانید؟",
                                reply_markup=keyboard
                            )


                except Exception as e:

                    print(f"Database Error: {e}")

                    send_message(chat_id, "❌ خطایی در ثبت اطلاعات رخ داد. لطفا دوباره تلاش کنید.")

            elif data in ["org_omid", "org_shahid", "org_emdad", "org_mostazaf", "org_alavi", "org_maskan",
                          "org_other"] and user_states.get(chat_id) == "waiting_for_support_organization":

                # نگاشت کردن دیتای دکمه به نام واقعی نهاد برای ذخیره در دیتابیس
                org_mapping = {
                    "org_omid": "صندوق کارآفرینی امید",
                    "org_shahid": "بنیاد شهید و امور ایثارگران",
                    "org_emdad": "کمیته امداد امام خمینی",
                    "org_mostazaf": "بنیاد مستضعفان",
                    "org_alavi": "بنیاد علوی",
                    "org_maskan": "بنیاد مسکن انقلاب اسلامی",
                    "org_other": "سایر نهادها"
                }
                selected_org = org_mapping[data]

                # بستن حالت لودینگ روی دکمه
                requests.post(
                    url + "answerCallbackQuery",
                    json={"callback_query_id": callback_query["id"]},
                    timeout=5
                )

                try:
                    cursor.execute("SELECT phone FROM BarghAppBot_users WHERE chat_id=%s", (chat_id,))
                    user_record = cursor.fetchone()

                    if user_record:
                        phone = user_record[0]

                        # ذخیره نام نهاد در دیتابیس
                        cursor.execute("""
                                       UPDATE barghapp_micro
                                       SET support_organization = %s
                                       WHERE phone = %s ORDER BY id DESC LIMIT 1
                                       """, (selected_org, phone))
                        db.commit()


                        user_states[chat_id] = "waiting_for_contract_type"

                        keyboard = {
                            "inline_keyboard": [
                                [{"text": "🔘 فروش تضمینی سالانه", "callback_data": "contract_guaranteed"}],
                                [{"text": "🔘 فروش در بورس انرژی", "callback_data": "contract_bourse"}]
                            ]
                        }
                        send_message(
                            chat_id,
                            f"✅ نهاد حمایتی ({selected_org}) با موفقیت ثبت شد.\n\n"
                            "تمایل دارید برق تولیدی خود را به کدام روش به فروش برسانید؟",
                            reply_markup=keyboard
                        )

                except Exception as e:
                    print(f"Database Error: {e}")
                    send_message(chat_id, "❌ خطایی در ثبت اطلاعات رخ داد. لطفا دوباره تلاش کنید.")

            elif data in ["contract_guaranteed", "contract_bourse"] and user_states.get(
                    chat_id) == "waiting_for_contract_type":

                # بستن حالت لودینگ روی دکمه

                requests.post(
                    url + "answerCallbackQuery",
                    json={"callback_query_id": callback_query["id"]},
                    timeout=5
                )

                contract_mapping = {
                    "contract_guaranteed": "فروش تضمینی سالانه",
                    "contract_bourse": "فروش در بورس انرژی"
                }

                selected_contract = contract_mapping[data]
                try:
                    cursor.execute("SELECT phone FROM BarghAppBot_users WHERE chat_id=%s", (chat_id,))
                    user_record = cursor.fetchone()
                    if user_record:
                        phone = user_record[0]
                        # ۱. ذخیره نوع قرارداد در دیتابیس

                        cursor.execute("""
                                       UPDATE barghapp_micro
                                       SET contract_type = %s
                                       WHERE phone = %s ORDER BY id DESC LIMIT 1
                                       """, (selected_contract, phone))
                        db.commit()

                        # ۲. واکشی اطلاعات نیروگاه جهت بررسی شروط محاسبه فرمول
                        cursor.execute("""
                                       SELECT plant_type, is_supported, generation, first_name
                                       FROM barghapp_micro
                                       WHERE phone = %s
                                       ORDER BY id DESC LIMIT 1
                                       """, (phone,))
                        plant_info = cursor.fetchone()

                        calculation_msg = ""

                        if plant_info:
                            plant_type = plant_info[0]
                            is_supported = plant_info[1]

                            # تبدیل ظرفیت به عدد اعشاری
                            generation = float(plant_info[2]) if plant_info[2] else 0.0
                            final_amount = None

                            if generation > 0:
                                # --- تعریف صریح هر ۶ شرط ---
                                condition_1 = (plant_type == "نیروگاه انشعابی / خانگی" and is_supported == False and data == "contract_guaranteed")
                                condition_2 = (plant_type == "نیروگاه خورشیدی مقیاس کوچک" and data == "contract_guaranteed")
                                condition_3 = (plant_type == "نیروگاه انشعابی / خانگی" and is_supported == True and data == "contract_guaranteed")
                                condition_4 = (plant_type == "نیروگاه خورشیدی مقیاس کوچک" and data == "contract_bourse")
                                condition_5 = (plant_type == "نیروگاه انشعابی / خانگی" and is_supported == False and data == "contract_bourse")
                                condition_6 = (plant_type == "نیروگاه انشعابی / خانگی" and is_supported == True and data == "contract_bourse")

                                # calculating final amounts (per month)
                                if condition_1 or condition_2:
                                    final_amount = generation * 720 * 0.2 * 6650
                                    satba_final_amount_month = generation * 720 * 0.2 * 5800
                                    satba_final_amount_year = satba_final_amount_month * 12
                                    mabetafavot_month = final_amount - satba_final_amount_month
                                    mabetafavot_year = mabetafavot_month * 12


                                elif condition_3:
                                    final_amount = generation * 720 * 0.2 * 7120
                                    satba_final_amount_month = generation * 720 * 0.2 * 6900
                                    satba_final_amount_year = satba_final_amount_month * 12
                                    mabetafavot_month = final_amount - satba_final_amount_month
                                    mabetafavot_year = mabetafavot_month * 12


                                elif condition_4 or condition_5 or condition_6:
                                    final_amount = (generation * 720 * 0.2 * 8300) * 0.97

                                # --- ساخت پیام خروجی مشترک برای مبلغ ماهانه و سالانه ---
                                if final_amount is not None:
                                    # محاسبه درآمد سالانه
                                    annual_amount = final_amount * 12
                                    # فرمت‌دهی سه رقم سه رقم اعداد
                                    formatted_monthly = "{:,.0f}".format(final_amount)
                                    formatted_annual = "{:,.0f}".format(annual_amount)

                                    # تفکیک متن پیام بر اساس وجود یا عدم وجود کارمزد بورس
                                    if data == "contract_bourse":
                                        calculation_msg = (
                                            f"\n\n📊 *برآورد درآمد نهایی نیروگاه شما در بورس انرژی (پس از کسر ۳٪ کارمزد برق‌آپ):*\n"
                                            f" 💰 *درآمد ماهانه:* {formatted_monthly}  تومان\n"
                                            f" 💰 *درآمد سالانه:* {formatted_annual}  تومان\n"
                                            f"قابل توجه است که برآورد درآمد شما با توجه به اخرین نرخ معامله شده در بورس انرژی است"

                                        )
                                    else:
                                        formatted_satba_final_amount = "{:,.0f}".format(satba_final_amount_month)
                                        formatted_mabetafavot_year = "{:,.0f}".format(mabetafavot_year)
                                        formatted_mabetafavot_month = "{:,.0f}".format(mabetafavot_month)
                                        formatted_satba_final_amount_year = "{:,.0f}".format(satba_final_amount_year)
                                        calculation_msg = (
                                            f"\n\n📊 *برآورد درآمد نهایی نیروگاه شما (در صورت فروش به برق‌اپ مایکرو):*\n"
                                            f" 💰 *درآمد ماهانه:* {formatted_monthly}  تومان\n"
                                            f" 💰 *درآمد سالانه:* {formatted_annual}  تومان\n"
                                            f" 📊 برآورد درآمد نهایی نیروگاه شما (در صورت فروش به دولت (ساتبا/توانیر) با نرخ مصوب):\n "
                                            f"درآمد ماهانه : {formatted_satba_final_amount} تومان \n"
                                            f"درآمد سالانه : {formatted_satba_final_amount_year} تومان \n"
                                            f" *افزایش درآمد ماهانه شما {formatted_mabetafavot_month} و سالانه {formatted_mabetafavot_year} تومان خواهد بود.*"
                                        )
                                    cursor.execute(
                                        "SELECT didar_lead_id FROM barghapp_micro WHERE phone = %s ORDER BY id DESC LIMIT 1",
                                        (phone,)
                                    )
                                    result = cursor.fetchone()

                                    if result and result[0]:
                                        didar_lead_id = result[0]

                                        # Extract first_name from the plant_info fetched earlier (index 3)
                                        user_first_name = plant_info[3] if plant_info and len(plant_info) > 3 and \
                                                                           plant_info[3] else "کاربر"

                                        # ساخت معامله (بدون آیتم و با ارسال مستقیم قیمت کل)
                                        create_deal_in_didar(
                                            contact_id=didar_lead_id,
                                            first_name=user_first_name,  # ✅ Added missing positional argument
                                            title=f"{user_first_name} | API",
                                            total_value=int(final_amount),  # ارسال قیمت بدون اعشار
                                            items=[]  # ارسال لیست خالی محصولات
                                        )
                                    else:
                                        log_message(
                                            f"⚠️ اخطار: didar_lead_id برای شماره {phone} یافت نشد، معامله ثبت نگردید.")

                                        # --- ذخیره همان مبلغ ماهانه در دیتابیس ---
                                        try:
                                            cursor.execute("""
                                                           UPDATE barghapp_micro
                                                           SET price = %s
                                                           WHERE phone = %s ORDER BY id DESC LIMIT 1
                                                           """, (final_amount, phone))
                                            db.commit()
                                            log_message(f"✅ Price {final_amount} saved for phone: {phone}")
                                        except Exception as db_err:
                                            print(f"Error saving price: {db_err}")

                                        # حالا واکشی اطلاعات نهایی نیروگاه جهت استفاده در پیام خروجی
                                        cursor.execute("""
                                                       SELECT plant_type, is_supported, generation, first_name
                                                       FROM barghapp_micro
                                                       WHERE phone = %s
                                                       ORDER BY id DESC LIMIT 1
                                                       """, (phone,))
                                        plant_info = cursor.fetchone()

                                else:
                                    calculation_msg = f"\n\n⚠️ شرایط نیروگاه شما با فرمول‌های سیستم همخوانی ندارد."
                            else:
                                calculation_msg = f"\n\n⚠️ ظرفیت نیروگاه شما ثبت نشده یا مقدار آن 0 است؛ به همین دلیل محاسبه مالی انجام نشد."
                        # ۳. پاک کردن وضعیت کاربر از حالت انتظار

                        user_states.pop(chat_id, None)
                        keyboard = {

                            "inline_keyboard": [
                                [{"text": "🔐 ثبت نام و ثبت قرارداد در سامانه برق‌آپ",
                                  "url": "https://micro.barghapp.app/"}],
                                [{"text": "🔙 تغییر روش فروش برق‌آپ مایکرو", "callback_data": "selected_contract_2"}],
                                [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
                            ]
                        }
                        # استخراج نام کاربر (اگر نامی ثبت نشده بود، کلمه "کاربر" جایگزین می‌شود)
                        user_name = plant_info[3] if plant_info and len(plant_info) > 3 and plant_info[3] else "کاربر"
                        send_message(
                            chat_id,
                            f"{user_name} عزیز، ✅ اطلاعات نیروگاه شما با موفقیت تکمیل و ثبت شد.\n"
                            f"📋 نوع روش فروش: {selected_contract}{calculation_msg}\n\n",
                            reply_markup=keyboard
                        )

                        if phone and phone != "نامشخص":
                            micro_msg = 'افزایش درآمدت رو در ماشین‌حساب برق‌آپ مایکرو دیدی؟ 🚀\nبرای اینکه درآمدتو افزایش بدی، فقط یک قدم تا امضای قرارداد با برق‌آپ مایکرو فاصله داری.\nتکمیل ثبت‌نام و شروع کسب درآمد:\nhttps://micro.barghapp.app'
                            send_delayed_sms(phone=phone, message_text=micro_msg, delay_seconds=10)


                except Exception as e:
                    print(f"Database Error: {e}")
                    send_message(chat_id, "❌ خطایی در ثبت نهایی اطلاعات رخ داد. لطفا دوباره تلاش کنید.")
            elif data == "selected_contract_2":
                # ۱. بستن حالت لودینگ (ساعت شنی) روی دکمه در تلگرام/بله
                requests.post(
                    url + "answerCallbackQuery",
                    json={"callback_query_id": callback_query["id"]},
                    timeout=5
                )

                # ۲. بازگرداندن وضعیت کاربر به مرحله انتخاب نوع قرارداد
                user_states[chat_id] = "waiting_for_contract_type"

                # ۳. تعریف مجدد کیبورد انتخاب روش فروش
                keyboard = {
                    "inline_keyboard": [
                        [{"text": "🔘 فروش تضمینی سالانه", "callback_data": "contract_guaranteed"}],
                        [{"text": "🔘 فروش در بورس انرژی", "callback_data": "contract_bourse"}]
                    ]
                }

                # ۴. ارسال پیام انتخاب روش فروش
                send_message(
                    chat_id,
                    "تمایل دارید برق تولیدی خود را به کدام روش به فروش برسانید؟\nلطفاً گزینه مورد نظر خود را مجدداً انتخاب کنید:",
                    reply_markup=keyboard
                )

            elif data == "equipment":

                keyboard = add_back_button({
                    "inline_keyboard": [
                        [
                            {"text": "🌐 ورود به سایت", "url": "https://barghappmarket.com"},
                        ]
                    ]
                })

                send_video(
                    chat_id,
                    VIDEO_FILE_ID_BARGHAPP_MARKET,
                    caption=(
                        "🛒 معرفی برق‌آپ مارکت\n\n"
                        "اولین فروشگاه خرید نیروگاه‌های تولیدکننده برق و لوازم و تجهیزات یدکی آن‌ها\n\n"
                        "برق‌آپ مارکت تنها یک فروشگاه آنلاین نیست؛ بلکه یک اکوسیستم کامل برای تأمین "
                        "تجهیزات صنعت برق است. این زنجیره تأمین جامع تجهیزات تولید برق و نیروگاهی است.\n\n"
                        "واردکنندگان و تولیدکنندگان می‌توانند محصولات خود مانند دیزل ژنراتور، "
                        "موتورژنراتور گازسوز، باتری، پنل خورشیدی و اینورتر را عرضه کنند.\n\n"
                        "مشترکین کشاورزی، صنعتی، عمومی، تجاری و خانگی نیز می‌توانند کلیه نیازهای خود "
                        "را در این حوزه تأمین کنند.\n\n"
                        "در طرح‌های توسعه‌ای، برق‌آپ مارکت تأمین تجهیزات نیروگاه‌های گاز، بخار و سیکل "
                        "ترکیبی در مقیاس کوچک و بزرگ را نیز پوشش خواهد داد."
                    ),
                    reply_markup=keyboard
                )

                # پاسخ به callback (الزامی)

                requests.post(
                    url + "answerCallbackQuery",
                    json={"callback_query_id": callback_query["id"]},
                    timeout=5
                )

            elif data == "website":

                keyboard = add_back_button({
                    "inline_keyboard": [
                        [{"text": "🌐 ورود به سایت", "url": "https://barghapp.com"},]
                    ]
                })

                send_video(
                    chat_id,
                    VIDEO_FILE_ID_DARBAREH_BARGHAPP,
                    caption=(
                        "🌟 مأموریت ما و چشم‌انداز برق‌آپ\n\n"
                        "برق‌آپ مأموریت دارد با استفاده از فناوری‌های نوین و زیرساخت دیجیتال بومی، "
                        "دسترسی به انرژی را شفاف، هوشمند و پایدار سازد. این پلتفرم با گردآوردن تمام "
                        "بازیگران صنعت برق در یک سامانه یکپارچه، امکان تعامل مستقیم، سریع و مطمئن "
                        "میان تولیدکنندگان، مصرف‌کنندگان، پیمانکاران، سرمایه‌گذاران و نهادهای مالی "
                        "را فراهم می‌کند.\n\n"
                        "🎯 مهم‌ترین اهداف برق‌آپ:\n"
                        "• ایجاد دسترسی شفاف و آسان به بازار برق برای همه مصرف‌کنندگان و تولیدکنندگان\n"
                        "• تسهیل سرمایه‌گذاری در پروژه‌های انرژی سبز و نیروگاه‌های مقیاس کوچک\n"
                        "• ارتقای بهره‌وری و صرفه‌جویی در مصرف برق از طریق تحلیل داده و هوش مصنوعی\n"
                        "• حمایت از تحول دیجیتال صنعت انرژی ایران\n"
                    ),
                    reply_markup=keyboard
                )

                # پاسخ به callback (الزامی)

                requests.post(
                    url + "answerCallbackQuery",
                    json={"callback_query_id": callback_query["id"]},
                    timeout=5
                )

        # Handle regular messages
        if "message" in update:
            msg = update["message"]
            chat_id = msg["chat"]["id"]
            user = msg.get("from", {})
            text = msg.get("text", "")
            first_name = user.get("first_name", "")
            last_name = user.get("last_name", "")
            name = f"{first_name} {last_name}".strip()
            log_message(f"Received message from {name} (chat_id: {chat_id})")

            if text == "/start":
                cursor.execute("SELECT phone FROM BarghAppBot_users WHERE chat_id=%s", (chat_id,))
                user_data = cursor.fetchone()

                # حالت اول: کاربر جدید است و هنوز شماره نداده
                if not user_data:
                    send_video(
                        chat_id,
                        VIDEO_FILE_ID_DARBAREH_BARGHAPP,
                        f"درود {first_name} عزیز 👋\nبه خانواده بزرگ برق‌آپ خوش آمدید! ⚡️"
                    )
                    send_message(
                        chat_id,
                        "برای اینکه بتوانیم خدمات ربات را برای شما فعال کنیم، به شماره تماس شما نیاز داریم.\n\n"
                        "کافیست روی دکمه پایین کیبورد کلیک کنید و شماره خود را بفرستید تا سریعاً کار را شروع کنیم. 👇",
                        reply_markup=get_contact_button()
                    )
                    return
                if not msg.get("contact"):  # اگر پیام ارسال شده از نوع کانتکت نیست
                    cursor.execute("SELECT phone FROM BarghAppBot_users WHERE chat_id=%s", (chat_id,))
                    if not cursor.fetchone():  # اگر کاربر در دیتابیس وجود ندارد
                        send_message(
                            chat_id,
                            "⚠️ برای استفاده از خدمات ربات، حتماً باید شماره تماس خود را از طریق دکمه پایین (ارسال اتوماتیک شماره تلفن) ارسال کنید.",
                            reply_markup=get_contact_button()
                        )
                        return

                # حالت دوم: کاربر شماره داده، حالا بررسی عضویت کانال
                is_member = check_channel_membership(chat_id)
                if not is_member:
                    send_message(
                        chat_id,
                        "ابتدا با استفاده از دکمه زیر عضو کانال شوید 👇 و سپس روی دکمه بررسی عضویت بزنید تا منوی خدمات برای شما ارسال شود.",
                        reply_markup=get_join_channel_keyboard()
                    )
                    return


                # حالت سوم: کاربر هم شماره داده و هم عضو کانال است (ارسال منوی اصلی برق‌آپ ماکرو)
                caption_text = (
                    f"{first_name} عزیز 👋\n\n"
                    f"⚡️ برق‌آپ ماکرو، سامانه هوشمند فروش برق با قیمتی بیشتر از دولت!\n\n"
                    f"☀️ مالکین محترم نیروگاه‌های خورشیدی (انشعابی و مقیاس کوچک):\n\n"
                    f"🧮 با استفاده از ماشین‌حساب هوشمند، می‌توانید میزان افزایش درآمد نیروگاه خود را محاسبه کنید. 📈💸"
                )
                send_photo(
                    chat_id=chat_id,
                    photo_file_id=PHOTO_FILE_ID_BARGHAPP_MICRO,
                    caption=caption_text,
                    reply_markup=get_service_keyboard()
                )
                return
            # پردازش نام و نام خانوادگی تایپ شده توسط کاربر
            if user_states.get(chat_id) == "waiting_for_full_name":
                full_name = text.strip()

                # ۱. بررسی خالی نبودن (ارسال استیکر، ویس یا پیام خالی)
                if not full_name:
                    send_message(chat_id, "❌ لطفاً نام خود را به صورت متنی ارسال کنید.")
                    return

                # ۲. بررسی اینکه فقط شامل حروف الفبا (فارسی/انگلیسی)، فاصله و نیم‌فاصله باشد
                # و هیچ‌گونه عدد یا علامتی مثل @، !، _ و... در آن نباشد.
                if not re.fullmatch(r"^[a-zA-Z\u0600-\u06FF\s\u200c]+$", full_name):
                    send_message(chat_id,
                                 "❌ نام وارد شده معتبر نیست. لطفاً فقط از حروف الفبا استفاده کنید و از وارد کردن عدد یا علامت خودداری کنید.")
                    return

                # ۳. بررسی منطقی بودن طول نام (حداقل ۳ و حداکثر ۵۰ حرف)
                if len(full_name) < 3 or len(full_name) > 50:
                    send_message(chat_id,
                                 "❌ نام وارد شده بیش از حد کوتاه یا بلند است. لطفاً نام واقعی خود را وارد کنید.")
                    return

                try:
                    # ۱. واکشی شماره تلفن
                    cursor.execute("SELECT phone FROM BarghAppBot_users WHERE chat_id=%s", (chat_id,))
                    user_record = cursor.fetchone()
                    phone = user_record[0] if user_record else "نامشخص"

                    # ۲. ثبت نام در دیتابیس (با مقدار موقت برای نوع نیروگاه)
                    cursor.execute("""
                                   INSERT INTO barghapp_micro (plant_type, first_name, phone)
                                   VALUES (%s, %s, %s)
                                   """, ("نامشخص", full_name, phone))
                    db.commit()

                    # --- اضافه کردن تست دیدار ---
                    didar_id = sync_to_didar_initial(full_name, phone)
                    if didar_id:
                        # آپدیت ID دریافت شده از دیدار در دیتابیس خودتان برای مراحل بعدی
                        cursor.execute(
                            "UPDATE barghapp_micro SET didar_lead_id = %s WHERE phone = %s ORDER BY id DESC LIMIT 1",
                            (didar_id, phone))
                        db.commit()
                        log_message(f"User {full_name} synced to Didar with ID: {didar_id}")

                    # ۳. پاک کردن وضعیت
                    user_states.pop(chat_id, None)

                    # ۴. نمایش کیبورد انتخاب نوع نیروگاه دقیقاً پس از دریافت اطلاعات هویتی
                    keyboard = {
                        "inline_keyboard": [
                            [{"text": "نیروگاه انشعابی / خانگی",
                              "callback_data": "Residential / Grid-tied Power Plant"}],
                            [{"text": "نیروگاه خورشیدی مقیاس کوچک",
                              "callback_data": "Medium-scale Solar Power Plant"}],
                            [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
                        ]
                    }

                    send_message(
                        chat_id,
                        f"ممنون {full_name} عزیز .\n\n"
                        " در این مرحله لطفا *نوع نیروگاه* خود را از طریق دکمه های زیر مشخص کنید:",
                        reply_markup=keyboard
                    )

                except Exception as e:
                    print(f"Database Error: {e}")
                    send_message(chat_id, "❌ خطایی در ثبت اطلاعات رخ داد. لطفا دوباره تلاش کنید.")

                return

            # در بخش handle_message (پردازش عدد وارد شده)
            if user_states.get(chat_id) == "waiting_exact_production":
                user_input = msg.get("text", "")

                if user_input.replace('.', '', 1).isdigit():
                    exact_value = float(user_input)
                    data_dict = user_temp_data.get(chat_id, {})

                    # اطلاعاتی که در مراحل قبل ذخیره کردیم

                    ownership = data_dict.get("ownership_type", "نامشخص")

                    final_message = (
                        f"✅ اطلاعات شما با موفقیت ثبت شد.\n\n"
                        f"🔹 نوع مالکیت: {ownership}\n"
                        f"🔹 میزان تولید ثبت شده: {exact_value} kWh\n\n"
                        "کارشناسان ما به‌زودی با شما تماس خواهند گرفت."
                    )

                    send_message(
                        chat_id,
                        final_message,
                        reply_markup={
                            "inline_keyboard": [[{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]]}
                    )

                    user_states.pop(chat_id, None)
                    user_temp_data.pop(chat_id, None)
                    return
            # مصرف صنعتی
            if user_states.get(chat_id) == "waiting_industrial_usage":
                usage = msg.get("text")
                user_temp_data[chat_id] = {"usage": usage}
                user_states[chat_id] = "waiting_saving_percent"
                send_message(
                    chat_id,
                    "📉 لطفا میزان صرفه‌جویی ماهانه خود را بر حسب KWh وارد کنید."
                )
                return

            if user_states.get(chat_id) == "waiting_saving_percent":

                # ۱. جلوگیری از کرش کردن ربات در صورت ری‌استارت شدن سرور
                if chat_id not in user_temp_data or "usage" not in user_temp_data[chat_id]:
                    keyboard = {"inline_keyboard": [[{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]]}
                    send_message(
                        chat_id,
                        "⚠️ نشست شما منقضی شده. لطفاً از منوی اصلی دوباره شروع کنید.",
                        reply_markup=keyboard)
                    user_states.pop(chat_id, None)
                    return

                user_text = msg.get("text", "")
                if not user_text.isdigit():
                    send_message(chat_id, "❌ لطفاً میزان صرفه‌جویی را فقط به صورت عدد (مثلاً 500) وارد کنید:")
                    return

                saving = int(user_text)
                usage = int(user_temp_data[chat_id]["usage"])
                new_usage = usage - saving

                # ---  دریافت قیمت گواهی و محاسبه درآمد ---
                govahei_price = get_govahei_price()
                estimated_income = saving * govahei_price
                # -------------------------------------------------------------

                keyboard = {
                    "inline_keyboard": [
                        [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
                    ]
                }
                send_message(
                    chat_id,
                    f"✅ اطلاعات ثبت شد\n\n"
                    f"⚡ مصرف اولیه: {usage:,} kWh\n"
                    f"📉 میزان صرفه‌جویی: {saving:,} kWh\n"
                    f"✅ مصرف پس از صرفه‌جویی: {new_usage:,} kWh\n"
                    f"───────────────────\n"
                    f"💰 **درآمد تخمینی شما از صرفه‌جویی:** {estimated_income:,} تومان",
                    reply_markup=keyboard
                )
                user_states.pop(chat_id, None)
                user_temp_data.pop(chat_id, None)
                return

            # مصرف خانگی
            if user_states.get(chat_id) == "waiting_bill_cost":
                try:
                    bill_cost = int(text.replace(",", "").strip())
                    # گرفتن بازه مصرف ذخیره شده
                    total_min, total_max = user_temp_data.get(chat_id, {}).get("total_range", (0, 0))
                    # ساخت گزارش دستگاه‌ها
                    appliances = user_temp_data.get(chat_id, {}).get("appliances", [])
                    device_report = "\n".join([f"• {n}: {min_u}-{max_u} kWh" for n, min_u, max_u in appliances])
                    # --- تغییرات جدید: محاسبه صرفه‌جویی و درآمد خانگی ---
                    govahei_price = get_govahei_price()
                    potential_saving = bill_cost - total_min
                    if potential_saving > 0:
                        estimated_income = potential_saving * govahei_price
                        income_text = f"📉 پتانسیل صرفه‌جویی شما: {potential_saving:,} kWh\n" \
                                      f"📊 قیمت هر کیلووات گواهی: {govahei_price:,} تومان\n" \
                                      f"💰 **درآمد احتمالی شما از :** {estimated_income:,} تومان"
                    else:
                        income_text = "🌱 مصرف شما در حال حاضر بهینه و در کف قرار دارد! با مدیریت بیشتر می‌توانید همچنان درآمدزایی کنید."

                    keyboard = {
                        "inline_keyboard": [
                            [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
                        ]
                    }

                    send_message(
                        chat_id,
                        f"✅ اطلاعات شما ثبت شد.\n\n"
                        f"📋 لیست نهایی دستگاه‌ها:\n{device_report}\n\n"
                        f"⚡ تخمین مصرف ماهانه دستگاه‌ها: {total_min} تا {total_max} kWh\n"
                        f"💰 مصرف آخرین قبض شما: {bill_cost:,} kWh\n"
                        f"───────────────────\n"
                        f"{income_text}",
                        reply_markup=keyboard
                    )

                    # پاکسازی وضعیت کاربر
                    user_states.pop(chat_id, None)
                    user_temp_data.pop(chat_id, None)
                    return

                except ValueError:
                    send_message(chat_id, "❌ لطفا مصرف آخرین قبض را فقط به صورت عدد وارد کنید.\nمثال: 450")
                    return

            # بررسی شماره پروانه بهره‌برداری (مخصوص نیروگاه مقیاس کوچک)
            if user_states.get(chat_id) == "waiting_for_license_number":
                license_number = normalize_digits(text.strip())
                if not license_number.isdigit():
                    send_message(chat_id, "❌ شماره پروانه وارد شده معتبر نیست. لطفاً فقط عدد وارد کنید:")
                    return

                try:
                    cursor.execute("SELECT phone FROM BarghAppBot_users WHERE chat_id=%s", (chat_id,))
                    user_record = cursor.fetchone()
                    if user_record:
                        phone = user_record[0]
                        cursor.execute("""
                                       UPDATE barghapp_micro
                                       SET contor_number = %s
                                       WHERE phone = %s ORDER BY id DESC LIMIT 1
                                       """, (license_number, phone))
                        db.commit()
                        user_states[chat_id] = "waiting_for_generation"
                        send_message(
                            chat_id,
                            "✅ شماره پروانه بهره‌برداری با موفقیت ثبت شد.\n\n"
                            "⚡ لطفا *میزان تولید* نیروگاه خود را (بر حسب کیلووات) وارد کنید:"
                        )
                    else:
                        send_message(chat_id, "❌ خطایی رخ داد. لطفا از ابتدا شروع کنید.")
                        user_states.pop(chat_id, None)

                except Exception as e:
                    print(f"Database Error: {e}")
                    send_message(chat_id, "❌ خطایی در ارتباط با دیتابیس رخ داد. لطفا دوباره تلاش کنید.")
                return

            # بررسی شناسه قبض (مخصوص نیروگاه انشعابی / خانگی)
            if user_states.get(chat_id) == "waiting_for_bill_id":
                bill_id = normalize_digits(text.strip())

                if not bill_id.isdigit():
                    send_message(chat_id, "❌ شناسه قبض وارد شده معتبر نیست. لطفاً فقط عدد وارد کنید:")
                    return
                try:
                    cursor.execute("SELECT phone FROM BarghAppBot_users WHERE chat_id=%s", (chat_id,))
                    user_record = cursor.fetchone()
                    if user_record:
                        phone = user_record[0]
                        cursor.execute("""
                                       UPDATE barghapp_micro
                                       SET contor_number = %s
                                       WHERE phone = %s ORDER BY id DESC LIMIT 1
                                       """, (bill_id, phone))
                        db.commit()

                        user_states[chat_id] = "waiting_for_generation"
                        send_message(
                            chat_id,
                            "✅ شناسه قبض با موفقیت ثبت شد.\n\n"
                            "⚡ لطفا *میزان تولید* نیروگاه خود را (بر حسب کیلووات) وارد کنید:"
                        )
                    else:
                        send_message(chat_id, "❌ خطایی رخ داد. لطفا از ابتدا شروع کنید.")
                        user_states.pop(chat_id, None)

                except Exception as e:
                    print(f"Database Error: {e}")
                    send_message(chat_id, "❌ خطایی در ارتباط با دیتابیس رخ داد. لطفا دوباره تلاش کنید.")
                return
            # بررسی میزان تولید
            if user_states.get(chat_id) == "waiting_for_generation":
                generation_amount = text.strip()

                # بررسی اینکه آیا کاربر عدد وارد کرده است یا خیر
                if not generation_amount.replace('.', '', 1).isdigit():
                    send_message(chat_id, "❌ لطفا میزان تولید را فقط به صورت عدد وارد کنید:")
                    return

                try:
                    cursor.execute("SELECT phone FROM BarghAppBot_users WHERE chat_id=%s", (chat_id,))
                    user_record = cursor.fetchone()

                    if user_record:
                        phone = user_record[0]

                        # ۱. آپدیت کردن ستون generation در دیتابیس
                        cursor.execute("""
                                       UPDATE barghapp_micro
                                       SET generation = %s
                                       WHERE phone = %s ORDER BY id DESC LIMIT 1
                                       """, (float(generation_amount), phone))
                        db.commit()

                        # ۲. خواندن نوع نیروگاه کاربر از دیتابیس برای تصمیم‌گیری مسیر بعدی
                        cursor.execute("""
                                       SELECT plant_type
                                       FROM barghapp_micro
                                       WHERE phone = %s
                                       ORDER BY id DESC LIMIT 1
                                       """, (phone,))
                        plant_record = cursor.fetchone()
                        if plant_record:
                            plant_type = plant_record[0]

                            # ۳. تصمیم‌گیری بر اساس نوع نیروگاه
                            if plant_type == "نیروگاه انشعابی / خانگی":
                                # مسیر اول: اگر خانگی بود، می‌رود برای پرسش وضعیت حمایتی
                                user_states[chat_id] = "waiting_for_support_status"

                                keyboard = {
                                    "inline_keyboard": [
                                        [{"text": "بله، تحت پوشش هستم", "callback_data": "support_yes"}],
                                        [{"text": "خیر، تحت پوشش نیستم", "callback_data": "support_no"}]
                                    ]
                                }

                                send_message(
                                    chat_id,
                                    "✅ میزان تولید ثبت شد.\n\n"
                                    "آیا نیروگاه انشعابی/خانگی شما تحت پوشش نهادهای حمایتی (کمیته امداد، بهزیستی و...) قرار دارد؟",
                                    reply_markup=keyboard
                                )

                            else:
                                # مسیر دوم: اگر مقیاس کوچک بود، یکراست می‌رود برای انتخاب روش فروش (بورس/تضمینی)
                                user_states[chat_id] = "waiting_for_contract_type"

                                keyboard = {
                                    "inline_keyboard": [
                                        [{"text": "🔘 فروش تضمینی سالانه", "callback_data": "contract_guaranteed"}],
                                        [{"text": "🔘 فروش در بورس انرژی", "callback_data": "contract_bourse"}]
                                    ]
                                }

                                send_message(
                                    chat_id,
                                    "✅ میزان تولید با موفقیت ثبت شد.\n\n"
                                    "تمایل دارید برق تولیدی خود را به کدام روش به فروش برسانید؟\n"
                                    "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                                    reply_markup=keyboard
                                )

                    else:
                        send_message(chat_id, "❌ خطایی رخ داد. لطفا از ابتدا شروع کنید.")
                        user_states.pop(chat_id, None)

                except Exception as e:
                    print(f"Database Error: {e}")
                    send_message(chat_id, "❌ خطایی در ارتباط با دیتابیس رخ داد. لطفا دوباره تلاش کنید.")

                return
            # بررسی شناسه قبض برای خرید برق

            if user_states.get(chat_id) == "waiting_buy_power_bill_id":

                bill_id = msg.get("text")

                if not validate_bill_id(bill_id):
                    keyboard = {
                        "inline_keyboard": [
                            [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
                        ]
                    }
                    send_message(
                        chat_id,
                        "❌لطفاً شناسه قبض ۱۳ رقمی خود را بدون فاصله و حروف و علامت ارسال کنید. 🔹",
                        reply_markup=keyboard
                    )
                    return

                status, power, customer_name = check_bill_from_api(bill_id)

                # گرفتن شماره موبایل کاربر از دیتابیس
                cursor.execute(
                    "SELECT phone FROM BarghAppBot_users WHERE chat_id=%s",
                    (chat_id,)
                )

                user_row = cursor.fetchone()
                if user_row:
                    phone = user_row[0]
                else:
                    phone = None
                # ذخیره در barghapp_plus
                if status in ["OVER_150", "UNDER_150"]:
                    upsert_plus_query(phone, bill_id, power, customer_name, db, cursor)
                log_message(
                    f"PLUS SAVE => chat_id={chat_id} phone={phone} bill_id={bill_id}"
                )

                if status == "SERVER_ERROR":
                    keyboard = {
                        "inline_keyboard": [
                            [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
                        ]
                    }
                    send_message(
                        chat_id,
                        "⚠️ سامانه استعلام برق موقتاً در دسترس نیست.\nلطفاً دقایقی دیگر دوباره تلاش کنید و شناسه قبض ۱۳ رقمی خود را وارد کنید.",
                        reply_markup=keyboard
                    )
                    return
                if status == "INVALID_BILL":
                    keyboard = {
                        "inline_keyboard": [
                            [{"text": "استعلام شناسه قبض دیگر", "callback_data": "buy_power_2"}],
                            [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
                        ]
                    }
                    send_message(
                        chat_id,
                        "❌ شناسه قبض وارد شده معتبر نیست. لطفاً شناسه قبض صحیح را وارد کنید.",
                        reply_markup=keyboard
                    )
                    return
                if status == "NOT_FOUND":
                    keyboard = {
                        "inline_keyboard": [
                            [{"text": "استعلام شناسه قبض دیگر", "callback_data": "buy_power_2"}],
                            [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
                        ]
                    }
                    send_message(
                        chat_id,
                        "❌ شناسه قبض در سیستم یافت نشد! لطفا دوباره تلاش کنید.",
                        reply_markup=keyboard
                    )
                    return

                name_display = f" {customer_name}" if customer_name else ""
                if status == "OVER_150":

                    keyboard = {
                        "inline_keyboard": [
                            [{"text": "🔐 ورود به سامانه خرید برق", "url": "https://barghapplus.com/"}],
                            [{"text": "🔐 ورود به سایت", "url": "https://plus.barghapp.app/"}],
                            [{"text": "استعلام شناسه قبض دیگر", "callback_data": "buy_power_2"}],
                            [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
                        ]
                    }

                    send_message(
                        chat_id,
                        f"{name_display}عزیز \n"
                        f"✅ شناسه قبض {bill_id} یافت شد.\n"
                        f"⚡ قدرت قراردادی: {int(power)} کیلووات\n\n"
                        "✅ شما مشمول خرید برق هستید.\n"
                        "برای خرید برق روی دکمه 🔐 ورود به سامانه خرید برق کلیک کنید.",
                        reply_markup=keyboard
                    )
                    # ارسال پیامک موفقیت‌آمیز بودن استعلام
                    if phone:
                        sms_text = f"کاربر گرامی، شناسه قبض {bill_id} بررسی شد. شما مشمول خرید برق هستید.\nبرای ورود به سامانه خرید برق کلیک کنید:\nhttps://plus.barghapp.app"
                        send_delayed_sms(phone=phone, message_text=sms_text, delay_seconds=300)

                else:
                    keyboard = {
                        "inline_keyboard": [
                            [{"text": "استعلام شناسه قبض دیگر", "callback_data": "buy_power_2"}],
                            [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]

                        ]
                    }

                    send_message(
                        chat_id,
                        f"{name_display}عزیز \n"
                        f"✅ شناسه قبض شما بررسی شد\n\n"
                        f"⚡ قدرت قراردادی اشتراک: {int(power)} کیلووات\n\n"
                        "❌ در حال حاضر این اشتراک مشمول خرید برق نیست.\n\n"
                        "در صورت فراهم شدن شرایط، به شما اطلاع‌رسانی خواهد شد.",
                        reply_markup=keyboard
                    )
                    # ارسال پیامک عدم شمولیت
                    if phone:
                        sms_text = f"کاربر گرامی، شناسه قبض شما بررسی شد. در حال حاضر اشتراک شما مشمول خرید برق در بورس انرژی نیست."
                        send_delayed_sms(phone=phone, message_text=sms_text, delay_seconds=300)

                user_states.pop(chat_id, None)
                return

            # --- USER SENT CONTACT ---
            if msg.get("contact"):
                phone = msg["contact"].get("phone_number")
                if not phone:
                    send_message(
                        chat_id,
                        "شماره تلفن دریافت نشد. دوباره تلاش کنید."
                    )
                    return
                save_user(chat_id, first_name, last_name, phone, db, cursor)
                user_id = user["id"]

                if not check_channel_membership(user_id):
                    send_message(
                        chat_id,
                        "✅ شماره تماس شما با موفقیت ثبت شد.\n\n"
                        "برای دسترسی به تمامی امکانات و منوی خدمات، لطفاً از طریق دکمه زیر در کانال رسمی **برق‌آپ** عضو شوید و سپس روی «بررسی عضویت» کلیک کنید.",
                        reply_markup=get_join_channel_keyboard()
                    )
                    return

            # --- USER STATE FLOW ---

            # Check if user already exists in DB to show the correct UI
            try:
                # ۱. بررسی اینکه آیا کاربر اصلاً در دیتابیس هست (شماره داده)؟
                cursor.execute(
                    "SELECT first_name FROM `BarghAppBot_users` WHERE chat_id = %s",
                    (chat_id,)
                )
                user_data = cursor.fetchone()

                if not user_data:
                    # کاربر ثبت نام نکرده (شماره نداده)
                    send_message(
                        chat_id,
                        f"درود {first_name} عزیز 👋\nبرای اینکه بتوانیم خدمات ربات را برای شما فعال کنیم، به شماره تماس شما نیاز داریم.\n\n"
                        "کافیست روی دکمه پایین کیبورد کلیک کنید و شماره خود را بفرستید تا سریعاً کار را شروع کنیم. 👇",
                        reply_markup=get_contact_button()
                    )
                    return

                # ۲. کاربر شماره داده، حالا چک می‌کنیم عضو کانال هست یا نه؟
                if not check_channel_membership(chat_id):
                    # عضو کانال نیست! راه ورودش به خدمات بسته می‌شود.
                    send_message(
                        chat_id,
                        "⚠️ شما هنوز عضو کانال نشده‌اید.\n"
                        "برای دسترسی به منوی خدمات، ابتدا با استفاده از دکمه زیر عضو کانال شوید 👇 و سپس روی دکمه بررسی عضویت بزنید.",
                        reply_markup=get_join_channel_keyboard()
                    )
                    return

                # ۳. کاربر هم شماره داده و هم عضو کانال هست (ارسال منوی اصلی خدمات)
                db_first_name = user_data[0]
                caption_text = (
                    f"{db_first_name} عزیز 👋\n\n"
                    f"⚡️ برق‌آپ ماکرو، سامانه هوشمند فروش برق با قیمتی بیشتر از دولت!\n\n"
                    f"☀️ مالکین محترم نیروگاه‌های خورشیدی (انشعابی و مقیاس کوچک):\n\n"
                    f"🧮 با استفاده از ماشین‌حساب هوشمند، می‌توانید میزان افزایش درآمد نیروگاه خود را محاسبه کنید. 📈💸"
                )

                send_photo(
                    chat_id=chat_id,
                    photo_file_id=PHOTO_FILE_ID_BARGHAPP_MICRO,
                    caption=caption_text,
                    reply_markup=get_service_keyboard()
                )

            except mysql.connector.Error as err:
                log_message(f"❌ Database error checking user existence: {err}")
                send_message(chat_id, "خطایی در بررسی اطلاعات شما رخ داد. لطفا کمی بعد دوباره تلاش کنید.")

    finally:
        # ۲. بازگرداندن کانکشن به استخر (بسیار مهم)
        if cursor: cursor.close()
        if db and db.is_connected(): db.close()


def main():
    """Main function to run the bot."""
    global last_update_id

    if not initialize_database():
        log_message("❌ Exiting due to database initialization failure.")
        return

    log_message("Bot started. Listening for updates...")
    while True:
        try:
            params = {"timeout": 30}
            if last_update_id:
                params["offset"] = last_update_id

            response = requests.get(url + "getUpdates", params=params, timeout=40)  # Add timeout for getUpdates
            response.raise_for_status()
            data = response.json()

            if data.get("result"):
                for update in data["result"]:
                    # پاس دادن پردازش به تردها
                    executor.submit(handle_message, update)
                    last_update_id = update["update_id"] + 1
            else:
                pass

        except requests.exceptions.Timeout:
            log_message("Request timed out. Retrying...")
            # No need to update last_update_id here, as no updates were processed
        except requests.exceptions.RequestException as e:
            log_message(f"❌ Network error during getUpdates: {e}")

            time.sleep(5)  # Wait before retrying
        except Exception as e:
            log_message(f"❌ An unexpected error occurred: {e}")
            time.sleep(5)  # Wait before retrying


if __name__ == "__main__":
    main()
