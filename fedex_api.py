import requests
import os
import json
import pandas as pd
import time

def get_fedex_access_token(client_id, client_secret, sandbox=True):
    """
    Obtains an OAuth 2.0 access token from the FedEx API.

    Args:
        client_id (str): Your FedEx API Client ID (also known as API Key).
        client_secret (str): Your FedEx API Client Secret (also known as Secret Key).
        sandbox (bool): If True, uses the sandbox environment URL. If False, uses production.

    Returns:
        str: The access token if successful, None otherwise.
    """
    # Determine the correct OAuth token endpoint based on the environment
    if sandbox:
        token_url = "https://apis-sandbox.fedex.com/oauth/token"
    else:
        # For production, you'd use the live URL.
        # Ensure you have a live FedEx shipping account and production keys for this.
        token_url = "https://apis.fedex.com/oauth/token"

    # The payload for the OAuth request
    # grant_type must be 'client_credentials' for this flow
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    # Headers for the OAuth request
    # Content-Type must be 'application/x-www-form-urlencoded'
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    print(f"Attempting to get access token from: {token_url}")
    try:
        # Make the POST request to the OAuth token endpoint
        response = requests.post(token_url, data=payload, headers=headers)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        # Parse the JSON response
        token_data = response.json()

        # Extract the access token
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in") # Token expiration in seconds

        if access_token:
            print(f"Successfully obtained access token. Expires in {expires_in} seconds.")
            return access_token
        else:
            print("Error: Access token not found in response.")
            print(f"Full response: {token_data}")
            return None

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.text}")
        return None
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
        return None
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"An unexpected error occurred: {req_err}")
        return None
    except json.JSONDecodeError as json_err:
        print(f"Error decoding JSON response: {json_err}")
        print(f"Raw response text: {response.text}")
        return None


def get_fedex_status(tracking_number):
    """
    Retrieves the status of a single tracking number via a FedEx API.

    Args:
        tracking_number (str): The specific tracking number to retrieve.

    Returns:
        dict or None: A dictionary containing the tracking status data if successful,
        otherwise None.
    """

    # Ensure you have set your FedEx API credentials in environment variables
    client_id = os.environ.get("FEDEX_CLIENT_ID")
    client_secret = os.environ.get("FEDEX_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("Error: FedEx API credentials are not set in environment variables.")
        return None

    access_token = get_fedex_access_token(client_id, client_secret, sandbox=True)

    if not access_token:
        print("Failed to obtain access token.")
        return None

    # Prepare the API request
    url = "https://apis-sandbox.fedex.com/track/v1/trackingnumbers"
    input = {
            "trackingInfo": [
                {
                    "trackingNumberInfo": {
                    "trackingNumber": tracking_number
                    }
                }
            ],
            "includeDetailedScans": True
        }

    payload = input # 'input' refers to JSON Payload
    headers = {
        'Content-Type': "application/json",
        'X-locale': "en_US",
        'Authorization': f"Bearer {access_token}"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        # Check if the request was successful (HTTP status code 200).
        if response.status_code == 200:
            tracking_data = response.json()
            print(f"Successfully retrieved status for {tracking_number}.")
            # Return the tracking data
            return tracking_data
        else:
            # Handle API errors.
            print(f"Error retrieving status for {tracking_number}. Status code: {response.status_code}")
            print(f"Error response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        # Handle network or other request-related errors.
        print(f"A request error occurred for {tracking_number}: {e}")
        return None
    except json.JSONDecodeError:
        # Handle cases where the response is not valid JSON.
        print(f"Failed to decode JSON from the response for {tracking_number}.")
        return None


def main():
    """
    Main function to process a list of tracking numbers from a "document"
    and check their status.
    """
    # --- Simulating a document with tracking information ---
    # In a real-world scenario, you would read this data from a file (CSV, Excel),
    # a database, or another source.
    tracking_documents = [
        {"tracking_id": "122816215025810"},
        {"tracking_id": "020207021381215"},
    ]

    results = []  # To store extracted info for DataFrame

    # Iterate through each tracking document and call the get status function.
    for doc in tracking_documents:
        tracking_id = doc["tracking_id"]
        status_data = get_fedex_status(tracking_id)
        if status_data:
            try:
                # The FedEx API response structure may vary; adjust as needed
                shipment = status_data.get("output", {}).get("completeTrackResults", [{}])[0]
                track_result = shipment.get("trackResults", [{}])[0]
                status_desc = track_result.get("latestStatusDetail", {}).get("description", None)
                shipper_cc = track_result.get("shipperInformation", {}).get("address",{}).get("countryCode", None)
                consignee_cc = track_result.get("recipientInformation", {}).get("address",{}).get("countryCode", None)
                results.append({
                    "tracking_id": tracking_id,
                    "status_description": status_desc,
                    "shipper_countryCode": shipper_cc,
                    "consignee_countryCode": consignee_cc
                })
            except (KeyError, IndexError, TypeError) as e:
                print(f"Error extracting fields for {tracking_id}: {e}")
        time.sleep(5)
        print("-" * 30)

    # Create DataFrame and print
    df = pd.DataFrame(results)
    print("\nSummary DataFrame:")
    print(df)

if __name__ == "__main__":
    main()
