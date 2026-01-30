# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx"
# ]
# ///

import httpx

payload = {
    "email": "test@mail.com",
    "secret": "something_random_12345",  # must match your SECRET_KEY in .env
    "url": "https://tds-llm-analysis.s-anand.net/demo"
}

try:
    response = httpx.post(
        "http://localhost:7860/receive_request",
        json=payload,
        timeout=20.0,        # explicitly give more time
    )
    print("Status Code:", response.status_code)
    try:
        print("Response Body:", response.json())
    except Exception:
        print("Response Text:", response.text)

except httpx.ReadTimeout:
    print("Client: ReadTimeout - server took too long to respond.")
except httpx.ConnectError:
    print("Client: Could not connect to server (is it running?).")
