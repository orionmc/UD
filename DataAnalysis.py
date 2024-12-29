# warehouse_parser.py
import re
from collections import defaultdict
from typing import List, Dict, Any

def parse_emails(email_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Parses a list of email data dictionaries describing hardware collected from the warehouse.
    # Returns a dictionary with the name and counts of items and list of unparsable lines with sender and time stamp details
    # for manual check (usually non stadart items).

    # imput parameter email_data: A list of dictionaries, each containing:
    #   "body": str (email body)
    #   "sender": str (sender's name or email)
    #   "received_time": str (timestamp of when the email was received)
    # return: A dictionary with aggregated counts per item category and a list of unparsable lines.
    
    # Define lists for desktop, laptop, and phone models for flexibility and future tuning if needed
    DESKTOP_MODELS = ["3000", "3010"]  
    LAPTOP_MODELS = ["5340", "5330", "5531", "5540", "5666"]  
    PHONE_MODELS = ["A32", "A34", "A35", "S23"]  
    
    # DATA STRUCTURES FOR FINAL COUNTS
    
    counts = {
        'monitors': 0,                       
        'desktops': defaultdict(int),        
        'laptops': defaultdict(int),         
        'phones': defaultdict(int),          
        'bags': defaultdict(int),            
        'chargers': defaultdict(int),        
        'docks': 0,                          
        'headsets': defaultdict(int),        

        'unparsable_lines': []               
    }

    # HELPER FUNCTIONS

    def normalize_item_name(item_name: str) -> str:
        #Lowercases and removes extra punctuation to help with matching.
        return re.sub(r'[^a-z0-9\s\-]+', '', item_name.lower()).strip()

    def increment_monitors(count: int):
        #Add monitors (screens) to the total count
        counts['monitors'] += count

    def increment_desktop(model: str, count: int):
        #Increment a recognized desktop model.
        counts['desktops'][model] += count

    def increment_laptop(model: str, count: int):
        #Increment a recognized laptop model.
        counts['laptops'][model] += count

    def increment_phone(model: str, count: int):
        #Add phones by model (e.g., A32, A34, A35). If model not given or unrecognized, default to A35.
        
        if model not in PHONE_MODELS:
            model = 'A35'  # default per requirement
        counts['phones'][model] += count

    def increment_unparsable(line: str, sender: str, time: str):
        #Add entire unparsable lines with sender and time details.
        counts['unparsable_lines'].append({
            'line': line,
            'sender': sender,
            'received_time': time
        })

    def increment_bag(size_label: str, count: int):
        #Add bags. 
        counts['bags'][size_label] += count

    def increment_charger(label: str, count: int):
        #Add charger counts 
        counts['chargers'][label] += count

    def increment_dock(count: int):
        #Add docking station / dock count.
        counts['docks'] += count

    def increment_headset(label: str, count: int):
        #Add headset count 
        counts['headsets'][label] += count

        # REGEX / PARSING LOGIC
    # Patterns to capture item references:
    # Lines like "X6 24” screens"
    # Lines like "4 x monitors", "19 x Samsung A35s", etc.
    # Lines like "Laptop 5666", "PC x2 3111"

    pattern_x_leading = r'^X(\d+)\s+(.*)'           
    pattern_generic   = r'(\d+)\s*[x×]\s+([^,;\n]+)' 
    pattern_category_model = r'^(Laptop|PC)\s+(\d{4})$' 

    # Compile phone model pattern to find models not followed by 'case' or 'cases'
    phone_pattern = re.compile(r'\b(' + '|'.join(PHONE_MODELS) + r')\b(?!\s*(?:case|cases))', re.IGNORECASE)

    for email in email_data:
        body = email.get("body", "")
        sender = email.get("sender", "Unknown Sender")
        received_time = email.get("received_time", "Unknown Time")

        lines = body.split('\n')
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue  

            parsed = False  # Flag to check if the line has been parsed

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
                continue  

            # Match generic pattern "<number> x <text>"
            found_items = re.findall(pattern_generic, line_clean, re.IGNORECASE)
            if found_items:
                for (num_str, raw_item_str) in found_items:
                    count_num = int(num_str)
                    item_str_normalized = normalize_item_name(raw_item_str)

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
                            # If 4-digit model not recognized, mark as unparsable [not in the list of defined models]
                            increment_unparsable(line_clean, sender, received_time)
                            parsed = True
                        continue  

                    # Check if it's a phone (look for A32, A34, A35)
                    if 'phone' in item_str_normalized:
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
                            increment_unparsable(line_clean, sender, received_time)
                            parsed = True
                        continue
                    # Directly check for phone models without the word "phone"
                    phone_model_match = re.search(r'\b(a3[245]|s23)\b', item_str_normalized, re.IGNORECASE)
                    if phone_model_match:
                        model = phone_model_match.group(1).upper()
                        if 'case' not in item_str_normalized:
                            increment_phone(model, count_num)
                            parsed = True
                        else:
                            increment_unparsable(line_clean, sender, received_time)
                            parsed = True
                        continue
                    # Check for "monitor" or "screen"
                    if 'monitor' in item_str_normalized or 'screen' in item_str_normalized:
                        increment_monitors(count_num)
                        parsed = True
                        continue
                    # Check for "bag"
                    if 'bag' in item_str_normalized:
                        if 'small' in item_str_normalized:
                            increment_bag('small', count_num)
                            parsed = True
                        elif 'large' in item_str_normalized:
                            increment_bag('large', count_num)
                            parsed = True
                        else:
                            increment_unparsable(line_clean, sender, received_time)
                            parsed = True
                        continue 
                    # Check for chargers
                    if 'charger' in item_str_normalized:
                        increment_charger(item_str_normalized, count_num)
                        parsed = True
                        continue 
                    # Check for dock/docking station
                    if 'dock' in item_str_normalized:
                        increment_dock(count_num)
                        parsed = True
                        continue 
                    # Check for headset
                    if 'headset' in item_str_normalized:
                        increment_headset(item_str_normalized, count_num)
                        parsed = True
                        continue 
                    # If it doesn't match any known category, mark as unparsable
                    increment_unparsable(line_clean, sender, received_time)
                    parsed = True
                continue  
            # Match category and model pattern, e.g., "Laptop 5666"
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
                    increment_unparsable(line_clean, sender, received_time)
                    parsed = True
                continue 

            # If no patterns matched, attempt to extract known models within the line
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
                    line_clean = re.sub(r'\b' + re.escape(model) + r'\b', '', line_clean)

            for model in LAPTOP_MODELS:
                if re.search(r'\b' + re.escape(model) + r'\b', line_clean):
                    increment_laptop(model, 1)
                    parsed = True
                    line_clean = re.sub(r'\b' + re.escape(model) + r'\b', '', line_clean)
            # After extracting known models, if there's any remaining text, mark as unparsable
            if parsed and line_clean.strip():
                increment_unparsable(line_clean.strip(), sender, received_time)
            # If nothing was parsed, mark the entire line as unparsable
            if not parsed and line_clean:
                increment_unparsable(line_clean, sender, received_time)

    # Convert defaultdicts to regular dicts for a cleaner return object
    counts['desktops'] = dict(counts['desktops'])      
    counts['laptops'] = dict(counts['laptops'])        
    counts['phones'] = dict(counts['phones'])          
    counts['bags'] = dict(counts['bags'])              
    counts['chargers'] = dict(counts['chargers'])      
    counts['headsets'] = dict(counts['headsets'])      

    return counts