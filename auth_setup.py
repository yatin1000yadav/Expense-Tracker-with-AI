import json
import os

AUTH_FILE = "auth.json"

if not os.path.exists(AUTH_FILE) or os.path.getsize(AUTH_FILE) == 0:
    with open(AUTH_FILE, "w") as f:
        json.dump({"users": []}, f, indent=4)

with open(AUTH_FILE, "r") as f:
    auth_data = json.load(f)
