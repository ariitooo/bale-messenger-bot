import time
import requests
import mysql.connector
from datetime import datetime

# --- Configuration ---
BOT_TOKEN = "1724414978:JQlr9LU_NdpD32WoiU6vngxgkIvnCrMoIqs"
url = f"https://tapi.bale.ai/bot{BOT_TOKEN}/"
VIDEO_FILE_ID_BARGHAPP = "729844006:-1772778552087404798:0:74d2d6c270bf5f3a"
VIDEO_FILE_ID_BARGHAPP_PLUS = "729844006:-2569460069165555968:0:d30763dba31b2824"
VIDEO_FILE_ID_BARGHAPP_ECO = "979506434:6208782014560608003:0:9332c0020b754fae"
VIDEO_FILE_ID_BARGHAPP_PRO = "729844006:-7987177643801567487:0:4887db61a7a8c514"
VIDEO_FILE_ID_BARGHAPP_MARKET = "729844006:-1136604059151032574:0:8850bf0d68f60f23"
VIDEO_FILE_ID_DARBAREH_BARGHAPP = "729844006:-1772778552087404798:0:74d2d6c270bf5f3a"
# --- create database and tables--- (run once)
# def initialize_database():
#
#     db = mysql.connector.connect(
#         host="localhost",
#         user="root",
#         password="1379Arta1380*"
#     )
#     cursor = db.cursor()
#
#     cursor.execute("CREATE DATABASE IF NOT EXISTS barghappbot;")
#     print("✅ Database 'barghappbot' is ready.")
#
#     cursor.execute("USE barghappbot;")
#
#     cursor.execute("""
#     CREATE TABLE IF NOT EXISTS `BarghAppBot` (
#         id INT AUTO_INCREMENT PRIMARY KEY,
#         chat_id BIGINT UNIQUE,
#         first_name VARCHAR(100),
#         last_name VARCHAR(100),
#         phone VARCHAR(30),
#         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#     );
#     """)
#     print("✅ Table 'BarghAppBot' is ready.")
#
#     cursor.close()
#     db.close()
#
#     print("🎉 Database setup complete.\n")
#
#
# initialize_database()

# --- data access ---

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1379Arta1380*",
    "database": "barghappbot"
}

# --- Global Variables ---
db = None
cursor = None
last_update_id = None

# --- Helper Functions ---

