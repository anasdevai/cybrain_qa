"""
Check if the server's API is responding via the external IP.
"""
import paramiko
import os
import requests

SERVER = "65.21.244.158"

def main():
    print(f"Connecting to http://{SERVER}/api/sops")
    try:
        response = requests.get(f"http://{SERVER}/api/sops", timeout=10)
        print("Status code:", response.status_code)
        print("Response body preview:", response.text[:200])
    except Exception as e:
        print("Error fetching API:", e)

if __name__ == "__main__":
    main()
