"""
PocketSmart AI: Quick Launcher Script
Starts the FastAPI application and opens the browser automatically.
"""

import sys
import os
import webbrowser
import time
import threading

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    print("\n" + "="*65)
    print("  PocketSmart AI: Your Smart Budget & Recommendation Assistant")
    print("  SmartBridge / TN Skill Wallet Project")
    print("="*65)
    print("  -> Application URL: http://127.0.0.1:8000")
    print("  -> Demo Credentials: demo / password123")
    print("  -> To stop the server: Press CTRL + C")
    print("="*65 + "\n")

    threading.Thread(target=open_browser, daemon=True).start()

    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
