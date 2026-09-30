import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CHECK = (By.CSS_SELECTOR, 'button[type="submit"][name$="-submit"].btn-secondary')
NEXT = (By.CSS_SELECTOR, '#mod_quiz-next-nav, input.mod_quiz-next-nav')

options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)

# Find the quiz tab (falls back to current tab)
for h in driver.window_handles:
    driver.switch_to.window(h)
    if "/mod/quiz/" in driver.current_url:
        break
print("Tab:", driver.title, driver.current_url)

def click(el):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    try:
        el.click()
    except Exception:
        driver.execute_script("arguments[0].click();", el)

# 1. Click Check
try:
    btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(CHECK))
    click(btn)
    print("Clicked Check")
except Exception:
    print("No Check button found, skipping")

# 2. Wait 5 seconds
time.sleep(5)

# 3. Click Next page
try:
    nxt = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(NEXT))
    click(nxt)
    print("Clicked Next page")
except Exception as e:
    print("Next button not found:", e)
