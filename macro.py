import os
import asyncio
import requests
# Removed pyautogui (ca), zendriver (zd), notifypy, pystyle
import random
import string
import json
import re
import socket
import httpx
import base64
import tls_client
import time
import hashlib
import hmac
from datetime import datetime
from dateutil.parser import isoparse
from colorama import Fore, Style, init
import websocket

init(autoreset=True)

# --- CONFIG LOADING & GLOBALS ---
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"{Fore.RED}ERROR: config.json not found. Please create it.")
    exit(1)

INCOGNITO_API_URL = config.get("mail_api", "https://api.incognitomail.co/")
INCOGNITO_DOMAIN = config.get("mail_domain", "vorlentis.xyz")

USE_HUMANIZER = False
USE_VPN = False

# --- UTILITY FUNCTIONS ---

def send_notification(title, message):
    """Replaced desktop notification with a simple log message for Termux."""
    if not config.get("notify", False):
        return
    log("INFO", f"NOTIFICATION: {title} - {message}")

def log(type, message):
    """Logging function adjusted for Termux terminal compatibility."""
    now = datetime.now().strftime("%H:%M:%S")
    type_map = {
        "SUCCESS": Fore.GREEN + "SUCCESS" + Style.RESET_ALL,
        "ERROR": Fore.RED + "ERROR" + Style.RESET_ALL,
        "INFO": Fore.CYAN + "INFO" + Style.RESET_ALL,
        "WARNING": Fore.YELLOW + "WARNING" + Style.RESET_ALL
    }
    tag = type_map.get(type.upper(), type.upper())
    
    # Simple message color logic for Termux
    message_color = Fore.LIGHTBLACK_EX if type.upper() == "INFO" else Style.RESET_ALL
    
    if ':' in message:
        parts = message.split(':', 1)
        key = parts[0].upper().strip()
        val = parts[1].strip()
        message_output = f"{key}: {message_color}{val}{Style.RESET_ALL}"
    else:
        message_output = f"{message_color}{message}{Style.RESET_ALL}"

    print(f"{Fore.LIGHTBLACK_EX}{now}{Style.RESET_ALL} - {tag} • {message_output}")

def clear_screen():
    """Use 'clear' command for Termux."""
    os.system('clear')

def vertical_gradient(lines, start_rgb=(0, 255, 200), end_rgb=(0, 100, 180)):
    """Standard terminal ANSI escape code gradient function (unchanged)."""
    total = len(lines)
    result = []
    for i, line in enumerate(lines):
        r = start_rgb[0] + (end_rgb[0] - start_rgb[0]) * i // max(1, total - 1)
        g = start_rgb[1] + (end_rgb[1] - start_rgb[1]) * i // max(1, total - 1)
        b = start_rgb[2] + (end_rgb[2] - start_rgb[2]) * i // max(1, total - 1)
        # Using ANSI 256 color codes
        result.append(f'\033[38;2;{r};{g};{b}m{line}\033[0m')
    return result

def print_ascii_logo():
    """ASCII printing simplified for Termux, removing pystyle.Center dependency."""
    ascii_art = [
        '                                                                                                    ',
        '▀████▄    ▄███▀      ██      ▄▄█▀▀▀█▄████▀▀▀██▄  ▄▄█▀▀██▄       ▄█▀▀▀█▄█████▀  ▀████▀▀ ▄▄█▀▀██▄ ▀███▀▀▀██▄',
        ' ████   ████     ▄██▄    ▄██▀      ▀█ ██  ▀██▄▄██▀    ▀██▄    ▄██   ▀█ ██    ██ ▄██▀    ▀██▄ ██  ▀██▄',
        ' █ ██  ▄█ ██    ▄█▀██▄   ██▀        ▀ ██  ▄██ ██▀      ▀██    ▀███▄    ██    ██ ██▀      ▀██ ██  ▄██',
        ' █  ██ █▀ ██   ▄█ ▀██   ██          ███████  ██        ██      ▀█████▄ ██████████  ██        ██ ███████ ',
        ' █  ██▄█▀  ██   ████████  ██▄        ██ ██▄  ██▄      ▄██    ▄     ▀██ ██    ██ ██▄      ▄██ ██     ',
        ' █  ▀██▀  ██  █▀      ██ ▀██▄    ▄▀ ██  ▀██▄▀██▄    ▄██▀    ██      ██ ██    ██ ▀██▄    ▄██▀ ██     ',
        '▄███▄ ▀▀ ▄████▄███▄  ▄████▄ ▀▀█████▀▄████▄ ▄███▄ ▀▀████▀▀    █▀█████▀▄████▄  ▄████▄▄ ▀▀████▀▀ ▄████▄     ',
        '                                                                                                    ',
        'Made by Marcus! with love'
    ]

    print('\n' * 2)
    gradient_lines = vertical_gradient(ascii_art)
    for colored_line in gradient_lines:
        print(colored_line)
    print('\n' * 2)

