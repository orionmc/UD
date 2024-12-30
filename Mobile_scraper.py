import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
from tabulate import tabulate
import json
from datetime import datetime
import re

# Constants
BASE_URL = "https://www.gsmarena.com/"
APPLE_PHONES_URL = "https://www.gsmarena.com/apple-phones-48.php"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/85.0.4183.102 Safari/537.36"
    )
}
REQUEST_DELAY = 1  # Seconds between requests to respect rate limiting

# Define Year Range
YEAR_FROM = 2023
YEAR_TO = datetime.now().year  # Present year

# Define the specifications to extract with their corresponding data-spec attributes
DESIRED_SPECS = {
    'Display Size': 'displaysize',
    'Display Resolution': 'displayresolution',
    'Battery Size': 'batdescription1',
    'Memory': 'internalmemory',
    'Front Camera': 'cam2modules',
    'Back Camera': 'cam1modules',
    'Weight': 'weight',
    'Dimension': 'dimensions'
}

def get_total_pages():
    """
    Determines the total number of pages for Apple phones.
    """
    try:
        response = requests.get(APPLE_PHONES_URL, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching Apple phones page: {e}")
        return 1  # Default to 1 to attempt at least the first page

    soup = BeautifulSoup(response.text, 'html.parser')
    pagination = soup.find('div', class_='nav-pages')
    if not pagination:
        return 1  # Only one page exists

    pages = pagination.find_all('a')
    page_numbers = [int(page.text) for page in pages if page.text.isdigit()]
    if max(page_numbers) > 20 
        return 20
    else:
        return max(page_numbers) if page_numbers else 1

def get_apple_phone_links(total_pages):
    """
    Retrieves all Apple phone model URLs from all pages.
    """
    phone_links = []
    for page in range(1, total_pages + 1):
        if page == 1:
            url = APPLE_PHONES_URL
        else:
            url = f"https://www.gsmarena.com/apple-phones-f-{page}.php"
        
        print(f"Fetching Apple phones list from page {page}...")
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to fetch page {page}: {e}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        phone_table = soup.find('div', class_='makers')
        if not phone_table:
            print(f"No phone table found on page {page}.")
            continue

        phones = phone_table.find_all('a')
        for phone in phones:
            href = phone.get('href')
            full_url = urljoin(BASE_URL, href)
            phone_links.append(full_url)
        
        time.sleep(REQUEST_DELAY)  # Respect rate limiting

    return phone_links

def extract_release_year(phone_soup):
    """
    Extracts the release year from a phone's specifications page.
    Looks for <td class="nfo" data-spec="year">2024, October 15</td>
    """
    year_td = phone_soup.find('td', {'class': 'nfo', 'data-spec': 'year'})
    if year_td:
        text = year_td.get_text(separator=" ", strip=True)
        # Extract the year using regex
        match = re.search(r'\b(20\d{2}|19\d{2})\b', text)
        if match:
            return int(match.group(0))
    return None

def get_spec_value(phone_soup, data_spec):
    """
    Retrieves the text value for a given data-spec attribute.
    """
    spec_td = phone_soup.find('td', {'class': 'nfo', 'data-spec': data_spec})
    if spec_td:
        # Remove any HTML tags like <sup> or <a>
        for sup in spec_td.find_all(['sup', 'a']):
            sup.decompose()
        return spec_td.get_text(separator=" ", strip=True)
    return "N/A"

def get_specs(phone_url):
    """
    Fetches and parses the phone specifications from its GSMArena page.
    Returns a dictionary of specifications.
    """
    try:
        response = requests.get(phone_url, headers=HEADERS)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch phone page: {phone_url}. Error: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    specs = {}

    # Extract phone name
    name_tag = soup.find('h1', class_='specs-phone-name-title')
    if name_tag:
        specs['Phone Name'] = name_tag.text.strip()
    else:
        specs['Phone Name'] = "Unknown"

    # Extract release year
    release_year = extract_release_year(soup)
    specs['Release Year'] = release_year if release_year else "Unknown"

    # Extract desired specifications
    for spec_name, data_spec in DESIRED_SPECS.items():
        spec_value = get_spec_value(soup, data_spec)
        specs[spec_name] = spec_value

    return specs

def display_specs_table(specs_list):
    """
    Displays the specifications in a table format.
    """
    if not specs_list:
        print("No specifications to display.")
        return

    # Define the table headers based on DESIRED_SPECS
    headers = ["Phone Name", "Release Year"] + list(DESIRED_SPECS.keys())
    table = []

    for specs in specs_list:
        row = [
            specs.get('Phone Name', 'N/A'),
            specs.get('Release Year', 'N/A'),
            specs.get('Display Size', 'N/A'),
            specs.get('Display Resolution', 'N/A'),
            specs.get('Battery Size', 'N/A'),
            specs.get('Memory', 'N/A'),
            specs.get('Front Camera', 'N/A'),
            specs.get('Back Camera', 'N/A'),
            specs.get('Weight', 'N/A'),
            specs.get('Dimension', 'N/A')
        ]
        table.append(row)

    print(tabulate(table, headers=headers, tablefmt="grid"))

def main():
    print(f"Fetching Apple phone models released from {YEAR_FROM} to {YEAR_TO}...\n")

    total_pages = get_total_pages()
    phone_links = get_apple_phone_links(total_pages)

    print(f"\nTotal Apple phones found: {len(phone_links)}")
    filtered_phones = []

    for idx, phone_url in enumerate(phone_links, 1):
        print(f"\nProcessing ({idx}/{len(phone_links)}): {phone_url}")
        specs = get_specs(phone_url)
        if not specs:
            print("Skipping due to failed specs retrieval.")
            continue

        release_year = specs.get('Release Year')
        if isinstance(release_year, int) and YEAR_FROM <= release_year <= YEAR_TO:
            filtered_phones.append(specs)
            print(f"Included: {specs.get('Phone Name')} ({release_year})")
        else:
            print(f"Excluded: Release Year {release_year} not in range.")

        time.sleep(REQUEST_DELAY)  # Respect rate limiting

    print(f"\nTotal Apple phones released between {YEAR_FROM} and {YEAR_TO}: {len(filtered_phones)}\n")
    display_specs_table(filtered_phones)

    if not filtered_phones:
        print("No phones found in the specified range.")
    else:
        # Save the specs to a JSON file
        output_filename = f"apple_phones_{YEAR_FROM}_{YEAR_TO}.json"
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(filtered_phones, f, ensure_ascii=False, indent=4)
            print(f"\nSpecifications saved to {output_filename}")
        except IOError as e:
            print(f"Failed to save specifications to {output_filename}. Error: {e}")

if __name__ == "__main__":
    main()
