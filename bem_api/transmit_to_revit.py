import requests
import json
import sys
import os

# Your pyRevit listener endpoint
URL = "http://localhost:48884/bem_api/execute"


def send_payload(json_filepath):
    print("--- BEM API TRANSMITTER ---")

    # 1. Validate file exists
    if not os.path.exists(json_filepath):
        print("ERROR: Could not find payload file at '{}'".format(json_filepath))
        return

    # 2. Read the JSON payload
    with open(json_filepath, 'r') as file:
        try:
            payload = json.load(file)
        except Exception as e:
            print("ERROR: Invalid JSON format in '{}'.\nDetails: {}".format(json_filepath, e))
            return

    print("Target Payload: {}".format(os.path.basename(json_filepath)))
    print("Connecting to:  {}...".format(URL))

    # 3. Fire the POST request
    try:
        response = requests.post(URL, json=payload, headers={'Content-Type': 'application/json'})

        # 4. Display the results
        print("\n--- SERVER RESPONSE [{}] ---".format(response.status_code))
        try:
            # Try to format the response nicely if it's JSON
            response_json = response.json()
            print(json.dumps(response_json, indent=2))
        except ValueError:
            # Fallback to raw text if the server throws a raw HTML/Text error
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("\nFATAL ERROR: Connection refused.")
        print("Are you sure Revit is open and the pyRevit listener script is running?")


if __name__ == "__main__":
    # If you run `python transmit_to_revit.py my_payload.json`, it uses that file.
    # Otherwise, it defaults to `level_maker.json`.
    target_file = sys.argv[1] if len(sys.argv) > 1 else "level_maker.json"
    send_payload(target_file)