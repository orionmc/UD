import re
from collections import defaultdict
import spacy

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

def extract_collected_items(email_data):
    # Define patterns
    inventory_pattern = re.compile(r'Inventory of Hardware Collected from warehouse\s*(.+)', re.IGNORECASE | re.DOTALL)
    item_pattern = re.compile(r'(\d+)\s*[xX]\s*([^,;\n]+)')
    
    # Define phone, laptop, and desktop models
    phone_models = {'A32', 'A34', 'A35'}
    laptop_models = {'5330', '5340', '5540', '5531'}  # Add all known laptop model numbers here
    desktop_models = {'3000'}  # Add all known desktop model numbers here
    
    # Initialize results
    collected_items = defaultdict(lambda: defaultdict(int))
    unknown_items = []
    
    for email in email_data:
        body = email.get("body", "")
        sender = email.get("sender", "Unknown Sender")
        received_time = email.get("received_time", "Unknown Time")
        
        # Search for inventory section
        inventory_match = inventory_pattern.search(body)
        if inventory_match:
            inventory_text = inventory_match.group(1)
            
            # Split the inventory text into items separated by commas, semicolons, or newlines
            items = re.split(r'[,\n;]+', inventory_text)
            
            for item in items:
                item = item.strip()
                if not item:
                    continue
                # Use regex to extract count and item description
                match = item_pattern.match(item)
                if match:
                    count = int(match.group(1))
                    item_desc = match.group(2).strip()
                    
                    # Process item description with spaCy
                    doc = nlp(item_desc)
                    tokens = [token.text for token in doc]
                    
                    # Initialize variables
                    category = None
                    model = None
                    
                    # Check for model numbers
                    # First, check for 4-digit model numbers
                    model_match = re.search(r'\b(\d{4})\b', item_desc)
                    if model_match:
                        model_number = model_match.group(1)
                        if model_number in laptop_models:
                            category = 'Laptop'
                            model = model_number
                            collected_items[category][model] += count
                            continue
                        elif model_number in desktop_models:
                            category = 'Desktop'
                            model = model_number
                            collected_items[category][model] += count
                            continue
                        else:
                            # Model number not recognized
                            unknown_items.append({
                                "text": item,
                                "sender": sender,
                                "received_time": received_time
                            })
                            continue  # Move to next item
                    
                    # Check for phone models
                    phone_model_match = re.search(r'\b(A32|A34|A35)\b', item_desc, re.IGNORECASE)
                    if 'phone' in item_desc.lower() or 'phones' in item_desc.lower():
                        if phone_model_match:
                            model = phone_model_match.group(1).upper()
                        else:
                            model = 'A35'  # Default model
                        category = 'Phone'
                        collected_items[category][model] += count
                        continue  # Move to next item
                    
                    # Check for chargers
                    if re.search(r'\bcharger\b', item_desc.lower()):
                        charger_type = item_desc.lower()
                        category = 'Charger'
                        collected_items[category][charger_type] += count
                        continue  # Move to next item
                        
                    # Check for docking stations or docks
                    if re.search(r'\bdocking station\b|\bdock\b', item_desc.lower()):
                        dock_type = item_desc.lower()
                        category = 'Dock'
                        collected_items[category][dock_type] += count
                        continue  # Move to next item
                        
                    # Check for laptop bags
                    if re.search(r'\blaptop bag\b', item_desc.lower()):
                        bag_type = item_desc.lower()
                        category = 'Laptop Bag'
                        collected_items[category][bag_type] += count
                        continue  # Move to next item
                        
                    # Check for headsets
                    if re.search(r'\bheadset\b', item_desc.lower()):
                        headset_type = item_desc.lower()
                        category = 'Headset'
                        collected_items[category][headset_type] += count
                        continue  # Move to next item
                        
                    # Check for screens/monitors
                    if re.search(r'\bmonitor\b|\bscreen\b', item_desc.lower()):
                        monitor_type = item_desc.lower()
                        category = 'Monitor'
                        collected_items[category][monitor_type] += count
                        continue  # Move to next item
                        
                    # If item description contains asset numbers but no model
                    asset_match = re.search(r'\bAsset\s+0\d{5}\b', item_desc, re.IGNORECASE)
                    if asset_match:
                        # Model is not mentioned, cannot extract
                        unknown_items.append({
                            "text": item,
                            "sender": sender,
                            "received_time": received_time
                        })
                        continue  # Move to next item
                        
                    # If none of the above, mark as unknown
                    unknown_items.append({
                        "text": item,
                        "sender": sender,
                        "received_time": received_time
                    })
                else:
                    # If pattern doesn't match, mark as unknown
                    unknown_items.append({
                        "text": item,
                        "sender": sender,
                        "received_time": received_time
                    })
        else:
            # If inventory section not found, consider entire email as unknown/unparsable
            unknown_items.append({
                "text": body,
                "sender": sender,
                "received_time": received_time
            })
    
    return collected_items, unknown_items