# warehouse_parser.py
import re
from collections import defaultdict
from typing import List, Dict, Any

def parse_emails(email_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Parses a list of email data dictionaries describing hardware collected from the warehouse.
    Returns a dictionary with the counts of monitors, desktops, laptops, phones,
    bags, chargers, docks, headsets, and a list of unparsable lines with sender and time details.

    :param email_data: A list of dictionaries, each containing:
                       - "body": str (email body)
                       - "sender": str (sender's name or email)
                       - "received_time": str (timestamp of when the email was received)
    :return: A dictionary with aggregated counts per item category and a list of unparsable lines.
    """
    
    # Define lists for desktop, laptop, and phone models for flexibility and future tuning
    DESKTOP_MODELS = ["3000", "3010"]  
    LAPTOP_MODELS = ["5340", "5330", "5531", "5540", "5666"]  
    PHONE_MODELS = ["A32", "A34", "A35", "S23"]  
    
    # --------------------------------------------------------------------------
    # DATA STRUCTURES FOR FINAL COUNTS
    # --------------------------------------------------------------------------
    counts = {
        'monitors': 0,                       # e.g., "4 x monitors", "X6 24” screens"
        'desktops': defaultdict(int),        # For recognized desktop models
        'laptops': defaultdict(int),         # For recognized laptop models
        'phones': defaultdict(int),          # For recognized phone models
        'bags': defaultdict(int),            # e.g., "small laptop bag", "large laptop bag"
        'chargers': defaultdict(int),        # e.g., "100w usb-c charger", "130w usb-c charger"
        'docks': 0,                          # Cumulative count of "dock"/"docking stn"
        'headsets': defaultdict(int),        # e.g., "5220 polywire headset"

        'unparsable_lines': []               # List to store entire unparsable lines with sender and time
    }

    # --------------------------------------------------------------------------
    # HELPER FUNCTIONS
    # --------------------------------------------------------------------------
    def normalize_item_name(item_name: str) -> str:
        """
        Lowercases and removes extra punctuation to help with matching.
        """
        return re.sub(r'[^a-z0-9\s\-]+', '', item_name.lower()).strip()

    def increment_monitors(count: int):
        """Add monitors (screens) to the total count."""
        counts['monitors'] += count

    def increment_desktop(model: str, count: int):
        """Increment a recognized desktop model."""
        counts['desktops'][model] += count

    def increment_laptop(model: str, count: int):
        """Increment a recognized laptop model."""
        counts['laptops'][model] += count

    def increment_phone(model: str, count: int):
        """
        Add phones by model (e.g., A32, A34, A35).
        If model not given or unrecognized, default to A35.
        """
        if model not in PHONE_MODELS:
            model = 'A35'  # default per requirement
        counts['phones'][model] += count

    def increment_unparsable(line: str, sender: str, time: str):
        """Add entire unparsable lines with sender and time details."""
        counts['unparsable_lines'].append({
            'line': line,
            'sender': sender,
            'received_time': time
        })

    def increment_bag(size_label: str, count: int):
        """Add bags. (e.g., 'small laptop bag', 'large laptop bag')"""
        counts['bags'][size_label] += count

    def increment_charger(label: str, count: int):
        """Add charger counts (e.g., '100w usb-c charger')."""
        counts['chargers'][label] += count

    def increment_dock(count: int):
        """Add docking station / dock count."""
        counts['docks'] += count

    def increment_headset(label: str, count: int):
        """Add headset count (e.g., '5220 polywire headset')."""
        counts['headsets'][label] += count

    # --------------------------------------------------------------------------
    # REGEX / PARSING LOGIC
    # --------------------------------------------------------------------------
    # Patterns to capture item references:
    #   (1) Lines like "X6 24” screens"
    #   (2) Lines like "4 x monitors", "19 x Samsung A35s", etc.
    #   (3) Lines like "Laptop 5666", "PC x2 3111"

    pattern_x_leading = r'^X(\d+)\s+(.*)'           # e.g., "X6 24” screens"
    pattern_generic   = r'(\d+)\s*[x×]\s+([^,;\n]+)' # e.g., "4 x monitors", "PC x2 3111"
    pattern_category_model = r'^(Laptop|PC)\s+(\d{4})$'  # e.g., "Laptop 5666"

    # Compile phone model pattern to find models not followed by 'case' or 'cases'
    phone_pattern = re.compile(r'\b(' + '|'.join(PHONE_MODELS) + r')\b(?!\s*(case|cases))', re.IGNORECASE)

    for email in email_data:
        body = email.get("body", "")
        sender = email.get("sender", "Unknown Sender")
        received_time = email.get("received_time", "Unknown Time")

        lines = body.split('\n')
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue  # skip empty lines

            parsed = False  # Flag to check if the line has been parsed

            # (1) Match lines like "X6 24” screens"
            match_x = re.match(pattern_x_leading, line_clean, re.IGNORECASE)
            if match_x:
                num_str, item_str = match_x.groups()
                count_num = int(num_str)
                item_str_normalized = normalize_item_name(item_str)

                # If it looks like monitors or screens
                if 'screen' in item_str_normalized or 'monitor' in item_str_normalized:
                    increment_monitors(count_num)
                    parsed = True
                else:
                    # Check if it starts with a known desktop or laptop model
                    four_digit_match = re.match(r'(\d{4})', item_str_normalized)
                    if four_digit_match:
                        model = four_digit_match.group(1)
                        if model in DESKTOP_MODELS:
                            increment_desktop(model, count_num)
                            parsed = True
                        elif model in LAPTOP_MODELS:
                            increment_laptop(model, count_num)
                            parsed = True
                        else:
                            # If 4-digit model not recognized, mark as unparsable
                            increment_unparsable(line_clean, sender, received_time)
                            parsed = True  # Consider the line as handled (unparsable)
                    else:
                        # If no recognizable pattern, mark as unparsable
                        increment_unparsable(line_clean, sender, received_time)
                        parsed = True  # Consider the line as handled (unparsable)
                continue  # Move to the next line after processing

            # (2) Match generic pattern "<number> x <text>"
            found_items = re.findall(pattern_generic, line_clean, re.IGNORECASE)
            if found_items:
                for (num_str, raw_item_str) in found_items:
                    count_num = int(num_str)
                    item_str_normalized = normalize_item_name(raw_item_str)

                    # Check for 4-digit model first
                    four_digit_match = re.match(r'(\d{4})', item_str_normalized)
                    if four_digit_match:
                        model = four_digit_match.group(1)

                        if model in DESKTOP_MODELS:
                            increment_desktop(model, count_num)
                            parsed = True
                        elif model in LAPTOP_MODELS:
                            increment_laptop(model, count_num)
                            parsed = True
                        else:
                            # If 4-digit model not recognized, mark as unparsable
                            increment_unparsable(line_clean, sender, received_time)
                            parsed = True
                        continue  # Move to the next found item

                    # Check if it's a phone (look for A32, A34, A35, S23)
                    if 'phone' in item_str_normalized:
                        # Extract phone model if present
                        phone_model_match = re.search(r'\b(a3[245]|s23)\b', item_str_normalized, re.IGNORECASE)
                        if phone_model_match:
                            model = phone_model_match.group(1).upper()
                        else:
                            model = 'A35'  # default
                        # Check if it includes 'case' to ignore phone cases
                        if 'case' not in item_str_normalized:
                            increment_phone(model, count_num)
                            parsed = True
                        else:
                            # If it's a phone case, mark as unparsable
                            increment_unparsable(line_clean, sender, received_time)
                            parsed = True
                        continue  # Move to the next found item

                    # Directly check for phone models without the word "phone"
                    phone_model_match = re.search(r'\b(a3[245]|s23)\b', item_str_normalized, re.IGNORECASE)
                    if phone_model_match:
                        model = phone_model_match.group(1).upper()
                        # Ensure it's not a case
                        if 'case' not in item_str_normalized:
                            increment_phone(model, count_num)
                            parsed = True
                        else:
                            # If it's a phone case, mark as unparsable
                            increment_unparsable(line_clean, sender, received_time)
                            parsed = True
                        continue  # Move to the next found item

                    # Check for "monitor" or "screen"
                    if 'monitor' in item_str_normalized or 'screen' in item_str_normalized:
                        increment_monitors(count_num)
                        parsed = True
                        continue  # Move to the next found item

                    # Check for "bag"
                    if 'bag' in item_str_normalized:
                        if 'small' in item_str_normalized:
                            increment_bag('small', count_num)
                            parsed = True
                        elif 'large' in item_str_normalized:
                            increment_bag('large', count_num)
                            parsed = True
                        else:
                            # Unknown type of bag, mark as unparsable
                            increment_unparsable(line_clean, sender, received_time)
                            parsed = True
                        continue  # Move to the next found item

                    # Check for chargers
                    if 'charger' in item_str_normalized:
                        increment_charger(item_str_normalized, count_num)
                        parsed = True
                        continue  # Move to the next found item

                    # Check for dock/docking station
                    if 'dock' in item_str_normalized:
                        increment_dock(count_num)
                        parsed = True
                        continue  # Move to the next found item

                    # Check for headset
                    if 'headset' in item_str_normalized:
                        increment_headset(item_str_normalized, count_num)
                        parsed = True
                        continue  # Move to the next found item

                    # If it doesn't match any known category, mark as unparsable
                    increment_unparsable(line_clean, sender, received_time)
                    parsed = True
                continue  # Move to the next line after processing all found items

            # (3) Match category and model pattern, e.g., "Laptop 5666"
            match_category_model = re.match(pattern_category_model, line_clean, re.IGNORECASE)
            if match_category_model:
                category, model = match_category_model.groups()
                category = category.lower()
                model = model.strip()

                if category == 'laptop' and model in LAPTOP_MODELS:
                    increment_laptop(model, 1)
                    parsed = True
                elif category == 'pc' and model in DESKTOP_MODELS:
                    increment_desktop(model, 1)
                    parsed = True
                else:
                    # If model not recognized, mark as unparsable
                    increment_unparsable(line_clean, sender, received_time)
                    parsed = True
                continue  # Move to the next line after processing

            # (4) If no patterns matched, attempt to extract known models within the line
            # and mark the remaining as unparsable
            # Extract known phone models
            phone_matches = phone_pattern.findall(line_clean)
            for model in phone_matches:
                model_upper = model.upper()
                increment_phone(model_upper, 1)
                parsed = True
                # Remove the matched model from the line to capture remaining unparsable text
                line_clean = re.sub(r'\b' + re.escape(model) + r'\b', '', line_clean, flags=re.IGNORECASE)

            # Extract known desktop and laptop models
            for model in DESKTOP_MODELS:
                if re.search(r'\b' + re.escape(model) + r'\b', line_clean):
                    increment_desktop(model, 1)
                    parsed = True
                    # Remove the matched model from the line
                    line_clean = re.sub(r'\b' + re.escape(model) + r'\b', '', line_clean)

            for model in LAPTOP_MODELS:
                if re.search(r'\b' + re.escape(model) + r'\b', line_clean):
                    increment_laptop(model, 1)
                    parsed = True
                    # Remove the matched model from the line
                    line_clean = re.sub(r'\b' + re.escape(model) + r'\b', '', line_clean)

            # After extracting known models, if there's any remaining text, mark as unparsable
            if parsed and line_clean.strip():
                increment_unparsable(line_clean.strip(), sender, received_time)

            # If nothing was parsed, mark the entire line as unparsable
            if not parsed and line_clean:
                increment_unparsable(line_clean, sender, received_time)

    # Convert defaultdicts to regular dicts for a cleaner return object
    counts['desktops'] = dict(counts['desktops'])      # Convert defaultdict to dict
    counts['laptops'] = dict(counts['laptops'])        # Convert defaultdict to dict
    counts['phones'] = dict(counts['phones'])          # Convert defaultdict to dict
    counts['bags'] = dict(counts['bags'])              # Convert defaultdict to dict
    counts['chargers'] = dict(counts['chargers'])      # Convert defaultdict to dict
    counts['headsets'] = dict(counts['headsets'])      # Convert defaultdict to dict
    # 'unparsable_lines' remains a list

    return counts