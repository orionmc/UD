import requests
import sys
import time

# County name or a full postcode.
INPUT_AREAS = [
    "Northamptonshire",    # County name
    "PE15 0PR",            # Full postcode (e.g., York)
]

ENV_AGENCY_API_KEY = None
# Environment Agency Flood Warnings API endpoint
FLOOD_WARNINGS_API_URL = "https://environment.data.gov.uk/flood-monitoring/id/floods"
# Postcodes.io API endpoint for resolving postcodes
POSTCODES_API_URL = "https://api.postcodes.io/postcodes/"

# Delay between API requests to respect rate limits (in seconds)
API_REQUEST_DELAY = 0.2

# Resolves a full postcode to its corresponding administrative district using Postcodes.io API.
    # Parameters: postcode (str): Postcode to resolve.
    # Returns:    str: The administrative district (county) associated with the postcode.
def resolve_postcode(postcode):

    postcode_clean = postcode.strip().replace(" ", "").upper()
    url = POSTCODES_API_URL + postcode_clean

    try:
        response = requests.get(url, timeout=10)
        time.sleep(API_REQUEST_DELAY)  # Respect rate limits
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error resolving postcode '{postcode}': {e}")
        return None

    data = response.json()

    if data['status'] != 200 or not data.get('result'):
        print(f"Warning: Postcode '{postcode}' not found.")
        return None

    admin_district = data['result'].get('admin_district')
    if not admin_district:
        print(f"Warning: Administrative district not found for postcode '{postcode}'.")
        return None

    return admin_district

# Retrieves flood warnings for a specified area using the Environment Agency API.
# Parameters: area_name (str): The name of the area to check for flood warnings.
# Returns:    list: A list of flood warnings for the specified area.
def get_flood_warnings(area_name):

    params = {
        'status': 'warning',  # Fetch only active warnings
        'limit': 1000,        
    }

    params['areaName'] = area_name
    headers = {}
    if ENV_AGENCY_API_KEY:
        headers['x-api-key'] = ENV_AGENCY_API_KEY

    try:
        response = requests.get(FLOOD_WARNINGS_API_URL, params=params, headers=headers, timeout=10)
        time.sleep(API_REQUEST_DELAY)  
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching flood warnings for area '{area_name}': {e}")
        return []

    data = response.json()

    if 'items' not in data:
        return []

    warnings = data['items']

    filtered_warnings = [
        warning for warning in warnings
        if 'areaName' in warning and warning['areaName'].lower() == area_name.lower()
    ]

    return filtered_warnings

# Processes a list of input areas
# Parameters: areas (list): A list of areas (county names or full postcodes).
# Returns:    dict: A dictionary with area names as keys and their flood warning statuses as values.
def process_areas(areas):   

    results = {}

    for input_area in areas:
        input_area_clean = input_area.strip()
        print(f"Processing input: '{input_area_clean}'")

        if any(char.isdigit() for char in input_area_clean):
            resolved_area = resolve_postcode(input_area_clean)
            if not resolved_area:
                results[input_area_clean] = "Invalid postcode or unable to resolve."
                continue

            area = resolved_area
            warnings = get_flood_warnings(area)
            if warnings:
                results[input_area_clean] = f"Active Flood Warnings ({len(warnings)} warning(s))"
            else:
                results[input_area_clean] = "No active flood warnings."
        else:
            area = input_area_clean
            warnings = get_flood_warnings(area)
            if warnings:
                results[area] = f"Active Flood Warnings ({len(warnings)} warning(s))"
            else:
                results[area] = "No active flood warnings."

    return results

# Prints the flood warning results in a structured format.
# Parameters: results (dict): A dictionary with area names as keys and flood warning statuses as values.
def print_results(results):

    print("\n=== Flood Warning Status ===\n")
    for area, status in results.items():
        print(f"Area: {area}")
        print(f"Status: {status}\n")

def main():
    print("Starting Flood Warning Checker...\n")
    results = process_areas(INPUT_AREAS)
    print_results(results)
    print("Flood Warning Checker completed.")

if __name__ == "__main__":
    main()
