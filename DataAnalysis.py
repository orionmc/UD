# warehouse_parser.py
import re
from collections import defaultdict

def parse_warehouse_list(lines: list[str]) -> dict:
    """
    Parses a list of text lines describing hardware collected from the warehouse.
    Returns a dictionary with the counts of monitors, desktops, laptops, phones,
    bags, chargers, docks, headsets, and unparsable lines.

    :param lines: A list of strings, where each string is one line of the unstructured text.
    :return: A dictionary with aggregated counts per item category and a list of unparsable lines.
    """

    # [NEW] Define lists for desktop, laptop, and phone models for flexibility
    DESKTOP_MODELS = ["3000", "3010"]                  # Add or remove desktop models here
    LAPTOP_MODELS = ["5340", "5330", "5531", "5540", "5666"]   # Add or remove laptop models here
    PHONE_MODELS = ["A32", "A34", "A35"]               # Add or remove phone models here

    # --------------------------------------------------------------------------
    # DATA STRUCTURES FOR FINAL COUNTS
    # --------------------------------------------------------------------------
    counts = {
        'monitors': 0,                       # e.g., "4 x monitors", "X6 24” screens"

        'desktops': defaultdict(int),        # [NEW] For recognized desktop models
        'laptops': defaultdict(int),         # [NEW] For recognized laptop models
        'phones': defaultdict(int),          # [NEW] For recognized phone models
        'bags': defaultdict(int),            # e.g., "small laptop bag", "large laptop bag"
        'chargers': defaultdict(int),        # e.g., "100w usb-c charger", "130w usb-c charger"
        'docks': 0,                          # Cumulative count of "dock"/"docking stn"
        'headsets': defaultdict(int),        # e.g., "5220 polywire headset"

        'unparsable_lines': []               # [NEW] List to store entire unparsable lines
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

    # [NEW] Function to increment desktop counts based on model
    def increment_desktop(model: str, count: int):
        """Increment a recognized desktop model."""
        counts['desktops'][model] += count

    # [NEW] Function to increment laptop counts based on model
    def increment_laptop(model: str, count: int):
        """Increment a recognized laptop model."""
        counts['laptops'][model] += count

    # [NEW] Function to increment phone counts based on model
    def increment_phone(model: str, count: int):
        """
        Add phones by model (e.g., A32, A34, A35).
        If model not given or unrecognized, default to A35.
        """
        if model not in PHONE_MODELS:
            model = 'A35'  # default per requirement
        counts['phones'][model] += count

    # [NEW] Function to increment unparsable lines
    def increment_unparsable(line: str):
        """Add entire unparsable lines to unparsable_lines list."""
        counts['unparsable_lines'].append(line)

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
    #   (2) Lines/phrases like "4 x monitors", "19 x Samsung A35s", etc.

    pattern_x_leading = r'^X(\d+)\s+(.*)'           # e.g., "X6 24” screens"
    pattern_generic   = r'(\d+)\s*[x×]\s+([^,;\n]+)' # e.g., "4 x monitors"

    # [NEW] Compile phone model pattern to find models not followed by 'case' or 'cases'
    phone_pattern = re.compile(r'\b(' + '|'.join(PHONE_MODELS) + r')\b(?!\s*(case|cases))', re.IGNORECASE)

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
                # [NEW] Check if it starts with a known desktop or laptop model
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
                        # [NEW] If 4-digit model not recognized, mark as unparsable
                        increment_unparsable(line_clean)
                        parsed = True  # Consider the line as handled (unparsable)
                else:
                    # [NEW] If no recognizable pattern, mark as unparsable
                    increment_unparsable(line_clean)
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

                    if model in DESKTOP_MODELS:          # [NEW]
                        increment_desktop(model, count_num)
                        parsed = True
                    elif model in LAPTOP_MODELS:         # [NEW]
                        increment_laptop(model, count_num)
                        parsed = True
                    else:
                        # [NEW] If 4-digit model not recognized, mark as unparsable
                        increment_unparsable(line_clean)
                        parsed = True
                    continue  # Move to the next found item

                # Check if it's a phone (look for A32, A34, A35)
                if 'phone' in item_str_normalized:
                    # Extract phone model if present
                    phone_model_match = re.search(r'\b(a3[245])\b', item_str_normalized)
                    if phone_model_match:
                        model = phone_model_match.group(1).upper()
                    else:
                        model = 'A35'  # default
                    # Check if it includes 'case' to ignore phone cases
                    if 'case' not in item_str_normalized:
                        increment_phone(model, count_num)
                        parsed = True
                    else:
                        # [NEW] If it's a phone case, mark as unparsable
                        increment_unparsable(line_clean)
                        parsed = True
                    continue  # Move to the next found item

                # Directly check for phone models without the word "phone"
                phone_model_match = re.search(r'\b(a3[245])\b', item_str_normalized)
                if phone_model_match:
                    model = phone_model_match.group(1).upper()
                    # Ensure it's not a case
                    if 'case' not in item_str_normalized:
                        increment_phone(model, count_num)
                        parsed = True
                    else:
                        # [NEW] If it's a phone case, mark as unparsable
                        increment_unparsable(line_clean)
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
                        # [NEW] Unknown type of bag, mark as unparsable
                        increment_unparsable(line_clean)
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

                # [NEW] If it doesn't match any known category, mark as unparsable
                increment_unparsable(line_clean)
                parsed = True
            continue  # Move to the next line after processing all found items

        # [NEW] If no patterns matched, attempt to detect known models without counts
        # Search for phone models not preceded by counts
        phone_matches = phone_pattern.findall(line_clean)
        if phone_matches:
            for model_tuple in phone_matches:
                model = model_tuple[0].upper()
                increment_phone(model, 1)  # [NEW] Assign a default count of 1
                parsed = True

        # [NEW] Additionally, scan for known laptop and desktop models without counts
        # Handle laptops
        for model in LAPTOP_MODELS:
            if re.search(r'\b' + re.escape(model) + r'\b', line_clean):
                counts['laptops'][model] += 1
                parsed = True

        # Handle desktops
        for model in DESKTOP_MODELS:
            if re.search(r'\b' + re.escape(model) + r'\b', line_clean):
                counts['desktops'][model] += 1
                parsed = True

        # [NEW] If the line has been parsed, continue to the next line
        if parsed:
            continue

        # [NEW] If the line couldn't be parsed, mark it as unparsable
        increment_unparsable(line_clean)

    # Convert defaultdicts to regular dicts for a cleaner return object
    counts['desktops'] = dict(counts['desktops'])      # [NEW]
    counts['laptops'] = dict(counts['laptops'])        # [NEW]
    counts['phones'] = dict(counts['phones'])          # [NEW]
    counts['bags'] = dict(counts['bags'])
    counts['chargers'] = dict(counts['chargers'])
    counts['headsets'] = dict(counts['headsets'])
    # 'unparsable_lines' remains a list

    return counts