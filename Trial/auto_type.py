import pyautogui
import keyboard  # pip install keyboard
import time

# The text you want to type
text_to_type = "Happy Hacking"

def type_text():
    """Function to type text and log it in terminal."""
    pyautogui.write(text_to_type, interval=0.05)  # slightly faster typing
    print(f"[{time.strftime('%H:%M:%S')}] Typed text: '{text_to_type}'")

# Register hotkey: ctrl
keyboard.add_hotkey('ctrl', type_text)

print("Hotkey set! Press ctrl to type your text anywhere. Press ESC to quit.")

# Keep the script running until ESC is pressed
keyboard.wait('esc')
print("Exiting...")
