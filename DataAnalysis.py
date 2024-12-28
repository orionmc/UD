import re
from collections import defaultdict

text = """
X6 24” screens – MASH @ CJC
==
Inventory of Hardware Collected from warehouse  1 x 5540  
  Asset details of devices collected (if required)     Asset 076975
==
X1 3000 - nhft-073807
==
Hi,

I have booked out the following items:

4 x monitors for SCTASK0035461, SCTASK0031985 and CJC 
==
Inventory of Hardware Collected from warehouse  4 x 5340, 4 x small laptop bag, 1 x 100w usb-c charger, 2 x 5531, 4 x 130w usb-c charger, 3 x 5540, 5 x large laptop bags, 3 x 90w usb-c chargers 
  Asset details of devices collected (if required)     Asset 076507, 077041, 077310, 077303, 074388, 076602, 076557, 075667, 076691
==
Inventory of Hardware Collected from warehouse  1 x 5340
  Asset details of devices collected (if required)     Asset 077309
==
18 x Phones and cases taken sorry
==
Inventory of Hardware Collected from warehouse  19 x Samsung A35s and 19 x Samsung A35 cases 
  Asset details of devices collected (if required)     Devices 12367 - 12384
==
3 x Dell Optiplex 3000 – 073855, 073958, 073917
==
Hi Team,

I have booked out the following items:

5 x monitors for SCTASK0030568, SCTASK0031851 and SCTASK0031985;
3 x docking stn for SCTASK0030568 & SCTASK0031851;
==
X1 3000 desktop – nhft-073920
==
1 x laptop 5330 074658
==
1 x dock and 1 x 5220 polywire headset
"""

# ------------------------------------------------------------------------------
# DATA STRUCTURES FOR FINAL COUNTS
# ------------------------------------------------------------------------------
counts = {
    'monitors': 0,                     # e.g. "4 x monitors", "X6 24” screens"
    'desktops_3000': 0,                # e.g. "X1 3000", "Dell Optiplex 3000"
    'laptops': defaultdict(int),       # key = 4-digit model, val = count
    'phones': defaultdict(int),        # key = phone model (A32 / A34 / A35), val = count
    'bags': defaultdict(int),          # e.g. "small laptop bag", "large laptop bags"
    'chargers': defaultdict(int),      # e.g. "100w usb-c charger", ...
    'docks': 0,                        # "dock" or "docking stn"
    'headsets': defaultdict(int),      # e.g. "5220 polywire headset"
}

# ------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------------

def normalize_item_name(item_name: str) -> str:
    """
    Lowercases and removes extra punctuation to help with matching.
    """
    return re.sub(r'[^a-z0-9\s\-]+', '', item_name.lower()).strip()

def increment_monitors(count: int):
    """Add monitors (or screens) to the total count."""
    counts['monitors'] += count

def increment_3000_desktops(count: int):
    """Add to the total count of '3000' desktops."""
    counts['desktops_3000'] += count

def increment_laptop(model: str, count: int):
    """Add laptops by their 4-digit model."""
    counts['laptops'][model] += count

def increment_phone(model: str, count: int):
    """Add phones by model (A32, A34, A35).
       If model not given, default to A35."""
    if model not in ['A32','A34','A35']:
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


# ------------------------------------------------------------------------------
# REGEX / PARSING LOGIC
# ------------------------------------------------------------------------------
# We look for patterns like:
#   "4 x 5340", "X6 24” screens", "3 x Dell Optiplex 3000", etc.
#
# We'll do a couple of pattern matches:
#   1) A broad pattern to capture something like "<number> x <text>"
#   2) Additional specific pattern checks (like "Dell Optiplex 3000")
#   3) Handling lines that do not follow the "<number> x <text>" pattern (e.g. "X6 24” screens")

# Pattern to match phrases like: "4 x monitors" OR "19 x Samsung A35s"
pattern = r'(\d+)\s*[x×]\s+([^,;\n]+)'

# We'll also handle lines that start with "X<digit>" as in "X6 24\" screens"
# Separate pattern: X(\d+)\s*(.*?)
pattern_x_leading = r'X(\d+)\s+(.*)'

lines = text.split('\n')

