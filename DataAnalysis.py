# warehouse_parser.py
import re
from collections import defaultdict

def parse_warehouse_text(text: str) -> dict:
    """
    Parses unstructured text about hardware collected from the warehouse.
    Returns a dictionary with the counts of monitors, desktops, laptops, phones,
    bags, chargers, docks, and headsets.
    """
    # --------------------------------------------------------------------------
    # DATA STRUCTURES FOR FINAL COUNTS
    # --------------------------------------------------------------------------
    counts = {
        'monitors': 0,                      # e.g. "4 x monitors", "X6 24” screens"
        'desktops_3000': 0,                 # e.g. "X1 3000", "Dell Optiplex 3000"
        'laptops': defaultdict(int),        # key = 4-digit model, value = count
        'phones': defaultdict(int),         # key = phone model (A32, A34, A35), value = count
        'bags': defaultdict(int),           # e.g. "small laptop bag", "large laptop bag"
        'chargers': defaultdict(int),       # e.g. "100w usb-c charger", "130w usb-c charger"
        'docks': 0,                         # cumulative count of "dock"/"docking stn"
        'headsets': defaultdict(int),       # e.g. "5220 polywire headset"
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

    def increment_3000_desktops(count: int):
        """Add to the total count of '3000' desktops."""
        counts['desktops_3000'] += count

    def increment_laptop(model: str, count: int):
        """Add laptops by their 4-digit model."""
        counts['laptops'][model] += count

    def increment_phone(model: str, count: int):
        """
        Add phones by model (A32, A34, A35).
        If model not given, default to A35.
        """
        if model not in ['A32', 'A34', 'A35']:
            model = 'A35'  # default per requirement
        counts['phones'][model] += count

    def increment_bag(size_label: str, count: int):
        """Add bags. (e.g. 'small laptop bag', 'large laptop bag')"""
        counts['bags'][size_label] += count

    def increment_charger(label: str, count: int):
        """Add charger counts (e.g. '100w usb-c charger')."""
        counts['chargers'][label] += count

    def increment_dock(count: int):
        """Add docking station / dock count."""
        counts['docks'] += count

    def increment_headset(label: str, count: int):
        """Add headset count (e.g. '5220 polywire headset')."""
        counts['headsets'][label] += count

    # --------------------------------------------------------------------------
    # REGEX / PARSING LOGIC
    # --------------------------------------------------------------------------
    # We look for patterns like:
    #   "4 x 5340", "X6 24” screens", "3 x Dell Optiplex 3000", etc.
    #
    # We'll do a couple of pattern matches:
    #   1) A pattern to capture something like "<number> x <text>"
    #   2) An additional pattern for lines starting with "X<digit>" (e.g. "X6 24” screens")

    pattern_x_leading = r'^X(\d+)\s+(.*)'           # e.g. "X6 24” screens"
    pattern_generic   = r'(\d+)\s*[x×]\s+([^,;\n]+)' # e.g. "4 x monitors"

    lines = text.split('\n')

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue  # skip empty lines

        # 1) Match lines like "X6 24” screens"
        match_x = re.match(pattern_x_leading, line_clean, re.IGNORECASE)
        if match_x:
            num_str, item_str = match_x.groups()
            count_num = int(num_str)
            item_str_normalized = normalize_item_name(item_str)

            # If it looks like monitors or screens
            if 'screen' in item_str_normalized or 'monitor' in item_str_normalized:
                increment_monitors(count_num)
            elif '3000' in item_str_normalized:
                # Could be "X1 3000 - ..." => a 3000 desktop
                increment_3000_desktops(count_num)
            else:
                # Extend logic if you have other 'X(...)' patterns
                pass
            continue

        # 2) Match generic pattern "<number> x <text>"
        found_items = re.findall(pattern_generic, line_clean, re.IGNORECASE)
        if found_items:
            for (num_str, raw_item_str) in found_items:
                count_num = int(num_str)
                item_str_normalized = normalize_item_name(raw_item_str)

                # Check if "Dell Optiplex 3000"
                if 'dell optiplex 3000' in item_str_normalized:
                    increment_3000_desktops(count_num)
                    continue

                # Check for 4-digit laptop models (e.g. 5340, 5540, 5531)
                four_digit_match = re.match(r'(\d{4})', item_str_normalized)
                if four_digit_match:
                    laptop_model = four_digit_match.group(1)
                    increment_laptop(laptop_model, count_num)
                    continue

                # If it specifically says "3000" (but not "dell optiplex 3000")
                if '3000' in item_str_normalized:
                    increment_3000_desktops(count_num)
                    continue

                # Check for "monitor" or "screen"
                if 'monitor' in item_str_normalized or 'screen' in item_str_normalized:
                    increment_monitors(count_num)
                    continue

                # Phones: look for "phone" or "a32"/"a34"/"a35"
                if 'phone' in item_str_normalized:
                    # If it doesn't say "a32"/"a34"/"a35", default to A35
                    phone_model_match = re.search(r'a3[245]', item_str_normalized)
                    if phone_model_match:
                        model = phone_model_match.group().upper()  # 'A35'
                    else:
                        model = 'A35'
                    increment_phone(model, count_num)
                    continue

                # If it says "a32", "a34", or "a35" specifically
                phone_model_match = re.search(r'a3[245]', item_str_normalized)
                if phone_model_match:
                    model = phone_model_match.group().upper()  # 'A35'
                    # Also check if it says 'case' => we ignore phone cases
                    if 'case' not in item_str_normalized:
                        increment_phone(model, count_num)
                    continue

                # Check for "bag"
                if 'bag' in item_str_normalized:
                    if 'small' in item_str_normalized:
                        increment_bag('small', count_num)
                    elif 'large' in item_str_normalized:
                        increment_bag('large', count_num)
                    else:
                        # Unknown type of bag
                        increment_bag('unknown', count_num)
                    continue

                # Check for chargers
                if 'charger' in item_str_normalized:
                    # We'll just store the entire label to keep it simple
                    increment_charger(item_str_normalized, count_num)
                    continue

                # Check for dock/docking station
                if 'dock' in item_str_normalized:
                    increment_dock(count_num)
                    continue

                # Check for headset
                if 'headset' in item_str_normalized:
                    increment_headset(item_str_normalized, count_num)
                    continue

                # If we reach here, it's something we don't handle or it might be
                # an asset reference alone. The problem states we only need the asset
                # number if no model is mentioned. That logic can be added as needed.
                pass
        else:
            # No match => handle if needed
            pass

    # Convert defaultdicts to regular dicts for a cleaner return object
    counts['laptops'] = dict(counts['laptops'])
    counts['phones'] = dict(counts['phones'])
    counts['bags'] = dict(counts['bags'])
    counts['chargers'] = dict(counts['chargers'])
    counts['headsets'] = dict(counts['headsets'])

    return counts


# ------------------------------------------------------------------------------
# EXAMPLE USAGE (if you were to run this module as a script)
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    example_text = """
    X6 24” screens – MASH @ CJC
    ==
    Inventory of Hardware Collected from warehouse  1 x 5540
      Asset details of devices collected (if required)     Asset 076975
    ==
    X1 3000 - nhft-073807
    ==
    4 x monitors
    ==
    Inventory of Hardware Collected from warehouse  4 x 5340, 4 x small laptop bag, 1 x 100w usb-c charger
    ...
    """
    results = parse_warehouse_text(example_text)

    print("RESULTS:")
    print(f"  Monitors: {results['monitors']}")
    print(f"  Desktops (3000): {results['desktops_3000']}")

    print("  Laptops:")
    for model, qty in results['laptops'].items():
        print(f"    {model}: {qty}")

    print("  Phones:")
    for model, qty in results['phones'].items():
        print(f"    {model}: {qty}")

    print("  Bags:")
    for bag_type, qty in results['bags'].items():
        print(f"    {bag_type} bag: {qty}")

    print("  Chargers:")
    for charger_label, qty in results['chargers'].items():
        print(f"    {charger_label}: {qty}")

    print(f"  Docks: {results['docks']}")

    print("  Headsets:")
    for headset_label, qty in results['headsets'].items():
        print(f"    {headset_label}: {qty}")
