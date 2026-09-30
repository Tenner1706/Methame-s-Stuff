"""
Finds the wrapping <div> around an answer input matching q<digits>:<digits>_answer
(e.g. q58328:5_answer), extracts the surrounding sentence text (stripping out
the visually-hidden label and the empty input itself), and copies it to the
system clipboard.

Chromium-based browsers (Chrome, Chromium, Brave, etc.)

Setup (CachyOS):
    paru -S chromedriver wl-clipboard
    pip install selenium

Before running:
    Close your browser fully, then relaunch with debugging on, e.g.:
        chromium --remote-debugging-port=9222
        brave --remote-debugging-port=9222
    Navigate to your page, THEN run this script.
"""

import re
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

PATTERN = re.compile(r"^q\d+:\d+_answer$")


def get_driver(debug_address="127.0.0.1:9222"):
    options = Options()
    options.add_experimental_option("debuggerAddress", debug_address)
    return webdriver.Chrome(options=options)


def find_matching_inputs(driver, pattern=PATTERN):
    inputs = driver.find_elements(By.TAG_NAME, "input")
    matched = []
    for el in inputs:
        el_id = el.get_attribute("id") or ""
        el_name = el.get_attribute("name") or ""
        if pattern.match(el_id) or pattern.match(el_name):
            matched.append(el)
    return matched


def extract_clean_text(driver, input_el):
    """
    Walks up to the nearest ancestor <div>, clones it, strips out any
    .visually-hidden elements and the <input> itself, then returns the
    remaining visible text, collapsed and trimmed.
    """
    text = driver.execute_script(
        """
        const input = arguments[0];
        const div = input.closest('div');
        if (!div) return null;

        const clone = div.cloneNode(true);

        clone.querySelectorAll('.visually-hidden').forEach(e => e.remove());
        clone.querySelectorAll('input').forEach(e => e.remove());

        return clone.textContent.replace(/\\s+/g, ' ').trim();
        """,
        input_el,
    )
    return text


def copy_to_clipboard(text):
    subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=True)


if __name__ == "__main__":
    driver = get_driver()
    matches = find_matching_inputs(driver)

    if not matches:
        print("No matching inputs found.")
    else:
        # Default: use the first match. Adjust index if you need a specific one.
        target = matches[0]
        sentence = extract_clean_text(driver, target)

        if sentence:
            copy_to_clipboard(sentence)
            print("Copied to clipboard:")
            print(sentence)
        else:
            print("Couldn't find a wrapping div with text for that input.")
