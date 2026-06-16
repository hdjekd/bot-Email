#!/usr/bin/env python3
# MR_Email_Bot_Ultimate.py
# بوت MR Email - بريد مؤقت خارق (مخفي المصادر بالكامل) مع نظام تسجيل ومراقبة وحماية
# الإصدار 7.0 - الإصدار الأسطوري الذي يفوق التصور 🏆🔥

import logging
import sqlite3
import random
import string
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import os
import threading
import time
import json
import hashlib
from functools import wraps
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
import urllib3
import ssl
import re

# تعطيل التحذيرات SSL الغير ضرورية
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= إعداد Flask للمراقبة المتطورة =================
monitor_app = Flask(__name__)
CORS(monitor_app)

# متغيرات حالة البوت المتطورة
BOT_STATUS = {
    "running": True,
    "start_time": datetime.now(),
    "total_users": 0,
    "total_emails": 0,
    "total_messages": 0,
    "last_activity": None,
    "api_status": {
        "api_1": "checking",
        "api_2": "checking",
        "api_3": "checking"
    },
    "ping_count": 0,
    "daily_users": 0,
    "weekly_users": 0,
    "total_requests": 0,
    "errors": 0,
    "last_error": None,
    "system_load": 0,
    "cache_hits": 0,
    "cache_misses": 0
}

# متغيرات لمنع النوم المحسنة
KEEP_AWAKE_URLS = []
PING_INTERVAL = 45  # ثانية (أسرع)
KEEP_AWAKE_THREAD_RUNNING = True
LAST_PING_TIME = datetime.now()

# ================= إعدادات المطور والتوكن الآمنة =================
TOKEN = os.environ.get("BOT_TOKEN", "8247787064:AAGkR9W7uj5NklpEnA1M-lZ4R1XDb-qTjrg")
DEV_ID = int(os.environ.get("DEV_ID", 8311254462))

# كاش للدومينات (تحسين الأداء)
_cached_domains = None
_cached_domains_time = None
CACHE_DURATION = 300  # 5 دقائق
user_lang_pending = {}
user_session_data = {}  # جلسات المستخدمين
email_cache = {}  # كاش للبريدات
MESSAGE_CACHE = {}  # كاش للرسائل
CACHE_MAX_SIZE = 1000

