#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت التفريغ الصوتي الاحترافي
Whisper AI Transcription Bot

نظام كامل مع خطة مجانية ومميزة
"""

import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
import json
import whisper
from telebot import TeleBot, types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import tempfile
import subprocess
from flask import Flask
import threading

# ===================================
# الإعدادات - Configuration
# ===================================

# معلومات البوت والمسؤول
TELEGRAM_TOKEN = "8464546031:AAH5Asw0jSspFzITgchZ_BQYcPbFgb2xn_s" 
ADMIN_USER_ID = 969596959695  # معرف التليجرام الخاص بك (رقم فقط)

# إعدادات نموذج Whisper
WHISPER_MODEL = "tiny"  # الخيارات: tiny, base, small, medium, large

# معلومات الحساب البنكي للدفع
BANK_INFO = {
    'bank_name': 'Bank of Alexandria',
    'account_name': 'EZZAT HOSNI MOHAMED',
    'account_number': '112012126002',
    'iban': 'EGEG120005101200000112012126002',
    'phone': '0193351307',  # فودافون كاش / إنستاباي
    'currency': 'USD',
    'dollar_rate': 50,  # سعر الدولار مقابل الجنيه
}

# خطط الاشتراك
SUBSCRIPTION_PLANS = {
    'free': {
        'name': 'الخطة المجانية',
        'name_en': 'Free Plan',
        'price': 0,
        'price_usd': 0,
        'duration_days': 1,  # يوم واحد (يتجدد يومياً)
        'daily_limit': 3,  # 3 محاولات فقط يومياً
        'max_duration': 300,  # 5 دقائق (300 ثانية)
        'formats': ['txt', 'srt'],
        'timestamps': True,
        'priority': False,
        'features': [
            '3 تفريغات يومياً',
            'حتى 5 دقائق لكل تسجيل',
            'تصدير TXT + SRT',
            'طوابع زمنية',
            'دعم فني عادي'
        ]
    },
    'premium': {
        'name': 'الخطة المميزة',
        'name_en': 'Premium Plan',
        'price': 500,  # 10 دولار × 50 = 500 جنيه
        'price_usd': 10,
        'duration_days': 30,  # شهر كامل
        'daily_limit': 999999,  # غير محدود
        'max_duration': 999999,  # غير محدود
        'formats': ['txt', 'srt'],
        'timestamps': True,
        'priority': True,
        'features': [
            '✨ تفريغات غير محدودة يومياً',
            '✨ بدون حد لمدة التسجيل',
            '✨ تصدير TXT + SRT',
            '✨ طوابع زمنية متقدمة',
            '✨ معالجة فورية وأولوية',
            '✨ دعم فني مميز 24/7',
            '✨ جودة تفريغ عالية',
            '✨ بدون إعلانات',
            '✨ تحديثات مجانية'
        ]
    }
}

# نظام الإحالات
REFERRAL_REWARDS = {
    'free_days': 7,  # 7 أيام مجانية لكل إحالة ناجحة
    'discount_percent': 10  # خصم 10% للمُحيل
}

# الكوبونات
COUPONS = {
    'WELCOME10': {'discount': 10, 'uses': 100, 'used': 0, 'description': 'خصم 10% للمستخدمين الجدد'},
    'FIRST20': {'discount': 20, 'uses': 50, 'used': 0, 'description': 'خصم 20% على الاشتراك الأول'},
    'NEWYEAR25': {'discount': 25, 'uses': 200, 'used': 0, 'description': 'خصم 25% بمناسبة العام الجديد'},
    'VIP30': {'discount': 30, 'uses': 20, 'used': 0, 'description': 'خصم 30% للعملاء المميزين'}
}

# الإشعارات الافتراضية
DEFAULT_NOTIFICATIONS = {
    'daily_limit_reminder': True,
    'subscription_expiry': True,
    'new_features': True,
    'special_offers': True
}

# إعدادات قاعدة البيانات
DB_FILE = 'users_db.json'

# معلومات الدعم والتواصل
SUPPORT_USERNAME = "YourSupportUsername"  # يوزر حساب الدعم (بدون @)
SUPPORT_EMAIL = "support@example.com"

# ===================================
# نهاية الإعدادات
# ===================================

# إعداد Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# التحقق من الإعدادات الأساسية
if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "ضع_توكن_البوت_هنا":
    logger.error("❌ يرجى تعيين TELEGRAM_TOKEN في الإعدادات")
    print("\n" + "="*50)
    print("❌ خطأ: لم يتم تعيين توكن البوت!")
    print("="*50)
    print("يرجى:")
    print("1. فتح الملف bot.py")
    print("2. البحث عن TELEGRAM_TOKEN")
    print("3. استبدال 'ضع_توكن_البوت_هنا' بتوكن البوت من @BotFather")
    print("="*50 + "\n")
    exit(1)

if not ADMIN_USER_ID or ADMIN_USER_ID == 123456789:
    logger.error("❌ يرجى تعيين ADMIN_USER_ID في الإعدادات")
    print("\n" + "="*50)
    print("❌ خطأ: لم يتم تعيين معرف المسؤول!")
    print("="*50)
    print("يرجى:")
    print("1. فتح الملف bot.py")
    print("2. البحث عن ADMIN_USER_ID")
    print("3. استبدال 123456789 بمعرف التليجرام الخاص بك")
    print("4. للحصول على معرفك، تحدث مع @userinfobot")
    print("="*50 + "\n")
    exit(1)

# إنشاء البوت
bot = TeleBot(TELEGRAM_TOKEN)

# تحميل نموذج Whisper
logger.info(f"🔄 جاري تحميل نموذج Whisper: {WHISPER_MODEL}")
print(f"⏳ جاري تحميل نموذج Whisper ({WHISPER_MODEL})... قد يستغرق بضع دقائق...")
try:
    whisper_model = whisper.load_model(WHISPER_MODEL)
    logger.info(f"✅ تم تحميل نموذج Whisper: {WHISPER_MODEL}")
    print(f"✅ تم تحميل نموذج Whisper بنجاح!")
except Exception as e:
    logger.error(f"❌ فشل تحميل نموذج Whisper: {e}")
    print(f"❌ خطأ في تحميل Whisper: {e}")
    exit(1)

# قاموس لحفظ بيانات المستخدمين
user_data = {}

# ===================================
# Flask App للحفاظ على البوت نشطاً
# ===================================

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    """الصفحة الرئيسية"""
    return """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>بوت التفريغ الصوتي</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-align: center;
                padding: 50px;
                margin: 0;
            }}
            .container {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                max-width: 600px;
                margin: 0 auto;
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            }}
            h1 {{
                font-size: 3em;
                margin: 20px 0;
            }}
            .status {{
                background: #10b981;
                padding: 15px 30px;
                border-radius: 50px;
                display: inline-block;
                margin: 20px 0;
                font-weight: bold;
                font-size: 1.2em;
            }}
            .info {{
                background: rgba(255, 255, 255, 0.2);
                padding: 20px;
                border-radius: 15px;
                margin: 20px 0;
            }}
            .stats {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-top: 20px;
            }}
            .stat-box {{
                background: rgba(255, 255, 255, 0.15);
                padding: 15px;
                border-radius: 10px;
            }}
            .stat-number {{
                font-size: 2em;
                font-weight: bold;
                color: #fbbf24;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎤 بوت التفريغ الصوتي</h1>
            <div class="status">
                ✅ البوت يعمل بنجاح!
            </div>
            <div class="info">
                <p><strong>📅 التاريخ:</strong> {}</p>
                <p><strong>🤖 النموذج:</strong> Whisper {}</p>
                <p><strong>🌐 الحالة:</strong> Online 24/7</p>
            </div>
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-number">{}</div>
                    <div>المستخدمين</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">99.9%</div>
                    <div>Uptime</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """.format(
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        WHISPER_MODEL.upper(),
        len(user_data)
    )

@flask_app.route('/ping')
def ping():
    """نقطة نهاية للـ UptimeRobot"""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "uptime": "running"
    }, 200

@flask_app.route('/health')
def health():
    """فحص صحة البوت"""
    return {
        "status": "healthy",
        "bot": "online",
        "users": len(user_data),
        "model": WHISPER_MODEL,
        "timestamp": datetime.now().isoformat()
    }, 200

@flask_app.route('/stats')
def stats():
    """إحصائيات البوت"""
    total_users = len(user_data)
    free_users = sum(1 for u in user_data.values() if u.get('plan') == 'free')
    premium_users = sum(1 for u in user_data.values() if u.get('plan') == 'premium')
    total_transcriptions = sum(u.get('total_transcriptions', 0) for u in user_data.values())
    
    return {
        "total_users": total_users,
        "free_users": free_users,
        "premium_users": premium_users,
        "total_transcriptions": total_transcriptions,
        "timestamp": datetime.now().isoformat()
    }, 200

def run_flask():
    """تشغيل Flask في خيط منفصل"""
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ===================================
# دوال قاعدة البيانات
# ===================================

def load_database():
    """تحميل قاعدة البيانات من الملف"""
    global user_data
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                user_data = json.load(f)
                # تحويل التواريخ من نص إلى datetime
                for user_id in user_data:
                    if 'subscription_end' in user_data[user_id]:
                        user_data[user_id]['subscription_end'] = datetime.fromisoformat(
                            user_data[user_id]['subscription_end']
                        )
                    if 'last_reset' in user_data[user_id]:
                        user_data[user_id]['last_reset'] = datetime.fromisoformat(
                            user_data[user_id]['last_reset']
                        )
            logger.info(f"✅ تم تحميل قاعدة البيانات: {len(user_data)} مستخدم")
        else:
            logger.info("📝 إنشاء قاعدة بيانات جديدة")
            user_data = {}
    except Exception as e:
        logger.error(f"❌ خطأ في تحميل قاعدة البيانات: {e}")
        user_data = {}

def save_database():
    """حفظ قاعدة البيانات إلى الملف"""
    try:
        # تحويل datetime إلى نص قبل الحفظ
        data_to_save = {}
        for user_id, data in user_data.items():
            data_to_save[user_id] = data.copy()
            if 'subscription_end' in data_to_save[user_id]:
                data_to_save[user_id]['subscription_end'] = data_to_save[user_id]['subscription_end'].isoformat()
            if 'last_reset' in data_to_save[user_id]:
                data_to_save[user_id]['last_reset'] = data_to_save[user_id]['last_reset'].isoformat()
        
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"❌ خطأ في حفظ قاعدة البيانات: {e}")

def get_user_info(user_id):
    """الحصول على معلومات المستخدم"""
    user_id = str(user_id)
    if user_id not in user_data:
        # إنشاء مستخدم جديد بالخطة المجانية
        user_data[user_id] = {
            'plan': 'free',
            'subscription_end': datetime.now() + timedelta(days=SUBSCRIPTION_PLANS['free']['duration_days']),
            'daily_usage': 0,
            'last_reset': datetime.now(),
            'total_transcriptions': 0,
            'pending_payment': None,
            'registration_date': datetime.now().isoformat()
        }
        save_database()
        logger.info(f"👤 مستخدم جديد: {user_id}")
    
    # إعادة تعيين الاستخدام اليومي إذا مر يوم
    user = user_data[user_id]
    if (datetime.now() - user['last_reset']).days >= 1:
        user['daily_usage'] = 0
        user['last_reset'] = datetime.now()
        save_database()
    
    return user

def is_subscription_active(user_id):
    """التحقق من نشاط الاشتراك"""
    user = get_user_info(user_id)
    return datetime.now() < user['subscription_end']

def can_transcribe(user_id, audio_duration):
    """التحقق من إمكانية التفريغ"""
    user = get_user_info(user_id)
    plan = SUBSCRIPTION_PLANS[user['plan']]
    
    # التحقق من نشاط الاشتراك
    if not is_subscription_active(user_id):
        return False, "⚠️ انتهت صلاحية اشتراكك! قم بالتجديد للمتابعة."
    
    # للخطة المميزة - كل شيء مسموح
    if user['plan'] == 'premium':
        return True, None
    
    # للخطة المجانية - التحقق من الحدود
    if user['plan'] == 'free':
        # التحقق من الحد اليومي
        if user['daily_usage'] >= plan['daily_limit']:
            egp_price = SUBSCRIPTION_PLANS['premium']['price']
            
            return False, (
                f"⚠️ **انتهت محاولاتك اليومية!**\n\n"
                f"لقد استخدمت {plan['daily_limit']}/{plan['daily_limit']} من محاولاتك المجانية.\n\n"
                f"🔄 **الخيارات:**\n"
                f"• انتظر حتى الغد (تتجدد تلقائياً)\n"
                f"• أو قم بالترقية للمميزة!\n\n"
                f"💎 **الخطة المميزة:**\n"
                f"✨ تفريغات غير محدودة\n"
                f"✨ بدون حد للمدة\n"
                f"✨ فقط 10$ ({egp_price} جنيه)\n\n"
                f"اضغط /upgrade للترقية الآن!"
            )
        
        # التحقق من مدة التسجيل
        if audio_duration > plan['max_duration']:
            max_mins = plan['max_duration'] // 60
            return False, (
                f"⚠️ **مدة التسجيل طويلة جداً!**\n\n"
                f"التسجيل: {audio_duration // 60} دقيقة\n"
                f"المسموح: {max_mins} دقائق\n\n"
                f"💎 **الحل:** قم بالترقية للخطة المميزة!\n"
                f"✨ بدون حد للمدة - فرّغ ساعات كاملة!\n\n"
                f"اضغط /upgrade للترقية"
            )
    
    return True, None

def create_main_menu():
    """إنشاء القائمة الرئيسية"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton('🎤 تفريغ صوتي'),
        KeyboardButton('📊 اشتراكي'),
        KeyboardButton('💎 الترقية'),
        KeyboardButton('❓ المساعدة')
    )
    return markup

def generate_referral_code(user_id):
    """توليد كود إحالة فريد"""
    import hashlib
    code = hashlib.md5(f"{user_id}{TELEGRAM_TOKEN}".encode()).hexdigest()[:8]
    return f"REF{code.upper()}"

def get_referral_link(user_id):
    """الحصول على رابط الإحالة"""
    code = generate_referral_code(user_id)
    bot_username = bot.get_me().username
    return f"https://t.me/{bot_username}?start={code}"

# ===================================
# معالجات الأوامر
# ===================================

@bot.message_handler(commands=['start'])
def start_command(message):
    """معالج أمر البداية"""
    user_id = message.from_user.id
    
    # التحقق من كود الإحالة
    if len(message.text.split()) > 1:
        ref_code = message.text.split()[1]
        if ref_code.startswith('REF'):
            # البحث عن المُحيل
            for uid, udata in user_data.items():
                if generate_referral_code(uid) == ref_code and uid != str(user_id):
                    # تسجيل الإحالة
                    if 'referred_by' not in get_user_info(user_id):
                        user_data[str(user_id)]['referred_by'] = uid
                        user_data[uid]['referrals'] = user_data[uid].get('referrals', 0) + 1
                        save_database()
                        
                        # إشعار المُحيل
                        try:
                            bot.send_message(int(uid), 
                                           f"🎉 مبروك! شخص استخدم رابط الإحالة الخاص بك!\n"
                                           f"عند اشتراكه ستحصل على {REFERRAL_REWARDS['free_days']} يوم مجاني")
                        except:
                            pass
                    break
    
    user = get_user_info(user_id)
    
    welcome_text = f"""
👋 مرحباً {message.from_user.first_name}!

🎤 **بوت التفريغ الصوتي الاحترافي**

✨ حوّل تسجيلاتك الصوتية إلى نص مكتوب بدقة عالية باستخدام تقنية Whisper AI!

📋 **خطتك الحالية:** {SUBSCRIPTION_PLANS[user['plan']]['name']}

💡 استخدم الأزرار بالأسفل للتنقل:
• 🎤 تفريغ صوتي - لإرسال تسجيل
• 📊 اشتراكي - لمعرفة تفاصيل خطتك
• 💎 الترقية - للترقية للخطة المميزة
• ❓ المساعدة - للمساعدة والدعم
    """
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=create_main_menu()
    )

