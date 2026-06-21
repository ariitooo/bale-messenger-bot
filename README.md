⚡ BarghApp Bot | ربات برق‌آپ
Bilingual Documentation: Scroll down for the Persian (Farsi) version. | برای مطالعه نسخه فارسی به پایین صفحه مراجعه کنید.

🇬🇧 English Documentation
Overview
The BarghApp Bot is a high-performance, multi-platform messaging bot (optimized for Bale and Telegram) designed to serve as the unified front-line interface for the entire BarghApp energy ecosystem. It seamlessly integrates various services—from energy purchasing and consumption optimization to solar power aggregation and equipment trading—into a single, user-friendly digital gateway.

The architecture leverages ThreadPoolExecutor for concurrent request handling, cachetools for efficient state management, and a robust MySQL connection pool for secure and rapid data persistence.

Key Features & Ecosystem Integration
BarghApp Plus (برق‌آپ پلاس): Direct integration with external billing APIs to check eligibility for power purchasing (under/over 150kW and 1MW thresholds).

BarghApp Eco (برق‌آپ اکو): Interactive energy consumption profiler for household and industrial users to estimate consumption, suggest optimizations, and calculate potential economic savings through energy certificates.

BarghApp Macro (برق‌آپ ماکرو): Automated solar income calculator and aggregator flow helping residential and medium-scale solar producers maximize their return on investment.

BarghApp Market (برق‌آپ مارکت): Direct routing to the dedicated marketplace for buying and selling power plant equipment and spare parts.

CRM Integration: Seamless, real-time synchronization with Didar CRM for lead generation and automated deal creation.

Smart SMS Routing: Delayed and instant SMS notifications using the Asanak API.

Concurrent Architecture: Built to natively handle high traffic using Python's threading and pooling capabilities.

Prerequisites
Python 3.9+

MySQL Server

Active API tokens for your messaging platform (Bale/Telegram), Didar CRM, and Asanak SMS.

Installation
Clone the repository:

Bash
git clone https://github.com/yourusername/barghapp-bot.git
cd barghapp-bot

2.  **Install dependencies:**
    Ensure you have all the required Python libraries installed:
    ```bash
pip install cachetools concurrent-futures mysql-connector-python requests python-dotenv
Database Setup:
The bot automatically initializes the required database (barghappbot) and tables upon the first run via the initialize_database() function. Ensure your MySQL server is running and accessible.

Environment Variables (.env)

<img width="566" height="652" alt="1" src="https://github.com/user-attachments/assets/abe25acc-d43d-4cf6-a6fa-7b3de5fd06bf" />

Usage
Run the bot using:

Bash
python bot.py




🇮🇷 مستندات فارسی (Persian Documentation)
معرفی
ربات جامع برق‌آپ یک ربات پیام‌رسان چندپلتفرمی (بله / تلگرام) با عملکرد بالا است که به عنوان درگاه یکپارچه و دیجیتال برای کل اکوسیستم انرژی برق‌آپ طراحی شده است. این ربات خدمات متنوعی از جمله خرید برق، بهینه‌سازی مصرف، تجمیع نیروگاه‌های خورشیدی و بازار تجهیزات را در یک رابط کاربری ساده و هوشمند به کاربران ارائه می‌دهد.

در معماری این پروژه از ThreadPoolExecutor برای مدیریت همزمان درخواست‌ها، cachetools برای مدیریت بهینه وضعیت (State) کاربران، و یک استخر اتصال (Connection Pool) قدرتمند MySQL برای ذخیره‌سازی امن اطلاعات استفاده شده است.

ویژگی‌های کلیدی و خدمات یکپارچه
برق‌آپ پلاس: ارتباط مستقیم با APIهای صورت‌حساب برای بررسی مشمولیت خرید برق در بورس انرژی (برای مشترکین بالای ۱۵۰ کیلووات و ۱ مگاوات).

برق‌آپ اکو: پروفایلر تعاملی مصرف انرژی برای مشترکین خانگی و صنعتی جهت تخمین میزان مصرف و پتانسیل کسب درآمد از طریق گواهی‌های صرفه‌جویی.

برق‌آپ ماکرو: محاسبه‌گر خودکار درآمد خورشیدی برای سودآوری بیشتر نیروگاه‌های انشعابی و مقیاس کوچک و ثبت قراردادهای تجمیع برق.

برق‌آپ مارکت: هدایت کاربران به فروشگاه تخصصی جهت خرید و فروش تجهیزات نیروگاهی و قطعات یدکی.

اتصال مستقیم به دیدار CRM: همگام‌سازی لحظه‌ای لیدها (سرنخ‌ها) و ایجاد خودکار معامله در سیستم ارتباط با مشتری.

سیستم هوشمند پیامک: ارسال پیامک‌های فوری و زمان‌بندی‌شده از طریق وب‌سرویس آسانک.

معماری همزمان (Concurrent): بهینه‌سازی شده برای مدیریت ترافیک بالا با استفاده از قابلیت Threading در پایتون.

پیش‌نیازها
پایتون ۳.۹ یا بالاتر

سرور MySQL

توکن‌های فعال برای پلتفرم پیام‌رسان (بله/تلگرام)، دیدار CRM و پنل پیامکی آسانک.

نصب و راه‌اندازی
۱. کلون کردن مخزن:
```bash
git clone https://github.com/yourusername/barghapp-bot.git
cd barghapp-bot


۲. **نصب وابستگی‌ها:**
    پکیج‌های مورد نیاز را نصب کنید:
    ```bash
pip install cachetools concurrent-futures mysql-connector-python requests python-dotenv
۳. پیکربندی دیتابیس:
ربات در اولین اجرا به صورت خودکار دیتابیس (barghappbot) و جداول مورد نیاز را می‌سازد. فقط کافیست مطمئن شوید سرویس MySQL شما روشن و در دسترس است.


<img width="630" height="590" alt="2" src="https://github.com/user-attachments/assets/9fcbd64f-1eb9-48d5-99a9-51e379f615e5" />




نحوه اجرا
برای روشن کردن ربات، دستور زیر را در ترمینال وارد کنید:

Bash
python bot.py



written  by : ariitooo

