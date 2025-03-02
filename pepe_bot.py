from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import json
import threading
import cv2
import numpy as np
from fake_useragent import UserAgent
import random

ua = UserAgent()
options = Options()
options.add_argument(f"--user-agent={ua.random}")
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-gpu")
options.add_argument("--disable-dev-shm-usage")

def solve_image_captcha(driver):
    try:
        main_img = driver.find_element_by_xpath("//img[contains(@class, 'captcha-main')]")
        main_img.screenshot("main.png")
        main_cv = cv2.imread("main.png", cv2.IMREAD_GRAYSCALE)
        main_cv = cv2.resize(main_cv, (50, 50))

        options = driver.find_elements_by_xpath("//img[contains(@class, 'captcha-option')]")
        best_match = None
        best_score = float('inf')

        for i, opt in enumerate(options):
            opt.screenshot(f"opt_{i}.png")
            opt_cv = cv2.imread(f"opt_{i}.png", cv2.IMREAD_GRAYSCALE)
            opt_cv = cv2.resize(opt_cv, (50, 50))
            diff = cv2.absdiff(main_cv, opt_cv)
            score = np.sum(diff)
            if score < best_score:
                best_score = score
                best_match = i

        options[best_match].click()
        time.sleep(random.uniform(0.1, 0.3))  # فاصله تصادفی برای طبیعی بودن
        return True
    except:
        return False

def create_new_account(base_email, index):
    driver = webdriver.Chrome(options=options)
    driver.get("https://earn-pepe.com/register")
    email = f"{base_email.split('@')[0]}+{index}@gmail.com"
    driver.find_element_by_name("email").send_keys(email)
    driver.find_element_by_name("password").send_keys(f"PepePass{index}")
    driver.find_element_by_name("confirm-password").send_keys(f"PepePass{index}")
    driver.find_element_by_css_selector("button[type='submit']").click()
    time.sleep(random.uniform(2, 4))  # طبیعی‌تر
    if solve_image_captcha(driver):
        print(f"حساب جدید {email} ساخته شد")
        driver.quit()
        return {"email": email, "pass": f"PepePass{index}", "active": True, "fails": 0, "balance": 0}
    driver.quit()
    return None

def claim_and_withdraw(account, main_email):
    driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://earn-pepe.com/login")
        driver.find_element_by_name("email").send_keys(account["email"])
        driver.find_element_by_name("password").send_keys(account["pass"])
        driver.find_element_by_css_selector("button[type='submit']").click()
        time.sleep(random.uniform(1, 2))  # تاخیر طبیعی

        # حلقه برای 60 کلیم در 60 ثانیه
        start_time = time.time()
        claims = 0
        while claims < 60 and time.time() - start_time < 60:
            driver.get("https://earn-pepe.com/claim")
            if not solve_image_captcha(driver):
                account["fails"] += 1
                if account["fails"] >= 3:
                    raise Exception("خطای کپچا چندباره")
                time.sleep(random.uniform(1, 2))
                continue
            driver.find_element_by_id("claim_button").click()
            claims += 1
            account["balance"] += 6
            time.sleep(random.uniform(0.8, 1.0))  # فاصله تصادفی برای 60 کلیم

        # چک و برداشت
        driver.get("https://earn-pepe.com/withdraw")
        balance = float(driver.find_element_by_id("balance").text)
        account["balance"] = balance
        if balance >= 10000:  # حداقل برداشت ۱۰,۰۰۰ پپه
            driver.find_element_by_id("withdraw_email").send_keys(main_email)
            driver.find_element_by_id("withdraw").click()
            account["balance"] = 0
            print(f"برداشت {balance} پپه از {account['email']} به {main_email}")

        account["fails"] = 0
        driver.quit()
        print(f"حساب {account['email']} جمع کرد: {claims * 6} پپه")
        return True
    except Exception as e:
        print(f"خطا با {account['email']}: {e}")
        driver.quit()
        return False

# اجرا اصلی
base_email = "aradirad2@gmail.com"  # ایمیلت برای ساخت حساب‌ها
main_email = "aradirad2@gmail.com"  # ایمیلت برای برداشت به Cwallet
account_index = 0
accounts = []

# بارگذاری یا ساخت حساب‌ها
try:
    with open("accounts.json", "r") as f:
        accounts = json.load(f)
    account_index = len(accounts)
except FileNotFoundError:
    for i in range(5):  # 5 حساب اولیه
        acc = create_new_account(base_email, i)
        if acc:
            accounts.append(acc)
    with open("accounts.json", "w") as f:
        json.dump(accounts, f)

# اجرای موازی برای 5 حساب
def run_account(acc):
    if acc["active"]:
        if not claim_and_withdraw(acc, main_email):
            if acc["fails"] >= 3:
                acc["active"] = False
                new_acc = create_new_account(base_email, globals()["account_index"])
                if new_acc:
                    accounts.append(new_acc)
                    globals()["account_index"] += 1
    with open("accounts.json", "w") as f:
        json.dump(accounts, f)

threads = []
for acc in accounts[:5]:  # فقط 5 حساب همزمان
    t = threading.Thread(target=run_account, args=(acc,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