def generate_random_string(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def random_username():
    return 'marcus' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

def get_user_input(prompt, valid_options=["yes", "no", "y", "n"]):
    while True:
        try:
            response = input(f"{Fore.CYAN}[+] {prompt}: {Style.RESET_ALL}").strip().lower()
            if response in valid_options:
                return response
        except KeyboardInterrupt:
            exit(0)
        except Exception:
            pass

def configure_user_options():
    global USE_HUMANIZER, USE_VPN
    
    print(f"\n{Fore.CYAN}Configuration Options{Style.RESET_ALL}\n")
    
    humanizer_choice = get_user_input("Do you want to use humanizer (y/n)")
    USE_HUMANIZER = humanizer_choice in ["yes", "y"]
    
    vpn_choice = get_user_input("Do you want to use VPN (y/n)")
    USE_VPN = vpn_choice in ["yes", "y"]
    
    print(f"\n{Fore.GREEN}Configuration completed!{Style.RESET_ALL}\n")

async def validate_license_key(license_key: str):
    return True

# --- INCOGNITOMAIL CLIENT (UNCHANGED CORE LOGIC) ---
class IncognitoMailClient:
    def __init__(self):
        self.email = None
        self.inbox_id = None
        self.inbox_token = None
        self.session = requests.Session()
        self.secret_key = None
        self._initialize_secret()

    def _initialize_secret(self):
        scrambled = "4O)QqiTV+(U+?Vi]qe|6..Xe"
        self.secret_key = ''.join([chr(ord(c) - 2) for c in scrambled])

    def _sign_payload(self, payload: dict) -> str:
        message = json.dumps(payload, separators=(',', ':')).encode()
        key = self.secret_key.encode()
        return hmac.new(key, message, hashlib.sha256).hexdigest()

    def _get_random_fr_ip(self):
        return f"90.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"

    async def create_temp_email(self):
        for attempt in range(1, 3):
            try:
                timestamp = int(time.time() * 1000)
                payload = {
                    "ts": timestamp,
                    "domain": INCOGNITO_DOMAIN
                }
                payload["key"] = self._sign_payload(payload)
                
                fake_ip = self._get_random_fr_ip()
                headers = {
                    "Content-Type": "application/json",
                    # Changed to a generic mobile User-Agent
                    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
                    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
                    "X-Forwarded-For": fake_ip,
                    "X-Real-IP": fake_ip,
                    "Via": fake_ip
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{INCOGNITO_API_URL}inbox/v2/create", 
                        json=payload, 
                        headers=headers,
                        timeout=15
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    if "id" in data and "token" in data:
                        self.inbox_id = data["id"]
                        self.inbox_token = data["token"]
                        self.email = self.inbox_id
                        log("SUCCESS", f"Email created: {self.email}")
                        return self.email
                
            except Exception as e:
                if attempt == 2:
                    log("ERROR", f"Failed to create email: {e}")
                await asyncio.sleep(2)
                    
        return None

    def check_verification_email(self):
        # Synchronous checking remains the same as it uses requests
        if not self.inbox_id or not self.inbox_token:
            return None
            
        for attempt in range(1, 30):
            try:
                ts = int(time.time() * 1000)
                payload = {
                    "inboxId": self.inbox_id,
                    "inboxToken": self.inbox_token,
                    "ts": ts
                }
                payload["key"] = self._sign_payload(payload)
                
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36"
                }
                
                response = requests.post(
                    f"{INCOGNITO_API_URL}inbox/v1/list", 
                    json=payload, 
                    headers=headers, 
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])
                    
                    if items:
                        for item in items:
                            message_url = item.get("messageURL")
                            if message_url:
                                try:
                                    email_data = requests.get(message_url, timeout=5).json()
                                    subject = email_data.get("subject", "")
                                    
                                    if "verify" in subject.lower():
                                        content = str(email_data.get("text", "")) + str(email_data.get("html", ""))
                                        
                                        patterns = [
                                            r'https:\/\/click\.discord\.com[^\s"\'\'<>\\]+',
                                            r'https://click\.discord\.com[^\s"\'\'<>\\]+',
                                            r'https://discord\.com/verify[^\s"\'\'<>\\]+'
                                        ]
                                        
                                        for pattern in patterns:
                                            match = re.search(pattern, content)
                                            if match:
                                                link = match.group(0).replace('\\/', '/').split("\n")[0].strip()
                                                link = link.replace('&amp;', '&')
                                                log("SUCCESS", "Verification link found")
                                                return link
                                except:
                                    continue
                    
            except:
                pass
            
            time.sleep(2.0)
        
        log("ERROR", "Verification email not received")
        return None