@bot.message_handler(commands=['subscription', 'sub'])
def subscription_command(message):
    """عرض معلومات الاشتراك"""
    user_id = message.from_user.id
    user = get_user_info(user_id)
    plan = SUBSCRIPTION_PLANS[user['plan']]
    
    if user['plan'] == 'free':
        days_left = "يتجدد يومياً"
        status = "✅ نشط"
        limit_text = f"{user['daily_usage']} / {plan['daily_limit']}"
    else:
        days_left = (user['subscription_end'] - datetime.now()).days
        status = "✅ نشط" if is_subscription_active(user_id) else "❌ منتهي"
        limit_text = "غير محدود ♾️"
    
    info_text = f"""
📊 **معلومات اشتراكك**

🎯 الخطة: {plan['name']}
{status} الحالة: {status}
"""
    
    if user['plan'] == 'premium':
        info_text += f"""📅 ينتهي في: {user['subscription_end'].strftime('%Y-%m-%d')}
⏳ المتبقي: {days_left} يوم
"""
    else:
        info_text += f"""📅 الصلاحية: {days_left}
"""
    
    info_text += f"""
📈 **الاستخدام اليومي:**
• التفريغات اليوم: {limit_text}
• إجمالي التفريغات: {user['total_transcriptions']}

⚙️ **مميزات خطتك:**
"""
    
    for feature in plan['features']:
        info_text += f"• {feature}\n"
    
    markup = InlineKeyboardMarkup()
    if user['plan'] == 'free':
        markup.add(InlineKeyboardButton('💎 الترقية للمميزة - 10$ فقط!', callback_data='upgrade_premium'))
        markup.add(InlineKeyboardButton('🎁 اربح أيام مجانية', callback_data='show_referral'))
    else:
        markup.add(InlineKeyboardButton('🔄 تجديد الاشتراك', callback_data='renew_subscription'))
    
    bot.send_message(message.chat.id, info_text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['upgrade'])
