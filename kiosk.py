import subprocess
import keyboard  # pip install keyboard
import time
import os
import psutil
from win32gui import ShowWindow, FindWindow
from win32con import SW_HIDE, SW_SHOW
import tkinter as tk
from tkinter import ttk, messagebox

# Browser configurations
BROWSER_CONFIGS = {
    "Chrome": {
        "path": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "proc_name": "chrome.exe",
        "launch_args": ["--kiosk"]
    },
    "Edge": {
        "path": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "proc_name": "msedge.exe",
        "launch_args": ["--kiosk", "--edge-kiosk-type=fullscreen", "--no-first-run"]
    },
    "Comet": {
        "path": r"C:\Users\navne\AppData\Local\Perplexity\Comet\Application\comet.exe",
        "proc_name": "comet.exe",
        "launch_args": ["--kiosk"]  # Assuming Chromium-based, so similar to Chrome
    }
}

def launch_browser(browser_config, url):
    args = [browser_config["path"]] + browser_config["launch_args"] + [url]
    proc = subprocess.Popen(args)
    return proc

def kill_other_browsers(exclude_proc):
    browsers = ["chrome.exe", "msedge.exe", "firefox.exe", "iexplore.exe", "opera.exe", "comet.exe"]
    browsers.remove(exclude_proc)  # Don't kill the chosen browser
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] in browsers:
            try:
                proc.kill()
            except Exception:
                pass

def kill_all_chosen_browser(proc_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == proc_name:
            try:
                proc.kill()
            except Exception:
                pass

def hide_taskbar():
    taskbar_hwnd = FindWindow("Shell_TrayWnd", None)
    ShowWindow(taskbar_hwnd, SW_HIDE)

def show_taskbar():
    taskbar_hwnd = FindWindow("Shell_TrayWnd", None)
    ShowWindow(taskbar_hwnd, SW_SHOW)

def is_browser_running(proc_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == proc_name:
            return True
    return False

def disable_secondary_monitors():
    # Switch system to "PC screen only" (internal display only)
    subprocess.run(["displayswitch.exe", "/internal"])
    time.sleep(2)

def restore_monitors():
    # Restore display mode to "extend" (multiple monitors)
    subprocess.run(["displayswitch.exe", "/extend"])
    time.sleep(2)

def show_config_gui():
    root = tk.Tk()
    root.title("Kiosk Mode Configuration")
    root.geometry("600x500")

    tk.Label(root, text="You are about to enter Kiosk Mode.", font=("Arial", 12, "bold")).pack(pady=10)
    tk.Label(root, text="This will launch a full-screen browser with limited controls.").pack()
    tk.Label(root,
             text="Warning: All open browser sessions will be closed. Please ensure any browser work is saved.").pack(
        pady=10)
    tk.Label(root, text="Choose your browser and enter the website URL below.").pack(pady=10)

    tk.Label(root, text="Select Browser:").pack()
    browser_var = tk.StringVar(value="Edge")
    browser_dropdown = ttk.Combobox(root, textvariable=browser_var, values=list(BROWSER_CONFIGS.keys()),
                                    state="readonly")
    browser_dropdown.pack(pady=5)

    tk.Label(root, text="Website URL (e.g., www.chess.com):").pack()
    url_var = tk.StringVar(value="www.chess.com")
    url_entry = tk.Entry(root, textvariable=url_var, width=50)
    url_entry.pack(pady=5)

    disable_monitors_var = tk.BooleanVar(value=True)
    tk.Checkbutton(root, text="Disable secondary monitors", variable=disable_monitors_var).pack(pady=5)

    tk.Label(root, text="To terminate Kiosk mode, use key combination: CTRL + ALT + Q").pack(pady=10)
    # Store result: proceed or cancel
    gui_result = {"proceed": False}

    def start_kiosk():
        selected_browser = browser_var.get()
        url = url_var.get().strip()
        if selected_browser not in BROWSER_CONFIGS:
            messagebox.showerror("Error", "Invalid browser selected.")
            return
        if not url:
            messagebox.showerror("Error", "Please enter a website URL.")
            return
        # If user forgot scheme: add https:// automatically
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
            url_var.set(url)  # Update the entry box visually (optional)
        gui_result["proceed"] = True
        root.quit()

    def on_close():
        gui_result["proceed"] = False
        root.quit()

    root.protocol("WM_DELETE_WINDOW", on_close)
    tk.Button(root, text="Enter Kiosk Mode", command=start_kiosk).pack(pady=20)

    root.mainloop()
    try:
        root.destroy()
    except Exception:
        pass  # Ignore if destroy is called on a closed/nonexistent window

    if gui_result["proceed"]:
        return browser_var.get(), url_var.get().strip(), disable_monitors_var.get()
    else:
        return None, None, None  # Indicate cancellation or window close

def main():
    selected_browser, url, disable_monitors = show_config_gui()
    if not selected_browser or not url:
        print("Kiosk setup cancelled by user or window closed.")
        return

    browser_config = BROWSER_CONFIGS[selected_browser]
    proc_name = browser_config["proc_name"]

    print(f"Starting kiosk mode with {selected_browser} at {url}...")

    if disable_monitors:
        disable_secondary_monitors()
        print("Secondary monitors disabled.")

    kill_all_chosen_browser(proc_name)
    time.sleep(1)

    proc = launch_browser(browser_config, url)
    hide_taskbar()
    print(f"Taskbar hidden. {selected_browser} launched in kiosk mode.")

    exit_flag = False
    def exit_kiosk():
        nonlocal exit_flag
        exit_flag = True
        print("Unlock hotkey pressed. Exiting kiosk mode.")

    keyboard.add_hotkey('ctrl + alt + q', exit_kiosk)

    try:
        while not exit_flag:
            kill_other_browsers(proc_name)
            if not is_browser_running(proc_name):
                print(f"{selected_browser} closed, relaunching...")
                kill_all_chosen_browser(proc_name)
                proc = launch_browser(browser_config, url)
            time.sleep(0.1)
    finally:
        keyboard.remove_hotkey('ctrl + alt + q')
        show_taskbar()
        print("Taskbar restored.")
        kill_all_chosen_browser(proc_name)
        if disable_monitors:
            restore_monitors()
            print("Secondary monitors restored.")
        print("Kiosk exited.")

if __name__ == "__main__":
    main()
