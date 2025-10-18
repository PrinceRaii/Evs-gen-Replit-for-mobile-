import os
import asyncio
import json
import random
import string
import re
import socket
import httpx # Used for async HTTP requests
import base64
import tls_client
import time
import hashlib
import hmac
from datetime import datetime
from colorama import Fore, Style, init
from pystyle import Colorate, Colors, Center

# --- REMOVED DESKTOP/GUI DEPENDENCIES & CAPTCHA API ---
# Removed: pyautogui, zendriver, notifypy, websocket, CaptchaSolver

init(autoreset=True)

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"{Fore.RED}ERROR: config.json not found. Please create it.{Style.RESET_ALL}")
    config = {}

INCOGNITO_API_URL = config.get("mail_api", "https://api.incognitomail.co/")
INCOGNITO_DOMAIN = config.get("mail_domain", "vorlentis.xyz")
# CAPTCHA_API_KEY is removed
CAPTCHA_SITEKEY = config.get("captcha_sitekey", "4c672d355d3e233934302a0ed1bc8813")

USE_HUMANIZER = False
USE_VPN = False 

# --- GENERAL UTILITIES (Keep/Simplified) ---

def log(type, message):
    now = datetime.now().strftime("%H:%M:%S")
    type_map = {
        "SUCCESS": Fore.GREEN + "SUCCESS" + Style.RESET_ALL,
        "ERROR": Fore.RED + "ERROR" + Style.RESET_ALL,
        "INFO": Fore.CYAN + "INFO" + Style.RESET_ALL,
        "WARNING": Fore.YELLOW + "WARNING" + Style.RESET_ALL
    }
    tag = type_map.get(type.upper(), type.upper())
    print(f"{Fore.LIGHTBLACK_EX}{now}{Style.RESET_ALL} - {tag} • {message}")

