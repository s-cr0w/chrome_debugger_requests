import subprocess
import time
import json
import urllib.request
import urllib.error
import websocket

DEBUGGER_URL = "http://127.0.0.1:9222"


# --------------------------------------------------
# Start Chrome
# --------------------------------------------------

subprocess.Popen([
    "powershell.exe",
    "-NoProfile",
    "-Command",
    r'Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222","--user-data-dir=C:\Temp","--remote-allow-origins=http://127.0.0.1:9222"'
])


# --------------------------------------------------
# Wait until Chrome's debugger is ready
# --------------------------------------------------

print("Waiting for Chrome to start...")

max_wait = 30
start_time = time.time()

while True:

    try:
        with urllib.request.urlopen(
            f"{DEBUGGER_URL}/json",
            timeout=2
        ) as response:

            tabs = json.load(response)

        print("Chrome debugger is ready.")
        break

    except (urllib.error.URLError, ConnectionRefusedError):

        if time.time() - start_time > max_wait:
            raise RuntimeError(
                "Chrome debugger did not become available within 30 seconds."
            )

        time.sleep(0.5)


# --------------------------------------------------
# Find a normal Chrome tab
# --------------------------------------------------

page_tabs = [
    tab for tab in tabs
    if tab.get("type") == "page"
]

if not page_tabs:
    raise RuntimeError("Chrome started, but no webpage tab was found.")

tab = page_tabs[0]

print("Using tab:", tab["url"])


# --------------------------------------------------
# Connect to Chrome DevTools
# --------------------------------------------------

ws = websocket.create_connection(
    tab["webSocketDebuggerUrl"],
    timeout=10
)

message_id = 0


def command(method, params=None):

    global message_id

    message_id += 1

    message = {
        "id": message_id,
        "method": method
    }

    if params:
        message["params"] = params

    ws.send(json.dumps(message))

    while True:

        response = json.loads(ws.recv())

        if response.get("id") == message_id:
            return response


# --------------------------------------------------
# Enable Page events
# --------------------------------------------------

command("Page.enable")


# --------------------------------------------------
# Navigate to example.com
# --------------------------------------------------

print("Navigating to example.com...")

command(
    "Page.navigate",
    {
        "url": "https://example.com"
    }
)


# --------------------------------------------------
# Wait until the page finishes loading
# --------------------------------------------------

print("Waiting for page to load...")

page_loaded = False

while not page_loaded:

    response = json.loads(ws.recv())

    if response.get("method") == "Page.loadEventFired":
        page_loaded = True


print("Page loaded.")


# --------------------------------------------------
# Get source code
# --------------------------------------------------

result = command(
    "Runtime.evaluate",
    {
        "expression": "document.documentElement.outerHTML",
        "returnByValue": True
    }
)

source = result["result"]["result"]["value"]


# --------------------------------------------------
# Print source
# --------------------------------------------------

print("\n========== SOURCE ==========\n")

print(source)

print("\n============================\n")


ws.close()
