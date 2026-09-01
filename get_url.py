import json
import urllib.request
import websocket


DEBUGGER_URL = "http://127.0.0.1:9222"


def get_page_source(url):
    # Ask Chrome for a new browser tab.
    request = urllib.request.Request(
        f"{DEBUGGER_URL}/json/new",
        data=url.encode(),
        method="PUT"
    )

    with urllib.request.urlopen(request) as response:
        target = json.load(response)

    websocket_url = target["webSocketDebuggerUrl"]

    # Connect to Chrome's DevTools WebSocket.
    ws = websocket.create_connection(websocket_url)

    message_id = 0

    def send(method, params=None):
        nonlocal message_id

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

    # Navigate Chrome.
    send(
        "Page.navigate",
        {"url": url}
    )

    # Wait for the page to finish loading.
    while True:
        response = json.loads(ws.recv())

        if (
            response.get("method") == "Page.loadEventFired"
        ):
            break

    # Get the HTML from Chrome itself.
    result = send(
        "Runtime.evaluate",
        {
            "expression": "document.documentElement.outerHTML",
            "returnByValue": True
        }
    )

    ws.close()

    return result["result"]["result"]["value"]


html = get_page_source("https://example.com")

print(html)
