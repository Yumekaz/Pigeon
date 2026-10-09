# launcher.py
"""Dedicated entrypoint for the standalone Windows portable launcher.

Handles:
- Immediate GUI splash screen creation using tkinter.
- Suppressing console stream crashes in windowed GUI mode via NullWriter.
- Spawning system tray icon via pystray and Pillow (lazy-loaded).
- Auto-opening default browser pointing to the running backend.
- Launching the FastAPI server (importing and running app.py).
"""
import os
import sys
import threading
import time
import webbrowser

# PyInstaller multiprocessing children re-enter this executable with a private
# bootstrap argument. Consume it before splash/UI or application imports so a
# spawn-based worker does not relaunch the full desktop application.
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()

# Define a dummy NullWriter to suppress standard stream crashes (isatty etc.) in GUI mode
class NullWriter:
    def write(self, text):
        pass
    def flush(self):
        pass
    def isatty(self):
        return False

if sys.stdout is None:
    sys.stdout = NullWriter()
if sys.stderr is None:
    sys.stderr = NullWriter()


splash_root = None

# If running from a frozen PyInstaller bundle, launch the splash screen IMMEDIATELY
if getattr(sys, 'frozen', False):
    import tkinter as tk

    def show_splash_instantly():
        global splash_root
        try:
            splash_root = tk.Tk()
            splash_root.title("PIGEON")
            splash_root.overrideredirect(True)
            splash_root.configure(bg="#0D0F14")

            # Accented borders
            splash_root.config(highlightbackground="#FBE7BA", highlightcolor="#FBE7BA", highlightthickness=1)

            w, h = 360, 160
            ws = splash_root.winfo_screenwidth()
            hs = splash_root.winfo_screenheight()
            x = (ws - w) // 2
            y = (hs - h) // 2
            splash_root.geometry(f"{w}x{h}+{x}+{y}")

            tk.Label(splash_root, text="PIGEON", font=("Segoe UI", 22, "bold"), bg="#0D0F14", fg="#FBE7BA").pack(pady=(22, 2))
            tk.Label(splash_root, text="Launching background services...", font=("Segoe UI", 10), bg="#0D0F14", fg="#d1d4e0").pack(pady=2)
            tk.Label(splash_root, text="Please wait, this will take a few seconds.", font=("Segoe UI", 8, "italic"), bg="#0D0F14", fg="#5c6370").pack(pady=(12, 0))

            splash_root.attributes("-topmost", True)
            splash_root.mainloop()
        except Exception:
            pass

    # Launch the GUI splash screen immediately on a background thread
    threading.Thread(target=show_splash_instantly, daemon=True).start()


def create_tray_image():
    # Reuse the approved application icon in source and frozen bundles.
    from PIL import Image
    bundle_root = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    with Image.open(os.path.join(bundle_root, 'static', 'icons', 'icon-192.png')) as source:
        return source.convert('RGBA').resize((64, 64), Image.Resampling.LANCZOS)


def on_open_browser(icon, item, url):
    webbrowser.open(url)


def on_exit(icon, item):
    icon.stop()
    os._exit(0)


def setup_system_tray(url):
    try:
        import pystray
        icon_img = create_tray_image()
        menu = (
            pystray.MenuItem('Open PIGEON', lambda icon, item: on_open_browser(icon, item, url), default=True),
            pystray.MenuItem('Exit', on_exit)
        )
        tray_icon = pystray.Icon(
            "PIGEON",
            icon_img,
            "PIGEON",
            menu
        )
        tray_icon.run()
    except Exception:
        pass


def open_browser(url):
    # Allow uvicorn and app lifecycles to complete warmups
    time.sleep(3.5)

    # Safely close the splash screen
    try:
        global splash_root
        if splash_root:
            splash_root.after(0, splash_root.destroy)
    except Exception:
        pass

    webbrowser.open(url)


if __name__ == "__main__":
    import uvicorn
    # Import the FastAPI app from app.py
    from app import app

    bind_host = os.getenv("APP_BIND", "127.0.0.1")
    bind_port = int(os.getenv("APP_PORT", "7011"))
    url = f"http://{bind_host}:{bind_port}"

    if getattr(sys, 'frozen', False):
        # Start browser manager thread
        threading.Thread(target=open_browser, args=(url,), daemon=True).start()
        # Start system tray manager thread
        threading.Thread(target=setup_system_tray, args=(url,), daemon=True).start()

    uvicorn.run(app, host=bind_host, port=bind_port, log_level="info")
