import os
import json
import time
import threading
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
REFRESH_INTERVAL = 35  # секунд
LOGIN_URL = "https://wsp.kbtu.kz/RegistrationOnline"


def load_users():
    """Load users from users.json"""
    config_path = os.path.join(os.path.dirname(__file__), "users.json")
    with open(config_path, "r") as f:
        return json.load(f)


def send_telegram_message(chat_id, message):
    """Sends a message via Telegram bot to specific chat_id"""
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")
        return False


def do_login(driver, wait, username, password):
    """Выполняет логин и возвращает True при успехе"""
    print(f"[{username}] Attempting login...")
    driver.get(LOGIN_URL)
    print(f"[{username}] Page opened successfully!")

    # Username - это combobox (выпадающий список с возможностью ввода)
    # Ищем input внутри v-filterselect
    username_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[contains(@class, 'v-filterselect-input')]")))
    username_field.clear()
    username_field.send_keys(username)
    time.sleep(0.5)  # дать время на ввод
    actual_username = username_field.get_attribute('value')
    print(f"[{username}] Entered username: {username} (actual in field: {actual_username})")

    # Password field
    password_field = driver.find_element(By.XPATH, "//input[@type='password']")

    password_field.clear()
    password_field.send_keys(password)
    actual_password = password_field.get_attribute('value')
    print(f"[{username}] Entered password (actual length: {len(actual_password) if actual_password else 0})")

    login_button = driver.find_element(By.XPATH, "//div[contains(@class, 'v-button') and contains(@class, 'primary')]")
    print(f"[{username}] Login button text: {login_button.text}")
    login_button.click()
    print(f"[{username}] Clicked login button")

    time.sleep(5)  # ждём дольше

    # Сохраняем скриншот
    driver.save_screenshot(f"/tmp/login_result_{username}.png")
    print(f"[{username}] Screenshot saved to /tmp/login_result_{username}.png")
    print(f"[{username}] After login URL: {driver.current_url}")

    # DEBUG: ищем ошибки на странице
    try:
        errors = driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(@class, 'v-Notification') or contains(@class, 'warning')]")
        for err in errors:
            if err.text.strip():
                print(f"[{username}]   [ERROR ON PAGE] {err.text}")
    except:
        pass

    # DEBUG: выведем весь текст на странице
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
        # Возьмем первые 500 символов
        print(f"[{username}]   [PAGE TEXT] {body_text[:500]}")
    except:
        pass

    # DEBUG: проверяем какие кнопки после логина
    try:
        all_buttons = driver.find_elements(By.XPATH, "//span[@class='v-button-caption']")
        btn_texts = [b.text for b in all_buttons if b.text.strip()]
        print(f"[{username}]   [POST-LOGIN BUTTONS] {btn_texts}")
        if 'Кіру' in btn_texts or 'Войти' in btn_texts:
            print(f"[{username}]   !!! LOGIN FAILED - still on login page !!!")
        else:
            print(f"[{username}]   LOGIN SUCCESS - inside the app")
    except Exception as e:
        print(f"[{username}]   Error checking buttons: {e}")

    return True


def is_session_expired(driver):
    """Проверяет, истекла ли сессия (появилась форма логина)"""
    try:
        # Проверяем наличие кнопки "Кіру" (казахский) или формы логина
        buttons = driver.find_elements(By.XPATH, "//span[@class='v-button-caption']")
        for btn in buttons:
            if btn.text in ['Кіру', 'Войти', 'Login']:
                return True
        # Также проверяем наличие полей логина
        login_fields = driver.find_elements(By.XPATH, "//input[@type='password']")
        if login_fields:
            return True
        return False
    except:
        return False


def run_for_user(user):
    """Run the attendance checker for a single user"""
    username = user["username"]
    password = user["password"]
    chat_id = user.get("telegram_chat_id")

    print(f"[{username}] Starting...")
    options = Options()
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--headless")  # без GUI для сервера
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    print(f"[{username}] Launching Chrome (headless)...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)

    try:
        do_login(driver, wait, username, password)

        # Цикл обновления
        refresh_count = 0
        while True:
            refresh_count += 1
            print(f"\n[{username}] [{time.strftime('%H:%M:%S')}] Refresh #{refresh_count}")

            # Вместо refresh() - переходим на URL заново (refresh может сбрасывать сессию)
            driver.get(LOGIN_URL)
            time.sleep(3)  # ждём загрузку страницы

            # DEBUG: показываем текущий URL и все кнопки
            print(f"[{username}]   [URL] {driver.current_url}")
            try:
                all_buttons = driver.find_elements(By.XPATH, "//span[@class='v-button-caption']")
                btn_texts = [b.text for b in all_buttons if b.text.strip()]
                print(f"[{username}]   [ALL BUTTONS] {btn_texts}")
            except:
                pass

            # Проверяем, не истекла ли сессия (кнопка Кіру видна = нужен логин)
            if is_session_expired(driver):
                print(f"[{username}] >>> Session expired! Re-logging in...")
                do_login(driver, wait, username, password)
                time.sleep(5)  # подождать после перелогина

            # Ищем кнопку "Отметиться"
            try:
                otmetitsya_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[@class='v-button-caption' and text()='Отметиться']/ancestor::div[contains(@class, 'v-button')]"))
                )
                print(f"[{username}] >>> FOUND 'Отметиться' button! Clicking...")
                otmetitsya_button.click()
                print(f"[{username}] >>> CLICKED! <<<")
                if send_telegram_message(chat_id, f"[{username}] ATTENDANCE MARKED"):
                    print(f"[{username}] >>> Telegram notification sent!")
                time.sleep(2)
            except:
                print(f"[{username}] Button 'Отметиться' not available")
                # DEBUG: показываем все кнопки на странице
                try:
                    buttons = driver.find_elements(By.XPATH, "//div[contains(@class, 'v-button')]//span[@class='v-button-caption']")
                    if buttons:
                        btn_texts = [b.text for b in buttons if b.text.strip()]
                        if btn_texts:
                            print(f"[{username}]   [DEBUG] Buttons on page: {btn_texts}")
                except:
                    pass

            print(f"[{username}] Waiting {REFRESH_INTERVAL} seconds...")
            time.sleep(REFRESH_INTERVAL)

    except KeyboardInterrupt:
        print(f"\n[{username}] Stopped by user")
    except Exception as e:
        print(f"[{username}] Error: {e}")
    finally:
        driver.quit()
        print(f"[{username}] Browser closed")


def main():
    users = load_users()
    print(f"Loaded {len(users)} users from users.json")

    threads = []
    for user in users:
        t = threading.Thread(target=run_for_user, args=(user,), daemon=True)
        t.start()
        threads.append(t)
        time.sleep(2)  # небольшая задержка между запусками

    # Ждём все потоки
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\nStopping all users...")

if __name__ == "__main__":
    main()
