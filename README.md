BarghApp Bale Messenger Bot ⚡
BarghApp Bot is an automated assistant for the Bale messenger platform, designed to bridge the gap between energy consumers, producers, and the BarghApp ecosystem. It facilitates electricity bill analysis, power purchasing, and energy market participation.

🚀 Features
User Registration: Seamlessly collects and stores user contact information in a MySQL database.
Service Integration: Direct access to various BarghApp specialized platforms:
Bill Analysis: Free electricity bill processing.
BarghApp Plus: Smart electricity purchasing for industrial/commercial users.
BarghApp Eco: Income generation through energy saving and optimization.
BarghApp Pro: Aggregation and sales management for small-scale power plants (Solar, Wind, etc.).
BarghApp Market: Specialized marketplace for power plant equipment and generators.
Rich Media Support: Sends instructional videos and interactive menus (Inline Keyboards) to enhance user experience.
Robust Database Handling: Automatic database and table initialization with error handling and rollbacks.
Persistent Connection: Built-in reconnection logic for both API requests and Database sessions.
🛠 Tech Stack
Language: Python 3.x
Database: MySQL
API: Bale Messenger Bot API (via requests)
Logging: Standard Python logging for real-time monitoring.
📋 Prerequisites
Python 3.8+
MySQL Server
A Bale Bot Token (obtainable via BotFather on Bale)
⚙️ Installation & Setup
Clone the repository:
bash
   git clone https://github.com/ariitooo/barghapp-bot.git
   cd barghapp-bot
Install dependencies:
bash
   pip install mysql-connector-python requests
Environment Variables:

For security, it is recommended to set the following environment variables. If not set, the bot will look for defaults (though editing the script is discouraged for production).

BOT_TOKEN: Your Bale API Token.
DB_HOST: Database host address (default: localhost).
DB_USER: Database username.
DB_PASSWORD: Database password.
DB_NAME: Database name (default: barghappbot).
Run the Bot:

bash
   python main.py
🗄 Database Schema
The bot automatically creates a table named BarghAppBot-users with the following structure:

id: Primary Key (Auto Increment)
chat_id: Unique Bale User ID
first_name / last_name: User profile names
phone: User’s shared contact number
created_at: Registration timestamp
🎥 Media Constants
The bot uses specific file_ids for videos. Ensure these IDs are valid within the Bale ecosystem or replace them with your own uploaded file IDs.

🤝 Contributing
Contributions are welcome! Please fork the repository and create a pull request for any improvements or bug fixes.
