# 🏢 SHAWO Moves Telegram Bot

A professional, multilingual Telegram bot for SHAWO Moves with AI integration, price calculations, and booking system.

🌐 **Official Website**: [shawo-umzug-app.de](https://shawo-umzug-app.de)  
🤖 **Telegram Bot**: [SHAWO_bot](https://t.me/SHAWO_bot)

---

## ✨ Key Features

### 🤖 Intelligent AI Assistant
- **Google Gemini AI Integration** for natural conversations
- **Automatic Language Detection** (20+ languages)
- **Context-Aware Responses** to customer inquiries

### 💰 Comprehensive Price Calculation
Complete price database for all services:
- **Moving Services** (1-room to house moves)
- **Painting & Renovation Work**
- **Floor Installation** (Laminate, PVC, etc.)
- **Cleaning Services**

### 📅 Calendar & Booking System
- **Visual Calendar View** with booked appointments
- **Real-Time Availability Check**
- **Automatic Conflict Detection**
- **Blocked Days Management**

### 🌍 Multilingual Support
Full support for 20+ languages including:
- German, English, Arabic, French, Spanish
- Italian, Turkish, Russian, Polish, Chinese
- Japanese, Korean, and many more

---

## 🛠️ Technical Architecture

### 🔐 Secure Data Processing
```python
class SecureBot:
    def decrypt_config(self, key):
        # Encrypted configuration files
        cipher_suite = Fernet(key.encode())
        # Secure key management
```

### 🗃️ Database Design
- **SQLite** for appointment management
- **Persistent Data Storage**
- **Transaction-Safe Bookings**
- **Index-Optimized Queries**

### 🎯 Core Classes & Modules

#### CalendarManager
```python
class CalendarManager:
    def book_appointment(self, date_str, customer_name, contact_info, service, user_id):
        # Appointment booking with availability check
        if not self.is_date_available(date_str):
            return False
```

#### Multilingual System
```python
MULTILINGUAL_RESPONSES = {
    'de': {'start': {'welcome': "Willkommen bei SHAWO!", ...}},
    'en': {'start': {'welcome': "Welcome to SHAWO!", ...}},
    # ... 20+ languages
}
```

#### Price Database
```python
PRICE_DATABASE = {
    "maler": {
        "grundierung": {"price": 5, "unit": "m²"},
        "anstrich": {"price": 12, "unit": "m²"}
    },
    "umzug": {
        "1_zimmer": {"min": 450, "max": 550},
        "2_zimmer": {"min": 650, "max": 750}
    }
}
```

---

## 🔒 Security & Encryption

### Configuration Encryption
Sensitive data (API Keys, Tokens) are stored encrypted in `config.enc`.

#### Creating Encrypted Configuration:

1. **Create a `.env` file with credentials:**
```bash
# .env Example
TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_google_gemini_api_key_here
ADMIN_CHAT_ID=your_group_or_chat_id_here
```

2. **Run encryption script:**
```python
from cryptography.fernet import Fernet
import os

# Generate key
key = Fernet.generate_key()
with open('key.txt', 'wb') as key_file:
    key_file.write(key)

# Encrypt configuration
cipher_suite = Fernet(key)
with open('.env', 'rb') as file:
    config_data = file.read()

encrypted_data = cipher_suite.encrypt(config_data)
with open('config.enc', 'wb') as file:
    file.write(encrypted_data)

print("✅ Configuration successfully encrypted!")
print("🔐 Key saved in key.txt")
print("📁 Encrypted file: config.enc")
```

3. **Decryption during operation:**
```python
def decrypt_config(self, key):
    cipher_suite = Fernet(key.encode())
    with open('config.enc', 'rb') as f:
        encrypted = f.read()
    decrypted = cipher_suite.decrypt(encrypted).decode()
    
    # Set environment variables
    for line in decrypted.splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip()
```

---

## 📋 Requirements.txt

```txt
python-telegram-bot==20.7
google-generativeai==0.3.0
python-dotenv==1.0.0
cryptography==41.0.7
langdetect==1.0.9
python-dateutil==2.8.2
```

### Install Dependencies:
```bash
pip install -r requirements.txt
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Telegram Bot Token
- Google Gemini API Key

### Step-by-Step Installation

1. **Clone repository**
```bash
git clone https://github.com/FouaadAI/shawo-telegram-bot.git
cd shawo-telegram-bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Setup configuration**
   - Create `.env` file with credentials
   - Run encryption with `encrypt_config.py`
   - Securely store `key.txt`

4. **Start bot**
```bash
python main_compiled_enhanced.py
```

---

## 📋 Bot Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Start bot & welcome | `/start` |
| `/contact` | Contact information | `/contact` |
| `/services` | Service overview | `/services` |
| `/prices` | Show price examples | `/prices` |
| `/calendar` | Show calendar | `/calendar` |
| `/book` | Book appointment | `/book 15.12.2024` |
| `/help` | Show help page | `/help` |

---

## 🏗️ Project Structure

```
shawo-telegram-bot/
├── main_compiled_enhanced.py    # Main application file
├── storage.db                   # SQLite database
├── config.enc                   # Encrypted configuration
├── key.txt                      # Encryption key
├── .env                         # Configuration template (do not commit!)
├── requirements.txt            # Python dependencies
├── encrypt_config.py           # Encryption script
└── README.md                   # This documentation
```

---

## 🔧 Important Code Components

### 1. Security System
```python
class SecureBot:
    def init_bot(self):
        # Initialize protected bot
        TOKEN = os.getenv("TOKEN")
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "your_default_chat_id")
```

### 2. Calendar Management
```python
def generate_calendar_view(self, year: int, month: int, language: str = 'de'):
    # Generate visual calendar view
    # with booked and available appointments
```

### 3. Language Detection
```python
def detect_telegram_language(update: Update):
    # Detect user language from Telegram system settings
    # Fallback to message analysis
```

### 4. Appointment Booking
```python
def book_appointment(self, date_str: str, customer_name: str, 
                    contact_info: str, service: str, user_id: str) -> bool:
    # Book appointment with full validation
```

---

## 📊 Database Schema

### Appointments Table
```sql
CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    contact_info TEXT NOT NULL,
    service TEXT NOT NULL,
    user_id TEXT NOT NULL,
    created_at TEXT,
    UNIQUE(date)
)
```

### Blocked Days Table
```sql
CREATE TABLE blocked_days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    reason TEXT,
    blocked_by TEXT,
    created_at TEXT,
    UNIQUE(date)
)
```

---

## 🌐 Supported Languages

- ✅ German
- ✅ English  
- ✅ Arabic
- ✅ French
- ✅ Spanish
- ✅ Italian
- ✅ Turkish
- ✅ Russian
- ✅ Polish
- ✅ Ukrainian
- ✅ Chinese
- ✅ Japanese
- ✅ Korean
- ✅ Portuguese
- ✅ Dutch
- ✅ Swedish
- ✅ Danish
- ✅ and more...

---

## 📞 Contact & Support

**SHAWO Moves**  
📍 Wörther Straße 32, 13595 Berlin  
📱 +49 176 72407732  
✉️ shawo.info.betrieb@gmail.com  
🌐 [shawo-umzug-app.de](https://shawo-umzug-app.de)

---

## ⚠️ Important Notes

- **Security**: Never commit `key.txt` and `.env` to repository
- **Backup**: Regularly backup `storage.db`
- **Updates**: Keep bot updated to latest versions
- **Monitoring**: Monitor system resources

---

## 📄 License

Proprietary - Developed for SHAWO Moves

---

*Professional moving and renovation services in Berlin and throughout Germany*
