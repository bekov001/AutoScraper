import os
import time
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

USERNAME = os.getenv("KBTU_USERNAME")
PASSWORD = os.getenv("KBTU_PASSWORD")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
REFRESH_INTERVAL = 35  # секунд
LOGIN_URL = "https://wsp.kbtu.kz/RegistrationOnline"


def send_telegram_message(message):
    """Sends a message via Telegram bot if token and chat_id are configured"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")
        return False


def do_login(driver, wait):
    """Выполняет логин и возвращает True при успехе"""
    print("Attempting login...")
    driver.get(LOGIN_URL)
    print("Page opened successfully!")

    username_xpath = "/html/body/div[1]/div/div[2]/div/div[2]/div/div/div/div/div/div/div/div/div[2]/div/table/tbody/tr[1]/td[3]/div/input"
    username_field = wait.until(EC.presence_of_element_located((By.XPATH, username_xpath)))

    password_xpath = "/html/body/div[1]/div/div[2]/div/div[2]/div/div/div/div/div/div/div/div/div[2]/div/table/tbody/tr[2]/td[3]/input"
    password_field = driver.find_element(By.XPATH, password_xpath)

    username_field.clear()
    username_field.send_keys(USERNAME)
    print(f"Entered username: {USERNAME}")

    password_field.clear()
    password_field.send_keys(PASSWORD)
    print("Entered password")

    login_button = driver.find_element(By.XPATH, "//div[contains(@class, 'v-button') and contains(@class, 'primary')]")
    login_button.click()
    print("Clicked login button")

    time.sleep(5)  # ждём дольше
    print(f"After login URL: {driver.current_url}")

    # DEBUG: ищем ошибки на странице
    try:
        errors = driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(@class, 'v-Notification') or contains(@class, 'warning')]")
        for err in errors:
            if err.text.strip():
                print(f"  [ERROR ON PAGE] {err.text}")
    except:
        pass

    # DEBUG: выведем весь текст на странице
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
        # Возьмем первые 500 символов
        print(f"  [PAGE TEXT] {body_text[:500]}")
    except:
        pass

    # DEBUG: проверяем какие кнопки после логина
    try:
        all_buttons = driver.find_elements(By.XPATH, "//span[@class='v-button-caption']")
        btn_texts = [b.text for b in all_buttons if b.text.strip()]
        print(f"  [POST-LOGIN BUTTONS] {btn_texts}")
        if 'Кіру' in btn_texts or 'Войти' in btn_texts:
            print("  !!! LOGIN FAILED - still on login page !!!")
        else:
            print("  LOGIN SUCCESS - inside the app")
    except Exception as e:
        print(f"  Error checking buttons: {e}")

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


def main():
    print("Starting...")
    options = Options()
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--headless")  # без GUI для сервера
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    print("Launching Chrome (headless)...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)

    try:
        do_login(driver, wait)

        # Цикл обновления
        refresh_count = 0
        while True:
            refresh_count += 1
            print(f"\n[{time.strftime('%H:%M:%S')}] Refresh #{refresh_count}")

            # Вместо refresh() - переходим на URL заново (refresh может сбрасывать сессию)
            driver.get(LOGIN_URL)
            time.sleep(3)  # ждём загрузку страницы

            # DEBUG: показываем текущий URL и все кнопки
            print(f"  [URL] {driver.current_url}")
            try:
                all_buttons = driver.find_elements(By.XPATH, "//span[@class='v-button-caption']")
                btn_texts = [b.text for b in all_buttons if b.text.strip()]
                print(f"  [ALL BUTTONS] {btn_texts}")
            except:
                pass

            # Проверяем, не истекла ли сессия (кнопка Кіру видна = нужен логин)
            if is_session_expired(driver):
                print(">>> Session expired! Re-logging in...")
                do_login(driver, wait)
                time.sleep(5)  # подождать после перелогина

            # Ищем кнопку "Отметиться"
            try:
                otmetitsya_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[@class='v-button-caption' and text()='Отметиться']/ancestor::div[contains(@class, 'v-button')]"))
                )
                print(">>> FOUND 'Отметиться' button! Clicking...")
                otmetitsya_button.click()
                print(">>> CLICKED! <<<")
                if send_telegram_message("ATTENDANCE MARKED"):
                    print(">>> Telegram notification sent!")
                time.sleep(2)
            except:
                print("Button 'Отметиться' not available")
                # DEBUG: показываем все кнопки на странице
                try:
                    buttons = driver.find_elements(By.XPATH, "//div[contains(@class, 'v-button')]//span[@class='v-button-caption']")
                    if buttons:
                        btn_texts = [b.text for b in buttons if b.text.strip()]
                        if btn_texts:
                            print(f"  [DEBUG] Buttons on page: {btn_texts}")
                except:
                    pass

            print(f"Waiting {REFRESH_INTERVAL} seconds...")
            time.sleep(REFRESH_INTERVAL)

    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()
        print("Browser closed")

if __name__ == "__main__":
    main()