def upgrade_command(message):
    """عرض خطط الترقية"""
    show_upgrade_plans(message.chat.id)

def show_upgrade_plans(chat_id, message_id=None):
    """عرض خطط الاشتراك"""
    premium_plan = SUBSCRIPTION_PLANS['premium']
    
    text = f"""
💎 **خطط الاشتراك**

🆓 **الخطة المجانية**
{chr(10).join(['• ' + f for f in SUBSCRIPTION_PLANS['free']['features']])}

━━━━━━━━━━━━━━━━━━━━

✨ **الخطة المميزة** - الأكثر شعبية!
{chr(10).join(['• ' + f for f in premium_plan['features']])}

💰 **السعر:**
• 10$ شهرياً
• {premium_plan['price']} جنيه مصري
• يتجدد كل 30 يوم

🎁 **عروض خاصة:**
• استخدم كود WELCOME10 لخصم 10%
• أو احصل على خصم 20% مع كود FIRST20
• دعوة صديق = 7 أيام مجانية!

💳 **طريقة الدفع:**
تحويل بنكي آمن ومباشر

⚡ التفعيل خلال 24 ساعة عادةً
    """
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(
            f'💎 اشترك الآن - ${premium_plan["price_usd"]} فقط!', 
            callback_data='buy_premium'
        ),
        InlineKeyboardButton('🎟 لدي كود خصم', callback_data='enter_coupon'),
        InlineKeyboardButton('🎁 برنامج الإحالة', callback_data='show_referral')
    )
    
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode='Markdown')
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['referral', 'invite'])
def referral_command(message):
    """نظام الإحالات"""
    user_id = message.from_user.id
    user = get_user_info(user_id)
    
    referral_link = get_referral_link(user_id)
    referrals_count = user.get('referrals', 0)
    
    text = f"""
🎁 **برنامج الإحالة والمكافآت**

📊 إحصائياتك:
• عدد الإحالات: {referrals_count}
• المكافآت المكتسبة: {referrals_count * REFERRAL_REWARDS['free_days']} يوم مجاني

🎯 **كيف يعمل:**
1. شارك رابطك الخاص مع أصدقائك
2. عند اشتراكهم في الخطة المميزة
3. تحصل على {REFERRAL_REWARDS['free_days']} أيام مجانية
4. ويحصلون على خصم {REFERRAL_REWARDS['discount_percent']}%

🔗 **رابط الإحالة الخاص بك:**
`{referral_link}`

💡 شارك الآن واربح أيام مجانية!
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton('📤 مشاركة الرابط', 
                                   url=f"https://t.me/share/url?url={referral_link}&text=جرّب بوت التفريغ الصوتي الاحترافي!"))
    
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'show_referral')
def show_referral_callback(call):
    """عرض نظام الإحالات"""
    referral_command(call.message)

@bot.callback_query_handler(func=lambda call: call.data in ['buy_premium', 'upgrade_premium', 'renew_subscription'])
def buy_premium_callback(call):
    """معالج شراء الخطة المميزة"""
    plan_id = 'premium'
    plan = SUBSCRIPTION_PLANS[plan_id]
    user_id = str(call.from_user.id)
    user = get_user_info(user_id)
    
    # التحقق من وجود كوبون نشط
    active_coupon = user.get('active_coupon', {})
    discount_percent = active_coupon.get('discount', 0) if active_coupon else 0
    
    original_price = plan['price']
    final_price = original_price
    
    if discount_percent > 0:
        final_price = original_price - (original_price * discount_percent / 100)
    
    # حساب السعر بالدولار
    price_usd = plan['price_usd']
    if discount_percent > 0:
        price_usd = price_usd - (price_usd * discount_percent / 100)
    
    # حفظ الخطة المعلقة
    user['pending_payment'] = {
        'plan': plan_id,
        'amount': final_price,
        'amount_usd': price_usd,
        'original_amount': original_price,
        'discount': discount_percent,
        'coupon_code': active_coupon.get('code') if active_coupon else None,
        'timestamp': datetime.now().isoformat()
    }
    save_database()
    
    # إنشاء رسالة معلومات الدفع
    discount_text = ""
    if discount_percent > 0:
        discount_text = f"""
