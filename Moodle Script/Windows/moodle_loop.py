import platform
import re
import selectors
import subprocess
import threading
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

IS_WIN = platform.system() == "Windows"

if IS_WIN:
    import keyboard
    import pyperclip
else:
    import evdev
    from evdev import ecodes

DOMAIN = "moodle.rodenborch.nl"
CHAT_URL = "https://chatgpt.com"
DEBUG_ADDR = "127.0.0.1:9222"

ANSWER_RE = re.compile(r"^q\d+:\d+_answer$")
ANSWER_CSS = 'input[name$="_answer"][id^="q"], input[id$="_answer"][id^="q"]'
CHAT_INPUT = (By.CSS_SELECTOR, "#prompt-textarea")
CHAT_REPLY = (By.CSS_SELECTOR, 'div[data-message-author-role="assistant"]')
CHECK = (By.CSS_SELECTOR, 'button[type="submit"][name$="-submit"].btn-secondary')
NEXT = (By.CSS_SELECTOR, "#mod_quiz-next-nav, input.mod_quiz-next-nav")

def set_clip(text):
    if IS_WIN:
        pyperclip.copy(text)
    else:
        subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=True)


# ---------- toggle (F8: evdev on Linux, keyboard on Windows) ----------
running = threading.Event()


class Stopped(Exception):
    pass


def toggle(*_):
    if running.is_set():
        running.clear()
        print("\n[F8] OFF", flush=True)
    else:
        running.set()
        print("\n[F8] ON", flush=True)


def hotkey_listener():
    selector = selectors.DefaultSelector()
    for path in evdev.list_devices():
        try:
            dev = evdev.InputDevice(path)
            if ecodes.KEY_F8 in dev.capabilities().get(ecodes.EV_KEY, []):
                selector.register(dev, selectors.EVENT_READ)
        except (PermissionError, OSError):
            continue
    if not selector.get_map():
        print("No readable keyboards. Add yourself to the 'input' group and re-login.")
        return
    while True:
        for key, _ in selector.select():
            try:
                for ev in key.fileobj.read():
                    if ev.type == ecodes.EV_KEY and ev.code == ecodes.KEY_F8 and ev.value == 1:
                        toggle()
            except OSError:
                selector.unregister(key.fileobj)


def checkpoint():
    if not running.is_set():
        raise Stopped


def sleep(s):
    end = time.time() + s
    while time.time() < end:
        checkpoint()
        time.sleep(0.1)


# ---------- driver ----------
options = Options()
options.add_experimental_option("debuggerAddress", DEBUG_ADDR)
driver = webdriver.Chrome(options=options)


def switch_to(match):
    for h in driver.window_handles:
        driver.switch_to.window(h)
        if match(driver.current_url):
            driver.switch_to.default_content()
            return True
    return False


def moodle_tab():
    if not switch_to(lambda u: DOMAIN in u):
        raise RuntimeError(f"No tab with {DOMAIN}")


def click(el):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    try:
        el.click()
    except Exception:
        driver.execute_script("arguments[0].click();", el)


def search_frames():
    found = driver.find_elements(By.CSS_SELECTOR, ANSWER_CSS)
    if found:
        return found
    frames = driver.find_elements(By.CSS_SELECTOR, "iframe, frame")
    for i in range(len(frames)):
        driver.switch_to.frame(i)
        found = search_frames()
        if found:
            return found
        driver.switch_to.parent_frame()
    return []


# ---------- 1. copytext ----------
def copytext():
    moodle_tab()
    inputs = [
        el for el in driver.find_elements(By.TAG_NAME, "input")
        if ANSWER_RE.match(el.get_attribute("id") or "")
        or ANSWER_RE.match(el.get_attribute("name") or "")
    ]
    if not inputs:
        return False
    text = driver.execute_script(
        """
        const div = arguments[0].closest('div');
        if (!div) return null;
        const clone = div.cloneNode(true);
        clone.querySelectorAll('.visually-hidden').forEach(e => e.remove());
        clone.querySelectorAll('input').forEach(e => e.remove());
        return clone.textContent.replace(/\\s+/g, ' ').trim();
        """,
        inputs[0],
    )
    if not text:
        return False
    set_clip(text)
    print("Copied:", text)
    return True


# ---------- 2. pastev4 (ChatGPT) ----------
def ask_chatgpt():
    if not switch_to(lambda u: "chatgpt.com" in u or "chat.openai.com" in u):
        driver.switch_to.new_window("tab")
        driver.get(CHAT_URL)
    driver.execute_script("window.focus();")

    box = WebDriverWait(driver, 30).until(EC.element_to_be_clickable(CHAT_INPUT))
    box.click()
    before = len(driver.find_elements(*CHAT_REPLY))
    box.send_keys(Keys.CONTROL, "v")
    sleep(0.5)
    box.send_keys(Keys.ENTER)

    end = time.time() + 60
    while len(driver.find_elements(*CHAT_REPLY)) <= before:
        checkpoint()
        if time.time() > end:
            print("No new reply appeared.")
            return False
        time.sleep(0.3)

    last, stable = "", 0
    for _ in range(180):
        sleep(1)
        els = driver.find_elements(*CHAT_REPLY)
        if not els:
            continue
        current = els[-1].get_attribute("innerText")
        if current == last and current.strip():
            stable += 1
            if stable >= 3:
                break
        else:
            stable, last = 0, current

    result = driver.find_elements(*CHAT_REPLY)[-1].get_attribute("innerText")
    set_clip(result)
    print("Answer:", result)
    return True


# ---------- 3. pasteanswerv2 ----------
def paste_answer():
    moodle_tab()
    found = search_frames()
    if not found:
        print("No answer input found.")
        return False
    el = found[0]
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    try:
        el.click()
    except Exception:
        driver.execute_script("arguments[0].focus();", el)
    el.send_keys(Keys.CONTROL, "a")
    el.send_keys(Keys.CONTROL, "v")
    sleep(0.2)
    driver.switch_to.default_content()
    return True


# ---------- 4. check ----------
def check_and_next():
    moodle_tab()
    try:
        btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(CHECK))
        click(btn)
        print("Clicked Check")
    except Exception:
        print("No Check button, skipping")

    sleep(5)

    try:
        nxt = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(NEXT))
        click(nxt)
        print("Clicked Next")
        sleep(2)
        return True
    except Exception:
        print("No Next button (last page?)")
        return False


STEPS = [copytext, ask_chatgpt, paste_answer, check_and_next]

if __name__ == "__main__":
    if IS_WIN:
        keyboard.add_hotkey("f8", toggle)
    else:
        threading.Thread(target=hotkey_listener, daemon=True).start()
    print("Ready. Press F8 to toggle.")
    while True:
        if not running.is_set():
            time.sleep(0.2)
            continue
        try:
            for step in STEPS:
                checkpoint()
                if not step():
                    running.clear()
                    print(f"[stopped at {step.__name__}]")
                    break
        except Stopped:
            pass
        except Exception as e:
            running.clear()
            print("Error:", e)
