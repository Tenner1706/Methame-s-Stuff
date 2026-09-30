"""
Chromium-based browsers (Chrome, Chromium, Brave, Edge, Vivaldi, etc.)

Finds all <input> fields whose id/name matches q<digits>:<digits>_answer
(e.g. q58328:4_answer) and highlights them.

Setup (CachyOS):
    paru -S chromedriver
    pip install selenium

Before running:
    Close all windows of your browser, then relaunch it with debugging on:

        chromium --remote-debugging-port=9222
        brave --remote-debugging-port=9222
        google-chrome-stable --remote-debugging-port=9222

    Log in / navigate to your target page, THEN run this script.
    Your session/cookies are preserved since you're reusing the real browser
    window, not a fresh automated one.
"""

import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

PATTERN = re.compile(r"^q\d+:\d+_answer$")


def get_driver(debug_address="127.0.0.1:9222"):
    options = Options()
    options.add_experimental_option("debuggerAddress", debug_address)
    return webdriver.Chrome(options=options)


def highlight_matching_inputs(driver, pattern=PATTERN):
    inputs = driver.find_elements(By.TAG_NAME, "input")
    matched = []

    for el in inputs:
        el_id = el.get_attribute("id") or ""
        el_name = el.get_attribute("name") or ""

        if pattern.match(el_id) or pattern.match(el_name):
            matched.append(el)
            driver.execute_script(
                """
                arguments[0].style.border = '3px solid red';
                arguments[0].style.backgroundColor = 'yellow';
                arguments[0].style.boxShadow = '0 0 8px 2px red';
                """,
                el,
            )

    return matched


if __name__ == "__main__":
    driver = get_driver()
    found = highlight_matching_inputs(driver)
    print(f"Highlighted {len(found)} matching input(s):")
    for el in found:
        print(" -", el.get_attribute("id") or el.get_attribute("name"))
