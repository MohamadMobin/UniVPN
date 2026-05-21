import requests
import time
import datetime
import sys

# آدرس دقییق ورود به شبکه دانشگاه یا سازمان
LOGIN_URL = "http://YourUniSite.ir/login" #or http://192.168.X.X/login
LOGOUT_URL = "http://YourUniSite.ir/logout" 
TEST_URL = "https://aparat.com" # سایتی ترجیحا ایرانی انتخاب شود

# در صورت محدودیت حجم مصرفی چند اکانت اضافه کنید
ACCOUNTS = [
    {"username": "user1", "password": "pass1"},
    {"username": "user2", "password": "pass2"},
]

session = requests.Session()

def log_print(message):
    """چاپ پیام با قابلیت نمایش فوری در لاگ‌های لینوکس درصورت نیاز"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

def is_connected():
    try:
        response = session.get(TEST_URL, timeout=10)
        return response.status_code == 204
    except requests.RequestException:
        return False

def verify_connection():
    for _ in range(3): #سه بار تلاش برای لاگین کردن برای هر اکانت
        if is_connected():
            return True
        time.sleep(5)
    return False

def login(username, password):
    try:
        payload = {"username": username, "password": password}
        response = session.post(LOGIN_URL, data=payload, timeout=10)
        log_print(f"POST /login -> Status {response.status_code} for user {username}")
        # در صورت نیاز به دیباگ بیشتر می‌توانید response.text را اینجا لاگ کنید
    except Exception as e:
        log_print(f"Login connection error: {e}")

def logout():
    try:
        session.post(LOGOUT_URL, timeout=10)
        log_print("Logout request sent.")
    except Exception as e:
        log_print(f"Logout failed: {e}")

if __name__ == "__main__":
    log_print("Auto-Login script started")
    current_idx = 0
    last_reset = None

    while True:
        try:
            today = datetime.date.today()
            # ریست هفتگی (شنبه = روز 5 در پایتون)
            if today.weekday() == 5 and today != last_reset:
                log_print("Weekly reset triggered: switching to first account.")
                logout()
                current_idx = 0
                last_reset = today
                time.sleep(2)
                continue

            if verify_connection():
                time.sleep(60)
                continue

            log_print("No internet access. Waiting 5 sec before login attempt...")
            time.sleep(5)

            acc = ACCOUNTS[current_idx]
            log_print(f"Trying account: {acc['username']}")
            login(acc["username"], acc["password"])
            
            # صبر برای اعمال شدن اتصال در شبکه دانشگاه
            time.sleep(15)

            if is_connected():
                log_print("Internet connected successfully.")
                continue

            log_print(f"Account {acc['username']} failed (no volume/invalid). Switching to next...")
            logout()
            time.sleep(2)
            current_idx = (current_idx + 1) % len(ACCOUNTS)
            
        except Exception as main_e:
            log_print(f"Unexpected error in main loop: {main_e}")
            time.sleep(10) # جلوگیری از مصرف منابع در صورت کرش مداوم حلقه