# --- BROWSER MANAGER (REMOVED) ---
# Removed the entire BrowserManager class as it's not applicable.

# --- DISCORD HUMANIZER (Kept, but uses API/WebSockets) ---
class DiscordHumanizer:
    def __init__(self):
        self.config = self.load_config()
        self.customization = self.config.get("CustomizationSettings", {})
        self.load_data_files()
        # tls_client is used for improved TLS fingerprinting
        self.session = tls_client.Session(client_identifier="chrome_115", random_tls_extension_order=True)

    def load_config(self):
        # ... (unchanged from original)
        try:
            with open("config.json", "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            log("ERROR", f"Failed to load config.json: {e}")
            return {}

    def load_data_files(self):
        # ... (unchanged from original)
        try:
            if self.customization.get("Pronouns", False):
                with open("data/pronouns.txt", "r", encoding="utf-8") as f:
                    self.pronouns = [line.strip() for line in f if line.strip()]
            
            if self.customization.get("Bio", False):
                with open("data/bios.txt", "r", encoding="utf-8") as f:
                    self.bios = [line.strip() for line in f if line.strip()]
            
            if self.customization.get("DisplayName", False):
                with open("data/names.txt", "r", encoding="utf-8") as f:
                    self.names = [line.strip() for line in f if line.strip()]
            
            if self.customization.get("Avatar", False):
                if not os.path.exists("avatar"):
                    os.makedirs("avatar")
                self.avatars = [f for f in os.listdir("avatar") if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]

        except Exception as e:
            log("ERROR", f"Failed to load data files: {e}")

    def go_online(self, token):
        """Uses websocket, which is fully compatible with Termux."""
        try:
            ws = websocket.WebSocket()
            ws.connect('wss://gateway.discord.gg/?v=6&encoding=json')
            hello = json.loads(ws.recv())
            heartbeat_interval = hello['d']['heartbeat_interval'] / 1000

            status = random.choice(['online', 'dnd', 'idle'])
            activity_type = random.choice(['Playing', 'Streaming', 'Watching', 'Listening', ''])

            # Simplified activity JSON
            gamejson = None
            if activity_type == "Playing":
                gamejson = {"name": "EV GEN", "type": 0}
            elif activity_type == 'Streaming':
                gamejson = {"name": "EV GEN", "type": 1, "url": "https://twitch.tv/c_mposee"}
            elif activity_type == "Listening":
                gamejson = {"name": "EV GEN", "type": 2}
            elif activity_type == "Watching":
                gamejson = {"name": "P0rn", "type": 3}

            auth = {
                "op": 2,
                "d": {
                    "token": token,
                    "properties": {
                        "$os": "android", # Changed OS to Android
                        "$browser": "Discord Android",
                        "$device": "android"
                    },
                    "presence": {
                        "activities": [gamejson] if gamejson else [],
                        "status": status,
                        "since": 0,
                        "afk": False
                    }
                }
            }
            ws.send(json.dumps(auth))
            return ws, heartbeat_interval
        except Exception as e:
            log("ERROR", f"WebSocket Error: {e}")
            return None, None

    def set_offline(self, ws):
        """Sets presence to offline via websocket."""
        try:
            if ws:
                offline_payload = {
                    "op": 3,
                    "d": {
                        "status": "invisible",
                        "since": 0,
                        "activities": [],
                        "afk": False
                    }
                }
                ws.send(json.dumps(offline_payload))
                time.sleep(1)
                ws.close()
        except Exception as e:
            log("ERROR", f"Error setting offline: {e}")

    async def humanize_account(self, token, email, password):
        # Core humanization logic remains the same (API PATCH/POST requests)
        if not USE_HUMANIZER:
            return True

        log("INFO", f"HUMANIZING TOKEN : {token[:12]}...")
        
        ws = None
        try:
            ws, _ = self.go_online(token)
            
            if any([self.customization.get("Pronouns"), self.customization.get("DisplayName"), 
                   self.customization.get("Bio"), self.customization.get("HypeSquad")]):
                await self.update_profile_fields(token)

            if self.customization.get("Avatar", False) and self.avatars:
                avatar_path = os.path.join("avatar", random.choice(self.avatars))
                self.update_avatar(token, avatar_path)

            log("SUCCESS", f"FINISHED HUMANIZING TOKEN : {token[:12]}...")
            return True
        except Exception as e:
            log("ERROR", f"Failed to humanize account: {str(e)}")
            return False
        finally:
            if ws:
                self.set_offline(ws)


    async def update_profile_fields(self, token):
        # Implementation remains the same (uses tls_client.Session)
        headers = {
            "authority": "discord.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "authorization": token,
            "content-type": "application/json",
            "origin": "https://discord.com",
            "referer": "https://discord.com/channels/@me",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            # Updated User-Agent
            "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
            "x-debug-options": "bugReporterEnabled",
            "x-discord-locale": "en-US",
            # Simplified X-Super-Properties for mobile
            "x-super-properties": "eyJvcyI6IkFuZHJvaWQiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiYW5kcm9pZCIsInN5c3RlbV9sb2NhbGUiOiJlbi1VUyIsImJyb3dzZXJfdXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChMaW51eDsgQW5kcm9pZCAxMDsgSykgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEyMC4wLjYwOTkuMTQ0IE1vYmlsZSBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTIwLjAuNjA5OS4xNDQiLCJvc192ZXJzaW9uIjoiMTAiLCJyZWZlcnJlciI6IiIsInJlZmVycmluZ19kb21haW4iOiIiLCJyZWZlcnJlcl9jdXJyZW50IjoiIiwicmVmZXJyaW5nX2RvbWFpbl9jdXJyZW50IjoiIiwicmVsZWFzZV9jaGFubmVsIjoic3RhYmxlIiwiY2xpZW50X2J1aWxkX251bWJlciI6MjUxNDQxLCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ=="
        }
        
        if self.customization.get("DisplayName", False) and self.names:
            global_name = random.choice(self.names)
            payload = {"global_name": global_name}
            try:
                response = self.session.patch(
                    "https://discord.com/api/v9/users/@me",
                    headers=headers,
                    json=payload
                )
                if response.status_code == 200:
                    log("SUCCESS", f"GLOBAL NAME UPDATED : {global_name}")
                else:
                    log("ERROR", f"FAILED TO UPDATE GLOBAL NAME : {response.text}")
            except Exception as e:
                log("ERROR", f"Exception updating global name: {str(e)}")
        
        payload = {}
        
        if self.customization.get("Pronouns", False) and self.pronouns:
            payload["pronouns"] = random.choice(self.pronouns)
        
        if self.customization.get("Bio", False) and self.bios:
            payload["bio"] = random.choice(self.bios)
        
        if payload:
            url = "https://discord.com/api/v9/users/@me/profile"
            try:
                response = self.session.patch(url, headers=headers, json=payload)
                if response.status_code == 200:
                    log("SUCCESS", "PROFILE FIELDS UPDATED SUCCESSFULLY")
                else:
                    log("ERROR", f"FAILED TO UPDATE PROFILE FIELDS : {response.text}")
            except Exception as e:
                log("ERROR", f"Exception updating profile fields: {str(e)}")
        
        if self.customization.get("HypeSquad", False):
            house_ids = {"bravery": 1, "brilliance": 2, "balance": 3}
            house = random.choice(list(house_ids.keys()))
            hypesquad_payload = {"house_id": house_ids[house]}
            url = "https://discord.com/api/v9/hypesquad/online"
            
            try:
                response = self.session.post(url, headers=headers, json=hypesquad_payload)
                if response.status_code == 204:
                    log("SUCCESS", f"HYPESQUAD UPDATED : {house.capitalize()}")
                else:
                    log("ERROR", f"FAILED TO UPDATE HYPESQUAD : {response.text}")
            except Exception as e:
                log("ERROR", f"Exception updating HypeSquad: {str(e)}")

    def update_avatar(self, token, image_path):
        # Implementation remains the same (uses tls_client.Session and base64)
        try:
            if not os.path.exists(image_path):
                log("ERROR", f"AVATAR IMAGE NOT FOUND : {image_path}")
                return False

            with open(image_path, "rb") as f:
                img_data = f.read()
                ext = os.path.splitext(image_path)[1].lower().replace('.', '')
                mime_type = "image/gif" if ext == "gif" else f"image/{'jpeg' if ext == 'jpg' else ext}"
                b64 = base64.b64encode(img_data).decode()
                avatar_data = f"data:{mime_type};base64,{b64}"

            headers = {
                "authorization": token,
                "content-type": "application/json",
                # Updated User-Agent
                "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
                "x-super-properties": "eyJvcyI6IkFuZHJvaWQiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiYW5kcm9pZCIsInN5c3RlbV9sb2NhbGUiOiJlbi1VUyIsImJyb3dzZXJfdXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChMaW51eDsgQW5kcm9pZCAxMDsgSykgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEyMC4wLjYwOTkuMTQ0IE1vYmlsZSBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTIwLjAuNjA5OS4xNDQiLCJvc192ZXJzaW9uIjoiMTAiLCJyZWZlcnJlciI6IiIsInJlZmVycmluZ19kb21haW4iOiIiLCJyZWZlcnJlcl9jdXJyZW50IjoiIiwicmVsZWFzZV9jaGFubmVsIjoic3RhYmxlIiwiY2xpZW50X2J1aWxkX251bWJlciI6MjUxNDQxLCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ=="
            }

            payload = {"avatar": avatar_data}

            response = self.session.patch(
                "https://discord.com/api/v9/users/@me",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                log("SUCCESS", f"AVATAR UPDATED : {os.path.basename(image_path)}")
                return True
            else:
                log("ERROR", f"FAILED TO UPDATE AVATAR : {response.text}")
                return False
        except Exception as e:
            log("ERROR", f"EXCEPTION UPDATING AVATAR : {str(e)}")
            return False

# --- DISCORD FORM FILLER (API-ONLY) ---
class DiscordFormFiller:
    def __init__(self, account_number=1):
        self.mail_client = IncognitoMailClient()
        # self.browser_mgr is now obsolete
        self.humanizer = DiscordHumanizer()
        self.password = None
        self.email = None
        self.token = None
        self.account_number = account_number
        self.username = random_username()
        self.display_name = "Macroo"

    async def _register_account_api(self):
        """API-only registration logic (replaces all browser steps)."""
        if not self.mail_client.inbox_id:
            return None

        self.email = self.mail_client.inbox_id
        self.password = self.mail_client.inbox_token if self.mail_client.inbox_token else "MAXX$" + generate_random_string(8) + "@7836"

        headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Host": "discord.com",
            "Referer": "https://discord.com/register",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
            "X-Discord-Locale": "en-US",
            "X-Discord-Timezone": "America/New_York",
        }

        current_year = datetime.now().year
        birth_year = random.randint(current_year - 30, current_year - 15)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        date_of_birth = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"

        data = {
            'email': self.email,
            'password': self.password,
            'date_of_birth': date_of_birth,
            'username': self.username,
            'global_name': self.display_name,
            'consent': True,
            'captcha_service': 'hcaptcha',
            'captcha_key': None, # This MUST be integrated with a solver API for production use
            'invite': None,
            'promotional_email_opt_in': False,
            'gift_code_sku_id': None
        }

        log("INFO", "ATTEMPTING API REGISTRATION")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://discord.com/api/v9/auth/register',
                    json=data,
                    headers=headers,
                    timeout=20
                )
            
            resp_data = response.json()

            if response.status_code == 201 and 'token' in resp_data:
                self.token = resp_data['token']
                log("SUCCESS", f"Account created via API: Token: {self.token[:12]}...")
                return self.token
            elif response.status_code == 400 and 'captcha_key' in resp_data.get('captcha_sitekey', {}):
                log("ERROR", "Registration requires CAPTCHA solution.")
                # Add CAPTCHA solving integration here
                return None
            elif response.status_code == 429 or 'retry_after' in resp_data:
                limit = resp_data.get('retry_after', 1)
                log("WARNING", f"Rate limit hit. Retrying after {limit} seconds.")
                await asyncio.sleep(int(float(limit)) + 1)
                return await self._register_account_api()
            else:
                log("ERROR", f"API Registration Failed: {response.status_code} - {resp_data.get('message', response.text[:100])}")
                return None

        except httpx.RequestError as e:
            log("ERROR", f"API Request Failed: {e}")
            return None

    async def _verify_email(self):
        """Verifies the email and retrieves the final token (API only)."""
        log("INFO", "Waiting for verification email...")
        
        verification_link = self.mail_client.check_verification_email()
        
        if not verification_link:
            log("ERROR", "No verification link received after timeout.")
            return None

        # Extract the token parameter from the Discord verification link
        match = re.search(r'token=([^&]+)', verification_link)
        if match:
            token_param = match.group(1)
            log("INFO", "Attempting verification via token parameter...")
            
            verify_url = f"https://discord.com/api/v9/auth/verify"
            payload = {"token": token_param}
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
                "Content-Type": "application/json"
            }
            
            try:
                response = requests.post(verify_url, json=payload, headers=headers)
                
                if response.status_code == 200 and 'token' in response.json():
                    final_token = response.json()['token']
                    log("SUCCESS", f"Email Verified. Final Token: {final_token[:12]}...")
                    return final_token
                else:
                    log("ERROR", f"Verification Failed via API: {response.text}")
                    return None
            except Exception as e:
                log("ERROR", f"Exception during API verification: {e}")
                return None
        
        log("ERROR", "Verification link did not contain an extractable token.")
        return None

    async def fill_form(self):
        try:
            send_notification("Account Generation", "Starting new account creation...")
            
            # 1. Create temporary email
            email = await self.mail_client.create_temp_email()
            if not email:
                return None

            self.email = email
            
            # 2. Register account via API
            token = await self._register_account_api()
            
            if not token:
                return None
            
            # 3. Verify email
            self.token = await self._verify_email()

            if self.token:
                # 4. Humanize account
                await self.humanizer.humanize_account(self.token, self.email, self.password)
                
                send_notification("Success", f"Account: {self.token[:12]}...")
                return self.token
            else:
                send_notification("Error", "Failed to complete account verification")
                return None
                
        except asyncio.CancelledError:
            log("INFO", "Account generation cancelled")
            raise
        except Exception as e:
            log("ERROR", f"Account generation failed: {e}")
            return None

# --- MAIN EXECUTION ---
async def main():
    clear_screen()
    print_ascii_logo()
    
    # Create required folders
    for folder in ['data', 'avatar']:
        if not os.path.exists(folder):
            os.makedirs(folder)
            log("INFO", f"Created missing folder: {folder}")
            
    configure_user_options()
    
    if not await validate_license_key(config.get("license_key", "default")):
        log("ERROR", "Invalid license key.")
        return

    try:
        filler = DiscordFormFiller(account_number=1)
        token = await filler.fill_form()
        if token:
            print(f"\n{Fore.LIGHTMAGENTA_EX}Final Token: {token}{Style.RESET_ALL}")
            # Optional: Add code to save the token here
            
    except Exception as e:
        log("ERROR", f"Critical loop error: {e}")
    finally:
        # cleanup_zendriver() is no longer needed
        log("INFO", "Script finished.")

# Run the main async function
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("INFO", "Script terminated by user.")
    except Exception as e:
        log("ERROR", f"Program exception: {e}")
