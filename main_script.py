import cv2
import subprocess
import numpy as np
import time
import pytesseract

# === Set your target ChatGPT window ID (get it using xwininfo)
WIN_ID = '0x1e00004'

# === Load icons
ICON_PATHS = {
    "newchat": "icons/2.png",
    "textbox": "icons/1.png",
    "send": "icons/5.png",
    "end":"icons/6.png"
}

icons = {key: cv2.imread(path) for key, path in ICON_PATHS.items()}

def wait_for_output(win_id, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        frame = capture_window(win_id)
        if frame is None:
            continue

        if find_icon_location(frame, icons["end"]):
            print("[✓] Output detected.")
            return True
        time.sleep(0.01)

    print("[!] Timeout waiting for ChatGPT output.")
    return False

def read_gpt_output(win_id):
    subprocess.run(['xwd', '-id', win_id, '-out', 'response.xwd'])
    subprocess.run(['convert', 'response.xwd', 'response.png'])

    img = cv2.imread("response.png")
    if img is None:
        print("Failed to load response.png")
        return

    # ---- Crop to only output box (adjust if needed) ----
    x1, y1 = 320, 160
    x2, y2 = 1250, 850
    output_only = img[y1:y2, x1:x2]

    # ---- Preview the cropped area (optional) ----
    cv2.imshow("GPT Output Region", output_only)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    text = pytesseract.image_to_string(output_only)
    print("\n🤖 ChatGPT response:")
    print("----------------------------------")
    print(text.strip())
    print("----------------------------------")

def minimize_window(win_id):
    subprocess.run(['xdotool', 'windowminimize', win_id])

def capture_window(win_id):
    # Capture the window
    subprocess.run(['xwd', '-id', win_id, '-out', 'shot.xwd'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['convert', 'shot.xwd', 'shot.png'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    img = cv2.imread('shot.png')
    return img


def find_icon_location(screen, icon, threshold=0.85):
    result = cv2.matchTemplate(screen, icon, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        h, w = icon.shape[:2]
        return (max_loc[0] + w // 2, max_loc[1] + h // 2)
    else:
        return None


def click_in_window(win_id, x, y):
    subprocess.run(['xdotool', 'windowactivate', '--sync', win_id])
    subprocess.run(['xdotool', 'mousemove', '--window', win_id, str(x), str(y)])
    subprocess.run(['xdotool', 'click', '--window', win_id, '1'])


def type_in_window(win_id, message):
    subprocess.run(['xdotool', 'windowactivate', '--sync', win_id])
    subprocess.run(['xdotool', 'type', '--window', win_id, message])
    subprocess.run(['xdotool', 'key', '--window', win_id, 'Return'])
    time.sleep(0.01)
    read_gpt_output(win_id)
    minimize_window(win_id)


def perform_command(cmd, frame):
    if cmd not in icons:
        print(f"[!] Unknown command: {cmd}")
        return

    loc = find_icon_location(frame, icons[cmd])
    if loc:
        click_in_window(WIN_ID, *loc)
        time.sleep(0.01)
        minimize_window(WIN_ID)
    else:
        print(f"[!] Icon '{cmd}' not found on screen.")
    

def main_loop():
    print("Type commands (newchat, textbox, send) or 'exit':")
    while True:
        frame = capture_window(WIN_ID)
        if frame is None:
            print("[!] Failed to capture window")
            break

        user_input = input(">> ").strip().lower()

        if user_input == "exit":
            break
        elif user_input == "type":
            text = input("Text to type: ")
            type_in_window(WIN_ID, text)
        else:
            perform_command(user_input, frame)


if _name_ == "_main_":
    main_loop()
