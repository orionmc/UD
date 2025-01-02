import win32com.client

SIGNATURE_TRIGGERS = [
    "Kind regards", 
    "Best regards", 
    "Sent from my", 
    "Sincerely",
    "Connor", 
    "Stuart", 
    "Nihat",
    "Nelson",
    "Ronnie",
    "Michael",
    "Darren",
    "David",
    "Alan",
    "Ben",
    "Ritesh",
    "Thabani",
]

def strip_signature(body, triggers=SIGNATURE_TRIGGERS):
    body_lower = body.lower()
    earliest_index = len(body)
    for trigger in triggers:
        trigger_index = body_lower.find(trigger.lower())
        if trigger_index != -1 and trigger_index < earliest_index:
            earliest_index = trigger_index
    return body[:earliest_index].rstrip()

def read_outlook_subfolder_stores(mailbox_display_name, subfolder_name):
    outlook_ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    target_store = None
    for store in outlook_ns.Stores:
        if store.DisplayName.lower() == mailbox_display_name.lower():
            target_store = store
            break

    if not target_store:
        raise ValueError(f"Mailbox '{mailbox_display_name}' not found in Outlook Stores.")
    
    inbox = target_store.GetDefaultFolder(6)
    try:
        subfolder = inbox.Folders[subfolder_name]
    except:
        raise ValueError(f"Subfolder '{subfolder_name}' not found under Inbox for '{mailbox_display_name}'.")

    messages = subfolder.Items
    messages.Sort("[ReceivedTime]", True)
    
    count_to_read = 10
    email_data = []
    
    for i, msg in enumerate(messages, start=1):
        try:
            raw_body = msg.Body
            body_no_sig = strip_signature(raw_body)
            sender_name = msg.SenderName
            received_time = msg.ReceivedTime
            email_data.append({
                "body": body_no_sig,
                "sender": sender_name,
                "received_time": received_time
            })
        except Exception as e:
            print("Error reading message:", e)
        if i >= count_to_read:
            break
    
    return email_data











