#!/usr/bin/env python3
"""
SpoofifyPro - Advanced Telegram Bot (Final Fixed Version)
A sophisticated Telegram bot for privacy and security services with multi-language support.

Author: SpoofifyPro Team
Contact: @Kawalgzaeery
Version: 1.1 - Final Fix
"""

import logging
import asyncio
import json
import signal
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================================
# CONFIGURATION
# ================================

# Replace with your bot token from @BotFather
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Global application instance
application = None

# Data storage (in production, use a real database)
users_data: Dict[int, Dict] = {}
messages_data: List[Dict] = []
user_sessions: Dict[int, Dict] = {}

# ================================
# TRANSLATIONS
# ================================

TRANSLATIONS = {
    'ar': {
        'welcome': "🌍 يرجى اختيار لغتك المفضلة لبدء استخدام البوت:",
        'choose_language': "يرجى اختيار لغتك المفضلة للمتابعة:",
        'language_selected': "✅ تم اختيار اللغة العربية بنجاح!",
        'main_menu': "القائمة الرئيسية - اختر الخدمة المطلوبة:",
        'insufficient_balance': "💰 لا يمكن إتمام العملية لأن رصيدك غير كافٍ.\n\n⚠️ كل شيء مدفوع مسبقاً. لا توجد اشتراكات أو رسوم مخفية.",
        'virtual_number': "📱 رقم افتراضي مؤقت\nهاتف افتراضي / رقم ثاني\n\nرقم افتراضي لاستقبال المكالمات والرسائل عبر الويب، دون الحاجة لبطاقة SIM حقيقية.\nمناسب لحماية الخصوصية ❗\n\nاختر الدولة التي تريد الحصول على رقم منها 👇",
        'whats_sim': "🔢 Whats SIM\n\nرقم مؤقت يُستخدم لتفعيل خدمات مثل واتساب وتليجرام ولاين، دون الحاجة لبطاقة SIM فعلية. يمكنك أيضاً استقبال مكالمات ورسائل التفعيل عبر الصوت أو النص.\n\nاختر الدولة المطلوبة 👇",
        'payment_sent': "✅ تم إرسال الإشعار للدعم الفني. سيتم تفعيل رصيدك خلال دقائق بعد تأكيد المعاملة.",
        'back_to_menu': "🔙 العودة للقائمة الرئيسية",
        'balance_text': "💰 رصيدك الحالي: ${balance}\n\n{status}",
        'balance_low': "⚠️ رصيدك منخفض. يمكنك الشحن من القائمة الرئيسية.",
        'balance_sufficient': "✅ رصيدك كافٍ لاستخدام الخدمات.",
    },
    'en': {
        'welcome': "🌍 Please choose your preferred language to start using the bot:",
        'choose_language': "Please choose your preferred language to continue:",
        'language_selected': "✅ English language selected successfully!",
        'main_menu': "Main Menu - Choose the required service:",
        'insufficient_balance': "💰 The transaction cannot be completed because you have insufficient balance.\n\n⚠️ Everything is prepaid. No subscriptions or hidden fees.",
        'virtual_number': "📱 Temporary Virtual Number\nVirtual Phone / Second Number\n\nA virtual number to receive calls and messages via the web, without the need for a real SIM card.\nSuitable for privacy protection ❗\n\nChoose the country you want to get a number from 👇",
        'whats_sim': "🔢 Whats SIM\n\nA temporary number used to activate services such as WhatsApp, Telegram, and Line, without the need for a physical SIM card. You can also receive activation calls and messages via voice or text.\n\nSelect the desired country 👇",
        'payment_sent': "✅ Support team has been notified. Your balance will be activated within minutes after transaction confirmation.",
        'back_to_menu': "🔙 Back to Main Menu",
        'balance_text': "💰 Your current balance: ${balance}\n\n{status}",
        'balance_low': "⚠️ Your balance is low. You can top up from the main menu.",
        'balance_sufficient': "✅ Your balance is sufficient to use services.",
    },
}

# ================================
# CRYPTO ADDRESSES
# ================================

CRYPTO_ADDRESSES = {
    'BTC': {
        'address': '3GvwS9tnSqp5hSKL5RquGKrxsR16quDdQv',
        'network': 'Bitcoin Network',
        'confirmations': 1,
        'price': 107198.37
    },
    'ETH': {
        'address': '0x2a3489047b085d04c8b9f8a2d7e3f1a6b8c9d0e1',
        'network': 'Ethereum (ERC20)',
        'confirmations': 12,
        'price': 3456.78
    },
    'USDT': {
        'address': 'TQn9Y2khEsLJW1ChVWFMSMeRDow5oREqjK',
        'network': 'TRC20 (Tron)',
        'confirmations': 1,
        'price': 1.0
    },
}

# ================================
# UTILITY FUNCTIONS
# ================================

