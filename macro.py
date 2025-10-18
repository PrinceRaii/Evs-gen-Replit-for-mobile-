import pyautogui as ca
import os
import asyncio
import requests
import zendriver as zd
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
from datetime import datetime, timezone, timedelta
from dateutil.parser import isoparse
from colorama import Fore, Style, init
from pystyle import Colorate, Colors, Center
import websocket
from notifypy import Notify


init(autoreset=True)

with open('config.json', 'r') as f:
    config = json.load(f)

INCOGNITO_API_URL = config.get("mail_api", "https://api.incognitomail.co/")
INCOGNITO_DOMAIN = config.get("mail_domain", "vorlentis.xyz")

USE_HUMANIZER = False
USE_VPN = False 

def send_notification(title, message):
    if not config.get("notify", False):
        return
    try:
        notification = Notify()
        notification.application_name = "Discord Account Generator"
        notification.title = title
        notification.message = message
        icon_path = "data/pack.ico"
        if icon_path and os.path.isfile(icon_path):
            notification.icon = icon_path
        notification.send()
    except Exception as e:
        pass

def log(type, message):
    if type.upper() in ["SUCCESS", "ERROR"]:
        now = datetime.now().strftime("%H:%M:%S")
        type_map = {
            "SUCCESS": Fore.GREEN + "SUCCESS" + Style.RESET_ALL,
            "ERROR": Fore.RED + "ERROR" + Style.RESET_ALL
        }
        tag = type_map.get(type.upper(), type.upper())
        print(f"{Fore.LIGHTBLACK_EX}{now}{Style.RESET_ALL} - {tag} • {message}")

def account_ratelimit(email=None, username=None):
    try:
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/json",
            "DNT": "1",
            "Host": "discord.com",
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/register",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
            "TE": "trailers",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "X-Debug-Options": "bugReporterEnabled",
            "X-Discord-Locale": "en-US",
            "X-Discord-Timezone": "America/New_York",
        }
        
        test_email = email if email else ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10)) + "@gmail.com"
        test_username = username if username else ''.join(random.choices(string.ascii_letters, k=8))
        
        data = {
            'email': test_email,
            'password': "TestPassword123!",
            'date_of_birth': "2000-01-01",
            'username': test_username,
            'global_name': test_username,
            'consent': True,
            'captcha_service': 'hcaptcha',
            'captcha_key': None,
            'invite': None,
            'promotional_email_opt_in': False,
            'gift_code_sku_id': None
        }
        
        req = requests.post('https://discord.com/api/v9/auth/register', json=data, headers=headers)
        try:
            resp_data = req.json()
        except Exception:
            return 1
            
        if req.status_code == 429 or 'retry_after' in resp_data:
            limit = resp_data.get('retry_after', 1)
            return int(float(limit)) + 1 if limit else 1
        else:
            return 1
    except Exception as e:
        log("ERROR", f"Rate limit check failed: {e}")
        return 1

def log(type, message):
    now = datetime.now().strftime("%H:%M:%S")
    type_map = {
        "SUCCESS": Fore.GREEN + "SUCCESS" + Style.RESET_ALL,
        "ERROR": Fore.RED + "ERROR" + Style.RESET_ALL,
        "INFO": Fore.CYAN + "INFO" + Style.RESET_ALL,
        "WARNING": Fore.YELLOW + "WARNING" + Style.RESET_ALL
    }
    tag = type_map.get(type.upper(), type.upper())

    if type.upper() == "INFO":
        message = f"{Fore.LIGHTBLACK_EX}{message}{Style.RESET_ALL}"
    elif ':' in message:
        parts = message.split(':', 1)
        key = parts[0].upper().strip()
        val = parts[1].strip()
        message = f"{key}: {Fore.LIGHTBLACK_EX}{val}{Style.RESET_ALL}"

    print(f"{Fore.LIGHTBLACK_EX}{now}{Style.RESET_ALL} - {tag} • {message}")

def get_device_id():
    return socket.gethostname()

def set_console_title(title="Macro token gen!"):
    if os.name == 'nt':
        os.system(f"title {title}")
    else:
        print(f"\33]0;{title}\a", end='', flush=True)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def cleanup_zendriver():
    try:
        import gc
        gc.collect()
        
        for task in asyncio.all_tasks() if hasattr(asyncio, 'all_tasks') else ():
            if not task.done() and task != asyncio.current_task():
                task.cancel()
    except Exception as e:
        log("ERROR", f"Cleanup error: {e}")
        pass