🎉 **تم تطبيق خصم {discount_percent}%!**
السعر الأصلي: ~~{original_price} جنيه~~ (~~${plan['price_usd']}~~)
"""
    
    payment_text = f"""
💰 **تفاصيل الاشتراك**

📦 الخطة: {plan['name']}
⏰ المدة: {plan['duration_days']} يوم (شهر كامل)

{discount_text}
💵 **المبلغ المطلوب:**
• {int(final_price)} جنيه مصري
• ${price_usd:.2f} دولار أمريكي

━━━━━━━━━━━━━━━━━━━━

🏦 **معلومات التحويل البنكي:**

🏛 البنك: {BANK_INFO['bank_name']}
👤 اسم الحساب: {BANK_INFO['account_name']}
🔢 رقم الحساب: {BANK_INFO['account_number']}
🌐 IBAN: {BANK_INFO['iban']}
📱 المحفظة الإلكترونية: {BANK_INFO['phone']}

━━━━━━━━━━━━━━━━━━━━

📋 **خطوات الدفع:**

1️⃣ قم بتحويل المبلغ ({int(final_price)} جنيه) إلى أحد الحسابات أعلاه

2️⃣ التقط صورة واضحة لإيصال التحويل تظهر:
   • المبلغ الكامل
   • تاريخ ووقت التحويل
   • اسم المستقبل
   • رقم العملية

