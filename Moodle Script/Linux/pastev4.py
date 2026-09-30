import time
import pyperclip
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CHAT_URL = "https://chatgpt.com"
INPUT = (By.CSS_SELECTOR, "#prompt-textarea")
REPLY = (By.CSS_SELECTOR, 'div[data-message-author-role="assistant"]')

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)

# 1. Find the ChatGPT tab, or open one
found = False
for h in driver.window_handles:
    driver.switch_to.window(h)
    if "chatgpt.com" in driver.current_url or "chat.openai.com" in driver.current_url:
        found = True
        break

if not found:
    driver.switch_to.new_window("tab")
    driver.get(CHAT_URL)

driver.execute_script("window.focus();")
print("Tab:", driver.title, driver.current_url)

# 2. Focus input and paste clipboard (Ctrl+V keeps newlines without sending)
box = WebDriverWait(driver, 30).until(EC.element_to_be_clickable(INPUT))
box.click()
before = len(driver.find_elements(*REPLY))
box.send_keys(Keys.CONTROL, "v")
time.sleep(0.5)

# 3. Send
box.send_keys(Keys.ENTER)

# 4. Wait for new reply to appear
try:
    WebDriverWait(driver, 60).until(
        lambda d: len(d.find_elements(*REPLY)) > before
    )
except Exception:
    print("No new reply appeared.")

# 5. Wait until text stops changing
last, stable = "", 0
for _ in range(180):
    time.sleep(1)
    els = driver.find_elements(*REPLY)
    if not els:
        continue
    current = els[-1].get_attribute("innerText")
    if current == last and current.strip():
        stable += 1
        if stable >= 3:
            break
    else:
        stable = 0
        last = current

# 6. Copy result
try:
    result = driver.find_elements(*REPLY)[-1].get_attribute("innerText")
    pyperclip.copy(result)
    print("Successfully copied response to clipboard:", result)
except Exception as e:
    print("Error finding element:", e)