# ================= قالب HTML للوحة التحكم المتطورة =================
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MR Email Bot - لوحة المراقبة الأسطورية</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            min-height: 100vh;
            padding: 20px;
            animation: bgPulse 10s ease-in-out infinite;
        }
        @keyframes bgPulse {
            0%, 100% { background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%); }
            50% { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); }
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { 
            font-size: 3em; 
            margin-bottom: 10px; 
            text-shadow: 0 0 20px #667eea, 0 0 40px #764ba2, 0 0 60px #667eea;
            animation: glow 2s ease-in-out infinite alternate;
        }
        @keyframes glow {
            from { text-shadow: 0 0 20px #667eea, 0 0 40px #764ba2; }
            to { text-shadow: 0 0 30px #764ba2, 0 0 60px #667eea, 0 0 80px #764ba2; }
        }
        .header p { font-size: 1.3em; opacity: 0.9; }
        .status-card {
            background: rgba(255,255,255,0.95);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 15px 50px rgba(0,0,0,0.4);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .status-badge {
            display: inline-block;
            padding: 10px 25px;
            border-radius: 50px;
            font-weight: bold;
            margin-bottom: 15px;
            font-size: 1.1em;
            animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        .status-online { background: #10b981; color: white; box-shadow: 0 0 30px #10b981; }
        .status-offline { background: #ef4444; color: white; box-shadow: 0 0 30px #ef4444; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            transition: all 0.3s;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .stat-card:hover { transform: translateY(-10px) scale(1.02); box-shadow: 0 20px 40px rgba(0,0,0,0.3); }
        .stat-number { font-size: 2.8em; font-weight: bold; margin-bottom: 10px; animation: countUp 1s ease-out; }
        @keyframes countUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .stat-label { font-size: 0.95em; opacity: 0.9; }
        .info-card {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        .info-card h3 { 
            margin-bottom: 15px; 
            color: #333; 
            border-right: 4px solid #667eea; 
            padding-right: 10px;
            font-size: 1.2em;
        }
        .info-item {
            padding: 12px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            transition: background 0.3s;
        }
        .info-item:hover { background: #f8f9fa; }
        .info-label { font-weight: bold; color: #666; }
        .info-value { color: #333; font-family: monospace; }
        .refresh-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 50px;
            cursor: pointer;
            font-size: 1.1em;
            margin-top: 20px;
            transition: all 0.3s;
            font-weight: bold;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }
        .refresh-btn:hover { transform: scale(1.05); box-shadow: 0 15px 40px rgba(102, 126, 234, 0.5); }
        .footer { text-align: center; color: white; margin-top: 30px; opacity: 0.7; }
        .api-status {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .api-item {
            background: #f3f4f6;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            transition: all 0.3s;
        }
        .api-item:hover { transform: scale(1.02); }
        .api-name { font-weight: bold; margin-bottom: 10px; color: #333; }
        .api-working { color: #10b981; font-weight: bold; }
        .api-error { color: #ef4444; font-weight: bold; }
        .api-checking { color: #f59e0b; font-weight: bold; }
        .ping-counter {
            font-size: 1.2em;
            color: #667eea;
            font-weight: bold;
            margin-top: 10px;
        }
        @media (max-width: 600px) {
            .header h1 { font-size: 2em; }
            .stat-number { font-size: 2em; }
            .stats-grid { grid-template-columns: 1fr 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ MR EMAIL BOT ⚡</h1>
            <p>نظام المراقبة المتطور - بريد مؤقت خارق - لا ينام أبداً 🔥</p>
        </div>
        
        <div class="status-card">
            <div id="statusBadge" class="status-badge status-online">🟢 البوت يعمل</div>
            <div id="uptime">⏱️ وقت التشغيل: جاري التحميل...</div>
            <div id="pingCount" class="ping-counter">📡 عدد النقرات: 0</div>
            <div id="systemLoad">📊 حمل النظام: 0%</div>
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
            <div class="stat-card">
                <div class="stat-number" id="dailyUsers">0</div>
                <div class="stat-label">📅 مستخدمين اليوم</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="totalRequests">0</div>
                <div class="stat-label">🚀 الطلبات</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="cacheHits">0</div>
                <div class="stat-label">💾 كاش</div>
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
            <div class="info-item">
                <span class="info-label">📡 حالة النوم:</span>
                <span class="info-value" id="sleepStatus">🟢 مستيقظ</span>
            </div>
            <div class="info-item">
                <span class="info-label">📊 الإصدار:</span>
                <span class="info-value">v7.0 الأسطوري 🏆</span>
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
                <div class="api-item">
                    <div class="api-name">🖥️ الخادم الاحتياطي</div>
                    <div id="api3Status">🟡 جاري الفحص...</div>
                </div>
            </div>
        </div>
        
        <div style="text-align: center;">
            <button class="refresh-btn" onclick="refreshData()">🔄 تحديث البيانات</button>
        </div>
        
        <div class="footer">
            <p>MR EMAIL BOT v7.0 - بريد مؤقت خارق | تم التطوير بواسطة @MR_Tails_YE | 🔥 لا ينام أبداً</p>
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
                document.getElementById('dailyUsers').textContent = data.daily_users || 0;
                document.getElementById('totalRequests').textContent = data.total_requests || 0;
                document.getElementById('cacheHits').textContent = data.cache_hits || 0;
                document.getElementById('uptime').innerHTML = `⏱️ وقت التشغيل: ${data.uptime || '0 ساعة'}`;
                document.getElementById('lastUpdate').textContent = data.last_activity || '-';
                document.getElementById('pingCount').innerHTML = `📡 عدد النقرات: ${data.ping_count || 0}`;
                document.getElementById('systemLoad').innerHTML = `📊 حمل النظام: ${data.system_load || 0}%`;
                
                if (data.ping_count > 0) {
                    document.getElementById('sleepStatus').innerHTML = '🟢 مستيقظ - يتم النقر باستمرار 🔥';
                    document.getElementById('sleepStatus').style.color = '#10b981';
                }
                
                const statusBadge = document.getElementById('statusBadge');
                if (data.running) {
                    statusBadge.className = 'status-badge status-online';
                    statusBadge.innerHTML = '🟢 البوت يعمل بقوة ⚡';
                } else {
                    statusBadge.className = 'status-badge status-offline';
                    statusBadge.innerHTML = '🔴 البوت متوقف';
                }
                
                if (data.api_status) {
                    const api1 = document.getElementById('api1Status');
                    if (data.api_status.api_1 === 'working') {
                        api1.innerHTML = '🟢 يعمل بشكل طبيعي';
                        api1.className = 'api-working';
                    } else if (data.api_status.api_1 === 'error') {
                        api1.innerHTML = '🟡 مشكلة مؤقتة';
                        api1.className = 'api-checking';
                    } else {
                        api1.innerHTML = '🔴 لا يعمل';
                        api1.className = 'api-error';
                    }
                    
                    const api2 = document.getElementById('api2Status');
                    if (data.api_status.api_2 === 'working') {
                        api2.innerHTML = '🟢 يعمل بشكل طبيعي';
                        api2.className = 'api-working';
                    } else if (data.api_status.api_2 === 'error') {
                        api2.innerHTML = '🟡 مشكلة مؤقتة';
                        api2.className = 'api-checking';
                    } else {
                        api2.innerHTML = '🔴 لا يعمل';
                        api2.className = 'api-error';
                    }
                    
                    const api3 = document.getElementById('api3Status');
                    if (data.api_status.api_3 === 'working') {
                        api3.innerHTML = '🟢 يعمل بشكل طبيعي';
                        api3.className = 'api-working';
                    } else if (data.api_status.api_3 === 'error') {
                        api3.innerHTML = '🟡 مشكلة مؤقتة';
                        api3.className = 'api-checking';
                    } else {
                        api3.innerHTML = '🔴 لا يعمل';
                        api3.className = 'api-error';
                    }
                }
            } catch (error) {
                console.error('خطأ:', error);
            }
        }
        
        refreshData();
        setInterval(refreshData, 3000);
    </script>
</body>
</html>
'''

# ================= نقاط نهاية Flask للمراقبة المتطورة =================
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
        "version": "7.0",
        "timestamp": int(time.time()),
        "uptime": f"{hours}h {minutes}m",
        "stats": {
            "total_users": BOT_STATUS["total_users"],
            "total_emails": BOT_STATUS["total_emails"],
            "total_messages": BOT_STATUS["total_messages"]
        },
        "ping_count": BOT_STATUS["ping_count"],
        "system_load": BOT_STATUS["system_load"]
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
        "api_status": BOT_STATUS["api_status"],
        "ping_count": BOT_STATUS["ping_count"],
        "daily_users": BOT_STATUS["daily_users"],
        "weekly_users": BOT_STATUS["weekly_users"],
        "total_requests": BOT_STATUS["total_requests"],
        "system_load": BOT_STATUS["system_load"],
        "cache_hits": BOT_STATUS["cache_hits"],
        "cache_misses": BOT_STATUS["cache_misses"]
    })

@monitor_app.route('/api/ping', methods=['GET', 'POST'])
def ping_endpoint():
    """نقطة نهاية للنبضات - للحفاظ على البوت مستيقظاً"""
    global LAST_PING_TIME
    LAST_PING_TIME = datetime.now()
    BOT_STATUS["ping_count"] += 1
    BOT_STATUS["last_activity"] = datetime.now()
    return jsonify({"status": "pong", "time": datetime.now().isoformat()})

@monitor_app.route('/api/stats/reset', methods=['POST'])
def reset_stats():
    """إعادة تعيين الإحصائيات (للمطور فقط)"""
    auth = request.headers.get('X-Dev-Key')
    if auth != "MR_DEV_7.0":
        return jsonify({"error": "Unauthorized"}), 401
    
    BOT_STATUS["daily_users"] = 0
    BOT_STATUS["total_requests"] = 0
    return jsonify({"status": "reset"})

# ================= دالة منع النوم المحسنة - الحل الجهني الأسطوري =================
def keep_alive_ping():
    """دالة جهنمية محسنة لمنع البوت من النوم - تضرب السيرفر بنبضات مستمرة بشراسة"""
    global KEEP_AWAKE_THREAD_RUNNING, LAST_PING_TIME
    
    # الحصول على رابط السيرفر الحالي
    try:
        # محاولة الحصول على رابط Replit الفعلي
        replit_domain = os.environ.get("REPLIT_URL") or os.environ.get("REPLIT_DEV_DOMAIN") or ""
        if replit_domain:
            public_url = f"https://{replit_domain}"
        else:
            # استخدام localhost كبديل
            public_url = "http://localhost:8080"
        
        KEEP_AWAKE_URLS = [
            public_url,
            f"{public_url}/health",
            f"{public_url}/api/status",
            f"{public_url}/api/ping"
        ]
    except:
        KEEP_AWAKE_URLS = ["http://localhost:8080", "http://localhost:8080/health", "http://localhost:8080/api/ping"]
    
    print(f"{Y}🔥 نظام منع النوم الأسطوري تم تفعيله!{RESET}")
    print(f"{C}📡 سيتم النقر على: {KEEP_AWAKE_URLS[0]}{RESET}")
    print(f"{G}⚡ سيبقى البوت مستيقظاً للأبد!{RESET}")
    
    ping_failures = 0
    max_failures = 5
    
    while KEEP_AWAKE_THREAD_RUNNING:
        try:
            # النقر على الروابط المختلفة لإبقاء السيرفر نشطاً
            for url in KEEP_AWAKE_URLS:
                try:
                    # استخدام timeout مناسب
                    response = requests.get(url, timeout=5, verify=False)
                    if response.status_code in [200, 404]:
                        BOT_STATUS["ping_count"] += 1
                        ping_failures = 0
                        if BOT_STATUS["ping_count"] % 10 == 0:
                            print(f"{G}✅ نبض {BOT_STATUS['ping_count']} - السيرفر مستيقظ 😈{RESET}")
                    else:
                        print(f"{Y}⚠️ نبض {BOT_STATUS['ping_count']} - استجابة غير متوقعة: {response.status_code}{RESET}")
                        ping_failures += 1
                except requests.exceptions.Timeout:
                    print(f"{R}⏰ مهلة النبض - المحاولة مرة أخرى{RESET}")
                    ping_failures += 1
                except requests.exceptions.ConnectionError:
                    print(f"{R}🔌 خطأ اتصال في النبض - إعادة المحاولة{RESET}")
                    ping_failures += 1
                except Exception as e:
                    print(f"{R}⚠️ خطأ في النبض: {e}{RESET}")
                    ping_failures += 1
                
                # إذا فشل النبض عدة مرات، نزيد من حدة المحاولات
                if ping_failures >= max_failures:
                    print(f"{R}🔥 {ping_failures} فشل متتالي - زيادة وتيرة النبضات!{RESET}")
                    ping_failures = 0
                    time.sleep(1)
                
                # ننتظر قليلاً بين كل نبضة
                time.sleep(1.5)
            
            # نوم قصير بين كل دورة كاملة
            time.sleep(PING_INTERVAL // 2)  # أكثر عدوانية
            
            # تحديث حالة النظام
            BOT_STATUS["system_load"] = min(100, BOT_STATUS["system_load"] + 0.1)
            if BOT_STATUS["system_load"] > 50:
                BOT_STATUS["system_load"] = 50
            
        except Exception as e:
            print(f"{R}🔥 خطأ في نظام منع النوم: {e}{RESET}")
            time.sleep(5)
            
            # إعادة تعيين حالة النظام في حالة الخطأ
            BOT_STATUS["system_load"] = 10

def run_monitor_server():
    """تشغيل خادم المراقبة مع إعدادات خاصة بـ Replit"""
    port = int(os.environ.get('PORT', 8080))
    
    # في Replit، نستخدم host = '0.0.0.0' للسماح بالوصول الخارجي
    try:
        monitor_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"{R}❌ فشل تشغيل خادم المراقبة: {e}{RESET}")
        # محاولة تشغيل على منفذ آخر
        try:
            monitor_app.run(host='0.0.0.0', port=8081, debug=False, use_reloader=False, threaded=True)
        except:
            print(f"{R}❌ فشل تشغيل خادم المراقبة على جميع المنافذ{RESET}")

def update_bot_stats():
    """تحديث إحصائيات البوت بشكل آمن"""
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'banned' in columns:
                cursor.execute("SELECT COUNT(*) FROM users WHERE banned = 0")
                BOT_STATUS["total_users"] = cursor.fetchone()[0]
            else:
                cursor.execute("SELECT COUNT(*) FROM users")
                BOT_STATUS["total_users"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM emails")
            BOT_STATUS["total_emails"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM inbox")
            BOT_STATUS["total_messages"] = cursor.fetchone()[0]
            
            # حساب المستخدمين اليوم
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(*) FROM users WHERE date(reg_date) = ?", (today,))
            BOT_STATUS["daily_users"] = cursor.fetchone()[0]
            
            # حساب المستخدمين الأسبوع
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(*) FROM users WHERE date(reg_date) >= ?", (week_ago,))
            BOT_STATUS["weekly_users"] = cursor.fetchone()[0]
            
    except Exception as e:
        log.error(f"Error updating stats: {e}")
        BOT_STATUS["errors"] += 1
        BOT_STATUS["last_error"] = str(e)

def check_apis_status():
    """فحص حالة APIs بشكل مستمر مع إضافة خادم ثالث"""
    while True:
        try:
            # فحص API 1 - tempmail.plus
            try:
                r = requests.get("https://tempmail.plus/api/mails", params={"email": "test@mailto.plus", "first_id": 1}, timeout=10)
                BOT_STATUS["api_status"]["api_1"] = "working" if r.status_code == 200 else "error"
                if r.status_code == 200:
                    BOT_STATUS["api_status"]["api_1"] = "working"
                else:
                    BOT_STATUS["api_status"]["api_1"] = "error"
            except:
                BOT_STATUS["api_status"]["api_1"] = "down"
            
            # فحص API 2 - inboxes.com
            try:
                r = requests.get("https://inboxes.com/api/v2/domain", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                if r.status_code == 200:
                    BOT_STATUS["api_status"]["api_2"] = "working"
                else:
                    BOT_STATUS["api_status"]["api_2"] = "error"
            except:
                BOT_STATUS["api_status"]["api_2"] = "down"
            
            # فحص API 3 - خادم احتياطي
            try:
                r = requests.get("https://api.temp-mail.org/request/domains/format/json", timeout=10)
                if r.status_code == 200:
                    BOT_STATUS["api_status"]["api_3"] = "working"
                else:
                    BOT_STATUS["api_status"]["api_3"] = "error"
            except:
                BOT_STATUS["api_status"]["api_3"] = "down"
                
            update_bot_stats()
            BOT_STATUS["total_requests"] += 1
            
        except Exception as e:
            log.error(f"API check error: {e}")
            BOT_STATUS["errors"] += 1
            BOT_STATUS["last_error"] = str(e)
        time.sleep(30)

# ================= إعداد التسجيل =================
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('mr_bot.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ================= ألوان للبانر =================
R = '\033[91m'
G = '\033[92m'
Y = '\033[93m'
C = '\033[96m'
W = '\033[97m'
B = '\033[94m'
P = '\033[95m'
RESET = '\033[0m'

# ================= جميع الدومينات (موسعة) =================
SOURCE1_DOMAINS = [
    "mailto.plus", "fexpost.com", "fexbox.org", "mailbok.in.ua",
    "chitthi.in", "fextemp.com", "any.pink", "merepost.com",
    "tempmail.plus", "temp-mail.org", "guerrillamail.com"
]

SOURCE2_STATIC_DOMAINS = [
    "blondmail.com", "chapsmail.com", "clowmail.com", "dropjar.com",
    "fivermail.com", "getairmail.com", "getmule.com", "getnada.com",
    "gimpmail.com", "givmail.com", "guysmail.com", "inboxbear.com",
    "replyloop.com", "robot-mail.com", "spicysoda.com", "tafmail.com",
    "temptami.com", "tupmail.com", "vomoto.com", "mailnator.com",
    "mailexpire.com", "mintemail.com", "moakt.com"
]

SOURCE3_DOMAINS = [
    "temp-mail.org", "guerrillamail.com", "sharklasers.com",
    "grr.la", "guerrillamail.biz", "guerrillamail.net"
]

# ================= دوال API المحسنة =================
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

# ================= API الثالثة (احتياطية) =================
SOURCE3_URL = "https://api.temp-mail.org"

def src3_create_email(username: str, domain: str) -> Optional[str]:
    email = f"{username}@{domain}"
    try:
        # التحقق من صحة البريد
        r = requests.get(f"{SOURCE3_URL}/request/mail/id/{username}/format/json", timeout=10)
        if r.status_code == 200:
            return email
    except:
        pass
    return None

def src3_get_messages(email: str) -> List[Dict]:
    try:
        username = email.split("@")[0]
        r = requests.get(f"{SOURCE3_URL}/request/mail/id/{username}/format/json", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data:
                return [{"mail_id": i, "from_mail": d.get("mail_from", ""), "subject": d.get("mail_subject", ""), "text": d.get("mail_text_only", "")} for i, d in enumerate(data)]
    except:
        pass
    return []

def src3_get_message_content(email: str, mail_id: int) -> Optional[Dict]:
    try:
        username = email.split("@")[0]
        r = requests.get(f"{SOURCE3_URL}/request/mail/id/{username}/format/json", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data and mail_id < len(data):
                d = data[mail_id]
                return {"from_mail": d.get("mail_from", ""), "subject": d.get("mail_subject", ""), "text": d.get("mail_text_only", "")}
    except:
        pass
    return None

def src3_delete_email(email: str) -> bool:
    try:
        username = email.split("@")[0]
        r = requests.delete(f"{SOURCE3_URL}/request/mail/id/{username}/format/json", timeout=10)
        return r.status_code == 200
    except:
        return False

# ================= الحصول على قائمة الدومينات (مع كاش محسن) =================
def get_all_domains() -> List[str]:
    global _cached_domains, _cached_domains_time
    
    current_time = time.time()
    if _cached_domains is not None and _cached_domains_time is not None:
        if current_time - _cached_domains_time < CACHE_DURATION:
            BOT_STATUS["cache_hits"] += 1
            return _cached_domains
    
    BOT_STATUS["cache_misses"] += 1
    
    try:
        src2_domains = src2_fetch_domains()
        all_domains = SOURCE1_DOMAINS.copy()
        for d in SOURCE3_DOMAINS:
            if d not in all_domains:
                all_domains.append(d)
        for d in src2_domains:
            if d not in all_domains:
                all_domains.append(d)
        
        _cached_domains = all_domains
        _cached_domains_time = current_time
        return all_domains
    except:
        if _cached_domains is not None:
            return _cached_domains
        return SOURCE1_DOMAINS + SOURCE2_STATIC_DOMAINS + SOURCE3_DOMAINS

def get_source_from_domain(domain: str) -> Optional[str]:
    if domain in SOURCE1_DOMAINS:
        return "src1"
    if domain in SOURCE2_STATIC_DOMAINS or domain in src2_fetch_domains():
        return "src2"
    if domain in SOURCE3_DOMAINS:
        return "src3"
    return None

# ================= وظائف إنشاء البريد المحسنة =================
def create_email_with_fallback(username: str, domain: str) -> Optional[str]:
    """إنشاء بريد مع إعادة محاولة تلقائية"""
    source = get_source_from_domain(domain)
    
    if source == "src1":
        email = src1_create_email(username, domain)
        if email:
            return email, "src1"
    elif source == "src2":
        email = src2_create_email(username, domain)
        if email:
            return email, "src2"
    elif source == "src3":
        email = src3_create_email(username, domain)
        if email:
            return email, "src3"
    
    # إذا فشل المصدر الرئيسي، نحاول مصدر آخر بنفس الدومين
    for alt_source in ["src1", "src2", "src3"]:
        if alt_source == source:
            continue
        if alt_source == "src1" and domain in SOURCE1_DOMAINS:
            email = src1_create_email(username, domain)
            if email:
                return email, "src1"
        elif alt_source == "src2" and (domain in SOURCE2_STATIC_DOMAINS or domain in src2_fetch_domains()):
            email = src2_create_email(username, domain)
            if email:
                return email, "src2"
        elif alt_source == "src3" and domain in SOURCE3_DOMAINS:
            email = src3_create_email(username, domain)
            if email:
                return email, "src3"
    
    return None, None

# ================= قاعدة البيانات المحسنة =================
DB_PATH = "mr_email_bot.db"

def init_db():
    with sqlite3.connect(DB_PATH, timeout=10) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT,
                phone TEXT,
                reg_date TEXT,
                lang TEXT DEFAULT 'en',
                banned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_emails_created INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
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
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                action TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def migrate_db():
    try:
        with sqlite3.connect(DB_PATH, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            for col, dtype in [('banned', 'INTEGER DEFAULT 0'), ('phone', 'TEXT'), ('name', 'TEXT'), 
                              ('username', 'TEXT'), ('reg_date', 'TEXT'), ('last_active', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
                              ('total_emails_created', 'INTEGER DEFAULT 0')]:
                if col not in columns:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {dtype}")
                    print(f"✅ تم إضافة عمود {col}")
            
            cursor.execute("PRAGMA table_info(emails)")
            emails_columns = [col[1] for col in cursor.fetchall()]
            if 'last_checked' not in emails_columns:
                cursor.execute("ALTER TABLE emails ADD COLUMN last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                print("✅ تم إضافة عمود last_checked")
            if 'is_active' not in emails_columns:
                cursor.execute("ALTER TABLE emails ADD COLUMN is_active INTEGER DEFAULT 1")
                print("✅ تم إضافة عمود is_active")
            
            cursor.execute("PRAGMA table_info(inbox)")
            inbox_columns = [col[1] for col in cursor.fetchall()]
            if 'is_read' not in inbox_columns:
                cursor.execute("ALTER TABLE inbox ADD COLUMN is_read INTEGER DEFAULT 0")
                print("✅ تم إضافة عمود is_read")
            
            # إنشاء جدول السجل
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER,
                    action TEXT,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            return True
    except Exception as e:
        print(f"⚠️ خطأ في تحديث قاعدة البيانات: {e}")
        return False

@contextmanager
def db_cursor():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10)
        conn.row_factory = sqlite3.Row
        yield conn.cursor()
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        log.error(f"Database error: {e}")
        BOT_STATUS["errors"] += 1
        BOT_STATUS["last_error"] = str(e)
        raise
    finally:
        if conn:
            conn.close()

# ================= دوال المستخدمين والتسجيل المحسنة =================
def is_user_registered(telegram_id: int) -> bool:
    with db_cursor() as cur:
        try:
            cur.execute("SELECT telegram_id FROM users WHERE telegram_id = ? AND banned = 0", (telegram_id,))
            return cur.fetchone() is not None
        except sqlite3.OperationalError:
            cur.execute("SELECT telegram_id FROM users WHERE telegram_id = ?", (telegram_id,))
            return cur.fetchone() is not None

def is_user_banned(telegram_id: int) -> bool:
    with db_cursor() as cur:
        try:
            cur.execute("SELECT banned FROM users WHERE telegram_id = ?", (telegram_id,))
            row = cur.fetchone()
            return row is not None and row["banned"] == 1
        except sqlite3.OperationalError:
            return False

def register_user(telegram_id: int, name: str, username: str, phone: str, reg_date: str):
    with db_cursor() as cur:
        try:
            cur.execute("SELECT banned FROM users WHERE telegram_id = ?", (telegram_id,))
            existing = cur.fetchone()
            
            if existing:
                cur.execute("""
                    UPDATE users 
                    SET name = ?, username = ?, phone = ?, reg_date = ?, last_active = CURRENT_TIMESTAMP
                    WHERE telegram_id = ?
                """, (name, username, phone, reg_date, telegram_id))
            else:
                cur.execute("""
                    INSERT INTO users (telegram_id, name, username, phone, reg_date, banned, last_active)
                    VALUES (?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
                """, (telegram_id, name, username, phone, reg_date))
            
            # تسجيل النشاط
            cur.execute("""
                INSERT INTO activity_log (telegram_id, action, details)
                VALUES (?, ?, ?)
            """, (telegram_id, "register", f"name: {name}, username: {username}"))
            
        except sqlite3.OperationalError:
            cur.execute("""
                INSERT OR REPLACE INTO users (telegram_id, name, username, phone, reg_date)
                VALUES (?, ?, ?, ?, ?)
            """, (telegram_id, name, username, phone, reg_date))
    update_bot_stats()

def get_user_data(telegram_id: int) -> Optional[Dict]:
    with db_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
        return dict(row) if row else None

def get_all_users() -> List[Dict]:
    with db_cursor() as cur:
        try:
            cur.execute("SELECT telegram_id, name, username, phone, reg_date, banned, total_emails_created FROM users ORDER BY reg_date DESC")
        except sqlite3.OperationalError:
            cur.execute("SELECT telegram_id, name, username, phone, reg_date FROM users ORDER BY reg_date DESC")
            users = []
            for row in cur.fetchall():
                u = dict(row)
                u["banned"] = 0
                u["total_emails_created"] = 0
                users.append(u)
            return users
        return [dict(row) for row in cur.fetchall()]

def get_active_users() -> List[Dict]:
    users = get_all_users()
    return [u for u in users if u.get("banned", 0) == 0 and u["telegram_id"] != DEV_ID]

def get_banned_users() -> List[Dict]:
    users = get_all_users()
    return [u for u in users if u.get("banned", 0) == 1 and u["telegram_id"] != DEV_ID]

def ban_user(telegram_id: int) -> bool:
    if telegram_id == DEV_ID:
        return False
    with db_cursor() as cur:
        try:
            cur.execute("UPDATE users SET banned = 1 WHERE telegram_id = ?", (telegram_id,))
            cur.execute("""
                INSERT INTO activity_log (telegram_id, action, details)
                VALUES (?, ?, ?)
            """, (telegram_id, "ban", "banned by developer"))
            return cur.rowcount > 0
        except sqlite3.OperationalError:
            return False

def unban_user(telegram_id: int) -> bool:
    with db_cursor() as cur:
        try:
            cur.execute("UPDATE users SET banned = 0 WHERE telegram_id = ?", (telegram_id,))
            cur.execute("""
                INSERT INTO activity_log (telegram_id, action, details)
                VALUES (?, ?, ?)
            """, (telegram_id, "unban", "unbanned by developer"))
            return cur.rowcount > 0
        except sqlite3.OperationalError:
            return False

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
        cur.execute("SELECT id, email, source FROM emails WHERE telegram_id = ? AND is_active = 1 ORDER BY created_at DESC", (telegram_id,))
        return [dict(row) for row in cur.fetchall()]

def add_user_email(telegram_id: int, email: str, source: str):
    with db_cursor() as cur:
        cur.execute("INSERT INTO emails (telegram_id, email, source) VALUES (?, ?, ?)", (telegram_id, email, source))
        cur.execute("UPDATE users SET total_emails_created = total_emails_created + 1, last_active = CURRENT_TIMESTAMP WHERE telegram_id = ?", (telegram_id,))
    update_bot_stats()

def remove_user_email(telegram_id: int, email: str):
    with db_cursor() as cur:
        cur.execute("UPDATE emails SET is_active = 0 WHERE telegram_id = ? AND email = ?", (telegram_id, email))
    update_bot_stats()

def save_inbox_message(telegram_id: int, email: str, source: str, from_email: str, subject: str, body: str, uid: str = None, mid: int = None):
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO inbox (telegram_id, email, source, from_email, subject, body, uid, mid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (telegram_id, email, source, from_email, subject, body, uid, mid))
    update_bot_stats()

def log_activity(telegram_id: int, action: str, details: str = ""):
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO activity_log (telegram_id, action, details)
            VALUES (?, ?, ?)
        """, (telegram_id, action, details))

# ================= أوامر البوت المحسنة =================
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# رسالة الحظر الثابتة
BAN_MESSAGE = """🫣 لقد تم حظرك من استخدام البوت

⤏͟͟͞͞༒⃝Ꭲ̴Ꭼ̴Ꭱ̴Ꮇ̴Ꮜ̴᙭̴♛Ꮎ̴Ꮩ̴Ꭼ̴Ꭱ̴Ꮮ̴Ꮎ̴Ꭱ̴Ꭰ̴༒⃟࿗⃝⏤͟͞➤⃟☠︎︎

إذا كنت تعتقد أن هذا خطأ، يرجى التواصل مع المطور:
@MR_Tails_YE"""

# ================= نصوص البوت المحسنة =================
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
        "welcome": f"🫣 مرحباً بك في بوت MR Email الأسطوري!\n⤏͟͟͞͞༒⃝Ꭲ̴Ꭼ̴Ꭱ̴Ꮇ̴Ꮜ̴᙭̴♛Ꮎ̴Ꮩ̴Ꭼ̴Ꭱ̴Ꮮ̴Ꮎ̴Ꭱ̴Ꭰ̴༒⃟࿗⃝⏤͟͞➤⃟☠︎︎\n\n🏆 *الإصدار 7.0 الأسطوري*\nبريد مؤقت خارق يدعم العديد من الدومينات.\nDEV: @MR_Tails_YE\n🔥 البوت لا ينام أبداً!",
        "need_phone": "📱 *يرجى تسجيل رقم هاتفك أولاً*\n\nاستخدم الأمر /phone لمشاركة رقم هاتفك والتحقق من حسابك.",
        "banned": BAN_MESSAGE,
        "phone_prompt": "📱 *يرجى مشاركة رقم هاتفك للتحقق من حسابك*\n\nاضغط على الزر أدناه لمشاركة رقم هاتفك.",
        "phone_saved": "✅ *تم حفظ رقم هاتفك بنجاح*\n\nالاسم: {name}\nاليوزر: {username}\nرقم الهاتف: {phone}\nتاريخ التسجيل: {date}\n\n✨ يمكنك الآن استخدام البوت!",
        "no_emails": "⚠️ ليس لديك أي بريد مؤقت بعد. استخدم /generate لإنشاء واحد.",
        "choose_domain": "🌐 *اختر الدومين لإنشاء بريد عشوائي:*",
        "choose_type": "🔢 *اختر نوع اسم البريد:*",
        "type_with_numbers": "🔢 مع أرقام (مثال: a1b2c3d4)",
        "type_without_numbers": "🔤 بدون أرقام (أحرف فقط)",
        "generate_success": "✅ *تم إنشاء بريد جديد:*\n`{email}`\n\nالمصدر: {source}",
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
        "custom_success": "✅ *تم إضافة البريد المخصص:*\n`{email}`\n\nالمصدر: {source}",
        "custom_invalid": "❌ بريد غير صالح أو دومين غير مدعوم.",
        "domains_list": "🌐 *جميع الدومينات المدعومة:*\n" + "\n".join([f"• `{d}`" for d in get_all_domains()]),
        "lang_changed": "🌐 تم تغيير اللغة إلى العربية.",
        "unknown": "❓ أمر غير معروف. استخدم القائمة الزرقاء.",
        "fetch_button": "📥 جلب",
        "delete_button": "🗑️ حذف",
        "back": "🔙 رجوع",
        "second_message": "✨ بريدك المؤقت الجديد هو: `{email}`\nأرسل /id لرؤية القائمة الكاملة.",
        "not_authorized": "⚠️ *غير مصرح*\n\nهذا الأمر متاح فقط للمطور.",
        "dev_panel": "👑 *لوحة تحكم المطور الأسطوري*\n\nمرحباً أيها المطور العظيم!\n\nاختر أحد الخيارات أدناه:",
        "dev_users_list": "👥 *قائمة المستخدمين*\n\nإجمالي المستخدمين: {total}\n\n{users_list}",
        "dev_no_users": "📭 لا يوجد مستخدمين مسجلين.",
        "dev_ban_success": "✅ تم حظر المستخدم `{user_id}` بنجاح.",
        "dev_ban_fail": "❌ فشل حظر المستخدم.",
        "dev_unban_success": "✅ تم إلغاء حظر المستخدم `{user_id}` بنجاح.",
        "dev_unban_fail": "❌ فشل إلغاء حظر المستخدم.",
        "dev_all_data": "📊 *جميع بيانات المستخدمين*\n\n{data}",
        "btn_users_count": "👥 عدد المستخدمين",
        "btn_ban_user": "🚫 حظر مستخدم",
        "btn_unban_user": "✅ إلغاء حظر مستخدم",
        "btn_all_data": "📊 جميع البيانات",
        "btn_back": "🔙 رجوع",
        "select_user": "👤 اختر المستخدم:",
        "confirm_ban": "⚠️ هل تريد حظر المستخدم {user_info}؟",
        "confirm_unban": "⚠️ هل تريد إلغاء حظر المستخدم {user_info}؟",
        "confirm_yes": "✅ نعم",
        "confirm_no": "❌ لا",
        "user_banned_success": "✅ تم حظر المستخدم {user_info} بنجاح",
        "user_unbanned_success": "✅ تم إلغاء حظر المستخدم {user_info} بنجاح",
        "user_details": "📋 *بيانات المستخدم*\n\n🆔 المعرف: {id}\n📛 الاسم: {name}\n🔖 اليوزر: {username}\n📞 الهاتف: {phone}\n📅 التسجيل: {date}\n📧 عدد البريدات: {total_emails}\n{'🚫 محظور' if banned else '✅ نشط'}",
        "click_message_button": "📨 اضغط على أي زر لعرض تفاصيل الرسالة",
        "view_message": "📄 رسالة من {from_addr}",
        "no_messages_inbox": "📭 لا توجد رسائل في هذا البريد",
        "dev_logs": "📋 *سجل النشاطات*\n\n{logs}",
        "dev_stats": "📊 *إحصائيات البوت*\n\n👥 المستخدمين: {users}\n📧 البريدات: {emails}\n💬 الرسائل: {messages}\n📅 مستخدمين اليوم: {daily}\n📡 عدد النقرات: {ping}\n🚀 الطلبات: {requests}\n💾 الكاش: {cache}\n⚠️ الأخطاء: {errors}",
        "btn_stats": "📊 الإحصائيات",
        "btn_logs": "📋 السجل",
        "btn_ping": "📡 النقرات",
        "btn_restart": "🔄 إعادة تشغيل",
        "user_banned": "🚫 تم حظرك من البوت",
    },
    "en": {
        "welcome": f"🫣 Welcome to MR Email Bot Legendary!\n⤏͟͟͞͞༒⃝Ꭲ̴Ꭼ̴Ꭱ̴Ꮇ̴Ꮜ̴᙭̴♛Ꮎ̴Ꮩ̴Ꭼ̴Ꭱ̴Ꮮ̴Ꮎ̴Ꭱ̴Ꭰ̴༒⃟࿗⃝⏤͟͞➤⃟☠︎︎\n\n🏆 *Version 7.0 Legendary*\nPowerful temporary email with many domains.\nDEV: @MR_Tails_YE\n🔥 The bot never sleeps!",
        "need_phone": "📱 *Please register your phone number first*\n\nUse /phone command to share your phone number and verify your account.",
        "banned": BAN_MESSAGE,
        "phone_prompt": "📱 *Please share your phone number to verify your account*\n\nTap the button below to share your phone number.",
        "phone_saved": "✅ *Your phone number has been saved successfully*\n\nName: {name}\nUsername: {username}\nPhone: {phone}\nRegistration Date: {date}\n\n✨ You can now use the bot!",
        "no_emails": "⚠️ You don't have any temporary email yet. Use /generate to create one.",
        "choose_domain": "🌐 *Choose domain to generate random email:*",
        "choose_type": "🔢 *Choose username type:*",
        "type_with_numbers": "🔢 With numbers (e.g., a1b2c3d4)",
        "type_without_numbers": "🔤 Without numbers (letters only)",
        "generate_success": "✅ *New email created:*\n`{email}`\n\nSource: {source}",
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
        "custom_success": "✅ *Custom email added:*\n`{email}`\n\nSource: {source}",
        "custom_invalid": "❌ Invalid email or domain not supported.",
        "domains_list": "🌐 *All Supported Domains:*\n" + "\n".join([f"• `{d}`" for d in get_all_domains()]),
        "lang_changed": "🌐 Language changed to English.",
        "unknown": "❓ Unknown command. Use blue menu.",
        "fetch_button": "📥 Fetch",
        "delete_button": "🗑️ Delete",
        "back": "🔙 Back",
        "second_message": "✨ Your new fake mail id is: `{email}`\nSend /id to see the full list.",
        "not_authorized": "⚠️ *Not Authorized*\n\nThis command is only available for the developer.",
        "dev_panel": "👑 *Legendary Developer Control Panel*\n\nWelcome, Great Developer!\n\nSelect an option below:",
        "dev_users_list": "👥 *Users List*\n\nTotal Users: {total}\n\n{users_list}",
        "dev_no_users": "📭 No registered users.",
        "dev_ban_success": "✅ User `{user_id}` has been banned successfully.",
        "dev_ban_fail": "❌ Failed to ban user.",
        "dev_unban_success": "✅ User `{user_id}` has been unbanned successfully.",
        "dev_unban_fail": "❌ Failed to unban user.",
        "dev_all_data": "📊 *All Users Data*\n\n{data}",
        "btn_users_count": "👥 Users Count",
        "btn_ban_user": "🚫 Ban User",
        "btn_unban_user": "✅ Unban User",
        "btn_all_data": "📊 All Data",
        "btn_back": "🔙 Back",
        "select_user": "👤 Select user:",
        "confirm_ban": "⚠️ Do you want to ban user {user_info}?",
        "confirm_unban": "⚠️ Do you want to unban user {user_info}?",
        "confirm_yes": "✅ Yes",
        "confirm_no": "❌ No",
        "user_banned_success": "✅ User {user_info} has been banned successfully",
        "user_unbanned_success": "✅ User {user_info} has been unbanned successfully",
        "user_details": "📋 *User Details*\n\n🆔 ID: {id}\n📛 Name: {name}\n🔖 Username: {username}\n📞 Phone: {phone}\n📅 Registered: {date}\n📧 Emails created: {total_emails}\n{'🚫 Banned' if banned else '✅ Active'}",
        "click_message_button": "📨 Click any button to view message details",
        "view_message": "📄 Message from {from_addr}",
        "no_messages_inbox": "📭 No messages in this inbox",
        "dev_logs": "📋 *Activity Logs*\n\n{logs}",
        "dev_stats": "📊 *Bot Statistics*\n\n👥 Users: {users}\n📧 Emails: {emails}\n💬 Messages: {messages}\n📅 Daily Users: {daily}\n📡 Pings: {ping}\n🚀 Requests: {requests}\n💾 Cache: {cache}\n⚠️ Errors: {errors}",
        "btn_stats": "📊 Statistics",
        "btn_logs": "📋 Logs",
        "btn_ping": "📡 Pings",
        "btn_restart": "🔄 Restart",
        "user_banned": "🚫 You have been banned from the bot",
    }
}

def get_text(telegram_id: int, key: str, **kwargs) -> str:
    lang = get_user_lang(telegram_id)
    text = TEXTS.get(lang, TEXTS["en"]).get(key, key)
    return text.format(**kwargs) if kwargs else text

# ================= أوامر البوت =================
async def set_commands(app: Application):
    user_commands = [
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
        BotCommand("stats", "📊 Bot statistics (Dev only)"),
    ]
    
    dev_extra_commands = [
        BotCommand("mydeveloper", "👑 Developer Control Panel"),
        BotCommand("monitor", "📊 Monitor Dashboard"),
        BotCommand("ping", "📡 Keep alive status"),
        BotCommand("logs", "📋 View activity logs"),
        BotCommand("restart", "🔄 Restart bot (Dev only)"),
        BotCommand("ban", "🚫 Ban user (Dev only)"),
        BotCommand("unban", "✅ Unban user (Dev only)"),
    ]
    
    try:
        dev_commands = user_commands + dev_extra_commands
        await app.bot.set_my_commands(dev_commands)
    except Exception as e:
        full_commands = user_commands + dev_extra_commands
        await app.bot.set_my_commands(full_commands)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    BOT_STATUS["total_requests"] += 1
    
    if is_user_banned(uid):
        await update.message.reply_text(BAN_MESSAGE, parse_mode="Markdown")
        return
    
    lang = get_user_lang(uid)
    user_data = get_user_data(uid)
    
    if user_data is None or lang not in ["ar", "en"]:
        keyboard = [
            [InlineKeyboardButton("العربية 🇸🇦", callback_data="first_lang_ar")],
            [InlineKeyboardButton("English 🇬🇧", callback_data="first_lang_en")],
        ]
        await update.message.reply_text(
            "🌐 Choose your language / اختر لغتك:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        user_lang_pending[uid] = True
        return
    
    if is_user_registered(uid):
        await update.message.reply_text(get_text(uid, "welcome"))
        log_activity(uid, "start", "User started bot")
    else:
        await update.message.reply_text(get_text(uid, "need_phone"))

async def phone_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    BOT_STATUS["total_requests"] += 1
    
    if is_user_banned(uid):
        await update.message.reply_text(BAN_MESSAGE, parse_mode="Markdown")
        return
    
    if not is_user_registered(uid):
        keyboard = [[KeyboardButton("📱 Share Phone Number", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(get_text(uid, "phone_prompt"), reply_markup=reply_markup)
    else:
        await update.message.reply_text(get_text(uid, "welcome"))

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    contact = update.message.contact
    BOT_STATUS["last_activity"] = datetime.now()
    BOT_STATUS["total_requests"] += 1
    
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
        
        remove_keyboard = ReplyKeyboardRemove()
        text = get_text(uid, "phone_saved", name=name, username=f"@{username}" if username != "No Username" else username, phone=phone, date=reg_date)
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=remove_keyboard)
        log_activity(uid, "phone_registered", f"phone: {phone}")

# ================= أوامر المطور المحسنة =================
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر لعرض حالة النقرات ومنع النوم"""
    uid = update.effective_user.id
    BOT_STATUS["total_requests"] += 1
    
    if uid != DEV_ID:
        await update.message.reply_text(get_text(uid, "not_authorized"), parse_mode="Markdown")
        return
    
    uptime_seconds = (datetime.now() - BOT_STATUS["start_time"]).total_seconds()
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    
    await update.message.reply_text(
        f"📡 *حالة نظام منع النوم الأسطوري*\n\n"
        f"⏱️ وقت التشغيل: {hours} ساعة {minutes} دقيقة\n"
        f"📊 عدد النقرات: {BOT_STATUS['ping_count']}\n"
        f"🟢 حالة البوت: {'مستيقظ' if BOT_STATUS['running'] else 'نائم'}\n"
        f"🔥 نظام منع النوم: نشط بشراسة\n"
        f"📊 حمل النظام: {BOT_STATUS['system_load']:.1f}%\n\n"
        f"⚡ كل {PING_INTERVAL} ثانية يتم النقر على السيرفر لمنعه من النوم!",
        parse_mode="Markdown"
    )

async def monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["total_requests"] += 1
    
    if uid != DEV_ID:
        await update.message.reply_text(get_text(uid, "not_authorized"), parse_mode="Markdown")
        return
    
    # جلب رابط الاستضافة الفعلي
    replit_url = os.environ.get("REPLIT_URL") or os.environ.get("REPLIT_DEV_DOMAIN") or ""
    if replit_url:
        monitor_link = f"https://{replit_url}"
    else:
        monitor_link = "http://localhost:8080"
    
    keyboard = [
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]
    ]
    
    await update.message.reply_text(
        f"📊 *لوحة مراقبة البوت الأسطوري*\n\n"
        f"🔗 *رابط لوحة التحكم:*\n{monitor_link}\n\n"
        f"🔗 *رابط فحص الصحة:*\n{monitor_link}/health\n\n"
        f"📡 عدد النقرات لمنع النوم: {BOT_STATUS['ping_count']}\n"
        f"⚡ الإصدار: 7.0 الأسطوري",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def mydeveloper(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["total_requests"] += 1
    
    if uid != DEV_ID:
        await update.message.reply_text(get_text(uid, "not_authorized"), parse_mode="Markdown")
        return
    
    keyboard = [
        [InlineKeyboardButton(get_text(uid, "btn_users_count"), callback_data="dev_users_count")],
        [InlineKeyboardButton(get_text(uid, "btn_ban_user"), callback_data="dev_ban_user")],
        [InlineKeyboardButton(get_text(uid, "btn_unban_user"), callback_data="dev_unban_user")],
        [InlineKeyboardButton(get_text(uid, "btn_all_data"), callback_data="dev_all_data")],
        [InlineKeyboardButton("📡 حالة النقرات", callback_data="dev_ping_status")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="dev_stats")],
        [InlineKeyboardButton("📋 السجل", callback_data="dev_logs")],
        [InlineKeyboardButton(get_text(uid, "btn_back"), callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(get_text(uid, "dev_panel"), reply_markup=reply_markup, parse_mode="Markdown")

async def dev_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["total_requests"] += 1
    
    if uid != DEV_ID:
        await update.message.reply_text(get_text(uid, "not_authorized"), parse_mode="Markdown")
        return
    
    uptime_seconds = (datetime.now() - BOT_STATUS["start_time"]).total_seconds()
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    
    text = get_text(uid, "dev_stats",
                   users=BOT_STATUS["total_users"],
                   emails=BOT_STATUS["total_emails"],
                   messages=BOT_STATUS["total_messages"],
                   daily=BOT_STATUS["daily_users"],
                   ping=BOT_STATUS["ping_count"],
                   requests=BOT_STATUS["total_requests"],
                   cache=f"{BOT_STATUS['cache_hits']}/{BOT_STATUS['cache_misses']}",
                   errors=BOT_STATUS["errors"])
    
    text += f"\n\n⏱️ وقت التشغيل: {hours} ساعة {minutes} دقيقة"
    text += f"\n📊 حمل النظام: {BOT_STATUS['system_load']:.1f}%"
    
    await update.message.reply_text(text, parse_mode="Markdown")

async def dev_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["total_requests"] += 1
    
    if uid != DEV_ID:
        await update.message.reply_text(get_text(uid, "not_authorized"), parse_mode="Markdown")
        return
    
    with db_cursor() as cur:
        cur.execute("SELECT telegram_id, action, details, timestamp FROM activity_log ORDER BY timestamp DESC LIMIT 50")
        logs = cur.fetchall()
    
    if not logs:
        await update.message.reply_text("📋 لا يوجد سجل نشاطات")
        return
    
    log_text = "📋 *آخر 50 نشاط*\n\n"
    for log_entry in logs:
        log_text += f"🕐 {log_entry['timestamp']}\n"
        log_text += f"👤 {log_entry['telegram_id']} - {log_entry['action']}\n"
        if log_entry['details']:
            log_text += f"📝 {log_entry['details']}\n"
        log_text += "─" * 20 + "\n"
    
    if len(log_text) > 4000:
        await update.message.reply_text(log_text[:4000] + "\n\n... (تم اختصار الباقي)")
    else:
        await update.message.reply_text(log_text, parse_mode="Markdown")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر حظر المستخدمين (للمطور فقط)"""
    uid = update.effective_user.id
    BOT_STATUS["total_requests"] += 1
    
    if uid != DEV_ID:
        await update.message.reply_text(get_text(uid, "not_authorized"), parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ استخدم: /ban <user_id>")
        return
    
    try:
        target_id = int(context.args[0])
        if target_id == DEV_ID:
            await update.message.reply_text("❌ لا يمكنك حظر نفسك!")
            return
        
        if ban_user(target_id):
            await update.message.reply_text(f"✅ تم حظر المستخدم `{target_id}` بنجاح", parse_mode="Markdown")
            try:
                await context.bot.send_message(target_id, get_text(target_id, "user_banned"), parse_mode="Markdown")
            except:
                pass
            log_activity(DEV_ID, "ban", f"banned user {target_id}")
        else:
            await update.message.reply_text("❌ فشل حظر المستخدم")
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال معرف صحيح")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر إلغاء حظر المستخدمين (للمطور فقط)"""
    uid = update.effective_user.id
    BOT_STATUS["total_requests"] += 1
    
    if uid != DEV_ID:
        await update.message.reply_text(get_text(uid, "not_authorized"), parse_mode="Markdown")
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ استخدم: /unban <user_id>")
        return
    
    try:
        target_id = int(context.args[0])
        if unban_user(target_id):
            await update.message.reply_text(f"✅ تم إلغاء حظر المستخدم `{target_id}` بنجاح", parse_mode="Markdown")
            try:
                await context.bot.send_message(target_id, "✅ تم إلغاء حظرك، يمكنك الآن استخدام البوت مرة أخرى")
            except:
                pass
            log_activity(DEV_ID, "unban", f"unbanned user {target_id}")
        else:
            await update.message.reply_text("❌ فشل إلغاء حظر المستخدم")
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال معرف صحيح")

async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إعادة تشغيل البوت (للمطور فقط)"""
    uid = update.effective_user.id
    BOT_STATUS["total_requests"] += 1
    
    if uid != DEV_ID:
        await update.message.reply_text(get_text(uid, "not_authorized"), parse_mode="Markdown")
        return
    
    await update.message.reply_text("🔄 جاري إعادة تشغيل البوت...")
    log_activity(DEV_ID, "restart", "Bot restarted")
    
    # إعادة تشغيل البوت
    os.execv(sys.executable, ['python'] + sys.argv)

# ================= أوامر البريد المؤقت المحسنة =================
async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    BOT_STATUS["total_requests"] += 1
    
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
    keyboard.append([InlineKeyboardButton(get_text(uid, "back"), callback_data="back_to_main")])
    await update.message.reply_text(
        get_text(uid, "choose_domain"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_emails(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    BOT_STATUS["total_requests"] += 1
    
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
    keyboard.append([InlineKeyboardButton(get_text(uid, "back"), callback_data="back_to_main")])
    await update.message.reply_text(
        get_text(uid, "emails_list"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_custom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    BOT_STATUS["total_requests"] += 1
    
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
    BOT_STATUS["total_requests"] += 1
    
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
    keyboard.append([InlineKeyboardButton(get_text(uid, "back"), callback_data="back_to_main")])
    await update.message.reply_text(
        get_text(uid, "fetch_select"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    BOT_STATUS["total_requests"] += 1
    
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
    keyboard.append([InlineKeyboardButton(get_text(uid, "back"), callback_data="back_to_main")])
    await update.message.reply_text(
        get_text(uid, "delete_select"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    BOT_STATUS["total_requests"] += 1
    
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
    
    messages = []
    if source == "src1":
        messages = src1_get_messages(email)
    elif source == "src2":
        messages = src2_get_messages(email)
    elif source == "src3":
        messages = src3_get_messages(email)
    
    if not messages:
        await update.message.reply_text(get_text(uid, "no_messages"))
        return
    
    content = None
    if source == "src1":
        content = src1_get_message_content(email, messages[0]["mail_id"])
    elif source == "src2":
        content = src2_get_message_content(messages[0]["uid"])
    elif source == "src3":
        content = src3_get_message_content(email, messages[0]["mail_id"])
    
    if content:
        text = get_text(uid, "message_detail",
                        from_addr=content.get("from_mail", content.get("f", "?")),
                        subject=content.get("subject", content.get("s", "?")),
                        body=content.get("text", "")[:1000])
        await update.message.reply_text(text, parse_mode="Markdown")
        log_activity(uid, "view_message", f"viewed message from {content.get('from_mail', content.get('f', '?'))}")

async def domains(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    BOT_STATUS["total_requests"] += 1
    
    if is_user_banned(uid):
        await update.message.reply_text(BAN_MESSAGE, parse_mode="Markdown")
        return
    
    text = get_text(uid, "domains_list")
    await update.message.reply_text(text, parse_mode="Markdown")

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    BOT_STATUS["total_requests"] += 1
    
    if is_user_banned(uid):
        await update.message.reply_text(BAN_MESSAGE, parse_mode="Markdown")
        return
    
    keyboard = [
        [InlineKeyboardButton("العربية 🇸🇦", callback_data="lang_ar")],
        [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")],
        [InlineKeyboardButton(get_text(uid, "back"), callback_data="back_to_main")]
    ]
    await update.message.reply_text("🌐 Choose language / اختر اللغة:", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= معالجة النصوص والأزرار المحسنة =================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["last_activity"] = datetime.now()
    BOT_STATUS["total_requests"] += 1
    
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
            email, source = create_email_with_fallback(username, domain)
            if email and source:
                add_user_email(uid, email, source)
                source_names = {"src1": "tempmail.plus", "src2": "inboxes.com", "src3": "temp-mail.org"}
                source_name = source_names.get(source, source)
                await update.message.reply_text(get_text(uid, "custom_success", email=email, source=source_name), parse_mode="Markdown")
                await update.message.reply_text(get_text(uid, "second_message", email=email), parse_mode="Markdown")
                log_activity(uid, "custom_email", f"created email: {email} from {source}")
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
    BOT_STATUS["total_requests"] += 1
    data = query.data
    
    # معالجة اختيار اللغة الأولية
    if data == "first_lang_ar":
        set_user_lang(uid, "ar")
        user_lang_pending.pop(uid, None)
        await query.edit_message_text(get_text(uid, "lang_changed"))
        await query.message.reply_text(get_text(uid, "need_phone"))
        return
    elif data == "first_lang_en":
        set_user_lang(uid, "en")
        user_lang_pending.pop(uid, None)
        await query.edit_message_text(get_text(uid, "lang_changed"))
        await query.message.reply_text(get_text(uid, "need_phone"))
        return
    
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
                [InlineKeyboardButton("📡 حالة النقرات", callback_data="dev_ping_status")],
                [InlineKeyboardButton("📊 الإحصائيات", callback_data="dev_stats")],
                [InlineKeyboardButton("📋 السجل", callback_data="dev_logs")],
                [InlineKeyboardButton(get_text(uid, "btn_back"), callback_data="back_main")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(get_text(uid, "dev_panel"), reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await query.edit_message_text(get_text(uid, "welcome"))
        return
    
    if data == "back_to_main":
        await query.edit_message_text(get_text(uid, "welcome"))
        return

    # ================= دوال المطور =================
    if uid == DEV_ID:
        # عرض حالة النقرات
        if data == "dev_ping_status":
            uptime_seconds = (datetime.now() - BOT_STATUS["start_time"]).total_seconds()
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            text = f"📡 *حالة نظام منع النوم الأسطوري*\n\n"
            text += f"⏱️ وقت التشغيل: {hours} ساعة {minutes} دقيقة\n"
            text += f"📊 عدد النقرات: {BOT_STATUS['ping_count']}\n"
            text += f"🟢 حالة البوت: {'مستيقظ' if BOT_STATUS['running'] else 'نائم'}\n"
            text += f"🔥 نظام منع النوم: نشط بشراسة\n"
            text += f"📊 حمل النظام: {BOT_STATUS['system_load']:.1f}%\n\n"
            text += f"⚡ كل {PING_INTERVAL} ثانية يتم النقر على السيرفر لمنعه من النوم!"
            
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
        
        if data == "dev_stats":
            uptime_seconds = (datetime.now() - BOT_STATUS["start_time"]).total_seconds()
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            text = get_text(uid, "dev_stats",
                           users=BOT_STATUS["total_users"],
                           emails=BOT_STATUS["total_emails"],
                           messages=BOT_STATUS["total_messages"],
                           daily=BOT_STATUS["daily_users"],
                           ping=BOT_STATUS["ping_count"],
                           requests=BOT_STATUS["total_requests"],
                           cache=f"{BOT_STATUS['cache_hits']}/{BOT_STATUS['cache_misses']}",
                           errors=BOT_STATUS["errors"])
            
            text += f"\n\n⏱️ وقت التشغيل: {hours} ساعة {minutes} دقيقة"
            text += f"\n📊 حمل النظام: {BOT_STATUS['system_load']:.1f}%"
            
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
        
        if data == "dev_logs":
            with db_cursor() as cur:
                cur.execute("SELECT telegram_id, action, details, timestamp FROM activity_log ORDER BY timestamp DESC LIMIT 50")
                logs = cur.fetchall()
            
            if not logs:
                await query.edit_message_text("📋 لا يوجد سجل نشاطات")
                return
            
            log_text = "📋 *آخر 50 نشاط*\n\n"
            for log_entry in logs:
                log_text += f"🕐 {log_entry['timestamp']}\n"
                log_text += f"👤 {log_entry['telegram_id']} - {log_entry['action']}\n"
                if log_entry['details']:
                    log_text += f"📝 {log_entry['details']}\n"
                log_text += "─" * 20 + "\n"
            
            if len(log_text) > 4000:
                await query.edit_message_text(log_text[:4000] + "\n\n... (تم اختصار الباقي)")
            else:
                await query.edit_message_text(log_text, parse_mode="Markdown")
            
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_main")]]
            await query.edit_message_text(log_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
        
        if data == "dev_users_count":
            users = get_all_users()
            if users:
                keyboard = []
                for u in users:
                    if u["telegram_id"] == DEV_ID:
                        continue
                    status = "✅" if u.get("banned", 0) == 0 else "🚫"
                    btn_text = f"{status} {u['telegram_id']} - {u.get('name', 'Unknown')}"
                    keyboard.append([InlineKeyboardButton(btn_text[:60], callback_data=f"user_detail_{u['telegram_id']}")])
                keyboard.append([InlineKeyboardButton(get_text(uid, "btn_back"), callback_data="back_main")])
                await query.edit_message_text(get_text(uid, "select_user"), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            else:
                await query.edit_message_text(get_text(uid, "dev_no_users"))
            return
        
        elif data == "dev_ban_user":
            active_users = get_active_users()
            if not active_users:
                await query.edit_message_text("📭 No active users to ban")
                return
            keyboard = []
            for u in active_users:
                if u["telegram_id"] == DEV_ID:
                    continue
                btn_text = f"✅ {u['telegram_id']} - {u.get('name', 'Unknown')}"
                keyboard.append([InlineKeyboardButton(btn_text[:60], callback_data=f"confirm_ban_{u['telegram_id']}")])
            keyboard.append([InlineKeyboardButton(get_text(uid, "btn_back"), callback_data="back_main")])
            await query.edit_message_text(get_text(uid, "select_user"), reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        elif data == "dev_unban_user":
            banned_users = get_banned_users()
            if not banned_users:
                await query.edit_message_text("📭 No banned users")
                return
            keyboard = []
            for u in banned_users:
                if u["telegram_id"] == DEV_ID:
                    continue
                btn_text = f"🚫 {u['telegram_id']} - {u.get('name', 'Unknown')}"
                keyboard.append([InlineKeyboardButton(btn_text[:60], callback_data=f"confirm_unban_{u['telegram_id']}")])
            keyboard.append([InlineKeyboardButton(get_text(uid, "btn_back"), callback_data="back_main")])
            await query.edit_message_text(get_text(uid, "select_user"), reply_markup=InlineKeyboardMarkup(keyboard))
            return
        
        elif data == "dev_all_data":
            users = get_all_users()
            if users:
                data_text = "📊 جميع بيانات المستخدمين\n\n"
                for u in users:
                    data_text += "═" * 20 + "\n"
                    data_text += f"🆔 المعرف: {u['telegram_id']}\n"
                    data_text += f"📛 الاسم: {u.get('name', 'غير معروف')}\n"
                    data_text += f"🔖 اليوزر: @{u.get('username', 'لا يوجد')}\n"
                    data_text += f"📞 الهاتف: {u.get('phone', 'غير مسجل')}\n"
                    data_text += f"📅 التسجيل: {u.get('reg_date', 'غير معروف')}\n"
                    data_text += f"📧 عدد البريدات: {u.get('total_emails_created', 0)}\n"
                    status = "🚫 محظور" if u.get('banned', 0) == 1 else "✅ نشط"
                    data_text += f"📌 الحالة: {status}\n\n"
                if len(data_text) > 4000:
                    await query.edit_message_text(data_text[:4000] + "\n\n... (تم اختصار الباقي)")
                else:
                    await query.edit_message_text(data_text)
            else:
                await query.edit_message_text("📭 لا يوجد مستخدمين مسجلين")
            return
        
        elif data.startswith("confirm_ban_"):
            target_id = int(data.split("_")[2])
            if target_id == DEV_ID:
                await query.edit_message_text("❌ You cannot ban yourself!")
                return
            user_data = get_user_data(target_id)
            if user_data:
                user_info = f"`{target_id}` - {user_data.get('name', 'Unknown')}"
                keyboard = [
                    [InlineKeyboardButton(get_text(uid, "confirm_yes"), callback_data=f"execute_ban_{target_id}")],
                    [InlineKeyboardButton(get_text(uid, "confirm_no"), callback_data="dev_ban_user")]
                ]
                await query.edit_message_text(get_text(uid, "confirm_ban", user_info=user_info), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
        
        elif data.startswith("execute_ban_"):
            target_id = int(data.split("_")[2])
            if target_id == DEV_ID:
                await query.edit_message_text("❌ You cannot ban yourself!")
                return
            user_data = get_user_data(target_id)
            if user_data and ban_user(target_id):
                user_info = f"`{target_id}` - {user_data.get('name', 'Unknown')}"
                await query.edit_message_text(get_text(uid, "user_banned_success", user_info=user_info), parse_mode="Markdown")
                try: await context.bot.send_message(target_id, BAN_MESSAGE, parse_mode="Markdown")
                except: pass
                log_activity(DEV_ID, "ban", f"banned user {target_id}")
            else:
                await query.edit_message_text(get_text(uid, "dev_ban_fail"))
            return
        
        elif data.startswith("confirm_unban_"):
            target_id = int(data.split("_")[2])
            user_data = get_user_data(target_id)
            if user_data:
                user_info = f"`{target_id}` - {user_data.get('name', 'Unknown')}"
                keyboard = [
                    [InlineKeyboardButton(get_text(uid, "confirm_yes"), callback_data=f"execute_unban_{target_id}")],
                    [InlineKeyboardButton(get_text(uid, "confirm_no"), callback_data="dev_unban_user")]
                ]
                await query.edit_message_text(get_text(uid, "confirm_unban", user_info=user_info), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return
        
        elif data.startswith("execute_unban_"):
            target_id = int(data.split("_")[2])
            user_data = get_user_data(target_id)
            if user_data and unban_user(target_id):
                user_info = f"`{target_id}` - {user_data.get('name', 'Unknown')}"
                await query.edit_message_text(get_text(uid, "user_unbanned_success", user_info=user_info), parse_mode="Markdown")
                try: await context.bot.send_message(target_id, "✅ تم إلغاء حظرك، يمكنك الآن استخدام البوت مرة أخرى")
                except: pass
                log_activity(DEV_ID, "unban", f"unbanned user {target_id}")
            else:
                await query.edit_message_text(get_text(uid, "dev_unban_fail"))
            return
        
        elif data.startswith("user_detail_"):
            target_id = int(data.split("_")[2])
            user_data = get_user_data(target_id)
            if user_data:
                banned = user_data.get("banned", 0) == 1
                text = get_text(uid, "user_details", 
                               id=target_id, 
                               name=user_data.get("name", "Unknown"),
                               username=user_data.get("username", "No Username"),
                               phone=user_data.get("phone", "No Phone"),
                               date=user_data.get("reg_date", "Unknown"),
                               total_emails=user_data.get("total_emails_created", 0),
                               banned=banned)
                keyboard = [[InlineKeyboardButton(get_text(uid, "btn_back"), callback_data="dev_users_count")]]
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
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
            [InlineKeyboardButton(get_text(uid, "back"), callback_data="back_to_main")]
        ]
        await query.edit_message_text(get_text(uid, "choose_type"), reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if data == "gen_with_numbers":
        domain = context.user_data.get("selected_domain")
        if not domain: return
        username = random_username(8, with_numbers=True)
        email, source = create_email_with_fallback(username, domain)
        if email and source:
            add_user_email(uid, email, source)
            source_names = {"src1": "tempmail.plus", "src2": "inboxes.com", "src3": "temp-mail.org"}
            source_name = source_names.get(source, source)
            await query.edit_message_text(get_text(uid, "generate_success", email=email, source=source_name), parse_mode="Markdown")
            await query.message.reply_text(get_text(uid, "second_message", email=email), parse_mode="Markdown")
            log_activity(uid, "generate_email", f"created email: {email} from {source}")
        else:
            await query.edit_message_text(get_text(uid, "generate_fail"))
        return

    if data == "gen_without_numbers":
        domain = context.user_data.get("selected_domain")
        if not domain: return
        username = random_username(8, with_numbers=False)
        email, source = create_email_with_fallback(username, domain)
        if email and source:
            add_user_email(uid, email, source)
            source_names = {"src1": "tempmail.plus", "src2": "inboxes.com", "src3": "temp-mail.org"}
            source_name = source_names.get(source, source)
            await query.edit_message_text(get_text(uid, "generate_success", email=email, source=source_name), parse_mode="Markdown")
            await query.message.reply_text(get_text(uid, "second_message", email=email), parse_mode="Markdown")
            log_activity(uid, "generate_email", f"created email: {email} from {source}")
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
                
                messages = []
                if source == "src1":
                    messages = src1_get_messages(email)
                elif source == "src2":
                    messages = src2_get_messages(email)
                elif source == "src3":
                    messages = src3_get_messages(email)
                
                if not messages:
                    await query.edit_message_text(get_text(uid, "inbox_empty", email=email), parse_mode="Markdown")
                    return
                
                keyboard = []
                for i, m in enumerate(messages[:10]):
                    from_addr = m.get("from_mail", m.get("f", "?"))
                    subject = m.get("subject", m.get("s", "?"))
                    btn_text = f"📨 {subject[:30]} - {from_addr[:20]}"
                    if source == "src1":
                        keyboard.append([InlineKeyboardButton(btn_text[:60], callback_data=f"msg1_{m['mail_id']}_{email}")])
                    elif source == "src2":
                        keyboard.append([InlineKeyboardButton(btn_text[:60], callback_data=f"msg2_{m['uid']}_{email}")])
                    elif source == "src3":
                        keyboard.append([InlineKeyboardButton(btn_text[:60], callback_data=f"msg3_{i}_{email}")])
                
                keyboard.append([InlineKeyboardButton(get_text(uid, "back"), callback_data="back_to_main")])
                await query.edit_message_text(get_text(uid, "click_message_button"), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                return

    if data.startswith("msg1_"):
        parts = data.split("_")
        if len(parts) >= 3:
            mail_id = int(parts[1])
            email = "_".join(parts[2:])
            content = src1_get_message_content(email, mail_id)
            if content:
                text = get_text(uid, "message_detail", from_addr=content.get("from_mail", "?"), subject=content.get("subject", "?"), body=content.get("text", "")[:1000])
                keyboard = [[InlineKeyboardButton(get_text(uid, "back"), callback_data="back_to_main")]]
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                log_activity(uid, "view_message", f"viewed message from {content.get('from_mail', '?')}")
        return
    
    if data.startswith("msg2_"):
        parts = data.split("_")
        if len(parts) >= 3:
            uid_msg = parts[1]
            email = "_".join(parts[2:])
            content = src2_get_message_content(uid_msg)
            if content:
                text = get_text(uid, "message_detail", from_addr=content.get("f", "?"), subject=content.get("s", "?"), body=content.get("text", "")[:1000])
                keyboard = [[InlineKeyboardButton(get_text(uid, "back"), callback_data="back_to_main")]]
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                log_activity(uid, "view_message", f"viewed message from {content.get('f', '?')}")
        return
    
    if data.startswith("msg3_"):
        parts = data.split("_")
        if len(parts) >= 3:
            msg_index = int(parts[1])
            email = "_".join(parts[2:])
            content = src3_get_message_content(email, msg_index)
            if content:
                text = get_text(uid, "message_detail", from_addr=content.get("from_mail", "?"), subject=content.get("subject", "?"), body=content.get("text", "")[:1000])
                keyboard = [[InlineKeyboardButton(get_text(uid, "back"), callback_data="back_to_main")]]
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                log_activity(uid, "view_message", f"viewed message from {content.get('from_mail', '?')}")
        return

    if data.startswith("del_"):
        eid = int(data.split("_")[1])
        for e in emails_info:
            if e["id"] == eid:
                email = e["email"]
                source = e["source"]
                success = False
                if source == "src1":
                    success = src1_delete_email(email)
                elif source == "src2":
                    success = src2_delete_email(email)
                elif source == "src3":
                    success = src3_delete_email(email)
                
                if success:
                    remove_user_email(uid, email)
                    await query.edit_message_text(get_text(uid, "delete_success", email=email), parse_mode="Markdown")
                    log_activity(uid, "delete_email", f"deleted email: {email}")
                else:
                    await query.edit_message_text(get_text(uid, "delete_fail"))
                return

# ================= معالجة رسائل المطور (نصي) =================
async def handle_dev_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    BOT_STATUS["total_requests"] += 1
    if uid != DEV_ID: return
    if context.user_data.get("dev_action"):
        action = context.user_data["dev_action"]
        text = update.message.text.strip()
        try: target_id = int(text)
        except ValueError: return
        
        if action == "ban" and target_id != DEV_ID:
            if ban_user(target_id):
                await update.message.reply_text(f"✅ User `{target_id}` banned")
                try: await context.bot.send_message(target_id, BAN_MESSAGE, parse_mode="Markdown")
                except: pass
                log_activity(DEV_ID, "ban", f"banned user {target_id}")
        elif action == "unban":
            if unban_user(target_id):
                await update.message.reply_text(f"✅ User `{target_id}` unbanned")
                try: await context.bot.send_message(target_id, "✅ تم إلغاء حظرك، يمكنك الآن استخدام البوت مرة أخرى")
                except: pass
                log_activity(DEV_ID, "unban", f"unbanned user {target_id}")
        context.user_data["dev_action"] = None

# ================= التشغيل =================
def main():
    print(f"""
{P}╔══════════════════════════════════════════════════════════════╗
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
{Y}                       MR EMAIL BOT v7.0                      ║
{Y}               LEGENDARY EDITION + NEVER SLEEP                ║
{P}╚══════════════════════════════════════════════════════════════╝{RESET}""")
    
    print(f"{C}╔══════════════════════════════════════════════════════════════╗")
    print(f"{C}║ {W}DEV      : {Y}@MR_Tails_YE                                              {C}║")
    print(f"{C}║ {W}TARGET   : {Y}TEMPORARY EMAIL + {len(get_all_domains())} DOMAINS + USER SYSTEM         {C}║")
    print(f"{C}║ {W}ENGINE   : {Y}STEALTH MODE + HIDDEN SOURCES + LEGENDARY UI           {C}║")
    print(f"{C}║ {W}MONITOR  : {Y}http://localhost:8080                                      {C}║")
    print(f"{C}║ {W}HEALTH   : {Y}http://localhost:8080/health                               {C}║")
    print(f"{C}║ {W}SLEEP    : {R}NEVER! 🔥 نظام منع النوم الأسطوري مفعل                      {C}║")
    print(f"{C}║ {W}VERSION  : {G}7.0 LEGENDARY 🏆                                            {C}║")
    print(f"{C}╚══════════════════════════════════════════════════════════════╝{RESET}\n")

    # التحقق من قاعدة البيانات
    if os.path.exists(DB_PATH):
        try:
            with sqlite3.connect(DB_PATH, timeout=10) as conn:
                conn.execute("SELECT lang FROM users LIMIT 1")
                print(f"{G}✅ قاعدة البيانات موجودة، يتم التحقق من هيكلها...{RESET}")
                migrate_db()
        except sqlite3.OperationalError:
            print(f"{Y}⚠️ قاعدة البيانات قديمة جداً، سيتم إنشاء جديدة.{RESET}")
            os.remove(DB_PATH)
            init_db()
    else:
        init_db()
    
    update_bot_stats()
    
    # تشغيل نظام منع النوم الأسطوري 🔥
    keep_alive_thread = threading.Thread(target=keep_alive_ping, daemon=True)
    keep_alive_thread.start()
    print(f"{G}🔥 نظام منع النوم الأسطوري تم تفعيله! سيتم النقر كل {PING_INTERVAL} ثانية{RESET}")

    # تشغيل خادم المراقبة
    monitor_thread = threading.Thread(target=run_monitor_server, daemon=True)
    monitor_thread.start()
    print(f"{G}✅ Monitor server started on http://localhost:8080{RESET}")
    
    # تشغيل فحص APIs
    api_check_thread = threading.Thread(target=check_apis_status, daemon=True)
    api_check_thread.start()
    print(f"{G}✅ API monitoring started (3 sources){RESET}")

    # إنشاء التطبيق
    app = Application.builder().token(TOKEN).build()
    app.post_init = set_commands

    # أوامر البوت
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
    
    # أوامر المطور المحسنة
    app.add_handler(CommandHandler("mydeveloper", mydeveloper))
    app.add_handler(CommandHandler("monitor", monitor))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("stats", dev_stats))
    app.add_handler(CommandHandler("logs", dev_logs))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("unban", unban_command))
    app.add_handler(CommandHandler("restart", restart_command))
    
    # معالجات إضافية
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.TEXT & filters.COMMAND, handle_dev_text))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print(f"{G}✅ MR Email Bot v7.0 Legendary is running! 🏆{RESET}")
    print(f"{C}👑 Developer commands: /mydeveloper , /monitor , /ping , /stats , /logs{RESET}")
    print(f"{C}🔧 Admin commands: /ban , /unban , /restart{RESET}")
    print(f"{C}📊 Monitor URL: http://localhost:8080{RESET}")
    print(f"{Y}💡 Users must register with /phone first{RESET}")
    print(f"{R}🔥 نظام منع النوم الأسطوري يعمل! البوت لن ينام أبداً 😈{RESET}")
    print(f"{P}🏆 الإصدار 7.0 الأسطوري - يتفوق التصور بالقوة والعظمة!{RESET}\n")
    
    app.run_polling()

if __name__ == "__main__":
    import sys
    main()
