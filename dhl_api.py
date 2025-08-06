import requests
import json
import time
import os
import pandas as pd

def get_dhl_status(tracking_number):
    """
    Retrieves the status of a single tracking number via a DHL API.

    Args:
        tracking_number (str): The specific tracking number to retrieve.

    Returns:
        dict or None: A dictionary containing the tracking status data if successful,
        otherwise None.
    """

    api_url = f"https://api-test.dhl.com/track/shipments?trackingNumber={tracking_number}"

    headers = {'DHL-API-Key': os.environ.get("DHL_API_KEY")}

    print(f"Attempting to retrieve status for tracking number: {tracking_number}...")

    try:
        # Make the GET request to the API endpoint.
        response = requests.get(api_url, headers=headers, timeout=10)

        # Check if the request was successful (HTTP status code 200).
        if response.status_code == 200:
            tracking_data = response.json()
            print(f"Successfully retrieved status for {tracking_number}.")
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
        {"tracking_id": "8917799995"},
        {"tracking_id": "8162797823"},
    ]

    results = []  # To store extracted info for DataFrame

    # Iterate through each tracking document and call the get status function.
    for doc in tracking_documents:
        tracking_id = doc["tracking_id"]
        status_data = get_dhl_status(tracking_id)
        if status_data:
            # Extract required fields from the DHL API response
            try:
                shipment = status_data["shipments"][0]
                #status_desc = shipment["status"]["description"]
                #shipper_cc = shipment["details"]["shipper"]["address"].get("countryCode", None)
                #consignee_cc = shipment["details"]['consignee']["address"].get("countryCode", None)
                results.append({
                    "tracking_id": tracking_id,
                    #"status_description": status_desc,
                    #"shipper_countryCode": shipper_cc,
                    #"consignee_countryCode": consignee_cc
                })
            except (KeyError, IndexError, TypeError) as e:
                print(f"Error extracting fields for {tracking_id}: {e}")

        # Add a small delay between API calls to avoid hitting rate limits.
        time.sleep(5) # Adjusted to 5 seconds for better rate limiting
        print("-" * 30)

    # Create DataFrame and print
    df = pd.DataFrame(results)
    print("\nSummary DataFrame:")
    print(df)

if __name__ == "__main__":
    main()
