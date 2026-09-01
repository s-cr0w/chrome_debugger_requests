import subprocess
import time
import json
import urllib.request
import websocket

DEBUGGER_URL = "http://127.0.0.1:9222"

# Open Chrome with remote debugging enabled
subprocess.Popen([
    "powershell.exe",
    "-NoProfile",
    "-Command",
    r'Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9222","--user-data-dir=C:\Temp","--remote-allow-origins=http://127.0.0.1:9222"'
])

# Give Chrome a moment to start
time.sleep(2)

# Get currently open Chrome tabs
with urllib.request.urlopen(
    f"{DEBUGGER_URL}/json",
    timeout=5
) as response:
    tabs = json.load(response)

# Find the first normal webpage tab
tab = next(
    tab for tab in tabs
    if tab.get("type") == "page"
)

print("Using tab:", tab["url"])

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


# Navigate
command(
    "Page.navigate",
    {"url": "https://example.com"}
)

time.sleep(1)

# Get source
result = command(
    "Runtime.evaluate",
    {
        "expression": "document.documentElement.outerHTML",
        "returnByValue": True
    }
)

source = result["result"]["result"]["value"]

print(source)

ws.close()