3️⃣ اضغط "إرسال إثبات الدفع" أدناه

4️⃣ أرسل صورة الإيصال

5️⃣ انتظر التفعيل (عادةً خلال 24 ساعة)

⚠️ **مهم جداً:**
اكتب في ملاحظات التحويل:
`Premium - {call.from_user.id}`

✅ بعد الموافقة:
• تفعيل فوري للخطة المميزة
• استخدام غير محدود لمدة 30 يوم
• جميع المميزات المتقدمة
    """
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton('📸 إرسال إثبات الدفع', callback_data=f'send_proof_{plan_id}')
    )
    markup.add(
        InlineKeyboardButton('🎟 لدي كود خصم', callback_data='enter_coupon'),
        InlineKeyboardButton('❌ إلغاء', callback_data='cancel_payment')
    )
    
    bot.edit_message_text(
        payment_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == 'enter_coupon')
def enter_coupon_callback(call):
    """طلب إدخال كوبون"""
    bot.answer_callback_query(call.id)
    
    coupons_text = "🎟 **الكوبونات المتاحة:**\n\n"
    for code, info in COUPONS.items():
        remaining = info['uses'] - info['used']
        if remaining > 0:
            coupons_text += f"• `{code}` - خصم {info['discount']}% ({remaining} متبقي)\n"
    
    coupons_text += "\n💡 أرسل كود الكوبون الآن:"
    
    bot.send_message(
        call.message.chat.id,
        coupons_text,
        parse_mode='Markdown'
    )
    
    user_data[str(call.from_user.id)]['awaiting_coupon'] = True
    save_database()

@bot.message_handler(func=lambda msg: user_data.get(str(msg.from_user.id), {}).get('awaiting_coupon'))
def handle_coupon(message):
    """معالجة الكوبون"""
    user_id = str(message.from_user.id)
    coupon_code = message.text.strip().upper()
    
    user_data[user_id]['awaiting_coupon'] = False
    
    if coupon_code in COUPONS:
        coupon = COUPONS[coupon_code]
        
        if coupon['used'] < coupon['uses']:
            user_data[user_id]['active_coupon'] = {
                'code': coupon_code,
                'discount': coupon['discount']
            }
            save_database()
            
            bot.send_message(
                message.chat.id,
                f"✅ **تم تفعيل الكوبون!**\n\n"
                f"الكود: `{coupon_code}`\n"
                f"الخصم: {coupon['discount']}%\n\n"
                f"سيتم تطبيق الخصم عند الاشتراك.\n\n"
                f"اضغط /upgrade للمتابعة",
                parse_mode='Markdown'
            )
        else:
            bot.send_message(message.chat.id, "❌ هذا الكوبون مستخدم بالكامل")
    else:
        bot.send_message(message.chat.id, "❌ كود خاطئ! حاول مرة أخرى أو اضغط /upgrade")
    
    save_database()

@bot.callback_query_handler(func=lambda call: call.data.startswith('send_proof_'))
def send_proof_callback(call):
    """طلب إرسال إثبات الدفع"""
    plan_id = call.data.split('_')[2]
    user_id = str(call.from_user.id)
    
    # حفظ حالة انتظار الإثبات
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['awaiting_proof'] = plan_id
    save_database()
    
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "📸 **الآن أرسل صورة إيصال التحويل**\n\n"
        "⚠️ تأكد من وضوح الصورة وظهور:\n"
        "• المبلغ المحول بالكامل\n"
        "• تاريخ ووقت التحويل\n"
        "• اسم المستقبل أو رقم الحساب\n"
        "• رقم العملية (إن وجد)\n\n"
        "💡 صورة واضحة = تفعيل أسرع!",
        parse_mode='Markdown'
    )

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """معالجة الصور (إثبات الدفع)"""
    user_id = str(message.from_user.id)
    
    if user_id in user_data and 'awaiting_proof' in user_data[user_id]:
        plan_id = user_data[user_id]['awaiting_proof']
        plan = SUBSCRIPTION_PLANS[plan_id]
        
        # الحصول على أكبر حجم للصورة
        photo = message.photo[-1]
        
        # معلومات المستخدم
        username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد"
        full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}"
        
        # إرسال الإثبات للمسؤول
        admin_text = f"""
🔔 **طلب اشتراك جديد**

👤 الاسم: {full_name}
🆔 اليوزر: {username}
🔢 المعرف: `{message.from_user.id}`