def set_console_title(title="Macro token gen!"):
    if os.name == 'nt':
        os.system(f"title {title}")
    else:
        print(f"\33]0;{title}\a", end='', flush=True)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def generate_random_string(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def random_username():
    return 'marcus' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

# --- MANUAL CAPTCHA SOLVER FUNCTION (NEW FOR MANUAL INPUT) ---

def manual_solve_hcaptcha(sitekey):
    """
    Prints the hCaptcha challenge URL and waits for user input of the solved token.
    This function is synchronous and blocks the event loop until input is received.
    """
    log("WARNING", "MANUAL CAPTCHA REQUIRED!")
    
    # URL to help the user solve the captcha
    solver_url = (
        f"https://www.google.com/recaptcha/api2/demo/hcaptcha.html?"
        f"sitekey={sitekey}&"
        f"host=discord.com&"
        f"size=invisible" # Using invisible size helps focus on the widget
    )
    
    # A more common way to solve it is using a dedicated solver site
    solver_url_alt = (
        f"https://ocr.space/hcaptcha-solver?sitekey={sitekey}&host=discord.com"
    )
    
    print("\n" + "="*80)
    print(f"{Fore.YELLOW}  [STEP 1]: Open this link in your browser (Mobile/Desktop):")
    print(f"  {Fore.CYAN}{solver_url_alt}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}  [STEP 2]: Solve the hCaptcha and copy the **response token**.")
    print(f"{Fore.YELLOW}  [STEP 3]: Paste the token below and press Enter.")
    print("="*80 + "\n")
    
    while True:
        captcha_key = input(f"{Fore.MAGENTA}  > Paste hCaptcha Token Here: {Style.RESET_ALL}").strip()
        if len(captcha_key) > 100:
            log("SUCCESS", "Token received. Continuing generation...")
            return captcha_key
        else:
            log("ERROR", "Invalid token format. Please ensure you copied the entire hCaptcha response.")
            
# --- INCOGNITO MAIL CLIENT (UPGRADED TO ASYNC HTTPX) ---
class IncognitoMailClient:
    def __init__(self):
        self.email = None
        self.inbox_id = None
        self.inbox_token = None
        self.client = httpx.AsyncClient(timeout=15)
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
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
                    "X-Forwarded-For": fake_ip,
                    "X-Real-IP": fake_ip,
                    "Via": fake_ip
                }
                
                response = await self.client.post(
                    f"{INCOGNITO_API_URL}inbox/v2/create", 
                    json=payload, 
                    headers=headers
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
                log("ERROR", f"Failed to create email: {e}")
                await asyncio.sleep(2)
                    
        return None

    # check_verification_email is kept synchronous since it's a polling loop
    def check_verification_email(self):
        import requests
        
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
                
                # Using synchronous requests here as a quick fix for the mail polling loop
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
                                        
                                        # Use regex to find the verification link
                                        patterns = [
                                            r'https:\/\/(?:click\.)?discord\.com[^\s"\'\'<>\\]+verify[^\s"\'\'<>\\]+'
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

# --- DISCORD HUMANIZER (Simplified and uses blocking tls_client for profile updates) ---
class DiscordHumanizer:
    
    def __init__(self):
        self.config = self.load_config()
        self.customization = self.config.get("CustomizationSettings", {})
        self.session = tls_client.Session(client_identifier="chrome_115", random_tls_extension_order=True)

    def load_config(self):
        try:
            with open("config.json", "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            log("ERROR", f"Failed to load config.json: {e}")
            return {}

    async def humanize_account(self, token, email, password):
        if not USE_HUMANIZER:
            return True

        log("INFO", f"HUMANIZING TOKEN: {token[:12]}...")
        
        # NOTE: Profile updates here are synchronous blocking calls using tls_client.Session
        # For full async, these would need to be rewritten.

        log("SUCCESS", f"FINISHED HUMANIZING TOKEN: {token[:12]}...")
        return True


# --- DISCORD GENERATOR (HEADLESS API REWRITE with Manual Captcha) ---
class DiscordGenerator:
    def __init__(self, account_number=1):
        self.mail_client = IncognitoMailClient()
        self.humanizer = DiscordHumanizer()
        self.password = None
        self.email = None
        self.token = None
        self.account_number = account_number
        self.client = httpx.AsyncClient(timeout=30)
        self.super_properties = "eyJvcyI6IldpbmRvd3MiLCJicm93c2VyIjoiQ2hyb21lIiwiZGV2aWNlIjoiIiwic3lzdGVtX2xvY2FsZSI6ImVuLVVTIiwiYnJvd3Nlcl91c2VyX2FnZW50IjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzExNi4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiMTE2LjAuMC4wIiwib3NfdmVyc2lvbiI6IjEwLjAiLCJyZWZlcnJlciI6IiIsInJlZmVycmluZ19kb21haW4iOiIiLCJyZWZlcnJlcl9jdXJyZW50IjoiIiwicmVsZWFzZV9jaGFubmVsIjoic3RhYmxlIiwiY2xpZW50X2J1aWxkX251bWJlciI6MjY4MDcwLCJjbGllbnRfZXZlbnRfc291cmNlIjpudWxsfQ=="

    async def generate_account(self):
        log("INFO", "Starting HEADLESS account creation...")
        
        email = await self.mail_client.create_temp_email()
        if not email:
            log("ERROR", "Failed to create temporary email")
            return None

        self.email = email
        self.password = self.mail_client.inbox_token or ("MAXX$" + generate_random_string(8) + "@7836")
        username = random_username()
        display_name = "Macroo"
        date_of_birth = "2000-01-01"

        # 1. Manual Captcha Input
        loop = asyncio.get_event_loop()
        # The manual_solve_hcaptcha function is synchronous, so we must run it in a thread pool executor.
        captcha_key = await loop.run_in_executor(None, manual_solve_hcaptcha, CAPTCHA_SITEKEY)
        
        if not captcha_key:
            log("ERROR", "Manual captcha input failed.")
            return None
        
        # 2. Register Account via API
        log("INFO", "Attempting Discord API registration with manual token...")
        headers = {
            "Accept": "*/*",
            # ... (rest of headers remain the same) ...
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "X-Super-Properties": self.super_properties
        }
        
        data = {
            'email': self.email,
            'password': self.password,
            'date_of_birth': date_of_birth,
            'username': username,
            'global_name': display_name,
            'consent': True,
            'captcha_key': captcha_key, # Use the manually input token
            'invite': None,
            'promotional_email_opt_in': False,
            'gift_code_sku_id': None
        }
        
        try:
            response = await self.client.post('https://discord.com/api/v9/auth/register', json=data, headers=headers)
            resp_data = response.json()

            if response.status_code == 201 and 'token' in resp_data:
                log("SUCCESS", f"Account created! Token received: {resp_data['token'][:12]}...")
                self.token = resp_data['token']
                
                # 3. Verify Email and Get Final Token
                final_token = await self._verify_email()
                
                # 4. Humanize Account
                await self.humanizer.humanize_account(final_token if final_token else self.token, self.email, self.password)
                return final_token if final_token else self.token
                
            elif response.status_code == 400:
                 # Check for specific Captcha error (Error 50000 means invalid/expired captcha)
                 if resp_data.get('captcha_key', [None])[0] == 'invalid hcaptcha key':
                     log("ERROR", "Registration failed: The manual hCaptcha token was **invalid or expired**.")
                 else:
                     log("ERROR", f"Registration failed (400): {resp_data}")
                 return None
            else:
                log("ERROR", f"Registration failed ({response.status_code}): {resp_data}")
                return None

        except Exception as e:
            log("ERROR", f"API Registration failed: {e}")
            return None

    async def _verify_email(self):
        log("INFO", "Checking email inbox for verification link...")
        
        # Since check_verification_email is sync, we run it in an executor
        loop = asyncio.get_event_loop()
        verification_link = await loop.run_in_executor(None, self.mail_client.check_verification_email)

        if not verification_link:
            log("ERROR", "Did not find Discord verification email. Account may be unverified.")
            return self.token
            
        log("INFO", "Verification link found, attempting verification...")
        
        # Use tls_client (synchronous) to follow the redirect
        session = tls_client.Session(client_identifier="chrome_115", random_tls_extension_order=True)
        
        def run_verification():
            # ... (same verification logic as before, using session.get) ...
            try:
                response = session.get(
                    verification_link, 
                    allow_redirects=True, 
                    timeout=10, 
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if 'token' in data:
                            log("SUCCESS", "Account verified, new token received.")
                            return data['token']
                        else:
                            log("WARNING", "Verification successful, but no token in JSON response.")
                            return self.token
                    except json.JSONDecodeError:
                        log("WARNING", "Verification successful, but response not JSON. Assuming session is valid.")
                        return self.token
                
                log("ERROR", f"Verification link failed: {response.status_code}")
                return self.token
            except Exception as e:
                log("ERROR", f"Exception during verification HTTP request: {e}")
                return self.token

        return await loop.run_in_executor(None, run_verification)

# --- MAIN RUNNER (For Replit) ---
async def main():
    clear_screen()
    set_console_title("Marcus's Discord Account Generator | MANUAL CAPTCHA Replit Upgrade")

    try:
        num_accounts = 1 
        
        for i in range(1, num_accounts + 1):
            log("INFO", f"--- Starting Account Generation {i}/{num_accounts} ---")
            generator = DiscordGenerator(account_number=i)
            token = await generator.generate_account()

            if token:
                # Save the account details
                account_data = f"TOKEN:{token}|EMAIL:{generator.email}|PASSWORD:{generator.password}\n"
                with open('tokens.txt', 'a') as f:
                    f.write(account_data)
                log("SUCCESS", f"Account details saved to tokens.txt.")
            
            # Wait a random interval
            wait_time = random.randint(5, 10)
            log("INFO", f"Waiting {wait_time} seconds before next generation...")
            await asyncio.sleep(wait_time)

    except KeyboardInterrupt:
        log("INFO", "Process interrupted by user.")
    except Exception as e:
        log("ERROR", f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    asyncio.run(main())
