import os
import time
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

def main():
    print("Starting...")
    options = Options()
    options.add_argument("--ignore-certificate-errors")

    print("Launching Chrome...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)

    try:
        driver.get("https://wsp.kbtu.kz/RegistrationOnline")
        print("Page opened successfully!")

        # Wait for login form to load
        username_xpath = "/html/body/div[1]/div/div[2]/div/div[2]/div/div/div/div/div/div/div/div/div[2]/div/table/tbody/tr[1]/td[3]/div/input"
        username_field = wait.until(EC.presence_of_element_located((By.XPATH, username_xpath)))

        # Find password field
        password_xpath = "/html/body/div[1]/div/div[2]/div/div[2]/div/div/div/div/div/div/div/div/div[2]/div/table/tbody/tr[2]/td[3]/input"
        password_field = driver.find_element(By.XPATH, password_xpath)

        # Enter credentials
        username_field.clear()
        username_field.send_keys(USERNAME)
        print(f"Entered username: {USERNAME}")

        password_field.clear()
        password_field.send_keys(PASSWORD)
        print("Entered password")

        # Click login button (Кіру)
        login_button = driver.find_element(By.XPATH, "//div[contains(@class, 'v-button') and contains(@class, 'primary')]")
        login_button.click()
        print("Clicked login button")

        # Wait for login to complete
        time.sleep(3)
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")

        # Look for "Отметиться" button and click if present
        try:
            otmetitsya_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[@class='v-button-caption' and text()='Отметиться']/ancestor::div[contains(@class, 'v-button')]"))
            )
            print("Found 'Отметиться' button, clicking...")
            otmetitsya_button.click()
            print("Clicked 'Отметиться' button!")
            time.sleep(2)
        except Exception as e:
            print(f"'Отметиться' button not found or not available: {e}")

        input("Press Enter to close...")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