def log_message(message):
    """Simple logging to console."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def connect_db():
    """Establishes connection to the database."""
    global db, cursor
    try:
        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor()
        log_message("✅ Database connection established.")
        return True
    except mysql.connector.Error as err:
        log_message(f"❌ Database connection error: {err}")
        db = None
        cursor = None
        return False

def close_db():
    """Closes the database connection."""
    global db, cursor
    if cursor:
        cursor.close()
    if db and db.is_connected():
        db.close()
        log_message("✅ Database connection closed.")

def send_message(chat_id, text, reply_markup=None):
    """Sends a message to the specified chat_id."""
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        response = requests.post(url + "sendMessage", json=payload, timeout=10)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
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
def send_gif(chat_id, GIF_FILE_ID, caption=None):
    payload = {
        "chat_id": chat_id,
        "animation": GIF_FILE_ID
    }
    if caption:
        payload["caption"] = caption

    try:
        response = requests.post(url + "sendAnimation", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        log_message(f"❌ Failed to send gif to {chat_id}: {e}")
        return None

def add_back_button(keyboard):
    keyboard["inline_keyboard"].append(
        [{"text": "🔙 بازگشت به منوی اصلی", "callback_data": "main_menu"}]
    )
    return keyboard
# --- Database Initialization (Run Once) ---
def initialize_database():
    """Creates the database and table if they don't exist."""
    log_message("Attempting to initialize database...")
    try:
        # Connect without specifying database first
        db_init = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor_init = db_init.cursor()

        cursor_init.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']};")
        log_message(f"✅ Database '{DB_CONFIG['database']}' is ready.")

        cursor_init.execute(f"USE {DB_CONFIG['database']};")

        cursor_init.execute("""
        CREATE TABLE IF NOT EXISTS `BarghAppBot-users` (
            id INT AUTO_INCREMENT PRIMARY KEY,
            chat_id BIGINT UNIQUE,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            phone VARCHAR(30),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
        log_message("✅ Table 'BarghAppBot-users' is ready.")

        cursor_init.close()
        db_init.close()
        log_message("🎉 Database setup complete.")
        return True
    except mysql.connector.Error as err:
        log_message(f"❌ Database initialization error: {err}")
        return False

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
            [{"text": "تحلیل قبض رایگان", "callback_data": "bill_analysis"}],
            [
                {"text": "خرید برق", "callback_data": "buy_power"},
                {"text": "درآمدزایی از صرفه‌جویی", "callback_data": "eco_income"}
            ],
            [
                {"text": "تجمیع نیروگاه‌ها", "callback_data": "power_plants"},
                {"text": "تجهیزات نیروگاهی", "callback_data": "equipment"}
            ],
            [{"text": "درباره برق‌آپ", "callback_data": "website"}]
        ]
    }

# --- Main Bot Loop ---

def handle_message(update):
    """Processes a single update from the Bale API."""
    global last_update_id

    if "message" in update:
        message = update["message"]
        chat_id = message["chat"]["id"]



          # اگر فایل webm یا ویدیو ارسال شد
    # if "message" in update:
    #     message = update["message"]
    #     chat_id = message["chat"]["id"]
    #
    #     if "video" in message:
    #         video_file_id = message["video"]["file_id"]
    #         log_message(f"VIDEO file_id: {video_file_id}")
    #         send_message(chat_id, "✅ ویدیو دریافت شد")
    #         return

    if "callback_query" in update:
        callback_query = update["callback_query"]
        chat_id = callback_query["message"]["chat"]["id"]
        data = callback_query["data"]

        if data == "bill_analysis":

            keyboard = add_back_button({
                "inline_keyboard": [
                    [
                        {"text": "🔗 ورود به سامانه", "url": "https://bill-analysis.barghapp.com"}
                    ]
                ]
            })

            send_video(
                chat_id,
                VIDEO_FILE_ID_DARBAREH_BARGHAPP,
                caption="✅ تحلیل قبض برق شما به‌صورت کاملاً رایگان انجام می‌شود.\n👇 روی لینک زیر بزنید",
                reply_markup=keyboard
            )







        elif data == "buy_power":

            keyboard =add_back_button ({
                "inline_keyboard": [
                    [
                        {"text": "🌐 ورود به سایت", "url": "https://plus.barghapp.com/"},
                        {"text": "🔐 ورود به سامانه", "url": "https://barghapplus.com/"}
                    ]
                ]
            })

            send_video(
                chat_id,
                VIDEO_FILE_ID_BARGHAPP_PLUS,
                caption=(
                    "💰 معرفی برق‌آپ پلاس\n\n"
                    "برق‌آپ پلاس، اولین سامانه هوشمند خرید برق در ایران\n\n"
                    "سامـــــانه بـــــرق‌آپ پـــــلاس اولیـــــن سامـــــانه جامع آنـــــلاین خریـــــد برق در کشـــــور است که در تاریخ ۱ آبان ۱۴۰۲ متـــــولد گردیـــــد. "
                    "این سامـــــانه دانش بنیـــــان به منظـــــور تسهیـــــل در خرـــــید بـــــرق مشترکیـــــن بـــــالای “۳۰” کیـــــلووات طراحـــــی و به بهـــــره بـــــرداری رسیـــــد  "
                    "و مشترکیـــــن شـــــرکتهای بـــــرق منطقه ای و توزیـــــع نیـــــروی بـــــرق می توانند بـــــرق عادی (حرارتی)، بـــــرق سبـــــز و بـــــرق عدم مشـــــمول مـــــدیریت مصرف "
                    "را با شرایـــــط کـــــاملاً منـــــعطف خـــــریداری نمـــــوده و از این سامـــــانه گزارشـــــات متنـــــوعی را دریـــــافت نمـــــایند. "

                ),
                reply_markup=keyboard
            )
        elif data == "main_menu":

            send_message(
                chat_id,
                "🏠 منوی اصلی:",
                get_service_keyboard()
            )

            # پاسخ به callback query (الزامی)

            requests.post(

                url + "answerCallbackQuery",

                json={"callback_query_id": callback_query["id"]},

                timeout=5

            )




        elif data == "eco_income":

            keyboard = add_back_button({
                "inline_keyboard": [
                    [
                        {"text": "🌐 ورود به سایت", "url": "https://eco.barghapp.com"},
                        {"text": "🔐 ورود به سامانه", "url": "https://eco.barghapp.app"}
                    ]
                ]
            })

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
                reply_markup=keyboard
            )

            # پاسخ به callback (الزامی)

            requests.post(

                url + "answerCallbackQuery",

                json={"callback_query_id": callback_query["id"]},

                timeout=5

            )
        elif data == "power_plants":

            keyboard = add_back_button({
                "inline_keyboard": [
                    [
                        {"text": "🌐 ورود به سایت", "url": "https://pro.barghapp.com"},
                        # {"text": "🔐 ورود به سامانه", "url": "https://eco.barghapp.com/login"}
                    ]
                ]
            })

            send_video(
                chat_id,
                VIDEO_FILE_ID_BARGHAPP_PRO,
                caption=(
                     "⚡ معرفی برق‌آپ پرو\n\n"
            "برق‌آپ پرو، اولین سامانه هوشمند تجمیع و فروش برق نیروگاه‌ها در ایران\n\n"
            "برق‌آپ پرو سامانه تجمیع خرید برق تولیدی نیروگاه‌های مقیاس کوچک، "
            "خورشیدی (انشعابی و غیرانشعابی)، برقابی، بادی و آبی می‌باشد که "
            "بصورت یک نیروگاه مجازی یکپارچه فعالیت می‌کند. مالکین این نیروگاه‌ها "
            "می‌توانند برق تولیدی نیروگاه خود را با ثبت‌نام در سامانه برق‌آپ پرو "
            "و با انعقاد قرارداد با بهترین شرایط و کمترین ریسک به‌فروش برسانند. "
            "مالکین نیروگاه‌ها می‌توانند از مزایایی همچون دریافت وجه پیش از شروع "
            "دوره تولید، امکان تولید و فروش بیش از حجم توافقی و همچنین جبران خسارت "
            "عدم تولید نیروگاه توسط برق‌آپ پرو بهره‌مند شوند. برای شروع کافیست "
            "مالکین نیروگاه‌ها با ثبت‌نام در سایت برق‌آپ پرو درخواست خود را ثبت نمایند."
                ),
                reply_markup=keyboard
            )

            # پاسخ به callback (الزامی)

            requests.post(

                url + "answerCallbackQuery",

                json={"callback_query_id": callback_query["id"]},

                timeout=5

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
                    [
                        {"text": "🌐 ورود به سایت", "url": "https://barghapp.com"},
                    ]
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

        first_name = user.get("first_name", "")
        last_name = user.get("last_name", "")
        name = f"{first_name} {last_name}".strip()
        log_message(f"Received message from {name} (chat_id: {chat_id})")

        # --- 5. USER SENT CONTACT ---
        if msg.get("contact"):
            phone = msg["contact"].get("phone_number")

            if not phone:
                send_message(chat_id, "متاسفانه شماره‌ای دریافت نشد. لطفا دوباره تلاش کنید.")
                return

            try:
                # Check if user already exists
                cursor.execute("SELECT phone FROM `BarghAppBot-users` WHERE chat_id = %s", (chat_id,))
                existing_user = cursor.fetchone()

                if existing_user:
                    send_message(chat_id, "📌 ما شماره شما را از قبل داریم.\nنیازی به ثبت دوباره نیست 😊")
                else:
                    # Save new user
                    cursor.execute(
                        """
                        INSERT INTO `BarghAppBot-users` (chat_id, first_name, last_name, phone)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (chat_id, first_name, last_name, phone)
                    )
                    db.commit()
                    send_message(chat_id, "✅ اطلاعات شما با موفقیت ذخیره شد.")

                # Send service keyboard after phone is received/processed
                send_message(chat_id, "حالا یکی از خدمات برق‌آپ را انتخاب کن:", reply_markup=get_service_keyboard())

            except mysql.connector.Error as err:
                log_message(f"❌ Database error handling contact: {err}")
                db.rollback() # Rollback in case of error
                send_message(chat_id, "خطایی در ذخیره اطلاعات رخ داد. لطفا کمی بعد دوباره تلاش کنید.")
            return

        # --- 6. NORMAL MESSAGE → SEND VIDEO + ASK CONTACT ---
        # This block is reached if the message is NOT a contact and the user hasn't sent contact before
        # We assume if they sent a normal message, they haven't sent contact yet.
        # A more robust check would involve querying the DB for the user's phone number.

        # Check if user already exists in DB to show the correct UI
        try:
            cursor.execute("SELECT phone FROM `BarghAppBot-users` WHERE chat_id = %s", (chat_id,))
            user_exists = cursor.fetchone()
            if user_exists and user_exists[0]:  # User is registered: show services, DO NOT ask phone again
                send_message(
                    chat_id,
                    f"درود {name} عزیز 👋\nبه برق‌آپ خوش آمدید.\nیکی از خدمات زیر را انتخاب کنید:",
                    reply_markup=get_service_keyboard()
                )
                log_message(f"User {chat_id} already registered. Sent service keyboard.")

            else:  # User not registered: ask for phone number
                send_video(
                    chat_id,
                    VIDEO_FILE_ID_DARBAREH_BARGHAPP,
                    f"سلام {name}! 👋\nبه برق‌آپ خوش آمدید.\nبرای ادامه، لطفا روی دکمه زیر بزنید و شماره خود را ارسال کنید.",
                    reply_markup=get_contact_button()
                )
                log_message(f"Sent intro video and asked phone to {chat_id} (unregistered user).")
        except mysql.connector.Error as err:
            log_message(f"❌ Database error checking user existence: {err}")
            send_message(chat_id, "خطایی در بررسی اطلاعات شما رخ داد. لطفا کمی بعد دوباره تلاش کنید.")


    last_update_id = update["update_id"] + 1 # Always update last_update_id


