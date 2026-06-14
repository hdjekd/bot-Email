#!/usr/bin/env python3
# MR_Email_Bot_Ultimate.py
# بوت MR Email - بريد مؤقت خارق (مخفي المصادر بالكامل) مع نظام تسجيل ومراقبة وحماية

import logging
import sqlite3
import random
import string
import requests
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import contextmanager
import os
import threading
import time
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS

from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# ================= إعداد Flask للمراقبة =================
monitor_app = Flask(__name__)
CORS(monitor_app)

# متغيرات حالة البوت
BOT_STATUS = {
    "running": True,
    "start_time": datetime.now(),
    "total_users": 0,
    "total_emails": 0,
    "total_messages": 0,
    "last_activity": None,
    "api_status": {
        "api_1": "checking",
        "api_2": "checking"
    }
}

# ================= إعدادات المطور =================
DEV_ID = 8311254462  # معرف المطور @MR_Tails_YE

# كاش للدومينات (تحسين الأداء)
_cached_domains = None

# ================= قالب HTML للوحة التحكم (مخفي المصادر) =================
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MR Email Bot - لوحة المراقبة</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { 
            font-size: 2.5em; 
            margin-bottom: 10px; 
            text-shadow: 0 0 10px #667eea, 0 0 20px #764ba2;
        }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .status-card {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .status-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 50px;
            font-weight: bold;
            margin-bottom: 15px;
        }
        .status-online { background: #10b981; color: white; box-shadow: 0 0 10px #10b981; }
        .status-offline { background: #ef4444; color: white; box-shadow: 0 0 10px #ef4444; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            transition: transform 0.3s;
        }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-number { font-size: 2.5em; font-weight: bold; margin-bottom: 10px; }
        .stat-label { font-size: 0.9em; opacity: 0.9; }
        .info-card {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .info-card h3 { margin-bottom: 15px; color: #333; border-right: 4px solid #667eea; padding-right: 10px; }
        .info-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
        }
        .info-label { font-weight: bold; color: #666; }
        .info-value { color: #333; font-family: monospace; }
        .refresh-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 50px;
            cursor: pointer;
            font-size: 1em;
            margin-top: 20px;
            transition: transform 0.3s;
        }
        .refresh-btn:hover { transform: scale(1.05); }
        .footer { text-align: center; color: white; margin-top: 30px; opacity: 0.7; }
        .api-status {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-top: 15px;
        }
        .api-item {
            flex: 1;
            background: #f3f4f6;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .api-name { font-weight: bold; margin-bottom: 10px; color: #333; }
        .api-working { color: #10b981; font-weight: bold; }
        .api-error { color: #ef4444; font-weight: bold; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .loading { animation: pulse 1.5s infinite; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ MR EMAIL BOT ⚡</h1>
            <p>نظام المراقبة المتقدم - بريد مؤقت احترافي</p>
        </div>
        
        <div class="status-card">
            <div id="statusBadge" class="status-badge status-online">🟢 البوت يعمل</div>
            <div id="uptime">⏱️ وقت التشغيل: جاري التحميل...</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="totalUsers">0</div>
                <div class="stat-label">👥 المستخدمين</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="totalEmails">0</div>
                <div class="stat-label">📧 البريد الإلكتروني</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="totalMessages">0</div>
                <div class="stat-label">💬 الرسائل</div>
            </div>
        </div>
        
        <div class="info-card">
            <h3>📊 معلومات البوت</h3>
            <div class="info-item">
                <span class="info-label">🤖 اسم البوت:</span>
                <span class="info-value">@MR_Email_Bot</span>
            </div>
            <div class="info-item">
                <span class="info-label">👨‍💻 المطور:</span>
                <span class="info-value">@MR_Tails_YE</span>
            </div>
            <div class="info-item">
                <span class="info-label">🌍 الدومينات المدعومة:</span>
                <span class="info-value" id="domainsCount">-</span>
            </div>
            <div class="info-item">
                <span class="info-label">🕐 آخر تحديث:</span>
                <span class="info-value" id="lastUpdate">-</span>
            </div>
        </div>
        
        <div class="info-card">
            <h3>🔌 حالة الخوادم</h3>
            <div class="api-status">
                <div class="api-item">
                    <div class="api-name">🖥️ الخادم الأساسي</div>
                    <div id="api1Status">🟡 جاري الفحص...</div>
                </div>
                <div class="api-item">
                    <div class="api-name">🖥️ الخادم الثانوي</div>
                    <div id="api2Status">🟡 جاري الفحص...</div>
                </div>
            </div>
        </div>
        
        <div style="text-align: center;">
            <button class="refresh-btn" onclick="refreshData()">🔄 تحديث البيانات</button>
        </div>
        
        <div class="footer">
            <p>MR EMAIL BOT - بريد مؤقت خارق | تم التطوير بواسطة @MR_Tails_YE</p>
        </div>
    </div>
    
    <script>
        async function refreshData() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                document.getElementById('totalUsers').textContent = data.total_users || 0;
                document.getElementById('totalEmails').textContent = data.total_emails || 0;
                document.getElementById('totalMessages').textContent = data.total_messages || 0;
                document.getElementById('domainsCount').textContent = data.domains_count || 0;
                document.getElementById('uptime').innerHTML = `⏱️ وقت التشغيل: ${data.uptime || '0 ساعة'}`;
                document.getElementById('lastUpdate').textContent = data.last_activity || '-';
                
                const statusBadge = document.getElementById('statusBadge');
                if (data.running) {
                    statusBadge.className = 'status-badge status-online';
                    statusBadge.innerHTML = '🟢 البوت يعمل';
                } else {
                    statusBadge.className = 'status-badge status-offline';
                    statusBadge.innerHTML = '🔴 البوت متوقف';
                }
                
                if (data.api_status) {
                    const api1 = document.getElementById('api1Status');
                    if (data.api_status.api_1 === 'working') {
                        api1.innerHTML = '🟢 يعمل بشكل طبيعي';
                        api1.className = 'api-working';
                    } else {
                        api1.innerHTML = '🔴 لا يعمل حالياً';
                        api1.className = 'api-error';
                    }
                    
                    const api2 = document.getElementById('api2Status');
                    if (data.api_status.api_2 === 'working') {
                        api2.innerHTML = '🟢 يعمل بشكل طبيعي';
                        api2.className = 'api-working';
                    } else {
                        api2.innerHTML = '🔴 لا يعمل حالياً';
                        api2.className = 'api-error';
                    }
                }
            } catch (error) {
                console.error('خطأ:', error);
            }
        }
        
        refreshData();
        setInterval(refreshData, 10000);
    </script>
</body>
</html>
'''

# ================= نقاط نهاية Flask للمراقبة =================
@monitor_app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@monitor_app.route('/health')
def health():
    uptime_seconds = (datetime.now() - BOT_STATUS["start_time"]).total_seconds()
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    
    return jsonify({
        "status": "ok" if BOT_STATUS["running"] else "down",
        "bot": "running" if BOT_STATUS["running"] else "stopped",
        "version": "4.0",
        "timestamp": int(time.time()),
        "uptime": f"{hours}h {minutes}m",
        "stats": {
            "total_users": BOT_STATUS["total_users"],
            "total_emails": BOT_STATUS["total_emails"],
            "total_messages": BOT_STATUS["total_messages"]
        }
    })

@monitor_app.route('/api/status')
def api_status():
    uptime_seconds = (datetime.now() - BOT_STATUS["start_time"]).total_seconds()
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    
    return jsonify({
        "running": BOT_STATUS["running"],
        "uptime": f"{hours} ساعة {minutes} دقيقة",
        "total_users": BOT_STATUS["total_users"],
        "total_emails": BOT_STATUS["total_emails"],
        "total_messages": BOT_STATUS["total_messages"],
        "domains_count": len(get_all_domains()),
        "last_activity": BOT_STATUS["last_activity"].strftime("%Y-%m-%d %H:%M:%S") if BOT_STATUS["last_activity"] else "-",
        "api_status": BOT_STATUS["api_status"]
    })

def run_monitor_server():
    port = int(os.environ.get('MONITOR_PORT', 8080))
    monitor_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def update_bot_stats():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE banned = 0")
            BOT_STATUS["total_users"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM emails")
            BOT_STATUS["total_emails"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM inbox")
            BOT_STATUS["total_messages"] = cursor.fetchone()[0]
    except Exception as e:
        log.error(f"Error updating stats: {e}")

def check_apis_status():
    while True:
        try:
            try:
                r = requests.get("https://tempmail.plus/api/mails", params={"email": "test@mailto.plus", "first_id": 1}, timeout=10)
                BOT_STATUS["api_status"]["api_1"] = "working" if r.status_code == 200 else "error"
            except:
                BOT_STATUS["api_status"]["api_1"] = "down"
            
            try:
                r = requests.get("https://inboxes.com/api/v2/domain", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                BOT_STATUS["api_status"]["api_2"] = "working" if r.status_code == 200 else "error"
            except:
                BOT_STATUS["api_status"]["api_2"] = "down"
        except Exception as e:
            log.error(f"API check error: {e}")
        time.sleep(30)

# ================= إصلاح مشكلة التسجيل (logging) =================
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

# ================= ألوان للبانر =================
R = '\033[91m'
G = '\033[92m'
Y = '\033[93m'
C = '\033[96m'
W = '\033[97m'
RESET = '\033[0m'

# ================= توكن البوت =================
TOKEN = "8513010794:AAH9_FatomlJIIPbCBajnYuRhYy2BcqwBxY"

# ================= جميع الدومينات (27 دومين) =================
SOURCE1_DOMAINS = [
    "mailto.plus", "fexpost.com", "fexbox.org", "mailbok.in.ua",
    "chitthi.in", "fextemp.com", "any.pink", "merepost.com"
]

SOURCE2_STATIC_DOMAINS = [
    "blondmail.com", "chapsmail.com", "clowmail.com", "dropjar.com",
    "fivermail.com", "getairmail.com", "getmule.com", "getnada.com",
    "gimpmail.com", "givmail.com", "guysmail.com", "inboxbear.com",
    "replyloop.com", "robot-mail.com", "spicysoda.com", "tafmail.com",
    "temptami.com", "tupmail.com", "vomoto.com"
]

# ================= دوال API =================
def random_username(length=8, with_numbers=True):
    if with_numbers:
        chars = string.ascii_lowercase + string.digits
    else:
        chars = string.ascii_lowercase
    return ''.join(random.choices(chars, k=length))

SOURCE1_URL = "https://tempmail.plus/api"

def src1_create_email(username: str, domain: str) -> Optional[str]:
    email = f"{username}@{domain}"
    try:
        r = requests.get(f"{SOURCE1_URL}/mails", params={"email": email, "first_id": random.randint(10000000, 99999999)}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if not data.get("err"):
                return email
    except Exception as e:
        log.error(f"SRC1 create error: {e}")
    return None

def src1_get_messages(email: str) -> List[Dict]:
    try:
        r = requests.get(f"{SOURCE1_URL}/mails", params={"email": email, "first_id": random.randint(10000000, 99999999)}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if not data.get("err"):
                return data.get("mail_list", [])
    except:
        pass
    return []

def src1_get_message_content(email: str, mail_id: int) -> Optional[Dict]:
    try:
        r = requests.get(f"{SOURCE1_URL}/mails/{mail_id}", params={"email": email}, timeout=15)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def src1_delete_email(email: str) -> bool:
    try:
        r = requests.delete(f"{SOURCE1_URL}/mails", params={"email": email}, timeout=15)
        return r.status_code == 200
    except:
        return False

SOURCE2_URL = "https://inboxes.com"
SOURCE2_HEADERS = {
    "authority": "inboxes.com",
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "referer": "https://inboxes.com/",
    "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/124.0.0.0 Mobile Safari/537.36",
}

def src2_fetch_domains() -> List[str]:
    try:
        r = requests.get(f"{SOURCE2_URL}/api/v2/domain", headers=SOURCE2_HEADERS, timeout=10)
        if r.status_code == 200:
            domains = r.json().get("domains", [])
            fetched = [d["qdn"] for d in domains]
            if fetched:
                return fetched
    except Exception as e:
        log.error(f"SRC2 fetch domains error: {e}")
    return SOURCE2_STATIC_DOMAINS.copy()

def src2_create_email(username: str, domain: str) -> Optional[str]:
    email = f"{username}@{domain}"
    try:
        r = requests.get(f"{SOURCE2_URL}/api/v2/inbox/{email}", headers=SOURCE2_HEADERS, timeout=10)
        return email if r.status_code == 200 else None
    except Exception as e:
        log.error(f"SRC2 create error: {e}")
    return None

def src2_get_messages(email: str) -> List[Dict]:
    try:
        r = requests.get(f"{SOURCE2_URL}/api/v2/inbox/{email}", headers=SOURCE2_HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json().get("msgs", [])
    except:
        pass
    return []

def src2_get_message_content(uid: str) -> Optional[Dict]:
    try:
        r = requests.get(f"{SOURCE2_URL}/api/v2/message/{uid}", headers=SOURCE2_HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None

def src2_delete_email(email: str) -> bool:
    try:
        requests.delete(f"{SOURCE2_URL}/api/v2/inbox/{email}", headers=SOURCE2_HEADERS, timeout=10)
        return True
    except:
        return False

# ================= الحصول على قائمة الدومينات (مع كاش) =================
def get_all_domains() -> List[str]:
    global _cached_domains
    if _cached_domains is None:
        src2_domains = src2_fetch_domains()
        all_domains = SOURCE1_DOMAINS.copy()
        for d in src2_domains:
            if d not in all_domains:
                all_domains.append(d)
        _cached_domains = all_domains
    return _cached_domains

def get_source_from_domain(domain: str) -> Optional[str]:
    if domain in SOURCE1_DOMAINS:
        return "src1"
    if domain in SOURCE2_STATIC_DOMAINS or domain in src2_fetch_domains():
        return "src2"
    return None

# ================= قاعدة البيانات الرئيسية =================
DB_PATH = "mr_email_bot.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        # جدول المستخدمين مع إضافة حقل banned
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT,
                phone TEXT,
                reg_date TEXT,
                lang TEXT DEFAULT 'en',
                banned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(telegram_id) REFERENCES users(telegram_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                source TEXT NOT NULL,
                from_email TEXT,
                subject TEXT,
                body TEXT,
                uid TEXT,
                mid INTEGER,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

@contextmanager
def db_cursor():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.close()

# ================= دوال المستخدمين والتسجيل =================
def is_user_registered(telegram_id: int) -> bool:
    """التحقق من تسجيل المستخدم وغير محظور"""
    with db_cursor() as cur:
        cur.execute("SELECT telegram_id FROM users WHERE telegram_id = ? AND banned = 0", (telegram_id,))
        return cur.fetchone() is not None

def is_user_banned(telegram_id: int) -> bool:
    """التحقق من حظر المستخدم"""
    with db_cursor() as cur:
        cur.execute("SELECT banned FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        return row is not None and row["banned"] == 1

def register_user(telegram_id: int, name: str, username: str, phone: str, reg_date: str):
    """تسجيل مستخدم جديد - لا يغير حالة الحظر"""
    with db_cursor() as cur:
        # التحقق من وجود المستخدم
        cur.execute("SELECT banned FROM users WHERE telegram_id = ?", (telegram_id,))
        existing = cur.fetchone()
        
        if existing:
            # تحديث البيانات مع الاحتفاظ بحالة الحظر
            cur.execute("""
                UPDATE users 
                SET name = ?, username = ?, phone = ?, reg_date = ?
                WHERE telegram_id = ?
            """, (name, username, phone, reg_date, telegram_id))
        else:
            # إدراج مستخدم جديد (غير محظور)
            cur.execute("""
                INSERT INTO users (telegram_id, name, username, phone, reg_date, banned)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (telegram_id, name, username, phone, reg_date))
    update_bot_stats()

def get_user_data(telegram_id: int) -> Optional[Dict]:
    """جلب بيانات مستخدم"""
    with db_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def get_all_users() -> List[Dict]:
    """جلب جميع المستخدمين"""
    with db_cursor() as cur:
        cur.execute("SELECT telegram_id, name, username, phone, reg_date, banned FROM users ORDER BY reg_date DESC")
        return [dict(row) for row in cur.fetchall()]

def ban_user(telegram_id: int) -> bool:
    """حظر مستخدم"""
    with db_cursor() as cur:
        cur.execute("UPDATE users SET banned = 1 WHERE telegram_id = ?", (telegram_id,))
        return cur.rowcount > 0

def unban_user(telegram_id: int) -> bool:
    """إلغاء حظر مستخدم"""
    with db_cursor() as cur:
        cur.execute("UPDATE users SET banned = 0 WHERE telegram_id = ?", (telegram_id,))
        return cur.rowcount > 0

def get_user_lang(telegram_id: int) -> str:
    with db_cursor() as cur:
        cur.execute("SELECT lang FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        if row:
            return row["lang"]
        return "en"

def set_user_lang(telegram_id: int, lang: str):
    with db_cursor() as cur:
        cur.execute("UPDATE users SET lang = ? WHERE telegram_id = ?", (lang, telegram_id))

def get_user_emails(telegram_id: int) -> List[Dict]:
    with db_cursor() as cur:
        cur.execute("SELECT id, email, source FROM emails WHERE telegram_id = ? ORDER BY created_at DESC", (telegram_id,))
        return [dict(row) for row in cur.fetchall()]

def add_user_email(telegram_id: int, email: str, source: str):
    with db_cursor() as cur:
        cur.execute("INSERT INTO emails (telegram_id, email, source) VALUES (?, ?, ?)", (telegram_id, email, source))
    update_bot_stats()

def remove_user_email(telegram_id: int, email: str):
    with db_cursor() as cur:
        cur.execute("DELETE FROM emails WHERE telegram_id = ? AND email = ?", (telegram_id, email))
    update_bot_stats()

def save_inbox_message(telegram_id: int, email: str, source: str, from_email: str, subject: str, body: str, uid: str = None, mid: int = None):
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO inbox (telegram_id, email, source, from_email, subject, body, uid, mid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (telegram_id, email, source, from_email, subject, body, uid, mid))
    update_bot_stats()

# رسالة الحظر الثابتة (لكل اللغات)
BAN_MESSAGE = """🚫 *لقد تم حظرك من استخدام البوت*

⤏͟͟͞͞༒⃝Ꭲ̴Ꭼ̴Ꭱ̴Ꮇ̴Ꮜ̴᙭̴♛Ꮎ̴Ꮩ̴Ꭼ̴Ꭱ̴Ꮮ̴Ꮎ̴Ꭱ̴Ꭰ̴༒⃟࿗⃝⏤͟͞➤⃟☠︎︎

إذا كنت تعتقد أن هذا خطأ، يرجى التواصل مع المطور:
@MR_Tails_YE"""

# ================= نصوص البوت =================
def get_domains_list_text(uid: int) -> str:
    lang = get_user_lang(uid)
    domains = get_all_domains()
    domains_text = "\n".join([f"• {d}" for d in domains])
    if lang == "ar":
        return f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n✍️ أرسل بريدك المخصص بالصيغة (مثال: `myself@blondmail.com`):\n\n💡 *الدومينات المتاحة:*\n{domains_text}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪"
    else:
        return f"~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n✍️ Send your custom email (e.g., `myself@blondmail.com`):\n\n💡 *Available Domains:*\n{domains_text}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪🇾🇪"

TEXTS = {
    "ar": {
        "welcome": f"✨ مرحباً بك في بوت MR Email!\n⤏͟͟͞͞༒⃝Ꭲ̴Ꭼ̴Ꭱ̴Ꮇ̴Ꮜ̴᙭̴♛Ꮎ̴Ꮩ̴Ꭼ̴Ꭱ̴Ꮮ̴Ꮎ̴Ꭱ̴Ꭰ̴༒⃟࿗⃝⏤͟͞➤⃟☠︎︎\n\nبريد مؤقت خارق يدعم العديد من الدومينات.\nDEV: @MR_Tails_YE",
        "need_phone": "📱 *يرجى تسجيل رقم هاتفك أولاً*\n\nاستخدم الأمر /phone لمشاركة رقم هاتفك والتحقق من حسابك.",
        "banned": BAN_MESSAGE,
        "phone_prompt": "📱 *يرجى مشاركة رقم هاتفك للتحقق من حسابك*\n\nاضغط على الزر أدناه لمشاركة رقم هاتفك.",
        "phone_saved": "✅ *تم حفظ رقم هاتفك بنجاح*\n\nالاسم: {name}\nاليوزر: {username}\nرقم الهاتف: {phone}\nتاريخ التسجيل: {date}\n\n✨ يمكنك الآن استخدام البوت!",
        "no_emails": "⚠️ ليس لديك أي بريد مؤقت بعد. استخدم /generate لإنشاء واحد.",
        "choose_domain": "🌐 *اختر الدومين لإنشاء بريد عشوائي:*",
        "choose_type": "🔢 *اختر نوع اسم البريد:*",
        "type_with_numbers": "🔢 مع أرقام (مثال: a1b2c3d4)",
        "type_without_numbers": "🔤 بدون أرقام (أحرف فقط)",
        "generate_success": "✅ *تم إنشاء بريد جديد:*\n`{email}`",
        "generate_fail": "❌ فشل إنشاء البريد، حاول مرة أخرى.",
        "emails_list": "📋 *قائمة بريدك الإلكتروني:*",
        "fetch_select": "🔍 *اختر البريد لجلب رسائله:*",
        "delete_select": "🗑️ *اختر البريد لحذفه:*",
        "inbox_empty": "📭 لا توجد رسائل لـ `{email}`.",
        "inbox_messages": "📨 *رسائل* `{email}`:\n",
        "view_latest_hint": "\n💡 استخدم /view لعرض تفاصيل آخر رسالة.",
        "no_messages": "📭 لا توجد رسائل.",
        "message_detail": "📄 *تفاصيل الرسالة*\n\n*من:* {from_addr}\n*الموضوع:* {subject}\n\n*النص:*\n{body}",
        "delete_success": "🗑️ تم حذف البريد `{email}`.",
        "delete_fail": "❌ فشل حذف البريد.",
        "custom_success": "✅ *تم إضافة البريد المخصص:*\n`{email}`",
        "custom_invalid": "❌ بريد غير صالح أو دومين غير مدعوم.",
        "domains_list": "🌐 *جميع الدومينات المدعومة:*\n" + "\n".join([f"• `{d}`" for d in get_all_domains()]),
        "lang_changed": "🌐 تم تغيير اللغة إلى العربية.",
        "unknown": "❓ أمر غير معروف. استخدم القائمة الزرقاء.",
        "fetch_button": "📥 جلب",
        "delete_button": "🗑️ حذف",
        "back": "🔙 رجوع",
        "second_message": "✨ بريدك المؤقت الجديد هو: `{email}`\nأرسل /id لرؤية القائمة الكاملة.",
        "not_authorized": "⚠️ *غير مصرح*\n\nهذا الأمر متاح فقط للمطور.",
        "dev_panel": "👑 *لوحة تحكم المطور*\n\nمرحباً أيها المطور العظيم!\n\nاختر أحد الخيارات أدناه:",
        "dev_users_list": "👥 *قائمة المستخدمين*\n\nإجمالي المستخدمين: {total}\n\n{users_list}",
        "dev_no_users": "📭 لا يوجد مستخدمين مسجلين.",
        "dev_ban_prompt": "🚫 *حظر مستخدم*\n\nأرسل معرف المستخدم (ID) الذي تريد حظره:",
        "dev_unban_prompt": "✅ *إلغاء حظر مستخدم*\n\nأرسل معرف المستخدم (ID) الذي تريد إلغاء حظره:",
        "dev_ban_success": "✅ تم حظر المستخدم `{user_id}` بنجاح.",
        "dev_ban_fail": "❌ فشل حظر المستخدم. تأكد من أن المعرف صحيح.",
        "dev_unban_success": "✅ تم إلغاء حظر المستخدم `{user_id}` بنجاح.",
        "dev_unban_fail": "❌ فشل إلغاء حظر المستخدم. تأكد من أن المعرف صحيح.",
        "dev_all_data": "📊 *جميع بيانات المستخدمين*\n\n{data}",
        "btn_users_count": "👥 عدد المستخدمين",
        "btn_ban_user": "🚫 حذف مستخدم",
        "btn_unban_user": "✅ إضافة مستخدم محذوف",
        "btn_all_data": "📊 جميع البيانات",
        "btn_back": "🔙 رجوع"
    },
    "en": {
        "welcome": f"✨ Welcome to MR Email Bot!\n⤏͟͟͞͞༒⃝Ꭲ̴Ꭼ̴Ꭱ̴Ꮇ̴Ꮜ̴᙭̴♛Ꮎ̴Ꮩ̴Ꭼ̴Ꭱ̴Ꮮ̴Ꮎ̴Ꭱ̴Ꭰ̴༒⃟࿗⃝⏤͟͞➤⃟☠︎︎\n\nPowerful temporary email with many domains.\nDEV: @MR_Tails_YE",
        "need_phone": "📱 *Please register your phone number first*\n\nUse /phone command to share your phone number and verify your account.",
        "banned": BAN_MESSAGE,
        "phone_prompt": "📱 *Please share your phone number to verify your account*\n\nTap the button below to share your phone number.",
        "phone_saved": "✅ *Your phone number has been saved successfully*\n\nName: {name}\nUsername: {username}\nPhone: {phone}\nRegistration Date: {date}\n\n✨ You can now use the bot!",
        "no_emails": "⚠️ You don't have any temporary email yet. Use /generate to create one.",
        "choose_domain": "🌐 *Choose domain to generate random email:*",
        "choose_type": "🔢 *Choose username type:*",
        "type_with_numbers": "🔢 With numbers (e.g., a1b2c3d4)",
        "type_without_numbers": "🔤 Without numbers (letters only)",
        "generate_success": "✅ *New email created:*\n`{email}`",
        "generate_fail": "❌ Failed to create email, try again.",
        "emails_list": "📋 *Your Emails List:*",
        "fetch_select": "🔍 *Select email to fetch messages:*",
        "delete_select": "🗑️ *Select email to delete:*",
        "inbox_empty": "📭 No messages for `{email}`.",
        "inbox_messages": "📨 *Messages for* `{email}`:\n",
        "view_latest_hint": "\n💡 Use /view to see full message.",
        "no_messages": "📭 No messages.",
        "message_detail": "📄 *Message Details*\n\n*From:* {from_addr}\n*Subject:* {subject}\n\n*Body:*\n{body}",
        "delete_success": "🗑️ Email `{email}` deleted.",
        "delete_fail": "❌ Failed to delete email.",
        "custom_success": "✅ *Custom email added:*\n`{email}`",
        "custom_invalid": "❌ Invalid email or domain not supported.",
        "domains_list": "🌐 *All Supported Domains:*\n" + "\n".join([f"• `{d}`" for d in get_all_domains()]),
        "lang_changed": "🌐 Language changed to English.",
        "unknown": "❓ Unknown command. Use blue menu.",
        "fetch_button": "📥 Fetch",
        "delete_button": "🗑️ Delete",
        "back": "🔙 Back",
        "second_message": "✨ Your new fake mail id is: `{email}`\nSend /id to see the full list.",
        "not_authorized": "⚠️ *Not Authorized*\n\nThis command is only available for the developer.",
        "dev_panel": "👑 *Developer Control Panel*\n\nWelcome, Great Developer!\n\nSelect an option below:",
        "dev_users_list": "👥 *Users List*\n\nTotal Users: {total}\n\n{users_list}",
        "dev_no_users": "📭 No registered users.",
        "dev_ban_prompt": "🚫 *Ban User*\n\nSend the user ID you want to ban:",
        "dev_unban_prompt": "✅ *Unban User*\n\nSend the user ID you want to unban:",
        "dev_ban_success": "✅ User `{user_id}` has been banned successfully.",
        "dev_ban_fail": "❌ Failed to ban user. Make sure the ID is correct.",
        "dev_unban_success": "✅ User `{user_id}` has been unbanned successfully.",
        "dev_unban_fail": "❌ Failed to unban user. Make sure the ID is correct.",
        "dev_all_data": "📊 *All Users Data*\n\n{data}",
        "btn_users_count": "👥 Users Count",
        "btn_ban_user": "🚫 Ban User",
        "btn_unban_user": "✅ Unban User",
        "btn_all_data": "📊 All Data",
        "btn_back": "🔙 Back"
    }
}

def get_text(telegram_id: int, key: str, **kwargs) -> str:
    lang = get_user_lang(telegram_id)
    text = TEXTS.get(lang, TEXTS["en"]).get(key, key)
    return text.format(**kwargs) if kwargs else text

# ================= أوامر البوت (العامة) =================
async def set_commands(app: Application):
    # فقط الأوامر العامة تظهر للجميع
    commands = [
        BotCommand("start", "Start MR Email Bot"),
        BotCommand("phone", "Register your phone number"),
        BotCommand("generate", "Create new temporary email"),
        BotCommand("id", "Show your emails list"),
        BotCommand("set", "Add custom email"),
        BotCommand("fetch", "Fetch inbox messages"),
        BotCommand("view", "View last message"),
        BotCommand("delete", "Delete an email"),
        BotCommand("domains", "Show all domains"),
        BotCommand("language", "Change language"),
    ]
    await app.bot.set_my_commands(commands)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    
    if is_user_banned(uid):
        await update.message.reply_text(BAN_MESSAGE, parse_mode="Markdown")
        return
    
    if is_user_registered(uid):
        await update.message.reply_text(get_text(uid, "welcome"))
    else:
        await update.message.reply_text(get_text(uid, "need_phone"))

async def phone_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    
    if is_user_banned(uid):
        await update.message.reply_text(BAN_MESSAGE, parse_mode="Markdown")
        return
    
    keyboard = [[{"text": "📱 Share Phone Number", "request_contact": True}]]
    reply_markup = {"keyboard": keyboard, "resize_keyboard": True, "one_time_keyboard": True}
    
    await update.message.reply_text(get_text(uid, "phone_prompt"), reply_markup=reply_markup)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    contact = update.message.contact
    BOT_STATUS["last_activity"] = datetime.now()
    
    if is_user_banned(uid):
        await update.message.reply_text(BAN_MESSAGE, parse_mode="Markdown")
        return
    
    if contact:
        name = update.effective_user.first_name or "Unknown"
        username = update.effective_user.username or "No Username"
        phone = contact.phone_number
        if not phone.startswith("+"):
            phone = "+" + phone
        
        reg_date = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
        
        register_user(uid, name, username, phone, reg_date)
        
        remove_keyboard = {"remove_keyboard": True}
        
        text = get_text(uid, "phone_saved", name=name, username=f"@{username}" if username != "No Username" else username, phone=phone, date=reg_date)
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=remove_keyboard)

# ================= أوامر المطور (مخفية - لا تظهر في قائمة الأوامر) =================
async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    if uid != DEV_ID:
        await update.message.reply_text(get_text(uid, "not_authorized"))
        return
    
    monitor_link = "http://localhost:8080"
    await update.message.reply_text(
        f"📊 *رابط مراقبة البوت*\n\n"
        f"🌐 {monitor_link}\n"
        f"🔍 {monitor_link}/health\n\n"
        f"📌 *استخدام الرابط:*\n"
        f"• افتح الرابط في المتصفح لرؤية لوحة التحكم\n"
        f"• استخدم /health لجلب حالة البوت بصيغة JSON",
        parse_mode="Markdown"
    )

async def my_developer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    if uid != DEV_ID:
        await update.message.reply_text(get_text(uid, "not_authorized"))
        return
    
    keyboard = [
        [InlineKeyboardButton(get_text(uid, "btn_users_count"), callback_data="dev_users_count")],
        [InlineKeyboardButton(get_text(uid, "btn_ban_user"), callback_data="dev_ban_user")],
        [InlineKeyboardButton(get_text(uid, "btn_unban_user"), callback_data="dev_unban_user")],
        [InlineKeyboardButton(get_text(uid, "btn_all_data"), callback_data="dev_all_data")],
        [InlineKeyboardButton(get_text(uid, "btn_back"), callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(get_text(uid, "dev_panel"), reply_markup=reply_markup, parse_mode="Markdown")

# ================= أوامر البريد المؤقت (مع التحقق من الحظر والتسجيل) =================
async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    
    if is_user_banned(uid):
        await update.message.reply_text(BAN_MESSAGE, parse_mode="Markdown")
        return
    
    if not is_user_registered(uid):
        await update.message.reply_text(get_text(uid, "need_phone"))
        return
    
    domains = get_all_domains()
    keyboard = []
    row = []
    for domain in domains:
        row.append(InlineKeyboardButton(domain, callback_data=f"gen_domain_{domain}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(get_text(uid, "back"), callback_data="back_main")])
    await update.message.reply_text(
        get_text(uid, "choose_domain"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_emails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    
    if is_user_banned(uid):
        await update.message.reply_text(BAN_MESSAGE, parse_mode="Markdown")
        return
    
    if not is_user_registered(uid):
        await update.message.reply_text(get_text(uid, "need_phone"))
        return
    
    emails = get_user_emails(uid)
    if not emails:
        await update.message.reply_text(get_text(uid, "no_emails"))
        return
    keyboard = []
    for e in emails:
        keyboard.append([InlineKeyboardButton(e['email'], callback_data=f"view_{e['id']}")])
    await update.message.reply_text(
        get_text(uid, "emails_list"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    
    if is_user_banned(uid):
        await update.message.reply_text(BAN_MESSAGE, parse_mode="Markdown")
        return
    
    if not is_user_registered(uid):
        await update.message.reply_text(get_text(uid, "need_phone"))
        return
    
    context.user_data["waiting_email"] = True
    await update.message.reply_text(
        get_domains_list_text(uid),
        parse_mode="Markdown"
    )

async def fetch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    
    if is_user_banned(uid):
        await update.message.reply_text(BAN_MESSAGE, parse_mode="Markdown")
        return
    
    if not is_user_registered(uid):
        await update.message.reply_text(get_text(uid, "need_phone"))
        return
    
    emails = get_user_emails(uid)
    if not emails:
        await update.message.reply_text(get_text(uid, "no_emails"))
        return
    keyboard = []
    for e in emails:
        keyboard.append([InlineKeyboardButton(f"{get_text(uid, 'fetch_button')} {e['email']}", callback_data=f"fetch_{e['id']}")])
    await update.message.reply_text(
        get_text(uid, "fetch_select"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    
    if is_user_banned(uid):
        await update.message.reply_text(BAN_MESSAGE, parse_mode="Markdown")
        return
    
    if not is_user_registered(uid):
        await update.message.reply_text(get_text(uid, "need_phone"))
        return
    
    emails = get_user_emails(uid)
    if not emails:
        await update.message.reply_text(get_text(uid, "no_emails"))
        return
    keyboard = []
    for e in emails:
        keyboard.append([InlineKeyboardButton(f"{get_text(uid, 'delete_button')} {e['email']}", callback_data=f"del_{e['id']}")])
    await update.message.reply_text(
        get_text(uid, "delete_select"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    
    if is_user_banned(uid):
        await update.message.reply_text(BAN_MESSAGE, parse_mode="Markdown")
        return
    
    if not is_user_registered(uid):
        await update.message.reply_text(get_text(uid, "need_phone"))
        return
    
    emails = get_user_emails(uid)
    if not emails:
        await update.message.reply_text(get_text(uid, "no_emails"))
        return
    email_info = emails[0]
    email = email_info["email"]
    source = email_info["source"]
    if source == "src1":
        messages = src1_get_messages(email)
        if not messages:
            await update.message.reply_text(get_text(uid, "no_messages"))
            return
        content = src1_get_message_content(email, messages[0]["mail_id"])
        if content:
            text = get_text(uid, "message_detail",
                            from_addr=content.get("from_mail", "?"),
                            subject=content.get("subject", "?"),
                            body=content.get("text", "")[:1000])
            await update.message.reply_text(text, parse_mode="Markdown")
    else:
        messages = src2_get_messages(email)
        if not messages:
            await update.message.reply_text(get_text(uid, "no_messages"))
            return
        content = src2_get_message_content(messages[0]["uid"])
        if content:
            text = get_text(uid, "message_detail",
                            from_addr=content.get("f", "?"),
                            subject=content.get("s", "?"),
                            body=content.get("text", "")[:1000])
            await update.message.reply_text(text, parse_mode="Markdown")

async def domains(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    
    if is_user_banned(uid):
        await update.message.reply_text(BAN_MESSAGE, parse_mode="Markdown")
        return
    
    text = get_text(uid, "domains_list")
    await update.message.reply_text(text, parse_mode="Markdown")

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    
    if is_user_banned(uid):
        await update.message.reply_text(BAN_MESSAGE, parse_mode="Markdown")
        return
    
    keyboard = [
        [InlineKeyboardButton("العربية 🇸🇦", callback_data="lang_ar")],
        [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")],
    ]
    await update.message.reply_text("🌐 Choose language / اختر اللغة:", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= معالجة النصوص والأزرار =================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    
    if is_user_banned(uid):
        await update.message.reply_text(BAN_MESSAGE, parse_mode="Markdown")
        return
    
    if context.user_data.get("waiting_email"):
        if not is_user_registered(uid):
            await update.message.reply_text(get_text(uid, "need_phone"))
            context.user_data["waiting_email"] = False
            return
            
        text = update.message.text.strip()
        if "@" in text:
            username, domain = text.split("@", 1)
            source = get_source_from_domain(domain)
            if source == "src1":
                email = src1_create_email(username, domain)
                if email:
                    add_user_email(uid, email, "src1")
                    await update.message.reply_text(get_text(uid, "custom_success", email=email), parse_mode="Markdown")
                    await update.message.reply_text(get_text(uid, "second_message", email=email), parse_mode="Markdown")
                else:
                    await update.message.reply_text(get_text(uid, "custom_invalid"))
            elif source == "src2":
                email = src2_create_email(username, domain)
                if email:
                    add_user_email(uid, email, "src2")
                    await update.message.reply_text(get_text(uid, "custom_success", email=email), parse_mode="Markdown")
                    await update.message.reply_text(get_text(uid, "second_message", email=email), parse_mode="Markdown")
                else:
                    await update.message.reply_text(get_text(uid, "custom_invalid"))
            else:
                await update.message.reply_text(get_text(uid, "custom_invalid"))
        else:
            await update.message.reply_text(get_text(uid, "custom_invalid"))
        context.user_data["waiting_email"] = False
    else:
        await update.message.reply_text(get_text(uid, "unknown"))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    data = query.data
    
    # للمستخدمين المحظورين (ما عدا المطور)
    if uid != DEV_ID and is_user_banned(uid):
        await query.edit_message_text(BAN_MESSAGE, parse_mode="Markdown")
        return

    if data == "lang_ar":
        set_user_lang(uid, "ar")
        await query.edit_message_text(get_text(uid, "lang_changed"))
        return
    elif data == "lang_en":
        set_user_lang(uid, "en")
        await query.edit_message_text(get_text(uid, "lang_changed"))
        return

    if data == "back_main":
        if uid == DEV_ID:
            keyboard = [
                [InlineKeyboardButton(get_text(uid, "btn_users_count"), callback_data="dev_users_count")],
                [InlineKeyboardButton(get_text(uid, "btn_ban_user"), callback_data="dev_ban_user")],
                [InlineKeyboardButton(get_text(uid, "btn_unban_user"), callback_data="dev_unban_user")],
                [InlineKeyboardButton(get_text(uid, "btn_all_data"), callback_data="dev_all_data")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(get_text(uid, "dev_panel"), reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await query.edit_message_text(get_text(uid, "welcome"))
        return

    # ================= دوال المطور =================
    if uid == DEV_ID:
        if data == "dev_users_count":
            users = get_all_users()
            total = len([u for u in users if u["banned"] == 0])
            banned = len([u for u in users if u["banned"] == 1])
            
            if users:
                users_list = ""
                for u in users[:20]:
                    status = "🚫" if u["banned"] == 1 else "✅"
                    users_list += f"{status} `{u['telegram_id']}` - {u['name']}\n"
                
                text = get_text(uid, "dev_users_list", total=total, users_list=users_list)
                text += f"\n\n🚫 المحظورين: {banned}"
            else:
                text = get_text(uid, "dev_no_users")
            
            await query.edit_message_text(text, parse_mode="Markdown")
            return
        
        elif data == "dev_ban_user":
            context.user_data["dev_action"] = "ban"
            await query.edit_message_text(get_text(uid, "dev_ban_prompt"), parse_mode="Markdown")
            return
        
        elif data == "dev_unban_user":
            context.user_data["dev_action"] = "unban"
            await query.edit_message_text(get_text(uid, "dev_unban_prompt"), parse_mode="Markdown")
            return
        
        elif data == "dev_all_data":
            users = get_all_users()
            if users:
                data_text = ""
                for u in users:
                    data_text += f"🆔 {u['telegram_id']}\n"
                    data_text += f"📛 {u['name']}\n"
                    data_text += f"🔖 {u['username']}\n"
                    data_text += f"📞 {u['phone']}\n"
                    data_text += f"📅 {u['reg_date']}\n"
                    data_text += f"{'🚫 محظور' if u['banned'] == 1 else '✅ نشط'}\n"
                    data_text += "─" * 20 + "\n"
                
                await query.edit_message_text(get_text(uid, "dev_all_data", data=data_text), parse_mode="Markdown")
            else:
                await query.edit_message_text(get_text(uid, "dev_no_users"))
            return

    # ================= باقي الكود للبريد المؤقت =================
    if not is_user_registered(uid):
        await query.edit_message_text(get_text(uid, "need_phone"))
        return

    emails_info = get_user_emails(uid)

    if data.startswith("gen_domain_"):
        domain = data[11:]
        context.user_data["selected_domain"] = domain
        keyboard = [
            [InlineKeyboardButton(get_text(uid, "type_with_numbers"), callback_data="gen_with_numbers")],
            [InlineKeyboardButton(get_text(uid, "type_without_numbers"), callback_data="gen_without_numbers")],
            [InlineKeyboardButton(get_text(uid, "back"), callback_data="back_main")]
        ]
        await query.edit_message_text(
            get_text(uid, "choose_type"),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data == "gen_with_numbers":
        domain = context.user_data.get("selected_domain")
        if not domain:
            await query.edit_message_text(get_text(uid, "generate_fail"))
            return
        source = get_source_from_domain(domain)
        username = random_username(8, with_numbers=True)
        email = None
        if source == "src1":
            email = src1_create_email(username, domain)
        elif source == "src2":
            email = src2_create_email(username, domain)
        if email:
            add_user_email(uid, email, source)
            await query.edit_message_text(
                get_text(uid, "generate_success", email=email),
                parse_mode="Markdown"
            )
            await query.message.reply_text(
                get_text(uid, "second_message", email=email),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(get_text(uid, "generate_fail"))
        return

    if data == "gen_without_numbers":
        domain = context.user_data.get("selected_domain")
        if not domain:
            await query.edit_message_text(get_text(uid, "generate_fail"))
            return
        source = get_source_from_domain(domain)
        username = random_username(8, with_numbers=False)
        email = None
        if source == "src1":
            email = src1_create_email(username, domain)
        elif source == "src2":
            email = src2_create_email(username, domain)
        if email:
            add_user_email(uid, email, source)
            await query.edit_message_text(
                get_text(uid, "generate_success", email=email),
                parse_mode="Markdown"
            )
            await query.message.reply_text(
                get_text(uid, "second_message", email=email),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(get_text(uid, "generate_fail"))
        return

    if data.startswith("view_"):
        eid = int(data.split("_")[1])
        for e in emails_info:
            if e["id"] == eid:
                await query.edit_message_text(f"📧 *{e['email']}*\nUse /fetch to get messages.", parse_mode="Markdown")
                return

    if data.startswith("fetch_"):
        eid = int(data.split("_")[1])
        for e in emails_info:
            if e["id"] == eid:
                email = e["email"]
                source = e["source"]
                if source == "src1":
                    messages = src1_get_messages(email)
                    if not messages:
                        await query.edit_message_text(get_text(uid, "inbox_empty", email=email), parse_mode="Markdown")
                        return
                    text = get_text(uid, "inbox_messages", email=email)
                    for i, m in enumerate(messages[:5], 1):
                        text += f"\n*{i}.* From: {m['from_mail'][:30]}\n   Subject: {m['subject'][:40]}\n"
                    text += get_text(uid, "view_latest_hint")
                    await query.edit_message_text(text, parse_mode="Markdown")
                    for m in messages[:5]:
                        content = src1_get_message_content(email, m["mail_id"])
                        if content:
                            save_inbox_message(uid, email, source, content.get("from_mail",""), content.get("subject",""), content.get("text",""), mid=m["mail_id"])
                else:
                    messages = src2_get_messages(email)
                    if not messages:
                        await query.edit_message_text(get_text(uid, "inbox_empty", email=email), parse_mode="Markdown")
                        return
                    text = get_text(uid, "inbox_messages", email=email)
                    for i, m in enumerate(messages[:5], 1):
                        text += f"\n*{i}.* From: {m['f'][:30]}\n   Subject: {m['s'][:40]}\n"
                    text += get_text(uid, "view_latest_hint")
                    await query.edit_message_text(text, parse_mode="Markdown")
                    for m in messages[:5]:
                        content = src2_get_message_content(m["uid"])
                        if content:
                            save_inbox_message(uid, email, source, content.get("f",""), content.get("s",""), content.get("text",""), uid=m["uid"])
                return

    if data.startswith("del_"):
        eid = int(data.split("_")[1])
        for e in emails_info:
            if e["id"] == eid:
                email = e["email"]
                source = e["source"]
                if source == "src1":
                    success = src1_delete_email(email)
                else:
                    success = src2_delete_email(email)
                if success:
                    remove_user_email(uid, email)
                    await query.edit_message_text(get_text(uid, "delete_success", email=email), parse_mode="Markdown")
                else:
                    await query.edit_message_text(get_text(uid, "delete_fail"))
                return

# ================= معالجة رسائل المطور (حظر/إلغاء حظر) =================
async def handle_dev_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    if uid != DEV_ID:
        return
    
    if context.user_data.get("dev_action"):
        action = context.user_data["dev_action"]
        text = update.message.text.strip()
        
        try:
            target_id = int(text)
        except ValueError:
            await update.message.reply_text("❌ يرجى إرسال معرف مستخدم صحيح (أرقام فقط)")
            return
        
        if action == "ban":
            if ban_user(target_id):
                await update.message.reply_text(f"✅ تم حظر المستخدم `{target_id}` بنجاح")
                try:
                    await context.bot.send_message(target_id, BAN_MESSAGE, parse_mode="Markdown")
                except:
                    pass
            else:
                await update.message.reply_text(f"❌ فشل حظر المستخدم `{target_id}`")
        elif action == "unban":
            if unban_user(target_id):
                await update.message.reply_text(f"✅ تم إلغاء حظر المستخدم `{target_id}` بنجاح")
                await context.bot.send_message(target_id, "✅ تم إلغاء حظرك يمكنك استخدام البوت مرة أخرى")
            else:
                await update.message.reply_text(f"❌ فشل إلغاء حظر المستخدم `{target_id}`")
        
        context.user_data["dev_action"] = None

# ================= التشغيل =================
def main():
    # طباعة البانر الجبار
    print(f"""{Y}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
{R}    ███╗   ███╗██████╗     ███████╗███╗   ███╗ █████╗ ██╗██╗     ║
{R}    ████╗ ████║██╔══██╗    ██╔════╝████╗ ████║██╔══██╗██║██║     ║
{R}    ██╔████╔██║██████╔╝    █████╗  ██╔████╔██║███████║██║██║     ║
{R}    ██║╚██╔╝██║██╔══██╗    ██╔══╝  ██║╚██╔╝██║██╔══██║██║██║     ║
{R}    ██║ ╚═╝ ██║██║  ██║    ███████╗██║ ╚═╝ ██║██║  ██║██║███████╗║
{R}    ╚═╝     ╚═╝╚═╝  ╚═╝    ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝║
{G}                                                              ║
{G}              ██████╗  ██████╗ ████████╗                     ║
{G}              ██╔══██╗██╔═══██╗╚══██╔══╝                     ║
{G}              ██████╔╝██║   ██║   ██║                        ║
{G}              ██╔══██╗██║   ██║   ██║                        ║
{G}              ██████╔╝╚██████╔╝   ██║                        ║
{G}              ╚═════╝  ╚═════╝    ╚═╝                        ║
{Y}                                                              ║
{Y}                       MR EMAIL BOT v4.0                      ║
{Y}                    ULTIMATE EDITION + DEV PANEL              ║
╚══════════════════════════════════════════════════════════════╝{RESET}""")
    print(f"{C}╔══════════════════════════════════════════════════════════════╗")
    print(f"{C}║ {W}DEV      : {Y}@MR_Tails_YE                                              {C}║")
    print(f"{C}║ {W}TARGET   : {Y}TEMPORARY EMAIL + {len(get_all_domains())} DOMAINS + USER SYSTEM         {C}║")
    print(f"{C}║ {W}ENGINE   : {Y}STEALTH MODE + HIDDEN SOURCES + DEV CONTROL            {C}║")
    print(f"{C}║ {W}MONITOR  : {Y}http://localhost:8080                                      {C}║")
    print(f"{C}║ {W}HEALTH   : {Y}http://localhost:8080/health                               {C}║")
    print(f"{C}╚══════════════════════════════════════════════════════════════╝{RESET}\n")

    if os.path.exists(DB_PATH):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("SELECT lang FROM users LIMIT 1")
        except sqlite3.OperationalError:
            print("⚠️ قاعدة البيانات قديمة، سيتم إنشاء جديدة.")
            os.remove(DB_PATH)
    init_db()
    
    update_bot_stats()

    monitor_thread = threading.Thread(target=run_monitor_server, daemon=True)
    monitor_thread.start()
    print(f"{G}✅ Monitor server started on http://localhost:8080{RESET}")
    
    api_check_thread = threading.Thread(target=check_apis_status, daemon=True)
    api_check_thread.start()
    print(f"{G}✅ API monitoring started (sources hidden){RESET}")

    app = Application.builder().token(TOKEN).build()
    app.post_init = set_commands

    # أوامر البوت العامة
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("phone", phone_command))
    app.add_handler(CommandHandler("generate", generate))
    app.add_handler(CommandHandler("id", show_emails))
    app.add_handler(CommandHandler("set", set_custom))
    app.add_handler(CommandHandler("fetch", fetch_command))
    app.add_handler(CommandHandler("view", view))
    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CommandHandler("domains", domains))
    app.add_handler(CommandHandler("language", language))
    
    # أوامر المطور (مخفية - لا تظهر في قائمة الأوامر)
    app.add_handler(CommandHandler("Mydeveloper", my_developer))
    app.add_handler(CommandHandler("monitor", monitor))
    
    # معالجات إضافية
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.TEXT & filters.COMMAND, handle_dev_text))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print(f"{G}✅ MR Email Bot is running! (All sources hidden){RESET}")
    print(f"{C}👑 Developer commands: /Mydeveloper , /monitor (hidden from users){RESET}")
    print(f"{C}📊 Monitor URL: http://localhost:8080{RESET}")
    print(f"{Y}💡 Users must register with /phone first{RESET}\n")
    
    app.run_polling()

if __name__ == "__main__":
    main()