📦 الخطة: {plan['name']}
💰 المبلغ: {plan['price']} جنيه ({plan['price_usd']}$)
⏰ المدة: {plan['duration_days']} يوم
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📸 إثبات الدفع في الصورة أعلاه
        """
        
        # إرسال الصورة والمعلومات للمسؤول
        try:
            bot.send_photo(ADMIN_USER_ID, photo.file_id)
            
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton('✅ قبول وتفعيل', callback_data=f'approve_{message.from_user.id}_{plan_id}'),
                InlineKeyboardButton('❌ رفض', callback_data=f'reject_{message.from_user.id}')
            )
            
            bot.send_message(
                ADMIN_USER_ID,
                admin_text,
                reply_markup=markup,
                parse_mode='Markdown'
            )
            
            # إرسال رسالة تأكيد للمستخدم
            bot.send_message(
                message.chat.id,
                "✅ **تم استلام إثبات الدفع بنجاح!**\n\n"
                "🔍 سيتم مراجعة طلبك من قبل الإدارة\n"
                "⏰ عادةً يتم التفعيل خلال 24 ساعة\n"
                "📧 ستصلك رسالة تأكيد فور التفعيل\n\n"
                "🙏 شكراً لثقتك!",
                parse_mode='Markdown'
            )
            
            # حذف حالة انتظار الإثبات
            del user_data[user_id]['awaiting_proof']
            save_database()
            
            logger.info(f"💰 طلب اشتراك جديد من المستخدم {user_id} - الخطة: {plan_id}")
            
        except Exception as e:
            logger.error(f"خطأ في إرسال الإثبات للمسؤول: {e}")
            bot.send_message(
                message.chat.id,
                "❌ حدث خطأ في إرسال الإثبات. حاول مرة أخرى لاحقاً."
            )
    else:
        bot.send_message(
            message.chat.id,
            "🎤 لتفريغ صوتي، أرسل تسجيل صوتي أو ملف صوتي."
        )

@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_'))
def admin_approval_callback(call):
    """معالج قبول/رفض الدفع من المسؤول"""
    if call.from_user.id != ADMIN_USER_ID:
        bot.answer_callback_query(call.id, "❌ غير مصرح لك")
        return
    
    parts = call.data.split('_')
    action = parts[0]
    target_user_id = parts[1]
    
    if action == 'approve':
        plan_id = parts[2]
        plan = SUBSCRIPTION_PLANS[plan_id]
        
        # تفعيل الاشتراك
        user = get_user_info(target_user_id)
        user['plan'] = plan_id
        user['subscription_end'] = datetime.now() + timedelta(days=plan['duration_days'])
        user['daily_usage'] = 0
        
        # تحديث استخدام الكوبون إذا وجد
        if 'pending_payment' in user and user['pending_payment'].get('coupon_code'):
            coupon_code = user['pending_payment']['coupon_code']
            if coupon_code in COUPONS:
                COUPONS[coupon_code]['used'] += 1
        
        # حذف الدفع المعلق والكوبون النشط
        if 'pending_payment' in user:
            del user['pending_payment']
        if 'active_coupon' in user:
            del user['active_coupon']
        
        save_database()
        
        # إرسال رسالة للمستخدم
        try:
            bot.send_message(
                int(target_user_id),
                f"🎉 **مبروك! تم تفعيل اشتراكك!**\n\n"
                f"✅ الخطة: {plan['name']}\n"
                f"📅 صالح حتى: {user['subscription_end'].strftime('%Y-%m-%d')}\n"
                f"🎯 استخدام: غير محدود ♾️\n"
                f"⏱ مدة التسجيل: غير محدودة ♾️\n\n"
                f"🚀 ابدأ الآن بإرسال تسجيلاتك الصوتية!\n"
                f"شكراً لاشتراكك معنا! 💚",
                parse_mode='Markdown'
            )
            logger.info(f"✅ تم تفعيل اشتراك المستخدم {target_user_id} - الخطة: {plan_id}")
        except Exception as e:
            logger.error(f"خطأ في إرسال رسالة التفعيل: {e}")
        
        bot.answer_callback_query(call.id, "✅ تم تفعيل الاشتراك بنجاح")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(
            call.message.chat.id, 
            f"✅ **تم قبول وتفعيل الاشتراك**\n\n"
            f"المستخدم: `{target_user_id}`\n"
            f"الخطة: {plan['name']}",
            parse_mode='Markdown'
        )
        
    else:  # reject
        # إرسال رسالة للمستخدم
        try:
            support_text = f"\n\n📧 للاستفسار تواصل: @{SUPPORT_USERNAME}" if SUPPORT_USERNAME != "YourSupportUsername" else ""
            bot.send_message(
                int(target_user_id),
                f"❌ **تم رفض طلب الاشتراك**\n\n"
                f"للأسف، لم نتمكن من التحقق من عملية الدفع.\n"
                f"قد يكون السبب:\n"
                f"• صورة الإيصال غير واضحة\n"
                f"• المبلغ غير مطابق\n"
                f"• معلومات الدفع ناقصة{support_text}",
                parse_mode='Markdown'
            )
            logger.info(f"❌ تم رفض طلب المستخدم {target_user_id}")
        except Exception as e:
            logger.error(f"خطأ في إرسال رسالة الرفض: {e}")
        
        bot.answer_callback_query(call.id, "❌ تم رفض الطلب")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(
            call.message.chat.id, 
            f"❌ **تم رفض الطلب**\n\nالمستخدم: `{target_user_id}`",
            parse_mode='Markdown'
        )

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_payment')
def cancel_payment_callback(call):
    """إلغاء عملية الدفع"""
    user_id = str(call.from_user.id)
    
    if user_id in user_data and 'pending_payment' in user_data[user_id]:
        del user_data[user_id]['pending_payment']
        save_database()
    
    bot.answer_callback_query(call.id, "تم الإلغاء")
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.message_handler(content_types=['voice', 'audio', 'document'])
def handle_audio(message):
    """معالجة الملفات الصوتية"""
    user_id = message.from_user.id
    
    # التحقق من الاشتراك
    if not is_subscription_active(user_id):
        bot.send_message(
            message.chat.id,
            "⚠️ **اشتراكك منتهي!**\n\n"
            "للمتابعة، قم بالترقية أو تجديد اشتراكك.",
            parse_mode='Markdown'
        )
        show_upgrade_plans(message.chat.id)
        return
    
    user = get_user_info(user_id)
    plan = SUBSCRIPTION_PLANS[user['plan']]
    
    # إرسال رسالة جارٍ المعالجة
    processing_msg = bot.send_message(
        message.chat.id,
        "⏳ جاري معالجة الملف الصوتي...\n"
        "🔄 قد يستغرق هذا بضع دقائق حسب حجم الملف."
    )
    
    try:
        # تحديد نوع الملف وتحميله
        if message.content_type == 'voice':
            file_id = message.voice.file_id
            file_extension = '.ogg'
            file_name = 'voice_message'
            duration = message.voice.duration
        elif message.content_type == 'audio':
            file_id = message.audio.file_id
            file_extension = '.mp3'
            file_name = message.audio.file_name or 'audio_file'
            duration = message.audio.duration
        else:  # document
            file_id = message.document.file_id
            file_name = message.document.file_name
            file_extension = Path(file_name).suffix
            duration = 0
        
        # التحقق من إمكانية التفريغ
        can_do, error_msg = can_transcribe(user_id, duration)
        if not can_do:
            bot.delete_message(message.chat.id, processing_msg.message_id)
            bot.send_message(message.chat.id, error_msg, parse_mode='Markdown')
            if "ترقية" in error_msg or "تجديد" in error_msg:
                show_upgrade_plans(message.chat.id)
            return
        
        base_name = Path(file_name).stem
        
        # تنزيل الملف
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # حفظ الملف مؤقتاً
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(downloaded_file)
            temp_file_path = temp_file.name
        
        # تحويل OGG إلى MP3 إذا لزم
        if file_extension == '.ogg':
            mp3_path = temp_file_path.replace('.ogg', '.mp3')
            try:
                subprocess.run([
                    'ffmpeg', '-i', temp_file_path,
                    '-acodec', 'libmp3lame', mp3_path, '-y'
                ], check=True, capture_output=True, timeout=120)
                os.remove(temp_file_path)
                temp_file_path = mp3_path
            except Exception as e:
                logger.warning(f"فشل تحويل OGG: {e}")
        
        # استدعاء Whisper
        logger.info(f"🎤 بدء تفريغ للمستخدم {user_id}")
        result = whisper_model.transcribe(temp_file_path, task='transcribe', verbose=False)
        
        # حذف الملف المؤقت
        os.remove(temp_file_path)
        
        full_text = result['text'].strip()
        segments = result['segments']
        
        # تحديث الاستخدام
        user['daily_usage'] += 1
        user['total_transcriptions'] += 1
        save_database()
        
        # حذف رسالة المعالجة
        bot.delete_message(message.chat.id, processing_msg.message_id)
        
        # إعداد الملفات للتصدير
        files_to_send = []
        
        # ملف TXT
        if 'txt' in plan['formats']:
            txt_content = generate_txt(segments, plan['timestamps'])
            txt_file = tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8', suffix='.txt', delete=False
            )
            txt_file.write(txt_content)
            txt_file.close()
            files_to_send.append({'path': txt_file.name, 'name': f"{base_name}.txt"})
        
        # ملف SRT
        if 'srt' in plan['formats']:
            srt_content = generate_srt(segments)
            srt_file = tempfile.NamedTemporaryFile(
                mode='w', encoding='utf-8', suffix='.srt', delete=False
            )
            srt_file.write(srt_content)
            srt_file.close()
            files_to_send.append({'path': srt_file.name, 'name': f"{base_name}.srt"})
        
        # رسالة النجاح
        success_msg = f"✅ **تم التفريغ بنجاح!**\n\n"
        if len(full_text) <= 400:
            success_msg += f"📝 {full_text}\n\n"
        else:
            success_msg += f"📝 {full_text[:400]}...\n\n"
        
        if user['plan'] == 'free':
            remaining = plan['daily_limit'] - user['daily_usage']
            success_msg += f"📊 المتبقي اليوم: {remaining} تفريغ"
        else:
            success_msg += f"📊 استخدام غير محدود ♾️"
        
        bot.send_message(message.chat.id, success_msg, parse_mode='Markdown')
        
        # إرسال الملفات
        for file_info in files_to_send:
            with open(file_info['path'], 'rb') as f:
                bot.send_document(message.chat.id, f, visible_file_name=file_info['name'])
            os.remove(file_info['path'])
        
        logger.info(f"✅ اكتمل التفريغ للمستخدم {user_id}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في التفريغ: {e}")
        bot.delete_message(message.chat.id, processing_msg.message_id)
        bot.send_message(
            message.chat.id, 
            f"❌ حدث خطأ في معالجة الملف\n\n"
            f"حاول مرة أخرى أو تواصل مع الدعم."
        )

def format_timestamp_srt(seconds):
    """تنسيق الوقت بصيغة SRT"""
    td = timedelta(seconds=seconds)
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    secs = td.seconds % 60
    millisecs = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def generate_srt(segments):
    """إنشاء ملف SRT"""
    srt_content = ""
    for i, segment in enumerate(segments, start=1):
        start_time = format_timestamp_srt(segment['start'])
        end_time = format_timestamp_srt(segment['end'])
        text = segment['text'].strip()
        srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"
    return srt_content

def generate_txt(segments, with_timestamps=False):
    """إنشاء ملف TXT"""
    if with_timestamps:
        txt_content = ""
        for segment in segments:
            mins = int(segment['start'] // 60)
            secs = int(segment['start'] % 60)
            txt_content += f"[{mins:02d}:{secs:02d}] {segment['text'].strip()}\n"
    else:
        txt_content = " ".join([segment['text'].strip() for segment in segments])
    return txt_content

@bot.message_handler(func=lambda message: message.text == '🎤 تفريغ صوتي')
def transcribe_button(message):
    user = get_user_info(message.from_user.id)
    plan = SUBSCRIPTION_PLANS[user['plan']]
    
    if user['plan'] == 'free':
        remaining = plan['daily_limit'] - user['daily_usage']
        bot.send_message(
            message.chat.id, 
            f"🎤 أرسل تسجيل صوتي أو ملف صوتي الآن\n\n"
            f"📝 الصيغ المدعومة: MP3, WAV, M4A, OGG\n"
            f"⏱ الحد الأقصى: {plan['max_duration']//60} دقائق\n"
            f"📊 المتبقي اليوم: {remaining}/{plan['daily_limit']}"
        )
    else:
        bot.send_message(
            message.chat.id,
            f"🎤 أرسل تسجيل صوتي أو ملف صوتي الآن\n\n"
            f"📝 الصيغ المدعومة: MP3, WAV, M4A, OGG\n"
            f"✨ استخدام غير محدود ♾️"
        )

@bot.message_handler(func=lambda message: message.text == '📊 اشتراكي')
def subscription_button(message):
    subscription_command(message)

@bot.message_handler(func=lambda message: message.text == '💎 الترقية')
def upgrade_button(message):
    show_upgrade_plans(message.chat.id)

@bot.message_handler(func=lambda message: message.text == '❓ المساعدة')
def help_button(message):
    support_contact = f"@{SUPPORT_USERNAME}" if SUPPORT_USERNAME != "YourSupportUsername" else "المسؤول"
    
    help_text = f"""
