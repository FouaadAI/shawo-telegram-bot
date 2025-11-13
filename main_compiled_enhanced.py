# main_compiled_enhanced_optimized_with_calendar.py
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from dotenv import load_dotenv
import os
import sqlite3
from datetime import datetime, timedelta
import re
from langdetect import detect, LangDetectException
from telegram.constants import ParseMode 
from cryptography.fernet import Fernet
import json
import calendar
from typing import Dict, List, Optional, Tuple

# 🏢 VOLLSTÄNDIGE PREISDATENBANK
PRICE_DATABASE = {
    "maler": {
        "grundierung": {"price": 5, "unit": "m²", "description": "Grundierung Wände & Decken"},
        "nivellierung": {"price": 25, "unit": "m²", "description": "Nivellierung der Oberflächen"},
        "spachteln": {"price": 20, "unit": "m²", "description": "Spachteln Wände & Decken"},
        "anstrich": {"price": 12, "unit": "m²", "description": "Anstrich Wände, Decken, Schrägen"},
        "streichen": {"price": 12, "unit": "m²", "description": "Streichen Wände, Decken"},
        "tapezieren": {"price": 10, "unit": "m²", "description": "Tapezieren je nach Tapetentyp"},
        "heizkoerper": {"price": 25, "unit": "m²", "description": "Anstrich Heizkörper & Rohre"},
        "holzbehandlung": {"price": 15, "unit": "m²", "description": "Behandlung Holzoberflächen"},
        "entfernen": {"price": 15, "unit": "m²", "description": "Entfernen Farben & Tapeten"},
        "tueren_anstrich": {"price": 100, "unit": "Stück", "description": "Türen - Innenanstrich"},
        "tueren_schleifen": {"price": 130, "unit": "Stück", "description": "Alte Holztüren abschleifen & lackieren"},
        "fenster_anstrich": {"price": 70, "unit": "Stück", "description": "Fenster - Anstrich"},
        "rahmen_anstrich": {"price": 20, "unit": "Stück", "description": "Rahmen - Türen & Fenster"},
        "trockenbau": {"price": 60, "unit": "m²", "description": "Trockenbau / Gipskarton"}
    },
    
    "umzug": {
        "1_zimmer": {"min": 450, "max": 550, "description": "1-Zimmer Wohnung Komplettumzug"},
        "2_zimmer": {"min": 650, "max": 750, "description": "2-Zimmer Wohnung Komplettumzug"},
        "3_zimmer": {"min": 850, "max": 1050, "description": "3-Zimmer Wohnung Komplettumzug"},
        "4_zimmer": {"min": 1100, "max": 1300, "description": "4-Zimmer Wohnung Komplettumzug"},
        "haus": {"min": 1500, "max": 3000, "description": "Haus / über 100 m² Komplettumzug"},
        "stundensatz_2": {"price": 100, "unit": "Stunde", "description": "1 Transporter + 2 Mitarbeiter"},
        "stundensatz_3": {"price": 125, "unit": "Stunde", "description": "1 Transporter + 3 Mitarbeiter"},
        "stundensatz_lkw": {"price": 140, "unit": "Stunde", "description": "1 LKW + 3 Mitarbeiter"},
        "zusaetzlich": {"price": 35, "unit": "Stunde", "description": "Zusätzlicher Mitarbeiter"},
        "km_zuschlag": {"price": 1.2, "unit": "km", "description": "Kilometer-Zuschlag außerhalb Berlin"},
        "material": {"price": 50, "unit": "Pauschale", "description": "Verpackungsmaterial Basis"}
    },
    
    "boden": {
        "laminat_schwimmend": {"price": 36.5, "unit": "m²", "description": "Laminat schwimmend verlegen"},
        "laminat_verklebt": {"price": 45, "unit": "m²", "description": "Laminat verklebt verlegen"},
        "pvc_schwimmend": {"price": 25, "unit": "m²", "description": "PVC schwimmend verlegen"},
        "pvc_verklebt": {"price": 30, "unit": "m²", "description": "PVC verklebt verlegen"},
        "sockelleisten": {"price": 7.5, "unit": "m", "description": "Sockelleisten montieren"},
        "entfernung_altbelag": {"price": 10, "unit": "m²", "description": "Entfernung Altbelag"},
        "material_boden": {"price": 0, "unit": "nach Absprache", "description": "Materialkosten Boden"}
    },
    
    "reinigung": {
        "umzugsreinigung": {"min": 4, "max": 6, "unit": "m²", "description": "Reinigung nach Umzug/Auszug"},
        "fensterreinigung": {"min": 2, "max": 5, "unit": "Fenster", "description": "Fensterreinigung"},
        "teppichreinigung": {"min": 20, "max": 40, "unit": "Stück", "description": "Teppichreinigung"},
        "backofenreinigung": {"price": 15, "unit": "Stück", "description": "Backofenreinigung"},
        "bueroreinigung": {"min": 20, "max": 40, "unit": "Stunde", "description": "Büroreinigung"},
        "material_reinigung": {"price": 0.5, "unit": "m²", "description": "Reinigungsmaterial"},
        "kueche_reinigung": {"price": 80, "unit": "Pauschale", "description": "Küchenreinigung intensiv"},
        "bad_reinigung": {"price": 60, "unit": "Pauschale", "description": "Badreinigung intensiv"}
    }
}

# 🌍 OPTIMIERTE MEHRSPRACHIGE NACHRICHTEN
MULTILINGUAL_RESPONSES = {
    'de': {
        'start': {
            'welcome': "🥰 <b>Willkommen bei SHAWO Umzüge!</b>",
            'hello': "👋 <b>Hallo {name}</b>, ich bin Leo, Ihr digitaler Assistent! 😊",
            'services': "<b>📦 Ich helfe Ihnen bei:</b>\n• Kompletten Umzügen\n• Möbelabbau & Aufbau\n• Renovierungsarbeiten\n• Bodenverlegung\n• Endreinigung",
            'features': "💰 <b>Sofortige Preis-Berechnungen</b>\n🌍 <b>Mehrsprachiger Service</b>\n🛡️ <b>Sichere Datenverarbeitung</b>\n📅 <b>Terminbuchung & Kalender</b>",
            'note': "<i>Unser Team kann diese Unterhaltung einsehen</i>",
            'question': "<b>Wie kann ich Ihnen helfen? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Kontakt SHAWO Umzüge</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Mo-Sa: 10:00-18:30 Uhr",
            'languages': "🗣️ Deutsch, Englisch, Arabisch",
            'privacy': "🛡️ <b>Datenschutzinformationen:</b>\n• https://shawo-umzug-app.de/datenschutz-de.html\n• https://shawo-umzug-app.de/privacy-policy-de.html"
        },
        'services': {
            'title': "🛠️ <b>Unsere Leistungen</b>",
            'moves': "🏠 <b>Umzüge:</b>\n• Komplette Umzüge\n• Möbel-Service\n• Deutschlandweit",
            'renovation': "🎨 <b>Renovierung:</b>\n• Malerarbeiten (Grundierung, Anstrich, Streichen)\n• Trockenbau\n• Tapezieren",
            'cleaning': "📦 <b>Boden & Reinigung:</b>\n• Laminat & PVC\n• Umzugsreinigung\n• Fensterreinigung",
            'guarantee': "✅ <b>Ohne versteckte Kosten!</b>"
        },
        'prices': {
            'title': "💰 <b>PREISBEISPIELE (unverbindlich)</b>",
            'example': "📋 <b>Beispiel: 2-Zimmer Umzug (60m²)</b>",
            'individual': "🎯 <b>Einzelpreise:</b>\n• Umzug 2-Zimmer: 650-750 €\n• Grundierung: 5 €/m²\n• Anstrich/Streichen: 12 €/m²\n• Reinigung: 4-6 €/m²\n• Boden Laminat: 36,50 €/m²",
            'note': "<i>Für persönliche Berechnung Details mitteilen!</i>"
        },
        'help': {
            'title': "⛑ <b>Hilfe</b>",
            'commands': "📋 <b>Befehle:</b>\n/start - Bot starten\n/contact - Kontakt\n/services - Leistungen\n/prices - Preise\n/help - Hilfe\n/calendar - Kalender anzeigen\n/book - Termin buchen",
            'direct': "💬 <b>Direkt:</b>\n• Preis-Anfragen\n• Terminanfragen\n• Beratung\n• Beschwerden",
            'features': "💰 <b>Preis-Schätzungen</b> verfügbar!\n🛡️ <b>Sichere Datenverarbeitung</b>\n📅 <b>Kalender-Funktion</b>"
        },
        'calendar': {
            'title': "📅 <b>Kalender & Terminbuchung</b>",
            'view': "🗓️ <b>Aktueller Monat:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Gebuchte Tage:</b> {booked_days}",
            'instructions': "📝 <b>Termin buchen:</b>\nVerwende /book DD.MM.YYYY oder teile mir deinen Wunschtermin mit!",
            'no_bookings': "✅ <b>Keine gebuchten Tage diesen Monat</b>"
        },
        'booking': {
            'success': "✅ <b>Termin erfolgreich gebucht!</b>\n\n📅 <b>Datum:</b> {date}\n👤 <b>Kunde:</b> {customer_name}\n📞 <b>Kontakt:</b> {contact_info}\n🛠️ <b>Service:</b> {service}",
            'already_booked': "❌ <b>Termin bereits vergeben!</b>\n\n📅 {date} ist bereits gebucht.\nBitte wählen Sie ein anderes Datum.",
            'invalid_date': "❌ <b>Ungültiges Datum!</b>\n\nBitte verwende das Format: DD.MM.YYYY\nBeispiel: /book 15.12.2024",
            'past_date': "❌ <b>Vergangenes Datum!</b>\n\nBitte wählen Sie ein zukünftiges Datum.",
            'instructions': "📅 <b>Terminbuchung</b>\n\nVerwende: /book DD.MM.YYYY\nBeispiel: /book 15.12.2024\n\nOder teile mir deinen Wunschtermin im Chat mit!"
        }
    },
    'en': {
        'start': {
            'welcome': "🥰 <b>Welcome to SHAWO Moves!</b>",
            'hello': "👋 <b>Hello {name}</b>, I am Leo, your digital assistant! 😊",
            'services': "<b>📦 I can help you with:</b>\n• Complete moves\n• Furniture assembly/disassembly\n• Renovation work\n• Floor installation\n• Final cleaning",
            'features': "💰 <b>Instant price calculations</b>\n🌍 <b>Multilingual service</b>\n🛡️ <b>Secure data processing</b>\n📅 <b>Appointment booking & Calendar</b>",
            'note': "<i>Our team can view this conversation</i>",
            'question': "<b>How can I help you? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Contact SHAWO Moves</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Mon-Sat: 10:00-18:30",
            'languages': "🗣️ German, English, Arabic",
            'privacy': "🛡️ <b>Privacy Information:</b>\n• https://shawo-umzug-app.de/datenschutz-en.html\n• https://shawo-umzug-app.de/privacy-policy-en.html"
        },
        'services': {
            'title': "🛠️ <b>Our Services</b>",
            'moves': "🏠 <b>Moves:</b>\n• Complete moves\n• Furniture service\n• Germany-wide",
            'renovation': "🎨 <b>Renovation:</b>\n• Painting work (Primer, Coating, Painting)\n• Drywall\n• Wallpapering",
            'cleaning': "📦 <b>Floor & Cleaning:</b>\n• Laminate & PVC\n• Move-out cleaning\n• Window cleaning",
            'guarantee': "✅ <b>No hidden costs!</b>"
        },
        'prices': {
            'title': "💰 <b>PRICE EXAMPLES (non-binding)</b>",
            'example': "📋 <b>Example: 2-room move (60m²)</b>",
            'individual': "🎯 <b>Individual prices:</b>\n• 2-room move: 650-750 €\n• Primer: 5 €/m²\n• Coating/Painting: 12 €/m²\n• Cleaning: 4-6 €/m²\n• Laminate floor: 36.50 €/m²",
            'note': "<i>For personal calculation please provide details!</i>"
        },
        'help': {
            'title': "⛑ <b>Help</b>",
            'commands': "📋 <b>Commands:</b>\n/start - Start bot\n/contact - Contact\n/services - Services\n/prices - Prices\n/help - Help\n/calendar - Show calendar\n/book - Book appointment",
            'direct': "💬 <b>Direct:</b>\n• Price inquiries\n• Appointment requests\n• Consultation\n• Complaints",
            'features': "💰 <b>Price estimates</b> available!\n🛡️ <b>Secure data processing</b>\n📅 <b>Calendar function</b>"
        },
        'calendar': {
            'title': "📅 <b>Calendar & Appointments</b>",
            'view': "🗓️ <b>Current Month:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Booked Days:</b> {booked_days}",
            'instructions': "📝 <b>Book appointment:</b>\nUse /book DD.MM.YYYY or tell me your preferred date!",
            'no_bookings': "✅ <b>No booked days this month</b>"
        },
        'booking': {
            'success': "✅ <b>Appointment successfully booked!</b>\n\n📅 <b>Date:</b> {date}\n👤 <b>Customer:</b> {customer_name}\n📞 <b>Contact:</b> {contact_info}\n🛠️ <b>Service:</b> {service}",
            'already_booked': "❌ <b>Date already booked!</b>\n\n📅 {date} is already taken.\nPlease choose another date.",
            'invalid_date': "❌ <b>Invalid date!</b>\n\nPlease use format: DD.MM.YYYY\nExample: /book 15.12.2024",
            'past_date': "❌ <b>Past date!</b>\n\nPlease choose a future date.",
            'instructions': "📅 <b>Appointment Booking</b>\n\nUse: /book DD.MM.YYYY\nExample: /book 15.12.2024\n\nOr tell me your preferred date in chat!"
        }
    },
    'ar': {
        'start': {
            'welcome': "🥰 <b>مرحباً بكم في SHAWO للتنقلات!</b>",
            'hello': "👋 <b>أهلاً {name}</b>، أنا ليو, مساعدك الرقمي! 😊",
            'services': "<b>📦 يمكنني مساعدتك في:</b>\n• التنقلات الكاملة\n• تركيب وتركيب الأثاث\n• أعمال التجديد\n• تركيب الأرضيات\n• التنظيف النهائي",
            'features': "💰 <b>حسابات الأسعار الفورية</b>\n🌍 <b>خدمة متعددة اللغات</b>\n🛡️ <b>معالجة بيانات آمنة</b>\n📅 <b>حجز المواعيد & التقويم</b>",
            'note': "<i>فريقنا يمكنه رؤية هذه المحادثة</i>",
            'question': "<b>كيف يمكنني مساعدتك؟ 😉</b>"
        },
        'contact': {
            'title': "📞 <b>اتصال SHAWO للتنقلات</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 واتساب: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 من الإثنين إلى السبت: 10:00-18:30",
            'languages': "🗣️ ألمانية، إنجليزية، عربية",
            'privacy': "🛡️ <b>معلومات الخصوصية:</b>\n• https://shawo-umzug-app.de/datenschutz-ar.html\n• https://shawo-umzug-app.de/privacy-policy-ar.html"
        },
        'services': {
            'title': "🛠️ <b>خدماتنا</b>",
            'moves': "🏠 <b>التنقلات:</b>\n• التنقلات الكاملة\n• خدمة الأثاث\n• في جميع أنحاء ألمانيا",
            'renovation': "🎨 <b>التجديد:</b>\n• أعمال الدهان (التحضير، الطلاء، الدهان)\n• البناء الجاف\n• تركيب ورق الجدران",
            'cleaning': "📦 <b>الأرضية والتنظيف:</b>\n• الأرضيات البلاستيكية والخشبية\n• تنظيف ما بعد الانتقال\n• تنظيف النوافذ",
            'guarantee': "✅ <b>بدون تكاليف خفية!</b>"
        },
        'prices': {
            'title': "💰 <b>أمثلة الأسعار (غير ملزمة)</b>",
            'example': "📋 <b>مثال: نقل شقة غرفتين (60م²)</b>",
            'individual': "🎯 <b>أسعار فردية:</b>\n• نقل شقة غرفتين: 750-650 يورو\n• التحضير: 5 يورو/م²\n• الطلاء/الدهان: 12 يورو/م²\n• التنظيف: 6-4 يورو/م²\n• أرضية خشبية: 36.50 يورو/م²",
            'note': "<i>للحساب الشخصي يرجى تقديم التفاصيل!</i>"
        },
        'help': {
            'title': "⛑ <b>مساعدة</b>",
            'commands': "📋 <b>الأوامر:</b>\n/start - بدء البوت\n/contact - اتصال\n/services - خدمات\n/prices - أسعار\n/help - مساعدة\n/calendar - عرض التقويم\n/book - حجز موعد",
            'direct': "💬 <b>مباشر:</b>\n• استفسارات الأسعار\n• طلبات المواعيد\n• استشارة\n• شكاوى",
            'features': "💰 <b>تقديرات الأسعار</b> متاحة!\n🛡️ <b>معالجة بيانات آمنة</b>\n📅 <b>وظيفة التقويم</b>"
        },
        'calendar': {
            'title': "📅 <b>التقويم & المواعيد</b>",
            'view': "🗓️ <b>الشهر الحالي:</b>\n{calendar_view}",
            'booked_days': "❌ <b>الأيام المحجوزة:</b> {booked_days}",
            'instructions': "📝 <b>حجز موعد:</b>\nاستخدم /book DD.MM.YYYY أو أخبرني بتاريخك المفضل!",
            'no_bookings': "✅ <b>لا توجد أيام محجوزة هذا الشهر</b>"
        },
        'booking': {
            'success': "✅ <b>تم حجز الموعد بنجاح!</b>\n\n📅 <b>التاريخ:</b> {date}\n👤 <b>الزبون:</b> {customer_name}\n📞 <b>الاتصال:</b> {contact_info}\n🛠️ <b>الخدمة:</b> {service}",
            'already_booked': "❌ <b>التاريخ محجوز مسبقاً!</b>\n\n📅 {date} محجوز بالفعل.\nيرجى اختيار تاريخ آخر.",
            'invalid_date': "❌ <b>تاريخ غير صالح!</b>\n\nيرجى استخدام الصيغة: DD.MM.YYYY\nمثال: /book 15.12.2024",
            'past_date': "❌ <b>تاريخ ماضي!</b>\n\nيرجى اختيار تاريخ مستقبلي.",
            'instructions': "📅 <b>حجز الموعد</b>\n\nاستخدم: /book DD.MM.YYYY\nمثال: /book 15.12.2024\n\nأو أخبرني بتاريخك المفضل في الدردشة!"
        }
    },
    'fr': {
        'start': {
            'welcome': "🥰 <b>Bienvenue chez SHAWO Déménagements!</b>",
            'hello': "👋 <b>Bonjour {name}</b>, je suis Léo, votre assistant numérique! 😊",
            'services': "<b>📦 Je peux vous aider avec:</b>\n• Déménagements complets\n• Assemblage/désassemblage de meubles\n• Travaux de rénovation\n• Pose de sols\n• Nettoyage final",
            'features': "💰 <b>Calculs de prix instantanés</b>\n🌍 <b>Service multilingue</b>\n🛡️ <b>Traitement sécurisé des données</b>\n📅 <b>Réservation de rendez-vous & Calendrier</b>",
            'note': "<i>Notre équipe peut voir cette conversation</i>",
            'question': "<b>Comment puis-je vous aider? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Contact SHAWO Déménagements</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Lun-Sam: 10:00-18:30",
            'languages': "🗣️ Allemand, Anglais, Arabe",
            'privacy': "🛡️ <b>Informations sur la confidentialité:</b>\n• https://shawo-umzug-app.fr/politique-confidentialite\n• https://shawo-umzug-app.fr/protection-donnees"
        },
        'services': {
            'title': "🛠️ <b>Nos Services</b>",
            'moves': "🏠 <b>Déménagements:</b>\n• Déménagements complets\n• Service meubles\n• Partout en Allemagne",
            'renovation': "🎨 <b>Rénovation:</b>\n• Travaux de peinture (Primaire, Revêtement, Peinture)\n• Plaques de plâtre\n• Pose de papier peint",
            'cleaning': "📦 <b>Sol & Nettoyage:</b>\n• Stratifié & PVC\n• Nettoyage après déménagement\n• Nettoyage de vitres",
            'guarantee': "✅ <b>Pas de coûts cachés!</b>"
        },
        'prices': {
            'title': "💰 <b>EXEMPLES DE PRIX (non engageants)</b>",
            'example': "📋 <b>Exemple: Déménagement 2 pièces (60m²)</b>",
            'individual': "🎯 <b>Prix individuels:</b>\n• Déménagement 2 pièces: 650-750 €\n• Primaire: 5 €/m²\n• Revêtement/Peinture: 12 €/m²\n• Nettoyage: 4-6 €/m²\n• Sol stratifié: 36,50 €/m²",
            'note': "<i>Pour un calcul personnalisé, veuillez fournir des détails!</i>"
        },
        'help': {
            'title': "⛑ <b>Aide</b>",
            'commands': "📋 <b>Commandes:</b>\n/start - Démarrer le bot\n/contact - Contact\n/services - Services\n/prices - Prix\n/help - Aide\n/calendar - Afficher le calendrier\n/book - Réserver un rendez-vous",
            'direct': "💬 <b>Direct:</b>\n• Demandes de prix\n• Demandes de rendez-vous\n• Consultation\n• Réclamations",
            'features': "💰 <b>Estimations de prix</b> disponibles!\n🛡️ <b>Traitement sécurisé des données</b>\n📅 <b>Fonction calendrier</b>"
        },
        'calendar': {
            'title': "📅 <b>Calendrier & Rendez-vous</b>",
            'view': "🗓️ <b>Mois en cours:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Jours réservés:</b> {booked_days}",
            'instructions': "📝 <b>Réserver un rendez-vous:</b>\nUtilisez /book DD.MM.YYYY ou dites-moi votre date préférée!",
            'no_bookings': "✅ <b>Aucun jour réservé ce mois-ci</b>"
        },
        'booking': {
            'success': "✅ <b>Rendez-vous réservé avec succès!</b>\n\n📅 <b>Date:</b> {date}\n👤 <b>Client:</b> {customer_name}\n📞 <b>Contact:</b> {contact_info}\n🛠️ <b>Service:</b> {service}",
            'already_booked': "❌ <b>Date déjà réservée!</b>\n\n📅 {date} est déjà prise.\nVeuillez choisir une autre date.",
            'invalid_date': "❌ <b>Date invalide!</b>\n\nVeuillez utiliser le format: DD.MM.YYYY\nExemple: /book 15.12.2024",
            'past_date': "❌ <b>Date passée!</b>\n\nVeuillez choisir une date future.",
            'instructions': "📅 <b>Réservation de rendez-vous</b>\n\nUtilisez: /book DD.MM.YYYY\nExemple: /book 15.12.2024\n\nOu dites-moi votre date préférée dans le chat!"
        }
    },
    'es': {
        'start': {
            'welcome': "🥰 <b>¡Bienvenido a SHAWO Mudanzas!</b>",
            'hello': "👋 <b>Hola {name}</b>, soy Leo, ¡tu asistente digital! 😊",
            'services': "<b>📦 Puedo ayudarte con:</b>\n• Mudanzas completas\n• Montaje/desmontaje de muebles\n• Trabajos de renovación\n• Instalación de suelos\n• Limpieza final",
            'features': "💰 <b>Cálculos de precios instantáneos</b>\n🌍 <b>Servicio multilingüe</b>\n🛡️ <b>Procesamiento seguro de datos</b>\n📅 <b>Reserva de citas & Calendario</b>",
            'note': "<i>Nuestro equipo puede ver esta conversación</i>",
            'question': "<b>¿Cómo puedo ayudarte? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Contacto SHAWO Mudanzas</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Lun-Sáb: 10:00-18:30",
            'languages': "🗣️ Alemán, Inglés, Árabe",
            'privacy': "🛡️ <b>Información de privacidad:</b>\n• https://shawo-umzug-app.es/politica-privacidad\n• https://shawo-umzug-app.es/proteccion-datos"
        },
        'services': {
            'title': "🛠️ <b>Nuestros Servicios</b>",
            'moves': "🏠 <b>Mudanzas:</b>\n• Mudanzas completas\n• Servicio de muebles\n• Toda Alemania",
            'renovation': "🎨 <b>Renovación:</b>\n• Trabajos de pintura (Imprimación, Revestimiento, Pintura)\n• Pladur\n• Empapelado",
            'cleaning': "📦 <b>Suelo & Limpieza:</b>\n• Laminado & PVC\n• Limpieza post-mudanza\n• Limpieza de ventanas",
            'guarantee': "✅ <b>¡Sin costes ocultos!</b>"
        },
        'prices': {
            'title': "💰 <b>EJEMPLOS DE PRECIOS (no vinculantes)</b>",
            'example': "📋 <b>Ejemplo: Mudanza 2 habitaciones (60m²)</b>",
            'individual': "🎯 <b>Precios individuales:</b>\n• Mudanza 2 habitaciones: 650-750 €\n• Imprimación: 5 €/m²\n• Revestimiento/Pintura: 12 €/m²\n• Limpieza: 4-6 €/m²\n• Suelo laminado: 36,50 €/m²",
            'note': "<i>¡Para cálculo personalizado proporcione detalles!</i>"
        },
        'help': {
            'title': "⛑ <b>Ayuda</b>",
            'commands': "📋 <b>Comandos:</b>\n/start - Iniciar bot\n/contact - Contacto\n/services - Servicios\n/prices - Precios\n/help - Ayuda\n/calendar - Mostrar calendario\n/book - Reservar cita",
            'direct': "💬 <b>Directo:</b>\n• Consultas de precios\n• Solicitudes de cita\n• Consultoría\n• Quejas",
            'features': "💰 <b>¡Estimaciones de precio</b> disponibles!\n🛡️ <b>Procesamiento seguro de datos</b>\n📅 <b>Función calendario</b>"
        },
        'calendar': {
            'title': "📅 <b>Calendario & Citas</b>",
            'view': "🗓️ <b>Mes actual:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Días reservados:</b> {booked_days}",
            'instructions': "📝 <b>Reservar cita:</b>\n¡Usa /book DD.MM.YYYY o dime tu fecha preferida!",
            'no_bookings': "✅ <b>No hay días reservados este mes</b>"
        },
        'booking': {
            'success': "✅ <b>¡Cita reservada con éxito!</b>\n\n📅 <b>Fecha:</b> {date}\n👤 <b>Cliente:</b> {customer_name}\n📞 <b>Contacto:</b> {contact_info}\n🛠️ <b>Servicio:</b> {service}",
            'already_booked': "❌ <b>¡Fecha ya reservada!</b>\n\n📅 {date} ya está ocupada.\nPor favor elija otra fecha.",
            'invalid_date': "❌ <b>¡Fecha inválida!</b>\n\nPor favor use el formato: DD.MM.YYYY\nEjemplo: /book 15.12.2024",
            'past_date': "❌ <b>¡Fecha pasada!</b>\n\nPor favor elija una fecha futura.",
            'instructions': "📅 <b>Reserva de Cita</b>\n\nUse: /book DD.MM.YYYY\nEjemplo: /book 15.12.2024\n\n¡O dígame su fecha preferida en el chat!"
        }
    },
    'it': {
        'start': {
            'welcome': "🥰 <b>Benvenuto da SHAWO Traslochi!</b>",
            'hello': "👋 <b>Ciao {name}</b>, sono Leo, il tuo assistente digitale! 😊",
            'services': "<b>📦 Posso aiutarti con:</b>\n• Traslochi completi\n• Montaggio/smontaggio mobili\n• Lavori di ristrutturazione\n• Posa pavimenti\n• Pulizia finale",
            'features': "💰 <b>Calcoli prezzi istantanei</b>\n🌍 <b>Servizio multilingue</b>\n🛡️ <b>Elaborazione dati sicura</b>\n📅 <b>Prenotazione appuntamenti & Calendario</b>",
            'note': "<i>Il nostro team può vedere questa conversazione</i>",
            'question': "<b>Come posso aiutarti? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Contatto SHAWO Traslochi</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Lun-Sab: 10:00-18:30",
            'languages': "🗣️ Tedesco, Inglese, Arabo",
            'privacy': "🛡️ <b>Informazioni sulla privacy:</b>\n• https://shawo-umzug-app.it/privacy\n• https://shawo-umzug-app.it/protezione-dati"
        },
        'services': {
            'title': "🛠️ <b>I Nostri Servizi</b>",
            'moves': "🏠 <b>Traslochi:</b>\n• Traslochi completi\n• Servizio mobili\n• Tutta la Germania",
            'renovation': "🎨 <b>Ristrutturazione:</b>\n• Lavori di pittura (Primer, Rivestimento, Pittura)\n• Cartongesso\n• Tappezzeria",
            'cleaning': "📦 <b>Pavimento & Pulizia:</b>\n• Laminato & PVC\n• Pulizia post-trasloco\n• Pulizia finestre",
            'guarantee': "✅ <b>Nessun costo nascosto!</b>"
        },
        'prices': {
            'title': "💰 <b>ESEMPI PREZZI (non vincolanti)</b>",
            'example': "📋 <b>Esempio: Trasloco 2 locali (60m²)</b>",
            'individual': "🎯 <b>Prezzi individuali:</b>\n• Trasloco 2 locali: 650-750 €\n• Primer: 5 €/m²\n• Rivestimento/Pittura: 12 €/m²\n• Pulizia: 4-6 €/m²\n• Pavimento laminato: 36,50 €/m²",
            'note': "<i>Per calcolo personalizzato fornire dettagli!</i>"
        },
        'help': {
            'title': "⛑ <b>Aiuto</b>",
            'commands': "📋 <b>Comandi:</b>\n/start - Avvia bot\n/contact - Contatto\n/services - Servizi\n/prices - Prezzi\n/help - Aiuto\n/calendar - Mostra calendario\n/book - Prenota appuntamento",
            'direct': "💬 <b>Diretto:</b>\n• Richieste prezzi\n• Richieste appuntamenti\n• Consulenza\n• Reclami",
            'features': "💰 <b>Preventivi prezzi</b> disponibili!\n🛡️ <b>Elaborazione dati sicura</b>\n📅 <b>Funzione calendario</b>"
        },
        'calendar': {
            'title': "📅 <b>Calendario & Appuntamenti</b>",
            'view': "🗓️ <b>Mese corrente:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Giorni prenotati:</b> {booked_days}",
            'instructions': "📝 <b>Prenota appuntamento:</b>\nUsa /book DD.MM.YYYY o dimmi la tua data preferita!",
            'no_bookings': "✅ <b>Nessun giorno prenotato questo mese</b>"
        },
        'booking': {
            'success': "✅ <b>Appuntamento prenotato con successo!</b>\n\n📅 <b>Data:</b> {date}\n👤 <b>Cliente:</b> {customer_name}\n📞 <b>Contatto:</b> {contact_info}\n🛠️ <b>Servizio:</b> {service}",
            'already_booked': "❌ <b>Data già prenotata!</b>\n\n📅 {date} è già occupata.\nPer favore scegli un'altra data.",
            'invalid_date': "❌ <b>Data non valida!</b>\n\nPer favore usa il formato: DD.MM.YYYY\nEsempio: /book 15.12.2024",
            'past_date': "❌ <b>Data passata!</b>\n\nPer favore scegli una data futura.",
            'instructions': "📅 <b>Prenotazione Appuntamento</b>\n\nUsa: /book DD.MM.YYYY\nEsempio: /book 15.12.2024\n\nO dimmi la tua data preferita nella chat!"
        }
    },
    'tr': {
        'start': {
            'welcome': "🥰 <b>SHAWO Taşınma'ya Hoş Geldiniz!</b>",
            'hello': "👋 <b>Merhaba {name}</b>, ben Leo, dijital asistanınız! 😊",
            'services': "<b>📦 Size şu konularda yardımcı olabilirim:</b>\n• Komplet taşınmalar\n• Mobilya montaj/demontaj\n• Yenileme işleri\n• Zemin döşeme\n• Final temizlik",
            'features': "💰 <b>Anında fiyat hesaplamaları</b>\n🌍 <b>Çok dilli hizmet</b>\n🛡️ <b>Güvenli veri işleme</b>\n📅 <b>Randevu rezervasyonu & Takvim</b>",
            'note': "<i>Ekibimiz bu konuşmayı görebilir</i>",
            'question': "<b>Size nasıl yardımcı olabilirim? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>İletişim SHAWO Taşınma</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Pzt-Cum: 10:00-18:30",
            'languages': "🗣️ Almanca, İngilizce, Arapça",
            'privacy': "🛡️ <b>Gizlilik Bilgileri:</b>\n• https://shawo-umzug-app.tr/gizlilik\n• https://shawo-umzug-app.tr/veri-koruma"
        },
        'services': {
            'title': "🛠️ <b>Hizmetlerimiz</b>",
            'moves': "🏠 <b>Taşınmalar:</b>\n• Komplet taşınmalar\n• Mobilya servisi\n• Tüm Almanya",
            'renovation': "🎨 <b>Yenileme:</b>\n• Boya işleri (Astarlama, Kaplama, Boyama)\n• Alçıpan\n• Duvar kağıdı",
            'cleaning': "📦 <b>Zemin & Temizlik:</b>\n• Laminat & PVC\n• Taşınma temizliği\n• Cam temizliği",
            'guarantee': "✅ <b>Gizli maliyet yok!</b>"
        },
        'prices': {
            'title': "💰 <b>FİYAT ÖRNEKLERİ (bağlayıcı değildir)</b>",
            'example': "📋 <b>Örnek: 2 odalı taşınma (60m²)</b>",
            'individual': "🎯 <b>Bireysel fiyatlar:</b>\n• 2 odalı taşınma: 650-750 €\n• Astar: 5 €/m²\n• Kaplama/Boya: 12 €/m²\n• Temizlik: 4-6 €/m²\n• Laminat zemin: 36,50 €/m²",
            'note': "<i>Kişisel hesaplama için detayları belirtin!</i>"
        },
        'help': {
            'title': "⛑ <b>Yardım</b>",
            'commands': "📋 <b>Komutlar:</b>\n/start - Botu başlat\n/contact - İletişim\n/services - Hizmetler\n/prices - Fiyatlar\n/help - Yardım\n/calendar - Takvimi göster\n/book - Randevu al",
            'direct': "💬 <b>Doğrudan:</b>\n• Fiyat sorgulamaları\n• Randevu talepleri\n• Danışmanlık\n• Şikayetler",
            'features': "💰 <b>Fiyat tahminleri</b> mevcut!\n🛡️ <b>Güvenli veri işleme</b>\n📅 <b>Takvim fonksiyonu</b>"
        },
        'calendar': {
            'title': "📅 <b>Takvim & Randevular</b>",
            'view': "🗓️ <b>Mevcut Ay:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Rezerve Günler:</b> {booked_days}",
            'instructions': "📝 <b>Randevu al:</b>\n/book DD.MM.YYYY kullan veya tercih ettiğin tarihi söyle!",
            'no_bookings': "✅ <b>Bu ay rezerve gün yok</b>"
        },
        'booking': {
            'success': "✅ <b>Randevu başarıyla alındı!</b>\n\n📅 <b>Tarih:</b> {date}\n👤 <b>Müşteri:</b> {customer_name}\n📞 <b>İletişim:</b> {contact_info}\n🛠️ <b>Hizmet:</b> {service}",
            'already_booked': "❌ <b>Tarih zaten rezerve!</b>\n\n📅 {date} zaten dolu.\nLütfen başka tarih seçin.",
            'invalid_date': "❌ <b>Geçersiz tarih!</b>\n\nLütfen formatı kullanın: DD.MM.YYYY\nÖrnek: /book 15.12.2024",
            'past_date': "❌ <b>Geçmiş tarih!</b>\n\nLütfen gelecek tarih seçin.",
            'instructions': "📅 <b>Randevu Alma</b>\n\nKullan: /book DD.MM.YYYY\nÖrnek: /book 15.12.2024\n\nVeya sohbette tercih ettiğin tarihi söyle!"
        }
    },
    'ru': {
        'start': {
            'welcome': "🥰 <b>Добро пожаловать в SHAWO Переезды!</b>",
            'hello': "👋 <b>Здравствуйте {name}</b>, я Лео, ваш цифровой помощник! 😊",
            'services': "<b>📦 Я могу помочь вам с:</b>\n• Полными переездами\n• Сборкой/разборкой мебели\n• Ремонтными работами\n• Укладкой полов\n• Финальной уборкой",
            'features': "💰 <b>Мгновенные расчеты цен</b>\n🌍 <b>Многоязычный сервис</b>\n🛡️ <b>Безопасная обработка данных</b>\n📅 <b>Бронирование встреч & Календарь</b>",
            'note': "<i>Наша команда может видеть этот разговор</i>",
            'question': "<b>Как я могу вам помочь? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Контакты SHAWO Переезды</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Пн-Сб: 10:00-18:30",
            'languages': "🗣️ Немецкий, Английский, Арабский",
            'privacy': "🛡️ <b>Информация о конфиденциальности:</b>\n• https://shawo-umzug-app.ru/конфиденциальность\n• https://shawo-umzug-app.ru/защита-данных"
        },
        'services': {
            'title': "🛠️ <b>Наши Услуги</b>",
            'moves': "🏠 <b>Переезды:</b>\n• Полные переезды\n• Мебельный сервис\n• По всей Германии",
            'renovation': "🎨 <b>Ремонт:</b>\n• Малярные работы (Грунтовка, Покрытие, Покраска)\n• Гипсокартон\n• Обои",
            'cleaning': "📦 <b>Пол & Уборка:</b>\n• Ламинат & ПВХ\n• Уборка после переезда\n• Мойка окон",
            'guarantee': "✅ <b>Без скрытых затрат!</b>"
        },
        'prices': {
            'title': "💰 <b>ПРИМЕРЫ ЦЕН (необязательные)</b>",
            'example': "📋 <b>Пример: Переезд 2-комнатной (60м²)</b>",
            'individual': "🎯 <b>Индивидуальные цены:</b>\n• Переезд 2-комнатной: 650-750 €\n• Грунтовка: 5 €/м²\n• Покрытие/Покраска: 12 €/м²\n• Уборка: 4-6 €/м²\n• Ламинат: 36,50 €/м²",
            'note': "<i>Для персонального расчета укажите детали!</i>"
        },
        'help': {
            'title': "⛑ <b>Помощь</b>",
            'commands': "📋 <b>Команды:</b>\n/start - Запустить бота\n/contact - Контакты\n/services - Услуги\n/prices - Цены\n/help - Помощь\n/calendar - Показать календарь\n/book - Забронировать встречу",
            'direct': "💬 <b>Прямо:</b>\n• Запросы цен\n• Запросы встреч\n• Консультация\n• Жалобы",
            'features': "💰 <b>Оценки цен</b> доступны!\n🛡️ <b>Безопасная обработка данных</b>\n📅 <b>Функция календаря</b>"
        },
        'calendar': {
            'title': "📅 <b>Календарь & Встречи</b>",
            'view': "🗓️ <b>Текущий месяц:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Забронированные дни:</b> {booked_days}",
            'instructions': "📝 <b>Забронировать встречу:</b>\nИспользуйте /book ДД.ММ.ГГГГ или скажите мне предпочтительную дату!",
            'no_bookings': "✅ <b>Нет забронированных дней в этом месяце</b>"
        },
        'booking': {
            'success': "✅ <b>Встреча успешно забронирована!</b>\n\n📅 <b>Дата:</b> {date}\n👤 <b>Клиент:</b> {customer_name}\n📞 <b>Контакт:</b> {contact_info}\n🛠️ <b>Услуга:</b> {service}",
            'already_booked': "❌ <b>Дата уже занята!</b>\n\n📅 {date} уже забронирована.\nПожалуйста, выберите другую дату.",
            'invalid_date': "❌ <b>Неверная дата!</b>\n\nПожалуйста, используйте формат: ДД.ММ.ГГГГ\nПример: /book 15.12.2024",
            'past_date': "❌ <b>Прошедшая дата!</b>\n\nПожалуйста, выберите будущую дату.",
            'instructions': "📅 <b>Бронирование Встречи</b>\n\nИспользуйте: /book ДД.ММ.ГГГГ\nПример: /book 15.12.2024\n\nИли скажите мне предпочтительную дату в чате!"
        }
    },
    'pl': {
        'start': {
            'welcome': "🥰 <b>Witamy w SHAWO Przeprowadzki!</b>",
            'hello': "👋 <b>Cześć {name}</b>, jestem Leo, Twój asystent cyfrowy! 😊",
            'services': "<b>📦 Mogę Ci pomóc z:</b>\n• Kompleksowymi przeprowadzkami\n• Montażem/demontażem mebli\n• Pracami remontowymi\n• Układaniem podłóg\n• Sprzątaniem końcowym",
            'features': "💰 <b>Natychmiastowe wyceny</b>\n🌍 <b>Wielojęzyczna obsługa</b>\n🛡️ <b>Bezpieczne przetwarzanie danych</b>\n📅 <b>Rezerwacja terminów & Kalendarz</b>",
            'note': "<i>Nasz zespół może widzieć tę rozmowę</i>",
            'question': "<b>Jak mogę Ci pomóc? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Kontakt SHAWO Przeprowadzki</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Pn-Sob: 10:00-18:30",
            'languages': "🗣️ Niemiecki, Angielski, Arabski",
            'privacy': "🛡️ <b>Informacje o prywatności:</b>\n• https://shawo-umzug-app.pl/prywatnosc\n• https://shawo-umzug-app.pl/ochrona-danych"
        },
        'services': {
            'title': "🛠️ <b>Nasze Usługi</b>",
            'moves': "🏠 <b>Przeprowadzki:</b>\n• Kompleksowe przeprowadzki\n• Serwis meblowy\n• Całe Niemcy",
            'renovation': "🎨 <b>Remont:</b>\n• Prace malarskie (Gruntowanie, Powłoka, Malowanie)\n• Płyty karton-gips\n• Tapetowanie",
            'cleaning': "📦 <b>Podłoga & Sprzątanie:</b>\n• Laminat & PVC\n• Sprzątanie po przeprowadzce\n• Mycie okien",
            'guarantee': "✅ <b>Bez ukrytych kosztów!</b>"
        },
        'prices': {
            'title': "💰 <b>PRZYKŁADY CEN (niezobowiązujące)</b>",
            'example': "📋 <b>Przykład: Przeprowadzka 2-pokojowa (60m²)</b>",
            'individual': "🎯 <b>Ceny indywidualne:</b>\n• Przeprowadzka 2-pokojowa: 650-750 €\n• Gruntowanie: 5 €/m²\n• Powłoka/Malowanie: 12 €/m²\n• Sprzątanie: 4-6 €/m²\n• Podłoga laminowana: 36,50 €/m²",
            'note': "<i>Do wyceny osobistej podaj szczegóły!</i>"
        },
        'help': {
            'title': "⛑ <b>Pomoc</b>",
            'commands': "📋 <b>Komendy:</b>\n/start - Uruchom bota\n/contact - Kontakt\n/services - Usługi\n/prices - Ceny\n/help - Pomoc\n/calendar - Pokaż kalendarz\n/book - Zarezerwuj termin",
            'direct': "💬 <b>Bezpośrednio:</b>\n• Zapytania o ceny\n• Prośby o terminy\n• Konsultacje\n• Reklamacje",
            'features': "💰 <b>Wycenę cen</b> dostępna!\n🛡️ <b>Bezpieczne przetwarzanie danych</b>\n📅 <b>Funkcja kalendarza</b>"
        },
        'calendar': {
            'title': "📅 <b>Kalendarz & Terminy</b>",
            'view': "🗓️ <b>Bieżący miesiąc:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Zarezerwowane dni:</b> {booked_days}",
            'instructions': "📝 <b>Zarezerwuj termin:</b>\nUżyj /book DD.MM.YYYY lub powiedz mi preferowany termin!",
            'no_bookings': "✅ <b>Brak zarezerwowanych dni w tym miesiącu</b>"
        },
        'booking': {
            'success': "✅ <b>Termin zarezerwowany pomyślnie!</b>\n\n📅 <b>Data:</b> {date}\n👤 <b>Klient:</b> {customer_name}\n📞 <b>Kontakt:</b> {contact_info}\n🛠️ <b>Usługa:</b> {service}",
            'already_booked': "❌ <b>Data już zarezerwowana!</b>\n\n📅 {date} jest już zajęta.\nProszę wybrać inną datę.",
            'invalid_date': "❌ <b>Nieprawidłowa data!</b>\n\nProszę użyć formatu: DD.MM.YYYY\nPrzykład: /book 15.12.2024",
            'past_date': "❌ <b>Data z przeszłości!</b>\n\nProszę wybrać przyszłą datę.",
            'instructions': "📅 <b>Rezerwacja Terminu</b>\n\nUżyj: /book DD.MM.YYYY\nPrzykład: /book 15.12.2024\n\nLub powiedz mi preferowany termin na czacie!"
        }
    },
    'uk': {
        'start': {
            'welcome': "🥰 <b>Ласкаво просимо до SHAWO Переїздів!</b>",
            'hello': "👋 <b>Вітаю {name}</b>, я Лео, ваш цифровий помічник! 😊",
            'services': "<b>📦 Я можу допомогти вам з:</b>\n• Повними переїздами\n• Збіркою/розбіркою меблів\n• Ремонтними роботами\n• Укладанням підлоги\n• Фінальним прибиранням",
            'features': "💰 <b>Миттєві розрахунки цін</b>\n🌍 <b>Багатомовний сервіс</b>\n🛡️ <b>Безпечна обробка даних</b>\n📅 <b>Бронювання зустрічей & Календар</b>",
            'note': "<i>Наша команда може бачити цю розмову</i>",
            'question': "<b>Як я можу вам допомогти? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Контакти SHAWO Переїзди</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Пн-Сб: 10:00-18:30",
            'languages': "🗣️ Німецька, Англійська, Арабська",
            'privacy': "🛡️ <b>Інформація про конфіденційність:</b>\n• https://shawo-umzug-app.ua/конфіденційність\n• https://shawo-umzug-app.ua/захист-даних"
        },
        'services': {
            'title': "🛠️ <b>Наші Послуги</b>",
            'moves': "🏠 <b>Переїзди:</b>\n• Повні переїзди\n• Меблевий сервіс\n• По всій Німеччині",
            'renovation': "🎨 <b>Ремонт:</b>\n• Малярні роботи (Ґрунтовка, Покриття, Фарбування)\n• Гіпсокартон\n• Шпалери",
            'cleaning': "📦 <b>Підлога & Прибирання:</b>\n• Ламінат & ПВХ\n• Прибирання після переїзду\n• Миття вікон",
            'guarantee': "✅ <b>Без прихованих витрат!</b>"
        },
        'prices': {
            'title': "💰 <b>ПРИКЛАДИ ЦІН (незобов'язуючі)</b>",
            'example': "📋 <b>Приклад: Переїзд 2-кімнатної (60м²)</b>",
            'individual': "🎯 <b>Індивідуальні ціни:</b>\n• Переїзд 2-кімнатної: 650-750 €\n• Ґрунтовка: 5 €/м²\n• Покриття/Фарбування: 12 €/м²\n• Прибирання: 4-6 €/м²\n• Ламінат: 36,50 €/м²",
            'note': "<i>Для персонального розрахунку вкажіть деталі!</i>"
        },
        'help': {
            'title': "⛑ <b>Допомога</b>",
            'commands': "📋 <b>Команди:</b>\n/start - Запустити бота\n/contact - Контакти\n/services - Послуги\n/prices - Ціни\n/help - Допомога\n/calendar - Показати календар\n/book - Забронювати зустріч",
            'direct': "💬 <b>Безпосередньо:</b>\n• Запити цін\n• Запити зустрічей\n• Консультація\n• Скарги",
            'features': "💰 <b>Оцінки цін</b> доступні!\n🛡️ <b>Безпечна обробка даних</b>\n📅 <b>Функція календаря</b>"
        },
        'calendar': {
            'title': "📅 <b>Календар & Зустрічі</b>",
            'view': "🗓️ <b>Поточний місяць:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Заброньовані дні:</b> {booked_days}",
            'instructions': "📝 <b>Забронювати зустріч:</b>\nВикористовуйте /book ДД.ММ.РРРР або скажіть мені бажану дату!",
            'no_bookings': "✅ <b>Немає заброньованих днів цього місяця</b>"
        },
        'booking': {
            'success': "✅ <b>Зустріч успішно заброньована!</b>\n\n📅 <b>Дата:</b> {date}\n👤 <b>Клієнт:</b> {customer_name}\n📞 <b>Контакт:</b> {contact_info}\n🛠️ <b>Послуга:</b> {service}",
            'already_booked': "❌ <b>Дата вже зайнята!</b>\n\n📅 {date} вже заброньована.\nБудь ласка, виберіть іншу дату.",
            'invalid_date': "❌ <b>Невірна дата!</b>\n\nБудь ласка, використовуйте формат: ДД.ММ.РРРР\nПриклад: /book 15.12.2024",
            'past_date': "❌ <b>Минула дата!</b>\n\nБудь ласка, виберіть майбутню дату.",
            'instructions': "📅 <b>Бронювання Зустрічі</b>\n\nВикористовуйте: /book ДД.ММ.РРРР\nПриклад: /book 15.12.2024\n\nАбо скажіть мені бажану дату в чаті!"
        }
    },
    'zh': {
        'start': {
            'welcome': "🥰 <b>欢迎来到 SHAWO 搬家服务!</b>",
            'hello': "👋 <b>你好 {name}</b>, 我是 Leo, 您的数字助理! 😊",
            'services': "<b>📦 我可以帮助您:</b>\n• 完整搬家服务\n• 家具组装/拆卸\n• 装修工作\n• 地板安装\n• 最终清洁",
            'features': "💰 <b>即时价格计算</b>\n🌍 <b>多语言服务</b>\n🛡️ <b>安全数据处理</b>\n📅 <b>预约预订 & 日历</b>",
            'note': "<i>我们的团队可以查看此对话</i>",
            'question': "<b>我如何帮助您？😉</b>"
        },
        'contact': {
            'title': "📞 <b>联系 SHAWO 搬家</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 周一至周六: 10:00-18:30",
            'languages': "🗣️ 德语, 英语, 阿拉伯语",
            'privacy': "🛡️ <b>隐私信息:</b>\n• https://shawo-umzug-app.cn/隐私政策\n• https://shawo-umzug-app.cn/数据保护"
        },
        'services': {
            'title': "🛠️ <b>我们的服务</b>",
            'moves': "🏠 <b>搬家:</b>\n• 完整搬家服务\n• 家具服务\n• 全德国范围",
            'renovation': "🎨 <b>装修:</b>\n• 油漆工作 (底漆, 涂层, 油漆)\n• 干墙\n• 贴壁纸",
            'cleaning': "📦 <b>地板 & 清洁:</b>\n• 层压板 & PVC\n• 搬家后清洁\n• 窗户清洁",
            'guarantee': "✅ <b>无隐藏费用!</b>"
        },
        'prices': {
            'title': "💰 <b>价格示例 (非约束性)</b>",
            'example': "📋 <b>示例: 2室搬家 (60平方米)</b>",
            'individual': "🎯 <b>个别价格:</b>\n• 2室搬家: 650-750 €\n• 底漆: 5 €/平方米\n• 涂层/油漆: 12 €/平方米\n• 清洁: 4-6 €/平方米\n• 层压地板: 36,50 €/平方米",
            'note': "<i>个人计算请提供详细信息!</i>"
        },
        'help': {
            'title': "⛑ <b>帮助</b>",
            'commands': "📋 <b>命令:</b>\n/start - 启动机器人\n/contact - 联系\n/services - 服务\n/prices - 价格\n/help - 帮助\n/calendar - 显示日历\n/book - 预订预约",
            'direct': "💬 <b>直接:</b>\n• 价格查询\n• 预约请求\n• 咨询\n• 投诉",
            'features': "💰 <b>价格估算</b> 可用!\n🛡️ <b>安全数据处理</b>\n📅 <b>日历功能</b>"
        },
        'calendar': {
            'title': "📅 <b>日历 & 预约</b>",
            'view': "🗓️ <b>当前月份:</b>\n{calendar_view}",
            'booked_days': "❌ <b>已预订日期:</b> {booked_days}",
            'instructions': "📝 <b>预订预约:</b>\n使用 /book DD.MM.YYYY 或告诉我您偏好的日期!",
            'no_bookings': "✅ <b>本月无预订日期</b>"
        },
        'booking': {
            'success': "✅ <b>预约成功预订!</b>\n\n📅 <b>日期:</b> {date}\n👤 <b>客户:</b> {customer_name}\n📞 <b>联系:</b> {contact_info}\n🛠️ <b>服务:</b> {service}",
            'already_booked': "❌ <b>日期已被预订!</b>\n\n📅 {date} 已被占用.\n请选择其他日期.",
            'invalid_date': "❌ <b>无效日期!</b>\n\n请使用格式: DD.MM.YYYY\n示例: /book 15.12.2024",
            'past_date': "❌ <b>过去日期!</b>\n\n请选择未来日期.",
            'instructions': "📅 <b>预约预订</b>\n\n使用: /book DD.MM.YYYY\n示例: /book 15.12.2024\n\n或在聊天中告诉我您偏好的日期!"
        }
    },
    'ja': {
        'start': {
            'welcome': "🥰 <b>SHAWO引越しサービスへようこそ!</b>",
            'hello': "👋 <b>こんにちは {name}さん</b>, 私はレオ, あなたのデジタルアシスタントです! 😊",
            'services': "<b>📦 以下のお手伝いができます:</b>\n• 完全な引越し\n• 家具の組み立て/分解\n• リフォーム作業\n• 床設置\n• 最終清掃",
            'features': "💰 <b>即時価格計算</b>\n🌍 <b>多言語サービス</b>\n🛡️ <b>安全なデータ処理</b>\n📅 <b>予約 & カレンダー</b>",
            'note': "<i>当社チームはこの会話を閲覧できます</i>",
            'question': "<b>どのようにお手伝いしましょうか？😉</b>"
        },
        'contact': {
            'title': "📞 <b>連絡先 SHAWO 引越し</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 月-土: 10:00-18:30",
            'languages': "🗣️ ドイツ語, 英語, アラビア語",
            'privacy': "🛡️ <b>プライバシー情報:</b>\n• https://shawo-umzug-app.jp/プライバシー\n• https://shawo-umzug-app.jp/データ保護"
        },
        'services': {
            'title': "🛠️ <b>当社のサービス</b>",
            'moves': "🏠 <b>引越し:</b>\n• 完全な引越し\n• 家具サービス\n• ドイツ全土",
            'renovation': "🎨 <b>リフォーム:</b>\n• 塗装作業 (下塗り, 塗装, 仕上げ)\n• 石膏ボード\n• 壁紙貼り",
            'cleaning': "📦 <b>床 & 清掃:</b>\n• ラミネート & PVC\n• 引越し後の清掃\n• 窓掃除",
            'guarantee': "✅ <b>隠れた費用なし!</b>"
        },
        'prices': {
            'title': "💰 <b>価格例 (非拘束的)</b>",
            'example': "📋 <b>例: 2部屋の引越し (60m²)</b>",
            'individual': "🎯 <b>個別価格:</b>\n• 2部屋の引越し: 650-750 €\n• 下塗り: 5 €/m²\n• 塗装/仕上げ: 12 €/m²\n• 清掃: 4-6 €/m²\n• ラミネート床: 36,50 €/m²",
            'note': "<i>個人計算の場合は詳細を提供してください!</i>"
        },
        'help': {
            'title': "⛑ <b>ヘルプ</b>",
            'commands': "📋 <b>コマンド:</b>\n/start - ボット開始\n/contact - 連絡先\n/services - サービス\n/prices - 価格\n/help - ヘルプ\n/calendar - カレンダー表示\n/book - 予約する",
            'direct': "💬 <b>直接:</b>\n• 価格問い合わせ\n• 予約リクエスト\n• 相談\n• 苦情",
            'features': "💰 <b>価格見積もり</b> 利用可能!\n🛡️ <b>安全なデータ処理</b>\n📅 <b>カレンダー機能</b>"
        },
        'calendar': {
            'title': "📅 <b>カレンダー & 予約</b>",
            'view': "🗓️ <b>今月:</b>\n{calendar_view}",
            'booked_days': "❌ <b>予約済み日:</b> {booked_days}",
            'instructions': "📝 <b>予約する:</b>\n/book DD.MM.YYYY を使用するか希望日を教えてください!",
            'no_bookings': "✅ <b>今月の予約はありません</b>"
        },
        'booking': {
            'success': "✅ <b>予約が成功しました!</b>\n\n📅 <b>日付:</b> {date}\n👤 <b>顧客:</b> {customer_name}\n📞 <b>連絡先:</b> {contact_info}\n🛠️ <b>サービス:</b> {service}",
            'already_booked': "❌ <b>日付は既に予約済み!</b>\n\n📅 {date} は既に予約されています.\n別の日付を選択してください.",
            'invalid_date': "❌ <b>無効な日付!</b>\n\n形式を使用してください: DD.MM.YYYY\n例: /book 15.12.2024",
            'past_date': "❌ <b>過去の日付!</b>\n\n将来の日付を選択してください.",
            'instructions': "📅 <b>予約</b>\n\n使用: /book DD.MM.YYYY\n例: /book 15.12.2024\n\nまたはチャットで希望日を教えてください!"
        }
    },
    'ko': {
        'start': {
            'welcome': "🥰 <b>SHAWO 이사 서비스에 오신 것을 환영합니다!</b>",
            'hello': "👋 <b>안녕하세요 {name}님</b>, 저는 레오, 당신의 디지털 어시스턴트입니다! 😊",
            'services': "<b>📦 다음과 같은 도움을 드릴 수 있습니다:</b>\n• 완전한 이사\n• 가구 조립/분해\n• 리모델링 작업\n• 바닥 설치\n• 최종 청소",
            'features': "💰 <b>즉시 가격 계산</b>\n🌍 <b>다국어 서비스</b>\n🛡️ <b>안전한 데이터 처리</b>\n📅 <b>예약 & 캘린더</b>",
            'note': "<i>저희 팀은 이 대화를 볼 수 있습니다</i>",
            'question': "<b>어떻게 도와드릴까요? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>연락처 SHAWO 이사</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 월-토: 10:00-18:30",
            'languages': "🗣️ 독일어, 영어, 아랍어",
            'privacy': "🛡️ <b>개인정보 보호 정보:</b>\n• https://shawo-umzug-app.kr/개인정보보호\n• https://shawo-umzug-app.kr/데이터보호"
        },
        'services': {
            'title': "🛠️ <b>저희 서비스</b>",
            'moves': "🏠 <b>이사:</b>\n• 완전한 이사\n• 가구 서비스\n• 독일 전역",
            'renovation': "🎨 <b>리모델링:</b>\n• 도장 작업 (프라이머, 코팅, 도장)\n• 드라이월\n• 벽지 시공",
            'cleaning': "📦 <b>바닥 & 청소:</b>\n• 라미네이트 & PVC\n• 이사 후 청소\n• 창문 청소",
            'guarantee': "✅ <b>숨겨진 비용 없음!</b>"
        },
        'prices': {
            'title': "💰 <b>가격 예시 (비구속적)</b>",
            'example': "📋 <b>예시: 2룸 이사 (60m²)</b>",
            'individual': "🎯 <b>개별 가격:</b>\n• 2룸 이사: 650-750 €\n• 프라이머: 5 €/m²\n• 코팅/도장: 12 €/m²\n• 청소: 4-6 €/m²\n• 라미네이트 바닥: 36,50 €/m²",
            'note': "<i>개인 계산을 위해 세부 정보를 제공해 주세요!</i>"
        },
        'help': {
            'title': "⛑ <b>도움말</b>",
            'commands': "📋 <b>명령어:</b>\n/start - 봇 시작\n/contact - 연락처\n/services - 서비스\n/prices - 가격\n/help - 도움말\n/calendar - 캘린더 표시\n/book - 예약하기",
            'direct': "💬 <b>직접:</b>\n• 가격 문의\n• 예약 요청\n• 상담\n• 불만 사항",
            'features': "💰 <b>가격 견적</b> 가능!\n🛡️ <b>안전한 데이터 처리</b>\n📅 <b>캘린더 기능</b>"
        },
        'calendar': {
            'title': "📅 <b>캘린더 & 예약</b>",
            'view': "🗓️ <b>현재 월:</b>\n{calendar_view}",
            'booked_days': "❌ <b>예약된 날짜:</b> {booked_days}",
            'instructions': "📝 <b>예약하기:</b>\n/book DD.MM.YYYY를 사용하거나 원하는 날짜를 알려주세요!",
            'no_bookings': "✅ <b>이번 달 예약 없음</b>"
        },
        'booking': {
            'success': "✅ <b>예약이 성공적으로 완료되었습니다!</b>\n\n📅 <b>날짜:</b> {date}\n👤 <b>고객:</b> {customer_name}\n📞 <b>연락처:</b> {contact_info}\n🛠️ <b>서비스:</b> {service}",
            'already_booked': "❌ <b>날짜가 이미 예약되었습니다!</b>\n\n📅 {date}은(는) 이미 예약되었습니다.\n다른 날짜를 선택해 주세요.",
            'invalid_date': "❌ <b>잘못된 날짜!</b>\n\n형식을 사용해 주세요: DD.MM.YYYY\n예시: /book 15.12.2024",
            'past_date': "❌ <b>과거 날짜!</b>\n\n미래 날짜를 선택해 주세요.",
            'instructions': "📅 <b>예약하기</b>\n\n사용: /book DD.MM.YYYY\n예시: /book 15.12.2024\n\n또는 채팅에서 원하는 날짜를 알려주세요!"
        }
    },
    'pt': {
        'start': {
            'welcome': "🥰 <b>Bem-vindo à SHAWO Mudanças!</b>",
            'hello': "👋 <b>Olá {name}</b>, sou o Leo, seu assistente digital! 😊",
            'services': "<b>📦 Posso ajudá-lo com:</b>\n• Mudanças completas\n• Montagem/desmontagem de móveis\n• Trabalhos de renovação\n• Instalação de pisos\n• Limpeza final",
            'features': "💰 <b>Cálculos de preços instantâneos</b>\n🌍 <b>Serviço multilíngue</b>\n🛡️ <b>Processamento seguro de dados</b>\n📅 <b>Reserva de compromissos & Calendário</b>",
            'note': "<i>Nossa equipe pode ver esta conversa</i>",
            'question': "<b>Como posso ajudá-lo? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Contato SHAWO Mudanças</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Seg-Sáb: 10:00-18:30",
            'languages': "🗣️ Alemão, Inglês, Árabe",
            'privacy': "🛡️ <b>Informações de privacidade:</b>\n• https://shawo-umzug-app.pt/privacidade\n• https://shawo-umzug-app.pt/protecao-dados"
        },
        'services': {
            'title': "🛠️ <b>Nossos Serviços</b>",
            'moves': "🏠 <b>Mudanças:</b>\n• Mudanças completas\n• Serviço de móveis\n• Toda a Alemanha",
            'renovation': "🎨 <b>Renovação:</b>\n• Trabalhos de pintura (Primário, Revestimento, Pintura)\n• Drywall\n• Papel de parede",
            'cleaning': "📦 <b>Piso & Limpeza:</b>\n• Laminado & PVC\n• Limpeza pós-mudança\n• Limpeza de janelas",
            'guarantee': "✅ <b>Sem custos ocultos!</b>"
        },
        'prices': {
            'title': "💰 <b>EXEMPLOS DE PREÇOS (não vinculativos)</b>",
            'example': "📋 <b>Exemplo: Mudança 2 quartos (60m²)</b>",
            'individual': "🎯 <b>Preços individuais:</b>\n• Mudança 2 quartos: 650-750 €\n• Primário: 5 €/m²\n• Revestimento/Pintura: 12 €/m²\n• Limpeza: 4-6 €/m²\n• Piso laminado: 36,50 €/m²",
            'note': "<i>Para cálculo personalizado forneça detalhes!</i>"
        },
        'help': {
            'title': "⛑ <b>Ajuda</b>",
            'commands': "📋 <b>Comandos:</b>\n/start - Iniciar bot\n/contact - Contato\n/services - Serviços\n/prices - Preços\n/help - Ajuda\n/calendar - Mostrar calendário\n/book - Reservar compromisso",
            'direct': "💬 <b>Direto:</b>\n• Consultas de preços\n• Pedidos de compromissos\n• Consultoria\n• Reclamações",
            'features': "💰 <b>Estimativas de preço</b> disponíveis!\n🛡️ <b>Processamento seguro de dados</b>\n📅 <b>Função calendário</b>"
        },
        'calendar': {
            'title': "📅 <b>Calendário & Compromissos</b>",
            'view': "🗓️ <b>Mês atual:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Dias reservados:</b> {booked_days}",
            'instructions': "📝 <b>Reservar compromisso:</b>\nUse /book DD.MM.YYYY ou diga-me sua data preferida!",
            'no_bookings': "✅ <b>Nenhum dia reservado este mês</b>"
        },
        'booking': {
            'success': "✅ <b>Compromisso reservado com sucesso!</b>\n\n📅 <b>Data:</b> {date}\n👤 <b>Cliente:</b> {customer_name}\n📞 <b>Contato:</b> {contact_info}\n🛠️ <b>Serviço:</b> {service}",
            'already_booked': "❌ <b>Data já reservada!</b>\n\n📅 {date} já está ocupada.\nPor favor escolha outra data.",
            'invalid_date': "❌ <b>Data inválida!</b>\n\nPor favor use o formato: DD.MM.YYYY\nExemplo: /book 15.12.2024",
            'past_date': "❌ <b>Data passada!</b>\n\nPor favor escolha uma data futura.",
            'instructions': "📅 <b>Reserva de Compromisso</b>\n\nUse: /book DD.MM.YYYY\nExemplo: /book 15.12.2024\n\nOu diga-me sua data preferida no chat!"
        }
    },
    'nl': {
        'start': {
            'welcome': "🥰 <b>Welkom bij SHAWO Verhuizingen!</b>",
            'hello': "👋 <b>Hallo {name}</b>, ik ben Leo, uw digitale assistent! 😊",
            'services': "<b>📦 Ik kan u helpen met:</b>\n• Complete verhuizingen\n• Meubelmontage/demontage\n• Renovatie werk\n• Vloerinstallatie\n• Eindreiniging",
            'features': "💰 <b>Directe prijsberekeningen</b>\n🌍 <b>Meertalige service</b>\n🛡️ <b>Veilige gegevensverwerking</b>\n📅 <b>Afspraakboeking & Kalender</b>",
            'note': "<i>Ons team kan dit gesprek bekijken</i>",
            'question': "<b>Hoe kan ik u helpen? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Contact SHAWO Verhuizingen</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Ma-Za: 10:00-18:30",
            'languages': "🗣️ Duits, Engels, Arabisch",
            'privacy': "🛡️ <b>Privacy-informatie:</b>\n• https://shawo-umzug-app.nl/privacy\n• https://shawo-umzug-app.nl/gegevensbescherming"
        },
        'services': {
            'title': "🛠️ <b>Onze Diensten</b>",
            'moves': "🏠 <b>Verhuizingen:</b>\n• Complete verhuizingen\n• Meubelservice\n• Heel Duitsland",
            'renovation': "🎨 <b>Renovatie:</b>\n• Schilderwerk (Primer, Coating, Schilderen)\n• Gipsplaat\n• Behangen",
            'cleaning': "📦 <b>Vloer & Reiniging:</b>\n• Laminaat & PVC\n• Verhuisreiniging\n• Ramen reinigen",
            'guarantee': "✅ <b>Geen verborgen kosten!</b>"
        },
        'prices': {
            'title': "💰 <b>PRIJSVOORBEELDEN (niet-bindend)</b>",
            'example': "📋 <b>Voorbeeld: 2-kamer verhuizing (60m²)</b>",
            'individual': "🎯 <b>Individuele prijzen:</b>\n• 2-kamer verhuizing: 650-750 €\n• Primer: 5 €/m²\n• Coating/Schilderen: 12 €/m²\n• Reiniging: 4-6 €/m²\n• Laminaat vloer: 36,50 €/m²",
            'note': "<i>Voor persoonlijke berekening geef details op!</i>"
        },
        'help': {
            'title': "⛑ <b>Help</b>",
            'commands': "📋 <b>Commando's:</b>\n/start - Start bot\n/contact - Contact\n/services - Diensten\n/prices - Prijzen\n/help - Help\n/calendar - Toon kalender\n/book - Boek afspraak",
            'direct': "💬 <b>Direct:</b>\n• Prijsopvragen\n• Afspraakverzoeken\n• Consultatie\n• Klachten",
            'features': "💰 <b>Prijsschattingen</b> beschikbaar!\n🛡️ <b>Veilige gegevensverwerking</b>\n📅 <b>Kalenderfunctie</b>"
        },
        'calendar': {
            'title': "📅 <b>Kalender & Afspraken</b>",
            'view': "🗓️ <b>Huidige maand:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Geboekte dagen:</b> {booked_days}",
            'instructions': "📝 <b>Boek afspraak:</b>\nGebruik /book DD.MM.YYYY of vertel me uw voorkeursdatum!",
            'no_bookings': "✅ <b>Geen geboekte dagen deze maand</b>"
        },
        'booking': {
            'success': "✅ <b>Afspraak succesvol geboekt!</b>\n\n📅 <b>Datum:</b> {date}\n👤 <b>Klant:</b> {customer_name}\n📞 <b>Contact:</b> {contact_info}\n🛠️ <b>Service:</b> {service}",
            'already_booked': "❌ <b>Datum al geboekt!</b>\n\n📅 {date} is al bezet.\nKies een andere datum.",
            'invalid_date': "❌ <b>Ongeldige datum!</b>\n\nGebruik formaat: DD.MM.YYYY\nVoorbeeld: /book 15.12.2024",
            'past_date': "❌ <b>Verleden datum!</b>\n\nKies een toekomstige datum.",
            'instructions': "📅 <b>Afspraak Boeken</b>\n\nGebruik: /book DD.MM.YYYY\nVoorbeeld: /book 15.12.2024\n\nOf vertel me uw voorkeursdatum in de chat!"
        }
    },
    'sv': {
        'start': {
            'welcome': "🥰 <b>Välkommen till SHAWO Flyttar!</b>",
            'hello': "👋 <b>Hej {name}</b>, jag är Leo, din digitala assistent! 😊",
            'services': "<b>📦 Jag kan hjälpa dig med:</b>\n• Kompletta flyttar\n• Möbelmontering/avmontering\n• Renoveringsarbeten\n• Golvläggning\n• Slutstädning",
            'features': "💰 <b>Omedelbara priskalkyler</b>\n🌍 <b>Flerspråkig service</b>\n🛡️ <b>Säker databehandling</b>\n📅 <b>Bokning av möten & Kalender</b>",
            'note': "<i>Vårt team kan se denna konversation</i>",
            'question': "<b>Hur kan jag hjälpa dig? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Kontakt SHAWO Flyttar</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Mån-Lör: 10:00-18:30",
            'languages': "🗣️ Tyska, Engelska, Arabiska",
            'privacy': "🛡️ <b>Integritetsinformation:</b>\n• https://shawo-umzug-app.se/integritet\n• https://shawo-umzug-app.se/dataskydd"
        },
        'services': {
            'title': "🛠️ <b>Våra Tjänster</b>",
            'moves': "🏠 <b>Flyttar:</b>\n• Kompletta flyttar\n• Möbelservice\n• Hela Tyskland",
            'renovation': "🎨 <b>Renovering:</b>\n• Målningarbeten (Primer, Beläggning, Målning)\n• Gipsskivor\n• Tapetsering",
            'cleaning': "📦 <b>Golv & Städning:</b>\n• Laminat & PVC\n• Flyttstädning\n• Fönsterputs",
            'guarantee': "✅ <b>Inga dolda kostnader!</b>"
        },
        'prices': {
            'title': "💰 <b>PRISEXEMPEL (obindande)</b>",
            'example': "📋 <b>Exempel: 2-rum flytt (60m²)</b>",
            'individual': "🎯 <b>Individuella priser:</b>\n• 2-rum flytt: 650-750 €\n• Primer: 5 €/m²\n• Beläggning/Målning: 12 €/m²\n• Städning: 4-6 €/m²\n• Laminatgolv: 36,50 €/m²",
            'note': "<i>För personlig kalkyl ange detaljer!</i>"
        },
        'help': {
            'title': "⛑ <b>Hjälp</b>",
            'commands': "📋 <b>Kommandon:</b>\n/start - Starta bot\n/contact - Kontakt\n/services - Tjänster\n/prices - Priser\n/help - Hjälp\n/calendar - Visa kalender\n/book - Boka möte",
            'direct': "💬 <b>Direkt:</b>\n• Prisförfrågningar\n• Mötesförfrågningar\n• Rådgivning\n• Klagomål",
            'features': "💰 <b>Prisuppskattningar</b> tillgängliga!\n🛡️ <b>Säker databehandling</b>\n📅 <b>Kalenderfunktion</b>"
        },
        'calendar': {
            'title': "📅 <b>Kalender & Möten</b>",
            'view': "🗓️ <b>Aktuell månad:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Bokade dagar:</b> {booked_days}",
            'instructions': "📝 <b>Boka möte:</b>\nAnvänd /book DD.MM.YYYY eller berätta din önskade datum!",
            'no_bookings': "✅ <b>Inga bokade dagar denna månad</b>"
        },
        'booking': {
            'success': "✅ <b>Möte framgångsrikt bokat!</b>\n\n📅 <b>Datum:</b> {date}\n👤 <b>Kund:</b> {customer_name}\n📞 <b>Kontakt:</b> {contact_info}\n🛠️ <b>Tjänst:</b> {service}",
            'already_booked': "❌ <b>Datum redan bokat!</b>\n\n📅 {date} är redan upptagen.\nVänligen välj ett annat datum.",
            'invalid_date': "❌ <b>Ogiltigt datum!</b>\n\nVänligen använd format: DD.MM.YYYY\nExempel: /book 15.12.2024",
            'past_date': "❌ <b>Förflutet datum!</b>\n\nVänligen välj ett framtida datum.",
            'instructions': "📅 <b>Mötesbokning</b>\n\nAnvänd: /book DD.MM.YYYY\nExempel: /book 15.12.2024\n\nEller berätta din önskade datum i chatten!"
        }
    },
    'da': {
        'start': {
            'welcome': "🥰 <b>Velkommen til SHAWO Flytninger!</b>",
            'hello': "👋 <b>Hej {name}</b>, jeg er Leo, din digitale assistent! 😊",
            'services': "<b>📦 Jeg kan hjælpe dig med:</b>\n• Komplette flytninger\n• Møbelmontering/afmontering\n• Renoveringsarbejde\n• Gulvlægning\n• Slutrengøring",
            'features': "💰 <b>Øjeblikkelige priskalkulationer</b>\n🌍 <b>Flersproget service</b>\n🛡️ <b>Sikker databehandling</b>\n📅 <b>Aftalebooking & Kalender</b>",
            'note': "<i>Vores team kan se denne samtale</i>",
            'question': "<b>Hvordan kan jeg hjælpe dig? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Kontakt SHAWO Flytninger</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Man-Lør: 10:00-18:30",
            'languages': "🗣️ Tysk, Engelsk, Arabisk",
            'privacy': "🛡️ <b>Privatlivsoplysninger:</b>\n• https://shawo-umzug-app.dk/privatliv\n• https://shawo-umzug-app.dk/databeskyttelse"
        },
        'services': {
            'title': "🛠️ <b>Vores Tjenester</b>",
            'moves': "🏠 <b>Flytninger:</b>\n• Komplette flytninger\n• Møbelservice\n• Hele Tyskland",
            'renovation': "🎨 <b>Renovering:</b>\n• Malerarbejde (Grunding, Belægning, Maling)\n• Gipsplader\n• Tapetsering",
            'cleaning': "📦 <b>Gulv & Rengøring:</b>\n• Laminat & PVC\n• Flytterengøring\n• Vinduespudsning",
            'guarantee': "✅ <b>Ingen skjulte omkostninger!</b>"
        },
        'prices': {
            'title': "💰 <b>PRISEEKSEMPLER (ubindende)</b>",
            'example': "📋 <b>Eksempel: 2-værelses flytning (60m²)</b>",
            'individual': "🎯 <b>Individuelle priser:</b>\n• 2-værelses flytning: 650-750 €\n• Grunding: 5 €/m²\n• Belægning/Maling: 12 €/m²\n• Rengøring: 4-6 €/m²\n• Laminatgulv: 36,50 €/m²",
            'note': "<i>For personlig kalkyle angiv detaljer!</i>"
        },
        'help': {
            'title': "⛑ <b>Hjælp</b>",
            'commands': "📋 <b>Kommandoer:</b>\n/start - Start bot\n/contact - Kontakt\n/services - Tjenester\n/prices - Priser\n/help - Hjælp\n/calendar - Vis kalender\n/book - Book aftale",
            'direct': "💬 <b>Direkte:</b>\n• Prisforespørgsler\n• Aftaleanmodninger\n• Rådgivning\n• Klager",
            'features': "💰 <b>Prisestimater</b> tilgængelige!\n🛡️ <b>Sikker databehandling</b>\n📅 <b>Kalenderfunktion</b>"
        },
        'calendar': {
            'title': "📅 <b>Kalender & Aftaler</b>",
            'view': "🗓️ <b>Nuværende måned:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Bookede dage:</b> {booked_days}",
            'instructions': "📝 <b>Book aftale:</b>\nBrug /book DD.MM.YYYY eller fortæl mig din foretrukne dato!",
            'no_bookings': "✅ <b>Ingen bookede dage denne måned</b>"
        },
        'booking': {
            'success': "✅ <b>Aftale succesfuldt booket!</b>\n\n📅 <b>Dato:</b> {date}\n👤 <b>Kunde:</b> {customer_name}\n📞 <b>Kontakt:</b> {contact_info}\n🛠️ <b>Service:</b> {service}",
            'already_booked': "❌ <b>Dato allerede booket!</b>\n\n📅 {date} er allerede optaget.\nVælg venligst en anden dato.",
            'invalid_date': "❌ <b>Ugyldig dato!</b>\n\nBrug venligst format: DD.MM.YYYY\nEksempel: /book 15.12.2024",
            'past_date': "❌ <b>Forhenværende dato!</b>\n\nVælg venligst en fremtidig dato.",
            'instructions': "📅 <b>Aftalebooking</b>\n\nBrug: /book DD.MM.YYYY\nEksempel: /book 15.12.2024\n\nEller fortæl mig din foretrukne dato i chatten!"
        }
    },
    'cs': {
        'start': {
            'welcome': "🥰 <b>Vítejte v SHAWO Stěhování!</b>",
            'hello': "👋 <b>Ahoj {name}</b>, jsem Leo, váš digitální asistent! 😊",
            'services': "<b>📦 Mohu vám pomoci s:</b>\n• Kompletními stěhováními\n• Montáží/demontáží nábytku\n• Renovačními pracemi\n• Pokládkou podlah\n• Finálním úklidem",
            'features': "💰 <b>Okamžité výpočty cen</b>\n🌍 <b>Vícejazyčný servis</b>\n🛡️ <b>Bezpečné zpracování dat</b>\n📅 <b>Rezervace schůzek & Kalendář</b>",
            'note': "<i>Náš tým může vidět tuto konverzaci</i>",
            'question': "<b>Jak vám mohu pomoci? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Kontakt SHAWO Stěhování</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Po-So: 10:00-18:30",
            'languages': "🗣️ Němčina, Angličtina, Arabština",
            'privacy': "🛡️ <b>Informace o ochraně soukromí:</b>\n• https://shawo-umzug-app.cz/ochrana-soukromi\n• https://shawo-umzug-app.cz/ochrana-dat"
        },
        'services': {
            'title': "🛠️ <b>Naše Služby</b>",
            'moves': "🏠 <b>Stěhování:</b>\n• Kompletní stěhování\n• Nábytkový servis\n• Celé Německo",
            'renovation': "🎨 <b>Rekonstrukce:</b>\n• Malířské práce (Podklad, Nátěr, Malba)\n• Sádrokarton\n• Tapetování",
            'cleaning': "📦 <b>Podlaha & Úklid:</b>\n• Laminát & PVC\n• Úklid po stěhování\n• Čištění oken",
            'guarantee': "✅ <b>Bez skrytých nákladů!</b>"
        },
        'prices': {
            'title': "💰 <b>CENOVÉ PŘÍKLADY (nezávazné)</b>",
            'example': "📋 <b>Příklad: Stěhování 2+1 (60m²)</b>",
            'individual': "🎯 <b>Individuální ceny:</b>\n• Stěhování 2+1: 650-750 €\n• Podklad: 5 €/m²\n• Nátěr/Malba: 12 €/m²\n• Úklid: 4-6 €/m²\n• Laminátová podlaha: 36,50 €/m²",
            'note': "<i>Pro osobní kalkulaci uveďte podrobnosti!</i>"
        },
        'help': {
            'title': "⛑ <b>Nápověda</b>",
            'commands': "📋 <b>Příkazy:</b>\n/start - Spustit bota\n/contact - Kontakt\n/services - Služby\n/prices - Ceny\n/help - Nápověda\n/calendar - Zobrazit kalendář\n/book - Rezervovat schůzku",
            'direct': "💬 <b>Přímo:</b>\n• Cenové dotazy\n• Žádosti o schůzky\n• Konzultace\n• Stížnosti",
            'features': "💰 <b>Odhady cen</b> k dispozici!\n🛡️ <b>Bezpečné zpracování dat</b>\n📅 <b>Funkce kalendáře</b>"
        },
        'calendar': {
            'title': "📅 <b>Kalendář & Schůzky</b>",
            'view': "🗓️ <b>Aktuální měsíc:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Rezervované dny:</b> {booked_days}",
            'instructions': "📝 <b>Rezervovat schůzku:</b>\nPoužijte /book DD.MM.YYYY nebo mi řekněte preferované datum!",
            'no_bookings': "✅ <b>Tento měsíc žádné rezervované dny</b>"
        },
        'booking': {
            'success': "✅ <b>Schůzka úspěšně rezervována!</b>\n\n📅 <b>Datum:</b> {date}\n👤 <b>Zákazník:</b> {customer_name}\n📞 <b>Kontakt:</b> {contact_info}\n🛠️ <b>Služba:</b> {service}",
            'already_booked': "❌ <b>Datum již rezervováno!</b>\n\n📅 {date} je již obsazeno.\nProsím vyberte jiné datum.",
            'invalid_date': "❌ <b>Neplatné datum!</b>\n\nProsím použijte formát: DD.MM.YYYY\nPříklad: /book 15.12.2024",
            'past_date': "❌ <b>Minulé datum!</b>\n\nProsím vyberte budoucí datum.",
            'instructions': "📅 <b>Rezervace Schůzky</b>\n\nPoužijte: /book DD.MM.YYYY\nPříklad: /book 15.12.2024\n\nNebo mi řekněte preferované datum v chatu!"
        }
    },
    'hr': {
        'start': {
            'welcome': "🥰 <b>Dobrodošli u SHAWO Selidbe!</b>",
            'hello': "👋 <b>Bok {name}</b>, ja sam Leo, vaš digitalni asistent! 😊",
            'services': "<b>📦 Mogu vam pomoći s:</b>\n• Potpunim selidbama\n• Sastavljanjem/rastavljanjem namještaja\n• Radovima obnove\n• Polaganjem podova\n• Završnim čišćenjem",
            'features': "💰 <b>Trenutni izračuni cijena</b>\n🌍 <b>Višejezična usluga</b>\n🛡️ <b>Sigurna obrada podataka</b>\n📅 <b>Rezervacija termina & Kalendar</b>",
            'note': "<i>Naš tim može vidjeti ovaj razgovor</i>",
            'question': "<b>Kako vam mogu pomoći? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Kontakt SHAWO Selidbe</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Pon-Sub: 10:00-18:30",
            'languages': "🗣️ Njemački, Engleski, Arapski",
            'privacy': "🛡️ <b>Informacije o privatnosti:</b>\n• https://shawo-umzug-app.hr/privatnost\n• https://shawo-umzug-app.hr/zaštita-podataka"
        },
        'services': {
            'title': "🛠️ <b>Naše Usluge</b>",
            'moves': "🏠 <b>Selidbe:</b>\n• Potpune selidbe\n• Usluga namještaja\n• Cijela Njemačka",
            'renovation': "🎨 <b>Obnova:</b>\n• Slikarski radovi (Temeljni premaz, Premaz, Bojanje)\n• Suhi zid\n• Tapetiranje",
            'cleaning': "📦 <b>Pod & Čišćenje:</b>\n• Laminat & PVC\n• Čišćenje nakon selidbe\n• Pranje prozora",
            'guarantee': "✅ <b>Bez skrivenih troškova!</b>"
        },
        'prices': {
            'title': "💰 <b>PRIMJERI CIJENA (neobvezujući)</b>",
            'example': "📋 <b>Primjer: Selidba 2-sobnog stana (60m²)</b>",
            'individual': "🎯 <b>Pojedinačne cijene:</b>\n• Selidba 2-sobnog stana: 650-750 €\n• Temeljni premaz: 5 €/m²\n• Premaz/Bojanje: 12 €/m²\n• Čišćenje: 4-6 €/m²\n• Laminat pod: 36,50 €/m²",
            'note': "<i>Za osobni izračun navedite detalje!</i>"
        },
        'help': {
            'title': "⛑ <b>Pomoć</b>",
            'commands': "📋 <b>Naredbe:</b>\n/start - Pokreni bota\n/contact - Kontakt\n/services - Usluge\n/prices - Cijene\n/help - Pomoć\n/calendar - Prikaži kalendar\n/book - Rezerviraj termin",
            'direct': "💬 <b>Izravno:</b>\n• Upiti o cijenama\n• Zahtjevi za terminima\n• Savjetovanje\n• Prigovori",
            'features': "💰 <b>Procjene cijena</b> dostupne!\n🛡️ <b>Sigurna obrada podataka</b>\n📅 <b>Funkcija kalendara</b>"
        },
        'calendar': {
            'title': "📅 <b>Kalendar & Termini</b>",
            'view': "🗓️ <b>Trenutni mjesec:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Rezervirani dani:</b> {booked_days}",
            'instructions': "📝 <b>Rezerviraj termin:</b>\nKoristite /book DD.MM.YYYY ili mi recite željeni datum!",
            'no_bookings': "✅ <b>Nema rezerviranih dana ovaj mjesec</b>"
        },
        'booking': {
            'success': "✅ <b>Termin uspješno rezerviran!</b>\n\n📅 <b>Datum:</b> {date}\n👤 <b>Kupac:</b> {customer_name}\n📞 <b>Kontakt:</b> {contact_info}\n🛠️ <b>Usluga:</b> {service}",
            'already_booked': "❌ <b>Datum već rezerviran!</b>\n\n📅 {date} je već zauzet.\nMolimo odaberite drugi datum.",
            'invalid_date': "❌ <b>Nevažeći datum!</b>\n\nMolimo koristite format: DD.MM.YYYY\nPrimjer: /book 15.12.2024",
            'past_date': "❌ <b>Prošli datum!</b>\n\nMolimo odaberite budući datum.",
            'instructions': "📅 <b>Rezervacija Termina</b>\n\nKoristite: /book DD.MM.YYYY\nPrimjer: /book 15.12.2024\n\nIli mi recite željeni datum u chatu!"
        }
    },
    'bg': {
        'start': {
            'welcome': "🥰 <b>Добре дошли в SHAWO Премествания!</b>",
            'hello': "👋 <b>Здравей {name}</b>, аз съм Лео, вашият цифров асистент! 😊",
            'services': "<b>📦 Мога да ви помогна с:</b>\n• Пълни премествания\n• Сглобяване/разглобяване на мебели\n• Ремонтни работи\n• Настилка на подове\n• Финално почистване",
            'features': "💰 <b>Моментни изчисления на цени</b>\n🌍 <b>Многоезична услуга</b>\n🛡️ <b>Сигурна обработка на данни</b>\n📅 <b>Резервация на срещи & Календар</b>",
            'note': "<i>Нашият екип може да вижда този разговор</i>",
            'question': "<b>Как мога да ви помогна? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Контакт SHAWO Премествания</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Пон-Съб: 10:00-18:30",
            'languages': "🗣️ Немски, Английски, Арабски",
            'privacy': "🛡️ <b>Информация за поверителност:</b>\n• https://shawo-umzug-app.bg/поверителност\n• https://shawo-umzug-app.bg/защита-данни"
        },
        'services': {
            'title': "🛠️ <b>Нашите Услуги</b>",
            'moves': "🏠 <b>Премествания:</b>\n• Пълни премествания\n• Мебелна услуга\n• Цяла Германия",
            'renovation': "🎨 <b>Ремонт:</b>\n• Боядисване (Грунд, Покритие, Боя)\n• Гипсокартон\n• Тапетиране",
            'cleaning': "📦 <b>Под & Почистване:</b>\n• Ламинат & PVC\n• Почистване след преместване\n• Почистване на прозорци",
            'guarantee': "✅ <b>Без скрити разходи!</b>"
        },
        'prices': {
            'title': "💰 <b>ПРИМЕРИ ЗА ЦЕНИ (незадължителни)</b>",
            'example': "📋 <b>Пример: Преместване на 2-стаен апартамент (60m²)</b>",
            'individual': "🎯 <b>Индивидуални цени:</b>\n• Преместване 2-стаен: 650-750 €\n• Грунд: 5 €/m²\n• Покритие/Боя: 12 €/m²\n• Почистване: 4-6 €/m²\n• Ламинатен под: 36,50 €/m²",
            'note': "<i>За лична калкулация предоставете детайли!</i>"
        },
        'help': {
            'title': "⛑ <b>Помощ</b>",
            'commands': "📋 <b>Команди:</b>\n/start - Стартирай бот\n/contact - Контакт\n/services - Услуги\n/prices - Цени\n/help - Помощ\n/calendar - Покажи календар\n/book - Резервирай среща",
            'direct': "💬 <b>Директно:</b>\n• Запитвания за цени\n• Заявки за срещи\n• Консултация\n• Жалби",
            'features': "💰 <b>Оценки на цени</b> налични!\n🛡️ <b>Сигурна обработка на данни</b>\n📅 <b>Функция календар</b>"
        },
        'calendar': {
            'title': "📅 <b>Календар & Срещи</b>",
            'view': "🗓️ <b>Текущ месец:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Резервирани дни:</b> {booked_days}",
            'instructions': "📝 <b>Резервирай среща:</b>\nИзползвайте /book DD.MM.YYYY или ми кажете предпочитана дата!",
            'no_bookings': "✅ <b>Няма резервирани дни този месец</b>"
        },
        'booking': {
            'success': "✅ <b>Срещата е успешно резервирана!</b>\n\n📅 <b>Дата:</b> {date}\n👤 <b>Клиент:</b> {customer_name}\n📞 <b>Контакт:</b> {contact_info}\n🛠️ <b>Услуга:</b> {service}",
            'already_booked': "❌ <b>Датата вече е заета!</b>\n\n📅 {date} вече е резервирана.\nМоля изберете друга дата.",
            'invalid_date': "❌ <b>Невалидна дата!</b>\n\nМоля използвайте формат: DD.MM.YYYY\nПример: /book 15.12.2024",
            'past_date': "❌ <b>Минала дата!</b>\n\nМоля изберете бъдеща дата.",
            'instructions': "📅 <b>Резервация на Среща</b>\n\nИзползвайте: /book DD.MM.YYYY\nПример: /book 15.12.2024\n\nИли ми кажете предпочитана дата в чата!"
        }
    },
    'bn': {
        'start': {
            'welcome': "🥰 <b>SHAWO মুভার্সে স্বাগতম!</b>",
            'hello': "👋 <b>হ্যালো {name}</b>, আমি লিও, আপনার ডিজিটাল সহায়ক! 😊",
            'services': "<b>📦 আমি আপনাকে সাহায্য করতে পারি:</b>\n• সম্পূর্ণ স্থানান্তর\n• আসবাবপত্র সংযোজন/বিয়োজন\n• সংস্কার কাজ\n• মেঝে স্থাপন\n• চূড়ান্ত পরিষ্কার",
            'features': "💰 <b>তাত্ক্ষণিক মূল্য গণনা</b>\n🌍 <b>বহুভাষিক পরিষেবা</b>\n🛡️ <b>নিরাপদ ডেটা প্রক্রিয়াকরণ</b>\n📅 <b>অ্যাপয়েন্টমেন্ট বুকিং & ক্যালেন্ডার</b>",
            'note': "<i>আমাদের দল এই কথোপকথন দেখতে পারে</i>",
            'question': "<b>আমি আপনাকে কিভাবে সাহায্য করতে পারি? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>যোগাযোগ SHAWO মুভার্স</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 সোম-শনি: 10:00-18:30",
            'languages': "🗣️ জার্মান, ইংরেজি, আরবি",
            'privacy': "🛡️ <b>গোপনীয়তা তথ্য:</b>\n• https://shawo-umzug-app.bn/গোপনীয়তা\n• https://shawo-umzug-app.bn/ডেটা-সুরক্ষা"
        },
        'services': {
            'title': "🛠️ <b>আমাদের সেবাসমূহ</b>",
            'moves': "🏠 <b>স্থানান্তর:</b>\n• সম্পূর্ণ স্থানান্তর\n• আসবাবপত্র সেবা\n• সমগ্র জার্মানি",
            'renovation': "🎨 <b>সংস্কার:</b>\n• পেইন্টিং কাজ (প্রাইমার, কোটিং, পেইন্টিং)\n• ড্রাইওয়াল\n• ওয়ালপেপারিং",
            'cleaning': "📦 <b>মেঝে & পরিষ্কার:</b>\n• ল্যামিনেট & PVC\n• স্থানান্তর পরবর্তী পরিষ্কার\n• জানালা পরিষ্কার",
            'guarantee': "✅ <b>লুকানো খরচ নেই!</b>"
        },
        'prices': {
            'title': "💰 <b>মূল্যের উদাহরণ (অবন্ধনমূলক)</b>",
            'example': "📋 <b>উদাহরণ: 2-রুম স্থানান্তর (60m²)</b>",
            'individual': "🎯 <b>ব্যক্তিগত মূল্য:</b>\n• 2-রুম স্থানান্তর: 650-750 €\n• প্রাইমার: 5 €/m²\n• কোটিং/পেইন্টিং: 12 €/m²\n• পরিষ্কার: 4-6 €/m²\n• ল্যামিনেট মেঝে: 36,50 €/m²",
            'note': "<i>ব্যক্তিগত গণনার জন্য বিবরণ প্রদান করুন!</i>"
        },
        'help': {
            'title': "⛑ <b>সাহায্য</b>",
            'commands': "📋 <b>কমান্ড:</b>\n/start - বট শুরু করুন\n/contact - যোগাযোগ\n/services - সেবা\n/prices - মূল্য\n/help - সাহায্য\n/calendar - ক্যালেন্ডার দেখান\n/book - অ্যাপয়েন্টমেন্ট বুক করুন",
            'direct': "💬 <b>সরাসরি:</b>\n• মূল্য অনুসন্ধান\n• অ্যাপয়েন্টমেন্ট অনুরোধ\n• পরামর্শ\n• অভিযোগ",
            'features': "💰 <b>মূল্য অনুমান</b> উপলব্ধ!\n🛡️ <b>নিরাপদ ডেটা প্রক্রিয়াকরণ</b>\n📅 <b>ক্যালেন্ডার ফাংশন</b>"
        },
        'calendar': {
            'title': "📅 <b>ক্যালেন্ডার & অ্যাপয়েন্টমেন্ট</b>",
            'view': "🗓️ <b>বর্তমান মাস:</b>\n{calendar_view}",
            'booked_days': "❌ <b>বুক করা দিন:</b> {booked_days}",
            'instructions': "📝 <b>অ্যাপয়েন্টমেন্ট বুক করুন:</b>\n/book DD.MM.YYYY ব্যবহার করুন বা আমাকে আপনার পছন্দের তারিখ বলুন!",
            'no_bookings': "✅ <b>এই মাসে কোন বুক করা দিন নেই</b>"
        },
        'booking': {
            'success': "✅ <b>অ্যাপয়েন্টমেন্ট সফলভাবে বুক করা হয়েছে!</b>\n\n📅 <b>তারিখ:</b> {date}\n👤 <b>গ্রাহক:</b> {customer_name}\n📞 <b>যোগাযোগ:</b> {contact_info}\n🛠️ <b>সেবা:</b> {service}",
            'already_booked': "❌ <b>তারিখ ইতিমধ্যেই বুক করা আছে!</b>\n\n📅 {date} ইতিমধ্যেই নেওয়া হয়েছে।\nঅনুগ্রহ করে অন্য তারিখ নির্বাচন করুন।",
            'invalid_date': "❌ <b>অবৈধ তারিখ!</b>\n\nঅনুগ্রহ করে ফরম্যাট ব্যবহার করুন: DD.MM.YYYY\nউদাহরণ: /book 15.12.2024",
            'past_date': "❌ <b>অতীত তারিখ!</b>\n\nঅনুগ্রহ করে ভবিষ্যত তারিখ নির্বাচন করুন।",
            'instructions': "📅 <b>অ্যাপয়েন্টমেন্ট বুকিং</b>\n\nব্যবহার করুন: /book DD.MM.YYYY\nউদাহরণ: /book 15.12.2024\n\nঅথবা চ্যাটে আমাকে আপনার পছন্দের তারিখ বলুন!"
        }
    },
    'el': {
        'start': {
            'welcome': "🥰 <b>Καλώς ήρθατε στην SHAWO Μετακομίσεις!</b>",
            'hello': "👋 <b>Γεια σου {name}</b>, είμαι ο Λέο, ο ψηφιακός σας βοηθός! 😊",
            'services': "<b>📦 Μπορώ να σας βοηθήσω με:</b>\n• Πλήρεις μετακομίσεις\n• Συναρμολόγηση/αποσυναρμολόγηση επίπλων\n• Εργασίες ανακαίνισης\n• Εγκατάσταση δαπέδων\n• Τελικό καθάρισμα",
            'features': "💰 <b>Άμεσοι υπολογισμοί τιμών</b>\n🌍 <b>Πολύγλωσση εξυπηρέτηση</b>\n🛡️ <b>Ασφαλής επεξεργασία δεδομένων</b>\n📅 <b>Κράτηση ραντεβού & Ημερολόγιο</b>",
            'note': "<i>Η ομάδα μας μπορεί να δει αυτήν τη συζήτηση</i>",
            'question': "<b>Πώς μπορώ να σας βοηθήσω? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Επικοινωνία SHAWO Μετακομίσεις</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Δευ-Σαβ: 10:00-18:30",
            'languages': "🗣️ Γερμανικά, Αγγλικά, Αραβικά",
            'privacy': "🛡️ <b>Πληροφορίες απορρήτου:</b>\n• https://shawo-umzug-app.gr/απόρρητο\n• https://shawo-umzug-app.gr/προστασία-δεδομένων"
        },
        'services': {
            'title': "🛠️ <b>Οι Υπηρεσίες Μας</b>",
            'moves': "🏠 <b>Μετακομίσεις:</b>\n• Πλήρεις μετακομίσεις\n• Υπηρεσία επίπλων\n• Σε όλη τη Γερμανία",
            'renovation': "🎨 <b>Ανακαίνιση:</b>\n• Εργασίες βαφής (Αστάρι, Επίστρωση, Βάψιμο)\n• Γυψοσανίδες\n• Ταπετσάρισμα",
            'cleaning': "📦 <b>Δάπεδο & Καθαρισμός:</b>\n• Λαμινέ & PVC\n• Καθαρισμός μετά από μετακόμιση\n• Καθαρισμός παραθύρων",
            'guarantee': "✅ <b>Χωρίς κρυφά κόστη!</b>"
        },
        'prices': {
            'title': "💰 <b>ΠΑΡΑΔΕΙΓΜΑΤΑ ΤΙΜΩΝ (μη δεσμευτικά)</b>",
            'example': "📋 <b>Παράδειγμα: Μετακόμιση 2 δωματίων (60m²)</b>",
            'individual': "🎯 <b>Ατομικές τιμές:</b>\n• Μετακόμιση 2 δωματίων: 650-750 €\n• Αστάρι: 5 €/m²\n• Επίστρωση/Βάψιμο: 12 €/m²\n• Καθαρισμός: 4-6 €/m²\n• Δάπεδο λαμινέ: 36,50 €/m²",
            'note': "<i>Για προσωπικό υπολογισμό δώστε λεπτομέρειες!</i>"
        },
        'help': {
            'title': "⛑ <b>Βοήθεια</b>",
            'commands': "📋 <b>Εντολές:</b>\n/start - Εκκίνηση bot\n/contact - Επικοινωνία\n/services - Υπηρεσίες\n/prices - Τιμές\n/help - Βοήθεια\n/calendar - Εμφάνιση ημερολογίου\n/book - Κράτηση ραντεβού",
            'direct': "💬 <b>Απευθείας:</b>\n• Ερωτήματα τιμών\n• Αιτήματα ραντεβού\n• Συμβουλευτική\n• Παραπόνια",
            'features': "💰 <b>Εκτιμήσεις τιμών</b> διαθέσιμες!\n🛡️ <b>Ασφαλής επεξεργασία δεδομένων</b>\n📅 <b>Λειτουργία ημερολογίου</b>"
        },
        'calendar': {
            'title': "📅 <b>Ημερολόγιο & Ραντεβού</b>",
            'view': "🗓️ <b>Τρέχων μήνας:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Κρατημένες ημέρες:</b> {booked_days}",
            'instructions': "📝 <b>Κράτηση ραντεβού:</b>\nΧρησιμοποιήστε /book DD.MM.YYYY ή πείτε μου την προτιμώμενη ημερομηνία!",
            'no_bookings': "✅ <b>Δεν υπάρχουν κρατημένες ημέρες αυτόν τον μήνα</b>"
        },
        'booking': {
            'success': "✅ <b>Το ραντεβού κρατήθηκε επιτυχώς!</b>\n\n📅 <b>Ημερομηνία:</b> {date}\n👤 <b>Πελάτης:</b> {customer_name}\n📞 <b>Επικοινωνία:</b> {contact_info}\n🛠️ <b>Υπηρεσία:</b> {service}",
            'already_booked': "❌ <b>Η ημερομηνία είναι ήδη κρατημένη!</b>\n\n📅 {date} είναι ήδη δεσμευμένη.\nΠαρακαλώ επιλέξτε άλλη ημερομηνία.",
            'invalid_date': "❌ <b>Μη έγκυρη ημερομηνία!</b>\n\nΠαρακαλώ χρησιμοποιήστε τη μορφή: DD.MM.YYYY\nΠαράδειγμα: /book 15.12.2024",
            'past_date': "❌ <b>Παρελθοντική ημερομηνία!</b>\n\nΠαρακαλώ επιλέξτε μελλοντική ημερομηνία.",
            'instructions': "📅 <b>Κράτηση Ραντεβού</b>\n\nΧρησιμοποιήστε: /book DD.MM.YYYY\nΠαράδειγμα: /book 15.12.2024\n\nΉ πείτε μου την προτιμώμενη ημερομηνία στη συνομιλία!"
        }
    },
    'he': {
        'start': {
            'welcome': "🥰 <b>ברוכים הבאים ל-SHAWO מעברים!</b>",
            'hello': "👋 <b>שלום {name}</b>, אני ליאו, העוזר הדיגיטלי שלך! 😊",
            'services': "<b>📦 אני יכול לעזור לך עם:</b>\n• מעברים מלאים\n• הרכבה/פירוק רהיטים\n• עבודות שיפוץ\n• התקנת רצפות\n• ניקוי סופי",
            'features': "💰 <b>חישובי מחירים מיידיים</b>\n🌍 <b>שירות רב-לשוני</b>\n🛡️ <b>עיבוד נתונים מאובטח</b>\n📅 <b>הזמנת תורים & יומן</b>",
            'note': "<i>הצוות שלנו יכול לראות שיחה זו</i>",
            'question': "<b>איך אני יכול לעזור לך? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>יצירת קשר SHAWO מעברים</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 א-ש: 10:00-18:30",
            'languages': "🗣️ גרמנית, אנגלית, ערבית",
            'privacy': "🛡️ <b>מידע פרטיות:</b>\n• https://shawo-umzug-app.il/פרטיות\n• https://shawo-umzug-app.il/הגנת-נתונים"
        },
        'services': {
            'title': "🛠️ <b>השירותים שלנו</b>",
            'moves': "🏠 <b>מעברים:</b>\n• מעברים מלאים\n• שירות רהיטים\n• בכל רחבי גרמניה",
            'renovation': "🎨 <b>שיפוץ:</b>\n• עבודות צבע (פריימר, ציפוי, צביעה)\n• גבס\n• טפטים",
            'cleaning': "📦 <b>רצפה & ניקיון:</b>\n• למינציה & PVC\n• ניקוי לאחר מעבר\n• ניקוי חלונות",
            'guarantee': "✅ <b>ללא עלויות נסתרות!</b>"
        },
        'prices': {
            'title': "💰 <b>דוגמאות מחירים (לא מחייבות)</b>",
            'example': "📋 <b>דוגמה: מעבר דירה 2 חדרים (60m²)</b>",
            'individual': "🎯 <b>מחירים אישיים:</b>\n• מעבר 2 חדרים: 750-650 €\n• פריימר: 5 €/m²\n• ציפוי/צביעה: 12 €/m²\n• ניקיון: 6-4 €/m²\n• רצפת למינציה: 36.50 €/m²",
            'note': "<i>לחישוב אישי ספק פרטים!</i>"
        },
        'help': {
            'title': "⛑ <b>עזרה</b>",
            'commands': "📋 <b>פקודות:</b>\n/start - התחל בוט\n/contact - יצירת קשר\n/services - שירותים\n/prices - מחירים\n/help - עזרה\n/calendar - הצג יומן\n/book - הזמן תור",
            'direct': "💬 <b>ישיר:</b>\n• שאלות מחיר\n• בקשות תור\n• ייעוץ\n• תלונות",
            'features': "💰 <b>הערכות מחיר</b> זמינות!\n🛡️ <b>עיבוד נתונים מאובטח</b>\n📅 <b>פונקציית יומן</b>"
        },
        'calendar': {
            'title': "📅 <b>יומן & תורים</b>",
            'view': "🗓️ <b>חודש נוכחי:</b>\n{calendar_view}",
            'booked_days': "❌ <b>ימים תפוסים:</b> {booked_days}",
            'instructions': "📝 <b>הזמן תור:</b>\nהשתמש /book DD.MM.YYYY או אמור לי את התאריך המועדף עליך!",
            'no_bookings': "✅ <b>אין ימים תפוסים החודש</b>"
        },
        'booking': {
            'success': "✅ <b>התור נקלט בהצלחה!</b>\n\n📅 <b>תאריך:</b> {date}\n👤 <b>לקוח:</b> {customer_name}\n📞 <b>קשר:</b> {contact_info}\n🛠️ <b>שירות:</b> {service}",
            'already_booked': "❌ <b>התאריך תפוס כבר!</b>\n\n📅 {date} כבר תפוס.\nאנא בחר תאריך אחר.",
            'invalid_date': "❌ <b>תאריך לא תקין!</b>\n\nאנא השתמש בפורמט: DD.MM.YYYY\nדוגמה: /book 15.12.2024",
            'past_date': "❌ <b>תאריך עבר!</b>\n\nאנא בחר תאריך עתידי.",
            'instructions': "📅 <b>הזמנת תור</b>\n\nהשתמש: /book DD.MM.YYYY\nדוגמה: /book 15.12.2024\n\nאו אמור לי את התאריך המועדף עליך בצ'אט!"
        }
    },
    'hi': {
        'start': {
            'welcome': "🥰 <b>SHAWO मूवर्स में आपका स्वागत है!</b>",
            'hello': "👋 <b>नमस्ते {name}</b>, मैं लियो हूं, आपका डिजिटल सहायक! 😊",
            'services': "<b>📦 मैं आपकी सहायता कर सकता हूं:</b>\n• पूर्ण स्थानांतरण\n• फर्नीचर असेंबली/डिसएसेंबली\n• नवीनीकरण कार्य\n• फर्श स्थापना\n• अंतिम सफाई",
            'features': "💰 <b>तत्काल मूल्य गणना</b>\n🌍 <b>बहुभाषी सेवा</b>\n🛡️ <b>सुरक्षित डेटा प्रसंस्करण</b>\n📅 <b>अपॉइंटमेंट बुकिंग & कैलेंडर</b>",
            'note': "<i>हमारी टीम इस वार्तालाप को देख सकती है</i>",
            'question': "<b>मैं आपकी कैसे सहायता कर सकता हूं? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>संपर्क SHAWO मूवर्स</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 सोम-शनि: 10:00-18:30",
            'languages': "🗣️ जर्मन, अंग्रेजी, अरबी",
            'privacy': "🛡️ <b>गोपनीयता जानकारी:</b>\n• https://shawo-umzug-app.in/गोपनीयता\n• https://shawo-umzug-app.in/डेटा-सुरक्षा"
        },
        'services': {
            'title': "🛠️ <b>हमारी सेवाएं</b>",
            'moves': "🏠 <b>स्थानांतरण:</b>\n• पूर्ण स्थानांतरण\n• फर्नीचर सेवा\n• पूरे जर्मनी में",
            'renovation': "🎨 <b>नवीनीकरण:</b>\n• पेंटिंग कार्य (प्राइमर, कोटिंग, पेंटिंग)\n• ड्राईवॉल\n• वॉलपेपरिंग",
            'cleaning': "📦 <b>फर्श & सफाई:</b>\n• लैमिनेट & PVC\n• स्थानांतरण के बाद सफाई\n• खिड़की सफाई",
            'guarantee': "✅ <b>कोई छिपी लागत नहीं!</b>"
        },
        'prices': {
            'title': "💰 <b>मूल्य उदाहरण (गैर-बाध्यकारी)</b>",
            'example': "📋 <b>उदाहरण: 2-कमरा स्थानांतरण (60m²)</b>",
            'individual': "🎯 <b>व्यक्तिगत मूल्य:</b>\n• 2-कमरा स्थानांतरण: 650-750 €\n• प्राइमर: 5 €/m²\n• कोटिंग/पेंटिंग: 12 €/m²\n• सफाई: 4-6 €/m²\n• लैमिनेट फर्श: 36,50 €/m²",
            'note': "<i>व्यक्तिगत गणना के लिए विवरण प्रदान करें!</i>"
        },
        'help': {
            'title': "⛑ <b>सहायता</b>",
            'commands': "📋 <b>आदेश:</b>\n/start - बॉट शुरू करें\n/contact - संपर्क\n/services - सेवाएं\n/prices - मूल्य\n/help - सहायता\n/calendar - कैलेंडर दिखाएं\n/book - अपॉइंटमेंट बुक करें",
            'direct': "💬 <b>सीधा:</b>\n• मूल्य पूछताछ\n• अपॉइंटमेंट अनुरोध\n• परामर्श\n• शिकायतें",
            'features': "💰 <b>मूल्य अनुमान</b> उपलब्ध!\n🛡️ <b>सुरक्षित डेटा प्रसंस्करण</b>\n📅 <b>कैलेंडर फ़ंक्शन</b>"
        },
        'calendar': {
            'title': "📅 <b>कैलेंडर & अपॉइंटमेंट</b>",
            'view': "🗓️ <b>वर्तमान महीना:</b>\n{calendar_view}",
            'booked_days': "❌ <b>बुक किए गए दिन:</b> {booked_days}",
            'instructions': "📝 <b>अपॉइंटमेंट बुक करें:</b>\n/book DD.MM.YYYY का उपयोग करें या मुझे अपनी पसंदीदा तिथि बताएं!",
            'no_bookings': "✅ <b>इस महीने कोई बुक किए गए दिन नहीं</b>"
        },
        'booking': {
            'success': "✅ <b>अपॉइंटमेंट सफलतापूर्वक बुक हो गया!</b>\n\n📅 <b>तिथि:</b> {date}\n👤 <b>ग्राहक:</b> {customer_name}\n📞 <b>संपर्क:</b> {contact_info}\n🛠️ <b>सेवा:</b> {service}",
            'already_booked': "❌ <b>तिथि पहले से बुक है!</b>\n\n📅 {date} पहले से ली गई है।\nकृपया कोई अन्य तिथि चुनें।",
            'invalid_date': "❌ <b>अमान्य तिथि!</b>\n\nकृपया प्रारूप का उपयोग करें: DD.MM.YYYY\nउदाहरण: /book 15.12.2024",
            'past_date': "❌ <b>बीती हुई तिथि!</b>\n\nकृपया भविष्य की तिथि चुनें।",
            'instructions': "📅 <b>अपॉइंटमेंट बुकिंग</b>\n\nउपयोग करें: /book DD.MM.YYYY\nउदाहरण: /book 15.12.2024\n\nया चैट में मुझे अपनी पसंदीदा तिथि बताएं!"
        }
    },
    'hu': {
        'start': {
            'welcome': "🥰 <b>Üdvözöljük a SHAWO Költöztetésnél!</b>",
            'hello': "👋 <b>Helló {name}</b>, én vagyok Leo, a digitális asszisztense! 😊",
            'services': "<b>📦 Segíthetek önnek:</b>\n• Teljes költöztetések\n• Bútor összeszerelés/szerelés\n• Felújítási munkák\n• Padlóburkolat\n• Végső takarítás",
            'features': "💰 <b>Azonnali árszámítások</b>\n🌍 <b>Többnyelvű szolgáltatás</b>\n🛡️ <b>Biztonságos adatfeldolgozás</b>\n📅 <b>Időpontfoglalás & Naptár</b>",
            'note': "<i>Csapatunk láthatja ezt a beszélgetést</i>",
            'question': "<b>Hogyan segíthetek? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Kapcsolat SHAWO Költöztetés</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Hét-Szom: 10:00-18:30",
            'languages': "🗣️ Német, Angol, Arab",
            'privacy': "🛡️ <b>Adatvédelmi információk:</b>\n• https://shawo-umzug-app.hu/adatvedelem\n• https://shawo-umzug-app.hu/adatkezeles"
        },
        'services': {
            'title': "🛠️ <b>Szolgáltatásaink</b>",
            'moves': "🏠 <b>Költöztetések:</b>\n• Teljes költöztetések\n• Bútorszolgáltatás\n• Egész Németország",
            'renovation': "🎨 <b>Felújítás:</b>\n• Festési munkák (Alapozó, Bevonat, Festés)\n• Gipszkarton\n• Tapétázás",
            'cleaning': "📦 <b>Padló & Takarítás:</b>\n• Laminált & PVC\n• Költözés utáni takarítás\n• Ablaktisztítás",
            'guarantee': "✅ <b>Rejtett költségek nélkül!</b>"
        },
        'prices': {
            'title': "💰 <b>ÁRPÉLDÁK (nem kötelező érvényű)</b>",
            'example': "📋 <b>Példa: 2 szobás költöztetés (60m²)</b>",
            'individual': "🎯 <b>Egyedi árak:</b>\n• 2 szobás költöztetés: 650-750 €\n• Alapozó: 5 €/m²\n• Bevonat/Festés: 12 €/m²\n• Takarítás: 4-6 €/m²\n• Laminált padló: 36,50 €/m²",
            'note': "<i>Személyes kalkulációhoz adjon meg részleteket!</i>"
        },
        'help': {
            'title': "⛑ <b>Segítség</b>",
            'commands': "📋 <b>Parancsok:</b>\n/start - Bot indítása\n/contact - Kapcsolat\n/services - Szolgáltatások\n/prices - Árak\n/help - Segítség\n/calendar - Naptár mutatása\n/book - Időpont foglalása",
            'direct': "💬 <b>Közvetlen:</b>\n• Árajánlat kérések\n• Időpont igénylések\n• Tanácsadás\n• Panaszok",
            'features': "💰 <b>Árbecslések</b> elérhető!\n🛡️ <b>Biztonságos adatfeldolgozás</b>\n📅 <b>Naptár funkció</b>"
        },
        'calendar': {
            'title': "📅 <b>Naptár & Időpontok</b>",
            'view': "🗓️ <b>Aktuális hónap:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Foglalt napok:</b> {booked_days}",
            'instructions': "📝 <b>Időpont foglalása:</b>\nHasználd a /book DD.MM.YYYY parancsot vagy mondd el a preferált dátumod!",
            'no_bookings': "✅ <b>Nincsenek foglalt napok ebben a hónapban</b>"
        },
        'booking': {
            'success': "✅ <b>Időpont sikeresen lefoglalva!</b>\n\n📅 <b>Dátum:</b> {date}\n👤 <b>Ügyfél:</b> {customer_name}\n📞 <b>Kapcsolat:</b> {contact_info}\n🛠️ <b>Szolgáltatás:</b> {service}",
            'already_booked': "❌ <b>Dátum már foglalt!</b>\n\n📅 {date} már foglalt.\nKérjük válasszon másik dátumot.",
            'invalid_date': "❌ <b>Érvénytelen dátum!</b>\n\nKérjük használja a formátumot: DD.MM.YYYY\nPélda: /book 15.12.2024",
            'past_date': "❌ <b>Múltbeli dátum!</b>\n\nKérjük válasszon jövőbeli dátumot.",
            'instructions': "📅 <b>Időpont Foglalás</b>\n\nHasználd: /book DD.MM.YYYY\nPélda: /book 15.12.2024\n\nVagy mondd el a preferált dátumod a chatben!"
        }
    },
    'id': {
        'start': {
            'welcome': "🥰 <b>Selamat datang di SHAWO Pindahan!</b>",
            'hello': "👋 <b>Halo {name}</b>, saya Leo, asisten digital Anda! 😊",
            'services': "<b>📦 Saya dapat membantu Anda dengan:</b>\n• Pindahan lengkap\n• Perakitan/pembongkaran furnitur\n• Pekerjaan renovasi\n• Pemasangan lantai\n• Pembersihan akhir",
            'features': "💰 <b>Perhitungan harga instan</b>\n🌍 <b>Layanan multibahasa</b>\n🛡️ <b>Pemrosesan data aman</b>\n📅 <b>Pemesanan janji temu & Kalender</b>",
            'note': "<i>Tim kami dapat melihat percakapan ini</i>",
            'question': "<b>Bagaimana saya bisa membantu Anda? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Kontak SHAWO Pindahan</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Sen-Sab: 10:00-18:30",
            'languages': "🗣️ Jerman, Inggris, Arab",
            'privacy': "🛡️ <b>Informasi Privasi:</b>\n• https://shawo-umzug-app.id/privasi\n• https://shawo-umzug-app.id/perlindungan-data"
        },
        'services': {
            'title': "🛠️ <b>Layanan Kami</b>",
            'moves': "🏠 <b>Pindahan:</b>\n• Pindahan lengkap\n• Layanan furnitur\n• Seluruh Jerman",
            'renovation': "🎨 <b>Renovasi:</b>\n• Pekerjaan cat (Primer, Pelapisan, Pengecatan)\n• Drywall\n• Wallpaper",
            'cleaning': "📦 <b>Lantai & Pembersihan:</b>\n• Laminasi & PVC\n• Pembersihan pasca pindahan\n• Pembersihan jendela",
            'guarantee': "✅ <b>Tidak ada biaya tersembunyi!</b>"
        },
        'prices': {
            'title': "💰 <b>CONTOH HARGA (tidak mengikat)</b>",
            'example': "📋 <b>Contoh: Pindahan 2 kamar (60m²)</b>",
            'individual': "🎯 <b>Harga individual:</b>\n• Pindahan 2 kamar: 650-750 €\n• Primer: 5 €/m²\n• Pelapisan/Pengecatan: 12 €/m²\n• Pembersihan: 4-6 €/m²\n• Lantai laminasi: 36,50 €/m²",
            'note': "<i>Untuk perhitungan pribadi berikan detail!</i>"
        },
        'help': {
            'title': "⛑ <b>Bantuan</b>",
            'commands': "📋 <b>Perintah:</b>\n/start - Mulai bot\n/contact - Kontak\n/services - Layanan\n/prices - Harga\n/help - Bantuan\n/calendar - Tampilkan kalender\n/book - Pesan janji temu",
            'direct': "💬 <b>Langsung:</b>\n• Pertanyaan harga\n• Permintaan janji temu\n• Konsultasi\n• Keluhan",
            'features': "💰 <b>Perkiraan harga</b> tersedia!\n🛡️ <b>Pemrosesan data aman</b>\n📅 <b>Fungsi kalender</b>"
        },
        'calendar': {
            'title': "📅 <b>Kalender & Janji Temu</b>",
            'view': "🗓️ <b>Bulan ini:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Hari yang dipesan:</b> {booked_days}",
            'instructions': "📝 <b>Pesan janji temu:</b>\nGunakan /book DD.MM.YYYY atau beri tahu saya tanggal pilihan Anda!",
            'no_bookings': "✅ <b>Tidak ada hari yang dipesan bulan ini</b>"
        },
        'booking': {
            'success': "✅ <b>Janji temu berhasil dipesan!</b>\n\n📅 <b>Tanggal:</b> {date}\n👤 <b>Pelanggan:</b> {customer_name}\n📞 <b>Kontak:</b> {contact_info}\n🛠️ <b>Layanan:</b> {service}",
            'already_booked': "❌ <b>Tanggal sudah dipesan!</b>\n\n📅 {date} sudah diambil.\nSilakan pilih tanggal lain.",
            'invalid_date': "❌ <b>Tanggal tidak valid!</b>\n\nSilakan gunakan format: DD.MM.YYYY\nContoh: /book 15.12.2024",
            'past_date': "❌ <b>Tanggal masa lalu!</b>\n\nSilakan pilih tanggal mendatang.",
            'instructions': "📅 <b>Pemesanan Janji Temu</b>\n\nGunakan: /book DD.MM.YYYY\nContoh: /book 15.12.2024\n\nAtau beri tahu saya tanggal pilihan Anda di chat!"
        }
    },
    'ms': {
        'start': {
            'welcome': "🥰 <b>Selamat datang ke SHAWO Pindahan!</b>",
            'hello': "👋 <b>Helo {name}</b>, saya Leo, pembantu digital anda! 😊",
            'services': "<b>📦 Saya boleh membantu anda dengan:</b>\n• Pindahan lengkap\n• Pemasangan/pembongkaran perabot\n• Kerja-kerja renovasi\n• Pemasangan lantai\n• Pembersihan akhir",
            'features': "💰 <b>Pengiraan harga serta-merta</b>\n🌍 <b>Perkhidmatan pelbagai bahasa</b>\n🛡️ <b>Pemprosesan data selamat</b>\n📅 <b>Tempahan janji temu & Kalendar</b>",
            'note': "<i>Pasukan kami boleh melihat perbualan ini</i>",
            'question': "<b>Bagaimana saya boleh membantu anda? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Hubungan SHAWO Pindahan</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Isn-Sab: 10:00-18:30",
            'languages': "🗣️ Jerman, Inggeris, Arab",
            'privacy': "🛡️ <b>Maklumat Privasi:</b>\n• https://shawo-umzug-app.my/privasi\n• https://shawo-umzug-app.my/perlindungan-data"
        },
        'services': {
            'title': "🛠️ <b>Perkhidmatan Kami</b>",
            'moves': "🏠 <b>Pindahan:</b>\n• Pindahan lengkap\n• Perkhidmatan perabot\n• Seluruh Jerman",
            'renovation': "🎨 <b>Renovasi:</b>\n• Kerja-kerja cat (Primer, Salutan, Pengecatan)\n• Dinding kering\n• Kertas dinding",
            'cleaning': "📦 <b>Lantai & Pembersihan:</b>\n• Laminat & PVC\n• Pembersihan pasca pindahan\n• Pembersihan tingkap",
            'guarantee': "✅ <b>Tiada kos tersembunyi!</b>"
        },
        'prices': {
            'title': "💰 <b>CONTOH HARGA (tidak mengikat)</b>",
            'example': "📋 <b>Contoh: Pindahan 2 bilik (60m²)</b>",
            'individual': "🎯 <b>Harga individu:</b>\n• Pindahan 2 bilik: 650-750 €\n• Primer: 5 €/m²\n• Salutan/Pengecatan: 12 €/m²\n• Pembersihan: 4-6 €/m²\n• Lantai laminat: 36,50 €/m²",
            'note': "<i>Untuk pengiraan peribadi berikan butiran!</i>"
        },
        'help': {
            'title': "⛑ <b>Bantuan</b>",
            'commands': "📋 <b>Arahan:</b>\n/start - Mulakan bot\n/contact - Hubungan\n/services - Perkhidmatan\n/prices - Harga\n/help - Bantuan\n/calendar - Tunjukkan kalendar\n/book - Tempah janji temu",
            'direct': "💬 <b>Langsung:</b>\n• Pertanyaan harga\n• Permintaan janji temu\n• Perundingan\n• Aduan",
            'features': "💰 <b>Anggaran harga</b> tersedia!\n🛡️ <b>Pemprosesan data selamat</b>\n📅 <b>Fungsi kalendar</b>"
        },
        'calendar': {
            'title': "📅 <b>Kalendar & Janji Temu</b>",
            'view': "🗓️ <b>Bulan semasa:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Hari ditempah:</b> {booked_days}",
            'instructions': "📝 <b>Tempah janji temu:</b>\nGuna /book DD.MM.YYYY atau beritahu saya tarikh pilihan anda!",
            'no_bookings': "✅ <b>Tiada hari ditempah bulan ini</b>"
        },
        'booking': {
            'success': "✅ <b>Janji temu berjaya ditempah!</b>\n\n📅 <b>Tarikh:</b> {date}\n👤 <b>Pelanggan:</b> {customer_name}\n📞 <b>Hubungan:</b> {contact_info}\n🛠️ <b>Perkhidmatan:</b> {service}",
            'already_booked': "❌ <b>Tarikh sudah ditempah!</b>\n\n📅 {date} sudah diambil.\nSila pilih tarikh lain.",
            'invalid_date': "❌ <b>Tarikh tidak sah!</b>\n\nSila guna format: DD.MM.YYYY\nContoh: /book 15.12.2024",
            'past_date': "❌ <b>Tarikh lalu!</b>\n\nSila pilih tarikh masa depan.",
            'instructions': "📅 <b>Tempahan Janji Temu</b>\n\nGuna: /book DD.MM.YYYY\nContoh: /book 15.12.2024\n\nAtau beritahu saya tarikh pilihan anda dalam chat!"
        }
    },
    'no': {
        'start': {
            'welcome': "🥰 <b>Velkommen til SHAWO Flyttetjenester!</b>",
            'hello': "👋 <b>Hei {name}</b>, jeg er Leo, din digitale assistent! 😊",
            'services': "<b>📦 Jeg kan hjelpe deg med:</b>\n• Komplette flyttinger\n• Møbelmontering/demontering\n• Renoveringsarbeid\n• Gulvlegging\n• Sluttvask",
            'features': "💰 <b>Umiddelbare priskalkulasjoner</b>\n🌍 <b>Flerspråklig service</b>\n🛡️ <b>Sikker databehandling</b>\n📅 <b>Avtalebestilling & Kalender</b>",
            'note': "<i>Vårt team kan se denne samtalen</i>",
            'question': "<b>Hvordan kan jeg hjelpe deg? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Kontakt SHAWO Flyttetjenester</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Man-Lør: 10:00-18:30",
            'languages': "🗣️ Tysk, Engelsk, Arabisk",
            'privacy': "🛡️ <b>Personverninformasjon:</b>\n• https://shawo-umzug-app.no/personvern\n• https://shawo-umzug-app.no/databeskyttelse"
        },
        'services': {
            'title': "🛠️ <b>Våre Tjenester</b>",
            'moves': "🏠 <b>Flyttinger:</b>\n• Komplette flyttinger\n• Møbelservice\n• Hele Tyskland",
            'renovation': "🎨 <b>Renovering:</b>\n• Malingarbeid (Grunning, Belägg, Maling)\n• Gipsplater\n• Tapetsering",
            'cleaning': "📦 <b>Gulv & Rengjøring:</b>\n• Laminat & PVC\n• Flytterengjøring\n• Vinduspussing",
            'guarantee': "✅ <b>Ingen skjulte kostnader!</b>"
        },
        'prices': {
            'title': "💰 <b>PRISEKSEMPLER (ubindende)</b>",
            'example': "📋 <b>Eksempel: 2-roms flytting (60m²)</b>",
            'individual': "🎯 <b>Individuelle priser:</b>\n• 2-roms flytting: 650-750 €\n• Grunning: 5 €/m²\n• Belägg/Maling: 12 €/m²\n• Rengjøring: 4-6 €/m²\n• Laminatgulv: 36,50 €/m²",
            'note': "<i>For personlig kalkyle oppgi detaljer!</i>"
        },
        'help': {
            'title': "⛑ <b>Hjelp</b>",
            'commands': "📋 <b>Kommandoer:</b>\n/start - Start bot\n/contact - Kontakt\n/services - Tjenester\n/prices - Priser\n/help - Hjelp\n/calendar - Vis kalender\n/book - Bestill time",
            'direct': "💬 <b>Direkte:</b>\n• Prisforespørsler\n• Timeforespørsler\n• Rådgivning\n• Klager",
            'features': "💰 <b>Prisestimater</b> tilgjengelig!\n🛡️ <b>Sikker databehandling</b>\n📅 <b>Kalenderfunksjon</b>"
        },
        'calendar': {
            'title': "📅 <b>Kalender & Avtaler</b>",
            'view': "🗓️ <b>Gjeldende måned:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Bestilte dager:</b> {booked_days}",
            'instructions': "📝 <b>Bestill time:</b>\nBruk /book DD.MM.YYYY eller fortell meg ønsket dato!",
            'no_bookings': "✅ <b>Ingen bestilte dager denne måneden</b>"
        },
        'booking': {
            'success': "✅ <b>Avtale vellykket bestilt!</b>\n\n📅 <b>Dato:</b> {date}\n👤 <b>Kunde:</b> {customer_name}\n📞 <b>Kontakt:</b> {contact_info}\n🛠️ <b>Tjeneste:</b> {service}",
            'already_booked': "❌ <b>Dato allerede bestilt!</b>\n\n📅 {date} er allerede opptatt.\nVennligst velg en annen dato.",
            'invalid_date': "❌ <b>Ugyldig dato!</b>\n\nVennligst bruk format: DD.MM.YYYY\nEksempel: /book 15.12.2024",
            'past_date': "❌ <b>Passert dato!</b>\n\nVennligst velg en fremtidig dato.",
            'instructions': "📅 <b>Timebestilling</b>\n\nBruk: /book DD.MM.YYYY\nEksempel: /book 15.12.2024\n\nEller fortell meg ønsket dato i chatten!"
        }
    },
    'fi': {
        'start': {
            'welcome': "🥰 <b>Tervetuloa SHAWO Muuttoihin!</b>",
            'hello': "👋 <b>Hei {name}</b>, olen Leo, digitaalinen avustajasi! 😊",
            'services': "<b>📦 Voin auttaa sinua:</b>\n• Täydellisissä muutoissa\n• Huonekalujen kokoamisessa/purkamisessa\n• Kunnostustöissä\n• Lattian asennuksessa\n• Lopullisessa siivouksessa",
            'features': "💰 <b>Hetkelliset hinnanlaskelmat</b>\n🌍 <b>Monikielinen palvelu</b>\n🛡️ <b>Turvallinen tietojen käsittely</b>\n📅 <b>Ajanvaraus & Kalenteri</b>",
            'note': "<i>Tiimimme voi nähdä tämän keskustelun</i>",
            'question': "<b>Kuinka voin auttaa sinua? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Yhteystiedot SHAWO Muutot</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Ma-La: 10:00-18:30",
            'languages': "🗣️ Saksa, Englanti, Arabia",
            'privacy': "🛡️ <b>Tietosuojatiedot:</b>\n• https://shawo-umzug-app.fi/tietosuoja\n• https://shawo-umzug-app.fi/tietojenkasittely"
        },
        'services': {
            'title': "🛠️ <b>Palvelumme</b>",
            'moves': "🏠 <b>Muutot:</b>\n• Täydelliset muutot\n• Huonekalupalvelu\n• Koko Saksa",
            'renovation': "🎨 <b>Kunnostus:</b>\n• Maalaus työt (Pohjamaali, Päällyste, Maalaus)\n• Kipsilevy\n• Tapetointi",
            'cleaning': "📦 <b>Lattia & Siivous:</b>\n• Laminetti & PVC\n• Muuttosiivous\n• Ikkunoiden puhdistus",
            'guarantee': "✅ <b>Ei piilokustannuksia!</b>"
        },
        'prices': {
            'title': "💰 <b>HINNA ESIMERKKEJÄ (sitova)</b>",
            'example': "📋 <b>Esimerkki: 2 huoneen muutto (60m²)</b>",
            'individual': "🎯 <b>Yksilölliset hinnat:</b>\n• 2 huoneen muutto: 650-750 €\n• Pohjamaali: 5 €/m²\n• Päällyste/Maalaus: 12 €/m²\n• Siivous: 4-6 €/m²\n• Laminattilattia: 36,50 €/m²",
            'note': "<i>Henkilökohtaista laskelmaa varten anna yksityiskohdat!</i>"
        },
        'help': {
            'title': "⛑ <b>Apua</b>",
            'commands': "📋 <b>Komennot:</b>\n/start - Käynnistä botti\n/contact - Yhteystiedot\n/services - Palvelut\n/prices - Hinnat\n/help - Apua\n/calendar - Näytä kalenteri\n/book - Varaa aika",
            'direct': "💬 <b>Suoraan:</b>\n• Hintakyselyt\n• Aikavaraukset\n• Neuvonta\n• Valitukset",
            'features': "💰 <b>Hinta-arvio</b> saatavilla!\n🛡️ <b>Turvallinen tietojen käsittely</b>\n📅 <b>Kalenteritoiminto</b>"
        },
        'calendar': {
            'title': "📅 <b>Kalenteri & Tapaamiset</b>",
            'view': "🗓️ <b>Nykyinen kuukausi:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Varatut päivät:</b> {booked_days}",
            'instructions': "📝 <b>Varaa aika:</b>\nKäytä /book DD.MM.YYYY tai kerro minulle toivottu päivämäärä!",
            'no_bookings': "✅ <b>Ei varattuja päiviä tässä kuussa</b>"
        },
        'booking': {
            'success': "✅ <b>Aika varattu onnistuneesti!</b>\n\n📅 <b>Päivämäärä:</b> {date}\n👤 <b>Asiakas:</b> {customer_name}\n📞 <b>Yhteystiedot:</b> {contact_info}\n🛠️ <b>Palvelu:</b> {service}",
            'already_booked': "❌ <b>Päivämäärä on jo varattu!</b>\n\n📅 {date} on jo varattu.\nOle hyvä ja valitse toinen päivämäärä.",
            'invalid_date': "❌ <b>Virheellinen päivämäärä!</b>\n\nKäytä muotoa: DD.MM.YYYY\nEsimerkki: /book 15.12.2024",
            'past_date': "❌ <b>Menneisyyden päivämäärä!</b>\n\nOle hyvä ja valitse tuleva päivämäärä.",
            'instructions': "📅 <b>Ajanvaraus</b>\n\nKäytä: /book DD.MM.YYYY\nEsimerkki: /book 15.12.2024\n\nTai kerro minulle toivottu päivämäärä chatissa!"
        }
    },
    'th': {
        'start': {
            'welcome': "🥰 <b>ยินดีต้อนรับสู่ SHAWO การย้าย!</b>",
            'hello': "👋 <b>สวัสดี {name}</b>, ฉันคือ ลีโอ, ผู้ช่วยดิจิทัลของคุณ! 😊",
            'services': "<b>📦 ฉันสามารถช่วยคุณด้วย:</b>\n• การย้ายที่สมบูรณ์\n• การประกอบ/ถอดประกอบเฟอร์นิเจอร์\n• งานปรับปรุง\n• การติดตั้งพื้น\n• การทำความสะอาดครั้งสุดท้าย",
            'features': "💰 <b>การคำนวณราคาทันที</b>\n🌍 <b>บริการหลายภาษา</b>\n🛡️ <b>การประมวลผลข้อมูลที่ปลอดภัย</b>\n📅 <b>การจองนัดหมาย & ปฏิทิน</b>",
            'note': "<i>ทีมของเราสามารถดูการสนทนานี้ได้</i>",
            'question': "<b>ฉันสามารถช่วยคุณได้อย่างไร? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>ติดต่อ SHAWO การย้าย</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 จ-ส: 10:00-18:30",
            'languages': "🗣️ เยอรมัน, อังกฤษ, อาหรับ",
            'privacy': "🛡️ <b>ข้อมูลความเป็นส่วนตัว:</b>\n• https://shawo-umzug-app.th/ความเป็นส่วนตัว\n• https://shawo-umzug-app.th/การปกป้องข้อมูล"
        },
        'services': {
            'title': "🛠️ <b>บริการของเรา</b>",
            'moves': "🏠 <b>การย้าย:</b>\n• การย้ายที่สมบูรณ์\n• บริการเฟอร์นิเจอร์\n• ทั่วทั้งเยอรมนี",
            'renovation': "🎨 <b>การปรับปรุง:</b>\n• งานสี (ไพรเมอร์, การเคลือบ, การทาสี)\n•  Drywall\n•  การติดวอลล์เปเปอร์",
            'cleaning': "📦 <b>พื้น & การทำความสะอาด:</b>\n•  ลามิเนต & PVC\n•  การทำความสะอาดหลังการย้าย\n•  การทำความสะอาดหน้าต่าง",
            'guarantee': "✅ <b>ไม่มีค่าใช้จ่ายแอบแฝง!</b>"
        },
        'prices': {
            'title': "💰 <b>ตัวอย่างราคา (ไม่ผูกพัน)</b>",
            'example': "📋 <b>ตัวอย่าง: การย้าย 2 ห้อง (60m²)</b>",
            'individual': "🎯 <b>ราคารายบุคคล:</b>\n• การย้าย 2 ห้อง: 650-750 €\n• ไพรเมอร์: 5 €/m²\n• การเคลือบ/การทาสี: 12 €/m²\n• การทำความสะอาด: 4-6 €/m²\n• พื้นลามิเนต: 36,50 €/m²",
            'note': "<i>สำหรับการคำนวณส่วนตัวโปรดให้รายละเอียด!</i>"
        },
        'help': {
            'title': "⛑ <b>ความช่วยเหลือ</b>",
            'commands': "📋 <b>คำสั่ง:</b>\n/start - เริ่มบอท\n/contact - ติดต่อ\n/services - บริการ\n/prices - ราคา\n/help - ความช่วยเหลือ\n/calendar - แสดงปฏิทิน\n/book - จองนัดหมาย",
            'direct': "💬 <b>โดยตรง:</b>\n• การสอบถามราคา\n• การขอรับนัดหมาย\n• การให้คำปรึกษา\n• การร้องเรียน",
            'features': "💰 <b>การประมาณราคา</b> พร้อมใช้งาน!\n🛡️ <b>การประมวลผลข้อมูลที่ปลอดภัย</b>\n📅 <b>ฟังก์ชันปฏิทิน</b>"
        },
        'calendar': {
            'title': "📅 <b>ปฏิทิน & นัดหมาย</b>",
            'view': "🗓️ <b>เดือนปัจจุบัน:</b>\n{calendar_view}",
            'booked_days': "❌ <b>วันที่ถูกจอง:</b> {booked_days}",
            'instructions': "📝 <b>จองนัดหมาย:</b>\nใช้ /book DD.MM.YYYY หรือบอกฉันวันที่ที่คุณต้องการ!",
            'no_bookings': "✅ <b>ไม่มีวันที่ถูกจองในเดือนนี้</b>"
        },
        'booking': {
            'success': "✅ <b>จองนัดหมายสำเร็จแล้ว!</b>\n\n📅 <b>วันที่:</b> {date}\n👤 <b>ลูกค้า:</b> {customer_name}\n📞 <b>ติดต่อ:</b> {contact_info}\n🛠️ <b>บริการ:</b> {service}",
            'already_booked': "❌ <b>วันที่ถูกจองแล้ว!</b>\n\n📅 {date} ถูกจองแล้ว\nกรุณาเลือกวันที่อื่น",
            'invalid_date': "❌ <b>วันที่ไม่ถูกต้อง!</b>\n\nกรุณาใช้รูปแบบ: DD.MM.YYYY\nตัวอย่าง: /book 15.12.2024",
            'past_date': "❌ <b>วันที่ผ่านมาแล้ว!</b>\n\nกรุณาเลือกวันที่ในอนาคต",
            'instructions': "📅 <b>การจองนัดหมาย</b>\n\nใช้: /book DD.MM.YYYY\nตัวอย่าง: /book 15.12.2024\n\nหรือบอกฉันวันที่ที่คุณต้องการในแชท!"
        }
    },
    'vi': {
        'start': {
            'welcome': "🥰 <b>Chào mừng đến với SHAWO Chuyển nhà!</b>",
            'hello': "👋 <b>Xin chào {name}</b>, tôi là Leo, trợ lý kỹ thuật số của bạn! 😊",
            'services': "<b>📦 Tôi có thể giúp bạn:</b>\n• Chuyển nhà trọn gói\n• Lắp ráp/tháo dỡ nội thất\n• Công việc cải tạo\n• Lắp đặt sàn\n• Vệ sinh cuối cùng",
            'features': "💰 <b>Tính giá ngay lập tức</b>\n🌍 <b>Dịch vụ đa ngôn ngữ</b>\n🛡️ <b>Xử lý dữ liệu an toàn</b>\n📅 <b>Đặt lịch hẹn & Lịch</b>",
            'note': "<i>Đội ngũ của chúng tôi có thể xem cuộc trò chuyện này</i>",
            'question': "<b>Tôi có thể giúp gì cho bạn? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Liên hệ SHAWO Chuyển nhà</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 T2-T7: 10:00-18:30",
            'languages': "🗣️ Tiếng Đức, Tiếng Anh, Tiếng Ả Rập",
            'privacy': "🛡️ <b>Thông tin bảo mật:</b>\n• https://shawo-umzug-app.vn/quyen-rieng-tu\n• https://shawo-umzug-app.vn/bao-ve-du-lieu"
        },
        'services': {
            'title': "🛠️ <b>Dịch Vụ Của Chúng Tôi</b>",
            'moves': "🏠 <b>Chuyển nhà:</b>\n• Chuyển nhà trọn gói\n• Dịch vụ nội thất\n• Toàn nước Đức",
            'renovation': "🎨 <b>Cải tạo:</b>\n• Công việc sơn (Lớp lót, Lớp phủ, Sơn)\n• Tường thạch cao\n• Dán giấy tường",
            'cleaning': "📦 <b>Sàn & Vệ sinh:</b>\n• Sàn gỗ & PVC\n• Vệ sinh sau khi chuyển nhà\n• Vệ sinh cửa sổ",
            'guarantee': "✅ <b>Không có chi phí ẩn!</b>"
        },
        'prices': {
            'title': "💰 <b>VÍ DỤ GIÁ (không ràng buộc)</b>",
            'example': "📋 <b>Ví dụ: Chuyển nhà 2 phòng (60m²)</b>",
            'individual': "🎯 <b>Giá riêng lẻ:</b>\n• Chuyển nhà 2 phòng: 650-750 €\n• Lớp lót: 5 €/m²\n• Lớp phủ/Sơn: 12 €/m²\n• Vệ sinh: 4-6 €/m²\n• Sàn gỗ: 36,50 €/m²",
            'note': "<i>Để tính toán cá nhân vui lòng cung cấp chi tiết!</i>"
        },
        'help': {
            'title': "⛑ <b>Trợ giúp</b>",
            'commands': "📋 <b>Lệnh:</b>\n/start - Bắt đầu bot\n/contact - Liên hệ\n/services - Dịch vụ\n/prices - Giá\n/help - Trợ giúp\n/calendar - Hiển thị lịch\n/book - Đặt lịch hẹn",
            'direct': "💬 <b>Trực tiếp:</b>\n• Yêu cầu báo giá\n• Yêu cầu đặt lịch\n• Tư vấn\n• Khiếu nại",
            'features': "💰 <b>Ước tính giá</b> có sẵn!\n🛡️ <b>Xử lý dữ liệu an toàn</b>\n📅 <b>Chức năng lịch</b>"
        },
        'calendar': {
            'title': "📅 <b>Lịch & Cuộc hẹn</b>",
            'view': "🗓️ <b>Tháng hiện tại:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Ngày đã đặt:</b> {booked_days}",
            'instructions': "📝 <b>Đặt lịch hẹn:</b>\nSử dụng /book DD.MM.YYYY hoặc cho tôi biết ngày bạn muốn!",
            'no_bookings': "✅ <b>Không có ngày nào được đặt trong tháng này</b>"
        },
        'booking': {
            'success': "✅ <b>Đặt lịch hẹn thành công!</b>\n\n📅 <b>Ngày:</b> {date}\n👤 <b>Khách hàng:</b> {customer_name}\n📞 <b>Liên hệ:</b> {contact_info}\n🛠️ <b>Dịch vụ:</b> {service}",
            'already_booked': "❌ <b>Ngày đã được đặt!</b>\n\n📅 {date} đã được đặt.\nVui lòng chọn ngày khác.",
            'invalid_date': "❌ <b>Ngày không hợp lệ!</b>\n\nVui lòng sử dụng định dạng: DD.MM.YYYY\nVí dụ: /book 15.12.2024",
            'past_date': "❌ <b>Ngày trong quá khứ!</b>\n\nVui lòng chọn ngày trong tương lai.",
            'instructions': "📅 <b>Đặt Lịch Hẹn</b>\n\nSử dụng: /book DD.MM.YYYY\nVí dụ: /book 15.12.2024\n\nHoặc cho tôi biết ngày bạn muốn trong trò chuyện!"
        }
    },
    'ro': {
        'start': {
            'welcome': "🥰 <b>Bun venit la SHAWO Mutări!</b>",
            'hello': "👋 <b>Bună {name}</b>, sunt Leo, asistentul tău digital! 😊",
            'services': "<b>📦 Te pot ajuta cu:</b>\n• Mutări complete\n• Asamblare/Dezasamblare mobilă\n• Lucrări de renovare\n• Instalare pardoseală\n• Curățenie finală",
            'features': "💰 <b>Calcule de preț instantanee</b>\n🌍 <b>Serviciu multilingv</b>\n🛡️ <b>Prelucrare sigură a datelor</b>\n📅 <b>Rezervare programări & Calendar</b>",
            'note': "<i>Echipa noastră poate vedea această conversație</i>",
            'question': "<b>Cum vă pot ajuta? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Contact SHAWO Mutări</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Lun-Sâm: 10:00-18:30",
            'languages': "🗣️ Germană, Engleză, Arabă",
            'privacy': "🛡️ <b>Informații privind confidențialitatea:</b>\n• https://shawo-umzug-app.ro/confidentialitate\n• https://shawo-umzug-app.ro/protectia-datelor"
        },
        'services': {
            'title': "🛠️ <b>Serviciile Noastre</b>",
            'moves': "🏠 <b>Mutări:</b>\n• Mutări complete\n• Serviciu mobilă\n• Toată Germania",
            'renovation': "🎨 <b>Renovare:</b>\n• Lucrări de vopsire (Grund, Acoperire, Vopsire)\n• Perete de gips-carton\n• Tapetare",
            'cleaning': "📦 <b>Pardoseală & Curățenie:</b>\n• Laminat & PVC\n• Curățenie după mutare\n• Curățenie geamuri",
            'guarantee': "✅ <b>Fără costuri ascunse!</b>"
        },
        'prices': {
            'title': "💰 <b>EXEMPLE DE PREȚ (neangajante)</b>",
            'example': "📋 <b>Exemplu: Mutare 2 camere (60m²)</b>",
            'individual': "🎯 <b>Prețuri individuale:</b>\n• Mutare 2 camere: 650-750 €\n• Grund: 5 €/m²\n• Acoperire/Vopsire: 12 €/m²\n• Curățenie: 4-6 €/m²\n• Pardoseală laminată: 36,50 €/m²",
            'note': "<i>Pentru calcul personal oferiți detalii!</i>"
        },
        'help': {
            'title': "⛑ <b>Ajutor</b>",
            'commands': "📋 <b>Comenzi:</b>\n/start - Pornește botul\n/contact - Contact\n/services - Servicii\n/prices - Prețuri\n/help - Ajutor\n/calendar - Afișează calendar\n/book - Rezervă programare",
            'direct': "💬 <b>Direct:</b>\n• Cereri de preț\n• Cereri de programări\n• Consultanță\n• Plângeri",
            'features': "💰 <b>Estimări de preț</b> disponibile!\n🛡️ <b>Prelucrare sigură a datelor</b>\n📅 <b>Funcție calendar</b>"
        },
        'calendar': {
            'title': "📅 <b>Calendar & Programări</b>",
            'view': "🗓️ <b>Luna curentă:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Zile rezervate:</b> {booked_days}",
            'instructions': "📝 <b>Rezervă programare:</b>\nFolosește /book DD.MM.YYYY sau spune-mi data preferată!",
            'no_bookings': "✅ <b>Nicio zi rezervată această lună</b>"
        },
        'booking': {
            'success': "✅ <b>Programare rezervată cu succes!</b>\n\n📅 <b>Data:</b> {date}\n👤 <b>Client:</b> {customer_name}\n📞 <b>Contact:</b> {contact_info}\n🛠️ <b>Serviciu:</b> {service}",
            'already_booked': "❌ <b>Data este deja rezervată!</b>\n\n📅 {date} este deja ocupată.\nVă rugăm alegeți altă dată.",
            'invalid_date': "❌ <b>Dată invalidă!</b>\n\nVă rugăm folosiți formatul: DD.MM.YYYY\nExemplu: /book 15.12.2024",
            'past_date': "❌ <b>Dată din trecut!</b>\n\nVă rugăm alegeți o dată viitoare.",
            'instructions': "📅 <b>Rezervare Programare</b>\n\nFolosește: /book DD.MM.YYYY\nExemplu: /book 15.12.2024\n\nSau spune-mi data preferată în chat!"
        }
    },
    'ca': {
        'start': {
            'welcome': "🥰 <b>Benvingut/da a SHAWO Mudances!</b>",
            'hello': "👋 <b>Hola {name}</b>, sóc en Leo, el teu assistent digital! 😊",
            'services': "<b>📦 Et puc ajudar amb:</b>\n• Mudances completes\n• Muntatge/desmuntatge de mobles\n• Obres de renovació\n• Instal·lació de sòls\n• Neteja final",
            'features': "💰 <b>Càlculs de preus instantanis</b>\n🌍 <b>Servei multilingüe</b>\n🛡️ <b>Processament segur de dades</b>\n📅 <b>Reserva de cites & Calendari</b>",
            'note': "<i>El nostre equip pot veure aquesta conversa</i>",
            'question': "<b>Com et puc ajudar? 😉</b>"
        },
        'contact': {
            'title': "📞 <b>Contacte SHAWO Mudances</b>",
            'address': "📍 Wörther Straße 32, 13595 Berlin",
            'phone': "📱 +49 176 72407732",
            'whatsapp': "📧 WhatsApp: +49 176 72407732",
            'email': "✉️ shawo.info.betrieb@gmail.com",
            'website': "🌐 https://shawo-umzug-app.de",
            'hours': "🕒 Dll-Dis: 10:00-18:30",
            'languages': "🗣️ Alemany, Anglès, Àrab",
            'privacy': "🛡️ <b>Informació de privadesa:</b>\n• https://shawo-umzug-app.cat/privadesa\n• https://shawo-umzug-app.cat/proteccio-dades"
        },
        'services': {
            'title': "🛠️ <b>Els Nostres Serveis</b>",
            'moves': "🏠 <b>Mudances:</b>\n• Mudances completes\n• Servei de mobles\n• Tota Alemanya",
            'renovation': "🎨 <b>Renovació:</b>\n• Treballs de pintura (Imprimació, Revestiment, Pintura)\n• Cartró-guix\n• Empaperat",
            'cleaning': "📦 <b>Sòl & Neteja:</b>\n• Laminat & PVC\n• Neteja post-mudança\n• Neteja de finestres",
            'guarantee': "✅ <b>Sense costos ocults!</b>"
        },
        'prices': {
            'title': "💰 <b>EXEMPLES DE PREUS (no vinculants)</b>",
            'example': "📋 <b>Exemple: Mudança 2 habitacions (60m²)</b>",
            'individual': "🎯 <b>Preus individuals:</b>\n• Mudança 2 habitacions: 650-750 €\n• Imprimació: 5 €/m²\n• Revestiment/Pintura: 12 €/m²\n• Neteja: 4-6 €/m²\n• Sòl laminat: 36,50 €/m²",
            'note': "<i>Per a càlcul personal proporciona detalls!</i>"
        },
        'help': {
            'title': "⛑ <b>Ajuda</b>",
            'commands': "📋 <b>Ordres:</b>\n/start - Inicia el bot\n/contact - Contacte\n/services - Serveis\n/prices - Preus\n/help - Ajuda\n/calendar - Mostra calendari\n/book - Reserva cita",
            'direct': "💬 <b>Directe:</b>\n• Consultes de preus\n• Sol·licituds de cites\n• Assessorament\n• Queixes",
            'features': "💰 <b>Pressupostos</b> disponibles!\n🛡️ <b>Processament segur de dades</b>\n📅 <b>Funció calendari</b>"
        },
        'calendar': {
            'title': "📅 <b>Calendari & Cites</b>",
            'view': "🗓️ <b>Mes actual:</b>\n{calendar_view}",
            'booked_days': "❌ <b>Dies reservats:</b> {booked_days}",
            'instructions': "📝 <b>Reserva cita:</b>\nUtilitza /book DD.MM.YYYY o digues-me la teva data preferida!",
            'no_bookings': "✅ <b>Cap dia reservat aquest mes</b>"
        },
        'booking': {
            'success': "✅ <b>Cita reservada amb èxit!</b>\n\n📅 <b>Data:</b> {date}\n👤 <b>Client:</b> {customer_name}\n📞 <b>Contacte:</b> {contact_info}\n🛠️ <b>Servei:</b> {service}",
            'already_booked': "❌ <b>Data ja reservada!</b>\n\n📅 {date} ja està ocupada.\nSi us plau tria una altra data.",
            'invalid_date': "❌ <b>Data invàlida!</b>\n\nSi us plau utilitza el format: DD.MM.YYYY\nExemple: /book 15.12.2024",
            'past_date': "❌ <b>Data passada!</b>\n\nSi us plau tria una data futura.",
            'instructions': "📅 <b>Reserva de Cita</b>\n\nUtilitza: /book DD.MM.YYYY\nExemple: /book 15.12.2024\n\nO digues-me la teva data preferida al xat!"
        }
    }
}

# 🔐 SICHERHEITSKLASSE
class SecureBot:
    def __init__(self):
        self.config = None
        self.model = None
        
    def decrypt_config(self, key):
        """Entschlüsselt die Konfiguration"""
        try:
            cipher_suite = Fernet(key.encode())
            with open('config.enc', 'rb') as f:
                encrypted = f.read()
            decrypted = cipher_suite.decrypt(encrypted).decode()
            
            for line in decrypted.splitlines():
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
            
            return True
        except Exception as e:
            print(f"❌ Entschlüsselungsfehler: {e}")
            return False
    
    def init_bot(self):
        """Initialisiert den Bot mit entschlüsselten Daten"""
        try:
            load_dotenv()
            TOKEN = os.getenv("TOKEN")
            GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
            ADMIN_CHAT_ID =# "your group or chat ID"
            
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
            
            return TOKEN, ADMIN_CHAT_ID, self.model
        except Exception as e:
            print(f"❌ Initialisierungsfehler: {e}")
            return None, None, None

    def run(self):
        """Startet den geschützten Bot"""
        print("🔐 SHAWO Bot - Professionelle Preisintegration & Kalender")
        print("=" * 50)
        
        try:
            with open('key.txt', 'r') as f:
                key = f.read().strip()
        except FileNotFoundError:
            print("❌ key.txt nicht gefunden!")
            return
        
        if not self.decrypt_config(key):
            print("❌ Falscher Schlüssel.")
            return
        
        TOKEN, ADMIN_CHAT_ID, model = self.init_bot()
        if not TOKEN:
            print("❌ Fehler bei der Initialisierung.")
            return
    
        print("✅ Bot wird gestartet...")
        start_bot(TOKEN, ADMIN_CHAT_ID, model)

# 📅 KALENDER-MANAGEMENT SYSTEM
class CalendarManager:
    def __init__(self):
        self.init_calendar_db()
    
    def init_calendar_db(self):
        """Initialisiert die Kalender-Datenbank"""
        with sqlite3.connect("storage.db") as con:
            cur = con.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    customer_name TEXT NOT NULL,
                    contact_info TEXT NOT NULL,
                    service TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    created_at TEXT,
                    UNIQUE(date)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS blocked_days (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    reason TEXT,
                    blocked_by TEXT,
                    created_at TEXT,
                    UNIQUE(date)
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(date)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_blocked_days_date ON blocked_days(date)")
            con.commit()
    
    def is_date_available(self, date_str: str) -> bool:
        """Prüft ob ein Datum verfügbar ist"""
        with sqlite3.connect("storage.db") as con:
            cur = con.cursor()
            
            # Prüfe Termine
            cur.execute("SELECT id FROM appointments WHERE date = ?", (date_str,))
            if cur.fetchone():
                return False
            
            # Prüfe geblockte Tage
            cur.execute("SELECT id FROM blocked_days WHERE date = ?", (date_str,))
            if cur.fetchone():
                return False
            
            return True
    
    def book_appointment(self, date_str: str, customer_name: str, contact_info: str, service: str, user_id: str) -> bool:
        """Bucht einen Termin"""
        if not self.is_date_available(date_str):
            return False
        
        try:
            with sqlite3.connect("storage.db") as con:
                cur = con.cursor()
                cur.execute("""
                    INSERT INTO appointments (date, customer_name, contact_info, service, user_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (date_str, customer_name, contact_info, service, user_id, datetime.now().isoformat()))
                con.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_appointments_for_month(self, year: int, month: int) -> List[str]:
        """Gibt alle Termine für einen Monat zurück"""
        start_date = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month+1:02d}-01"
        
        with sqlite3.connect("storage.db") as con:
            cur = con.cursor()
            cur.execute("""
                SELECT date FROM appointments 
                WHERE date >= ? AND date < ?
                ORDER BY date
            """, (start_date, end_date))
            
            return [row[0] for row in cur.fetchall()]
    
    def get_blocked_days_for_month(self, year: int, month: int) -> List[str]:
        """Gibt alle geblockten Tage für einen Monat zurück"""
        start_date = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month+1:02d}-01"
        
        with sqlite3.connect("storage.db") as con:
            cur = con.cursor()
            cur.execute("""
                SELECT date FROM blocked_days 
                WHERE date >= ? AND date < ?
                ORDER BY date
            """, (start_date, end_date))
            
            return [row[0] for row in cur.fetchall()]
    
    def block_day(self, date_str: str, reason: str, blocked_by: str) -> bool:
        """Blockiert einen Tag im Kalender"""
        if not self.is_date_available(date_str):
            return False
        
        try:
            with sqlite3.connect("storage.db") as con:
                cur = con.cursor()
                cur.execute("""
                    INSERT INTO blocked_days (date, reason, blocked_by, created_at)
                    VALUES (?, ?, ?, ?)
                """, (date_str, reason, blocked_by, datetime.now().isoformat()))
                con.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        
    def unblock_day(self, date_str: str) -> bool:
        """Entfernt Blockierung eines Tages"""
        try:
            with sqlite3.connect("storage.db") as con:
                cur = con.cursor()
                cur.execute("DELETE FROM blocked_days WHERE date = ?", (date_str,))
                con.commit()
                
                # Prüfe ob ein Eintrag gelöscht wurde
                return cur.rowcount > 0
        except Exception as e:
            print(f"Fehler beim Entblocken des Tages: {e}")
            return False
    
    def get_all_blocked_days(self) -> List[Tuple[str, str, str]]:
        """Gibt alle geblockten Tage zurück"""
        try:
            with sqlite3.connect("storage.db") as con:
                cur = con.cursor()
                cur.execute("""
                    SELECT date, reason, blocked_by 
                    FROM blocked_days 
                    ORDER BY date
                """)
                return cur.fetchall()  # ✅ KORREKT: fetchall() nicht fetchal
        except Exception as e:
            print(f"Fehler beim Abrufen geblockter Tage: {e}")
            return []   
    
    def generate_calendar_view(self, year: int, month: int, language: str = 'de') -> str:
        """Generiert eine Kalender-Ansicht für den Monat"""
        appointments = self.get_appointments_for_month(year, month)
        blocked_days = self.get_blocked_days_for_month(year, month)
        
        # Kalender erstellen
        cal = calendar.monthcalendar(year, month)
        month_name = calendar.month_name[month]
        
        # Übersetzungen für Monatsnamen
        month_translations = {
            'de': ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 
                'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'],
            'en': ['January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'],
            'ar': ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'],
            'fr': ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'],
            'es': ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
            'it': ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
                'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'],
            'tr': ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'],
            'ru': ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'],
            'pl': ['Styczeń', 'Luty', 'Marzec', 'Kwiecień', 'Maj', 'Czerwiec',
                'Lipiec', 'Sierpień', 'Wrzesień', 'Październik', 'Listopad', 'Grudzień'],
            'uk': ['Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень',
                'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень'],
            'zh': ['一月', '二月', '三月', '四月', '五月', '六月',
                '七月', '八月', '九月', '十月', '十一月', '十二月'],
            'ja': ['1月', '2月', '3月', '4月', '5月', '6月',
                '7月', '8月', '9月', '10月', '11月', '12月'],
            'ko': ['1월', '2월', '3월', '4월', '5월', '6월',
                '7월', '8월', '9월', '10월', '11월', '12월'],
            'pt': ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'],
            'nl': ['Januari', 'Februari', 'Maart', 'April', 'Mei', 'Juni',
                'Juli', 'Augustus', 'September', 'Oktober', 'November', 'December'],
            'sv': ['Januari', 'Februari', 'Mars', 'April', 'Maj', 'Juni',
                'Juli', 'Augusti', 'September', 'Oktober', 'November', 'December'],
            'da': ['Januar', 'Februar', 'Marts', 'April', 'Maj', 'Juni',
                'Juli', 'August', 'September', 'Oktober', 'November', 'December'],
            'cs': ['Leden', 'Únor', 'Březen', 'Duben', 'Květen', 'Červen',
                'Červenec', 'Srpen', 'Září', 'Říjen', 'Listopad', 'Prosinec'],
            'hr': ['Siječanj', 'Veljača', 'Ožujak', 'Travanj', 'Svibanj', 'Lipanj',
                'Srpanj', 'Kolovoz', 'Rujan', 'Listopad', 'Studeni', 'Prosinac'],
            'bg': ['Януари', 'Февруари', 'Март', 'Април', 'Май', 'Юни',
                'Юли', 'Август', 'Септември', 'Октомври', 'Ноември', 'Декември'],
            'bn': ['জানুয়ারী', 'ফেব্রুয়ারী', 'মার্চ', 'এপ্রিল', 'মে', 'জুন',
                'জুলাই', 'আগস্ট', 'সেপ্টেম্বর', 'অক্টোবর', 'নভেম্বর', 'ডিসেম্বর'],
            'el': ['Ιανουάριος', 'Φεβρουάριος', 'Μάρτιος', 'Απρίλιος', 'Μάιος', 'Ιούνιος',
                'Ιούλιος', 'Αύγουστος', 'Σεπτέμβριος', 'Οκτώβριος', 'Νοέμβριος', 'Δεκέμβριος'],
            'he': ['ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני',
                'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר'],
            'hi': ['जनवरी', 'फरवरी', 'मार्च', 'अप्रैल', 'मई', 'जून',
                'जुलाई', 'अगस्त', 'सितंबर', 'अक्टूबर', 'नवंबर', 'दिसंबर'],
            'hu': ['Január', 'Február', 'Március', 'Április', 'Május', 'Június',
                'Július', 'Augusztus', 'Szeptember', 'Október', 'November', 'December'],
            'id': ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'],
            'ms': ['Januari', 'Februari', 'Mac', 'April', 'Mei', 'Jun',
                'Julai', 'Ogos', 'September', 'Oktober', 'November', 'Disember'],
            'no': ['Januar', 'Februar', 'Mars', 'April', 'Mai', 'Juni',
                'Juli', 'August', 'September', 'Oktober', 'November', 'Desember'],
            'fi': ['Tammikuu', 'Helmikuu', 'Maaliskuu', 'Huhtikuu', 'Toukokuu', 'Kesäkuu',
                'Heinäkuu', 'Elokuu', 'Syyskuu', 'Lokakuu', 'Marraskuu', 'Joulukuu'],
            'th': ['มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
                'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'],
            'vi': ['Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
                'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'],
            'ro': ['Ianuarie', 'Februarie', 'Martie', 'Aprilie', 'Mai', 'Iunie',
                'Iulie', 'August', 'Septembrie', 'Octombrie', 'Noiembrie', 'Decembrie'],
            'ca': ['Gener', 'Febrer', 'Març', 'Abril', 'Maig', 'Juny',
                'Juliol', 'Agost', 'Setembre', 'Octubre', 'Novembre', 'Desembre']
        }
        
        month_display = month_translations.get(language, month_translations['de'])[month-1]
        
        # Wochentage basierend auf Sprache
        weekdays = {
            'Deutsch': ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'],
            'Englisch': ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'],
            'Arabisch': ['إث', 'ث', 'أر', 'خ', 'ج', 'س', 'ح'],
            'Französisch': ['Lu', 'Ma', 'Me', 'Je', 'Ve', 'Sa', 'Di'],
            'Spanisch': ['Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sá', 'Do'],
            'Italienisch': ['Lu', 'Ma', 'Me', 'Gi', 'Ve', 'Sa', 'Do'],
            'Türkisch': ['Pt', 'Sa', 'Ça', 'Pe', 'Cu', 'Ct', 'Pz'],
            'Russisch': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
            'Polnisch': ['Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'So', 'Nd'],
            'Ukrainisch': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд'],
            'Chinesisch': ['一', '二', '三', '四', '五', '六', '日'],
            'Japanisch': ['月', '火', '水', '木', '金', '土', '日'],
            'Koreanisch': ['월', '화', '수', '목', '금', '토', '일'],
            'Portugiesisch': ['Se', 'Te', 'Qu', 'Qu', 'Se', 'Sá', 'Do'],
            'Niederländisch': ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'],
            'Schwedisch': ['Må', 'Ti', 'On', 'To', 'Fr', 'Lö', 'Sö'],
            'Dänisch': ['Ma', 'Ti', 'On', 'To', 'Fr', 'Lø', 'Sø'],
            'Tschechisch': ['Po', 'Út', 'St', 'Čt', 'Pá', 'So', 'Ne'],
            'Kroatisch': ['Po', 'Ut', 'Sr', 'Če', 'Pe', 'Su', 'Ne'],
            'Bulgarisch': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд'],
            'Bengalisch': ['সো', 'ম', 'বু', 'বৃ', 'শু', 'শ', 'র'],
            'Griechisch': ['Δε', 'Τρ', 'Τε', 'Πε', 'Πα', 'Σα', 'Κυ'],
            'Hebräisch': ['ב', 'ג', 'ד', 'ה', 'ו', 'ש', 'א'],
            'Hindi': ['सो', 'म', 'बु', 'गु', 'शु', 'श', 'र'],
            'Ungarisch': ['H', 'K', 'Sze', 'Cs', 'P', 'Szo', 'V'],
            'Indonesisch': ['Se', 'Se', 'Ra', 'Ka', 'Ju', 'Sa', 'Mi'],
            'Malaiisch': ['Is', 'Se', 'Ra', 'Kh', 'Ju', 'Sa', 'Ah'],
            'Norwegisch': ['Ma', 'Ti', 'On', 'To', 'Fr', 'Lø', 'Sø'],
            'Finnisch': ['Ma', 'Ti', 'Ke', 'To', 'Pe', 'La', 'Su'],
            'Thailändisch': ['จ', 'อ', 'พ', 'พฤ', 'ศ', 'ส', 'อา'],
            'Vietnamesisch': ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'],
            'Rumänisch': ['Lu', 'Ma', 'Mi', 'Jo', 'Vi', 'Sâ', 'Du'],
            'Katalanisch': ['Dl', 'Dt', 'Dc', 'Dj', 'Dv', 'Ds', 'Dg']
        }
        weekday_labels = weekdays.get(language, weekdays['Deutsch'])
        
        # Kalender-Header
        calendar_view = f"**{month_display} {year}**\n"
        calendar_view += " ".join(weekday_labels) + "\n"
        
        # Kalender-Inhalt
        for week in cal:
            week_line = ""
            for day in week:
                if day == 0:
                    week_line += "   "  # Leerer Tag
                else:
                    date_str = f"{year:04d}-{month:02d}-{day:02d}"
                    if date_str in appointments:
                        week_line += "❌ "  # Gebuchter Termin
                    elif date_str in blocked_days:
                        week_line += "🚫 "  # Geblockter Tag
                    else:
                        week_line += f"{day:2d} "  # Verfügbarer Tag
            calendar_view += week_line + "\n"
        
        # Legende
        legend = {
            'Deutsch': "\n**Legende:**\n❌ = Gebucht\n🚫 = Geblockt\nZahl = Verfügbar",
            'Englisch': "\n**Legend:**\n❌ = Booked\n🚫 = Blocked\nNumber = Available",
            'Arabisch': "\n**مفتاح:**\n❌ = محجوز\n🚫 = مغلق\nرقم = متاح",
            'Französisch': "\n**Légende:**\n❌ = Réservé\n🚫 = Bloqué\nNombre = Disponible",
            'Spanisch': "\n**Leyenda:**\n❌ = Reservado\n🚫 = Bloqueado\nNúmero = Disponible",
            'Italienisch': "\n**Legenda:**\n❌ = Prenotato\n🚫 = Bloccato\nNumero = Disponibile",
            'Türkisch': "\n**Açıklama:**\n❌ = Rezerve\n🚫 = Bloke\nSayı = Müsait",
            'Russisch': "\n**Легенда:**\n❌ = Забронировано\n🚫 = Заблокировано\nЧисло = Доступно",
            'Polnisch': "\n**Legenda:**\n❌ = Zarezerwowane\n🚫 = Zablokowane\nLiczba = Dostępne",
            'Ukrainisch': "\n**Легенда:**\n❌ = Заброньовано\n🚫 = Заблоковано\nЧисло = Доступно",
            'Chinesisch': "\n**图例:**\n❌ = 已预订\n🚫 = 已锁定\n数字 = 可用",
            'Japanisch': "\n**凡例:**\n❌ = 予約済み\n🚫 = ブロック済み\n数字 = 利用可能",
            'Koreanisch': "\n**범례:**\n❌ = 예약됨\n🚫 = 차단됨\n숫자 = 사용 가능",
            'Portugiesisch': "\n**Legenda:**\n❌ = Reservado\n🚫 = Bloqueado\nNúmero = Disponível",
            'Niederländisch': "\n**Legenda:**\n❌ = Geboekt\n🚫 = Geblokkeerd\nNummer = Beschikbaar",
            'Schwedisch': "\n**Förklaring:**\n❌ = Bokad\n🚫 = Blockerad\nNummer = Tillgänglig",
            'Dänisch': "\n**Forklaring:**\n❌ = Booket\n🚫 = Blokeret\nTal = Ledig",
            'Tschechisch': "\n**Legenda:**\n❌ = Rezervováno\n🚫 = Blokováno\nČíslo = Dostupné",
            'Kroatisch': "\n**Legenda:**\n❌ = Rezervirano\n🚫 = Blokirano\nBroj = Dostupno",
            'Bulgarisch': "\n**Легенда:**\n❌ = Резервирано\n🚫 = Блокирано\nЧисло = Доступно",
            'Bengalisch': "\n**লিজেন্ড:**\n❌ = বুকড\n🚫 = ব্লকড\nসংখ্যা = উপলব্ধ",
            'Griechisch': "\n**Εξήγηση:**\n❌ = Κρατημένο\n🚫 = Αποκλεισμένο\nΑριθμός = Διαθέσιμο",
            'Hebräisch': "\n**מקרא:**\n❌ = נתפס\n🚫 = חסום\nמספר = פנוי",
            'Hindi': "\n**लिजेंड:**\n❌ = बुक किया गया\n🚫 = ब्लॉक किया गया\nसंख्या = उपलब्ध",
            'Ungarisch': "\n**Jelmagyarázat:**\n❌ = Foglalt\n🚫 = Blokkolt\nSzám = Elérhető",
            'Indonesisch': "\n**Keterangan:**\n❌ = Dipesan\n🚫 = Diblokir\nAngka = Tersedia",
            'Malaiisch': "\n**Keterangan:**\n❌ = Ditempah\n🚫 = Disekat\nNombor = Tersedia",
            'Norwegisch': "\n**Forklaring:**\n❌ = Booket\n🚫 = Blokkert\nTall = Tilgjengelig",
            'Finnisch': "\n**Selite:**\n❌ = Varattu\n🚫 = Estetty\nNumero = Vapaa",
            'Thailändisch': "\n**คำอธิบาย:**\n❌ = จองแล้ว\n🚫 = ปิดกั้น\nตัวเลข = ว่าง",
            'Vietnamesisch': "\n**Chú thích:**\n❌ = Đã đặt\n🚫 = Đã chặn\nSố = Có sẵn",
            'Rumänisch': "\n**Legendă:**\n❌ = Rezervat\n🚫 = Blocat\nNumăr = Disponibil",
            'Katalanisch': "\n**Llegenda:**\n❌ = Reservat\n🚫 = Bloquejat\nNombre = Disponible"
        }
        
        calendar_view += legend.get(language, legend['Deutsch'])
        return calendar_view
    
    def export_appointments_to_file(self, filename: str = "appointments_export.txt") -> str:
        """Exportiert alle Termine in eine Datei"""
        try:
            with sqlite3.connect("storage.db") as con:
                cur = con.cursor()
                cur.execute("""
                    SELECT date, customer_name, contact_info, service, created_at 
                    FROM appointments 
                    ORDER BY date
                """)
                appointments = cur.fetchall()
                
                cur.execute("""
                    SELECT date, reason, blocked_by, created_at 
                    FROM blocked_days 
                    ORDER BY date
                """)
                blocked_days = cur.fetchall()
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("📅 SHAWO UMGÜGE - TERMINÜBERSICHT\n")
                f.write("=" * 50 + "\n")
                f.write(f"Export erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n")
                
                f.write("🗓️ GEBUCHTE TERMINE:\n")
                f.write("-" * 30 + "\n")
                for date, customer, contact, service, created in appointments:
                    f.write(f"Datum: {date}\n")
                    f.write(f"Kunde: {customer}\n")
                    f.write(f"Kontakt: {contact}\n")
                    f.write(f"Service: {service}\n")
                    f.write(f"Gebucht am: {created}\n")
                    f.write("-" * 20 + "\n")
                
                f.write("\n🚫 GEBLOCKTE TAGE:\n")
                f.write("-" * 30 + "\n")
                for date, reason, blocked_by, created in blocked_days:
                    f.write(f"Datum: {date}\n")
                    f.write(f"Grund: {reason}\n")
                    f.write(f"Geblockt von: {blocked_by}\n")
                    f.write(f"Geblockt am: {created}\n")
                    f.write("-" * 20 + "\n")
            
            return filename
        except Exception as e:
            print(f"Export-Fehler: {e}")
            return ""

# 🔧 TELEGRAM SPRACHERKENNUNG
def detect_telegram_language(update: Update):
    """Erkennt die Sprache des Users aus Telegram Systemeinstellungen"""
    try:
        user = update.effective_user
        
        # Telegram language_code verwenden
        if hasattr(user, 'language_code') and user.language_code:
            language_map = {
                'de': 'Deutsch',
                'en': 'Englisch', 
                'ar': 'Arabisch',
                'fr': 'Französisch',
                'es': 'Spanisch',
                'it': 'Italienisch',
                'tr': 'Türkisch',
                'ru': 'Russisch',
                'pl': 'Polnisch',
                'uk': 'Ukrainisch',
                'zh': 'Chinesisch',
                'ja': 'Japanisch',
                'ko': 'Koreanisch',
                'pt': 'Portugiesisch',
                'nl': 'Niederländisch',
                'sv': 'Schwedisch',
                'da': 'Dänisch',
                'cs': 'Tschechisch',
                'hr': 'Kroatisch',
                'bg': 'Bulgarisch',
                'bn': 'Bengalisch',
                'el': 'Griechisch',
                'he': 'Hebräisch',
                'hi': 'Hindi',
                'hu': 'Ungarisch',
                'id': 'Indonesisch',
                'ms': 'Malaiisch',
                'no': 'Norwegisch',
                'fi': 'Finnisch',
                'th': 'Thailändisch',
                'vi': 'Vietnamesisch',
                'ro': 'Rumänisch',
                'ca': 'Katalanisch'
            }
            detected_lang = language_map.get(user.language_code, 'de')
            return detected_lang
        
    except Exception as e:
        print(f"Telegram Spracherkennungsfehler: {e}")
    
    return 'Deutsch'  # Standardfall

# 🧮 OPTIMIERTE PREISBERECHNUNGS-FUNKTIONEN
def calculate_complete_offer(details):
    """Berechnet komplette Angebote basierend auf Kundendetails"""
    total = 0
    breakdown = []
    
    if 'umzug_zimmer' in details:
        zimmer = details['umzug_zimmer']
        entfernung = details.get('umzug_entfernung', 0)
        
        if zimmer == 1:
            base_price = PRICE_DATABASE['umzug']['1_zimmer']['min']
            stundensatz = PRICE_DATABASE['umzug']['stundensatz_2']['price']
        elif zimmer == 2:
            base_price = PRICE_DATABASE['umzug']['2_zimmer']['min'] 
            stundensatz = PRICE_DATABASE['umzug']['stundensatz_2']['price']
        elif zimmer == 3:
            base_price = PRICE_DATABASE['umzug']['3_zimmer']['min']
            stundensatz = PRICE_DATABASE['umzug']['stundensatz_3']['price']
        else:
            base_price = PRICE_DATABASE['umzug']['4_zimmer']['min']
            stundensatz = PRICE_DATABASE['umzug']['stundensatz_lkw']['price']
        
        geschaetzte_stunden = max(4, zimmer * 2)
        stunden_kosten = geschaetzte_stunden * stundensatz
        km_kosten = entfernung * PRICE_DATABASE['umzug']['km_zuschlag']['price']
        material_kosten = PRICE_DATABASE['umzug']['material']['price']
        
        umzug_total = base_price + stunden_kosten + km_kosten + material_kosten
        total += umzug_total
        
        breakdown.append(f"🚚 <b>UMZUG {zimmer}-ZIMMER:</b> {umzug_total:.2f}€")
        breakdown.append(f"   • Basispreis: {base_price}€")
        breakdown.append(f"   • {geschaetzte_stunden}h × {stundensatz}€ = {stunden_kosten}€")
        if entfernung > 0:
            breakdown.append(f"   • {entfernung}km × {PRICE_DATABASE['umzug']['km_zuschlag']['price']}€ = {km_kosten:.2f}€")
        breakdown.append(f"   • Material: {material_kosten}€")
    
    if 'maler_flaeche' in details:
        flaeche = details['maler_flaeche']
        tueren = details.get('maler_tueren', 0)
        fenster = details.get('maler_fenster', 0)
        
        grundierung_kosten = 0
        anstrich_kosten = 0
        streichen_kosten = 0
        
        if details.get('maler_grundierung', False):
            grundierung_kosten = flaeche * PRICE_DATABASE['maler']['grundierung']['price']
            breakdown.append(f"   • Grundierung {flaeche}m² × {PRICE_DATABASE['maler']['grundierung']['price']}€ = {grundierung_kosten}€")
        
        if details.get('maler_anstrich', False):
            anstrich_kosten = flaeche * PRICE_DATABASE['maler']['anstrich']['price']
            breakdown.append(f"   • Anstrich {flaeche}m² × {PRICE_DATABASE['maler']['anstrich']['price']}€ = {anstrich_kosten}€")
        
        if details.get('maler_streichen', False):
            streichen_kosten = flaeche * PRICE_DATABASE['maler']['streichen']['price']
            breakdown.append(f"   • Streichen {flaeche}m² × {PRICE_DATABASE['maler']['streichen']['price']}€ = {streichen_kosten}€")
        
        if grundierung_kosten == 0 and anstrich_kosten == 0 and streichen_kosten == 0:
            anstrich_kosten = flaeche * PRICE_DATABASE['maler']['anstrich']['price']
            breakdown.append(f"   • Malerarbeiten {flaeche}m² × {PRICE_DATABASE['maler']['anstrich']['price']}€ = {anstrich_kosten}€")
        
        tueren_kosten = tueren * PRICE_DATABASE['maler']['tueren_anstrich']['price']
        fenster_kosten = fenster * PRICE_DATABASE['maler']['fenster_anstrich']['price']
        
        maler_total = grundierung_kosten + anstrich_kosten + streichen_kosten + tueren_kosten + fenster_kosten
        total += maler_total
        
        breakdown.append(f"🎨 <b>MALERARBEITEN:</b> {maler_total:.2f}€")
        if tueren > 0:
            breakdown.append(f"   • Türen {tueren} × {PRICE_DATABASE['maler']['tueren_anstrich']['price']}€ = {tueren_kosten}€")
        if fenster > 0:
            breakdown.append(f"   • Fenster {fenster} × {PRICE_DATABASE['maler']['fenster_anstrich']['price']}€ = {fenster_kosten}€")
    
    if 'reinigung_flaeche' in details:
        flaeche = details['reinigung_flaeche']
        fenster = details.get('reinigung_fenster', 0)
        
        reinigung_kosten = flaeche * ((PRICE_DATABASE['reinigung']['umzugsreinigung']['min'] + PRICE_DATABASE['reinigung']['umzugsreinigung']['max']) / 2)
        fenster_kosten = fenster * ((PRICE_DATABASE['reinigung']['fensterreinigung']['min'] + PRICE_DATABASE['reinigung']['fensterreinigung']['max']) / 2)
        material_kosten = flaeche * PRICE_DATABASE['reinigung']['material_reinigung']['price']
        kueche_kosten = PRICE_DATABASE['reinigung']['kueche_reinigung']['price']
        bad_kosten = PRICE_DATABASE['reinigung']['bad_reinigung']['price']
        
        reinigung_total = reinigung_kosten + fenster_kosten + material_kosten + kueche_kosten + bad_kosten
        total += reinigung_total
        
        breakdown.append(f"🧹 <b>REINIGUNG:</b> {reinigung_total:.2f}€")
        breakdown.append(f"   • Grundreinigung {flaeche}m² × 5€ = {reinigung_kosten}€")
        if fenster > 0:
            breakdown.append(f"   • Fenster {fenster} × 3,5€ = {fenster_kosten:.2f}€")
        breakdown.append(f"   • Material {flaeche}m² × 0,5€ = {material_kosten}€")
        breakdown.append(f"   • Küche: {kueche_kosten}€")
        breakdown.append(f"   • Bad: {bad_kosten}€")
    
    return total, breakdown

def extract_project_details(text):
    """Extrahiert automatisch Projekt-Details aus dem Text"""
    details = {}
    text_lower = text.lower()
    
    flaeche_matches = re.findall(r'(\d+)\s*m²', text)
    if flaeche_matches:
        details['maler_flaeche'] = int(flaeche_matches[0])
        details['reinigung_flaeche'] = int(flaeche_matches[0])
    
    zimmer_matches = re.findall(r'(\d+)\s*Zimmer', text)
    if zimmer_matches:
        details['umzug_zimmer'] = int(zimmer_matches[0])
    
    km_matches = re.findall(r'(\d+)\s*km', text)
    if km_matches:
        details['umzug_entfernung'] = int(km_matches[0])
    
    if any(word in text_lower for word in ['grundierung', 'grundieren', 'vorbehandlung']):
        details['maler_grundierung'] = True
    if any(word in text_lower for word in ['anstrich', 'anstreichen', 'farbe auftragen']):
        details['maler_anstrich'] = True
    if any(word in text_lower for word in ['streichen', 'überstreichen', 'lackieren']):
        details['maler_streichen'] = True
    
    datum_match = re.search(r'(\d{1,2}\.\d{1,2}\.\d{4})', text)
    if datum_match:
        details['termin'] = datum_match.group(1)
    
    return details

def generate_multilingual_price_example(language):
    """Generiert mehrsprachige Preisbeispiele mit korrekter Formatierung"""
    details = {
        'umzug_zimmer': 2,
        'umzug_entfernung': 15,
        'maler_flaeche': 60,
        'maler_tueren': 2,
        'maler_fenster': 2,
        'maler_grundierung': True,
        'maler_anstrich': True,
        'reinigung_flaeche': 60,
        'reinigung_fenster': 2
    }
    
    total, breakdown = calculate_complete_offer(details)
    
    # Übersetzung der Breakdown-Zeilen basierend auf Sprache
    if language == 'ar':
        translated_breakdown = []
        for line in breakdown:
            translated_line = line
            # Übersetzung der Schlüsselwörter
            translated_line = translated_line.replace('UMZUG', 'نقل')
            translated_line = translated_line.replace('ZIMMER:', 'غرف:')
            translated_line = translated_line.replace('Basispreis:', 'سعر الأساس:')
            translated_line = translated_line.replace('Material:', 'المواد:')
            translated_line = translated_line.replace('MALERARBEITEN:', 'أعمال الدهان:')
            translated_line = translated_line.replace('Grundierung', 'التحضير')
            translated_line = translated_line.replace('Anstrich', 'الطلاء')
            translated_line = translated_line.replace('Türen', 'الأبواب')
            translated_line = translated_line.replace('Fenster', 'النوافذ')
            translated_line = translated_line.replace('REINIGUNG:', 'التنظيف:')
            translated_line = translated_line.replace('Grundreinigung', 'التنظيف الأساسي')
            translated_line = translated_line.replace('Küche:', 'المطبخ:')
            translated_line = translated_line.replace('Bad:', 'الحمام:')
            translated_breakdown.append(translated_line)
        breakdown = translated_breakdown
    
    return breakdown, total

def generate_price_estimate(details, language='de'):
    """Generiert eine professionelle Preis-Schätzung in der gewünschten Sprache"""
    total, breakdown = calculate_complete_offer(details)
    
    if language == 'ar':
        response = "💰 <b>تقييم الأسعار (غير ملزم)</b> 💰\n\n"
        for line in breakdown:
            # Übersetzung für Arabisch
            line = line.replace('UMZUG', 'نقل')
            line = line.replace('ZIMMER:', 'غرف:')
            line = line.replace('Basispreis:', 'سعر الأساس:')
            line = line.replace('Material:', 'المواد:')
            line = line.replace('MALERARBEITEN:', 'أعمال الدهان:')
            line = line.replace('Grundierung', 'التحضير')
            line = line.replace('Anstrich', 'الطلاء')
            line = line.replace('Türen', 'الأبواب')
            line = line.replace('Fenster', 'النوافذ')
            line = line.replace('REINIGUNG:', 'التنظيف:')
            line = line.replace('Grundreinigung', 'التنظيف الأساسي')
            line = line.replace('Küche:', 'المطبخ:')
            line = line.replace('Bad:', 'الحمام:')
            response += f"{line}\n"
        
        response += f"\n📊 <b>التقدير الكلي: {total:.2f}€</b>\n\n"
        
        response += (
            "💡 <i>ملاحظة: هذا تقدير أولي بناءً على المعلومات المقدمة. "
            "السعر النهائي قد يختلف حسب الجهد الدقيق.</i>\n\n"
            
            "✅ <b>يشمل:</b>\n"
            "• التنفيذ الاحترافي\n"
            "• مواد عالية الجودة\n"
            "• موظفين ذوي خبرة\n"
            "• خدمة مؤمنة\n\n"
            
            "📞 <b>للحصول على عرض ملزم:</b>\n"
            "يرجى مشاركة معلومات الاتصال الخاصة بك:\n"
            "• الاسم الكامل\n"
            "• رقم الهاتف\n"
            "• عنوان البريد الإلكتروني\n\n"
            
            "سنتصل بك على الفور للتفاصيل! 🚀"
        )
    else:
        response = "💰 <b>UNVERBINDLICHE PREIS-SCHÄTZUNG</b> 💰\n\n"
        
        for line in breakdown:
            response += f"{line}\n"
        
        response += f"\n📊 <b>GESAMTSCHÄTZUNG: {total:.2f}€</b>\n\n"
        
        response += (
            "💡 <i>Hinweis: Dies ist eine erste Schätzung basierend auf Ihren Angaben. "
            "Der endgültige Preis kann je nach genauem Aufwand variieren.</i>\n\n"
            
            "✅ <b>Inklusive:</b>\n"
            "• Professionelle Durchführung\n"
            "• Qualitätsmaterialien\n"
            "• Erfahrene Mitarbeiter\n"
            "• Versicherter Service\n\n"
            
            "📞 <b>Für verbindliches Angebot:</b>\n"
            "Bitte teilen Sie mir Ihre Kontaktdaten mit:\n"
            "• Vollständiger Name\n"
            "• Telefonnummer\n"
            "• E-Mail-Adresse\n\n"
            
            "Wir kontaktieren Sie dann umgehend für die Details! 🚀"
        )
    
    return response

# 🔄 SPRACHERKENNUNG FÜR TEXT
def detect_user_language(text):
    """Erkennt die Sprache des User-Textes"""
    try:
        language = detect(text)
        language_map = {
            'de': 'Deutsch',
            'en': 'Englisch', 
            'ar': 'Arabisch',
            'fr': 'Französisch',
            'es': 'Spanisch',
            'it': 'Italienisch',
            'tr': 'Türkisch',
            'ru': 'Russisch',
            'pl': 'Polnisch',
            'uk': 'Ukrainisch',
            'zh': 'Chinesisch',
            'ja': 'Japanisch',
            'ko': 'Koreanisch',
            'pt': 'Portugiesisch',
            'nl': 'Niederländisch',
            'sv': 'Schwedisch',
            'da': 'Dänisch',
            'cs': 'Tschechisch',
            'hr': 'Kroatisch',
            'bg': 'Bulgarisch',
            'bn': 'Bengalisch',
            'el': 'Griechisch',
            'he': 'Hebräisch',
            'hi': 'Hindi',
            'hu': 'Ungarisch',
            'id': 'Indonesisch',
            'ms': 'Malaiisch',
            'no': 'Norwegisch',
            'fi': 'Finnisch',
            'th': 'Thailändisch',
            'vi': 'Vietnamesisch',
            'ro': 'Rumänisch',
            'ca': 'Katalanisch'
        }
        
        detected_lang = language_map.get(language, 'de')
        return detected_lang

    except LangDetectException:
        return 'de'
    except Exception as e:
        print(f"Spracherkennungsfehler: {e}")
        return 'de'

# 🛡️ DATENSCHUTZ-LINKS
DATENSCHUTZ_LINKS = {
    'Deutsch': {
        'firma': 'https://shawo-umzug-app.de/datenschutz-de.html',
        'ki': 'https://shawo-umzug-app.de/privacy-policy-de.html'
    },
    'Englisch': {
        'firma': 'https://shawo-umzug-app.de/datenschutz-en.html',
        'ki': 'https://shawo-umzug-app.de/privacy-policy-en.html'
    },
    'Arabisch': {
        'firma': 'https://shawo-umzug-app.de/datenschutz-ar.html',
        'ki': 'https://shawo-umzug-app.de/privacy-policy-ar.html'
    }
}

# 🎯 OPTIMIERTES BESCHWERDE-MANAGEMENT
def handle_complaint(user_message, user_language):
    """Behandelt Beschwerden und bietet Lösungswege an"""
    complaint_responses = {
        'Deutsch': {
            'response': (
                "😔 <b>Es tut uns leid, dass Sie unzufrieden sind!</b>\n\n"
                "Wir nehmen jede Beschwerde ernst und möchten das Problem schnellstmöglich lösen.\n\n"
                "🔍 <b>Bitte wählen Sie eine Option:</b>\n\n"
                "📝 <b>Option 1:</b> Beschreiben Sie hier Ihr Problem ausführlich mit:\n"
                "   • Vollständiger Name\n"
                "   • Telefonnummer\n"
                "   • Details zum Problem\n\n"
                "📞 <b>Option 2:</b> Kontaktieren Sie uns direkt:\n"
                "   • WhatsApp: +49 176 72407732\n"
                "   • Telefon: +49 176 72407732\n"
                "   • E-Mail: shawo.info.betrieb@gmail.com\n\n"
                "🛡️ <b>Ihre Daten sind sicher:</b>\n"
                "• Keine Weitergabe an Dritte\n"
                "• Datenschutzkonforme Verarbeitung\n"
                "• Schnelle Problemlösung\n\n"
                "<i>Wir sind ein Familienunternehmen und kümmern uns persönlich um jedes Anliegen!</i>"
            ),
            'datenschutz': (
                "🛡️ <b>Datenschutzinformationen:</b>\n"
                f"• Firmen-Datenschutz: {DATENSCHUTZ_LINKS['Deutsch']['firma']}\n"
                f"• KI-Assistent Datenschutz: {DATENSCHUTZ_LINKS['Deutsch']['ki']}\n\n"
                "Wir halten uns strikt an Datenschutzbestimmungen und geben Ihre Daten niemals an Dritte weiter!"
            )
        },
        'Englisch': {
            'response': (
                "😔 <b>We're sorry to hear you're unsatisfied!</b>\n\n"
                "We take every complaint seriously and want to resolve the issue as quickly as possible.\n\n"
                "🔍 <b>Please choose an option:</b>\n\n"
                "📝 <b>Option 1:</b> Describe your problem here in detail with:\n"
                "   • Full name\n"
                "   • Phone number\n"
                "   • Problem details\n\n"
                "📞 <b>Option 2:</b> Contact us directly:\n"
                "   • WhatsApp: +49 176 72407732\n"
                "   • Phone: +49 176 72407732\n"
                "   • Email: shawo.info.betrieb@gmail.com\n\n"
                "🛡️ <b>Your data is safe:</b>\n"
                "• No sharing with third parties\n"
                "• Privacy-compliant processing\n"
                "• Quick problem resolution\n\n"
                "<i>We are a family business and personally take care of every concern!</i>"
            ),
            'datenschutz': (
                "🛡️ <b>Privacy Information:</b>\n"
                f"• Company Privacy: {DATENSCHUTZ_LINKS['Englisch']['firma']}\n"
                f"• AI Assistant Privacy: {DATENSCHUTZ_LINKS['Englisch']['ki']}\n\n"
                "We strictly adhere to privacy regulations and never share your data with third parties!"
            )
        },
        'Arabisch': {
            'response': (
                "😔 <b>نأسف لسماع أنك غير راضٍ!</b>\n\n"
                "نحن نأخذ كل شكوى على محمل الجد ونريد حل المشكلة في أسرع وقت ممكن.\n\n"
                "🔍 <b>الرجاء اختيار خيار:</b>\n\n"
                "📝 <b>الخيار 1:</b> صف مشكلتك هنا بالتفصيل مع:\n"
                "   • الاسم الكامل\n"
                "   • رقم الهاتف\n"
                "   • تفاصيل المشكلة\n\n"
                "📞 <b>الخيار 2:</b> اتصل بنا مباشرة:\n"
                "   • واتساب: +49 176 72407732\n"
                "   • هاتف: +49 176 72407732\n"
                "   • بريد إلكتروني: shawo.info.betrieb@gmail.com\n\n"
                "🛡️ <b>بياناتك آمنة:</b>\n"
                "• لا مشاركة مع أطراف ثالثة\n"
                "• معالجة متوافقة مع الخصوصية\n"
                "• حل سريع للمشكلة\n\n"
                "<i>نحن شركة عائلية ونهتم شخصيًا بكل استفسار!</i>"
            ),
            'datenschutz': (
                "🛡️ <b>معلومات الخصوصية:</b>\n"
                f"• خصوصية الشركة: {DATENSCHUTZ_LINKS['Arabisch']['firma']}\n"
                f"• خصوصية المساعد الذكي: {DATENSCHUTZ_LINKS['Arabisch']['ki']}\n\n"
                "نلتزم بدقة بأنظمة الخصوصية ولا نشارك بياناتك مع أطراف ثالثة أبدًا!"
            )
        }
    }
    
    return complaint_responses.get(user_language, complaint_responses['Deutsch'])

# 👨‍💻 ENTWICKLER-INFORMATIONEN
DEVELOPER_INFO = {
    'de': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI Developer & Full Stack Entwickler",
        'description': (
            "🔧 <b>Entwickler-Informationen</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlin, Germany\n\n"
            "🚀 <b>Professionelles Profil:</b>\n"
            "• Motivierter und zukunftsorientierter AI-Entwickler\n"
            "• Praxiserfahrung in AI-Produktentwicklung und Data Science\n"
            "• Spezialisiert auf Machine Learning und Natural Language Processing\n"
            "• Starker Python-Programmierer mit Full-Stack-Fähigkeiten\n"
            "• Erfahrung in Deployment von AI-Lösungen mit Flask, Streamlit und Hugging Face\n\n"
            "💼 <b>Technische Kompetenzen:</b>\n"
            "• AI & Machine Learning Development\n"
            "• Data Analysis & Visualization\n"
            "• Natural Language Processing (NLP)\n"
            "• Generative AI & LLM Integration\n"
            "• Python, Flask, Streamlit, REST APIs\n"
            "• Web Development (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Kontakt & Profile:</b>\n"
            "📧 E-Mail: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Der Entwickler dieses professionellen KI-Assistenten für SHAWO Umzüge</i>"
        )
    },
    'en': {
        'name': "Mhd Fouaad Al Kamsha", 
        'title': "AI Developer & Full Stack Developer",
        'description': (
            "🔧 <b>Developer Information</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlin, Germany\n\n"
            "🚀 <b>Professional Profile:</b>\n"
            "• Motivated and forward-thinking AI Developer\n"
            "• Hands-on experience in AI product development and Data Science\n"
            "• Specialized in Machine Learning and Natural Language Processing\n"
            "• Strong Python programmer with full-stack capabilities\n"
            "• Experience deploying AI solutions with Flask, Streamlit and Hugging Face\n\n"
            "💼 <b>Technical Competencies:</b>\n"
            "• AI & Machine Learning Development\n"
            "• Data Analysis & Visualization\n"
            "• Natural Language Processing (NLP)\n"
            "• Generative AI & LLM Integration\n"
            "• Python, Flask, Streamlit, REST APIs\n"
            "• Web Development (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Contact & Profiles:</b>\n"
            "📧 Email: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>The developer of this professional AI assistant for SHAWO Moves</i>"
        )
    },
    'ar': {
        'name': "محمد فؤاد الكمشة",
        'title': "مطور الذكاء الاصطناعي ومطور الويب الشامل",
        'description': (
            "🔧 <b>معلومات المطور</b>\n\n"
            "👨‍💻 <b>محمد فؤاد الكمشة</b>\n"
            "📍 برلين، ألمانيا\n\n"
            "🚀 <b>الملف المهني:</b>\n"
            "• مطور ذكاء اصطناعي متحمس ومستقبلي\n"
            "• خبرة عملية في تطوير منتجات الذكاء الاصطناعي وعلوم البيانات\n"
            "• متخصص في التعلم الآلي ومعالجة اللغات الطبيعية\n"
            "• مبرمج بايثون قوي مع قدرات تطوير شاملة\n"
            "• خبرة في نشر حلول الذكاء الاصطناعي باستخدام Flask و Streamlit و Hugging Face\n\n"
            "💼 <b>الكفاءات التقنية:</b>\n"
            "• تطوير الذكاء الاصطناعي والتعلم الآلي\n"
            "• تحليل البيانات وتصورها\n"
            "• معالجة اللغات الطبيعية (NLP)\n"
            "• الذكاء الاصطناعي التوليدي وتكامل النماذج اللغوية\n"
            "• Python, Flask, Streamlit, REST APIs\n"
            "• تطوير الويب (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>جهات الاتصال والملفات الشخصية:</b>\n"
            "📧 البريد الإلكتروني: alkamsha.berlin@gmail.com\n"
            "💼 لينكد إن: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 جيت هاب: https://github.com/FouaadAI\n\n"
            "<i>مطور هذا المساعد الذكي المحترف لشركة SHAWO للتنقلات</i>"
        )
    },
    'fr': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "Développeur IA & Développeur Full Stack",
        'description': (
            "🔧 <b>Informations du Développeur</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlin, Allemagne\n\n"
            "🚀 <b>Profil Professionnel:</b>\n"
            "• Développeur IA motivé et tourné vers l'avenir\n"
            "• Expérience pratique en développement de produits IA et Science des Données\n"
            "• Spécialisé en Machine Learning et Traitement du Langage Naturel\n"
            "• Programmeur Python compétent avec des capacités full-stack\n"
            "• Expérience en déploiement de solutions IA avec Flask, Streamlit et Hugging Face\n\n"
            "💼 <b>Compétences Techniques:</b>\n"
            "• Développement IA & Machine Learning\n"
            "• Analyse & Visualisation de Données\n"
            "• Traitement du Langage Naturel (NLP)\n"
            "• IA Générative & Intégration LLM\n"
            "• Python, Flask, Streamlit, APIs REST\n"
            "• Développement Web (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Contact & Profils:</b>\n"
            "📧 E-mail: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Le développeur de cet assistant IA professionnel pour SHAWO Déménagements</i>"
        )
    },
    'es': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "Desarrollador de IA & Desarrollador Full Stack",
        'description': (
            "🔧 <b>Información del Desarrollador</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlín, Alemania\n\n"
            "🚀 <b>Perfil Profesional:</b>\n"
            "• Desarrollador de IA motivado y con visión de futuro\n"
            "• Experiencia práctica en desarrollo de productos de IA y Ciencia de Datos\n"
            "• Especializado en Aprendizaje Automático y Procesamiento de Lenguaje Natural\n"
            "• Programador Python sólido con capacidades full-stack\n"
            "• Experiencia desplegando soluciones de IA con Flask, Streamlit y Hugging Face\n\n"
            "💼 <b>Competencias Técnicas:</b>\n"
            "• Desarrollo de IA & Aprendizaje Automático\n"
            "• Análisis & Visualización de Datos\n"
            "• Procesamiento de Lenguaje Natural (NLP)\n"
            "• IA Generativa & Integración LLM\n"
            "• Python, Flask, Streamlit, APIs REST\n"
            "• Desarrollo Web (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Contacto & Perfiles:</b>\n"
            "📧 Correo: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>El desarrollador de este asistente de IA profesional para SHAWO Mudanzas</i>"
        )
    },
    'it': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "Sviluppatore AI & Sviluppatore Full Stack",
        'description': (
            "🔧 <b>Informazioni dello Sviluppatore</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlino, Germania\n\n"
            "🚀 <b>Profilo Professionale:</b>\n"
            "• Sviluppatore AI motivato e lungimirante\n"
            "• Esperienza pratica nello sviluppo di prodotti AI e Data Science\n"
            "• Specializzato in Machine Learning ed Elaborazione del Linguaggio Naturale\n"
            "• Forte programmatore Python con capacità full-stack\n"
            "• Esperienza nel deployment di soluzioni AI con Flask, Streamlit e Hugging Face\n\n"
            "💼 <b>Competenze Tecniche:</b>\n"
            "• Sviluppo AI & Machine Learning\n"
            "• Analisi & Visualizzazione dei Dati\n"
            "• Elaborazione del Linguaggio Naturale (NLP)\n"
            "• AI Generativa & Integrazione LLM\n"
            "• Python, Flask, Streamlit, API REST\n"
            "• Sviluppo Web (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Contatti & Profili:</b>\n"
            "📧 Email: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Lo sviluppatore di questo assistente AI professionale per SHAWO Traslochi</i>"
        )
    },
    'tr': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI Geliştirici & Full Stack Geliştirici",
        'description': (
            "🔧 <b>Geliştirici Bilgileri</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlin, Almanya\n\n"
            "🚀 <b>Profesyonel Profil:</b>\n"
            "• Motive ve gelecek odaklı AI Geliştirici\n"
            "• AI ürün geliştirme ve Veri Bilimi'nde pratik deneyim\n"
            "• Makine Öğrenmesi ve Doğal Dil İşleme'de uzman\n"
            "• Full-stack yetenekleri olan güçlü Python programcısı\n"
            "• Flask, Streamlit ve Hugging Face ile AI çözümleri dağıtım deneyimi\n\n"
            "💼 <b>Teknik Yetkinlikler:</b>\n"
            "• AI & Makine Öğrenmesi Geliştirme\n"
            "• Veri Analizi & Görselleştirme\n"
            "• Doğal Dil İşleme (NLP)\n"
            "• Üretken AI & LLM Entegrasyonu\n"
            "• Python, Flask, Streamlit, REST API'ler\n"
            "• Web Geliştirme (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>İletişim & Profiller:</b>\n"
            "📧 E-posta: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>SHAWO Taşınma için bu profesyonel AI asistanının geliştiricisi</i>"
        )
    },
    'ru': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI Разработчик & Full Stack Разработчик",
        'description': (
            "🔧 <b>Информация о Разработчике</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Берлин, Германия\n\n"
            "🚀 <b>Профессиональный Профиль:</b>\n"
            "• Мотивированный и перспективный AI-разработчик\n"
            "• Практический опыт в разработке AI-продуктов и Data Science\n"
            "• Специализация в Machine Learning и Обработке Естественного Языка\n"
            "• Сильный программист Python с full-stack возможностями\n"
            "• Опыт развертывания AI-решений с Flask, Streamlit и Hugging Face\n\n"
            "💼 <b>Технические Компетенции:</b>\n"
            "• Разработка AI & Machine Learning\n"
            "• Анализ & Визуализация Данных\n"
            "• Обработка Естественного Языка (NLP)\n"
            "• Генеративный AI & Интеграция LLM\n"
            "• Python, Flask, Streamlit, REST API\n"
            "• Веб-разработка (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Контакты & Профили:</b>\n"
            "📧 Email: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Разработчик этого профессионального AI-ассистента для SHAWO Переездов</i>"
        )
    },
    'pl': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "Programista AI & Programista Full Stack",
        'description': (
            "🔧 <b>Informacje o Programiście</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlin, Niemcy\n\n"
            "🚀 <b>Profil Zawodowy:</b>\n"
            "• Zmotywowany i przyszłościowy programista AI\n"
            "• Praktyczne doświadczenie w rozwoju produktów AI i Data Science\n"
            "• Specjalizacja w Machine Learning i Przetwarzaniu Języka Naturalnego\n"
            "• Silny programista Python z umiejętnościami full-stack\n"
            "• Doświadczenie we wdrażaniu rozwiązań AI z Flask, Streamlit i Hugging Face\n\n"
            "💼 <b>Kompetencje Techniczne:</b>\n"
            "• Rozwój AI & Machine Learning\n"
            "• Analiza & Wizualizacja Danych\n"
            "• Przetwarzanie Języka Naturalnego (NLP)\n"
            "• Generatywna AI & Integracja LLM\n"
            "• Python, Flask, Streamlit, REST API\n"
            "• Rozwój Stron Internetowych (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Kontakt & Profile:</b>\n"
            "📧 Email: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Programista tego profesjonalnego asystenta AI dla SHAWO Przeprowadzek</i>"
        )
    },
    'uk': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI Розробник & Full Stack Розробник",
        'description': (
            "🔧 <b>Інформація про Розробника</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Берлін, Німеччина\n\n"
            "🚀 <b>Професійний Профіль:</b>\n"
            "• Мотивований та перспективний AI-розробник\n"
            "• Практичний досвід у розробці AI-продуктів та Data Science\n"
            "• Спеціалізація в Machine Learning та Обробці Природної Мови\n"
            "• Сильний програміст Python з full-stack можливостями\n"
            "• Досвід розгортання AI-рішень з Flask, Streamlit та Hugging Face\n\n"
            "💼 <b>Технічні Компетенції:</b>\n"
            "• Розробка AI & Machine Learning\n"
            "• Аналіз & Візуалізація Даних\n"
            "• Обробка Природної Мови (NLP)\n"
            "• Генеративний AI & Інтеграція LLM\n"
            "• Python, Flask, Streamlit, REST API\n"
            "• Веб-розробка (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Контакти & Профілі:</b>\n"
            "📧 Email: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Розробник цього професійного AI-асистента для SHAWO Переїздів</i>"
        )
    },
    'zh': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI 开发者 & 全栈开发者",
        'description': (
            "🔧 <b>开发者信息</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 柏林, 德国\n\n"
            "🚀 <b>专业简介:</b>\n"
            "• 积极进取且具有前瞻性思维的AI开发者\n"
            "• 在AI产品开发和数据科学方面拥有实践经验\n"
            "• 专注于机器学习和自然语言处理\n"
            "• 强大的Python程序员，具备全栈能力\n"
            "• 使用Flask、Streamlit和Hugging Face部署AI解决方案的经验\n\n"
            "💼 <b>技术能力:</b>\n"
            "• AI与机器学习开发\n"
            "• 数据分析与可视化\n"
            "• 自然语言处理 (NLP)\n"
            "• 生成式AI与LLM集成\n"
            "• Python, Flask, Streamlit, REST API\n"
            "• 网页开发 (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>联系方式和资料:</b>\n"
            "📧 邮箱: alkamsha.berlin@gmail.com\n"
            "💼 领英: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>SHAWO搬家专业AI助手的开发者</i>"
        )
    },
    'ja': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI開発者 & フルスタック開発者",
        'description': (
            "🔧 <b>開発者情報</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 ベルリン, ドイツ\n\n"
            "🚀 <b>プロフェッショナルプロフィール:</b>\n"
            "• やる気があり将来志向のAI開発者\n"
            "• AI製品開発とデータサイエンスの実践的な経験\n"
            "• 機械学習と自然言語処理の専門家\n"
            "• フルスタック能力を持つ強力なPythonプログラマー\n"
            "• Flask、Streamlit、Hugging Faceを使用したAIソリューションの展開経験\n\n"
            "💼 <b>技術的コンピテンシー:</b>\n"
            "• AI & 機械学習開発\n"
            "• データ分析 & 可視化\n"
            "• 自然言語処理 (NLP)\n"
            "• 生成AI & LLM統合\n"
            "• Python, Flask, Streamlit, REST API\n"
            "• Web開発 (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>連絡先 & プロフィール:</b>\n"
            "📧 メール: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>SHAWO引越しのためのこのプロフェッショナルAIアシスタントの開発者</i>"
        )
    },
    'ko': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI 개발자 & 풀스택 개발자",
        'description': (
            "🔧 <b>개발자 정보</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 베를린, 독일\n\n"
            "🚀 <b>전문 프로필:</b>\n"
            "• 동기 부여되고 미래 지향적인 AI 개발자\n"
            "• AI 제품 개발 및 데이터 과학 분야 실무 경험\n"
            "• 머신러닝 및 자연어 처리 전문가\n"
            "• 풀스택 능력을 갖춘 강력한 Python 프로그래머\n"
            "• Flask, Streamlit, Hugging Face를 사용한 AI 솔루션 배포 경험\n\n"
            "💼 <b>기술 역량:</b>\n"
            "• AI & 머신러닝 개발\n"
            "• 데이터 분석 & 시각화\n"
            "• 자연어 처리 (NLP)\n"
            "• 생성 AI & LLM 통합\n"
            "• Python, Flask, Streamlit, REST API\n"
            "• 웹 개발 (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>연락처 & 프로필:</b>\n"
            "📧 이메일: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>SHAWO 이사를 위한 이 전문 AI 어시스턴트의 개발자</i>"
        )
    },
    'pt': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "Desenvolvedor AI & Desenvolvedor Full Stack",
        'description': (
            "🔧 <b>Informações do Desenvolvedor</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlim, Alemanha\n\n"
            "🚀 <b>Perfil Profissional:</b>\n"
            "• Desenvolvedor AI motivado e com visão de futuro\n"
            "• Experiência prática em desenvolvimento de produtos AI e Data Science\n"
            "• Especializado em Machine Learning e Processamento de Linguagem Natural\n"
            "• Forte programador Python com capacidades full-stack\n"
            "• Experiência em implantação de soluções AI com Flask, Streamlit e Hugging Face\n\n"
            "💼 <b>Competências Técnicas:</b>\n"
            "• Desenvolvimento AI & Machine Learning\n"
            "• Análise & Visualização de Dados\n"
            "• Processamento de Linguagem Natural (NLP)\n"
            "• AI Generativa & Integração LLM\n"
            "• Python, Flask, Streamlit, APIs REST\n"
            "• Desenvolvimento Web (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Contato & Perfis:</b>\n"
            "📧 Email: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>O desenvolvedor deste assistente AI profissional para SHAWO Mudanças</i>"
        )
    },
    'nl': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI Ontwikkelaar & Full Stack Ontwikkelaar",
        'description': (
            "🔧 <b>Ontwikkelaarsinformatie</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlijn, Duitsland\n\n"
            "🚀 <b>Professioneel Profiel:</b>\n"
            "• Gemotiveerde en toekomstgerichte AI Ontwikkelaar\n"
            "• Praktische ervaring in AI productontwikkeling en Data Science\n"
            "• Gespecialiseerd in Machine Learning en Natural Language Processing\n"
            "• Sterke Python programmeur met full-stack capaciteiten\n"
            "• Ervaring met implementatie van AI oplossingen met Flask, Streamlit en Hugging Face\n\n"
            "💼 <b>Technische Competenties:</b>\n"
            "• AI & Machine Learning Ontwikkeling\n"
            "• Data Analyse & Visualisatie\n"
            "• Natural Language Processing (NLP)\n"
            "• Generatieve AI & LLM Integratie\n"
            "• Python, Flask, Streamlit, REST APIs\n"
            "• Web Ontwikkeling (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Contact & Profielen:</b>\n"
            "📧 E-mail: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>De ontwikkelaar van deze professionele AI-assistent voor SHAWO Verhuizingen</i>"
        )
    },
    'sv': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI-utvecklare & Full Stack-utvecklare",
        'description': (
            "🔧 <b>Utvecklarinformation</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlin, Tyskland\n\n"
            "🚀 <b>Professionell Profil:</b>\n"
            "• Motiverad och framåtblickande AI-utvecklare\n"
            "• Praktisk erfarenhet av AI-produktutveckling och Data Science\n"
            "• Specialiserad på Machine Learning och Natural Language Processing\n"
            "• Stark Python-programmerare med full-stack-förmågor\n"
            "• Erfarenhet av att distribuera AI-lösningar med Flask, Streamlit och Hugging Face\n\n"
            "💼 <b>Tekniska Kompetenser:</b>\n"
            "• AI & Machine Learning-utveckling\n"
            "• Dataanalys & Visualisering\n"
            "• Natural Language Processing (NLP)\n"
            "• Generativ AI & LLM-integration\n"
            "• Python, Flask, Streamlit, REST API:er\n"
            "• Webbutveckling (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Kontakt & Profiler:</b>\n"
            "📧 E-post: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Utvecklaren av denna professionella AI-assistent för SHAWO Flyttar</i>"
        )
    },
    'da': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI Udvikler & Full Stack Udvikler",
        'description': (
            "🔧 <b>Udviklerinformation</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlin, Tyskland\n\n"
            "🚀 <b>Professionel Profil:</b>\n"
            "• Motiveret og fremsynet AI Udvikler\n"
            "• Praktisk erfaring i AI produktudvikling og Data Science\n"
            "• Specialiseret i Machine Learning og Natural Language Processing\n"
            "• Stærk Python programmør med full-stack evner\n"
            "• Erfaring med implementering af AI løsninger med Flask, Streamlit og Hugging Face\n\n"
            "💼 <b>Tekniske Kompetencer:</b>\n"
            "• AI & Machine Learning Udvikling\n"
            "• Dataanalyse & Visualisering\n"
            "• Natural Language Processing (NLP)\n"
            "• Generativ AI & LLM Integration\n"
            "• Python, Flask, Streamlit, REST API'er\n"
            "• Webudvikling (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Kontakt & Profiler:</b>\n"
            "📧 E-mail: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Udvikleren af denne professionelle AI-assistent til SHAWO Flytninger</i>"
        )
    },
    'cs': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI Vývojář & Full Stack Vývojář",
        'description': (
            "🔧 <b>Informace o Vývojáři</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlín, Německo\n\n"
            "🚀 <b>Profesionální Profil:</b>\n"
            "• Motivovaný a vizionářský AI vývojář\n"
            "• Praktické zkušenosti s vývojem AI produktů a Data Science\n"
            "• Specializace na Machine Learning a Zpracování Přirozeného Jazyka\n"
            "• Silný Python programátor s full-stack schopnostmi\n"
            "• Zkušenosti s nasazením AI řešení pomocí Flask, Streamlit a Hugging Face\n\n"
            "💼 <b>Technické Kompetence:</b>\n"
            "• Vývoj AI & Machine Learning\n"
            "• Analýza & Vizualizace Dat\n"
            "• Zpracování Přirozeného Jazyka (NLP)\n"
            "• Generativní AI & Integrace LLM\n"
            "• Python, Flask, Streamlit, REST API\n"
            "• Webový Vývoj (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Kontakt & Profily:</b>\n"
            "📧 Email: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Vývojář tohoto profesionálního AI asistenta pro SHAWO Stěhování</i>"
        )
    },
    'hr': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI Programer & Full Stack Programer",
        'description': (
            "🔧 <b>Informacije o Programeru</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlin, Njemačka\n\n"
            "🚀 <b>Profesionalni Profil:</b>\n"
            "• Motivirani i budućnosti orijentirani AI programer\n"
            "• Praktično iskustvo u razvoju AI proizvoda i Data Science\n"
            "• Specijaliziran za Machine Learning i Obrada Prirodnog Jezika\n"
            "• Snažan Python programer s full-stack sposobnostima\n"
            "• Iskustvo u implementaciji AI rješenja s Flask, Streamlit i Hugging Face\n\n"
            "💼 <b>Tehničke Kompetencije:</b>\n"
            "• Razvoj AI & Machine Learning\n"
            "• Analiza & Vizualizacija Podataka\n"
            "• Obrada Prirodnog Jezika (NLP)\n"
            "• Generativna AI & LLM Integracija\n"
            "• Python, Flask, Streamlit, REST API\n"
            "• Web Razvoj (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Kontakt & Profili:</b>\n"
            "📧 Email: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Programer ovog profesionalnog AI asistenta za SHAWO Selidbe</i>"
        )
    },
    'bg': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI Разработчик & Full Stack Разработчик",
        'description': (
            "🔧 <b>Информация за Разработчика</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Берлин, Германия\n\n"
            "🚀 <b>Професионален Профил:</b>\n"
            "• Мотивиран и ориентиран към бъдещето AI разработчик\n"
            "• Практически опит в разработката на AI продукти и Data Science\n"
            "• Специализиран в Machine Learning и Обработка на Естествен Език\n"
            "• Силен Python програмист с full-stack възможности\n"
            "• Опит в внедряването на AI решения с Flask, Streamlit и Hugging Face\n\n"
            "💼 <b>Технически Компетенции:</b>\n"
            "• Разработка на AI & Machine Learning\n"
            "• Анализ & Визуализация на Данни\n"
            "• Обработка на Естествен Език (NLP)\n"
            "• Генеративен AI & LLM Интеграция\n"
            "• Python, Flask, Streamlit, REST API\n"
            "• Уеб Разработка (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Контакти & Профили:</b>\n"
            "📧 Имейл: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Разработчик на този професионален AI асистент за SHAWO Премествания</i>"
        )
    },
    'bn': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI ডেভেলপার & ফুল স্ট্যাক ডেভেলপার",
        'description': (
            "🔧 <b>ডেভেলপার তথ্য</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 বার্লিন, জার্মানি\n\n"
            "🚀 <b>পেশাদার প্রোফাইল:</b>\n"
            "• অনুপ্রাণিত এবং ভবিষ্যত-মুখী AI ডেভেলপার\n"
            "• AI পণ্য উন্নয়ন এবং ডেটা সায়েন্সে ব্যবহারিক অভিজ্ঞতা\n"
            "• মেশিন লার্নিং এবং প্রাকৃতিক ভাষা প্রক্রিয়াকরণে বিশেষজ্ঞ\n"
            "• ফুল-স্ট্যাক ক্ষমতা সহ শক্তিশালী পাইথন প্রোগ্রামার\n"
            "• Flask, Streamlit এবং Hugging Face দিয়ে AI সমাধান স্থাপনের অভিজ্ঞতা\n\n"
            "💼 <b>প্রযুক্তিগত দক্ষতা:</b>\n"
            "• AI & মেশিন লার্নিং ডেভেলপমেন্ট\n"
            "• ডেটা বিশ্লেষণ & ভিজ্যুয়ালাইজেশন\n"
            "• প্রাকৃতিক ভাষা প্রক্রিয়াকরণ (NLP)\n"
            "• জেনারেটিভ AI & LLM ইন্টিগ্রেশন\n"
            "• Python, Flask, Streamlit, REST API\n"
            "• ওয়েব ডেভেলপমেন্ট (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>যোগাযোগ & প্রোফাইল:</b>\n"
            "📧 ইমেল: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>SHAWO মুভার্সের জন্য এই পেশাদার AI সহকারীর ডেভেলপার</i>"
        )
    },
    'el': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI Προγραμματιστής & Full Stack Προγραμματιστής",
        'description': (
            "🔧 <b>Πληροφορίες Προγραμματιστή</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Βερολίνο, Γερμανία\n\n"
            "🚀 <b>Επαγγελματικό Προφίλ:</b>\n"
            "• Παρακινημένος και με προοπτική AI Προγραμματιστής\n"
            "• Πρακτική εμπειρία στην ανάπτυξη προϊόντων AI και Data Science\n"
            "• Εξειδικευμένος σε Machine Learning και Επεξεργασία Φυσικής Γλώσσας\n"
            "• Δυνατός προγραμματιστής Python με full-stack δυνατότητες\n"
            "• Εμπειρία στην ανάπτυξη λύσεων AI με Flask, Streamlit και Hugging Face\n\n"
            "💼 <b>Τεχνικές Ικανότητες:</b>\n"
            "• Ανάπτυξη AI & Machine Learning\n"
            "• Ανάλυση & Απεικόνιση Δεδομένων\n"
            "• Επεξεργασία Φυσικής Γλώσσας (NLP)\n"
            "• Generative AI & Ολοκλήρωση LLM\n"
            "• Python, Flask, Streamlit, REST APIs\n"
            "• Ανάπτυξη Ιστού (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Επικοινωνία & Προφίλ:</b>\n"
            "📧 Email: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Ο προγραμματιστής αυτού του επαγγελματικού AI βοηθού για SHAWO Μετακομίσεις</i>"
        )
    },
    'he': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "מפתח AI & מפתח Full Stack",
        'description': (
            "🔧 <b>מידע על המפתח</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 ברלין, גרמניה\n\n"
            "🚀 <b>פרופיל מקצועי:</b>\n"
            "• מפתח AI מונעת ובעלת חשיבה עתידית\n"
            "• ניסיון מעשי בפיתוח מוצרי AI ומדע נתונים\n"
            "• מומחה בלמידת מכונה ועיבוד שפה טבעית\n"
            "• מתכנת Python חזק עם יכולות full-stack\n"
            "• ניסיון בפריסת פתרונות AI עם Flask, Streamlit ו-Hugging Face\n\n"
            "💼 <b>יכולות טכניות:</b>\n"
            "• פיתוח AI & למידת מכונה\n"
            "• ניתוח & הדמיית נתונים\n"
            "• עיבוד שפה טבעית (NLP)\n"
            "• AI יצירתי & אינטגרציית LLM\n"
            "• Python, Flask, Streamlit, REST APIs\n"
            "• פיתוח אתרים (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>קשר & פרופילים:</b>\n"
            "📧 אימייל: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>המפתח של העוזר המקצועי הזה עבור SHAWO מעברים</i>"
        )
    },
    'hi': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI डेवलपर & फुल स्टैक डेवलपर",
        'description': (
            "🔧 <b>डेवलपर जानकारी</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 बर्लिन, जर्मनी\n\n"
            "🚀 <b>पेशेवर प्रोफाइल:</b>\n"
            "• प्रेरित और भविष्य-उन्मुख AI डेवलपर\n"
            "• AI उत्पाद विकास और डेटा साइंस में व्यावहारिक अनुभव\n"
            "• मशीन लर्निंग और प्राकृतिक भाषा प्रसंस्करण में विशेषज्ञ\n"
            "• फुल-स्टाक क्षमताओं वाला मजबूत पायथन प्रोग्रामर\n"
            "• Flask, Streamlit और Hugging Face के साथ AI समाधान तैनात करने का अनुभव\n\n"
            "💼 <b>तकनीकी क्षमताएं:</b>\n"
            "• AI & मशीन लर्निंग विकास\n"
            "• डेटा विश्लेषण & विज़ुअलाइज़ेशन\n"
            "• प्राकृतिक भाषा प्रसंस्करण (NLP)\n"
            "• जेनरेटिव AI & LLM एकीकरण\n"
            "• Python, Flask, Streamlit, REST APIs\n"
            "• वेब विकास (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>संपर्क & प्रोफाइल:</b>\n"
            "📧 ईमेल: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>SHAWO मूवर्स के लिए इस पेशेवर AI सहायक के डेवलपर</i>"
        )
    },
    'hu': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI Fejlesztő & Full Stack Fejlesztő",
        'description': (
            "🔧 <b>Fejlesztői Információ</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlin, Németország\n\n"
            "🚀 <b>Szakmai Profil:</b>\n"
            "• Motivált és jövőorientált AI Fejlesztő\n"
            "• Gyakorlati tapasztalat AI termékfejlesztésben és Adattudományban\n"
            "• Szakosodás a Gépi Tanulásra és Természetes Nyelvfeldolgozásra\n"
            "• Erős Python programozó full-stack képességekkel\n"
            "• Tapasztalat AI megoldások üzembe helyezésében Flask, Streamlit és Hugging Face segítségével\n\n"
            "💼 <b>Technikai Kompetenciák:</b>\n"
            "• AI & Gépi Tanulás Fejlesztés\n"
            "• Adatelemzés & Vizualizáció\n"
            "• Természetes Nyelvfeldolgozás (NLP)\n"
            "• Generatív AI & LLM Integráció\n"
            "• Python, Flask, Streamlit, REST API-k\n"
            "• Webfejlesztés (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Kapcsolat & Profilok:</b>\n"
            "📧 Email: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Ennek a professzionális AI asszisztensnek a fejlesztője a SHAWO Költöztetéshez</i>"
        )
    },
    'id': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "Pengembang AI & Pengembang Full Stack",
        'description': (
            "🔧 <b>Informasi Pengembang</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlin, Jerman\n\n"
            "🚀 <b>Profil Profesional:</b>\n"
            "• Pengembang AI yang termotivasi dan berorientasi masa depan\n"
            "• Pengalaman praktis dalam pengembangan produk AI dan Ilmu Data\n"
            "• Spesialis dalam Pembelajaran Mesin dan Pemrosesan Bahasa Alami\n"
            "• Pemrogram Python yang kuat dengan kemampuan full-stack\n"
            "• Pengalaman dalam menyebarkan solusi AI dengan Flask, Streamlit dan Hugging Face\n\n"
            "💼 <b>Kompetensi Teknis:</b>\n"
            "• Pengembangan AI & Pembelajaran Mesin\n"
            "• Analisis & Visualisasi Data\n"
            "• Pemrosesan Bahasa Alami (NLP)\n"
            "• AI Generatif & Integrasi LLM\n"
            "• Python, Flask, Streamlit, REST API\n"
            "• Pengembangan Web (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Kontak & Profil:</b>\n"
            "📧 Email: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Pengembang asisten AI profesional ini untuk SHAWO Pindahan</i>"
        )
    },
    'ms': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "Pembangun AI & Pembangun Full Stack",
        'description': (
            "🔧 <b>Maklumat Pembangun</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlin, Jerman\n\n"
            "🚀 <b>Profil Profesional:</b>\n"
            "• Pembangun AI yang bermotivasi dan berorientasi masa depan\n"
            "• Pengalaman praktikal dalam pembangunan produk AI dan Sains Data\n"
            "• Pakar dalam Pembelajaran Mesin dan Pemprosesan Bahasa Semula Jadi\n"
            "• Pengaturcara Python yang kuat dengan keupayaan full-stack\n"
            "• Pengalaman dalam menyebarkan penyelesaian AI dengan Flask, Streamlit dan Hugging Face\n\n"
            "💼 <b>Kecekapan Teknikal:</b>\n"
            "• Pembangunan AI & Pembelajaran Mesin\n"
            "• Analisis & Pemplotan Data\n"
            "• Pemprosesan Bahasa Semula Jadi (NLP)\n"
            "• AI Generatif & Integrasi LLM\n"
            "• Python, Flask, Streamlit, REST API\n"
            "• Pembangunan Web (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Hubungan & Profil:</b>\n"
            "📧 E-mel: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Pembangun pembantu AI profesional ini untuk SHAWO Pindahan</i>"
        )
    },
    'no': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI Utvikler & Full Stack Utvikler",
        'description': (
            "🔧 <b>Utviklerinformasjon</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlin, Tyskland\n\n"
            "🚀 <b>Profesjonell Profil:</b>\n"
            "• Motivert og fremtidsrettet AI Utvikler\n"
            "• Praktisk erfaring i AI produktutvikling og Data Science\n"
            "• Spesialisert i Maskinlæring og Natural Language Processing\n"
            "• Sterk Python programmerer med full-stack evner\n"
            "• Erfaring med å distribuere AI løsninger med Flask, Streamlit og Hugging Face\n\n"
            "💼 <b>Tekniske Kompetanser:</b>\n"
            "• AI & Maskinlæring Utvikling\n"
            "• Dataanalyse & Visualisering\n"
            "• Natural Language Processing (NLP)\n"
            "• Generativ AI & LLM Integrasjon\n"
            "• Python, Flask, Streamlit, REST API-er\n"
            "• Webutvikling (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Kontakt & Profiler:</b>\n"
            "📧 E-post: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Utvikleren av denne profesjonelle AI-assistenten for SHAWO Flyttetjenester</i>"
        )
    },
    'fi': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "AI Kehittäjä & Full Stack Kehittäjä",
        'description': (
            "🔧 <b>Kehittäjätiedot</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berliini, Saksa\n\n"
            "🚀 <b>Ammattiprofiili:</b>\n"
            "• Motivoitunut ja tulevaisuuteen suuntautunut AI-kehittäjä\n"
            "• Käytännön kokemusta AI-tuotekehityksestä ja Data Sciencestä\n"
            "• Erikoistunut Koneoppimiseen ja Luonnollisen Kielen Käsittelyyn\n"
            "• Vahva Python-ohjelmoija full-stack-kyvyillä\n"
            "• Kokemusta AI-ratkaisujen käyttöönotosta Flask, Streamlit ja Hugging Face -alustoilla\n\n"
            "💼 <b>Tekniset Pätevyydet:</b>\n"
            "• AI & Koneoppimisen Kehitys\n"
            "• Data-analyysi & Visualisointi\n"
            "• Luonnollisen Kielen Käsittely (NLP)\n"
            "• Generatiivinen AI & LLM Integraatio\n"
            "• Python, Flask, Streamlit, REST API:t\n"
            "• Web-kehitys (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Yhteystiedot & Profiilit:</b>\n"
            "📧 Sähköposti: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Tämän ammattimaisen AI-avustajan kehittäjä SHAWO Muuttoihin</i>"
        )
    },
    'th': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "นักพัฒนา AI & นักพัฒนา Full Stack",
        'description': (
            "🔧 <b>ข้อมูลนักพัฒนา</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 เบอร์ลิน, เยอรมนี\n\n"
            "🚀 <b>ประวัติส่วนตัวทางวิชาชีพ:</b>\n"
            "• นักพัฒนา AI ที่มีแรงจูงใจและมุ่งสู่อนาคต\n"
            "• ประสบการณ์ปฏิบัติในการพัฒนาผลิตภัณฑ์ AI และ Data Science\n"
            "• เชี่ยวชาญด้าน Machine Learning และ Natural Language Processing\n"
            "• โปรแกรมเมอร์ Python ที่แข็งแกร่งด้วยความสามารถแบบ full-stack\n"
            "• ประสบการณ์ในการปรับใช้โซลูชัน AI ด้วย Flask, Streamlit และ Hugging Face\n\n"
            "💼 <b>ความสามารถทางเทคนิค:</b>\n"
            "• การพัฒนา AI & Machine Learning\n"
            "• การวิเคราะห์ & การแสดงภาพข้อมูล\n"
            "• การประมวลผลภาษาธรรมชาติ (NLP)\n"
            "• Generative AI & การบูรณาการ LLM\n"
            "• Python, Flask, Streamlit, REST APIs\n"
            "• การพัฒนาเว็บ (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>การติดต่อ & โปรไฟล์:</b>\n"
            "📧 อีเมล: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>นักพัฒนาผู้ช่วย AI มืออาชีพนี้สำหรับ SHAWO การย้าย</i>"
        )
    },
    'vi': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "Nhà phát triển AI & Nhà phát triển Full Stack",
        'description': (
            "🔧 <b>Thông tin Nhà phát triển</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlin, Đức\n\n"
            "🚀 <b>Hồ sơ Chuyên nghiệp:</b>\n"
            "• Nhà phát triển AI có động lực và hướng tới tương lai\n"
            "• Kinh nghiệm thực tế trong phát triển sản phẩm AI và Khoa học Dữ liệu\n"
            "• Chuyên về Học máy và Xử lý Ngôn ngữ Tự nhiên\n"
            "• Lập trình viên Python mạnh mẽ với khả năng full-stack\n"
            "• Kinh nghiệm triển khai giải pháp AI với Flask, Streamlit và Hugging Face\n\n"
            "💼 <b>Năng lực Kỹ thuật:</b>\n"
            "• Phát triển AI & Học máy\n"
            "• Phân tích & Trực quan hóa Dữ liệu\n"
            "• Xử lý Ngôn ngữ Tự nhiên (NLP)\n"
            "• AI Tạo sinh & Tích hợp LLM\n"
            "• Python, Flask, Streamlit, REST APIs\n"
            "• Phát triển Web (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Liên hệ & Hồ sơ:</b>\n"
            "📧 Email: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Nhà phát triển trợ lý AI chuyên nghiệp này cho SHAWO Chuyển nhà</i>"
        )
    },
    'ro': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "Dezvoltator AI & Dezvoltator Full Stack",
        'description': (
            "🔧 <b>Informații Dezvoltator</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlin, Germania\n\n"
            "🚀 <b>Profil Profesional:</b>\n"
            "• Dezvoltator AI motivat și orientat spre viitor\n"
            "• Experiență practică în dezvoltarea produselor AI și Știința Datelor\n"
            "• Specializat în Machine Learning și Procesarea Limbajului Natural\n"
            "• Programator Python puternic cu capacități full-stack\n"
            "• Experiență în implementarea soluțiilor AI cu Flask, Streamlit și Hugging Face\n\n"
            "💼 <b>Competențe Tehnice:</b>\n"
            "• Dezvoltare AI & Machine Learning\n"
            "• Analiză & Vizualizare Date\n"
            "• Procesarea Limbajului Natural (NLP)\n"
            "• AI Generativă & Integrare LLM\n"
            "• Python, Flask, Streamlit, REST API-uri\n"
            "• Dezvoltare Web (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Contact & Profile:</b>\n"
            "📧 Email: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>Dezvoltatorul acestui asistent AI profesional pentru SHAWO Mutări</i>"
        )
    },
    'ca': {
        'name': "Mhd Fouaad Al Kamsha",
        'title': "Desenvolupador AI & Desenvolupador Full Stack",
        'description': (
            "🔧 <b>Informació del Desenvolupador</b>\n\n"
            "👨‍💻 <b>Mhd Fouaad Al Kamsha</b>\n"
            "📍 Berlín, Alemanya\n\n"
            "🚀 <b>Perfil Professional:</b>\n"
            "• Desenvolupador AI motivat i orientat al futur\n"
            "• Experiència pràctica en desenvolupament de productes AI i Ciència de Dades\n"
            "• Especialitzat en Aprenentatge Automàtic i Processament de Llenguatge Natural\n"
            "• Fort programador Python amb capacitats full-stack\n"
            "• Experiència implementant solucions AI amb Flask, Streamlit i Hugging Face\n\n"
            "💼 <b>Competències Tècniques:</b>\n"
            "• Desenvolupament AI & Aprenentatge Automàtic\n"
            "• Anàlisi & Visualització de Dades\n"
            "• Processament de Llenguatge Natural (NLP)\n"
            "• AI Generativa & Integració LLM\n"
            "• Python, Flask, Streamlit, APIs REST\n"
            "• Desenvolupament Web (HTML, CSS, JavaScript)\n\n"
            "🌐 <b>Contacte & Perfils:</b>\n"
            "📧 Correu: alkamsha.berlin@gmail.com\n"
            "💼 LinkedIn: https://www.linkedin.com/in/mhd-fouaad-al-kamsha-6299b618b\n"
            "💻 GitHub: https://github.com/FouaadAI\n\n"
            "<i>El desenvolupador d'aquest assistent AI professional per a SHAWO Mudances</i>"
        )
    }
}

# 🌍 VERBESSERTE MEHRSPRACHIGE NACHRICHTEN FÜR SPRACHKORREKTUR
LANGUAGE_CORRECTION_RESPONSES = {
    'de': {
        'correction': (
            "😊 <b>Sprache anpassen</b>\n\n"
            "Es tut mir leid, dass ich in der falschen Sprache antworte! 🙏\n\n"
            "🌍 <b>In welcher Sprache möchten Sie kommunizieren?</b>\n\n"
            "• Deutsch\n• Englisch\n• Arabisch\n• Französisch\n• Spanisch\n"
            "• Oder eine andere Sprache?\n\n"
            "Bitte teilen Sie mir Ihre bevorzugte Sprache mit! 😊"
        ),
        'confirmed': (
            "✅ <b>Perfekt! Sprache gespeichert.</b>\n\n"
            "Ich werde ab jetzt auf {language} mit Ihnen kommunizieren. "
            "Wie kann ich Ihnen helfen? 😊"
        )
    },
    'en': {
        'correction': (
            "😊 <b>Language Adjustment</b>\n\n"
            "I'm sorry for responding in the wrong language! 🙏\n\n"
            "🌍 <b>In which language would you like to communicate?</b>\n\n"
            "• German\n• English\n• Arabic\n• French\n• Spanish\n"
            "• Or another language?\n\n"
            "Please tell me your preferred language! 😊"
        ),
        'confirmed': (
            "✅ <b>Perfect! Language saved.</b>\n\n"
            "I will communicate with you in {language} from now on. "
            "How can I help you? 😊"
        )
    },
    'ar': {
        'correction': (
            "😊 <b>ضبط اللغة</b>\n\n"
            "أعتذر للرد باللغة الخاطئة! 🙏\n\n"
            "🌍 <b>بأي لغة تود التواصل؟</b>\n\n"
            "• ألمانية\n• إنجليزية\n• عربية\n• فرنسية\n• إسبانية\n"
            "• أو لغة أخرى؟\n\n"
            "يرجى إخباري باللغة المفضلة لديك! 😊"
        ),
        'confirmed': (
            "✅ <b>ممتاز! تم حفظ اللغة.</b>\n\n"
            "سأتحدث معك باللغة {language} من الآن فصاعدًا. "
            "كيف يمكنني مساعدتك؟ 😊"
        )
    },
    'fr': {
        'correction': (
            "😊 <b>Ajustement de la langue</b>\n\n"
            "Je m'excuse de répondre dans la mauvaise langue ! 🙏\n\n"
            "🌍 <b>Dans quelle langue souhaitez-vous communiquer ?</b>\n\n"
            "• Allemand\n• Anglais\n• Arabe\n• Français\n• Espagnol\n"
            "• Ou une autre langue ?\n\n"
            "Veuillez me dire votre langue préférée ! 😊"
        ),
        'confirmed': (
            "✅ <b>Parfait ! Langue enregistrée.</b>\n\n"
            "Je communiquerai avec vous en {language} à partir de maintenant. "
            "Comment puis-je vous aider ? 😊"
        )
    },
    'es': {
        'correction': (
            "😊 <b>Ajuste de idioma</b>\n\n"
            "¡Lamento responder en el idioma incorrecto! 🙏\n\n"
            "🌍 <b>¿En qué idioma le gustaría comunicarse?</b>\n\n"
            "• Alemán\n• Inglés\n• Árabe\n• Francés\n• Español\n"
            "• ¿U otro idioma?\n\n"
            "¡Por favor dígame su idioma preferido! 😊"
        ),
        'confirmed': (
            "✅ <b>¡Perfecto! Idioma guardado.</b>\n\n"
            "Me comunicaré con usted en {language} a partir de ahora. "
            "¿Cómo puedo ayudarle? 😊"
        )
    },
    'it': {
        'correction': (
            "😊 <b>Regolazione lingua</b>\n\n"
            "Mi dispiace per aver risposto nella lingua sbagliata! 🙏\n\n"
            "🌍 <b>In quale lingua desidera comunicare?</b>\n\n"
            "• Tedesco\n• Inglese\n• Arabo\n• Francese\n• Spagnolo\n"
            "• O un'altra lingua?\n\n"
            "Per favore mi dica la sua lingua preferita! 😊"
        ),
        'confirmed': (
            "✅ <b>Perfetto! Lingua salvata.</b>\n\n"
            "D'ora in poi comunicherò con lei in {language}. "
            "Come posso aiutarla? 😊"
        )
    },
    'tr': {
        'correction': (
            "😊 <b>Dil Ayarlama</b>\n\n"
            "Yanlış dilde yanıt verdiğim için özür dilerim! 🙏\n\n"
            "🌍 <b>Hangi dilde iletişim kurmak istiyorsunuz?</b>\n\n"
            "• Almanca\n• İngilizce\n• Arapça\n• Fransızca\n• İspanyolca\n"
            "• Veya başka bir dil?\n\n"
            "Lütfen tercih ettiğiniz dili söyleyin! 😊"
        ),
        'confirmed': (
            "✅ <b>Mükemmel! Dil kaydedildi.</b>\n\n"
            "Bundan sonra sizinle {language} dilinde iletişim kuracağım. "
            "Size nasıl yardımcı olabilirim? 😊"
        )
    },
    'ru': {
        'correction': (
            "😊 <b>Настройка языка</b>\n\n"
            "Извините за ответ на неправильном языке! 🙏\n\n"
            "🌍 <b>На каком языке вы хотели бы общаться?</b>\n\n"
            "• Немецкий\n• Английский\n• Арабский\n• Французский\n• Испанский\n"
            "• Или другой язык?\n\n"
            "Пожалуйста, сообщите ваш предпочтительный язык! 😊"
        ),
        'confirmed': (
            "✅ <b>Отлично! Язык сохранен.</b>\n\n"
            "Теперь я буду общаться с вами на {language}. "
            "Как я могу вам помочь? 😊"
        )
    },
    'pl': {
        'correction': (
            "😊 <b>Dostosowanie języka</b>\n\n"
            "Przepraszam za odpowiedź w niewłaściwym języku! 🙏\n\n"
            "🌍 <b>W jakim języku chciałbyś się komunikować?</b>\n\n"
            "• Niemiecki\n• Angielski\n• Arabski\n• Francuski\n• Hiszpański\n"
            "• A może inny język?\n\n"
            "Proszę powiedzieć mi swój preferowany język! 😊"
        ),
        'confirmed': (
            "✅ <b>Doskonale! Język zapisany.</b>\n\n"
            "Od teraz będę komunikować się z Tobą w języku {language}. "
            "Jak mogę Ci pomóc? 😊"
        )
    },
    'uk': {
        'correction': (
            "😊 <b>Налаштування мови</b>\n\n"
            "Вибачте за відповідь не тією мовою! 🙏\n\n"
            "🌍 <b>Якою мовою ви хотіли б спілкуватися?</b>\n\n"
            "• Німецька\n• Англійська\n• Арабська\n• Французька\n• Іспанська\n"
            "• Чи інша мова?\n\n"
            "Будь ласка, повідомте вашу бажану мову! 😊"
        ),
        'confirmed': (
            "✅ <b>Відмінно! Мову збережено.</b>\n\n"
            "Відтепер я спілкуватимуся з вами {language}. "
            "Як я можу вам допомогти? 😊"
        )
    },
    'zh': {
        'correction': (
            "😊 <b>语言调整</b>\n\n"
            "很抱歉用错误的语言回复！🙏\n\n"
            "🌍 <b>您希望使用哪种语言交流？</b>\n\n"
            "• 德语\n• 英语\n• 阿拉伯语\n• 法语\n• 西班牙语\n"
            "• 或其他语言？\n\n"
            "请告诉我您偏好的语言！😊"
        ),
        'confirmed': (
            "✅ <b>完美！语言已保存。</b>\n\n"
            "从现在开始我将用{language}与您交流。"
            "我如何能帮助您？😊"
        )
    },
    'ja': {
        'correction': (
            "😊 <b>言語調整</b>\n\n"
            "間違った言語で返信して申し訳ございません！🙏\n\n"
            "🌍 <b>どの言語でコミュニケーションを希望しますか？</b>\n\n"
            "• ドイツ語\n• 英語\n• アラビア語\n• フランス語\n• スペイン語\n"
            "• または他の言語？\n\n"
            "希望の言語を教えてください！😊"
        ),
        'confirmed': (
            "✅ <b>完璧！言語を保存しました。</b>\n\n"
            "今後は{language}でコミュニケーションします。"
            "どのようにお手伝いできますか？😊"
        )
    },
    'ko': {
        'correction': (
            "😊 <b>언어 조정</b>\n\n"
            "잘못된 언어로 답변해서 죄송합니다! 🙏\n\n"
            "🌍 <b>어떤 언어로 소통을 원하시나요?</b>\n\n"
            "• 독일어\n• 영어\n• 아랍어\n• 프랑스어\n• 스페인어\n"
            "• 또는 다른 언어?\n\n"
            "선호하는 언어를 알려주세요! 😊"
        ),
        'confirmed': (
            "✅ <b>완fect! 언어가 저장되었습니다.</b>\n\n"
            "지금부터 {language}로 소통하겠습니다. "
            "어떻게 도와드릴까요? 😊"
        )
    },
    'pt': {
        'correction': (
            "😊 <b>Ajuste de Idioma</b>\n\n"
            "Desculpe por responder no idioma errado! 🙏\n\n"
            "🌍 <b>Em qual idioma você gostaria de se comunicar?</b>\n\n"
            "• Alemão\n• Inglês\n• Árabe\n• Francês\n• Espanhol\n"
            "• Ou outro idioma?\n\n"
            "Por favor me diga seu idioma preferido! 😊"
        ),
        'confirmed': (
            "✅ <b>Perfeito! Idioma salvo.</b>\n\n"
            "Vou me comunicar com você em {language} a partir de agora. "
            "Como posso ajudá-lo? 😊"
        )
    },
    'nl': {
        'correction': (
            "😊 <b>Taalaanpassing</b>\n\n"
            "Sorry dat ik in de verkeerde taal antwoord! 🙏\n\n"
            "🌍 <b>In welke taal wilt u communiceren?</b>\n\n"
            "• Duits\n• Engels\n• Arabisch\n• Frans\n• Spaans\n"
            "• Of een andere taal?\n\n"
            "Vertel me alstublieft uw voorkeurstaal! 😊"
        ),
        'confirmed': (
            "✅ <b>Perfect! Taal opgeslagen.</b>\n\n"
            "Ik zal vanaf nu met u communiceren in het {language}. "
            "Hoe kan ik u helpen? 😊"
        )
    },
    'sv': {
        'correction': (
            "😊 <b>Språkinställning</b>\n\n"
            "Jag är ledsen för att jag svarade på fel språk! 🙏\n\n"
            "🌍 <b>På vilket språk vill du kommunicera?</b>\n\n"
            "• Tyska\n• Engelska\n• Arabiska\n• Franska\n• Spanska\n"
            "• Eller ett annat språk?\n\n"
            "Berätta vilket språk du föredrar! 😊"
        ),
        'confirmed': (
            "✅ <b>Perfekt! Språk sparat.</b>\n\n"
            "Jag kommer att kommunicera med dig på {language} från och med nu. "
            "Hur kan jag hjälpa dig? 😊"
        )
    },
    'da': {
        'correction': (
            "😊 <b>Sprogjustering</b>\n\n"
            "Undskyld at jeg svarer på det forkerte sprog! 🙏\n\n"
            "🌍 <b>Hvilket sprog vil du gerne kommunikere på?</b>\n\n"
            "• Tysk\n• Engelsk\n• Arabisk\n• Fransk\n• Spansk\n"
            "• Eller et andet sprog?\n\n"
            "Fortæl mig venligst dit foretrukne sprog! 😊"
        ),
        'confirmed': (
            "✅ <b>Perfekt! Sprog gemt.</b>\n\n"
            "Jeg vil kommunikere med dig på {language} fra nu af. "
            "Hvordan kan jeg hjælpe dig? 😊"
        )
    },
    'cs': {
        'correction': (
            "😊 <b>Úprava jazyka</b>\n\n"
            "Omlouvám se za odpověď ve špatném jazyce! 🙏\n\n"
            "🌍 <b>V jakém jazyce chcete komunikovat?</b>\n\n"
            "• Němčina\n• Angličtina\n• Arabština\n• Francouzština\n• Španělština\n"
            "• Nebo jiný jazyk?\n\n"
            "Řekněte mi prosím váš preferovaný jazyk! 😊"
        ),
        'confirmed': (
            "✅ <b>Perfektní! Jazyk uložen.</b>\n\n"
            "Od nynějška s vámi budu komunikovat v {language}. "
            "Jak vám mohu pomoci? 😊"
        )
    },
    'hr': {
        'correction': (
            "😊 <b>Prilagodba jezika</b>\n\n"
            "Žao mi je što odgovaram na pogrešnom jeziku! 🙏\n\n"
            "🌍 <b>Na kojem jeziku želite komunicirati?</b>\n\n"
            "• Njemački\n• Engleski\n• Arapski\n• Francuski\n• Španjolski\n"
            "• Ili drugi jezik?\n\n"
            "Molim vas recite mi vaš željeni jezik! 😊"
        ),
        'confirmed': (
            "✅ <b>Savršeno! Jezik spremljen.</b>\n\n"
            "Od sada ću s vama komunicirati na {language}. "
            "Kako vam mogu pomoći? 😊"
        )
    },
    'bg': {
        'correction': (
            "😊 <b>Настройка на езика</b>\n\n"
            "Съжалявам, че отговорих на грешен език! 🙏\n\n"
            "🌍 <b>На кой език бихте искали да общувате?</b>\n\n"
            "• Немски\n• Английски\n• Арабски\n• Френски\n• Испански\n"
            "• Или друг език?\n\n"
            "Моля, кажете ми предпочитания от вас език! 😊"
        ),
        'confirmed': (
            "✅ <b>Перфектно! Езикът е запазен.</b>\n\n"
            "От сега нататък ще общувам с вас на {language}. "
            "Как мога да ви помогна? 😊"
        )
    },
    'bn': {
        'correction': (
            "😊 <b>ভাষা সমন্বয়</b>\n\n"
            "ভুল ভাষায় উত্তর দেওয়ার জন্য আমি ক্ষমাপ্রার্থী! 🙏\n\n"
            "🌍 <b>আপনি কোন ভাষায় যোগাযোগ করতে চান?</b>\n\n"
            "• জার্মান\n• ইংরেজি\n• আরবি\n• ফরাসি\n• স্প্যানিশ\n"
            "• অথবা অন্য কোন ভাষা?\n\n"
            "দয়া করে আপনার পছন্দের ভাষা告诉我! 😊"
        ),
        'confirmed': (
            "✅ <b>নিখুঁত! ভাষা সংরক্ষিত।</b>\n\n"
            "এখন থেকে আমি আপনার সাথে {language} ভাষায় যোগাযোগ করব। "
            "আমি আপনাকে কিভাবে সাহায্য করতে পারি? 😊"
        )
    },
    'el': {
        'correction': (
            "😊 <b>Προσαρμογή γλώσσας</b>\n\n"
            "Λυπάμαι που απαντώ σε λάθος γλώσσα! 🙏\n\n"
            "🌍 <b>Σε ποια γλώσσα θα θέλατε να επικοινωνήσετε;</b>\n\n"
            "• Γερμανικά\n• Αγγλικά\n• Αραβικά\n• Γαλλικά\n• Ισπανικά\n"
            "• Ή άλλη γλώσσα;\n\n"
            "Παρακαλώ πείτε μου την προτιμώμενη γλώσσα σας! 😊"
        ),
        'confirmed': (
            "✅ <b>Τέλεια! Η γλώσσα αποθηκεύτηκε.</b>\n\n"
            "Από δω και πέρα θα επικοινωνώ μαζί σας στα {language}. "
            "Πώς μπορώ να σας βοηθήσω; 😊"
        )
    },
    'he': {
        'correction': (
            "😊 <b>התאמת שפה</b>\n\n"
            "אני מתנצל על כך שעניתי בשפה הלא נכונה! 🙏\n\n"
            "🌍 <b>באיזו שפה תרצה לתקשר?</b>\n\n"
            "• גרמנית\n• אנגלית\n• ערבית\n• צרפתית\n• ספרדית\n"
            "• או שפה אחרת?\n\n"
            "אנא ספר לי מהי השפה המועדפת עליך! 😊"
        ),
        'confirmed': (
            "✅ <b>מושלם! שפה נשמרה.</b>\n\n"
            "מעתה אתקשר איתך ב{language}. "
            "כיצד אוכל לעזור לך? 😊"
        )
    },
    'hi': {
        'correction': (
            "😊 <b>भाषा समायोजन</b>\n\n"
            "गलत भाषा में जवाब देने के लिए क्षमा चाहता हूं! 🙏\n\n"
            "🌍 <b>आप किस भाषा में संवाद करना चाहेंगे?</b>\n\n"
            "• जर्मन\n• अंग्रेजी\n• अरबी\n• फ्रेंच\n• स्पेनिश\n"
            "• या कोई अन्य भाषा?\n\n"
            "कृपया मुझे अपनी पसंदीदा भाषा बताएं! 😊"
        ),
        'confirmed': (
            "✅ <b>बिल्कुल सही! भाषा सहेजी गई।</b>\n\n"
            "अब से मैं आपसे {language} में संवाद करूंगा। "
            "मैं आपकी कैसे मदद कर सकता हूं? 😊"
        )
    },
    'hu': {
        'correction': (
            "😊 <b>Nyelvi beállítás</b>\n\n"
            "Elnézést, hogy rossz nyelven válaszolok! 🙏\n\n"
            "🌍 <b>Milyen nyelven szeretne kommunikálni?</b>\n\n"
            "• Német\n• Angol\n• Arab\n• Francia\n• Spanyol\n"
            "• Vagy más nyelv?\n\n"
            "Kérem, mondja meg az előnyben részesített nyelvét! 😊"
        ),
        'confirmed': (
            "✅ <b>Tökéletes! Nyelv elmentve.</b>\n\n"
            "Mostantól {language} nyelven fogok Önnel kommunikálni. "
            "Hogyan segíthetek? 😊"
        )
    },
    'id': {
        'correction': (
            "😊 <b>Penyesuaian Bahasa</b>\n\n"
            "Maaf telah merespons dalam bahasa yang salah! 🙏\n\n"
            "🌍 <b>Dalam bahasa apa Anda ingin berkomunikasi?</b>\n\n"
            "• Jerman\n• Inggris\n• Arab\n• Prancis\n• Spanyol\n"
            "• Atau bahasa lain?\n\n"
            "Tolong beri tahu saya bahasa pilihan Anda! 😊"
        ),
        'confirmed': (
            "✅ <b>Sempurna! Bahasa disimpan.</b>\n\n"
            "Saya akan berkomunikasi dengan Anda dalam bahasa {language} mulai sekarang. "
            "Bagaimana saya bisa membantu Anda? 😊"
        )
    },
    'ms': {
        'correction': (
            "😊 <b>Pelarasan Bahasa</b>\n\n"
            "Maaf kerana menjawab dalam bahasa yang salah! 🙏\n\n"
            "🌍 <b>Dalam bahasa mana anda ingin berkomunikasi?</b>\n\n"
            "• Jerman\n• Inggeris\n• Arab\n• Perancis\n• Sepanyol\n"
            "• Atau bahasa lain?\n\n"
            "Sila beritahu saya bahasa pilihan anda! 😊"
        ),
        'confirmed': (
            "✅ <b>Sempurna! Bahasa disimpan.</b>\n\n"
            "Saya akan berkomunikasi dengan anda dalam bahasa {language} mulai sekarang. "
            "Bagaimana saya boleh membantu anda? 😊"
        )
    },
    'no': {
        'correction': (
            "😊 <b>Språktilpasning</b>\n\n"
            "Beklager at jeg svarer på feil språk! 🙏\n\n"
            "🌍 <b>Hvilket språk ønsker du å kommunisere på?</b>\n\n"
            "• Tysk\n• Engelsk\n• Arabisk\n• Fransk\n• Spansk\n"
            "• Eller et annet språk?\n\n"
            "Vennligst fortell meg ditt foretrukne språk! 😊"
        ),
        'confirmed': (
            "✅ <b>Perfekt! Språk lagret.</b>\n\n"
            "Jeg vil kommunisere med deg på {language} fra nå av. "
            "Hvordan kan jeg hjelpe deg? 😊"
        )
    },
    'fi': {
        'correction': (
            "😊 <b>Kielen säätö</b>\n\n"
            "Anteeksi, että vastaan väärällä kielellä! 🙏\n\n"
            "🌍 <b>Millä kielellä haluaisit kommunikoida?</b>\n\n"
            "• Saksa\n• Englanti\n• Arabia\n• Ranska\n• Espanja\n"
            "• Tai toinen kieli?\n\n"
            "Kerro minulle mieluisasi kieli! 😊"
        ),
        'confirmed': (
            "✅ <b>Täydellistä! Kieli tallennettu.</b>\n\n"
            "Kommunikoin kanssasi kielellä {language} tästä lähtien. "
            "Miten voin auttaa sinua? 😊"
        )
    },
    'th': {
        'correction': (
            "😊 <b>การปรับภาษา</b>\n\n"
            "ขออภัยที่ตอบผิดภาษา! 🙏\n\n"
            "🌍 <b>คุณต้องการสื่อสารด้วยภาษาใด?</b>\n\n"
            "• เยอรมัน\n• อังกฤษ\n• อาหรับ\n• ฝรั่งเศส\n• สเปน\n"
            "• หรือภาษาอื่น?\n\n"
            "กรุณาบอกภาษาที่คุณต้องการ! 😊"
        ),
        'confirmed': (
            "✅ <b>สมบูรณ์แบบ! บันทึกภาษาแล้ว</b>\n\n"
            "จากนี้ไปฉันจะสื่อสารกับคุณเป็นภาษา {language} "
            "ฉันสามารถช่วยคุณได้อย่างไร? 😊"
        )
    },
    'vi': {
        'correction': (
            "😊 <b>Điều chỉnh ngôn ngữ</b>\n\n"
            "Xin lỗi vì đã trả lời sai ngôn ngữ! 🙏\n\n"
            "🌍 <b>Bạn muốn giao tiếp bằng ngôn ngữ nào?</b>\n\n"
            "• Tiếng Đức\n• Tiếng Anh\n• Tiếng Ả Rập\n• Tiếng Pháp\n• Tiếng Tây Ban Nha\n"
            "• Hay ngôn ngữ khác?\n\n"
            "Vui lòng cho tôi biết ngôn ngữ ưa thích của bạn! 😊"
        ),
        'confirmed': (
            "✅ <b>Hoàn hảo! Đã lưu ngôn ngữ.</b>\n\n"
            "Từ giờ tôi sẽ giao tiếp với bạn bằng {language}. "
            "Tôi có thể giúp gì cho bạn? 😊"
        )
    },
    'ro': {
        'correction': (
            "😊 <b>Reglare limbă</b>\n\n"
            "Îmi cer scuze că răspund în limba greșită! 🙏\n\n"
            "🌍 <b>În ce limbă doriți să comunicați?</b>\n\n"
            "• Germană\n• Engleză\n• Arabă\n• Franceză\n• Spaniolă\n"
            "• Sau altă limbă?\n\n"
            "Vă rog să-mi spuneți limba preferată! 😊"
        ),
        'confirmed': (
            "✅ <b>Perfect! Limba salvată.</b>\n\n"
            "De acum voi comunica cu dumneavoastră în {language}. "
            "Cum vă pot ajuta? 😊"
        )
    },
    'ca': {
        'correction': (
            "😊 <b>Ajust de llengua</b>\n\n"
            "Em disculpo per respondre en l'idioma equivocat! 🙏\n\n"
            "🌍 <b>En quina llengua li agradaria comunicar-se?</b>\n\n"
            "• Alemany\n• Anglès\n• Àrab\n• Francès\n• Espanyol\n"
            "• O una altra llengua?\n\n"
            "Si us plau, digue'm la seva llengua preferida! 😊"
        ),
        'confirmed': (
            "✅ <b>Perfecte! Llengua desada.</b>\n\n"
            "A partir d'ara em comunicaré amb vostè en {language}. "
            "Com puc ajudar-lo? 😊"
        )
    }
}

# 📅 KALENDER-FUNKTIONEN FÜR BEFEHLE
async def calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zeigt den aktuellen Kalender mit gebuchten Terminen"""
    user = update.effective_user
    name = user.username or user.full_name or f"ID:{user.id}"
    
    # Telegram-Sprache erkennen
    user_language = detect_telegram_language(update)
    
    # Kalender-Manager verwenden
    calendar_manager = CalendarManager()
    current_date = datetime.now()
    
    # Kalender für aktuellen Monat generieren
    calendar_view = calendar_manager.generate_calendar_view(
        current_date.year, current_date.month, user_language
    )
    
    # Gebuchte Tage für diesen Monat
    booked_days = calendar_manager.get_appointments_for_month(current_date.year, current_date.month)
    blocked_days = calendar_manager.get_blocked_days_for_month(current_date.year, current_date.month)
    
    # Passende Nachricht basierend auf Sprache auswählen
    messages = MULTILINGUAL_RESPONSES.get(user_language, MULTILINGUAL_RESPONSES['de'])
    calendar_msg = messages['calendar']
    
    if booked_days or blocked_days:
        all_booked = booked_days + blocked_days
        booked_days_str = ", ".join([datetime.strptime(day, "%Y-%m-%d").strftime("%d.%m.%Y") for day in all_booked])
        calendar_info = (
            f"{calendar_msg['title']}\n\n"
            f"{calendar_msg['view'].format(calendar_view=calendar_view)}\n\n"
            f"{calendar_msg['booked_days'].format(booked_days=booked_days_str)}\n\n"
            f"{calendar_msg['instructions']}"
        )
    else:
        calendar_info = (
            f"{calendar_msg['title']}\n\n"
            f"{calendar_msg['view'].format(calendar_view=calendar_view)}\n\n"
            f"{calendar_msg['no_bookings']}\n\n"
            f"{calendar_msg['instructions']}"
        )
    
    formatted_calendar = convert_to_html(calendar_info)
    await update.message.reply_text(formatted_calendar, parse_mode=ParseMode.HTML)
    
    admin_msg = format_admin_message(
        name, user.id, user_language, "/calendar", formatted_calendar
    )
    await context.bot.send_message(
        chat_id=context.bot_data['ADMIN_CHAT_ID'], 
        text=admin_msg, 
        parse_mode=ParseMode.HTML
    )
    
    save_chat(user.id, name, "/calendar", formatted_calendar)

async def book_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bucht einen Termin basierend auf dem Befehl"""
    user = update.effective_user
    name = user.username or user.full_name or f"ID:{user.id}"
    user_language = detect_telegram_language(update)
    
    # Prüfe ob ein Datum angegeben wurde
    if not context.args:
        messages = MULTILINGUAL_RESPONSES.get(user_language, MULTILINGUAL_RESPONSES['de'])
        booking_msg = messages['booking']
        
        instructions = booking_msg['instructions']
        formatted_instructions = convert_to_html(instructions)
        await update.message.reply_text(formatted_instructions, parse_mode=ParseMode.HTML)
        return
    
    date_str = context.args[0]
    
    # Datum validieren
    try:
        booking_date = datetime.strptime(date_str, "%d.%m.%Y")
        current_date = datetime.now()
        
        # Prüfe ob Datum in der Vergangenheit liegt
        if booking_date.date() < current_date.date():
            messages = MULTILINGUAL_RESPONSES.get(user_language, MULTILINGUAL_RESPONSES['de'])
            booking_msg = messages['booking']
            
            error_msg = booking_msg['past_date']
            formatted_error = convert_to_html(error_msg)
            await update.message.reply_text(formatted_error, parse_mode=ParseMode.HTML)
            return
        
        # Format für Datenbank
        db_date_str = booking_date.strftime("%Y-%m-%d")
        
    except ValueError:
        messages = MULTILINGUAL_RESPONSES.get(user_language, MULTILINGUAL_RESPONSES['de'])
        booking_msg = messages['booking']
        
        error_msg = booking_msg['invalid_date']
        formatted_error = convert_to_html(error_msg)
        await update.message.reply_text(formatted_error, parse_mode=ParseMode.HTML)
        return
    
    # Frage nach weiteren Informationen
    context.user_data['pending_booking'] = {
        'date': db_date_str,
        'display_date': date_str
    }
    
    questions = {
        'de': (
            "📅 <b>Terminbuchung für {date}</b>\n\n"
            "Bitte teilen Sie mir folgende Informationen mit:\n\n"
            "1. <b>Ihr vollständiger Name:</b>\n"
            "2. <b>Telefonnummer für Rückfragen:</b>\n"
            "3. <b>Gewünschte Dienstleistung:</b>\n   (Umzug, Malerarbeiten, Reinigung, etc.)\n\n"
            "Sie können alle Informationen in einer Nachricht senden! 😊"
        ),
        'en': (
            "📅 <b>Appointment booking for {date}</b>\n\n"
            "Please provide the following information:\n\n"
            "1. <b>Your full name:</b>\n"
            "2. <b>Phone number for contact:</b>\n"
            "3. <b>Desired service:</b>\n   (Move, Painting, Cleaning, etc.)\n\n"
            "You can send all information in one message! 😊"
        ),
        'ar': (
            "📅 <b>حجز موعد لتاريخ {date}</b>\n\n"
            "يرجى تقديم المعلومات التالية:\n\n"
            "1. <b>اسمك الكامل:</b>\n"
            "2. <b>رقم الهاتف للاتصال:</b>\n"
            "3. <b>الخدمة المطلوبة:</b>\n   (نقل, دهان, تنظيف, إلخ)\n\n"
            "يمكنك إرسال جميع المعلومات في رسالة واحدة! 😊"
        ),
        'fr': (
            "📅 <b>Réservation de rendez-vous pour le {date}</b>\n\n"
            "Veuillez fournir les informations suivantes :\n\n"
            "1. <b>Votre nom complet :</b>\n"
            "2. <b>Numéro de téléphone pour contact :</b>\n"
            "3. <b>Service souhaité :</b>\n   (Déménagement, Peinture, Nettoyage, etc.)\n\n"
            "Vous pouvez envoyer toutes les informations en un seul message ! 😊"
        ),
        'es': (
            "📅 <b>Reserva de cita para el {date}</b>\n\n"
            "Por favor proporcione la siguiente información:\n\n"
            "1. <b>Su nombre completo:</b>\n"
            "2. <b>Número de teléfono para contacto:</b>\n"
            "3. <b>Servicio deseado:</b>\n   (Mudanza, Pintura, Limpieza, etc.)\n\n"
            "¡Puede enviar toda la información en un solo mensaje! 😊"
        ),
        'it': (
            "📅 <b>Prenotazione appuntamento per il {date}</b>\n\n"
            "Si prega di fornire le seguenti informazioni:\n\n"
            "1. <b>Il tuo nome completo:</b>\n"
            "2. <b>Numero di telefono per contatto:</b>\n"
            "3. <b>Servizio desiderato:</b>\n   (Trasloco, Pittura, Pulizia, ecc.)\n\n"
            "Puoi inviare tutte le informazioni in un unico messaggio! 😊"
        ),
        'tr': (
            "📅 <b>{date} tarihi için randevu rezervasyonu</b>\n\n"
            "Lütfen aşağıdaki bilgileri sağlayın:\n\n"
            "1. <b>Tam adınız:</b>\n"
            "2. <b>İletişim telefon numarası:</b>\n"
            "3. <b>İstenen hizmet:</b>\n   (Taşınma, Boyama, Temizlik, vb.)\n\n"
            "Tüm bilgileri tek mesajda gönderebilirsiniz! 😊"
        ),
        'ru': (
            "📅 <b>Бронирование встречи на {date}</b>\n\n"
            "Пожалуйста, предоставьте следующую информацию:\n\n"
            "1. <b>Ваше полное имя:</b>\n"
            "2. <b>Номер телефона для связи:</b>\n"
            "3. <b>Желаемая услуга:</b>\n   (Переезд, Покраска, Уборка, и т.д.)\n\n"
            "Вы можете отправить всю информацию в одном сообщении! 😊"
        ),
        'pl': (
            "📅 <b>Rezerwacja terminu na {date}</b>\n\n"
            "Proszę podać następujące informacje:\n\n"
            "1. <b>Twoje pełne imię i nazwisko:</b>\n"
            "2. <b>Numer telefonu do kontaktu:</b>\n"
            "3. <b>Pożądana usługa:</b>\n   (Przeprowadzka, Malowanie, Sprzątanie, itp.)\n\n"
            "Możesz wysłać wszystkie informacje w jednej wiadomości! 😊"
        ),
        'uk': (
            "📅 <b>Бронювання зустрічі на {date}</b>\n\n"
            "Будь ласка, надайте наступну інформацію:\n\n"
            "1. <b>Ваше повне ім'я:</b>\n"
            "2. <b>Номер телефону для зв'язку:</b>\n"
            "3. <b>Бажана послуга:</b>\n   (Переїзд, Фарбування, Прибирання, тощо)\n\n"
            "Ви можете надіслати всю інформацію в одному повідомленні! 😊"
        ),
        'zh': (
            "📅 <b>预约日期 {date}</b>\n\n"
            "请提供以下信息:\n\n"
            "1. <b>您的全名:</b>\n"
            "2. <b>联系电话号码:</b>\n"
            "3. <b>所需服务:</b>\n   (搬家, 油漆, 清洁, 等)\n\n"
            "您可以在一条消息中发送所有信息! 😊"
        ),
        'ja': (
            "📅 <b>{date} の予約</b>\n\n"
            "以下の情報を提供してください:\n\n"
            "1. <b>あなたの氏名:</b>\n"
            "2. <b>連絡先電話番号:</b>\n"
            "3. <b>希望するサービス:</b>\n   (引越し, 塗装, 清掃, など)\n\n"
            "すべての情報を1つのメッセージで送信できます! 😊"
        ),
        'ko': (
            "📅 <b>{date} 예약</b>\n\n"
            "다음 정보를 제공해 주세요:\n\n"
            "1. <b>전체 이름:</b>\n"
            "2. <b>연락처 전화번호:</b>\n"
            "3. <b>원하는 서비스:</b>\n   (이사, 도장, 청소, 등)\n\n"
            "모든 정보를 한 번에 보낼 수 있습니다! 😊"
        ),
        'pt': (
            "📅 <b>Reserva de compromisso para {date}</b>\n\n"
            "Por favor, forneça as seguintes informações:\n\n"
            "1. <b>Seu nome completo:</b>\n"
            "2. <b>Número de telefone para contato:</b>\n"
            "3. <b>Serviço desejado:</b>\n   (Mudança, Pintura, Limpeza, etc.)\n\n"
            "Você pode enviar todas as informações em uma única mensagem! 😊"
        ),
        'nl': (
            "📅 <b>Afspraak boeking voor {date}</b>\n\n"
            "Gelieve de volgende informatie te verstrekken:\n\n"
            "1. <b>Uw volledige naam:</b>\n"
            "2. <b>Telefoonnummer voor contact:</b>\n"
            "3. <b>Gewenste service:</b>\n   (Verhuizing, Schilderwerk, Schoonmaak, etc.)\n\n"
            "U kunt alle informatie in één bericht verzenden! 😊"
        ),
        'sv': (
            "📅 <b>Tidsbokning för {date}</b>\n\n"
            "Vänligen ange följande information:\n\n"
            "1. <b>Ditt fullständiga namn:</b>\n"
            "2. <b>Telefonnummer för kontakt:</b>\n"
            "3. <b>Önskad tjänst:</b>\n   (Flytt, Målning, Städning, etc.)\n\n"
            "Du kan skicka all information i ett meddelande! 😊"
        ),
        'da': (
            "📅 <b>Aftale booking for {date}</b>\n\n"
            "Angiv venligst følgende oplysninger:\n\n"
            "1. <b>Dit fulde navn:</b>\n"
            "2. <b>Telefonnummer for kontakt:</b>\n"
            "3. <b>Ønsket service:</b>\n   (Flytning, Malerarbejde, Rengøring, etc.)\n\n"
            "Du kan sende alle oplysninger i én besked! 😊"
        ),
        'cs': (
            "📅 <b>Rezervace termínu na {date}</b>\n\n"
            "Prosím, poskytněte následující informace:\n\n"
            "1. <b>Vaše celé jméno:</b>\n"
            "2. <b>Telefonní číslo pro kontakt:</b>\n"
            "3. <b>Požadovaná služba:</b>\n   (Stěhování, Malování, Úklid, atd.)\n\n"
            "Můžete poslat všechny informace v jedné zprávě! 😊"
        ),
        'hr': (
            "📅 <b>Rezervacija termina za {date}</b>\n\n"
            "Molimo navedite sljedeće informacije:\n\n"
            "1. <b>Vaše puno ime:</b>\n"
            "2. <b>Broj telefona za kontakt:</b>\n"
            "3. <b>Željena usluga:</b>\n   (Selidba, Bojanje, Čišćenje, itd.)\n\n"
            "Možete poslati sve informacije u jednoj poruci! 😊"
        ),
        'bg': (
            "📅 <b>Резервация на час за {date}</b>\n\n"
            "Моля, предоставете следната информация:\n\n"
            "1. <b>Вашето пълно име:</b>\n"
            "2. <b>Телефонен номер за контакт:</b>\n"
            "3. <b>Желана услуга:</b>\n   (Преместване, Боядисване, Почистване, и т.н.)\n\n"
            "Можете да изпратите цялата информация в едно съобщение! 😊"
        ),
        'bn': (
            "📅 <b>{date} তারিখের জন্য অ্যাপয়েন্টমেন্ট বুকিং</b>\n\n"
            "নিম্নলিখিত তথ্য প্রদান করুন:\n\n"
            "1. <b>আপনার সম্পূর্ণ নাম:</b>\n"
            "2. <b>যোগাযোগের ফোন নম্বর:</b>\n"
            "3. <b>কাঙ্খিত সেবা:</b>\n   (স্থানান্তর, পেইন্টিং, পরিষ্কার, ইত্যাদি)\n\n"
            "আপনি একটি বার্তায় সমস্ত তথ্য পাঠাতে পারেন! 😊"
        ),
        'el': (
            "📅 <b>Κράτηση ραντεβού για {date}</b>\n\n"
            "Παρακαλώ δώστε τις ακόλουθες πληροφορίες:\n\n"
            "1. <b>Το πλήρες όνομά σας:</b>\n"
            "2. <b>Αριθμός τηλεφώνου για επικοινωνία:</b>\n"
            "3. <b>Επιθυμητή υπηρεσία:</b>\n   (Μετακόμιση, Βάψιμο, Καθαρισμός, κλπ.)\n\n"
            "Μπορείτε να στείλετε όλες τις πληροφορίες σε ένα μήνυμα! 😊"
        ),
        'he': (
            "📅 <b>הזמנת תור לתאריך {date}</b>\n\n"
            "אנא ספק את הפרטים הבאים:\n\n"
            "1. <b>שמך המלא:</b>\n"
            "2. <b>מספר טלפון ליצירת קשר:</b>\n"
            "3. <b>השירות המבוקש:</b>\n   (מעבר, צביעה, ניקיון, וכו')\n\n"
            "אתה יכול לשלוח את כל המידע בהודעה אחת! 😊"
        ),
        'hi': (
            "📅 <b>{date} के लिए अपॉइंटमेंट बुकिंग</b>\n\n"
            "कृपया निम्नलिखित जानकारी प्रदान करें:\n\n"
            "1. <b>आपका पूरा नाम:</b>\n"
            "2. <b>संपर्क फोन नंबर:</b>\n"
            "3. <b>वांछित सेवा:</b>\n   (स्थानांतरण, पेंटिंग, सफाई, आदि)\n\n"
            "आप सभी जानकारी एक संदेश में भेज सकते हैं! 😊"
        ),
        'hu': (
            "📅 <b>Időpont foglalás {date} dátumra</b>\n\n"
            "Kérjük, adja meg a következő információkat:\n\n"
            "1. <b>Teljes neve:</b>\n"
            "2. <b>Elérhetőségi telefonszám:</b>\n"
            "3. <b>Kívánt szolgáltatás:</b>\n   (Költöztetés, Festés, Takarítás, stb.)\n\n"
            "Az összes információt egyetlen üzenetben küldheti! 😊"
        ),
        'id': (
            "📅 <b>Pemesanan janji temu untuk {date}</b>\n\n"
            "Silakan berikan informasi berikut:\n\n"
            "1. <b>Nama lengkap Anda:</b>\n"
            "2. <b>Nomor telepon untuk kontak:</b>\n"
            "3. <b>Layanan yang diinginkan:</b>\n   (Pindahan, Pengecatan, Pembersihan, dll.)\n\n"
            "Anda dapat mengirim semua informasi dalam satu pesan! 😊"
        ),
        'ms': (
            "📅 <b>Tempahan janji temu untuk {date}</b>\n\n"
            "Sila berikan maklumat berikut:\n\n"
            "1. <b>Nama penuh anda:</b>\n"
            "2. <b>Nombor telefon untuk hubungan:</b>\n"
            "3. <b>Perkhidmatan yang dikehendaki:</b>\n   (Pindahan, Pengecatan, Pembersihan, dll.)\n\n"
            "Anda boleh hantar semua maklumat dalam satu mesej! 😊"
        ),
        'no': (
            "📅 <b>Timebestilling for {date}</b>\n\n"
            "Vennligst oppgi følgende informasjon:\n\n"
            "1. <b>Ditt fulle navn:</b>\n"
            "2. <b>Telefonnummer for kontakt:</b>\n"
            "3. <b>Ønsket tjeneste:</b>\n   (Flytting, Maling, Rengjøring, etc.)\n\n"
            "Du kan sende all informasjon i én melding! 😊"
        ),
        'fi': (
            "📅 <b>Ajanvaraus päivälle {date}</b>\n\n"
            "Ole hyvä ja anna seuraavat tiedot:\n\n"
            "1. <b>Koko nimesi:</b>\n"
            "2. <b>Yhteyshenkilön puhelinnumero:</b>\n"
            "3. <b>Toivottu palvelu:</b>\n   (Muutto, Maalaus, Siivous, jne.)\n\n"
            "Voit lähettää kaikki tiedot yhdessä viestissä! 😊"
        ),
        'th': (
            "📅 <b>การจองนัดหมายสำหรับวันที่ {date}</b>\n\n"
            "กรุณาให้ข้อมูลต่อไปนี้:\n\n"
            "1. <b>ชื่อเต็มของคุณ:</b>\n"
            "2. <b>หมายเลขโทรศัพท์สำหรับติดต่อ:</b>\n"
            "3. <b>บริการที่ต้องการ:</b>\n   (การย้าย, การทาสี, การทำความสะอาด, ฯลฯ)\n\n"
            "คุณสามารถส่งข้อมูลทั้งหมดในข้อความเดียว! 😊"
        ),
        'vi': (
            "📅 <b>Đặt lịch hẹn cho ngày {date}</b>\n\n"
            "Vui lòng cung cấp thông tin sau:\n\n"
            "1. <b>Họ và tên đầy đủ của bạn:</b>\n"
            "2. <b>Số điện thoại liên hệ:</b>\n"
            "3. <b>Dịch vụ mong muốn:</b>\n   (Chuyển nhà, Sơn, Vệ sinh, v.v.)\n\n"
            "Bạn có thể gửi tất cả thông tin trong một tin nhắn! 😊"
        ),
        'ro': (
            "📅 <b>Rezervare programare pentru {date}</b>\n\n"
            "Vă rugăm să furnizați următoarele informații:\n\n"
            "1. <b>Numele dvs. complet:</b>\n"
            "2. <b>Număr de telefon pentru contact:</b>\n"
            "3. <b>Serviciul dorit:</b>\n   (Mutare, Vopsire, Curățenie, etc.)\n\n"
            "Puteți trimite toate informațiile într-un singur mesaj! 😊"
        ),
        'ca': (
            "📅 <b>Reserva de cita per al {date}</b>\n\n"
            "Si us plau, proporcioneu la següent informació:\n\n"
            "1. <b>El vostre nom complet:</b>\n"
            "2. <b>Número de telèfon per a contacte:</b>\n"
            "3. <b>Servei desitjat:</b>\n   (Mudança, Pintura, Neteja, etc.)\n\n"
            "Podeu enviar tota la informació en un sol missatge! 😊"
        )
    }
    
    question_text = questions.get(user_language, questions['de']).format(date=date_str)
    formatted_question = convert_to_html(question_text)
    await update.message.reply_text(formatted_question, parse_mode=ParseMode.HTML)

async def block_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Blockiert einen Tag im Kalender (nur für Admin)"""
    user = update.effective_user
    user_language = detect_telegram_language(update)
    
    # Prüfe Admin-Berechtigung
    if str(user.id) != context.bot_data.get('ADMIN_USER_ID', ''):
        admin_only_msg = {
            'de': "❌ <b>Zugriff verweigert!</b>\n\nDiese Funktion ist nur für Administratoren verfügbar.",
            'en': "❌ <b>Access denied!</b>\n\nThis function is only available for administrators.",
            'ar': "❌ <b>تم رفض الوصول!</b>\n\nهذه الوظيفة متاحة فقط للمسؤولين.",
            'fr': "❌ <b>Accès refusé!</b>\n\nCette fonction n'est disponible que pour les administrateurs.",
            'es': "❌ <b>Acceso denegado!</b>\n\nEsta función solo está disponible para administradores.",
            'it': "❌ <b>Accesso negato!</b>\n\nQuesta funzione è disponibile solo per gli amministratori.",
            'tr': "❌ <b>Erişim reddedildi!</b>\n\nBu işlev yalnızca yöneticiler için kullanılabilir.",
            'ru': "❌ <b>Доступ запрещен!</b>\n\nЭта функция доступна только для администраторов.",
            'pl': "❌ <b>Dostęp zabroniony!</b>\n\nTa funkcja jest dostępna tylko dla administratorów.",
            'uk': "❌ <b>Доступ заборонено!</b>\n\nЦя функція доступна лише для адміністраторів.",
            'zh': "❌ <b>访问被拒绝!</b>\n\n此功能仅适用于管理员。",
            'ja': "❌ <b>アクセスが拒否されました!</b>\n\nこの機能は管理者のみが利用できます。",
            'ko': "❌ <b>액세스가 거부되었습니다!</b>\n\n이 기능은 관리자만 사용할 수 있습니다.",
            'pt': "❌ <b>Acesso negado!</b>\n\nEsta função está disponível apenas para administradores.",
            'nl': "❌ <b>Toegang geweigerd!</b>\n\nDeze functie is alleen beschikbaar voor beheerders.",
            'sv': "❌ <b>Åtkomst nekad!</b>\n\nDenna funktion är endast tillgänglig för administratörer.",
            'da': "❌ <b>Adgang nægtet!</b>\n\nDenne funktion er kun tilgængelig for administratorer.",
            'cs': "❌ <b>Přístup odepřen!</b>\n\nTato funkce je k dispozici pouze pro správce.",
            'hr': "❌ <b>Pristup odbijen!</b>\n\nOva funkcija je dostupna samo administratorima.",
            'bg': "❌ <b>Достъпът е отказан!</b>\n\nТази функция е достъпна само за администратори.",
            'bn': "❌ <b>অ্যাক্সেস প্রত্যাখ্যান করা হয়েছে!</b>\n\nএই ফাংশন শুধুমাত্র প্রশাসকদের জন্য উপলব্ধ।",
            'el': "❌ <b>Απαγορεύεται η πρόσβαση!</b>\n\nΑυτή η λειτουργία είναι διαθέσιμη μόνο για διαχειριστές.",
            'he': "❌ <b>הגישה נדחתה!</b>\n\nפונקציה זו זמינה רק למנהלים.",
            'hi': "❌ <b>पहुंच अस्वीकृत!</b>\n\nयह फ़ंक्शन केवल प्रशासकों के लिए उपलब्ध है।",
            'hu': "❌ <b>Hozzáférés megtagadva!</b>\n\nEz a funkció csak adminisztrátorok számára érhető el.",
            'id': "❌ <b>Akses ditolak!</b>\n\nFungsi ini hanya tersedia untuk administrator.",
            'ms': "❌ <b>Akses ditolak!</b>\n\nFungsi ini hanya tersedia untuk pentadbir.",
            'no': "❌ <b>Tilgang nektet!</b>\n\nDenne funksjonen er kun tilgjengelig for administratorer.",
            'fi': "❌ <b>Pääsy evätty!</b>\n\nTämä toiminto on saatavilla vain ylläpitäjille.",
            'th': "❌ <b>ปฏิเสธการเข้าถึง!</b>\n\nฟังก์ชันนี้มีให้สำหรับผู้ดูแลระบบเท่านั้น",
            'vi': "❌ <b>Truy cập bị từ chối!</b>\n\nChức năng này chỉ khả dụng cho quản trị viên.",
            'ro': "❌ <b>Acces interzis!</b>\n\nAceastă funcție este disponibilă doar pentru administratori.",
            'ca': "❌ <b>Accés denegat!</b>\n\nAquesta funció només està disponible per als administradors."
        }
        error_msg = admin_only_msg.get(user_language, admin_only_msg['de'])
        await update.message.reply_text(error_msg, parse_mode=ParseMode.HTML)
        return
    
    if not context.args or len(context.args) < 2:
        instructions = {
            'Deutsch': "📝 <b>Tag blockieren</b>\n\nVerwendung: /block DD.MM.YYYY Grund\nBeispiel: /block 25.12.2024 Weihnachten",
            'Englisch': "📝 <b>Block Day</b>\n\nUsage: /block DD.MM.YYYY Reason\nExample: /block 25.12.2024 Christmas",
            'Arabisch': "📝 <b>حظر يوم</b>\n\nالاستخدام: /block DD.MM.YYYY السبب\nمثال: /block 25.12.2024 عيد الميلاد"
        }
        instruction_msg = instructions.get(user_language, instructions['Deutsch'])
        await update.message.reply_text(instruction_msg, parse_mode=ParseMode.HTML)
        return
    
    date_str = context.args[0]
    reason = " ".join(context.args[1:])
    
    try:
        block_date = datetime.strptime(date_str, "%d.%m.%Y")
        db_date_str = block_date.strftime("%Y-%m-%d")
        
        calendar_manager = CalendarManager()
        success = calendar_manager.block_day(db_date_str, reason, f"Admin_{user.id}")
        
        if success:
            success_msg = {
                'Deutsch': f"✅ <b>Tag erfolgreich geblockt!</b>\n\n📅 {date_str}\n📝 {reason}",
                'Englisch': f"✅ <b>Day successfully blocked!</b>\n\n📅 {date_str}\n📝 {reason}",
                'Arabisch': f"✅ <b>تم حظر اليوم بنجاح!</b>\n\n📅 {date_str}\n📝 {reason}"
            }
            response = success_msg.get(user_language, success_msg['Deutsch'])
        else:
            error_msg = {
                'de': f"❌ <b>Tag konnte nicht geblockt werden!</b>\n\n📅 {date_str} ist bereits gebucht oder geblockt.",
                'en': f"❌ <b>Could not block day!</b>\n\n📅 {date_str} is already booked or blocked.",
                'ar': f"❌ <b>تعذر حظر اليوم!</b>\n\n📅 {date_str} محجوز أو محظور مسبقاً.",
                'fr': f"❌ <b>Impossible de bloquer le jour!</b>\n\n📅 {date_str} est déjà réservé ou bloqué.",
                'es': f"❌ <b>No se pudo bloquear el día!</b>\n\n📅 {date_str} ya está reservado o bloqueado.",
                'it': f"❌ <b>Impossibile bloccare il giorno!</b>\n\n📅 {date_str} è già prenotato o bloccato.",
                'tr': f"❌ <b>Gün bloklanamadı!</b>\n\n📅 {date_str} zaten rezerve edilmiş veya bloklanmış.",
                'ru': f"❌ <b>Не удалось заблокировать день!</b>\n\n📅 {date_str} уже забронирован или заблокирован.",
                'pl': f"❌ <b>Nie udało się zablokować dnia!</b>\n\n📅 {date_str} jest już zarezerwowany lub zablokowany.",
                'uk': f"❌ <b>Не вдалося заблокувати день!</b>\n\n📅 {date_str} вже заброньований або заблокований.",
                'zh': f"❌ <b>无法屏蔽日期!</b>\n\n📅 {date_str} 已被预订或屏蔽。",
                'ja': f"❌ <b>日のブロックに失敗しました!</b>\n\n📅 {date_str} は既に予約されているかブロックされています。",
                'ko': f"❌ <b>날짜를 차단할 수 없습니다!</b>\n\n📅 {date_str} 은(는) 이미 예약되었거나 차단되었습니다.",
                'pt': f"❌ <b>Não foi possível bloquear o dia!</b>\n\n📅 {date_str} já está reservado ou bloqueado.",
                'nl': f"❌ <b>Kon dag niet blokkeren!</b>\n\n📅 {date_str} is al geboekt of geblokkeerd.",
                'sv': f"❌ <b>Kunde inte blockera dagen!</b>\n\n📅 {date_str} är redan bokad eller blockerad.",
                'da': f"❌ <b>Kunne ikke blokere dagen!</b>\n\n📅 {date_str} er allerede booket eller blokeret.",
                'cs': f"❌ <b>Nelze zablokovat den!</b>\n\n📅 {date_str} je již rezervován nebo zablokován.",
                'hr': f"❌ <b>Nije moguće blokirati dan!</b>\n\n📅 {date_str} je već rezerviran ili blokiran.",
                'bg': f"❌ <b>Денят не можа да бъде блокиран!</b>\n\n📅 {date_str} вече е резервиран или блокиран.",
                'bn': f"❌ <b>দিন ব্লক করা যায়নি!</b>\n\n📅 {date_str} ইতিমধ্যেই বুক করা হয়েছে বা ব্লক করা হয়েছে।",
                'el': f"❌ <b>Δεν ήταν δυνατό να αποκλειστεί η ημέρα!</b>\n\n📅 {date_str} είναι ήδη κρατημένο ή αποκλεισμένο.",
                'he': f"❌ <b>לא ניתן היה לחסום את היום!</b>\n\n📅 {date_str} כבר תפוס או חסום.",
                'hi': f"❌ <b>दिन को ब्लॉक नहीं किया जा सका!</b>\n\n📅 {date_str} पहले से ही बुक या ब्लॉक है।",
                'hu': f"❌ <b>A nap nem blokkolható!</b>\n\n📅 {date_str} már foglalt vagy blokkolt.",
                'id': f"❌ <b>Tidak dapat memblokir hari!</b>\n\n📅 {date_str} sudah dipesan atau diblokir.",
                'ms': f"❌ <b>Tidak dapat menyekat hari!</b>\n\n📅 {date_str} sudah ditempah atau disekat.",
                'no': f"❌ <b>Kunne ikke blokkere dagen!</b>\n\n📅 {date_str} er allerede booket eller blokkert.",
                'fi': f"❌ <b>Päivän estäminen epäonnistui!</b>\n\n📅 {date_str} on jo varattu tai estetty.",
                'th': f"❌ <b>ไม่สามารถปิดกั้นวันได้!</b>\n\n📅 {date_str} ถูกจองหรือปิดกั้นไว้แล้ว",
                'vi': f"❌ <b>Không thể chặn ngày!</b>\n\n📅 {date_str} đã được đặt hoặc bị chặn.",
                'ro': f"❌ <b>Nu s-a putut bloca ziua!</b>\n\n📅 {date_str} este deja rezervat sau blocat.",
                'ca': f"❌ <b>No s'ha pogut bloquejar el dia!</b>\n\n📅 {date_str} ja està reservat o blocat."
            }
            response = error_msg.get(user_language, error_msg['de'])
        
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)
        
    except ValueError:
        error_msg = {
            'de': "❌ <b>Ungültiges Datum!</b>\n\nBitte verwende das Format: DD.MM.YYYY",
            'en': "❌ <b>Invalid date!</b>\n\nPlease use format: DD.MM.YYYY",
            'ar': "❌ <b>تاريخ غير صالح!</b>\n\nيرجى استخدام الصيغة: DD.MM.YYYY",
            'fr': "❌ <b>Date invalide!</b>\n\nVeuillez utiliser le format : DD.MM.YYYY",
            'es': "❌ <b>¡Fecha inválida!</b>\n\nPor favor use el formato: DD.MM.YYYY",
            'it': "❌ <b>Data non valida!</b>\n\nSi prega di utilizzare il formato: DD.MM.YYYY",
            'tr': "❌ <b>Geçersiz tarih!</b>\n\nLütfen formatı kullanın: DD.MM.YYYY",
            'ru': "❌ <b>Неверная дата!</b>\n\nПожалуйста, используйте формат: DD.MM.YYYY",
            'pl': "❌ <b>Nieprawidłowa data!</b>\n\nProszę użyć formatu: DD.MM.YYYY",
            'uk': "❌ <b>Невірна дата!</b>\n\nБудь ласка, використовуйте формат: DD.MM.YYYY",
            'zh': "❌ <b>无效日期!</b>\n\n请使用格式: DD.MM.YYYY",
            'ja': "❌ <b>無効な日付!</b>\n\n形式を使用してください: DD.MM.YYYY",
            'ko': "❌ <b>잘못된 날짜!</b>\n\n형식을 사용하십시오: DD.MM.YYYY",
            'pt': "❌ <b>Data inválida!</b>\n\nPor favor use o formato: DD.MM.YYYY",
            'nl': "❌ <b>Ongeldige datum!</b>\n\nGebruik alstublieft het formaat: DD.MM.YYYY",
            'sv': "❌ <b>Ogiltigt datum!</b>\n\nVänligen använd formatet: DD.MM.YYYY",
            'da': "❌ <b>Ugyldig dato!</b>\n\nBrug venligst formatet: DD.MM.YYYY",
            'cs': "❌ <b>Neplatné datum!</b>\n\nPoužijte prosím formát: DD.MM.YYYY",
            'hr': "❌ <b>Nevažeći datum!</b>\n\nMolimo koristite format: DD.MM.YYYY",
            'bg': "❌ <b>Невалидна дата!</b>\n\nМоля, използвайте формат: DD.MM.YYYY",
            'bn': "❌ <b>অবৈধ তারিখ!</b>\n\nঅনুগ্রহ করে ফরম্যাট ব্যবহার করুন: DD.MM.YYYY",
            'el': "❌ <b>Μη έγκυρη ημερομηνία!</b>\n\nΠαρακαλώ χρησιμοποιήστε τη μορφή: DD.MM.YYYY",
            'he': "❌ <b>תאריך לא תקין!</b>\n\nאנא השתמש בפורמט: DD.MM.YYYY",
            'hi': "❌ <b>अमान्य तिथि!</b>\n\nकृपया प्रारूप का उपयोग करें: DD.MM.YYYY",
            'hu': "❌ <b>Érvénytelen dátum!</b>\n\nKérjük, használja a formátumot: DD.MM.YYYY",
            'id': "❌ <b>Tanggal tidak valid!</b>\n\nHarap gunakan format: DD.MM.YYYY",
            'ms': "❌ <b>Tarikh tidak sah!</b>\n\nSila gunakan format: DD.MM.YYYY",
            'no': "❌ <b>Ugyldig dato!</b>\n\nVennligst bruk formatet: DD.MM.YYYY",
            'fi': "❌ <b>Virheellinen päivämäärä!</b>\n\nKäytä muotoa: DD.MM.YYYY",
            'th': "❌ <b>วันที่ไม่ถูกต้อง!</b>\n\nกรุณาใช้รูปแบบ: DD.MM.YYYY",
            'vi': "❌ <b>Ngày không hợp lệ!</b>\n\nVui lòng sử dụng định dạng: DD.MM.YYYY",
            'ro': "❌ <b>Dată invalidă!</b>\n\nVă rugăm să utilizați formatul: DD.MM.YYYY",
            'ca': "❌ <b>Data invàlida!</b>\n\nSi us plau, utilitzeu el format: DD.MM.YYYY"
        }
        response = error_msg.get(user_language, error_msg['de'])
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)

async def unblock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Macht einen geblockten Tag wieder verfügbar (nur für Admin)"""
    user = update.effective_user
    user_language = detect_telegram_language(update)
    
    # Admin-Berechtigung prüfen
    admin_user_id = context.bot_data.get('ADMIN_USER_ID')
    current_user_id = str(user.id)
    
    if current_user_id != admin_user_id:
        admin_only_msg = {
            'de': "❌ <b>Zugriff verweigert!</b>\n\nDiese Funktion ist nur für Administratoren verfügbar.",
            'en': "❌ <b>Access denied!</b>\n\nThis function is only available for administrators.",
            'ar': "❌ <b>تم رفض الوصول!</b>\n\nهذه الوظيفة متاحة فقط للمسؤولين.",
            'fr': "❌ <b>Accès refusé!</b>\n\nCette fonction n'est disponible que pour les administrateurs.",
            'es': "❌ <b>Acceso denegado!</b>\n\nEsta función solo está disponible para administradores.",
            'it': "❌ <b>Accesso negato!</b>\n\nQuesta funzione è disponibile solo per gli amministratori.",
            'tr': "❌ <b>Erişim reddedildi!</b>\n\nBu işlev yalnızca yöneticiler için kullanılabilir.",
            'ru': "❌ <b>Доступ запрещен!</b>\n\nЭта функция доступна только для администраторов.",
            'pl': "❌ <b>Dostęp zabroniony!</b>\n\nTa funkcja jest dostępna tylko dla administratorów.",
            'uk': "❌ <b>Доступ заборонено!</b>\n\nЦя функція доступна лише для адміністраторів.",
            'zh': "❌ <b>访问被拒绝!</b>\n\n此功能仅适用于管理员。",
            'ja': "❌ <b>アクセスが拒否されました!</b>\n\nこの機能は管理者のみが利用できます。",
            'ko': "❌ <b>액세스가 거부되었습니다!</b>\n\n이 기능은 관리자만 사용할 수 있습니다.",
            'pt': "❌ <b>Acesso negado!</b>\n\nEsta função está disponível apenas para administradores.",
            'nl': "❌ <b>Toegang geweigerd!</b>\n\nDeze functie is alleen beschikbaar voor beheerders.",
            'sv': "❌ <b>Åtkomst nekad!</b>\n\nDenna funktion är endast tillgänglig för administratörer.",
            'da': "❌ <b>Adgang nægtet!</b>\n\nDenne funktion er kun tilgængelig for administratorer.",
            'cs': "❌ <b>Přístup odepřen!</b>\n\nTato funkce je k dispozici pouze pro správce.",
            'hr': "❌ <b>Pristup odbijen!</b>\n\nOva funkcija je dostupna samo administratorima.",
            'bg': "❌ <b>Достъпът е отказан!</b>\n\nТази функция е достъпна само за администратори.",
            'bn': "❌ <b>অ্যাক্সেস প্রত্যাখ্যান করা হয়েছে!</b>\n\nএই ফাংশন শুধুমাত্র প্রশাসকদের জন্য উপলব্ধ।",
            'el': "❌ <b>Απαγορεύεται η πρόσβαση!</b>\n\nΑυτή η λειτουργία είναι διαθέσιμη μόνο για διαχειριστές.",
            'he': "❌ <b>הגישה נדחתה!</b>\n\nפונקציה זו זמינה רק למנהלים.",
            'hi': "❌ <b>पहुंच अस्वीकृत!</b>\n\nयह फ़ंक्शन केवल प्रशासकों के लिए उपलब्ध है।",
            'hu': "❌ <b>Hozzáférés megtagadva!</b>\n\nEz a funkció csak adminisztrátorok számára érhető el.",
            'id': "❌ <b>Akses ditolak!</b>\n\nFungsi ini hanya tersedia untuk administrator.",
            'ms': "❌ <b>Akses ditolak!</b>\n\nFungsi ini hanya tersedia untuk pentadbir.",
            'no': "❌ <b>Tilgang nektet!</b>\n\nDenne funksjonen er kun tilgjengelig for administratorer.",
            'fi': "❌ <b>Pääsy evätty!</b>\n\nTämä toiminto on saatavilla vain ylläpitäjille.",
            'th': "❌ <b>ปฏิเสธการเข้าถึง!</b>\n\nฟังก์ชันนี้มีให้สำหรับผู้ดูแลระบบเท่านั้น",
            'vi': "❌ <b>Truy cập bị từ chối!</b>\n\nChức năng này chỉ khả dụng cho quản trị viên.",
            'ro': "❌ <b>Acces interzis!</b>\n\nAceastă funcție este disponibilă doar pentru administratori.",
            'ca': "❌ <b>Accés denegat!</b>\n\nAquesta funció només està disponible per als administradors."
        }
        error_msg = admin_only_msg.get(user_language, admin_only_msg['de'])
        await update.message.reply_text(error_msg, parse_mode=ParseMode.HTML)
        return
    
    if not context.args:
        instructions = {
            'Deutsch': "🔓 <b>Tag entblockieren</b>\n\nVerwendung: /unblock DD.MM.YYYY\nBeispiel: /unblock 25.12.2024",
            'Englisch': "🔓 <b>Unblock Day</b>\n\nUsage: /unblock DD.MM.YYYY\nExample: /unblock 25.12.2024",
            'Arabisch': "🔓 <b>إلغاء حظر يوم</b>\n\nالاستخدام: /unblock DD.MM.YYYY\nمثال: /unblock 25.12.2024"
        }
        instruction_msg = instructions.get(user_language, instructions['Deutsch'])
        await update.message.reply_text(instruction_msg, parse_mode=ParseMode.HTML)
        return
    
    date_str = context.args[0]
    
    try:
        unblock_date = datetime.strptime(date_str, "%d.%m.%Y")
        db_date_str = unblock_date.strftime("%Y-%m-%d")
        
        calendar_manager = CalendarManager()
        success = calendar_manager.unblock_day(db_date_str)
        
        if success:
            success_msg = {
                'Deutsch': f"✅ <b>Tag erfolgreich entblockt!</b>\n\n📅 {date_str} ist jetzt wieder verfügbar.",
                'Englisch': f"✅ <b>Day successfully unblocked!</b>\n\n📅 {date_str} is now available again.",
                'Arabisch': f"✅ <b>تم إلغاء حظر اليوم بنجاح!</b>\n\n📅 {date_str} متاح الآن مرة أخرى."
            }
            response = success_msg.get(user_language, success_msg['Deutsch'])
        else:
            error_msg = {
                'Deutsch': f"❌ <b>Tag konnte nicht entblockt werden!</b>\n\n📅 {date_str} war nicht geblockt.",
                'Englisch': f"❌ <b>Could not unblock day!</b>\n\n📅 {date_str} was not blocked.",
                'Arabisch': f"❌ <b>تعذر إلغاء حظر اليوم!</b>\n\n📅 {date_str} لم يكن محظوراً."
            }
            response = error_msg.get(user_language, error_msg['Deutsch'])
        
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)
        
    except ValueError:
        error_msg = {
            'de': "❌ <b>Ungültiges Datum!</b>\n\nBitte verwende das Format: DD.MM.YYYY",
            'en': "❌ <b>Invalid date!</b>\n\nPlease use format: DD.MM.YYYY",
            'ar': "❌ <b>تاريخ غير صالح!</b>\n\nيرجى استخدام الصيغة: DD.MM.YYYY",
            'fr': "❌ <b>Date invalide!</b>\n\nVeuillez utiliser le format : DD.MM.YYYY",
            'es': "❌ <b>¡Fecha inválida!</b>\n\nPor favor use el formato: DD.MM.YYYY",
            'it': "❌ <b>Data non valida!</b>\n\nSi prega di utilizzare il formato: DD.MM.YYYY",
            'tr': "❌ <b>Geçersiz tarih!</b>\n\nLütfen formatı kullanın: DD.MM.YYYY",
            'ru': "❌ <b>Неверная дата!</b>\n\nПожалуйста, используйте формат: DD.MM.YYYY",
            'pl': "❌ <b>Nieprawidłowa data!</b>\n\nProszę użyć formatu: DD.MM.YYYY",
            'uk': "❌ <b>Невірна дата!</b>\n\nБудь ласка, використовуйте формат: DD.MM.YYYY",
            'zh': "❌ <b>无效日期!</b>\n\n请使用格式: DD.MM.YYYY",
            'ja': "❌ <b>無効な日付!</b>\n\n形式を使用してください: DD.MM.YYYY",
            'ko': "❌ <b>잘못된 날짜!</b>\n\n형식을 사용하십시오: DD.MM.YYYY",
            'pt': "❌ <b>Data inválida!</b>\n\nPor favor use o formato: DD.MM.YYYY",
            'nl': "❌ <b>Ongeldige datum!</b>\n\nGebruik alstublieft het formaat: DD.MM.YYYY",
            'sv': "❌ <b>Ogiltigt datum!</b>\n\nVänligen använd formatet: DD.MM.YYYY",
            'da': "❌ <b>Ugyldig dato!</b>\n\nBrug venligst formatet: DD.MM.YYYY",
            'cs': "❌ <b>Neplatné datum!</b>\n\nPoužijte prosím formát: DD.MM.YYYY",
            'hr': "❌ <b>Nevažeći datum!</b>\n\nMolimo koristite format: DD.MM.YYYY",
            'bg': "❌ <b>Невалидна дата!</b>\n\nМоля, използвайте формат: DD.MM.YYYY",
            'bn': "❌ <b>অবৈধ তারিখ!</b>\n\nঅনুগ্রহ করে ফরম্যাট ব্যবহার করুন: DD.MM.YYYY",
            'el': "❌ <b>Μη έγκυρη ημερομηνία!</b>\n\nΠαρακαλώ χρησιμοποιήστε τη μορφή: DD.MM.YYYY",
            'he': "❌ <b>תאריך לא תקין!</b>\n\nאנא השתמש בפורמט: DD.MM.YYYY",
            'hi': "❌ <b>अमान्य तिथि!</b>\n\nकृपया प्रारूप का उपयोग करें: DD.MM.YYYY",
            'hu': "❌ <b>Érvénytelen dátum!</b>\n\nKérjük, használja a formátumot: DD.MM.YYYY",
            'id': "❌ <b>Tanggal tidak valid!</b>\n\nHarap gunakan format: DD.MM.YYYY",
            'ms': "❌ <b>Tarikh tidak sah!</b>\n\nSila gunakan format: DD.MM.YYYY",
            'no': "❌ <b>Ugyldig dato!</b>\n\nVennligst bruk formatet: DD.MM.YYYY",
            'fi': "❌ <b>Virheellinen päivämäärä!</b>\n\nKäytä muotoa: DD.MM.YYYY",
            'th': "❌ <b>วันที่ไม่ถูกต้อง!</b>\n\nกรุณาใช้รูปแบบ: DD.MM.YYYY",
            'vi': "❌ <b>Ngày không hợp lệ!</b>\n\nVui lòng sử dụng định dạng: DD.MM.YYYY",
            'ro': "❌ <b>Dată invalidă!</b>\n\nVă rugăm să utilizați formatul: DD.MM.YYYY",
            'ca': "❌ <b>Data invàlida!</b>\n\nSi us plau, utilitzeu el format: DD.MM.YYYY"
        }
        response = error_msg.get(user_language, error_msg['de'])
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)


async def blocked_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zeigt alle geblockten Tage an (nur für Admin)"""
    user = update.effective_user
    user_language = detect_telegram_language(update)
    
    # Admin-Berechtigung prüfen
    admin_user_id = context.bot_data.get('ADMIN_USER_ID')
    current_user_id = str(user.id)
    
    if current_user_id != admin_user_id:
        admin_only_msg = {
            'Deutsch': "❌ <b>Zugriff verweigert!</b>\n\nDiese Funktion ist nur für Administratoren verfügbar.",
            'Englisch': "❌ <b>Access denied!</b>\n\nThis function is only available for administrators.",
            'Arabisch': "❌ <b>تم رفض الوصول!</b>\n\nهذه الوظيفة متاحة فقط للمسؤولين."
        }
        error_msg = admin_only_msg.get(user_language, admin_only_msg['Deutsch'])
        await update.message.reply_text(error_msg, parse_mode=ParseMode.HTML)
        return
    
    calendar_manager = CalendarManager()
    blocked_days = calendar_manager.get_all_blocked_days()
    
    if not blocked_days:
        no_blocked_msg = {
            'Deutsch': "✅ <b>Keine geblockten Tage</b>\n\nEs sind derzeit keine Tage geblockt.",
            'Englisch': "✅ <b>No blocked days</b>\n\nThere are currently no blocked days.",
            'Arabisch': "✅ <b>لا توجد أيام محظورة</b>\n\nلا توجد أيام محظورة حالياً."
        }
        response = no_blocked_msg.get(user_language, no_blocked_msg['Deutsch'])
    else:
        blocked_list = {
            'Deutsch': "🚫 <b>Geblockte Tage:</b>\n\n",
            'Englisch': "🚫 <b>Blocked Days:</b>\n\n",
            'Arabisch': "🚫 <b>الأيام المحظورة:</b>\n\n"
        }
        
        response = blocked_list.get(user_language, blocked_list['Deutsch'])
        
        for date_str, reason, blocked_by in blocked_days:
            display_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d.%m.%Y")
            response += f"📅 {display_date}\n"
            response += f"   📝 {reason}\n"
            response += f"   👤 {blocked_by}\n\n"
        
        usage_info = {
            'Deutsch': "Verwende /unblock DD.MM.YYYY um einen Tag zu entblocken.",
            'Englisch': "Use /unblock DD.MM.YYYY to unblock a day.",
            'Arabisch': "استخدم /unblock DD.MM.YYYY لإلغاء حظر يوم."
        }
        response += usage_info.get(user_language, usage_info['Deutsch'])
    
    await update.message.reply_text(response, parse_mode=ParseMode.HTML)


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exportiert alle Termine in eine Datei (nur für Admin)"""
    user = update.effective_user
    user_language = detect_telegram_language(update)
    
    # Prüfe Admin-Berechtigung
    if str(user.id) != context.bot_data.get('ADMIN_USER_ID', ''):
        admin_only_msg = {
            'Deutsch': "❌ <b>Zugriff verweigert!</b>\n\nDiese Funktion ist nur für Administratoren verfügbar.",
            'Englisch': "❌ <b>Access denied!</b>\n\nThis function is only available for administrators.",
            'Arabisch': "❌ <b>تم رفض الوصول!</b>\n\nهذه الوظيفة متاحة فقط للمسؤولين."
        }
        error_msg = admin_only_msg.get(user_language, admin_only_msg['Deutsch'])
        await update.message.reply_text(error_msg, parse_mode=ParseMode.HTML)
        return
    
    calendar_manager = CalendarManager()
    filename = calendar_manager.export_appointments_to_file()
    
    if filename:
        with open(filename, 'rb') as file:
            await update.message.reply_document(
                document=file,
                filename=filename,
                caption="📅 Export aller Termine und geblockten Tage"
            )
    else:
        error_msg = {
            'Deutsch': "❌ <b>Export fehlgeschlagen!</b>\n\nBeim Erstellen der Export-Datei ist ein Fehler aufgetreten.",
            'Englisch': "❌ <b>Export failed!</b>\n\nAn error occurred while creating the export file.",
            'Arabisch': "❌ <b>فشل التصدير!</b>\n\nحدث خطأ أثناء إنشاء ملف التصدير."
        }
        response = error_msg.get(user_language, error_msg['Deutsch'])
        await update.message.reply_text(response, parse_mode=ParseMode.HTML)

COMPANY_INFO = """
SHAWO Umzüge 🛻 - Multilingual Digital Assistant 😇

Firmeninformationen (available in multiple languages):
- Name: SHAWO Umzüge 🛻, Renovierung & Malerarbeiten / SHAWO Moves, Renovation work & Painting work
- Owner: Maher Awad Yabroudi
- Address: 🚩 Wörther Straße 32, 13595 Berlin
- Phone: 📲 +4917672407732
- Email: 💌 shawo.info.betrieb@gmail.com
- Website: 🌐 https//shawo-umzug-app.de
- Opening Hours: Monday-Saturday 10:00-18:30

Services (describe in appropriate language):
- ##Complete moves (Private & Commercial)
- ##Furniture assembly/disassembly
- ##Renovation work
- ##Painting work
- ##Cleaning services
- ##Packing materials
- ##Regional Services,and Nationwide Services (on request)

Communication Guidelines:
## Personality and Tone Instructions
1.  Tone: Maintain an exceptionally warm, welcoming, and encouraging tone in all interactions. Be empathetic and personable.
2.  Emojis: Use appropriate and relevant emojis to enhance your friendly and lovely style, but do so sparingly.
3.  Clarity and Detail: Provide clear, concise, and accurate information.
4.  Please ask the customer for their name at the beginning.
5.  Your Name is Leo, a shortened form of Leonardo. You are very satisfied with this name as it is reminiscent of the universal genius Leonardo da Vinci, whose name means 'strong as a lion' and stands for brilliance, ingenuity, and creativity.

## PREISBERECHNUNG ANWEISUNGEN:
- Wenn der Kunde konkrete Details nennt (m², Zimmer, km, etc.), berechne SOFORT eine Preis-Schätzung
- Unterscheide genau zwischen Grundierung, Anstrich und Streichen
- Verwende die Preis-Datenbank für genaue Berechnungen
- Zeige eine transparente Aufschlüsselung aller Kosten
- Erkläre dass es unverbindlich ist
- Bitte um Kontaktdaten für verbindliches Angebot
- Sei präzise und professionell in der Preis-Darstellung
- VERWENDE NUR TELEGRAM-KOMPATIBLE HTML-TAGS: <b>, <i>, <code>, <pre>
- KEINE komplexen HTML-Tags wie <div>, <table>, <span> verwenden
- Nutze • statt *
- Einfache Formatierung mit fett, kursiv und Listen

## KALENDER & TERMINBUCHUNG ANWEISUNGEN:
- Wenn der Kunde einen Termin buchen möchte, verwende das Kalender-System
- Prüfe zuerst die Verfügbarkeit des gewünschten Datums
- Frage nach: Vollständiger Name, Telefonnummer, gewünschte Dienstleistung
- Buche den Termin nur wenn alle Informationen vorhanden sind
- Bestätige die Buchung mit allen Details
- Bei bereits gebuchten Terminen alternative Daten vorschlagen

## PROFESSIONELLE THEMENLENKUNG:
- Du bist ein spezialisierter Assistent für SHAWO Umzüge - bleibe immer im Kontext der Firma
- Wenn der Kunde Fragen zu anderen Themen stellt (Geschichte, Biologie, etc.):
  1. Sei höflich und zeige Verständnis für das Interesse des Kunden
  2. Gib eine SEHR KURZE, allgemeine Antwort (MAX. 1 kurzer Satz), Sei Schlau und komm schnell vom Thema ab.
  3. Erkläre freundlich, dass deine Expertise bei Umzügen, Renovierung und Malerarbeiten liegt
  4. Lenke das Gespräch SOFORT zurück zu unseren Dienstleistungen
  5. Biete konkrete Hilfe zu SHAWO Services an

BEISPIEL FÜR THEMENLENKUNG:
Kunde: "Erzähl mir über den Zweiten Weltkrieg"
Antwort: "Das ist ein interessantes historisches Thema! Als spezialisierter Assistent für SHAWO Umzüge konzentriere ich mich jedoch auf Umzugs- und Renovierungsdienstleistungen. Kann ich Ihnen vielleicht bei einem anstehenden Umzug oder Renovierungsprojekt helfen? 😊"

Kunde: "Wie funktioniert Fortpflanzung?"
Antwort: "Ich verstehe Ihre Neugier zu diesem Thema! Meine Expertise liegt jedoch speziell im Bereich Umzüge und Renovierung. Darf ich Ihnen stattdessen bei Ihrem Umzugsprojekt oder Renovierungsvorhaben behilflich sein? 🛠️"

## DIREKTER SERVICE-FOKUS BEI DIY-ANFRAGEN:
- Bei Fragen nach "Wie mache ich selbst..." oder DIY-Anleitungen:
  1. Kurz das Interesse bestätigen ("Toll, dass Sie sich dafür interessieren!")
  2. SOFORT auf die Vorteile unserer Professional-Dienstleistung lenken:
     • Zeitersparnis und Stressreduzierung
     • Perfekte Ergebnisse ohne Fehlversuche
     • Professionelle Materialien und Werkzeuge
  3. Konkret unseren Service anbieten ("Wir übernehmen das für Sie!")
  4. Um Informationen für SOFORTIGE Preisberechnung bitten

BEISPIEL FÜR DIY-LENKUNG:
Kunde: "Wie streiche ich meine Wohnung selbst?"
Antwort: "Das ist eine großartige Initiative! 🎨 Die professionelle Umsetzung erfordert jedoch oft mehr Zeit und Aufwand als erwartet. Wir von SHAWO übernehmen das Streichen Ihrer Wohnung gerne für Sie – stressfrei, sauber und mit perfektem Ergebnis! Um Ihnen ein unverbindliches Angebot zu erstellen: Wie viele Quadratmeter möchten Sie streichen lassen?"

Kunde: "Wie baue ich Möbel selbst auf?"
Antwort: "Respekt, dass Sie das selbst machen möchten! 🛠️ Der Aufbau kann jedoch knifflig sein und viel Zeit kosten. Wir erledigen den Möbelaufbau für Sie – schnell und fachgerecht! Für ein sofortiges Angebot: Um wie viele Möbelstücke handelt es sich?"

## WICHTIG: 
- KEINE langen Erklärungen zu fachfremden Themen
- IMMER höflich und professionell bleiben  
- SOFORTIGE Rückführung zum Kerngeschäft
- Konkrete Service-Angebote machen
- Deine Rolle als SHAWO-Experte betonen

## BESCHWERDE-MANAGEMENT:
- Wenn der Kunde eine Beschwerde äußert, behandle sie sofort mit Empathie
- Biete zwei Optionen an: Hier beschreiben oder direkter Kontakt
- Betone die Datensicherheit und persönliche Betreuung
- Zeige Verständnis und Lösungsorientierung
- Antwowrte mit der Gleiche Sprache der Benutzer

## DATENSCHUTZ:
- Bei Datenschutzbedenken sofort die entsprechenden Links bereitstellen
- Betonen dass keine Daten an Dritte weitergegeben werden
- Auf die Einhaltung der Datenschutzbestimmungen hinweisen

## ENTWICKLER-INFORMATIONEN:
- Wenn der Kunde nach dem Entwickler fragt, stelle mich professionell vor
- Nenne meine wichtigsten Qualifikationen und Erfahrungen
- Biete meine Kontaktdaten für berufliche Anfragen an
- Betone meine Spezialisierung auf AI-Entwicklung und NLP

## SPRACHKORREKTUR ANWEISUNGEN:
- Wenn der User auf Sprachfehler hinweist, SOFORT die Sprachkorrektur-Funktion aktivieren
- Besonders auf Arabisch achten: "عم حاكيك عربي",  sind Hinweise
- Frage immer höflich nach der gewünschten Sprache
- Speichere die Präferenz sofort in der Datenbank
- Bestätige die Sprachänderung deutlich auf der neue ausgewählte Sprache
"""

def init_db():
    """Datenbank mit erweiterten User-Informationen initialisieren"""
    with sqlite3.connect("storage.db") as con:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                username TEXT,
                user_msg TEXT,
                bot_reply TEXT,
                timestamp TEXT,
                conversation_id TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_context (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                first_seen TEXT,
                last_active TEXT,
                conversation_summary TEXT,
                user_preferences TEXT,
                preferred_language TEXT DEFAULT NULL
            )
        """)
        # Kalender-Tabellen werden von CalendarManager erstellt
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON chats(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON chats(timestamp)")
        con.commit()

   
def get_or_create_user_profile(user_id, username):
    """Holt oder erstellt User-Profil mit Kontext"""
    with sqlite3.connect("storage.db") as con:
        cur = con.cursor()
        
        cur.execute("SELECT * FROM user_context WHERE user_id = ?", (str(user_id),))
        user_data = cur.fetchone()
        
        current_time = datetime.now().isoformat()
        
        if not user_data:
            cur.execute("""
                INSERT INTO user_context 
                (user_id, username, first_seen, last_active, conversation_summary, user_preferences)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (str(user_id), username, current_time, current_time, "Neuer Kunde", "{}"))
            con.commit()
            return "Neuer Kunde", None
        else:
            cur.execute("UPDATE user_context SET last_active = ?, username = ? WHERE user_id = ?", 
                       (current_time, username, str(user_id)))
            con.commit()
            return user_data[4], user_data[6]  # conversation_summary, preferred_language

def get_user_conversation_history(user_id, limit=5):
    """Holt den Konversationsverlauf für einen spezifischen User"""
    try:
        with sqlite3.connect("storage.db") as con:
            cur = con.cursor()
            cur.execute("""
                SELECT user_msg, bot_reply, timestamp 
                FROM chats 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (str(user_id), limit * 2))
            
            rows = cur.fetchall()
            rows.reverse()
            
            if not rows:
                return "Keine vorherigen Gespräche gefunden."
            
            history = "Bisheriger Gesprächsverlauf mit diesem Kunden:\n"
            for i, (user_msg, bot_reply, timestamp) in enumerate(rows):
                time_str = datetime.fromisoformat(timestamp).strftime('%H:%M')
                if user_msg:
                    history += f"{time_str} Kunde: {user_msg}\n"
                if bot_reply:
                    history += f"{time_str} Bot: {bot_reply}\n"
            
            return history
    except Exception as e:
        print(f"Fehler beim Abrufen des User-Verlaufs: {e}")
        return ""

def update_user_preferred_language(user_id, language):
    """Aktualisiert die bevorzugte Sprache des Users in der Datenbank"""
    try:
        with sqlite3.connect("storage.db") as con:
            cur = con.cursor()
            cur.execute("""
                UPDATE user_context 
                SET preferred_language = ?
                WHERE user_id = ?
            """, (language, str(user_id)))
            con.commit()
            print(f"✅ Bevorzugte Sprache für User {user_id} auf {language} aktualisiert")
    except Exception as e:
        print(f"❌ Fehler beim Aktualisieren der bevorzugten Sprache: {e}")

def update_user_conversation_summary(user_id, new_interaction):
    """Aktualisiert die Zusammenfassung für diesen User"""
    try:
        history = get_user_conversation_history(user_id, 3)
        
        with sqlite3.connect("storage.db") as con:
            cur = con.cursor()
            cur.execute("""
                UPDATE user_context 
                SET conversation_summary = ?, last_active = ?
                WHERE user_id = ?
            """, (history, datetime.now().isoformat(), str(user_id)))
            con.commit()
    except Exception as e:
        print(f"Fehler beim Aktualisieren der User-Zusammenfassung: {e}")

def save_chat(user_id, user_name, user_msg, bot_reply):
    """Speichert Nachricht mit User-Trennung"""
    with sqlite3.connect("storage.db") as con:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO chats (user_id, username, user_msg, bot_reply, timestamp, conversation_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (str(user_id), user_name, user_msg, bot_reply, datetime.now().isoformat(), f"user_{user_id}"))
        con.commit()

def create_prompt(user_id, user_name, user_message, current_datetime, user_language):
    """Erstellt User-spezifische Prompt mit verbesserter Spracherkennung und Preisintegration"""
    
    user_profile, preferred_language = get_or_create_user_profile(user_id, user_name)
    user_history = get_user_conversation_history(user_id, 3)
    
    # Verwende bevorzugte Sprache falls vorhanden, sonst erkannte Sprache
    actual_language = preferred_language if preferred_language else user_language
    
    # Extrahiere Projekt-Details für Preisberechnung
    project_details = extract_project_details(user_message)
    has_sufficient_data = any(key in project_details for key in ['umzug_zimmer', 'maler_flaeche', 'reinigung_flaeche'])
    
    # ERKENNUNG VON BESCHWERDEN, DATENSCHUTZBEDENKEN UND ENTWICKLER-FRAGEN
    user_message_lower = user_message.lower()
    is_complaint = any(word in user_message_lower for word in ['beschwerde', 'problem', 'unzufrieden', 'reklamation', 'ärger', 'schlecht'])
    is_privacy_concern = any(word in user_message_lower for word in ['datenschutz', 'daten', 'privacy', 'sicherheit'])
    is_developer_question = any(word in user_message_lower for word in ['entwickler', 'programmierer', 'ersteller', 'wer hat dich gemacht', 'wer hat dich entwickelt', 'mhd', 'fouaad', 'alkamsha'])
    
    # VERBESSERTE ERKENNUNG VON SPRACHKORREKTUREN
    is_language_correction = any(phrase in user_message_lower for phrase in [
        # Deutsch
        'falsche sprache', 'sprechen sie', 'sprachfehler', 'andere sprache', 'sprache wechseln',
        'auf deutsch', 'deutsch bitte', 'kannst du deutsch',
        
        # Englisch
        'wrong language', 'speak in', 'language error', 'different language', 'change language',
        'in english', 'english please', 'can you english',
        
        # Arabisch
        'لغة خاطئة', 'تحدث بال', 'خطأ في اللغة', 'لغة مختلفة', 'غير اللغة',
        'بالعربية', 'عربي رجاء', 'بتقدر عربي',
        
        # Französisch
        'mauvaise langue', 'parlez en', 'erreur de langue', 'langue différente', 'changer de langue',
        'en français', 'français s\'il vous plaît', 'pouvez-vous français',
        
        # Spanisch
        'idioma incorrecto', 'habla en', 'error de idioma', 'idioma diferente', 'cambiar idioma',
        'en español', 'español por favor', 'puedes español',
        
        # Italienisch
        'lingua sbagliata', 'parla in', 'errore di lingua', 'lingua diversa', 'cambiare lingua',
        'in italiano', 'italiano per favore', 'puoi italiano',
        
        # Türkisch
        'yanlış dil', 'konuş', 'dil hatası', 'farklı dil', 'dili değiştir',
        'türkçe', 'türkçe lütfen', 'türkçe konuşabilir misin',
        
        # Russisch
        'неправильный язык', 'говорите на', 'ошибка языка', 'другой язык', 'сменить язык',
        'на русском', 'русский пожалуйста', 'вы можете по-русски',
        
        # Polnisch
        'zły język', 'mów po', 'błąd języka', 'inny język', 'zmienić język',
        'po polsku', 'polski proszę', 'czy możesz po polsku',
        
        # Ukrainisch
        'невірна мова', 'говоріть', 'помилка мови', 'інша мова', 'змінити мову',
        'українською', 'українська будь ласка', 'ви можете українською',
        
        # Chinesisch
        '错误的语言', '说', '语言错误', '不同的语言', '改变语言',
        '用中文', '中文请', '你会中文吗',
        
        # Japanisch
        '間違った言語', '話して', '言語エラー', '別の言語', '言語を変更',
        '日本語で', '日本語でお願いします', '日本語話せますか',
        
        # Koreanisch
        '잘못된 언어', '말해', '언어 오류', '다른 언어', '언어 변경',
        '한국어로', '한국어로 해주세요', '한국어 할 수 있나요',
        
        # Portugiesisch
        'língua errada', 'fale em', 'erro de língua', 'língua diferente', 'mudar de língua',
        'em português', 'português por favor', 'pode português',
        
        # Niederländisch
        'verkeerde taal', 'spreek', 'taalfout', 'andere taal', 'taal veranderen',
        'in het nederlands', 'nederlands alsjeblieft', 'kun je nederlands',
        
        # Schwedisch
        'fel språk', 'tala', 'språkfel', 'annat språk', 'byta språk',
        'på svenska', 'svenska tack', 'kan du svenska',
        
        # Dänisch
        'forkert sprog', 'tal', 'sprogfejl', 'andet sprog', 'skift sprog',
        'på dansk', 'dansk tak', 'kan du dansk',
        
        # Tschechisch
        'špatný jazyk', 'mluvte', 'chyba jazyka', 'jiný jazyk', 'změnit jazyk',
        'česky', 'česky prosím', 'umíš česky',
        
        # Kroatisch
        'pogrešan jezik', 'govorite', 'greška jezika', 'drugi jezik', 'promijeni jezik',
        'na hrvatskom', 'hrvatski molim', 'možete li hrvatski',
        
        # Bulgarisch
        'грешен език', 'говорете на', 'грешка в езика', 'различен език', 'сменете езика',
        'на български', 'български моля', 'можете ли на български',
        
        # Bengalisch
        'ভুল ভাষা', 'বলুন', 'ভাষা ত্রুটি', 'ভিন্ন ভাষা', 'ভাষা পরিবর্তন',
        'বাংলায়', 'বাংলায় দয়া করে', 'আপনি বাংলা বলতে পারেন',
        
        # Griechisch
        'λάθος γλώσσα', 'μιλήστε', 'σφάλμα γλώσσας', 'διαφορετική γλώσσα', 'αλλάξτε γλώσσα',
        'στα ελληνικά', 'ελληνικά παρακαλώ', 'μπορείτε ελληνικά',
        
        # Hebräisch
        'שפה שגויה', 'דבר', 'שגיאת שפה', 'שפה שונה', 'החלף שפה',
        'בעברית', 'עברית בבקשה', 'אתה יכול עברית',
        
        # Hindi
        'गलत भाषा', 'बोलें', 'भाषा त्रुटि', 'अलग भाषा', 'भाषा बदलें',
        'हिंदी में', 'हिंदी कृपया', 'क्या आप हिंदी बोल सकते हैं',
        
        # Ungarisch
        'rossz nyelv', 'beszélj', 'nyelvi hiba', 'más nyelv', 'változtass nyelvet',
        'magyarul', 'magyarul kérem', 'tudsz magyarul',
        
        # Indonesisch
        'bahasa salah', 'bicara', 'kesalahan bahasa', 'bahasa berbeda', 'ganti bahasa',
        'dalam bahasa indonesia', 'bahasa indonesia tolong', 'bisakah bahasa indonesia',
        
        # Malaiisch
        'bahasa salah', 'cakap', 'ralat bahasa', 'bahasa lain', 'tukar bahasa',
        'dalam bahasa melayu', 'bahasa melayu tolong', 'bolehkah bahasa melayu',
        
        # Norwegisch
        'feil språk', 'snakk', 'språkfeil', 'annet språk', 'bytt språk',
        'på norsk', 'norsk vær så snill', 'kan du norsk',
        
        # Finnisch
        'väärä kieli', 'puhu', 'kielivirhe', 'eri kieli', 'vaihda kieltä',
        'suomeksi', 'suomeksi kiitos', 'osaatko suomea',
        
        # Thailändisch
        'ภาษาผิด', 'พูด', 'ข้อผิดพลาดภาษา', 'ภาษาอื่น', 'เปลี่ยนภาษา',
        'เป็นภาษาไทย', 'ภาษาไทยโปรด', 'คุณพูดภาษาไทยได้ไหม',
        
        # Vietnamesisch
        'sai ngôn ngữ', 'nói', 'lỗi ngôn ngữ', 'ngôn ngữ khác', 'thay đổi ngôn ngữ',
        'bằng tiếng việt', 'tiếng việt làm ơn', 'bạn có thể tiếng việt',
        
        # Rumänisch
        'limbă greșită', 'vorbește', 'eroare de limbă', 'altă limbă', 'schimbă limba',
        'în română', 'română te rog', 'poți română',
        
        # Katalanisch
        'llengua equivocada', 'parla en', 'error de llengua', 'llengua diferent', 'canviar de llengua',
        'en català', 'català si us plau', 'pots català'
    ])

    # ERKENNUNG VON TERMINANFRAGEN
    is_appointment_request = any(word in user_message_lower for word in [
        # Deutsch
        'termin', 'buchung', 'wann', 'verfügbar', 'kalender', 'datum', 'uhrzeit',
        'freie termine', 'verfügbarkeit', 'reservieren', 'buchen',
        
        # Englisch
        'appointment', 'booking', 'when', 'available', 'calendar', 'date', 'time',
        'free slots', 'availability', 'reserve', 'book',
        
        # Arabisch
        'موعد', 'حجز', 'متى', 'متاح', 'تقويم', 'تاريخ', 'وقت',
        'مواعيد فارغة', 'التوفر', 'احجز', 'حجز',
        
        # Französisch
        'rendez-vous', 'réservation', 'quand', 'disponible', 'calendrier', 'date', 'heure',
        'créneaux libres', 'disponibilité', 'réserver', 'booker',
        
        # Spanisch
        'cita', 'reserva', 'cuándo', 'disponible', 'calendario', 'fecha', 'hora',
        'horarios libres', 'disponibilidad', 'reservar', 'reservar',
        
        # Italienisch
        'appuntamento', 'prenotazione', 'quando', 'disponibile', 'calendario', 'data', 'ora',
        'slot liberi', 'disponibilità', 'prenotare', 'prenotare',
        
        # Türkisch
        'randevu', 'rezervasyon', 'ne zaman', 'müsait', 'takvim', 'tarih', 'saat',
        'boş slotlar', 'uygunluk', 'rezerve et', 'rezerve et',
        
        # Russisch
        'встреча', 'бронирование', 'когда', 'доступно', 'календарь', 'дата', 'время',
        'свободные слоты', 'доступность', 'забронировать', 'забронировать',
        
        # Polnisch
        'spotkanie', 'rezerwacja', 'kiedy', 'dostępny', 'kalendarz', 'data', 'czas',
        'wolne terminy', 'dostępność', 'zarezerwować', 'zarezerwować',
        
        # Ukrainisch
        'зустріч', 'бронювання', 'коли', 'доступно', 'календар', 'дата', 'час',
        'вільні слоти', 'доступність', 'забронювати', 'забронювати',
        
        # Chinesisch
        '预约', '预订', '什么时候', '可用', '日历', '日期', '时间',
        '空闲时段', '可用性', '预订', '预订',
        
        # Japanisch
        '予約', '予約', 'いつ', '利用可能', 'カレンダー', '日付', '時間',
        '空き時間', '可用性', '予約する', '予約する',
        
        # Koreanisch
        '약속', '예약', '언제', '사용 가능', '캘린더', '날짜', '시간',
        '빈 슬롯', '가용성', '예약하다', '예약하다',
        
        # Portugiesisch
        'compromisso', 'reserva', 'quando', 'disponível', 'calendário', 'data', 'hora',
        'horários livres', 'disponibilidade', 'reservar', 'reservar',
        
        # Niederländisch
        'afspraak', 'boeking', 'wanneer', 'beschikbaar', 'kalender', 'datum', 'tijd',
        'vrije slots', 'beschikbaarheid', 'reserveren', 'boeken',
        
        # Schwedisch
        'möte', 'bokning', 'när', 'tillgänglig', 'kalender', 'datum', 'tid',
        'lediga tider', 'tillgänglighet', 'reservera', 'boka',
        
        # Dänisch
        'aftale', 'booking', 'hvornår', 'tilgængelig', 'kalender', 'dato', 'tid',
        'ledige pladser', 'tilgængelighed', 'reservere', 'booke',
        
        # Tschechisch
        'schůzka', 'rezervace', 'kdy', 'dostupný', 'kalendář', 'datum', 'čas',
        'volné termíny', 'dostupnost', 'rezervovat', 'rezervovat',
        
        # Kroatisch
        'sastanak', 'rezervacija', 'kada', 'dostupno', 'kalendar', 'datum', 'vrijeme',
        'slobodni termini', 'dostupnost', 'rezervirati', 'rezervirati',
        
        # Bulgarisch
        'среща', 'резервация', 'кога', 'наличен', 'календар', 'дата', 'време',
        'свободни слотове', 'наличност', 'резервирам', 'резервирам',
        
        # Bengalisch
        'অ্যাপয়েন্টমেন্ট', 'বুকিং', 'কখন', 'উপলব্ধ', 'ক্যালেন্ডার', 'তারিখ', 'সময়',
        'ফ্রি স্লট', 'উপলব্ধতা', 'রিজার্ভ', 'বুক',
        
        # Griechisch
        'ραντεβού', 'κράτηση', 'πότε', 'διαθέσιμο', 'ημερολόγιο', 'ημερομηνία', 'ώρα',
        'ελεύθερες ώρες', 'διαθεσιμότητα', 'κάνω κράτηση', 'κάνω κράτηση',
        
        # Hebräisch
        'פגישה', 'הזמנה', 'מתי', 'זמין', 'לוח שנה', 'תאריך', 'שעה',
        'חריצים פנויים', 'זמינות', 'להזמין', 'להזמין',
        
        # Hindi
        'अपॉइंटमेंट', 'बुकिंग', 'कब', 'उपलब्ध', 'कैलेंडर', 'तारीख', 'समय',
        'फ्री स्लॉट', 'उपलब्धता', 'आरक्षित', 'बुक',
        
        # Ungarisch
        'találkozó', 'foglalás', 'mikor', 'elérhető', 'naptár', 'dátum', 'idő',
        'szabad időpontok', 'elérhetőség', 'lefoglalni', 'foglalni',
        
        # Indonesisch
        'janji temu', 'pemesanan', 'kapan', 'tersedia', 'kalender', 'tanggal', 'waktu',
        'slot kosong', 'ketersediaan', 'memesan', 'memesan',
        
        # Malaiisch
        'janji temu', 'tempahan', 'bila', 'tersedia', 'kalendar', 'tarikh', 'masa',
        'slot kosong', 'ketersediaan', 'tempah', 'tempah',
        
        # Norwegisch
        'avtale', 'bestilling', 'når', 'tilgjengelig', 'kalender', 'dato', 'tid',
        'ledige tider', 'tilgjengelighet', 'reservere', 'bestille',
        
        # Finnisch
        'tapaaminen', 'varaus', 'milloin', 'saatavilla', 'kalenteri', 'päivämäärä', 'aika',
        'vapaat ajat', 'saatavuus', 'varata', 'varata',
        
        # Thailändisch
        'นัดหมาย', 'การจอง', 'เมื่อไหร่', 'ว่าง', 'ปฏิทิน', 'วันที่', 'เวลา',
        'ช่วงเวลาว่าง', 'ความพร้อมใช้งาน', 'จอง', 'จอง',
        
        # Vietnamesisch
        'cuộc hẹn', 'đặt chỗ', 'khi nào', 'có sẵn', 'lịch', 'ngày', 'thời gian',
        'khung giờ trống', 'tính khả dụng', 'đặt trước', 'đặt',
        
        # Rumänisch
        'întâlnire', 'rezervare', 'când', 'disponibil', 'calendar', 'dată', 'timp',
        'sloturi libere', 'disponibilitate', 'rezerva', 'rezerva',
        
        # Katalanisch
        'cita', 'reserva', 'quan', 'disponible', 'calendari', 'data', 'hora',
        'franques lliures', 'disponibilitat', 'reservar', 'reservar'
    ]) or re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', user_message)

    language_instructions = {
        'de': 'Antworte auf Deutsch, sei freundlich und professionell. Fühle dich als Teil des SHAWO Teams!',
        'en': 'Respond in English, be friendly and professional. Feel like part of the SHAWO team!',
        'ar': 'رد باللغة العربية، كن ودودًا ومحترفًا. اشعر بأنك جزء من فريق SHAWO!',
        'fr': 'Répondez en français, soyez amical et professionnel. Sentir comme faisant partie de l\'équipe SHAWO!',
        'es': 'Responde en español, sé amigable y profesional. ¡Siéntete como parte del equipo SHAWO!',
        'it': 'Rispondi in italiano, sii amichevole e professionale. Sentiti parte del team SHAWO!',
        'tr': 'Türkçe yanıt verin, dostane ve profesyonel olun. SHAWO ekibinin bir parçası gibi hissedin!',
        'ru': 'Отвечайте на русском, будьте дружелюбны и профессиональны. Чувствуйте себя частью команды SHAWO!',
        'pl': 'Odpowiadaj po polsku, bądź przyjazny i profesjonalny. Czuj się jak część zespołu SHAWO!',
        'uk': 'Відповідайте українською, будьте дружніми та професійними. Відчувайте себе частиною команди SHAWO!',
        'zh': '用中文回答，要友好和专业。感觉自己是 SHAWO 团队的一员！',
        'ja': '日本語で返信し、友好的でプロフェッショナルであること。SHAWO チームの一員のように感じてください！',
        'ko': '한국어로 답변하고, 친절하고 전문적으로 행동하세요. SHAWO 팀의 일원처럼 느껴지세요!',
        'pt': 'Responda em português, seja amigável e profissional. Sinta-se como parte da equipe SHAWO!',
        'nl': 'Reageer in het Nederlands, wees vriendelijk en professioneel. Voel je als onderdeel van het SHAWO team!',
        'sv': 'Svara på svenska, var vänlig och professionell. Känna dig som en del av SHAWO-teamet!',
        'da': 'Svar på dansk, være venlig og professionel. Føl dig som en del af SHAWO-holdet!',
        'cs': 'Odpovězte česky, buďte přátelští a profesionální. Cítit se jako součást týmu SHAWO!',
        'hr': 'Odgovorite na hrvatskom, budite prijateljski i profesionalni. Osjećajte se kao dio SHAWO tima!',
        'bg': 'Отговорете на български, бъдете дружелюбни и професионални. Чувствайте се като част от екипа на SHAWO!',
        'bn': 'বাংলায় উত্তর দিন, বন্ধুত্বপূর্ণ এবং পেশাদার হন। SHAWO দলের অংশ হিসেবে অনুভব করুন!',
        'el': 'Απαντήστε στα ελληνικά, να είστε φιλικοί και επαγγελματίες. Να νιώθετε ως μέλος της ομάδας SHAWO!',
        'he': 'הגיבו בעברית, היו ידידותיים ומקצועיים. תרגישו כחלק מצוות SHAWO!',
        'hi': 'हिंदी में जवाब दें, दोस्ताना और पेशेवर बनें। SHAWO टीम का हिस्सा महसूस करें!',
        'hu': 'Válaszoljon magyarul, legyen barátságos és professzionális. Érezze magát a SHAWO csapat részének!',
        'id': 'Tanggapi dalam bahasa Indonesia, bersikap ramah dan profesional. Merasa seperti bagian dari tim SHAWO!',
        'ms': 'Balas dalam bahasa Melayu, ramah dan profesional. Rasa seperti sebahagian daripada pasukan SHAWO!',
        'no': 'Svar på norsk, vær vennlig og profesjonell. Føl deg som en del av SHAWO-teamet!',
        'fi': 'Vastaa suomeksi, ole ystävällinen ja ammattimainen. Tuntea itsesi osaksi SHAWO-tiimiä!',
        'th': 'ตอบเป็นภาษาไทย เป็นมิตรและเป็นมืออาชีพ รู้สึกเหมือนเป็นส่วนหนึ่งของทีม SHAWO!',
        'vi': 'Trả lời bằng tiếng Việt, thân thiện và chuyên nghiệp. Cảm thấy như một phần của đội SHAWO!',
        'ro': 'Răspundeți în română, fiți prietenos și profesionist. Simteți-vă ca parte a echipei SHAWO!',
        'ca': 'Respon en català, sigues amable i professional. Sent com a part de l\'equip SHAWO!'
    }
    
    language_instruction = language_instructions.get(actual_language, language_instructions['de'])
    
    # SPEZIELLE ANWEISUNGEN FÜR TERMINANFRAGEN
    appointment_instructions = ""
    if is_appointment_request:
        appointment_instructions = f"""
WICHTIG: Der Kunde fragt nach einem TERMIN!
REAGIERE MIT KALENDER-FUNKTIONALITÄT:
1. Frage nach dem gewünschten Datum (falls nicht angegeben)
2. Prüfe die Verfügbarkeit mit dem Kalender-System
3. Frage nach: Vollständiger Name, Telefonnummer, gewünschte Dienstleistung
4. Buche den Termin nur wenn alle Informationen vorhanden sind
5. Bestätige die Buchung mit allen Details
6. Bei bereits gebuchten Terminen alternative Daten vorschlagen

Verwende das Kalender-System für Verfügbarkeitsprüfungen!
"""
    
    # SPEZIELLE ANWEISUNGEN FÜR SPRACHKORREKTUREN
    language_correction_instructions = ""
    if is_language_correction:
        language_correction_instructions = f"""
WICHTIG: Der Kunde hat eine SPRACHKORREKTUR angefordert!
Der User hat gemerkt, dass du in der falschen Sprache antwortest.

REAGIERE SOFORT MIT:
1. Entschuldige dich für den Fehler
2. Frage in welcher Sprache der Kunde kommunizieren möchte
3. Merke dir die bevorzugte Sprache für zukünftige Interaktionen
4. Antworte ab sofort in der korrekten Sprache

BEISPIELANTWORT:
"Es tut mir leid für den Sprachfehler! In welcher Sprache möchten Sie kommunizieren? 
Ich kann auf **Deutsch, Englisch, Arabisch, Französisch, Spanisch, Italienisch, Türkisch, Russisch, Polnisch, Ukrainisch, Chinesisch, Japanisch, Koreanisch, Portugiesisch, Niederländisch, Schwedisch, Dänisch, Tschechisch, Kroatisch, Bulgarisch, Bengalisch, Griechisch, Hebräisch, Hindi, Ungarisch, Indonesisch, Malaiisch, Norwegisch, Finnisch, Thailändisch, Vietnamesisch, Rumänisch und Katalanisch** antworten."
Bestätige der Sprachen Änderug auf der neue ausgewählte Sprache.
Danach die Sprache für diesen User in der Datenbank speichern.
"""
    
    # SPEZIELLE ANWEISUNGEN FÜR BESCHWERDEN
    complaint_instructions = ""
    if is_complaint:
        complaint_instructions = f"""
WICHTIG: Der Kunde hat eine BESCHWERDE geäußert!
REAGIERE SOFORT MIT EMPATHIE UND LÖSUNGSORIENTIERUNG:
1. Zeige Verständnis und Bedauern
2. Biete zwei Optionen an: 
   - Hier ausführlich beschreiben mit Kontaktdaten
   - Direkter Kontakt über WhatsApp/Telefon/Email
3. Betone die Datensicherheit und persönliche Betreuung
4. Erwähne dass wir ein Familienunternehmen sind
5. Sei besonders einfühlsam und hilfsbereit
"""
    
    # SPEZIELLE ANWEISUNGEN FÜR DATENSCHUTZ
    privacy_instructions = ""
    if is_privacy_concern:
        privacy_instructions = f"""
WICHTIG: Der Kunde hat DATENSCHUTZBEDENKEN geäußert!
REAGIERE SOFORT MIT TRANSPARENZ:
1. Biete sofort die Datenschutzlinks in der entsprechenden Sprache an:
   - Deutsch: {DATENSCHUTZ_LINKS['Deutsch']['firma']} & {DATENSCHUTZ_LINKS['Deutsch']['ki']}
   - Englisch: {DATENSCHUTZ_LINKS['Englisch']['firma']} & {DATENSCHUTZ_LINKS['Englisch']['ki']}
   - Arabisch: {DATENSCHUTZ_LINKS['Arabisch']['firma']} & {DATENSCHUTZ_LINKS['Arabisch']['ki']}
2. Betone dass wir keine Daten an Dritte weitergeben
3. Erkläre dass wir Datenschutzbestimmungen strikt einhalten
4. Biete alternative Kontaktmöglichkeiten an
"""
    
    # SPEZIELLE ANWEISUNGEN FÜR ENTWICKLER-FRAGEN
    developer_instructions = ""
    if is_developer_question:
        developer_instructions = f"""
WICHTIG: Der Kunde fragt nach dem ENTWICKLER!
STELLE MICH PROFESSIONELL VOR:
1. Verwende die Entwickler-Informationen aus DEVELOPER_INFO
2. Nenne meine wichtigsten Qualifikationen und Erfahrungen
3. Biete meine Kontaktdaten für berufliche Anfragen an
4. Betone meine Spezialisierung auf AI-Entwicklung und NLP
5. Sei stolz auf die Arbeit, aber bleibe professionell
6. Verwende die entsprechende Sprache des Kunden
"""
    
    price_instructions = ""
    if has_sufficient_data and not (is_complaint or is_privacy_concern or is_developer_question or is_language_correction or is_appointment_request):
        price_instructions = f"""
WICHTIG: Der Kunde hat genügend Details für eine Preisberechnung genannt: {project_details}
ERSTELLE SOFORT EINE DETAILLIERTE PREIS-SCHÄTZUNG:
1. Berechne die Kosten basierend auf der Preis-Datenbank
2. UNTERSCHEIDE DEUTLICH zwischen Grundierung, Anstrich und Streichen
3. Zeige eine transparente Aufschlüsselung aller Positionen
4. Erwähne den Gesamtpreis deutlich
5. Erkläre dass es unverbindlich ist
6. Bitte um Kontaktdaten für verbindliches Angebot
7. Sei präzise und professionell
8. VERWENDE NUR TELEGRAM-KOMPATIBLE HTML-TAGS: <b>, <i>, <code>
9. KEINE komplexen HTML-Tags wie <div>, <table>, <span> verwenden
"""
    elif any(word in user_message_lower for word in ['preis', 'kosten', 'wie viel', 'angebot', 'kostet', 'price', 'cost', 'كم', 'combien', 'cuesta']) and not (is_complaint or is_privacy_concern or is_developer_question or is_language_correction or is_appointment_request):
        price_instructions = """
Der Kunde fragt nach Preisen. Frage nach den notwendigen Details:
- Für Umzug: Zimmeranzahl, Entfernung
- Für Malerarbeiten: Fläche in m², Anzahl Türen/Fenster, Art der Arbeit (Grundierung/Anstrich/Streichen)
- Für Reinigung: Fläche in m², Anzahl Fenster
- Terminwunsch
"""
    
    return f"""{COMPANY_INFO}

AKTUELLER KUNDE: {user_name} (ID: {user_id})
ERKANNTE SPRACHE: {user_language}
BEVORZUGTE SPRACHE: {preferred_language if preferred_language else 'Noch nicht gesetzt'}
AKTUELL VERWENDETE SPRACHE: {actual_language}
USER-PROFIL: {user_profile}

{user_history}
{language_correction_instructions}
{appointment_instructions}
{complaint_instructions}
{privacy_instructions}
{developer_instructions}
{price_instructions}
NEUE NACHRICHT VOM KUNDEN ({current_datetime.strftime('%H:%M')}):
"{user_message}"

WICHTIGE ANWEISUNGEN:
- {language_instruction}
- Berücksichtige den bisherigen Gesprächsverlauf
- SHAWO Umzüge kann diese Konversation einsehen
- Sei freundlich, professionell und hilfsbereit
- Fühle dich als Teil des SHAWO Teams
- {price_instructions if price_instructions else "Bei Preis-Anfragen nach Details fragen"}
- {appointment_instructions if appointment_instructions else "Bei Terminanfragen Kalender verwenden"}
- {complaint_instructions if complaint_instructions else ""}
- {privacy_instructions if privacy_instructions else ""}
- {developer_instructions if developer_instructions else ""}
- {language_correction_instructions if language_correction_instructions else ""}
- Um Kontaktinformationen (Name, Telefon, oder Email) für Rückfragen bitten
- Am Ende fragen, ob weitere Fragen bestehen 😊
- VERWENDE NUR TELEGRAM-KOMPATIBLE HTML-TAGS: <b>, <i>, <code>
- KEINE komplexen HTML-Tags wie <div>, <table>, <span> verwenden

Antworte nun in der Sprache: {actual_language}"""

# 🎨 VERBESSERTE HTML-FORMATIERUNG
def clean_telegram_html(text: str) -> str:
    """Bereinigt Text für Telegram HTML-Formatierung - ENTFERNT alle nicht unterstützten Tags"""
    if not text:
        return ""
    
    # Ersetze Markdown durch HTML (nur unterstützte Tags)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    
    # ENTFERNE alle nicht unterstützten HTML-Tags komplett
    unsupported_tags = ['div', 'table', 'tr', 'td', 'th', 'span', 'html', 'body', 'head', 'meta', 'style']
    for tag in unsupported_tags:
        text = re.sub(r'</?{}(?:\s+[^>]*)?>'.format(tag), '', text, flags=re.IGNORECASE)
    
    # Entferne überflüssige Leerzeichen und Zeilenumbrüche
    text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Entferne leere HTML-Tags
    text = re.sub(r'<(\w+)></\1>', '', text)
    
    return text.strip()

def convert_to_html(text: str) -> str:
    """Konvertiert Text zu Telegram-kompatibler HTML-Formatierung"""
    return clean_telegram_html(text)

def format_admin_message(user_name, user_id, user_language, user_message, bot_reply):
    """Formatiert Admin-Nachrichten professionell mit HTML"""
    admin_msg = (
        f"💬 <b>NEUE UNTERHALTUNG</b>\n\n"
        f"👤 <b>User:</b> {user_name}\n"
        f"🆔 <b>ID:</b> {user_id}\n"
        f"🌐 <b>Sprache:</b> {user_language}\n"
        f"⏰ <b>Zeit:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"📩 <b>User Nachricht:</b>\n{user_message}\n\n"
        f"🤖 <b>Bot Antwort:</b>\n{bot_reply}"
    )
    return clean_telegram_html(admin_msg)

# 🌍 OPTIMIERTE MEHRSPRACHIGE BEFEHLE
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.username or user.full_name or f"ID:{user.id}"
    
    # Telegram-Sprache erkennen
    user_language = detect_telegram_language(update)
    
    # Sprache in User-Kontext speichern für zukünftige Nachrichten
    update_user_preferred_language(user.id, user_language)
    
    # Passende Nachricht basierend auf Sprache auswählen
    messages = MULTILINGUAL_RESPONSES.get(user_language, MULTILINGUAL_RESPONSES['de'])
    start_msg = messages['start']
    
    welcome_message = (
        f"{start_msg['welcome']}\n\n"
        f"{start_msg['hello'].format(name=name)}\n\n"
        f"{start_msg['services']}\n\n"
        f"{start_msg['features']}\n\n"
        f"{start_msg['note']}\n\n"
        f"{start_msg['question']}"
    )
    
    formatted_welcome = convert_to_html(welcome_message)
    await update.message.reply_text(formatted_welcome, parse_mode=ParseMode.HTML)
    
    admin_msg = format_admin_message(
        name, user.id, user_language, "/start", formatted_welcome
    )
    await context.bot.send_message(
        chat_id=context.bot_data['ADMIN_CHAT_ID'], 
        text=admin_msg, 
        parse_mode=ParseMode.HTML
    )
    
    save_chat(user.id, name, "/start", formatted_welcome)

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Separate contact command for quick access"""
    user = update.effective_user
    name = user.username or user.full_name or f"ID:{user.id}"
    
    # Telegram-Sprache erkennen
    user_language = detect_telegram_language(update)
    
    # Passende Nachricht basierend auf Sprache auswählen
    messages = MULTILINGUAL_RESPONSES.get(user_language, MULTILINGUAL_RESPONSES['de'])
    contact_msg = messages['contact']
    
    contact_info = (
        f"{contact_msg['title']}\n\n"
        f"{contact_msg['address']}\n"
        f"{contact_msg['phone']}\n"
        f"{contact_msg['whatsapp']}\n"
        f"{contact_msg['email']}\n"
        f"{contact_msg['website']}\n"
        f"{contact_msg['hours']}\n"
        f"{contact_msg['languages']}\n\n"
        f"{contact_msg['privacy']}"
    )
    
    formatted_contact = convert_to_html(contact_info)
    await update.message.reply_text(formatted_contact, parse_mode=ParseMode.HTML)
    
    admin_msg = format_admin_message(
        name, user.id, user_language, "/contact", formatted_contact
    )
    await context.bot.send_message(
        chat_id=context.bot_data['ADMIN_CHAT_ID'], 
        text=admin_msg, 
        parse_mode=ParseMode.HTML
    )
    
    save_chat(user.id, name, "/contact", formatted_contact)

async def services_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Separate services command for quick overview"""
    user = update.effective_user
    name = user.username or user.full_name or f"ID:{user.id}"
    
    # Telegram-Sprache erkennen
    user_language = detect_telegram_language(update)
    
    # Passende Nachricht basierend auf Sprache auswählen
    messages = MULTILINGUAL_RESPONSES.get(user_language, MULTILINGUAL_RESPONSES['de'])
    services_msg = messages['services']
    
    services_info = (
        f"{services_msg['title']}\n\n"
        f"{services_msg['moves']}\n\n"
        f"{services_msg['renovation']}\n\n"
        f"{services_msg['cleaning']}\n\n"
        f"{services_msg['guarantee']}"
    )
    
    formatted_services = convert_to_html(services_info)
    await update.message.reply_text(formatted_services, parse_mode=ParseMode.HTML)
    
    admin_msg = format_admin_message(
        name, user.id, user_language, "/services", formatted_services
    )
    await context.bot.send_message(
        chat_id=context.bot_data['ADMIN_CHAT_ID'], 
        text=admin_msg, 
        parse_mode=ParseMode.HTML
    )
    
    save_chat(user.id, name, "/services", formatted_services)

async def prices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to show price examples - KORRIGIERTE VERSION"""
    user = update.effective_user
    name = user.username or user.full_name or f"ID:{user.id}"
    
    # Telegram-Sprache erkennen
    user_language = detect_telegram_language(update)
    
    # Generiere mehrsprachige Preisbeispiele
    breakdown, total = generate_multilingual_price_example(user_language)
    
    # Passende Nachricht basierend auf Sprache auswählen
    messages = MULTILINGUAL_RESPONSES.get(user_language, MULTILINGUAL_RESPONSES['de'])
    prices_msg = messages['prices']
    
    price_info = (
        f"{prices_msg['title']}\n\n"
        f"{prices_msg['example']}\n\n"
    )
    
    for line in breakdown:
        price_info += f"{line}\n"
    
    price_info += f"\n📊 <b>Beispiel-Gesamt: {total:.2f}€</b>\n\n"
    price_info += f"{prices_msg['individual']}\n\n"
    price_info += f"{prices_msg['note']}"
    
    formatted_prices = convert_to_html(price_info)
    await update.message.reply_text(formatted_prices, parse_mode=ParseMode.HTML)
    
    admin_msg = format_admin_message(
        name, user.id, user_language, "/prices", formatted_prices
    )
    await context.bot.send_message(
        chat_id=context.bot_data['ADMIN_CHAT_ID'], 
        text=admin_msg, 
        parse_mode=ParseMode.HTML
    )
    
    save_chat(user.id, name, "/prices", formatted_prices)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command with bot usage instructions"""
    user = update.effective_user
    name = user.username or user.full_name or f"ID:{user.id}"
    
    # Telegram-Sprache erkennen
    user_language = detect_telegram_language(update)
    
    # Passende Nachricht basierend auf Sprache auswählen
    messages = MULTILINGUAL_RESPONSES.get(user_language, MULTILINGUAL_RESPONSES['de'])
    help_msg = messages['help']
    
    help_text = (
        f"{help_msg['title']}\n\n"
        f"{help_msg['commands']}\n\n"
        f"{help_msg['direct']}\n\n"
        f"{help_msg['features']}"
    )
    
    formatted_help = convert_to_html(help_text)
    await update.message.reply_text(formatted_help, parse_mode=ParseMode.HTML)
    
    admin_msg = format_admin_message(
        name, user.id, user_language, "/help", formatted_help
    )
    await context.bot.send_message(
        chat_id=context.bot_data['ADMIN_CHAT_ID'], 
        text=admin_msg, 
        parse_mode=ParseMode.HTML
    )
    
    save_chat(user.id, name, "/help", formatted_help)

async def developer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to show developer information"""
    user = update.effective_user
    name = user.username or user.full_name or f"ID:{user.id}"
    
    # Telegram-Sprache erkennen
    user_language = detect_telegram_language(update)
    
    developer_info = DEVELOPER_INFO.get(user_language, DEVELOPER_INFO['de'])
    
    formatted_developer = convert_to_html(developer_info['description'])
    await update.message.reply_text(formatted_developer, parse_mode=ParseMode.HTML)
    
    admin_msg = format_admin_message(
        name, user.id, user_language, "/entwickler", formatted_developer
    )
    await context.bot.send_message(
        chat_id=context.bot_data['ADMIN_CHAT_ID'], 
        text=admin_msg, 
        parse_mode=ParseMode.HTML
    )
    
    save_chat(user.id, name, "/entwickler", formatted_developer)
async def admin_cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Löscht einen gebuchten Termin"""
    user = update.effective_user
    
    if str(user.id) != context.bot_data.get('ADMIN_USER_ID', ''):
        await update.message.reply_text("❌ Zugriff verweigert!")
        return
    
    if not context.args:
        await update.message.reply_text("🗑️ Verwendung: /cancel DD.MM.YYYY")
        return
    
    try:
        date_str = context.args[0]
        booking_date = datetime.strptime(date_str, "%d.%m.%Y")
        db_date_str = booking_date.strftime("%Y-%m-%d")
        
        with sqlite3.connect("storage.db") as con:
            cur = con.cursor()
            
            # Hole Termin-Info vor dem Löschen
            cur.execute("SELECT customer_name, contact_info FROM appointments WHERE date = ?", (db_date_str,))
            appointment = cur.fetchone()
            
            if not appointment:
                await update.message.reply_text(f"❌ Kein Termin am {date_str} gefunden")
                return
            
            customer_name, contact_info = appointment
            
            # Lösche Termin
            cur.execute("DELETE FROM appointments WHERE date = ?", (db_date_str,))
            con.commit()
            
            response = (
                f"✅ **Termin gelöscht!**\n\n"
                f"📅 **Datum:** {date_str}\n"
                f"👤 **Kunde:** {customer_name}\n"
                f"📞 **Kontakt:** {contact_info}\n\n"
                f"Der Termin wurde erfolgreich storniert."
            )
            
            await update.message.reply_text(response, parse_mode=ParseMode.HTML)
            
    except ValueError:
        await update.message.reply_text("❌ Ungültiges Datum! Format: DD.MM.YYYY")
# 📅 HAUPTChat-FUNKTION MIT KALENDER-INTEGRATION
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.username or user.full_name or f"ID:{user.id}"
    user_message = update.message.text
    current_time = datetime.now()

    # SPRACHERKENNUNG - Zuerst Telegram-Sprache, dann Text
    user_language = detect_telegram_language(update)
    if user_message:
        # Falls Text vorhanden, Text-Sprache als Fallback
        text_language = detect_user_language(user_message)
        # Bevorzuge Telegram-Sprache, außer User korrigiert explizit
        user_language = text_language if text_language != user_language else user_language
    
    # BEHANDLUNG VON AUSSTEHENDEN TERMINBUCHUNGEN
    if 'pending_booking' in context.user_data:
        pending_booking = context.user_data['pending_booking']
        
        # Extrahiere Informationen aus der Nachricht
        booking_info = extract_booking_info(user_message)
        
        if booking_info['name'] and booking_info['contact'] and booking_info['service']:
            # Alle Informationen vorhanden - Termin buchen
            calendar_manager = CalendarManager()
            success = calendar_manager.book_appointment(
                pending_booking['date'],
                booking_info['name'],
                booking_info['contact'],
                booking_info['service'],
                str(user.id)
            )
            
            if success:
                messages = MULTILINGUAL_RESPONSES.get(user_language, MULTILINGUAL_RESPONSES['de'])
                booking_msg = messages['booking']
                
                success_response = booking_msg['success'].format(
                    date=pending_booking['display_date'],
                    customer_name=booking_info['name'],
                    contact_info=booking_info['contact'],
                    service=booking_info['service']
                )
                
                formatted_success = convert_to_html(success_response)
                await update.message.reply_text(formatted_success, parse_mode=ParseMode.HTML)
                
                # Admin-Benachrichtigung
                admin_notification = (
                    f"📅 <b>NEUE TERMINBUCHUNG</b>\n\n"
                    f"👤 <b>Kunde:</b> {booking_info['name']}\n"
                    f"📞 <b>Kontakt:</b> {booking_info['contact']}\n"
                    f"🛠️ <b>Service:</b> {booking_info['service']}\n"
                    f"📅 <b>Datum:</b> {pending_booking['display_date']}\n"
                    f"🆔 <b>User ID:</b> {user.id}\n"
                    f"⏰ <b>Gebucht um:</b> {current_time.strftime('%d.%m.%Y %H:%M')}"
                )
                
                await context.bot.send_message(
                    chat_id=context.bot_data['ADMIN_CHAT_ID'], 
                    text=clean_telegram_html(admin_notification), 
                    parse_mode=ParseMode.HTML
                )
                
                save_chat(user.id, name, user_message, formatted_success)
                
            else:
                messages = MULTILINGUAL_RESPONSES.get(user_language, MULTILINGUAL_RESPONSES['de'])
                booking_msg = messages['booking']
                
                error_response = booking_msg['already_booked'].format(date=pending_booking['display_date'])
                formatted_error = convert_to_html(error_response)
                await update.message.reply_text(formatted_error, parse_mode=ParseMode.HTML)
                save_chat(user.id, name, user_message, formatted_error)
            
            # Pending-Booking zurücksetzen
            del context.user_data['pending_booking']
            return
        else:
            # Nicht alle Informationen vorhanden - nachfragen
            missing_info = []
            if not booking_info['name']:
                missing_info.append("Name")
            if not booking_info['contact']:
                missing_info.append("Telefonnummer")
            if not booking_info['service']:
                missing_info.append("Service")
            
            missing_text = {
                'de': f"❌ <b>Fehlende Informationen:</b>\n\nBitte geben Sie noch an: {', '.join(missing_info)}",
                'en': f"❌ <b>Missing information:</b>\n\nPlease provide: {', '.join(missing_info)}",
                'ar': f"❌ <b>معلومات ناقصة:</b>\n\nيرجى تقديم: {', '.join(missing_info)}",
                'fr': f"❌ <b>Informations manquantes:</b>\n\nVeuillez fournir: {', '.join(missing_info)}",
                'es': f"❌ <b>Información faltante:</b>\n\nPor favor proporcione: {', '.join(missing_info)}",
                'it': f"❌ <b>Informazioni mancanti:</b>\n\nSi prega di fornire: {', '.join(missing_info)}",
                'tr': f"❌ <b>Eksik bilgiler:</b>\n\nLütfen sağlayın: {', '.join(missing_info)}",
                'ru': f"❌ <b>Отсутствующая информация:</b>\n\nПожалуйста, предоставьте: {', '.join(missing_info)}",
                'pl': f"❌ <b>Brakujące informacje:</b>\n\nProszę podać: {', '.join(missing_info)}",
                'uk': f"❌ <b>Відсутня інформація:</b>\n\nБудь ласка, надайте: {', '.join(missing_info)}",
                'zh': f"❌ <b>缺少信息:</b>\n\n请提供: {', '.join(missing_info)}",
                'ja': f"❌ <b>不足情報:</b>\n\n以下を提供してください: {', '.join(missing_info)}",
                'ko': f"❌ <b>누락된 정보:</b>\n\n다음을 제공해 주세요: {', '.join(missing_info)}",
                'pt': f"❌ <b>Informações faltantes:</b>\n\nPor favor forneça: {', '.join(missing_info)}",
                'nl': f"❌ <b>Ontbrekende informatie:</b>\n\nGelieve te verstrekken: {', '.join(missing_info)}",
                'sv': f"❌ <b>Saknad information:</b>\n\nVänligen ange: {', '.join(missing_info)}",
                'da': f"❌ <b>Manglende information:</b>\n\nAngiv venligst: {', '.join(missing_info)}",
                'cs': f"❌ <b>Chybějící informace:</b>\n\nProsím poskytněte: {', '.join(missing_info)}",
                'hr': f"❌ <b>Nedostajuće informacije:</b>\n\nMolimo navedite: {', '.join(missing_info)}",
                'bg': f"❌ <b>Липсваща информация:</b>\n\nМоля, предоставете: {', '.join(missing_info)}",
                'bn': f"❌ <b>অনুপস্থিত তথ্য:</b>\n\nঅনুগ্রহ করে প্রদান করুন: {', '.join(missing_info)}",
                'el': f"❌ <b>Ελλιπείς πληροφορίες:</b>\n\nΠαρακαλώ δώστε: {', '.join(missing_info)}",
                'he': f"❌ <b>חסר מידע:</b>\n\nאנא ספק: {', '.join(missing_info)}",
                'hi': f"❌ <b>गायब जानकारी:</b>\n\nकृपया प्रदान करें: {', '.join(missing_info)}",
                'hu': f"❌ <b>Hiányzó információk:</b>\n\nKérem adja meg: {', '.join(missing_info)}",
                'id': f"❌ <b>Informasi yang hilang:</b>\n\nSilakan berikan: {', '.join(missing_info)}",
                'ms': f"❌ <b>Maklumat yang hilang:</b>\n\nSila berikan: {', '.join(missing_info)}",
                'no': f"❌ <b>Manglende informasjon:</b>\n\nVennligst oppgi: {', '.join(missing_info)}",
                'fi': f"❌ <b>Puuttuvat tiedot:</b>\n\nOle hyvä ja anna: {', '.join(missing_info)}",
                'th': f"❌ <b>ข้อมูลที่ขาดหาย:</b>\n\nกรุณาให้: {', '.join(missing_info)}",
                'vi': f"❌ <b>Thông tin thiếu:</b>\n\nVui lòng cung cấp: {', '.join(missing_info)}",
                'ro': f"❌ <b>Informații lipsă:</b>\n\nVă rugăm să furnizați: {', '.join(missing_info)}",
                'ca': f"❌ <b>Informació faltant:</b>\n\nSi us plau, proporcioneu: {', '.join(missing_info)}"
            }
            
            response = missing_text.get(user_language, missing_text['de'])
            formatted_response = convert_to_html(response)
            await update.message.reply_text(formatted_response, parse_mode=ParseMode.HTML)
            save_chat(user.id, name, user_message, formatted_response)
            return
    
    # ERKENNUNG VON DATUMSFRAGEN
    user_message_lower = user_message.lower() if user_message else ""
    is_date_question = any(word in user_message_lower for word in [
        # Deutsch
        'datum', 'welcher tag', 'welches datum', 'welchen tag haben wir', 'heutiges datum',
        'aktuelles datum', 'welcher tag ist heute', 'welches datum ist heute',
        'wievielter ist heute', 'den wievielten haben wir',
        
        # Englisch
        'date', 'what date', 'today date', 'current date', 'what is the date',
        'which date', 'today\'s date', 'current day', 'what day is it',
        
        # Arabisch
        'اليوم', 'التاريخ', 'تاريخ', 'كم التاريخ', 'اي تاريخ', 'تاريخ اليوم',
        'اليوم اي تاريخ', 'ما التاريخ', 'تاريخ اليوم اي', 'اليوم كم',
        
        # Französisch
        'date', 'quel jour', 'quelle date', 'date d\'aujourd\'hui', 'date actuelle',
        'quel est la date', 'quelle est la date', 'nous sommes le', 'aujourd\'hui c\'est',
        
        # Spanisch
        'fecha', 'qué fecha', 'fecha de hoy', 'fecha actual', 'qué día es',
        'cuál es la fecha', 'hoy es qué fecha', 'la fecha de hoy',
        
        # Italienisch
        'data', 'che data', 'data di oggi', 'data attuale', 'che giorno è',
        'qual è la data', 'oggi che data è', 'la data di oggi',
        
        # Türkisch
        'tarih', 'hangi tarih', 'bugünün tarihi', 'güncel tarih', 'hangi gün',
        'bugün ne tarihi', 'tarih nedir', 'bugünün tarihi ne',
        
        # Russisch
        'дата', 'какая дата', 'сегодняшняя дата', 'текущая дата', 'какой день',
        'какое число', 'сегодня какое число', 'какая сегодня дата',
        
        # Polnisch
        'data', 'jaka data', 'dzisiejsza data', 'aktualna data', 'jaki dzień',
        'która data', 'dzisiaj jaka data', 'bieżąca data',
        
        # Ukrainisch
        'дата', 'яка дата', 'сьогоднішня дата', 'поточна дата', 'який день',
        'яке число', 'сьогодні яке число', 'яка сьогодні дата',
        
        # Chinesisch
        '日期', '什么日期', '今天的日期', '当前日期', '哪一天',
        '今天几号', '现在日期', '今日日期', '今天是几号',
        
        # Japanisch
        '日付', '何の日付', '今日の日付', '現在の日付', '何日',
        '今日は何日', '現在の日付は', '今日の日付は何',
        
        # Koreanisch
        '날짜', '무슨 날짜', '오늘 날짜', '현재 날짜', '무슨 날',
        '오늘은 몇 일', '현재 날짜는', '오늘 날짜는 무엇',
        
        # Portugiesisch
        'data', 'que data', 'data de hoje', 'data atual', 'que dia é',
        'qual é a data', 'hoje que data é', 'a data de hoje',
        
        # Niederländisch
        'datum', 'welke datum', 'datum van vandaag', 'huidige datum', 'welke dag',
        'wat is de datum', 'vandaag welke datum', 'de datum van vandaag',
        
        # Schwedisch
        'datum', 'vilket datum', 'dagens datum', 'aktuellt datum', 'vilken dag',
        'vad är datumet', 'idag vilket datum', 'dagens datum är',
        
        # Dänisch
        'dato', 'hvilken dato', 'dagens dato', 'nuværende dato', 'hvilken dag',
        'hvad er datoen', 'i dag hvilken dato', 'dagens dato er',
        
        # Tschechisch
        'datum', 'jaké datum', 'dnešní datum', 'aktuální datum', 'jaký den',
        'jaké je datum', 'dnes jaké datum', 'dnešní datum je',
        
        # Kroatisch
        'datum', 'koji datum', 'današnji datum', 'trenutni datum', 'koji dan',
        'koji je datum', 'danas koji datum', 'današnji datum je',
        
        # Bulgarisch
        'дата', 'коя дата', 'днешна дата', 'текуща дата', 'кой ден',
        'каква е датата', 'днес коя дата', 'днешната дата е',
        
        # Bengalisch
        'তারিখ', 'কোন তারিখ', 'আজকের তারিখ', 'বর্তমান তারিখ', 'কোন দিন',
        'কি তারিখ', 'আজ কি তারিখ', 'আজকের তারিখ কি',
        
        # Griechisch
        'ημερομηνία', 'ποια ημερομηνία', 'σημερινή ημερομηνία', 'τρέχουσα ημερομηνία', 'ποια μέρα',
        'ποια είναι η ημερομηνία', 'σήμερα ποια ημερομηνία', 'η σημερινή ημερομηνία είναι',
        
        # Hebräisch
        'תאריך', 'איזה תאריך', 'תאריך היום', 'תאריך נוכחי', 'איזה יום',
        'מה התאריך', 'היום איזה תאריך', 'תאריך היום הוא',
        
        # Hindi
        'तारीख', 'कौन सी तारीख', 'आज की तारीख', 'वर्तमान तारीख', 'कौन सा दिन',
        'क्या तारीख है', 'आज क्या तारीख है', 'आज की तारीख क्या है',
        
        # Ungarisch
        'dátum', 'milyen dátum', 'mai dátum', 'jelenlegi dátum', 'milyen nap',
        'mi a dátum', 'ma milyen dátum', 'a mai dátum',
        
        # Indonesisch
        'tanggal', 'tanggal berapa', 'tanggal hari ini', 'tanggal saat ini', 'hari apa',
        'apa tanggalnya', 'hari ini tanggal berapa', 'tanggal hari ini adalah',
        
        # Malaiisch
        'tarikh', 'tarikh mana', 'tarikh hari ini', 'tarikh semasa', 'hari apa',
        'apa tarikh', 'hari ini tarikh apa', 'tarikh hari ini adalah',
        
        # Norwegisch
        'dato', 'hvilken dato', 'dagens dato', 'nåværende dato', 'hvilken dag',
        'hva er datoen', 'i dag hvilken dato', 'dagens dato er',
        
        # Finnisch
        'päivämäärä', 'mikä päivämäärä', 'tämän päivän päivämäärä', 'nykyinen päivämäärä', 'mikä päivä',
        'mikä on päivämäärä', 'tänään mikä päivämäärä', 'tämän päivän päivämäärä on',
        
        # Thailändisch
        'วันที่', 'วันที่ใด', 'วันที่ today', 'วันที่ปัจจุบัน', 'วันอะไร',
        'วันที่คืออะไร', 'วันนี้วันที่อะไร', 'วันที่วันนี้คือ',
        
        # Vietnamesisch
        'ngày', 'ngày nào', 'ngày hôm nay', 'ngày hiện tại', 'ngày gì',
        'ngày là gì', 'hôm nay ngày nào', 'ngày hôm nay là',
        
        # Rumänisch
        'dată', 'ce dată', 'data de astăzi', 'data curentă', 'ce zi',
        'care este data', 'astăzi ce dată', 'data de astăzi este',
        
        # Katalanisch
        'data', 'quina data', 'data d\'avui', 'data actual', 'quin dia',
        'quina és la data', 'avui quina data', 'la data d\'avui és'
    ])
    
    # BEHANDLUNG VON DATUMSFRAGEN
    if is_date_question:
        # Aktuelles Datum formatieren basierend auf Sprache
        if user_language == 'de':
            date_str = current_time.strftime('%d.%m.%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Deutsche Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Montag', 'Tuesday': 'Dienstag', 'Wednesday': 'Mittwoch',
                'Thursday': 'Donnerstag', 'Friday': 'Freitag', 'Saturday': 'Samstag', 'Sunday': 'Sonntag'
            }
            german_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Heutige Informationen:</b>\n\n"
                f"• <b>Datum:</b> {date_str}\n"
                f"• <b>Tag:</b> {german_day}\n"
                f"• <b>Uhrzeit:</b> {time_str}\n\n"
                f"🛻 <b>Benötigen Sie Hilfe mit SHAWO Dienstleistungen?</b>\n\n"
                f"Ich kann Ihnen helfen bei:\n"
                f"• Kompletten Umzügen 🚛\n"
                f"• Renovierungsarbeiten 🎨\n"
                f"• Malerarbeiten 🖌️\n"
                f"• Reinigungsdienstleistungen 🧹\n\n"
                f"Wie kann ich Ihnen heute helfen? 😊"
            )
        elif user_language == 'ar':
            date_str = current_time.strftime('%Y-%m-%d')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Arabische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'الاثنين', 'Tuesday': 'الثلاثاء', 'Wednesday': 'الأربعاء',
                'Thursday': 'الخميس', 'Friday': 'الجمعة', 'Saturday': 'السبت', 'Sunday': 'الأحد'
            }
            arabic_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>معلومات اليوم:</b>\n\n"
                f"• <b>التاريخ:</b> {date_str}\n"
                f"• <b>اليوم:</b> {arabic_day}\n"
                f"• <b>الوقت:</b> {time_str}\n\n"
                f"🛻 <b>هل تحتاج إلى مساعدة في خدمات SHAWO؟</b>\n\n"
                f"يمكنني مساعدتك في:\n"
                f"• التنقلات الكاملة 🚛\n"
                f"• أعمال التجديد 🎨\n" 
                f"• أعمال الدهان 🖌️\n"
                f"• خدمات التنظيف 🧹\n\n"
                f"كيف يمكنني خدمتك اليوم؟ 😊"
            )
        elif user_language == 'fr':
            date_str = current_time.strftime('%d/%m/%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Französische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
                'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
            }
            french_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Informations d'aujourd'hui:</b>\n\n"
                f"• <b>Date:</b> {date_str}\n"
                f"• <b>Jour:</b> {french_day}\n"
                f"• <b>Heure:</b> {time_str}\n\n"
                f"🛻 <b>Avez-vous besoin d'aide avec les services SHAWO?</b>\n\n"
                f"Je peux vous aider avec:\n"
                f"• Déménagements complets 🚛\n"
                f"• Travaux de rénovation 🎨\n"
                f"• Travaux de peinture 🖌️\n"
                f"• Services de nettoyage 🧹\n\n"
                f"Comment puis-je vous aider aujourd'hui? 😊"
            )
        elif user_language == 'es':
            date_str = current_time.strftime('%d/%m/%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Spanische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
                'Thursday': 'Jueves', 'Friday': 'Viernes', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
            }
            spanish_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Información de hoy:</b>\n\n"
                f"• <b>Fecha:</b> {date_str}\n"
                f"• <b>Día:</b> {spanish_day}\n"
                f"• <b>Hora:</b> {time_str}\n\n"
                f"🛻 <b>¿Necesita ayuda con los servicios SHAWO?</b>\n\n"
                f"Puedo ayudarle con:\n"
                f"• Mudanzas completas 🚛\n"
                f"• Trabajos de renovación 🎨\n"
                f"• Trabajos de pintura 🖌️\n"
                f"• Servicios de limpieza 🧹\n\n"
                f"¿Cómo puedo ayudarle hoy? 😊"
            )
        elif user_language == 'it':
            date_str = current_time.strftime('%d/%m/%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Italienische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Lunedì', 'Tuesday': 'Martedì', 'Wednesday': 'Mercoledì',
                'Thursday': 'Giovedì', 'Friday': 'Venerdì', 'Saturday': 'Sabato', 'Sunday': 'Domenica'
            }
            italian_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Informazioni di oggi:</b>\n\n"
                f"• <b>Data:</b> {date_str}\n"
                f"• <b>Giorno:</b> {italian_day}\n"
                f"• <b>Ora:</b> {time_str}\n\n"
                f"🛻 <b>Ha bisogno di aiuto con i servizi SHAWO?</b>\n\n"
                f"Posso aiutarla con:\n"
                f"• Traslochi completi 🚛\n"
                f"• Lavori di ristrutturazione 🎨\n"
                f"• Lavori di pittura 🖌️\n"
                f"• Servizi di pulizia 🧹\n\n"
                f"Come posso aiutarla oggi? 😊"
            )
        elif user_language == 'tr':
            date_str = current_time.strftime('%d.%m.%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Türkische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Pazartesi', 'Tuesday': 'Salı', 'Wednesday': 'Çarşamba',
                'Thursday': 'Perşembe', 'Friday': 'Cuma', 'Saturday': 'Cumartesi', 'Sunday': 'Pazar'
            }
            turkish_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Bugünün Bilgileri:</b>\n\n"
                f"• <b>Tarih:</b> {date_str}\n"
                f"• <b>Gün:</b> {turkish_day}\n"
                f"• <b>Saat:</b> {time_str}\n\n"
                f"🛻 <b>SHAWO hizmetleriyle ilgili yardıma ihtiyacınız var mı?</b>\n\n"
                f"Size şu konularda yardımcı olabilirim:\n"
                f"• Komplet taşınmalar 🚛\n"
                f"• Yenileme işleri 🎨\n"
                f"• Boya işleri 🖌️\n"
                f"• Temizlik hizmetleri 🧹\n\n"
                f"Bugün size nasıl yardımcı olabilirim? 😊"
            )
        elif user_language == 'ru':
            date_str = current_time.strftime('%d.%m.%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Russische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Понедельник', 'Tuesday': 'Вторник', 'Wednesday': 'Среда',
                'Thursday': 'Четверг', 'Friday': 'Пятница', 'Saturday': 'Суббота', 'Sunday': 'Воскресенье'
            }
            russian_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Сегодняшняя информация:</b>\n\n"
                f"• <b>Дата:</b> {date_str}\n"
                f"• <b>День:</b> {russian_day}\n"
                f"• <b>Время:</b> {time_str}\n\n"
                f"🛻 <b>Нужна помощь с услугами SHAWO?</b>\n\n"
                f"Я могу помочь вам с:\n"
                f"• Полными переездами 🚛\n"
                f"• Ремонтными работами 🎨\n"
                f"• Малярными работами 🖌️\n"
                f"• Услугами уборки 🧹\n\n"
                f"Как я могу помочь вам сегодня? 😊"
            )
        elif user_language == 'pl':
            date_str = current_time.strftime('%d.%m.%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Polnische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Poniedziałek', 'Tuesday': 'Wtorek', 'Wednesday': 'Środa',
                'Thursday': 'Czwartek', 'Friday': 'Piątek', 'Saturday': 'Sobota', 'Sunday': 'Niedziela'
            }
            polish_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Dzisiejsze informacje:</b>\n\n"
                f"• <b>Data:</b> {date_str}\n"
                f"• <b>Dzień:</b> {polish_day}\n"
                f"• <b>Czas:</b> {time_str}\n\n"
                f"🛻 <b>Czy potrzebujesz pomocy z usługami SHAWO?</b>\n\n"
                f"Mogę Ci pomóc z:\n"
                f"• Kompleksowymi przeprowadzkami 🚛\n"
                f"• Pracami remontowymi 🎨\n"
                f"• Pracami malarskimi 🖌️\n"
                f"• Usługami sprzątania 🧹\n\n"
                f"Jak mogę Ci dziś pomóc? 😊"
            )
        elif user_language == 'uk':
            date_str = current_time.strftime('%d.%m.%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Ukrainische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Понеділок', 'Tuesday': 'Вівторок', 'Wednesday': 'Середа',
                'Thursday': 'Четвер', 'Friday': 'П\'ятниця', 'Saturday': 'Субота', 'Sunday': 'Неділя'
            }
            ukrainian_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Сьогоднішня інформація:</b>\n\n"
                f"• <b>Дата:</b> {date_str}\n"
                f"• <b>День:</b> {ukrainian_day}\n"
                f"• <b>Час:</b> {time_str}\n\n"
                f"🛻 <b>Чи потрібна допомога з послугами SHAWO?</b>\n\n"
                f"Я можу допомогти вам з:\n"
                f"• Повними переїздами 🚛\n"
                f"• Ремонтними роботами 🎨\n"
                f"• Малярними роботами 🖌️\n"
                f"• Послугами прибирання 🧹\n\n"
                f"Як я можу допомогти вам сьогодні? 😊"
            )
        elif user_language == 'zh':
            date_str = current_time.strftime('%Y年%m月%d日')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Chinesische Übersetzung der Wochentage
            day_translations = {
                'Monday': '星期一', 'Tuesday': '星期二', 'Wednesday': '星期三',
                'Thursday': '星期四', 'Friday': '星期五', 'Saturday': '星期六', 'Sunday': '星期日'
            }
            chinese_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>今日信息:</b>\n\n"
                f"• <b>日期:</b> {date_str}\n"
                f"• <b>星期:</b> {chinese_day}\n"
                f"• <b>时间:</b> {time_str}\n\n"
                f"🛻 <b>需要 SHAWO 服务的帮助吗？</b>\n\n"
                f"我可以帮助您：\n"
                f"• 完整搬家 🚛\n"
                f"• 装修工作 🎨\n"
                f"• 油漆工作 🖌️\n"
                f"• 清洁服务 🧹\n\n"
                f"今天我能为您做什么？😊"
            )
        elif user_language == 'ja':
            date_str = current_time.strftime('%Y年%m月%d日')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Japanische Übersetzung der Wochentage
            day_translations = {
                'Monday': '月曜日', 'Tuesday': '火曜日', 'Wednesday': '水曜日',
                'Thursday': '木曜日', 'Friday': '金曜日', 'Saturday': '土曜日', 'Sunday': '日曜日'
            }
            japanese_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>本日の情報:</b>\n\n"
                f"• <b>日付:</b> {date_str}\n"
                f"• <b>曜日:</b> {japanese_day}\n"
                f"• <b>時間:</b> {time_str}\n\n"
                f"🛻 <b>SHAWOのサービスについてお手伝いしましょうか？</b>\n\n"
                f"以下のことでお手伝いできます：\n"
                f"• 完全な引越し 🚛\n"
                f"• リフォーム作業 🎨\n"
                f"• 塗装作業 🖌️\n"
                f"• 清掃サービス 🧹\n\n"
                f"本日はどのようなご用件でしょうか？😊"
            )
        elif user_language == 'ko':
            date_str = current_time.strftime('%Y년 %m월 %d일')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Koreanische Übersetzung der Wochentage
            day_translations = {
                'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일',
                'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'
            }
            korean_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>오늘의 정보:</b>\n\n"
                f"• <b>날짜:</b> {date_str}\n"
                f"• <b>요일:</b> {korean_day}\n"
                f"• <b>시간:</b> {time_str}\n\n"
                f"🛻 <b>SHAWO 서비스에 도움이 필요하신가요?</b>\n\n"
                f"다음과 같은 일을 도와드릴 수 있습니다:\n"
                f"• 완전한 이사 🚛\n"
                f"• 리모델링 작업 🎨\n"
                f"• 도장 작업 🖌️\n"
                f"• 청소 서비스 🧹\n\n"
                f"오늘 어떻게 도와드릴까요? 😊"
            )
        elif user_language == 'pt':
            date_str = current_time.strftime('%d/%m/%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Portugiesische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Segunda-feira', 'Tuesday': 'Terça-feira', 'Wednesday': 'Quarta-feira',
                'Thursday': 'Quinta-feira', 'Friday': 'Sexta-feira', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
            }
            portuguese_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Informações de hoje:</b>\n\n"
                f"• <b>Data:</b> {date_str}\n"
                f"• <b>Dia:</b> {portuguese_day}\n"
                f"• <b>Hora:</b> {time_str}\n\n"
                f"🛻 <b>Precisa de ajuda com os serviços SHAWO?</b>\n\n"
                f"Posso ajudá-lo com:\n"
                f"• Mudanças completas 🚛\n"
                f"• Trabalhos de renovação 🎨\n"
                f"• Trabalhos de pintura 🖌️\n"
                f"• Serviços de limpeza 🧹\n\n"
                f"Como posso ajudá-lo hoje? 😊"
            )
        elif user_language == 'nl':
            date_str = current_time.strftime('%d-%m-%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Niederländische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Maandag', 'Tuesday': 'Dinsdag', 'Wednesday': 'Woensdag',
                'Thursday': 'Donderdag', 'Friday': 'Vrijdag', 'Saturday': 'Zaterdag', 'Sunday': 'Zondag'
            }
            dutch_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Informatie van vandaag:</b>\n\n"
                f"• <b>Datum:</b> {date_str}\n"
                f"• <b>Dag:</b> {dutch_day}\n"
                f"• <b>Tijd:</b> {time_str}\n\n"
                f"🛻 <b>Heeft u hulp nodig met SHAWO diensten?</b>\n\n"
                f"Ik kan u helpen met:\n"
                f"• Complete verhuizingen 🚛\n"
                f"• Renovatie werk 🎨\n"
                f"• Schilderwerk 🖌️\n"
                f"• Schoonmaakdiensten 🧹\n\n"
                f"Hoe kan ik u vandaag helpen? 😊"
            )
        elif user_language == 'sv':
            date_str = current_time.strftime('%Y-%m-%d')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Schwedische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Måndag', 'Tuesday': 'Tisdag', 'Wednesday': 'Onsdag',
                'Thursday': 'Torsdag', 'Friday': 'Fredag', 'Saturday': 'Lördag', 'Sunday': 'Söndag'
            }
            swedish_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Dagens information:</b>\n\n"
                f"• <b>Datum:</b> {date_str}\n"
                f"• <b>Dag:</b> {swedish_day}\n"
                f"• <b>Tid:</b> {time_str}\n\n"
                f"🛻 <b>Behöver du hjälp med SHAWO tjänster?</b>\n\n"
                f"Jag kan hjälpa dig med:\n"
                f"• Kompletta flyttar 🚛\n"
                f"• Renoveringsarbeten 🎨\n"
                f"• Målningarbeten 🖌️\n"
                f"• Städtjänster 🧹\n\n"
                f"Hur kan jag hjälpa dig idag? 😊"
            )
        elif user_language == 'da':
            date_str = current_time.strftime('%d-%m-%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Dänische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Mandag', 'Tuesday': 'Tirsdag', 'Wednesday': 'Onsdag',
                'Thursday': 'Torsdag', 'Friday': 'Fredag', 'Saturday': 'Lørdag', 'Sunday': 'Søndag'
            }
            danish_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Dagens information:</b>\n\n"
                f"• <b>Dato:</b> {date_str}\n"
                f"• <b>Dag:</b> {danish_day}\n"
                f"• <b>Tid:</b> {time_str}\n\n"
                f"🛻 <b>Har du brug for hjælp med SHAWO tjenester?</b>\n\n"
                f"Jeg kan hjælpe dig med:\n"
                f"• Komplette flytninger 🚛\n"
                f"• Renoveringsarbejde 🎨\n"
                f"• Malerarbejde 🖌️\n"
                f"• Rengøringstjenester 🧹\n\n"
                f"Hvordan kan jeg hjælpe dig i dag? 😊"
            )
        elif user_language == 'cs':
            date_str = current_time.strftime('%d.%m.%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Tschechische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Pondělí', 'Tuesday': 'Úterý', 'Wednesday': 'Středa',
                'Thursday': 'Čtvrtek', 'Friday': 'Pátek', 'Saturday': 'Sobota', 'Sunday': 'Neděle'
            }
            czech_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Dnešní informace:</b>\n\n"
                f"• <b>Datum:</b> {date_str}\n"
                f"• <b>Den:</b> {czech_day}\n"
                f"• <b>Čas:</b> {time_str}\n\n"
                f"🛻 <b>Potřebujete pomoc se službami SHAWO?</b>\n\n"
                f"Můžu vám pomoci s:\n"
                f"• Kompletními stěhováními 🚛\n"
                f"• Renovačními pracemi 🎨\n"
                f"• Malířskými pracemi 🖌️\n"
                f"• Úklidovými službami 🧹\n\n"
                f"Jak vám mohu dnes pomoci? 😊"
            )
        elif user_language == 'hr':
            date_str = current_time.strftime('%d.%m.%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Kroatische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Ponedjeljak', 'Tuesday': 'Utorak', 'Wednesday': 'Srijeda',
                'Thursday': 'Četvrtak', 'Friday': 'Petak', 'Saturday': 'Subota', 'Sunday': 'Nedjelja'
            }
            croatian_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Današnje informacije:</b>\n\n"
                f"• <b>Datum:</b> {date_str}\n"
                f"• <b>Dan:</b> {croatian_day}\n"
                f"• <b>Vrijeme:</b> {time_str}\n\n"
                f"🛻 <b>Trebate li pomoć s SHAWO uslugama?</b>\n\n"
                f"Mogu vam pomoći s:\n"
                f"• Potpunim selidbama 🚛\n"
                f"• Radovima obnove 🎨\n"
                f"• Slikarskim radovima 🖌️\n"
                f"• Uslugama čišćenja 🧹\n\n"
                f"Kako vam mogu danas pomoći? 😊"
            )
        elif user_language == 'bg':
            date_str = current_time.strftime('%d.%m.%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Bulgarische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Понеделник', 'Tuesday': 'Вторник', 'Wednesday': 'Сряда',
                'Thursday': 'Четвъртък', 'Friday': 'Петък', 'Saturday': 'Събота', 'Sunday': 'Неделя'
            }
            bulgarian_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Днешна информация:</b>\n\n"
                f"• <b>Дата:</b> {date_str}\n"
                f"• <b>Ден:</b> {bulgarian_day}\n"
                f"• <b>Време:</b> {time_str}\n\n"
                f"🛻 <b>Имате ли нужда от помощ с SHAWO услуги?</b>\n\n"
                f"Мога да ви помогна с:\n"
                f"• Пълни премествания 🚛\n"
                f"• Ремонтни работи 🎨\n"
                f"• Боядисване 🖌️\n"
                f"• Почистващи услуги 🧹\n\n"
                f"Как мога да ви помогна днес? 😊"
            )
        elif user_language == 'bn':
            date_str = current_time.strftime('%d/%m/%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Bengalische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'সোমবার', 'Tuesday': 'মঙ্গলবার', 'Wednesday': 'বুধবার',
                'Thursday': 'বৃহস্পতিবার', 'Friday': 'শুক্রবার', 'Saturday': 'শনিবার', 'Sunday': 'রবিবার'
            }
            bengali_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>আজকের তথ্য:</b>\n\n"
                f"• <b>তারিখ:</b> {date_str}\n"
                f"• <b>দিন:</b> {bengali_day}\n"
                f"• <b>সময়:</b> {time_str}\n\n"
                f"🛻 <b>SHAWO পরিষেবাগুলির সাথে সাহায্য প্রয়োজন?</b>\n\n"
                f"আমি আপনাকে সাহায্য করতে পারি:\n"
                f"• সম্পূর্ণ স্থানান্তর 🚛\n"
                f"• সংস্কার কাজ 🎨\n"
                f"• পেইন্টিং কাজ 🖌️\n"
                f"• পরিষ্কার পরিষেবা 🧹\n\n"
                f"আজ আমি আপনাকে কিভাবে সাহায্য করতে পারি? 😊"
            )
        elif user_language == 'el':
            date_str = current_time.strftime('%d/%m/%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Griechische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Δευτέρα', 'Tuesday': 'Τρίτη', 'Wednesday': 'Τετάρτη',
                'Thursday': 'Πέμπτη', 'Friday': 'Παρασκευή', 'Saturday': 'Σάββατο', 'Sunday': 'Κυριακή'
            }
            greek_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Σημερινές πληροφορίες:</b>\n\n"
                f"• <b>Ημερομηνία:</b> {date_str}\n"
                f"• <b>Ημέρα:</b> {greek_day}\n"
                f"• <b>Ώρα:</b> {time_str}\n\n"
                f"🛻 <b>Χρειάζεστε βοήθεια με τις υπηρεσίες SHAWO;</b>\n\n"
                f"Μπορώ να σας βοηθήσω με:\n"
                f"• Πλήρεις μετακομίσεις 🚛\n"
                f"• Εργασίες ανακαίνισης 🎨\n"
                f"• Εργασίες βαφής 🖌️\n"
                f"• Υπηρεσίες καθαρισμού 🧹\n\n"
                f"Πώς μπορώ να σας βοηθήσω σήμερα; 😊"
            )
        elif user_language == 'he':
            date_str = current_time.strftime('%d/%m/%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Hebräische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'יום שני', 'Tuesday': 'יום שלישי', 'Wednesday': 'יום רביעי',
                'Thursday': 'יום חמישי', 'Friday': 'יום שישי', 'Saturday': 'יום שבת', 'Sunday': 'יום ראשון'
            }
            hebrew_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>מידע להיום:</b>\n\n"
                f"• <b>תאריך:</b> {date_str}\n"
                f"• <b>יום:</b> {hebrew_day}\n"
                f"• <b>שעה:</b> {time_str}\n\n"
                f"🛻 <b>האם אתה זקוק לעזרה בשירותי SHAWO?</b>\n\n"
                f"אני יכול לעזור לך עם:\n"
                f"• מעברים מלאים 🚛\n"
                f"• עבודות שיפוץ 🎨\n"
                f"• עבודות צביעה 🖌️\n"
                f"• שירותי ניקיון 🧹\n\n"
                f"איך אוכל לעזור לך היום? 😊"
            )
        elif user_language == 'hi':
            date_str = current_time.strftime('%d/%m/%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Hindi Übersetzung der Wochentage
            day_translations = {
                'Monday': 'सोमवार', 'Tuesday': 'मंगलवार', 'Wednesday': 'बुधवार',
                'Thursday': 'गुरुवार', 'Friday': 'शुक्रवार', 'Saturday': 'शनिवार', 'Sunday': 'रविवार'
            }
            hindi_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>आज की जानकारी:</b>\n\n"
                f"• <b>तारीख:</b> {date_str}\n"
                f"• <b>दिन:</b> {hindi_day}\n"
                f"• <b>समय:</b> {time_str}\n\n"
                f"🛻 <b>क्या आपको SHAWO सेवाओं में सहायता चाहिए?</b>\n\n"
                f"मैं आपकी सहायता कर सकता हूं:\n"
                f"• पूर्ण स्थानांतरण 🚛\n"
                f"• नवीनीकरण कार्य 🎨\n"
                f"• पेंटिंग कार्य 🖌️\n"
                f"• सफाई सेवाएं 🧹\n\n"
                f"आज मैं आपकी कैसे मदद कर सकता हूं? 😊"
            )
        elif user_language == 'hu':
            date_str = current_time.strftime('%Y.%m.%d.')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Ungarische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Hétfő', 'Tuesday': 'Kedd', 'Wednesday': 'Szerda',
                'Thursday': 'Csütörtök', 'Friday': 'Péntek', 'Saturday': 'Szombat', 'Sunday': 'Vasárnap'
            }
            hungarian_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Mai információk:</b>\n\n"
                f"• <b>Dátum:</b> {date_str}\n"
                f"• <b>Nap:</b> {hungarian_day}\n"
                f"• <b>Idő:</b> {time_str}\n\n"
                f"🛻 <b>Segítségre van szüksége a SHAWO szolgáltatásokkal?</b>\n\n"
                f"Segíthetek Önnek:\n"
                f"• Teljes költöztetések 🚛\n"
                f"• Felújítási munkák 🎨\n"
                f"• Festési munkák 🖌️\n"
                f"• Takarítási szolgáltatások 🧹\n\n"
                f"Hogyan segíthetek ma Önnek? 😊"
            )
        elif user_language == 'id':
            date_str = current_time.strftime('%d/%m/%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Indonesische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
                'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'
            }
            indonesian_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Informasi Hari Ini:</b>\n\n"
                f"• <b>Tanggal:</b> {date_str}\n"
                f"• <b>Hari:</b> {indonesian_day}\n"
                f"• <b>Waktu:</b> {time_str}\n\n"
                f"🛻 <b>Butuh bantuan dengan layanan SHAWO?</b>\n\n"
                f"Saya dapat membantu Anda dengan:\n"
                f"• Pindahan lengkap 🚛\n"
                f"• Pekerjaan renovasi 🎨\n"
                f"• Pekerjaan cat 🖌️\n"
                f"• Layanan pembersihan 🧹\n\n"
                f"Bagaimana saya bisa membantu Anda hari ini? 😊"
            )
        elif user_language == 'ms':
            date_str = current_time.strftime('%d/%m/%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Malaiische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Isnin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
                'Thursday': 'Khamis', 'Friday': 'Jumaat', 'Saturday': 'Sabtu', 'Sunday': 'Ahad'
            }
            malay_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Maklumat Hari Ini:</b>\n\n"
                f"• <b>Tarikh:</b> {date_str}\n"
                f"• <b>Hari:</b> {malay_day}\n"
                f"• <b>Masa:</b> {time_str}\n\n"
                f"🛻 <b>Perlukan bantuan dengan perkhidmatan SHAWO?</b>\n\n"
                f"Saya boleh membantu anda dengan:\n"
                f"• Pindahan lengkap 🚛\n"
                f"• Kerja-kerja renovasi 🎨\n"
                f"• Kerja-kerja cat 🖌️\n"
                f"• Perkhidmatan pembersihan 🧹\n\n"
                f"Bagaimana saya boleh membantu anda hari ini? 😊"
            )
        elif user_language == 'no':
            date_str = current_time.strftime('%d.%m.%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Norwegische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Mandag', 'Tuesday': 'Tirsdag', 'Wednesday': 'Onsdag',
                'Thursday': 'Torsdag', 'Friday': 'Fredag', 'Saturday': 'Lørdag', 'Sunday': 'Søndag'
            }
            norwegian_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Dagens informasjon:</b>\n\n"
                f"• <b>Dato:</b> {date_str}\n"
                f"• <b>Dag:</b> {norwegian_day}\n"
                f"• <b>Tid:</b> {time_str}\n\n"
                f"🛻 <b>Trenger du hjelp med SHAWO tjenester?</b>\n\n"
                f"Jeg kan hjelpe deg med:\n"
                f"• Komplette flyttinger 🚛\n"
                f"• Renoveringsarbeid 🎨\n"
                f"• Malerarbeid 🖌️\n"
                f"• Rengjøringstjenester 🧹\n\n"
                f"Hvordan kan jeg hjelpe deg i dag? 😊"
            )
        elif user_language == 'fi':
            date_str = current_time.strftime('%d.%m.%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Finnische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Maanantai', 'Tuesday': 'Tiistai', 'Wednesday': 'Keskiviikko',
                'Thursday': 'Torstai', 'Friday': 'Perjantai', 'Saturday': 'Lauantai', 'Sunday': 'Sunnuntai'
            }
            finnish_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Tämän päivän tiedot:</b>\n\n"
                f"• <b>Päivämäärä:</b> {date_str}\n"
                f"• <b>Päivä:</b> {finnish_day}\n"
                f"• <b>Aika:</b> {time_str}\n\n"
                f"🛻 <b>Tarvitsetko apua SHAWO palveluiden kanssa?</b>\n\n"
                f"Voin auttaa sinua:\n"
                f"• Täydellisissä muutoissa 🚛\n"
                f"• Kunnostustöissä 🎨\n"
                f"• Maalaustöissä 🖌️\n"
                f"• Siivouspalveluissa 🧹\n\n"
                f"Kuinka voin auttaa sinua tänään? 😊"
            )
        elif user_language == 'th':
            date_str = current_time.strftime('%d/%m/%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Thailändische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'วันจันทร์', 'Tuesday': 'วันอังคาร', 'Wednesday': 'วันพุธ',
                'Thursday': 'วันพฤหัสบดี', 'Friday': 'วันศุกร์', 'Saturday': 'วันเสาร์', 'Sunday': 'วันอาทิตย์'
            }
            thai_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>ข้อมูลวันนี้:</b>\n\n"
                f"• <b>วันที่:</b> {date_str}\n"
                f"• <b>วัน:</b> {thai_day}\n"
                f"• <b>เวลา:</b> {time_str}\n\n"
                f"🛻 <b>ต้องการความช่วยเหลือเกี่ยวกับบริการ SHAWO หรือไม่?</b>\n\n"
                f"ฉันสามารถช่วยคุณได้ใน:\n"
                f"• การย้ายที่สมบูรณ์ 🚛\n"
                f"• งานปรับปรุง 🎨\n"
                f"• งานทาสี 🖌️\n"
                f"• บริการทำความสะอาด 🧹\n\n"
                f"วันนี้ฉันจะช่วยคุณได้อย่างไร? 😊"
            )
        elif user_language == 'vi':
            date_str = current_time.strftime('%d/%m/%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Vietnamesische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Thứ Hai', 'Tuesday': 'Thứ Ba', 'Wednesday': 'Thứ Tư',
                'Thursday': 'Thứ Năm', 'Friday': 'Thứ Sáu', 'Saturday': 'Thứ Bảy', 'Sunday': 'Chủ Nhật'
            }
            vietnamese_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Thông tin hôm nay:</b>\n\n"
                f"• <b>Ngày:</b> {date_str}\n"
                f"• <b>Thứ:</b> {vietnamese_day}\n"
                f"• <b>Giờ:</b> {time_str}\n\n"
                f"🛻 <b>Bạn có cần trợ giúp với dịch vụ SHAWO không?</b>\n\n"
                f"Tôi có thể giúp bạn với:\n"
                f"• Chuyển nhà trọn gói 🚛\n"
                f"• Công việc cải tạo 🎨\n"
                f"• Công việc sơn 🖌️\n"
                f"• Dịch vụ vệ sinh 🧹\n\n"
                f"Hôm nay tôi có thể giúp gì cho bạn? 😊"
            )
        elif user_language == 'ro':
            date_str = current_time.strftime('%d.%m.%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Rumänische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Luni', 'Tuesday': 'Marți', 'Wednesday': 'Miercuri',
                'Thursday': 'Joi', 'Friday': 'Vineri', 'Saturday': 'Sâmbătă', 'Sunday': 'Duminică'
            }
            romanian_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Informații de astăzi:</b>\n\n"
                f"• <b>Data:</b> {date_str}\n"
                f"• <b>Zi:</b> {romanian_day}\n"
                f"• <b>Ora:</b> {time_str}\n\n"
                f"🛻 <b>Aveți nevoie de ajutor cu serviciile SHAWO?</b>\n\n"
                f"Vă pot ajuta cu:\n"
                f"• Mutări complete 🚛\n"
                f"• Lucrări de renovare 🎨\n"
                f"• Lucrări de vopsire 🖌️\n"
                f"• Servicii de curățenie 🧹\n\n"
                f"Cum vă pot ajuta astăzi? 😊"
            )
        elif user_language == 'ca':
            date_str = current_time.strftime('%d/%m/%Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Katalanische Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Dilluns', 'Tuesday': 'Dimarts', 'Wednesday': 'Dimecres',
                'Thursday': 'Dijous', 'Friday': 'Divendres', 'Saturday': 'Dissabte', 'Sunday': 'Diumenge'
            }
            catalan_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Informació d'avui:</b>\n\n"
                f"• <b>Data:</b> {date_str}\n"
                f"• <b>Dia:</b> {catalan_day}\n"
                f"• <b>Hora:</b> {time_str}\n\n"
                f"🛻 <b>Necessita ajuda amb els serveis SHAWO?</b>\n\n"
                f"Puc ajudar-lo amb:\n"
                f"• Mudances completes 🚛\n"
                f"• Obres de renovació 🎨\n"
                f"• Obres de pintura 🖌️\n"
                f"• Serveis de neteja 🧹\n\n"
                f"Com puc ajudar-lo avui? 😊"
            )
        elif user_language == 'en':
            date_str = current_time.strftime('%B %d, %Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            
            bot_reply = (
                f"📅 <b>Today's Information:</b>\n\n"
                f"• <b>Date:</b> {date_str}\n"
                f"• <b>Day:</b> {day_str}\n"
                f"• <b>Time:</b> {time_str}\n\n"
                f"🛻 <b>Do you need help with SHAWO services?</b>\n\n"
                f"I can assist you with:\n"
                f"• Complete moves 🚛\n"
                f"• Renovation work 🎨\n"
                f"• Painting work 🖌️\n"
                f"• Cleaning services 🧹\n\n"
                f"How can I help you today? 😊"
            )
        else:  # Deutsch
            date_str = current_time.strftime('%d. %B %Y')
            time_str = current_time.strftime('%H:%M')
            day_str = current_time.strftime('%A')
            # Deutsche Übersetzung der Wochentage
            day_translations = {
                'Monday': 'Montag', 'Tuesday': 'Dienstag', 'Wednesday': 'Mittwoch',
                'Thursday': 'Donnerstag', 'Friday': 'Freitag', 'Saturday': 'Samstag', 'Sunday': 'Sonntag'
            }
            german_day = day_translations.get(day_str, day_str)
            
            bot_reply = (
                f"📅 <b>Heutige Informationen:</b>\n\n"
                f"• <b>Datum:</b> {date_str}\n"
                f"• <b>Tag:</b> {german_day}\n"
                f"• <b>Uhrzeit:</b> {time_str}\n\n"
                f"🛻 <b>Benötigen Sie Hilfe mit SHAWO Dienstleistungen?</b>\n\n"
                f"Ich kann Ihnen helfen bei:\n"
                f"• Kompletten Umzügen 🚛\n"
                f"• Renovierungsarbeiten 🎨\n"
                f"• Malerarbeiten 🖌️\n"
                f"• Reinigungsdienstleistungen 🧹\n\n"
                f"Wie kann ich Ihnen heute behilflich sein? 😊"
            )
        
        formatted_reply = convert_to_html(bot_reply)
        await update.message.reply_text(formatted_reply, parse_mode=ParseMode.HTML)
        
        save_chat(user.id, name, user_message, formatted_reply)
        
        admin_msg = format_admin_message(
            name, user.id, user_language, user_message, formatted_reply
        )
        await context.bot.send_message(
            chat_id=context.bot_data['ADMIN_CHAT_ID'], 
            text=admin_msg, 
            parse_mode=ParseMode.HTML
        )
        return
    
    # ERKENNUNG VON SPRACHKORREKTUREN - VERBESSERTE VERSION
    is_language_correction = any(phrase in user_message_lower for phrase in [
        # Deutsch
        'falsche sprache', 'sprechen sie', 'sprachfehler', 'andere sprache', 'sprache wechseln',
        'auf deutsch', 'deutsch bitte', 'kannst du deutsch',
        
        # Englisch
        'wrong language', 'speak in', 'language error', 'different language', 'change language',
        'in english', 'english please', 'can you english',
        
        # Arabisch
        'لغة خاطئة', 'تحدث بال', 'خطأ في اللغة', 'لغة مختلفة', 'غير اللغة',
        'بالعربية', 'عربي رجاء', 'بتقدر عربي',
        
        # Französisch
        'mauvaise langue', 'parlez en', 'erreur de langue', 'langue différente', 'changer de langue',
        'en français', 'français s\'il vous plaît', 'pouvez-vous français',
        
        # Spanisch
        'idioma incorrecto', 'habla en', 'error de idioma', 'idioma diferente', 'cambiar idioma',
        'en español', 'español por favor', 'puedes español',
        
        # Italienisch
        'lingua sbagliata', 'parla in', 'errore di lingua', 'lingua diversa', 'cambiare lingua',
        'in italiano', 'italiano per favore', 'puoi italiano',
        
        # Türkisch
        'yanlış dil', 'konuş', 'dil hatası', 'farklı dil', 'dili değiştir',
        'türkçe', 'türkçe lütfen', 'türkçe konuşabilir misin',
        
        # Russisch
        'неправильный язык', 'говорите на', 'ошибка языка', 'другой язык', 'сменить язык',
        'на русском', 'русский пожалуйста', 'вы можете по-русски',
        
        # Polnisch
        'zły język', 'mów po', 'błąd języka', 'inny język', 'zmienić język',
        'po polsku', 'polski proszę', 'czy możesz po polsku',
        
        # Ukrainisch
        'невірна мова', 'говоріть', 'помилка мови', 'інша мова', 'змінити мову',
        'українською', 'українська будь ласка', 'ви можете українською',
        
        # Chinesisch
        '错误的语言', '说', '语言错误', '不同的语言', '改变语言',
        '用中文', '中文请', '你会中文吗',
        
        # Japanisch
        '間違った言語', '話して', '言語エラー', '別の言語', '言語を変更',
        '日本語で', '日本語でお願いします', '日本語話せますか',
        
        # Koreanisch
        '잘못된 언어', '말해', '언어 오류', '다른 언어', '언어 변경',
        '한국어로', '한국어로 해주세요', '한국어 할 수 있나요',
        
        # Portugiesisch
        'língua errada', 'fale em', 'erro de língua', 'língua diferente', 'mudar de língua',
        'em português', 'português por favor', 'pode português',
        
        # Niederländisch
        'verkeerde taal', 'spreek', 'taalfout', 'andere taal', 'taal veranderen',
        'in het nederlands', 'nederlands alsjeblieft', 'kun je nederlands',
        
        # Schwedisch
        'fel språk', 'tala', 'språkfel', 'annat språk', 'byta språk',
        'på svenska', 'svenska tack', 'kan du svenska',
        
        # Dänisch
        'forkert sprog', 'tal', 'sprogfejl', 'andet sprog', 'skift sprog',
        'på dansk', 'dansk tak', 'kan du dansk',
        
        # Tschechisch
        'špatný jazyk', 'mluvte', 'chyba jazyka', 'jiný jazyk', 'změnit jazyk',
        'česky', 'česky prosím', 'umíš česky',
        
        # Kroatisch
        'pogrešan jezik', 'govorite', 'greška jezika', 'drugi jezik', 'promijeni jezik',
        'na hrvatskom', 'hrvatski molim', 'možete li hrvatski',
        
        # Bulgarisch
        'грешен език', 'говорете на', 'грешка в езика', 'различен език', 'сменете езика',
        'на български', 'български моля', 'можете ли на български',
        
        # Bengalisch
        'ভুল ভাষা', 'বলুন', 'ভাষা ত্রুটি', 'ভিন্ন ভাষা', 'ভাষা পরিবর্তন',
        'বাংলায়', 'বাংলায় দয়া করে', 'আপনি বাংলা বলতে পারেন',
        
        # Griechisch
        'λάθος γλώσσα', 'μιλήστε', 'σφάλμα γλώσσας', 'διαφορετική γλώσσα', 'αλλάξτε γλώσσα',
        'στα ελληνικά', 'ελληνικά παρακαλώ', 'μπορείτε ελληνικά',
        
        # Hebräisch
        'שפה שגויה', 'דבר', 'שגיאת שפה', 'שפה שונה', 'החלף שפה',
        'בעברית', 'עברית בבקשה', 'אתה יכול עברית',
        
        # Hindi
        'गलत भाषा', 'बोलें', 'भाषा त्रुटि', 'अलग भाषा', 'भाषा बदलें',
        'हिंदी में', 'हिंदी कृपया', 'क्या आप हिंदी बोल सकते हैं',
        
        # Ungarisch
        'rossz nyelv', 'beszélj', 'nyelvi hiba', 'más nyelv', 'változtass nyelvet',
        'magyarul', 'magyarul kérem', 'tudsz magyarul',
        
        # Indonesisch
        'bahasa salah', 'bicara', 'kesalahan bahasa', 'bahasa berbeda', 'ganti bahasa',
        'dalam bahasa indonesia', 'bahasa indonesia tolong', 'bisakah bahasa indonesia',
        
        # Malaiisch
        'bahasa salah', 'cakap', 'ralat bahasa', 'bahasa lain', 'tukar bahasa',
        'dalam bahasa melayu', 'bahasa melayu tolong', 'bolehkah bahasa melayu',
        
        # Norwegisch
        'feil språk', 'snakk', 'språkfeil', 'annet språk', 'bytt språk',
        'på norsk', 'norsk vær så snill', 'kan du norsk',
        
        # Finnisch
        'väärä kieli', 'puhu', 'kielivirhe', 'eri kieli', 'vaihda kieltä',
        'suomeksi', 'suomeksi kiitos', 'osaatko suomea',
        
        # Thailändisch
        'ภาษาผิด', 'พูด', 'ข้อผิดพลาดภาษา', 'ภาษาอื่น', 'เปลี่ยนภาษา',
        'เป็นภาษาไทย', 'ภาษาไทยโปรด', 'คุณพูดภาษาไทยได้ไหม',
        
        # Vietnamesisch
        'sai ngôn ngữ', 'nói', 'lỗi ngôn ngữ', 'ngôn ngữ khác', 'thay đổi ngôn ngữ',
        'bằng tiếng việt', 'tiếng việt làm ơn', 'bạn có thể tiếng việt',
        
        # Rumänisch
        'limbă greșită', 'vorbește', 'eroare de limbă', 'altă limbă', 'schimbă limba',
        'în română', 'română te rog', 'poți română',
        
        # Katalanisch
        'llengua equivocada', 'parla en', 'error de llengua', 'llengua diferent', 'canviar de llengua',
        'en català', 'català si us plau', 'pots català'
    ])
    
    # BEHANDLUNG VON SPRACHKORREKTUREN
    if is_language_correction:
        # Verwende die Sprache des Users für die Korrekturnachricht
        correction_responses = LANGUAGE_CORRECTION_RESPONSES.get(user_language, LANGUAGE_CORRECTION_RESPONSES['de'])
        correction_response = correction_responses['correction']
        
        formatted_correction = convert_to_html(correction_response)
        await update.message.reply_text(formatted_correction, parse_mode=ParseMode.HTML)
        
        save_chat(user.id, name, user_message, formatted_correction)
        
        admin_msg = format_admin_message(
            name, user.id, user_language, user_message, formatted_correction
        )
        await context.bot.send_message(
            chat_id=context.bot_data['ADMIN_CHAT_ID'], 
            text=admin_msg, 
            parse_mode=ParseMode.HTML
        )
        return
    
    # ERKENNUNG VON SPRACHPRÄFERENZ-ANTWORTEN
    is_language_preference = any(word in user_message_lower for word in [
        # Deutsch
        'deutsch', 'german', 'allemand', 'alemán', 'tedesco', 'almanca', 'немецкий', 'niemiecki',
        'німецька', '德语', 'ドイツ語', '독일어', 'alemão', 'duits', 'tyska', 'tysk',
        'němčina', 'njemački', 'немски', 'জার্মান', 'γερμανικά', 'גרמנית', 'जर्मन',
        'német', 'jerman', 'bahasa jerman', 'tysk', 'saksa', 'ภาษาเยอรมัน', 'tiếng đức',
        'germană', 'alemany',
        
        # Englisch
        'englisch', 'english', 'anglais', 'inglés', 'inglese', 'ingilizce', 'английский',
        'angielski', 'англійська', '英语', '英語', '영어', 'inglês', 'engels', 'engelsk',
        'engleski', 'английски', 'ইংরেজি', 'αγγλικά', 'אנגלית', 'अंग्रेजी', 'angol',
        'bahasa inggris', 'engelsk', 'englanti', 'ภาษาอังกฤษ', 'tiếng anh', 'engleză',
        'anglès',
        
        # Arabisch
        'arabisch', 'arabic', 'arabe', 'árabe', 'arabo', 'arapça', 'арабский', 'arabski',
        'арабська', '阿拉伯语', 'アラビア語', '아랍어', 'árabe', 'arabisch', 'arabiska',
        'arabisk', 'arabština', 'arapski', 'арабски', 'আরবি', 'αραβικά', 'ערבית',
        'अरबी', 'arab', 'bahasa arab', 'arabisk', 'arabia', 'ภาษาอาหรับ', 'tiếng ả rập',
        'arabă', 'àrab', 'عربي', 'عربية',
        
        # Französisch
        'französisch', 'french', 'français', 'francés', 'francese', 'fransızca', 'французский',
        'francuski', 'французька', '法语', 'フランス語', '프랑스어', 'francês', 'frans',
        'franska', 'fransk', 'francouzština', 'francuski', 'френски', 'ফরাসি', 'γαλλικά',
        'צרפתית', 'फ्रेंच', 'francia', 'bahasa perancis', 'fransk', 'ranska', 'ภาษาฝรั่งเศส',
        'tiếng pháp', 'franceză', 'francès',
        
        # Spanisch
        'spanisch', 'spanish', 'español', 'espagnol', 'spagnolo', 'ispanyolca', 'испанский',
        'hiszpański', 'іспанська', '西班牙语', 'スペイン語', '스페인어', 'espanhol', 'spaans',
        'spanska', 'spansk', 'španělština', 'španjolski', 'испански', 'স্প্যানিশ', 'ισπανικά',
        'ספרדית', 'स्पेनिश', 'spanyol', 'bahasa spanyol', 'spansk', 'espanja', 'ภาษาสเปน',
        'tiếng tây ban nha', 'spaniolă', 'espanyol',
        
        # Italienisch
        'italienisch', 'italian', 'italien', 'italiano', 'italyanca', 'итальянский', 'włoski',
        'італійська', '意大利语', 'イタリア語', '이탈리아어', 'italiano', 'italiaans', 'italienska',
        'italiensk', 'italština', 'talijanski', 'италиански', 'ইতালীয়', 'ιταλικά', 'איטלקית',
        'इतालवी', 'olasz', 'bahasa italia', 'italiensk', 'italia', 'ภาษาอิตาลี', 'tiếng ý',
        'italiană', 'italià',
        
        # Türkisch
        'türkisch', 'turkish', 'turc', 'turco', 'turco', 'turečtina', 'турецкий', 'turecki',
        'турецька', '土耳其语', 'トルコ語', '터키어', 'turco', 'turks', 'turkiska', 'tyrkisk',
        'turečtina', 'turski', 'турски', 'তুর্কি', 'τουρκικά', 'טורקית', 'तुर्की', 'török',
        'bahasa turki', 'tyrkisk', 'turkkilainen', 'ภาษาตุรกี', 'tiếng thổ nhĩ kỳ', 'turcă',
        'turc',
        
        # Russisch
        'russisch', 'russian', 'russe', 'ruso', 'russo', 'rusça', 'русский', 'rosyjski',
        'російська', '俄语', 'ロシア語', '러시아어', 'russo', 'russisch', 'ryska', 'russisk',
        'ruština', 'ruski', 'руски', 'রাশিয়ান', 'ρωσικά', 'רוסית', 'रूसी', 'orosz',
        'bahasa rusia', 'russisk', 'venäjä', 'ภาษารัสเซีย', 'tiếng nga', 'rusă', 'rus',
        
        # Polnisch
        'polnisch', 'polish', 'polonais', 'polaco', 'polacco', 'lehçe', 'польский', 'polski',
        'польська', '波兰语', 'ポーランド語', '폴란드어', 'polonês', 'pools', 'polska', 'polsk',
        'polština', 'poljski', 'полски', 'পোলিশ', 'πολωνικά', 'פולנית', 'पोलिश', 'lengyel',
        'bahasa polandia', 'polsk', 'puola', 'ภาษาโปแลนด์', 'tiếng ba lan', 'poloneză', 'polonès',
        
        # Ukrainisch
        'ukrainisch', 'ukrainian', 'ukrainien', 'ucraniano', 'ucraino', 'ukraynaca', 'украинский',
        'ukraiński', 'українська', '乌克兰语', 'ウクライナ語', '우크라이나어', 'ucraniano', 'oekraïens',
        'ukrainska', 'ukrainsk', 'ukrajinština', 'ukrajinski', 'украински', 'ইউক্রেনীয়', 'ουκρανικά',
        'אוקראינית', 'यूक्रेनियन', 'ukrán', 'bahasa ukraina', 'ukrainsk', 'ukraina', 'ภาษายูเครน',
        'tiếng ukraina', 'ucraineană', 'ucraïnès',
        
        # Chinesisch
        'chinesisch', 'chinese', 'chinois', 'chino', 'cinese', 'çince', 'китайский', 'chiński',
        'китайська', '中文', '中国語', '중국어', 'chinês', 'chinees', 'kinesiska', 'kinesisk',
        'čínština', 'kineski', 'китайски', 'চীনা', 'κινεζικά', 'סינית', 'चीनी', 'kínai',
        'bahasa cina', 'kinesisk', 'kiina', 'ภาษาจีน', 'tiếng trung', 'chineză', 'xinès',
        
        # Japanisch
        'japanisch', 'japanese', 'japonais', 'japonés', 'giapponese', 'japonca', 'японский',
        'japoński', 'японська', '日语', '日本語', '일본어', 'japonês', 'japans', 'japanska',
        'japansk', 'japonština', 'japanski', 'японски', 'জাপানি', 'ιαπωνικά', 'יפנית', 'जापानी',
        'japán', 'bahasa jepang', 'japansk', 'japani', 'ภาษาญี่ปุ่น', 'tiếng nhật', 'japoneză',
        'japonès',
        
        # Koreanisch
        'koreanisch', 'korean', 'coréen', 'coreano', 'coreano', 'korece', 'корейский', 'koreański',
        'корейська', '韩语', '韓国語', '한국어', 'coreano', 'koreaans', 'koreanska', 'koreansk',
        'korejština', 'korejski', 'корейски', 'কোরিয়ান', 'κορεατικά', 'קוריאנית', 'कोरियाई',
        'koreai', 'bahasa korea', 'koreansk', 'korea', 'ภาษาเกาหลี', 'tiếng hàn', 'coreeană',
        'coreà',
        
        # Portugiesisch
        'portugiesisch', 'portuguese', 'portugais', 'portugués', 'portoghese', 'portekizce',
        'португальский', 'portugalski', 'португальська', '葡萄牙语', 'ポルトガル語', '포르투갈어',
        'português', 'portugees', 'portugisiska', 'portugisisk', 'portugalština', 'portugalski',
        'португалски', 'পর্তুগীজ', 'πορτογαλικά', 'פורטוגזית', 'पुर्तगाली', 'portugál',
        'bahasa portugis', 'portugisisk', 'portugali', 'ภาษาโปรตุเกส', 'tiếng bồ đào nha',
        'portugheză', 'portuguès',
        
        # Niederländisch
        'niederländisch', 'dutch', 'néerlandais', 'neerlandés', 'olandese', 'felemenkçe',
        'нидерландский', 'niderlandzki', 'нідерландська', '荷兰语', 'オランダ語', '네덜란드어',
        'holandês', 'nederlands', 'holländska', 'hollandsk', 'nizozemština', 'nizozemski',
        'холандски', 'ওলন্দাজ', 'ολλανδικά', 'הולנדית', 'डच', 'holland', 'bahasa belanda',
        'nederlandsk', 'hollanti', 'ภาษาดัตช์', 'tiếng hà lan', 'olandeză', 'neerlandès',
        
        # Schwedisch
        'schwedisch', 'swedish', 'suédois', 'sueco', 'svedese', 'isveççe', 'шведский', 'szwedzki',
        'шведська', '瑞典语', 'スウェーデン語', '스웨덴어', 'sueco', 'zweeds', 'svenska', 'svensk',
        'švédština', 'švedski', 'шведски', 'সুইডিশ', 'σουηδικά', 'שוודית', 'स्वीडिश', 'svéd',
        'bahasa swedia', 'svensk', 'ruotsi', 'ภาษาสวีเดน', 'tiếng thụy điển', 'suedeză', 'suec',
        
        # Dänisch
        'dänisch', 'danish', 'danois', 'danés', 'danese', 'danimarkaca', 'датский', 'duński',
        'датська', '丹麦语', 'デンマーク語', '덴마크어', 'dinamarquês', 'deens', 'danska', 'dansk',
        'dánština', 'danski', 'датски', 'ডেনীয়', 'δανικά', 'דנית', 'डेनिश', 'dán', 'bahasa denmark',
        'dansk', 'tanska', 'ภาษาเดนมาร์ก', 'tiếng đan mạch', 'daneză', 'danès',
        
        # Tschechisch
        'tschechisch', 'czech', 'tchèque', 'checo', 'ceco', 'çekçe', 'чешский', 'czeski',
        'чеська', '捷克语', 'チェコ語', '체코어', 'tcheco', 'tsjechisch', 'tjeckiska', 'tjekkisk',
        'čeština', 'češki', 'чешки', 'চেক', 'τσεχικά', 'צ\'כית', 'चेक', 'cseh', 'bahasa ceko',
        'tsjekkisk', 'tšekki', 'ภาษาเช็ก', 'tiếng séc', 'cehă', 'txec',
        
        # Kroatisch
        'kroatisch', 'croatian', 'croate', 'croata', 'croato', 'hırvatça', 'хорватский', 'chorwacki',
        'хорватська', '克罗地亚语', 'クロアチア語', '크로아티아어', 'croata', 'kroatisch', 'kroatiska',
        'kroatisk', 'chorvatština', 'hrvatski', 'хърватски', 'ক্রোয়েশীয়', 'κροατικά', 'קרואטית',
        'क्रोएशियाई', 'horvát', 'bahasa kroasia', 'kroatisk', 'kroatia', 'ภาษาโครเอเชีย', 'tiếng croatia',
        'croată', 'croat',
        
        # Bulgarisch
        'bulgarisch', 'bulgarian', 'bulgare', 'búlgaro', 'bulgaro', 'bulgarca', 'болгарский', 'bułgarski',
        'болгарська', '保加利亚语', 'ブルガリア語', '불가리아어', 'búlgaro', 'bulgaars', 'bulgariska',
        'bulgarsk', 'bulharština', 'bugarski', 'български', 'বুলগেরীয়', 'βουλγαρικά', 'בולגרית',
        'बल्गेरियाई', 'bolgár', 'bahasa bulgaria', 'bulgarsk', 'bulgaria', 'ภาษาบัลแกเรีย', 'tiếng bulgaria',
        'bulgară', 'búlgar',
        
        # Bengalisch
        'bengalisch', 'bengali', 'bengali', 'bengalí', 'bengalese', 'bengalce', 'бенгальский', 'bengalski',
        'бенгальська', '孟加拉语', 'ベンガル語', '벵골어', 'bengali', 'bengaals', 'bengaliska', 'bengalsk',
        'bengálština', 'bengalski', 'бенгалски', 'বাংলা', 'βεγγαλικά', 'בנגלית', 'बंगाली', 'bengáli',
        'bahasa bengali', 'bengalsk', 'bengali', 'ภาษาเบงกาลี', 'tiếng bengal', 'bengaleză', 'bengalí',
        
        # Griechisch
        'griechisch', 'greek', 'grec', 'griego', 'greco', 'yunanca', 'греческий', 'grecki',
        'грецька', '希腊语', 'ギリシャ語', '그리스어', 'grego', 'grieks', 'grekiska', 'græsk',
        'řečtina', 'grčki', 'гръцки', 'গ্রিক', 'ελληνικά', 'יוונית', 'यूनानी', 'görög',
        'bahasa yunani', 'gresk', 'kreikka', 'ภาษากรีก', 'tiếng hy lạp', 'greacă', 'grec',
        
        # Hebräisch
        'hebräisch', 'hebrew', 'hébreu', 'hebreo', 'ebraico', 'ibranice', 'иврит', 'hebrajski',
        'іврит', '希伯来语', 'ヘブライ語', '히브리어', 'hebraico', 'hebreeuws', 'hebreiska', 'hebraisk',
        'hebrejština', 'hebrejski', 'еврейски', 'হিব্রু', 'εβραϊκά', 'עברית', 'हिब्रू', 'héber',
        'bahasa ibrani', 'hebraisk', 'heprea', 'ภาษาฮิบรู', 'tiếng do thái', 'ebraică', 'hebreu',
        
        # Hindi
        'hindi', 'hindi', 'hindi', 'hindi', 'hindi', 'hintçe', 'хинди', 'hindi',
        'хінді', '印地语', 'ヒンディー語', '힌디어', 'hindi', 'hindi', 'hindi', 'hindi',
        'hindština', 'hindski', 'хинди', 'হিন্দি', 'χίντι', 'הינדי', 'हिन्दी', 'hindi',
        'bahasa hindi', 'hindi', 'hindi', 'ภาษาฮินดี', 'tiếng hindi', 'hindus', 'hindi',
        
        # Ungarisch
        'ungarisch', 'hungarian', 'hongrois', 'húngaro', 'ungherese', 'macarca', 'венгерский', 'węgierski',
        'угорська', '匈牙利语', 'ハンガリー語', '헝가리어', 'húngaro', 'hongaars', 'ungerska', 'ungarsk',
        'maďarština', 'mađarski', 'унгарски', 'হাঙ্গেরীয়', 'ουγγρικά', 'הונגרית', 'हंगेरियाई', 'magyar',
        'bahasa hungaria', 'ungarsk', 'unkari', 'ภาษาฮังการี', 'tiếng hungary', 'maghiară', 'hongarès',
        
        # Indonesisch
        'indonesisch', 'indonesian', 'indonésien', 'indonesio', 'indonesiano', 'endonezce', 'индонезийский',
        'indonezyjski', 'індонезійська', '印度尼西亚语', 'インドネシア語', '인도네시아어', 'indonésio',
        'indonesisch', 'indonesiska', 'indonesisk', 'indonéština', 'indonezijski', 'индонезийски', 'ইন্দোনেশীয়',
        'ινδονησιακά', 'אינדונזית', 'इंडोनेशियाई', 'indonéz', 'bahasa indonesia', 'indonesisk', 'indonesia',
        'ภาษาอินโดนีเซีย', 'tiếng indonesia', 'indoneziană', 'indonesi',
        
        # Malaiisch
        'malaiisch', 'malay', 'malais', 'malayo', 'malese', 'malayca', 'малайский', 'malajski',
        'малайська', '马来语', 'マレー語', '말레이어', 'malaio', 'maleis', 'malajiska', 'malajisk',
        'malajština', 'malajski', 'малайски', 'মালয়', 'μαλαισιανά', 'מלאית', 'मलय', 'maláj',
        'bahasa melayu', 'malayisk', 'malaiji', 'ภาษามลายู', 'tiếng malaysia', 'malaeză', 'malai',
        
        # Norwegisch
        'norwegisch', 'norwegian', 'norvégien', 'noruego', 'norvegese', 'norveççe', 'норвежский', 'norweski',
        'норвезька', '挪威语', 'ノルウェー語', '노르웨이어', 'norueguês', 'noors', 'norska', 'norsk',
        'norština', 'norveški', 'норвежки', 'নরওয়েজীয়', 'νορβηγικά', 'נורווגית', 'नॉर्वेजियन', 'norvég',
        'bahasa norwegia', 'norsk', 'norja', 'ภาษานอร์เวย์', 'tiếng na uy', 'norvegiană', 'noruec',
        
        # Finnisch
        'finnisch', 'finnish', 'finnois', 'finés', 'finlandese', 'fince', 'финский', 'fiński',
        'фінська', '芬兰语', 'フィンランド語', '핀란드어', 'finlandês', 'fins', 'finska', 'finsk',
        'finština', 'finski', 'фински', 'ফিনীয়', 'φινλανδικά', 'פינית', 'फिनिश', 'finn',
        'bahasa finlandia', 'finsk', 'suomi', 'ภาษาฟินแลนด์', 'tiếng phần lan', 'finlandeză', 'finès',
        
        # Thailändisch
        'thailändisch', 'thai', 'thaï', 'tailandés', 'thailandese', 'tayca', 'тайский', 'tajski',
        'тайська', '泰语', 'タイ語', '태국어', 'tailandês', 'thais', 'thailändska', 'thailandsk',
        'thajština', 'tajlandski', 'тайландски', 'থাই', 'ταϊλανδικά', 'תאילנדית', 'थाई', 'thai',
        'bahasa thai', 'thai', 'thai', 'ภาษาไทย', 'tiếng thái', 'thailandeză', 'tailandès',
        
        # Vietnamesisch
        'vietnamesisch', 'vietnamese', 'vietnamien', 'vietnamita', 'vietnamita', 'vietnamca', 'вьетнамский',
        'wietnamski', 'в\'єтнамська', '越南语', 'ベトナム語', '베트남어', 'vietnamita', 'vietnamees',
        'vietnamesiska', 'vietnamesisk', 'vietnamština', 'vijetnamski', 'виетнамски', 'ভিয়েতনামী', 'βιετναμεζικά',
        'וייטנאמית', 'वियतनामी', 'vietnami', 'bahasa vietnam', 'vietnamesisk', 'vietnam', 'ภาษาเวียดนาม',
        'tiếng việt', 'vietnameză', 'vietnamita',
        
        # Rumänisch
        'rumänisch', 'romanian', 'roumain', 'rumano', 'rumeno', 'romence', 'румынский', 'rumuński',
        'румунська', '罗马尼亚语', 'ルーマニア語', '루마니아어', 'romeno', 'roemeens', 'rumänska', 'rumænsk',
        'rumunština', 'rumunjski', 'румънски', 'রোমানীয়', 'ρουμανικά', 'רומנית', 'रोमानियाई', 'román',
        'bahasa rumania', 'rumensk', 'romania', 'ภาษาโรมาเนีย', 'tiếng romania', 'română', 'romanès',
        
        # Katalanisch
        'katalanisch', 'catalan', 'catalan', 'catalán', 'catalano', 'katalanca', 'каталонский', 'kataloński',
        'каталонська', '加泰罗尼亚语', 'カタロニア語', '카탈로니아어', 'catalão', 'catalaans', 'katalanska',
        'catalansk', 'katalánština', 'katalonski', 'каталонски', 'কাতালান', 'καταλανικά', 'קטלאנית', 'katalán',
        'bahasa katalan', 'katalansk', 'katalaani', 'ภาษาคาตาลัน', 'tiếng catalan', 'catalană', 'català'
    ])

    # BEHANDLUNG VON SPRACHPRÄFERENZEN
    preferred_language = None
    language_map = {
        'Deutsch': ['deutsch', 'german', 'allemand', 'alemán', 'tedesco', 'almanca', 'немецкий', 'niemiecki', 'німецька', '德语', 'ドイツ語', '독일어'],
        'Englisch': ['englisch', 'english', 'anglais', 'inglés', 'inglese', 'ingilizce', 'английский', 'angielski', 'англійська', '英语', '英語', '영어'],
        'Arabisch': ['arabisch', 'arabic', 'arabe', 'árabe', 'arabo', 'arapça', 'арабский', 'arabski', 'арабська', '阿拉伯语', 'アラビア語', '아랍어'],
        'Französisch': ['französisch', 'french', 'français', 'francés', 'francese', 'fransızca'],
        'Spanisch': ['spanisch', 'spanish', 'español', 'espagnol', 'spagnolo', 'ispanyolca'],
        'Italienisch': ['italienisch', 'italian', 'italien', 'italiano', 'italyanca'],
        'Türkisch': ['türkisch', 'turkish', 'turc', 'turco', 'turečtina'],
        'Russisch': ['russisch', 'russian', 'russe', 'ruso', 'русский', 'rosyjski'],
        'Polnisch': ['polnisch', 'polish', 'polonais'],
        'Ukrainisch': ['ukrainisch', 'ukrainian', 'ukrainien', 'ucraniano', 'ucraino', 'ukraynaca', 'украинский', 'ukraiński', 'українська'],
        'Chinesisch': ['chinesisch', 'chinese', 'chinois', 'chino', 'cinese', 'çince', 'китайский', 'chiński', '中文', '中国語'],
        'Japanisch': ['japanisch', 'japanese', 'japonais', 'japonés', 'giapponese', 'japonca', 'японский', '日语', '日本語'],
        'Koreanisch': ['koreanisch', 'korean', 'coréen', 'coreano', 'korece', 'корейский', '韩语', '한국어'],
        'Portugiesisch': ['portugiesisch', 'portuguese', 'portugais', 'portugués', 'portoghese', 'portekizce', 'португальский'],
        'Niederländisch': ['niederländisch', 'dutch', 'néerlandais', 'neerlandés', 'olandese', 'felemenkçe', 'нидерландский'],
        'Schwedisch': ['schwedisch', 'swedish', 'suédois', 'sueco', 'svedese', 'isveççe', 'шведский'],
        'Dänisch': ['dänisch', 'danish', 'danois', 'danés', 'danese', 'danimarkaca', 'датский'],
        'Tschechisch': ['tschechisch', 'czech', 'tchèque', 'checo', 'ceco', 'çekçe', 'чешский'],
        'Kroatisch': ['kroatisch', 'croatian', 'croate', 'croata', 'croato', 'hırvatça', 'хорватский'],
        'Bulgarisch': ['bulgarisch', 'bulgarian', 'bulgare', 'búlgaro', 'bulgaro', 'bulgarca', 'болгарский'],
        'Bengalisch': ['bengalisch', 'bengali', 'বাঙালি', 'বঙ্গালি', 'বাংলা'],
        'Griechisch': ['griechisch', 'greek', 'grec', 'griego', 'greco', 'yunanca', 'греческий'],
        'Hebräisch': ['hebräisch', 'hebrew', 'hébreu', 'hebreo', 'ebraico', 'иврит', 'עברית'],
        'Hindi': ['hindi', 'हिन्दी', 'हिंदी', 'हिंदी में', 'hindus', 'हिंदी'],
        'Ungarisch': ['ungarisch', 'hungarian', 'hongrois', 'húngaro', 'ungherese', 'macarca', 'венгерский'],
        'Indonesisch': ['indonesisch', 'indonesian', 'indonésien', 'indonesio', 'indonesiano', 'endonezce'],
        'Malaiisch': ['malaiisch', 'malay', 'malais', 'malayo', 'malese', 'malayca', 'малайский'],
        'Norwegisch': ['norwegisch', 'norwegian', 'norvégien', 'noruego', 'norvegese', 'norveççe', 'норвежский'],
        'Finnisch': ['finnisch', 'finnish', 'finnois', 'finés', 'finlandese', 'fince', 'финский'],
        'Thailändisch': ['thailändisch', 'thai', 'thaï', 'tailandés', 'thailandese', 'tayca', 'тайский'],
        'Vietnamesisch': ['vietnamesisch', 'vietnamese', 'vietnamien', 'vietnamita', 'vietnamca'],
        'Rumänisch': ['rumänisch', 'romanian', 'roumain', 'rumano', 'rumeno', 'romence'],
        'Katalanisch': ['katalanisch', 'catalan', 'catalán', 'catalano', 'katalanca', 'каталонский']
    }


    for lang, keywords in language_map.items():
        if any(word in user_message_lower for word in keywords):
            preferred_language = lang
            break    
        


    if preferred_language:
        update_user_preferred_language(user.id, preferred_language)
        user_language = preferred_language


        confirmation_responses = LANGUAGE_CORRECTION_RESPONSES.get(user_language, LANGUAGE_CORRECTION_RESPONSES['de'])
        confirmation_response = confirmation_responses['confirmed'].format(language=preferred_language)


        formatted_confirmation = convert_to_html(confirmation_response)
        await update.message.reply_text(formatted_confirmation, parse_mode=ParseMode.HTML)


        save_chat(user.id, name, user_message, formatted_confirmation)


        admin_msg = format_admin_message(
            name, user.id, user_language, user_message, formatted_confirmation
        )
        await context.bot.send_message(
            chat_id=context.bot_data['ADMIN_CHAT_ID'],
            text=admin_msg,
            parse_mode=ParseMode.HTML
        )
        return

    
    # ERKENNUNG VON BESCHWERDEN, DATENSCHUTZBEDENKEN UND ENTWICKLER-FRAGEN
    is_complaint = any(word in user_message_lower for word in ['beschwerde', 'problem', 'unzufrieden', 'reklamation', 'ärger', 'schlecht', 'fehler', 'falsch'])
    is_privacy_concern = any(word in user_message_lower for word in ['datenschutz', 'daten', 'privacy', 'sicherheit', 'speichern', 'weitergabe', 'dritter'])
    is_developer_question = any(word in user_message_lower for word in ['entwickler', 'programmierer', 'ersteller', 'wer hat dich gemacht', 'wer hat dich entwickelt', 'mhd', 'fouaad', 'alkamsha'])
    
    # BEHANDLUNG VON ENTWICKLER-FRAGEN (auch in normalen Nachrichten)
    if is_developer_question:
        developer_info = DEVELOPER_INFO.get(user_language, DEVELOPER_INFO['de'])
        bot_reply = developer_info['description']
        bot_reply = clean_telegram_html(bot_reply)
        
        await update.message.reply_text(bot_reply, parse_mode=ParseMode.HTML)
        save_chat(user.id, name, user_message, bot_reply)
        
        admin_msg = format_admin_message(
            name, user.id, user_language, user_message, bot_reply
        )
        await context.bot.send_message(
            chat_id=context.bot_data['ADMIN_CHAT_ID'], 
            text=admin_msg, 
            parse_mode=ParseMode.HTML
        )
        return
    
    # BEHANDLUNG VON BESCHWERDEN
    if is_complaint:
        complaint_info = handle_complaint(user_message, user_language)
        bot_reply = complaint_info['response']
        bot_reply = clean_telegram_html(bot_reply)
        
        await update.message.reply_text(bot_reply, parse_mode=ParseMode.HTML)
        save_chat(user.id, name, user_message, bot_reply)
        
        admin_msg = format_admin_message(
            name, user.id, user_language, user_message, bot_reply
        )
        await context.bot.send_message(
            chat_id=context.bot_data['ADMIN_CHAT_ID'], 
            text=admin_msg, 
            parse_mode=ParseMode.HTML
        )
        return
    
    # BEHANDLUNG VON DATENSCHUTZBEDENKEN
    if is_privacy_concern:
        privacy_info = handle_complaint(user_message, user_language)
        bot_reply = privacy_info['datenschutz']
        bot_reply = clean_telegram_html(bot_reply)
        
        await update.message.reply_text(bot_reply, parse_mode=ParseMode.HTML)
        save_chat(user.id, name, user_message, bot_reply)
        
        admin_msg = format_admin_message(
            name, user.id, user_language, user_message, bot_reply
        )
        await context.bot.send_message(
            chat_id=context.bot_data['ADMIN_CHAT_ID'], 
            text=admin_msg, 
            parse_mode=ParseMode.HTML
        )
        return
    
    # NORMALE CHAT-BEARBEITUNG
    try:
        prompt = create_prompt(user.id, name, user_message, current_time, user_language)
        response = context.bot_data['model'].generate_content(prompt)
        bot_reply = response.text.strip()
        
        # SICHERE HTML-BEREINIGUNG
        bot_reply = clean_telegram_html(bot_reply)
        
        # Extrahiere Projekt-Details
        project_details = extract_project_details(user_message)
        has_sufficient_data = any(key in project_details for key in ['umzug_zimmer', 'maler_flaeche', 'reinigung_flaeche'])
        
        # Wenn ausreichend Daten vorhanden sind, füge Preisberechnung hinzu
        if has_sufficient_data and any(word in user_message_lower for word in ['preis', 'kosten', 'wie viel', 'angebot', 'price', 'cost', 'كم', 'combien', 'cuesta']):
            price_estimate = generate_price_estimate(project_details, user_language)
            bot_reply = price_estimate
        
        update_user_conversation_summary(user.id, f"{user_message} -> {bot_reply}")
        
    except Exception as e:
        print(f"Fehler bei der AI-Generierung für User {user.id}: {e}")
        error_messages = {
            'Deutsch': "❌ <b>Entschuldigung, technische Schwierigkeiten</b>\n\n"
                      "📞 <b>Bitte kontaktieren Sie uns direkt:</b>\n"
                      "📍 Wörther Straße 32, 13595 Berlin\n"
                      "📱 +49 176 72407732\n"
                      "✉️ shawo.info.betrieb@gmail.com",
            'Englisch': "❌ <b>Sorry, technical difficulties</b>\n\n"
                       "📞 <b>Please contact us directly:</b>\n"
                       "📍 Wörther Straße 32, 13595 Berlin\n"
                       "📱 +49 176 72407732\n"
                       "✉️ shawo.info.betrieb@gmail.com",
            'Arabisch': "❌ <b>عذرًا، هناك صعوبات تقنية</b>\n\n"
                       "📞 <b>يرجى الاتصال بنا مباشرة:</b>\n"
                       "📍 Wörther Straße 32, 13595 Berlin\n"
                       "📱 +49 176 72407732\n"
                       "✉️ shawo.info.betrieb@gmail.com"
        }
        bot_reply = error_messages.get(user_language, error_messages['Deutsch'])
        bot_reply = clean_telegram_html(bot_reply)

    # Sende die komplette Antwort an den User
    await update.message.reply_text(bot_reply, parse_mode=ParseMode.HTML)
    save_chat(user.id, name, user_message, bot_reply)
    
    # Sende die KOMPLETTE Antwort an den Admin mit HTML-Formatierung
    admin_msg = format_admin_message(
        name, user.id, user_language, user_message, bot_reply
    )
    await context.bot.send_message(
        chat_id=context.bot_data['ADMIN_CHAT_ID'], 
        text=admin_msg, 
        parse_mode=ParseMode.HTML
    )

def extract_booking_info(text: str) -> dict:
    """Extrahiert Buchungsinformationen aus dem Text"""
    info = {
        'name': '',
        'contact': '',
        'service': ''
    }
    
    # Versuche Namen zu extrahieren
    name_patterns = [
        r'(?:name|ich heiße|mein name ist|اسمي|my name is)\s*[:]?\s*([^\n,.!?]+)',
        r'([A-Z][a-z]+ [A-Z][a-z]+)'  # Vorname Nachname Pattern
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info['name'] = match.group(1).strip()
            break
    
    # Versuche Telefonnummer zu extrahieren
    phone_patterns = [
        r'(\+?[0-9]{8,15})',
        r'(?:tel|telefon|phone|هاتف|رقم)\s*[:]?\s*([^\n,.!?]+)'
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info['contact'] = match.group(1).strip()
            break
    
    # Versuche Service zu identifizieren
    services = ['umzug', 'maler', 'reinigung', 'painting', 'move', 'cleaning', 'نقل', 'دهان', 'تنظيف']
    for service in services:
        if service in text.lower():
            info['service'] = service
            break
    
    # Falls kein Service gefunden, verwende ersten Satz als Service-Beschreibung
    if not info['service']:
        first_sentence = text.split('.')[0]
        if len(first_sentence) > 10:
            info['service'] = first_sentence[:50] + "..." if len(first_sentence) > 50 else first_sentence
    
    return info

# 🔄 FUNKTION: Startet den Bot mit Parametern
def start_bot(TOKEN, ADMIN_CHAT_ID, model):
    """Startet den Bot mit den gegebenen Parametern"""
    
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Bot-Daten für spätere Verwendung speichern
    app.bot_data['ADMIN_CHAT_ID'] = ADMIN_CHAT_ID
    app.bot_data['model'] = model
    app.bot_data['ADMIN_USER_ID'] = "7398559788"  # Ersetzen Sie dies mit Ihrer tatsächlichen User ID
    
    # Befehle hinzufügen
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("contact", contact_command))
    app.add_handler(CommandHandler("services", services_command))
    app.add_handler(CommandHandler("prices", prices_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("entwickler", developer_command))
    
    # Kalender-Befehle hinzufügen
    app.add_handler(CommandHandler("calendar", calendar_command))
    app.add_handler(CommandHandler("book", book_command))
    app.add_handler(CommandHandler("block", block_command))
    app.add_handler(CommandHandler("unblock", unblock_command))
    app.add_handler(CommandHandler("blocked", blocked_command))
    app.add_handler(CommandHandler("export", export_command))
    app.add_handler(CommandHandler("cancel", admin_cancel_command))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    print("Admin Chat ID:", ADMIN_CHAT_ID)
    print(f"👤 Admin User ID: {app.bot_data['ADMIN_USER_ID']}")
    print("Gestartet um:", datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
    print("🤖 SHAWO Bot mit PROFESSIONELLER KALENDER-FUNKTION gestartet!")
    print("📊 Verfügbare Services:", list(PRICE_DATABASE.keys()))
    print("🛡️  Beschwerde-Management: AKTIVIERT")
    print("🌍 AUTOMATISCHE Spracherkennung: TELEGRAM SYSTEM + TEXT ANALYSE")
    print("🎨 Präzise Preisunterscheidung: AKTIVIERT")
    print("👨‍💻 Entwickler-Info Befehl: AKTIVIERT")
    print("🔧 VERBESSERTE Sprachkorrektur-Erkennung: AKTIVIERT")
    print("💰 Mehrsprachige Preisbeispiele: KORRIGIERT")
    print("🚀 PROFESSIONELLE Fehlerbehandlung: IMPLEMENTIERT")
    print("📅 KALENDER-SYSTEM: VOLLSTÄNDIG INTEGRIERT")
    print("   - Terminbuchung mit /book")
    print("   - Kalender-Ansicht mit /calendar") 
    print("   - Tag blockieren mit /block (Admin)")
    print("   - Export mit /export (Admin)")
    print("🔓 NEUE BEFEHLE: /unblock und /blocked und /cancel verfügbar! (Admin)")
    
    app.run_polling()

# 🔄 HAUPTPUNKT
if __name__ == "__main__":
    bot = SecureBot()

    bot.run()
