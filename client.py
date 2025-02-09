import json

import requests
import sseclient

# Step 1: Read JSON file
with open("input/data_50.json", "r", encoding="utf-8") as file:
    json_data = json.load(file)

# Step 2: Send JSON data to the server
upload_url = "http://localhost:8000/upload-data"
response = requests.post(upload_url, json=json_data)

if response.status_code == 200:
    session_id = response.json()["session_id"]
    print(f"Session ID: {session_id}")
else:
    print(f"Failed to upload data: {response.text}")
    exit(1)

# Step 3: Connect to the SSE stream
sse_url = f"http://localhost:8000/solve/{session_id}"
client = sseclient.SSEClient(sse_url)

print("Listening for events...")
for event in client:
    print("Received:", event.data)