❓ **المساعدة والدعم**

🎤 **كيفية الاستخدام:**
1. اضغط "🎤 تفريغ صوتي"
2. أرسل تسجيل صوتي أو ملف صوتي
3. انتظر المعالجة (ثواني إلى دقائق)
4. ستستلم ملفات TXT + SRT

💎 **الخطط المتاحة:**

🆓 **المجانية:**
• 3 تفريغات يومياً
• حتى 5 دقائق
• ملفات TXT + SRT
• طوابع زمنية

💎 **المميزة (10$ شهرياً):**
• تفريغات غير محدودة
• بدون حد للمدة
• معالجة فورية
• دعم مميز 24/7

📧 **للدعم الفني:**
{support_contact}

💡 **نصائح:**
• استخدم تسجيلات واضحة
• تجنب الضوضاء الخلفية
• تحدث بوضوح وهدوء

🎁 **عروض خاصة:**
• /referral - اربح أيام مجانية
• كود WELCOME10 - خصم 10%
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['admin'])
def admin_command(message):
    """لوحة المسؤول"""
    if message.from_user.id != ADMIN_USER_ID:
        return
    
    total_users = len(user_data)
    free_users = sum(1 for u in user_data.values() if u['plan'] == 'free')
    premium_users = sum(1 for u in user_data.values() if u['plan'] == 'premium')
    total_transcriptions = sum(u['total_transcriptions'] for u in user_data.values())
    
    # حساب المستخدمين النشطين
    week_ago = datetime.now() - timedelta(days=7)
    active_users = sum(
        1 for u in user_data.values() 
        if 'last_reset' in u and u['last_reset'] > week_ago
    )
    
    # الإيرادات
    monthly_revenue = premium_users * SUBSCRIPTION_PLANS['premium']['price']
    
    admin_text = f"""
🔧 **لوحة تحكم المسؤول**

👥 **إحصائيات المستخدمين:**
• إجمالي المستخدمين: {total_users}
• المجانية: {free_users}
• المميزة: {premium_users}
• النشطين (7 أيام): {active_users}

📊 **الاستخدام:**
• إجمالي التفريغات: {total_transcriptions}

💰 **الإيرادات:**
• شهرياً: {monthly_revenue} جنيه ({monthly_revenue//BANK_INFO['dollar_rate']}$)
• سنوياً (متوقع): {monthly_revenue * 12} جنيه

⚙️ **الإعدادات:**
• نموذج Whisper: {WHISPER_MODEL}
• قاعدة البيانات: {DB_FILE}
    """
    
    bot.send_message(message.chat.id, admin_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    """معالج النصوص العادية"""
    bot.send_message(
        message.chat.id,
        "🎤 أرسل لي تسجيلاً صوتياً لأقوم بتفريغه\n\n"
        "أو استخدم القائمة أدناه للتنقل 👇",
        reply_markup=create_main_menu()
    )

# ===================================
# تشغيل البوت
# ===================================

if __name__ == '__main__':
    # تحميل قاعدة البيانات
    load_database()
    
    # طباعة معلومات البدء
    print("\n" + "=" * 50)
    print("🚀 تشغيل بوت التفريغ الصوتي")
    print("=" * 50)
    print(f"📋 النموذج: {WHISPER_MODEL}")
    print(f"👤 المسؤول: {ADMIN_USER_ID}")
    print(f"💾 قاعدة البيانات: {DB_FILE}")
    print(f"👥 المستخدمين: {len(user_data)}")
    print("=" * 50)
    print("✅ البوت يعمل الآن...")
    print("🌐 Flask يعمل على المنفذ:", os.environ.get('PORT', 8080))
    print("⏹ للإيقاف: اضغط Ctrl+C")
    print("=" * 50 + "\n")
    
    logger.info("=" * 50)
    logger.info("🚀 تشغيل بوت التفريغ الصوتي")
    logger.info(f"📋 النموذج: {WHISPER_MODEL}")
    logger.info(f"👤 المسؤول: {ADMIN_USER_ID}")
    logger.info(f"💾 قاعدة البيانات: {DB_FILE}")
    logger.info(f"👥 المستخدمين المحملين: {len(user_data)}")
    logger.info("=" * 50)
    
    # تشغيل Flask في خيط منفصل
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # تشغيل البوت
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        print("\n⏹ تم إيقاف البوت بنجاح!")
        logger.info("⏹ تم إيقاف البوت")
    except Exception as e:
        print(f"\n❌ خطأ في تشغيل البوت: {e}")
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")