def vertical_gradient(lines, start_rgb=(0, 255, 200), end_rgb=(0, 100, 180)):
    total = len(lines)
    result = []
    for i, line in enumerate(lines):
        r = start_rgb[0] + (end_rgb[0] - start_rgb[0]) * i // max(1, total - 1)
        g = start_rgb[1] + (end_rgb[1] - start_rgb[1]) * i // max(1, total - 1)
        b = start_rgb[2] + (end_rgb[2] - start_rgb[2]) * i // max(1, total - 1)
        result.append(f'\033[38;2;{r};{g};{b}m{line}\033[0m')
    return result

def print_ascii_logo():
    ascii_art = ['''
                                                                                                            
▀████▄     ▄███▀     ██       ▄▄█▀▀▀█▄████▀▀▀██▄   ▄▄█▀▀██▄      ▄█▀▀▀█▄█████▀  ▀████▀▀ ▄▄█▀▀██▄ ▀███▀▀▀██▄ 
  ████    ████      ▄██▄    ▄██▀     ▀█ ██   ▀██▄▄██▀    ▀██▄   ▄██    ▀█ ██      ██  ▄██▀    ▀██▄ ██   ▀██▄
  █ ██   ▄█ ██     ▄█▀██▄   ██▀       ▀ ██   ▄██ ██▀      ▀██   ▀███▄     ██      ██  ██▀      ▀██ ██   ▄██ 
  █  ██  █▀ ██    ▄█  ▀██   ██          ███████  ██        ██     ▀█████▄ ██████████  ██        ██ ███████  
  █  ██▄█▀  ██    ████████  ██▄         ██  ██▄  ██▄      ▄██   ▄     ▀██ ██      ██  ██▄      ▄██ ██       
  █  ▀██▀   ██   █▀      ██ ▀██▄     ▄▀ ██   ▀██▄▀██▄    ▄██▀   ██     ██ ██      ██  ▀██▄    ▄██▀ ██       
▄███▄ ▀▀  ▄████▄███▄   ▄████▄ ▀▀█████▀▄████▄ ▄███▄ ▀▀████▀▀     █▀█████▀▄████▄  ▄████▄▄ ▀▀████▀▀ ▄████▄     
                                                                                                            
                                                                                                            
                                                                                                         
'''
        "Made by Marcus! with love"
    ]

    print('\n' * 2)
    gradient_lines = vertical_gradient(ascii_art)
    for colored_line in gradient_lines:
        print(Center.XCenter(colored_line))
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
        except Exception as e:
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

    def debug_inbox_status(self):
        if not self.inbox_id or not self.inbox_token:
            log("ERROR", "No inbox credentials for debugging")
            return False
            
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
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.post(
                f"{INCOGNITO_API_URL}inbox/v1/list", 
                json=payload, 
                headers=headers, 
                timeout=10
            )
            
            log("INFO", f"API Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                log("INFO", f"Inbox accessible, {len(items)} emails found")
                
                for i, item in enumerate(items[:3]):
                    log("INFO", f"Email {i+1}: messageURL present = {bool(item.get('messageURL'))}")
                    
                return True
            else:
                log("ERROR", f"API Error: {response.text[:100]}")
                return False
                
        except Exception as e:
            log("ERROR", f"Exception: {e}")
            return False

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
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
                    "X-Forwarded-For": fake_ip,
                    "X-Real-IP": fake_ip,
                    "Via": fake_ip
                }
                
                response = httpx.post(
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
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
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
            
            time.sleep(2.0)  # Slowed down from 0.5
        
        log("ERROR", "Verification email not received")
        return None

def check_chrome_installation():
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            return True
    
    log("ERROR", "Chrome not found")
    log("INFO", "Install from: https://www.google.com/chrome/")
    return False

class BrowserManager:
    def __init__(self):
        self.browser = None

    async def start(self, url):
        self.browser = await zd.start()
            
        page = await self.browser.get(url)
        await page.wait_for_ready_state('complete', timeout=30000)
        
        # Press enter after page loads
        ca.press('enter')
        await asyncio.sleep(0.1)
                
        log("SUCCESS", "Registration page opened")
        return page

    async def stop(self):
        if self.browser:
            try:
                await asyncio.wait_for(self.browser.stop(), timeout=5.0)
            except asyncio.TimeoutError:
                log("WARNING", "Browser stop timed out")
            except Exception as e:
                log("ERROR", f"Browser stop error: {e}")
            finally:
                self.browser = None
                log("SUCCESS", "Browser terminated")

class DiscordHumanizer:
    def __init__(self):
        self.config = self.load_config()
        self.customization = self.config.get("CustomizationSettings", {})
        self.load_data_files()
        self.session = tls_client.Session(client_identifier="chrome_115", random_tls_extension_order=True)

    def load_config(self):
        try:
            with open("config.json", "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            log("ERROR", f"Failed to load config.json: {e}")
            return {}

    def load_data_files(self):
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
        try:
            ws = websocket.WebSocket()
            ws.connect('wss://gateway.discord.gg/?v=6&encoding=json')
            hello = json.loads(ws.recv())
            heartbeat_interval = hello['d']['heartbeat_interval'] / 1000

            status = random.choice(['online', 'dnd', 'idle'])
            activity_type = random.choice(['Playing', 'Streaming', 'Watching', 'Listening', ''])

            if activity_type == "Playing":
                gamejson = {"name": "EV GEN", "type": 0}
            elif activity_type == 'Streaming':
                gamejson = {"name": "EV GEN", "type": 1, "url": "https://twitch.tv/c_mposee"}
            elif activity_type == "Listening":
                gamejson = {"name": random.choice(["EV GEN", "EV GEN"]), "type": 2}
            elif activity_type == "Watching":
                gamejson = {"name": "P0rn", "type": 3}
            else:
                gamejson = None

            auth = {
                "op": 2,
                "d": {
                    "token": token,
                    "properties": {
                        "$os": "windows",
                        "$browser": "Chrome",
                        "$device": "Windows"
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
        except Exception as e:
            log("ERROR", f"Error setting offline: {e}")

    async def humanize_account(self, token, email, password):
        if not USE_HUMANIZER:
            return True

        log("INFO", f"HUMANIZING TOKEN : {token[:12]}...")
        
        try:
            ws, _ = self.go_online(token)
            
            if any([self.customization.get("Pronouns"), self.customization.get("DisplayName"), 
                   self.customization.get("Bio"), self.customization.get("HypeSquad")]):
                await self.update_profile_fields(token)

            if self.customization.get("Avatar", False) and self.avatars:
                avatar_path = os.path.join("avatar", random.choice(self.avatars))
                self.update_avatar(token, avatar_path)

            if ws:
                self.set_offline(ws)

            log("SUCCESS", f"FINISHED HUMANIZING TOKEN : {token[:12]}...")
            return True
        except Exception as e:
            log("ERROR", f"Failed to humanize account: {str(e)}")
            return False

    async def update_profile_fields(self, token):
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
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "x-debug-options": "bugReporterEnabled",
            "x-discord-locale": "en-US",
            "x-super-properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImVuLVVTIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzExNi4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTE2LjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwLjAiLCJyZWZlcnJlciI6IiIsInJlZmVycmluZ19kb21haW4iOiIiLCJyZWZlcnJlcl9jdXJyZW50IjoiIiwicmVmZXJyaW5nX2RvbWFpbl9jdXJyZW50IjoiIiwicmVsZWFzZV9jaGFubmVsIjoic3RhYmxlIiwiY2xpZW50X2J1aWxkX251bWJlciI6MjUxNDQxLCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ=="
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
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "x-super-properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImVuLVVTIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEyMC4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTIwLjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwLjAiLCJyZWZlcnJlciI6IiIsInJlZmVycmluZ19kb21haW4iOiIiLCJyZWZlcnJlcl9jdXJyZW50IjoiIiwicmVmZXJyaW5nX2RvbWFpbl9jdXJyZW50IjoiIiwicmVsZWFzZV9jaGFubmVsIjoic3RhYmxlIiwiY2xpZW50X2J1aWxkX251bWJlciI6MjUxNDQxLCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ=="
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

class DiscordFormFiller:
    def __init__(self, account_number=1):
        self.mail_client = IncognitoMailClient()
        self.browser_mgr = BrowserManager()
        self.humanizer = DiscordHumanizer()
        self.password = None
        self.email = None
        self.token = None
        self.account_number = account_number

    async def fill_form(self):
        try:
            send_notification("Account Generation", "Starting new account creation...")
            
            email = await self.mail_client.create_temp_email()
            if not email:
                send_notification("Error", "Failed to create temporary email")
                log("ERROR", "Failed to create email")
                return None

            self.email = email
            
            try:
                page = await self.browser_mgr.start("https://discord.com/register")
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log("ERROR", f"Failed to start browser: {e}")
                return None
            
            try:
                await self._fill_basic_fields(page, email)
                await self._select_birth_date(page)
                
                log("SUCCESS", "Fields filled!")
                
                await self._wait_for_captcha_completion(page)
                
                
                token = await self._verify_email()
                
                await self.browser_mgr.stop()
                
                if token:
                    send_notification("Success", f"Account: {token[:12]}...")
                    return token
                else:
                    send_notification("Error", "Failed to complete account verification")
                    return None
                
            except asyncio.CancelledError:
                log("INFO", "Form filling cancelled")
                raise
            except Exception as e:
                log("ERROR", f"Form filling failed: {e}")
                try:
                    await self.browser_mgr.stop()
                except Exception:
                    pass
                return None
                
        except asyncio.CancelledError:
            log("INFO", "Account generation cancelled")
            try:
                await self.browser_mgr.stop()
            except Exception:
                pass
            raise
        except Exception as e:
            log("ERROR", f"Account generation failed: {e}")
            try:
                await self.browser_mgr.stop()
            except Exception:
                pass
            return None

    async def _countdown_timer(self, duration):
        for i in range(duration):
            remaining = duration - i
            log("INFO", f"Waiting... {remaining}s remaining")
            await asyncio.sleep(1)

    async def _fill_basic_fields(self, page, email):
        # Press enter first when loading the page
        ca.press('enter')
        await asyncio.sleep(0.1)
        
        display_name = "Macroo"
        username = random_username()
        password = self.mail_client.inbox_token
        
        if not password:
            password = "MAXX$" + generate_random_string(8) + "@7836"

        email_field = await page.wait_for('input[name="email"]', timeout=15000)
        await email_field.send_keys(self.mail_client.inbox_id)
        await asyncio.sleep(0.05)

        display_name_field = await page.wait_for('input[name="global_name"]', timeout=15000)
        await display_name_field.send_keys(display_name)
        await asyncio.sleep(0.05)

        username_field = await page.wait_for('input[name="username"]', timeout=15000)
        await username_field.send_keys(username)
        await asyncio.sleep(0.05)

        password_field = await page.wait_for('input[name="password"]', timeout=15000)
        await password_field.send_keys(password)
        
        self.password = password
        self.email = self.mail_client.inbox_id

    async def _select_birth_date(self, page):
        try:
            await asyncio.sleep(0.1)
            
            ca.press('tab')
            await asyncio.sleep(0.05)
            
            # Select January (first month) - press space and then enter immediately
            ca.press('space')
            await asyncio.sleep(0.05)
            ca.press('enter')
            await asyncio.sleep(0.05)
            ca.press('tab')
            
            # Select day 1 - press space and then enter immediately
            ca.press('space')
            await asyncio.sleep(0.05)
            ca.press('enter')
            await asyncio.sleep(0.05)
            ca.press('tab')
            
            # Select year 2001 - navigate directly to this year with faster movements
            ca.press('space')
            await asyncio.sleep(0.05)
            
            # Navigate to 2001 (24 down presses from 1970) - but do it faster
            for _ in range(24):
                ca.press('down')
            ca.press('enter')
            
            await asyncio.sleep(0.1)
            
            # Use direct JavaScript for checkbox clicking for better performance
            try:
                await page.evaluate('''
                    (function() {
                        const checkboxes = document.querySelectorAll('input[type="checkbox"]:not([disabled])');
                        for (let i = 0; i < checkboxes.length; i++) {
                            const checkbox = checkboxes[i];
                            if (checkbox.offsetParent !== null) {
                                checkbox.click();
                                return true;
                            }
                        }
                        return false;
                    })();
                ''')
            except Exception as e:
                pass
            
            await asyncio.sleep(0.1)
            
            # Use direct JavaScript for submit button clicking
            try:
                await page.evaluate('''
                    (function() {
                        const selectors = [
                            'button[type="submit"]',
                            'button[class*="button"]',
                            'button'
                        ];
                        
                        for (let i = 0; i < selectors.length; i++) {
                            const selector = selectors[i];
                            const buttons = document.querySelectorAll(selector);
                            for (let j = 0; j < buttons.length; j++) {
                                const button = buttons[j];
                                if (button.offsetParent !== null && 
                                    !button.disabled) {
                                    const text = button.textContent.toLowerCase();
                                    if (text.includes('continue') || 
                                        text.includes('next') ||
                                        text.trim() !== '') {
                                        button.click();
                                        return true;
                                    }
                                }
                            }
                        }
                        return false;
                    })();
                ''')
            except Exception as e:
                ca.press('enter')
            
            await asyncio.sleep(1)

        except Exception as e:
            pass

    async def _wait_for_captcha_completion(self, page):
        try:
            captcha_detected = False
            attempt = 0
            while True:
                try:
                    captcha_elements = [
                        'iframe[src*="hcaptcha"]',
                        'iframe[src*="recaptcha"]', 
                        'div[class*="captcha"]',
                        '.h-captcha',
                        '.g-recaptcha',
                        '[data-sitekey]'
                    ]
                    
                    captcha_found = False
                    for selector in captcha_elements:
                        captcha = await page.query_selector(selector)
                        if captcha:
                            captcha_found = True
                            break
                    
                    if captcha_found and not captcha_detected:
                        log("INFO", "Waiting for you to solve captcha...")
                        send_notification("Captcha", "Please solve the CAPTCHA manually")
                        captcha_detected = True
                    
                    if not captcha_found:
                        if captcha_detected:
                            log("SUCCESS", "Captcha solved successfully!")
                            send_notification("Success", "CAPTCHA solved, continuing...")
                        return True
                    
                    await asyncio.sleep(1.0)  # Slowed down from 0.2
                    attempt += 1
                        
                except asyncio.CancelledError:
                    raise
                except Exception:
                    pass
                    
        except asyncio.CancelledError:
            log("INFO", "Captcha wait cancelled")
            raise
        except Exception as e:
            log("WARNING", f"Captcha wait error: {e}")
            return True

    def get_token(self, inbox_id=None, inbox_token=None):
        try:
            login_id = inbox_id or self.mail_client.inbox_id
            login_password = inbox_token or self.mail_client.inbox_token
            
            if not login_id or not login_password:
                return None
                
            payload = {
                'login': login_id,
                'password': login_password
            }
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Origin': 'https://discord.com',
                'Referer': 'https://discord.com/login'
            }
            
            res = requests.post('https://discord.com/api/v9/auth/login', json=payload, headers=headers)
            
            if res.status_code == 200:
                try:
                    response_data = res.json()
                    if 'token' in response_data:
                        token = response_data['token']
                        log("SUCCESS", f"Token: {token[:12]}...")
                        
                        os.makedirs("OUTPUT", exist_ok=True)
                        
                        with open("OUTPUT/tokens.txt", "a", encoding="utf-8") as tf:
                            tf.write(token + "\n")
                        
                        with open("OUTPUT/accounts.txt", "a", encoding="utf-8") as af:
                            af.write(f"{login_id}:{login_password}:{token}\n")
                        
                        self.token = token
                        return token
                except json.JSONDecodeError:
                    pass
                
        except Exception:
            pass
        return None

    def check_email_verified_api(self, token):
        url = "https://discord.com/api/v9/users/@me"
        headers = {
            "Authorization": token,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "DNT": "1",
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/channels/@me",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Debug-Options": "bugReporterEnabled",
            "X-Discord-Locale": "en-US",
            "X-Super-Properties": "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImVuLVVTIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzEyMC4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTIwLjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwLjAiLCJyZWZlcnJlciI6IiIsInJlZmVycmluZ19kb21haW4iOiIiLCJyZWZlcnJlcl9jdXJyZW50IjoiIiwicmVmZXJyaW5nX2RvbWFpbl9jdXJyZW50IjoiIiwicmVsZWFzZV9jaGFubmVsIjoic3RhYmxlIiwiY2xpZW50X2J1aWxkX251bWJlciI6MjUxNDQxLCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ=="
        }
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                verified = data.get("verified", False)
                email = data.get("email", "No Email")
                return verified, email
            else:
                return None, None
        except:
            return None, None

    async def _verify_email(self):
        for attempt in range(150):
            try:
                verification_link = self.mail_client.check_verification_email()
                if verification_link:
                    break
                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                log("INFO", "Verification check cancelled")
                return None
            except Exception:
                pass
        
        if not verification_link:
            return None

        verification_browser = None
        try:
            log("SUCCESS", "Opening verification link...")
            verification_browser = await zd.start()
            page = await verification_browser.get(verification_link)
            await asyncio.sleep(1.0)

            token = None
            for check_attempt in range(80):
                try:
                    token = self.get_token(self.mail_client.inbox_id, self.mail_client.inbox_token)
                    if token:
                        break
                    await asyncio.sleep(0.5)
                except asyncio.CancelledError:
                    log("INFO", "Token check cancelled")
                    return None
                except Exception:
                    pass

            if not token:
                return None

            verification_complete = False
            
            for verify_attempt in range(300):
                try:
                    verified, email_address = self.check_email_verified_api(token)
                    if verified:
                        verification_complete = True
                        log("SUCCESS", "Email verified successfully!")
                        break
                    await asyncio.sleep(0.5)
                except asyncio.CancelledError:
                    log("INFO", "Email verification cancelled")
                    return None
                except Exception:
                    pass
            
            if not verification_complete:
                return None
                
            if USE_HUMANIZER and self.humanizer.config.get("Humanize", False):
                try:
                    await self.humanizer.humanize_account(
                        token, 
                        self.mail_client.inbox_id, 
                        self.mail_client.inbox_token
                    )
                    log("SUCCESS", "Account humanized successfully")
                except asyncio.CancelledError:
                    log("INFO", "Humanization cancelled")
                except Exception as e:
                    log("ERROR", f"Humanization failed: {e}")
            
            return token
            
        except asyncio.CancelledError:
            log("INFO", "Verification process cancelled")
            return None
        except Exception as e:
            log("ERROR", f"Verification error: {e}")
            return None
        finally:
            if verification_browser:
                try:
                    await asyncio.wait_for(verification_browser.stop(), timeout=3.0)
                except:
                    pass

async def main():
    clear_screen()
    set_console_title()
    
    if not check_chrome_installation():
        log("ERROR", "Chrome not installed")
        input("Press Enter to exit...")
        return
    
    configure_user_options()
    print_ascii_logo()
    
    try:
        rizzler_runs = int(input(f"{Fore.CYAN}[+] Number of accounts to generate (0 = infinite): {Style.RESET_ALL}"))
    except ValueError:
        rizzler_runs = 1
    
    run_count = 0
    
    try:
        while True:
            if rizzler_runs != 0 and run_count >= rizzler_runs:
                break
                
            run_count += 1
            log("SUCCESS", f"Starting account {run_count} generation...")
            
            try:
                filler = DiscordFormFiller(account_number=run_count)
                token = await filler.fill_form()
                
                if token:
                    log("SUCCESS", "Account created successfully")
                else:
                    log("ERROR", f"Account {run_count} generation failed")
            except asyncio.CancelledError:
                log("INFO", "Generation task cancelled")
                break
            except Exception as e:
                log("ERROR", f"Error generating account: {e}")
            
            if rizzler_runs == 1:
                break
            elif rizzler_runs != 0 and run_count >= rizzler_runs:
                break
            else:
                wait_time = 30 if USE_VPN else 200  # Increased wait times
                
                log("INFO", f"Waiting {wait_time}s before generating next account ({'VPN' if USE_VPN else 'No VPN'} mode)")
                try:
                    await asyncio.sleep(wait_time)
                except asyncio.CancelledError:
                    break
                
    except KeyboardInterrupt:
        log("SUCCESS", "Exiting...")
    except asyncio.CancelledError:
        log("INFO", "Main task cancelled")
    except Exception as e:
        log("ERROR", f"Generation error: {e}")
    finally:
        cleanup_zendriver()
        log("SUCCESS", "Finished generating tokens!")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting gracefully...")
    except asyncio.CancelledError:
        print("\nAsyncio tasks were cancelled. Exiting gracefully...")
    except Exception as e:
        print(f"\nUnexpected error: {e}")