def main():
    """Main function to run the bot."""
    global last_update_id

    if not initialize_database():
        log_message("❌ Exiting due to database initialization failure.")
        return

    if not connect_db():
        log_message("❌ Exiting due to initial database connection failure.")
        return

    log_message("Bot started. Listening for updates...")
    while True:
        try:
            params = {"timeout": 30} # Long polling timeout
            if last_update_id:
                params["offset"] = last_update_id

            response = requests.get(url + "getUpdates", params=params, timeout=40) # Add timeout for getUpdates
            response.raise_for_status() # Check for HTTP errors
            data = response.json()

            if data.get("result"):
                for update in data["result"]:
                    handle_message(update)
                    last_update_id = update["update_id"] + 1 # Ensure last_update_id is updated after each processed update
            else:
                # No updates received, just keep looping. Optionally log this.
                # log_message("No new updates.")
                pass

        except requests.exceptions.Timeout:
            log_message("Request timed out. Retrying...")
            # No need to update last_update_id here, as no updates were processed
        except requests.exceptions.RequestException as e:
            log_message(f"❌ Network error during getUpdates: {e}")
            # Attempt to reconnect if connection is lost
            if db and not db.is_connected():
                log_message("Database connection lost, attempting to reconnect...")
                close_db()
                connect_db()
            time.sleep(5) # Wait before retrying
        except Exception as e:
            log_message(f"❌ An unexpected error occurred: {e}")
            # Attempt to reconnect if connection is lost
            if db and not db.is_connected():
                log_message("Database connection lost, attempting to reconnect...")
                close_db()
                connect_db()
            time.sleep(5) # Wait before retrying

        # If needed, add a small sleep for very high traffic scenarios to reduce load.

if __name__ == "__main__":
    main()