def log_activity(action: str, user_id: int = 0, data: Any = None):
    """Log bot activities"""
    timestamp = datetime.now().isoformat()
    log_message = f"[{timestamp}] {action} - User: {user_id}"
    
    logger.info(log_message)
    if data:
        logger.info(f"Data: {json.dumps(data, default=str)}")
    
    # Store in messages_data
    messages_data.append({
        'timestamp': timestamp,
        'action': action,
        'user_id': user_id,
        'data': data
    })
    
    # Keep only last 1000 messages
    if len(messages_data) > 1000:
        messages_data[:] = messages_data[-1000:]

def get_user_language(user_id: int) -> str:
    """Get user's selected language"""
    user = users_data.get(user_id, {})
    return user.get('selected_language', 'en')

def get_translation(user_id: int, key: str) -> str:
    """Get translated text for user"""
    lang = get_user_language(user_id)
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, TRANSLATIONS['en'].get(key, key))

def update_user_data(user_id: int, user_info: Dict, **kwargs):
    """Update user data"""
    if user_id not in users_data:
        users_data[user_id] = {
            **user_info,
            'balance': 0,
            'selected_language': None,
            'join_date': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'message_count': 0
        }
    
    users_data[user_id].update(kwargs)
    users_data[user_id]['last_activity'] = datetime.now().isoformat()
    users_data[user_id]['message_count'] = users_data[user_id].get('message_count', 0) + 1

def get_user_balance(user_id: int) -> float:
    """Get user balance"""
    return users_data.get(user_id, {}).get('balance', 0)

def update_user_balance(user_id: int, amount: float):
    """Update user balance"""
    if user_id in users_data:
        users_data[user_id]['balance'] = users_data[user_id].get('balance', 0) + amount
        log_activity("BALANCE_UPDATE", user_id, {
            'new_balance': users_data[user_id]['balance'],
            'added': amount
        })

# ================================
# KEYBOARD CREATORS
# ================================

def create_language_keyboard():
    """Create language selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🇸🇦 Arabic 🕌", callback_data="lang_ar"),
            InlineKeyboardButton("🇺🇸 English 🌐", callback_data="lang_en"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def create_main_menu_keyboard():
    """Create main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🕵️‍♂️ Spoof", callback_data="spoof"),
            InlineKeyboardButton("🔢 Whats SIM", callback_data="whats_sim")
        ],
        [
            InlineKeyboardButton("📱 Virtual Number", callback_data="virtual_number"),
            InlineKeyboardButton("💎 Top Up", callback_data="topup")
        ],
        [
            InlineKeyboardButton("🔍 Spokeo - Detect People", callback_data="spokeo"),
            InlineKeyboardButton("🛠️ Tools", callback_data="tools")
        ],
        [
            InlineKeyboardButton("ℹ️ Instructions and Support", callback_data="support")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_insufficient_balance_keyboard():
    """Create insufficient balance keyboard"""
    keyboard = [
        [InlineKeyboardButton("💎 Top up your balance", callback_data="topup")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_topup_keyboard():
    """Create top-up amounts keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("$50", callback_data="topup_50"),
            InlineKeyboardButton("$100", callback_data="topup_100"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ================================
# COMMAND HANDLERS
# ================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = user.id
    
    log_activity("START_COMMAND", user_id)
    
    # Update user data
    update_user_data(user_id, {
        'id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username
    })
    
    # Check if user has selected language
    if not users_data.get(user_id, {}).get('selected_language'):
        await show_language_selection(update, context)
    else:
        await show_main_menu(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user_id = update.effective_user.id
    log_activity("HELP_COMMAND", user_id)
    
    help_text = """ℹ️ <b>Help and FAQ</b>

Welcome to <b>SpoofifyPro</b> 👋
Here's your quick guide to using the available services:

<b>📱 Virtual Number</b>
Use a real number without a SIM card to activate services.

<b>🔢 Whats SIM</b>
Numbers to activate WhatsApp/Telegram without a physical SIM.

<b>💎 Top-up Your Balance</b>
Choose the top-up amount and select the digital currency.

<b>📞 Technical Support:</b>
Message us via: <a href="https://t.me/Kawalgzaeery">@Kawalgzaeery</a>

⚠️ The services may not be used for illegal purposes.
Designed for privacy, testing, and security purposes only ✅"""
    
    await update.message.reply_text(help_text, parse_mode='HTML', disable_web_page_preview=True)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /balance command"""
    user_id = update.effective_user.id
    log_activity("BALANCE_COMMAND", user_id)
    
    balance = get_user_balance(user_id)
    status = get_translation(user_id, 'balance_low' if balance < 50 else 'balance_sufficient')
    
    balance_text = get_translation(user_id, 'balance_text').format(
        balance=balance,
        status=status
    )
    
    await update.message.reply_text(balance_text)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command"""
    user_id = update.effective_user.id
    log_activity("MENU_COMMAND", user_id)
    
    await show_main_menu(update, context)

# ================================
# MENU DISPLAY FUNCTIONS
# ================================

async def show_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language selection menu"""
    keyboard = create_language_keyboard()
    text = "🌍 Please choose your preferred language to start using the bot:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit_message=False):
    """Show main menu"""
    user_id = update.effective_user.id
    keyboard = create_main_menu_keyboard()
    text = get_translation(user_id, 'main_menu')
    
    if edit_message and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)

async def show_insufficient_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show insufficient balance message"""
    user_id = update.effective_user.id
    keyboard = create_insufficient_balance_keyboard()
    text = get_translation(user_id, 'insufficient_balance')
    
    await update.callback_query.edit_message_text(text, reply_markup=keyboard)

async def show_topup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top-up menu"""
    user_id = update.effective_user.id
    keyboard = create_topup_keyboard()
    
    lang = get_user_language(user_id)
    text = {
        'ar': "💰 تجديد الرصيد\n\nيرجى اختيار المبلغ الذي تريد شحنه (بالدولار).\n🔻 الحد الأدنى للشحن: $50",
        'en': "💰 Renewal\n\nPlease select the amount you want to top up (in dollars).\n🔻 Minimum top-up: $50"
    }.get(lang, "💰 Renewal\n\nPlease select the amount you want to top up (in dollars).\n🔻 Minimum top-up: $50")
    
    await update.callback_query.edit_message_text(text, reply_markup=keyboard)

# ================================
# CALLBACK QUERY HANDLER
# ================================

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback queries"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    log_activity("CALLBACK_RECEIVED", user_id, {'data': data})
    
    # Language selection
    if data.startswith("lang_"):
        selected_lang = data.replace("lang_", "")
        users_data[user_id]['selected_language'] = selected_lang
        log_activity("LANGUAGE_SELECTED", user_id, {'language': selected_lang})
        
        await query.edit_message_text(get_translation(user_id, 'language_selected'))
        await asyncio.sleep(1.5)
        await show_main_menu(update, context, edit_message=True)
    
    # Main menu selections
    elif data in ["virtual_number", "whats_sim", "spoof", "spokeo", "tools"]:
        await show_insufficient_balance(update, context)
    elif data == "topup":
        await show_topup_menu(update, context)
    elif data == "support":
        support_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📩 Message Support", url="https://t.me/Kawalgzaeery")],
            [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
        ])
        support_text = "📞 للتواصل مع الدعم الفني:\n👤 تليجرام: @Kawalgzaeery" if get_user_language(user_id) == 'ar' else "📞 To contact technical support:\n👤 Telegram: @Kawalgzaeery"
        await query.edit_message_text(support_text, reply_markup=support_keyboard)
    
    # Top-up flow
    elif data.startswith("topup_"):
        amount = data.replace("topup_", "")
        payment_text = f"💰 Payment for ${amount}\n\nContact support to complete payment:\n@Kawalgzaeery"
        payment_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Payment completed", callback_data="payment_sent")],
            [InlineKeyboardButton("🔙 Back", callback_data="topup")]
        ])
        await query.edit_message_text(payment_text, reply_markup=payment_keyboard)
    
    # Payment confirmation
    elif data == "payment_sent":
        log_activity("PAYMENT_REPORTED", user_id, {"amount": "unknown"})
        await query.edit_message_text(get_translation(user_id, 'payment_sent'))
    
    # Back buttons
    elif data == "back_main":
        await show_main_menu(update, context, edit_message=True)

