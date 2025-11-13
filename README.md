# 🏢 SHAWO Umzüge Telegram Bot

Ein professioneller, mehrsprachiger Telegram-Bot für SHAWO Umzüge mit KI-Integration, Preisberechnungen und Terminbuchungssystem.

🌐 **Offizielle Website**: [shawo-umzug-app.de](https://shawo-umzug-app.de)
🌐 **Telegram Bot**: [SHAWO_bot](https://t.me/SHAWO_bot)

---

## ✨ Hauptfunktionen

### 🤖 Intelligenter KI-Assistent
- **Google Gemini AI Integration** für natürliche Konversationen
- **Automatische Spracherkennung** (20+ Sprachen)
- **Kontextbewusste Antworten** auf Kundenanfragen

### 💰 Umfassende Preisberechnung
Vollständige Preis-Datenbank für alle Dienstleistungen:
- **Umzugsdienstleistungen** (1-Zimmer bis Hausumzüge)
- **Maler- & Renovierungsarbeiten**
- **Bodenverlegung** (Laminat, PVC, etc.)
- **Reinigungsdienstleistungen**

### 📅 Kalender & Buchungssystem
- **Visuelle Kalenderansicht** mit gebuchten Terminen
- **Echtzeit-Verfügbarkeitsprüfung**
- **Automatische Terminkonflikterkennung**
- **Blockierte Tage Management**

### 🌍 Mehrsprachiger Support
Vollständige Unterstützung für 20+ Sprachen inklusive:
- Deutsch, Englisch, Arabisch, Französisch, Spanisch
- Italienisch, Türkisch, Russisch, Polnisch, Chinesisch
- Japanisch, Koreanisch, und viele mehr

---

## 🛠️ Technische Architektur

### 🔐 Sichere Datenverarbeitung
```python
class SecureBot:
    def decrypt_config(self, key):
        # Verschlüsselte Konfigurationsdateien
        cipher_suite = Fernet(key.encode())
        # Sichere Schlüsselverwaltung
```

### 🗃️ Datenbank-Design
- **SQLite** für Terminverwaltung
- **Persistente Datenspeicherung**
- **Transaktionssichere Buchungen**
- **Index-optimierte Abfragen**

### 🎯 Kern-Klassen & Module

#### CalendarManager
```python
class CalendarManager:
    def book_appointment(self, date_str, customer_name, contact_info, service, user_id):
        # Terminbuchung mit Verfügbarkeitsprüfung
        if not self.is_date_available(date_str):
            return False
```

#### Mehrsprachiges System
```python
MULTILINGUAL_RESPONSES = {
    'de': {'start': {'welcome': "Willkommen bei SHAWO!", ...}},
    'en': {'start': {'welcome': "Welcome to SHAWO!", ...}},
    # ... 20+ Sprachen
}
```

#### Preis-Datenbank
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

## 🚀 Installation & Einrichtung

### Voraussetzungen
- Python 3.8 oder höher
- Telegram Bot Token
- Google Gemini API Key

### Schritt-für-Schritt Installation

1. **Repository klonen**
```bash
git clone https://github.com/FouaadAI/shawo-telegram-bot.git
cd shawo-telegram-bot
```

2. **Abhängigkeiten installieren**
```bash
pip install -r requirements.txt
```

3. **Konfiguration einrichten**
   - Bot Token in `config.enc` setzen
   - Gemini API Key konfigurieren
   - Datenbank initialisieren

4. **Bot starten**
```bash
python main_compiled_enhanced.py
```

---

## 📋 Bot-Befehle

| Befehl | Beschreibung | Beispiel |
|--------|--------------|----------|
| `/start` | Bot starten & Begrüßung | `/start` |
| `/contact` | Kontaktinformationen | `/contact` |
| `/services` | Dienstleistungsübersicht | `/services` |
| `/prices` | Preisbeispiele anzeigen | `/prices` |
| `/calendar` | Kalender anzeigen | `/calendar` |
| `/book` | Termin buchen | `/book 15.12.2024` |
| `/help` | Hilfeseite anzeigen | `/help` |

---

## 🏗️ Projektstruktur

```
shawo-telegram-bot/
├── main_compiled_enhanced.py    # Hauptanwendungsdatei
├── storage.db                   # SQLite Datenbank
├── config.enc                   # Verschlüsselte Konfiguration
├── requirements.txt            # Python Abhängigkeiten
├── key.txt                     # Verschlüsselungsschlüssel
└── README.md                   # Diese Dokumentation
```

---

## 🔧 Wichtige Code-Komponenten

### 1. Sicherheits-System
```python
class SecureBot:
    def init_bot(self):
        # Initialisiert den geschützten Bot
        TOKEN = os.getenv("TOKEN")
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        ADMIN_CHAT_ID =# "your group or chat ID"
```

### 2. Kalender-Management
```python
def generate_calendar_view(self, year: int, month: int, language: str = 'de'):
    # Generiert eine visuelle Kalenderansicht
    # mit gebuchten und verfügbaren Terminen
```

### 3. Sprach-Erkennung
```python
def detect_telegram_language(update: Update):
    # Erkennt die Sprache des Users aus Telegram Systemeinstellungen
    # Fallback zur Nachrichtenanalyse
```

### 4. Termin-Buchung
```python
def book_appointment(self, date_str: str, customer_name: str, 
                    contact_info: str, service: str, user_id: str) -> bool:
    # Bucht einen Termin mit vollständiger Validierung
```

---

## 📊 Datenbank-Schema

### Appointments Tabelle
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

### Blocked Days Tabelle
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

## 🌐 Unterstützte Sprachen

- ✅ Deutsch
- ✅ Englisch  
- ✅ Arabisch
- ✅ Französisch
- ✅ Spanisch
- ✅ Italienisch
- ✅ Türkisch
- ✅ Russisch
- ✅ Polnisch
- ✅ Ukrainisch
- ✅ Chinesisch
- ✅ Japanisch
- ✅ Koreanisch
- ✅ Portugiesisch
- ✅ Niederländisch
- ✅ Schwedisch
- ✅ Dänisch
- ✅ und mehr...

---

## 📞 Kontakt & Support

**SHAWO Umzüge**  
📍 Wörther Straße 32, 13595 Berlin  
📱 +49 176 72407732  
✉️ shawo.info.betrieb@gmail.com  
🌐 [shawo-umzug-app.de](https://shawo-umzug-app.de)

---

## 📄 Lizenz

Proprietär - Entwickelt für SHAWO Umzüge

---

*Professionelle Umzugs- und Renovierungsdienstleistungen in Berlin und ganz Deutschland*