for line in lines:
    line_clean = line.strip()
    if not line_clean:
        continue  # skip empty lines

    # 1) Try the "X(\d+)" pattern first (e.g. "X6 24” screens")
    match_x_leading = re.match(pattern_x_leading, line_clean, re.IGNORECASE)
    if match_x_leading:
        num_str, item_str = match_x_leading.groups()
        count_num = int(num_str)
        item_str = normalize_item_name(item_str)

        # If it looks like monitors or screens
        if 'screen' in item_str or 'monitor' in item_str:
            increment_monitors(count_num)
        elif '3000' in item_str:
            # Could be "X1 3000 - nhft-073807" => a 3000 desktop
            increment_3000_desktops(count_num)
        else:
            # If none of the above, you could add additional logic here
            pass
        continue

    # 2) Try the broader "<number> x <something>" pattern
    matches = re.findall(pattern, line_clean, re.IGNORECASE)
    if matches:
        for (num_str, item_str) in matches:
            count_num = int(num_str)
            item_str = normalize_item_name(item_str)

            # Check if "Dell Optiplex 3000"
            if 'dell optiplex 3000' in item_str:
                increment_3000_desktops(count_num)
                continue

            # Check for 4-digit laptops (e.g. "5540", "5340", etc.)
            # We'll use a regex to see if there's a 4-digit match
            four_digit_match = re.match(r'(\d{4})', item_str)
            if four_digit_match:
                laptop_model = four_digit_match.group(1)
                increment_laptop(laptop_model, count_num)
                continue

            # If item_str has the word "3000" (like "1 x 3000 - nhft-073807")
            if '3000' in item_str and 'dell optiplex' not in item_str:
                increment_3000_desktops(count_num)
                continue

            # Check for "monitor" or "screen"
            if 'monitor' in item_str or 'screen' in item_str:
                increment_monitors(count_num)
                continue

            # Phones: check if "phone" or "a32"/"a34"/"a35"
            # ignoring the case or the word "samsung"
            if 'phone' in item_str:
                # If it doesn't say "a32"/"a34"/"a35", default to A35
                # e.g. "18 x phones and cases..."
                phone_model_match = re.search(r'a3[245]', item_str)
                if phone_model_match:
                    model = phone_model_match.group().upper()  # e.g. 'A35'
                else:
                    model = 'A35'  # default
                increment_phone(model, count_num)
                continue

            # If it says "a32" or "a34" or "a35" specifically
            # e.g. "19 x Samsung A35s"
            phone_model_match = re.search(r'a3[245]', item_str)
            if phone_model_match:
                model = phone_model_match.group().upper()  # 'A35'
                # Also check if it says "cases" - we ignore phone cases
                if 'case' not in item_str:
                    increment_phone(model, count_num)
                # If "cases" is included, we skip them.
                continue

            # Check for "bag" => small / large
            if 'bag' in item_str:
                if 'small' in item_str:
                    increment_bag('small', count_num)
                elif 'large' in item_str:
                    increment_bag('large', count_num)
                else:
                    # You can decide how to handle an unspecified bag type
                    increment_bag('unknown', count_num)
                continue

            # Check for chargers: e.g. "100w usb-c charger", "130w usb-c charger"
            if 'charger' in item_str:
                # We'll just store the entire label to keep it simple
                increment_charger(item_str, count_num)
                continue

            # Check for docking station or dock
            if 'dock' in item_str:
                # We'll assume "docking stn", "dock" => same category
                increment_dock(count_num)
                continue

            # Check for headset
            if 'headset' in item_str:
                increment_headset(item_str, count_num)
                continue

            # If we reach here, either it's an unknown item
            # or an asset reference with no model:
            # "Asset 076975" alone doesn't count as an item unless
            # we need the 6-digit asset to represent a device with no model.
            # The problem states:
            # "Where the asset is mentioned - the asset number is always 6 digits
            #  starting with 0, but we only need the asset number if the model
            #  of the item is not mentioned."
            # 
            # So we only count an "unknown device" if we see something like:
            #   "1 x ??? ... Asset 076xxx"
            # 
            # For simplicity, let's skip here.
            pass
    else:
        # Lines that do not match either pattern above can be handled here if needed.
        pass


# ------------------------------------------------------------------------------
# OUTPUT RESULTS
# ------------------------------------------------------------------------------
print("RESULTS:")
print(f"Monitors: {counts['monitors']}")
print(f"Desktops (3000): {counts['desktops_3000']}")

print("Laptops:")
for model, qty in counts['laptops'].items():
    print(f"  {model}: {qty}")

print("Phones:")
for model, qty in counts['phones'].items():
    print(f"  {model}: {qty}")

print("Bags:")
for bag_type, qty in counts['bags'].items():
    print(f"  {bag_type} laptop bag: {qty}")

print("Chargers:")
for charger_label, qty in counts['chargers'].items():
    print(f"  {charger_label}: {qty}")

print(f"Docks: {counts['docks']}")

print("Headsets:")
for headset_label, qty in counts['headsets'].items():
    print(f"  {headset_label}: {qty}")