# ================================
# SIGNAL HANDLERS
# ================================

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}. Shutting down gracefully...")
    
    # Get the current event loop
    try:
        loop = asyncio.get_running_loop()
        # Schedule the shutdown
        loop.create_task(shutdown_application())
    except RuntimeError:
        # No running loop, exit directly
        logger.info("No running event loop, exiting directly")
        sys.exit(0)

async def shutdown_application():
    """Shutdown the application gracefully"""
    global application
    
    logger.info("🛑 Shutting down SpoofifyPro Bot...")
    
    if application:
        try:
            # Stop the application
            await application.stop()
            await application.shutdown()
            logger.info("✅ Bot shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    # Stop the event loop
    loop = asyncio.get_running_loop()
    loop.stop()

# ================================
# MAIN BOT SETUP AND RUN
# ================================

async def setup_bot():
    """Setup the bot with handlers"""
    global application
    
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ Please set your bot token in the BOT_TOKEN variable!")
        logger.error("Get your token from @BotFather on Telegram")
        return None
    
    logger.info("🚀 Starting SpoofifyPro Bot...")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Log startup
    log_activity("BOT_STARTED", 0, {"version": "1.1"})
    
    logger.info("✅ SpoofifyPro Bot is running!")
    logger.info("📱 Send /start to your bot to begin")
    logger.info("🛑 Press Ctrl+C to stop the bot")
    
    return application

async def run_bot():
    """Run the bot"""
    try:
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Setup and run the bot
        app = await setup_bot()
        if app:
            # Run the bot with polling
            await app.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
    finally:
        # Ensure cleanup
        if application:
            try:
                await application.stop()
                await application.shutdown()
            except Exception as e:
                logger.error(f"Error during final cleanup: {e}")

# ================================
# MAIN EXECUTION
# ================================

def main():
    """Main function"""
    print("🌟 SpoofifyPro - Advanced Telegram Bot")
    print("=" * 50)
    print("🔧 Initializing bot...")
    
    try:
        # Run the bot
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Main error: {e}")
    finally:
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()
