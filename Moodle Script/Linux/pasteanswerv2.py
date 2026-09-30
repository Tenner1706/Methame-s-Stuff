import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

DOMAIN = "moodle.rodenborch.nl"
CSS = 'input[name$="_answer"][id^="q"], input[id$="_answer"][id^="q"]'
PASTE_INTO_ALL = False


def get_driver(debug_address="127.0.0.1:9222"):
    options = Options()
    options.add_experimental_option("debuggerAddress", debug_address)
    return webdriver.Chrome(options=options)


def switch_to_moodle(driver):
    for h in driver.window_handles:
        driver.switch_to.window(h)
        if DOMAIN in driver.current_url:
            driver.switch_to.default_content()
            print("Tab:", driver.title, driver.current_url)
            return True
    return False


def search_frames(driver):
    found = driver.find_elements(By.CSS_SELECTOR, CSS)
    if found:
        return found
    frames = driver.find_elements(By.CSS_SELECTOR, "iframe, frame")
    for i in range(len(frames)):
        driver.switch_to.frame(i)
        found = search_frames(driver)
        if found:
            return found
        driver.switch_to.parent_frame()
    return []


def highlight(driver, el):
    driver.execute_script(
        """
        arguments[0].style.border = '3px solid red';
        arguments[0].style.backgroundColor = 'yellow';
        arguments[0].style.boxShadow = '0 0 8px 2px red';
        """,
        el,
    )


def select_and_paste(driver, el):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    try:
        el.click()
    except Exception:
        driver.execute_script("arguments[0].focus();", el)
    el.send_keys(Keys.CONTROL, "a")
    el.send_keys(Keys.CONTROL, "v")


if __name__ == "__main__":
    driver = get_driver()

    if not switch_to_moodle(driver):
        raise SystemExit(f"No tab with {DOMAIN} found.")

    found = search_frames(driver)
    print(f"Found {len(found)} matching input(s)")
    if not found:
        raise SystemExit("No matching inputs on the Moodle tab.")

    for el in found:
        highlight(driver, el)

    targets = found if PASTE_INTO_ALL else found[:1]
    for el in targets:
        select_and_paste(driver, el)
        time.sleep(0.2)
        print(" - pasted into:", el.get_attribute("id") or el.get_attribute("name"))
