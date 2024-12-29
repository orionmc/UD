import win32com.client

SIGNATURE_TRIGGERS = [              # A common email signature delimiter
    "Kind regards", 
    "Best regards", 
    "Sent from my", 
    "Sincerely",
    "Connor",                       # Specific names of the parties involved in hardware collection from the warehouse
    "Stuart",                       # The signature follows the name and there is no need to process the text after the sender's name
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
    # My approach: given an email body (string), find the earliest occurrence of any 'trigger' phrase
    # and return only the text before that occurrence.
    # Normalize to a common case (lower) for searching
    body_lower = body.lower()
    earliest_index = len(body)
    for trigger in triggers:
        trigger_index = body_lower.find(trigger.lower())
        if trigger_index != -1 and trigger_index < earliest_index:
            earliest_index = trigger_index
    return body[:earliest_index].rstrip()

def read_outlook_subfolder_stores(mailbox_display_name, subfolder_name):
    # Reads emails from a specific subfolder in the specified mailbox (by Store.DisplayName).
    # mailbox_display_name: The DisplayName of the Store in Outlook. Often the email address, or a friendly name.
    # subfolder_name: The subfolder under Inbox from which to read emails.
    # Get the MAPI Namespace
    outlook_ns = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    # Find the specific store by its DisplayName
    target_store = None
    for store in outlook_ns.Stores:
        # Compare case-insensitively
        if store.DisplayName.lower() == mailbox_display_name.lower():
            target_store = store
            break

    if not target_store:
        raise ValueError(f"Mailbox '{mailbox_display_name}' not found in Outlook Stores.")
    # Get the default Inbox folder 
    inbox = target_store.GetDefaultFolder(6)
    # Access the specified subfolder under the Inbox
    # If the subfolder is nested deeper, you can chain .Folders[...] calls
    try:
        subfolder = inbox.Folders[subfolder_name]
    except:
        raise ValueError(f"Subfolder '{subfolder_name}' not found under Inbox for '{mailbox_display_name}'.")

    # Get all items (emails) in that subfolder
    messages = subfolder.Items
    # Sort them by ReceivedTime descending (newest first)
    messages.Sort("[ReceivedTime]", True)
    
    count_to_read = 5 # Number of emails to read
    # The commented-out lines below are kept for debug and maintenance purposes in future.
    #print(f"--- Reading up to {count_to_read} emails from subfolder '{subfolder_name}' in mailbox '{mailbox_display_name}' ---")
    messagebodies = []
    for i, msg in enumerate(messages, start=1):
        try:
            #print(f"Email #{i}")
            #print("  From:   ", msg.SenderName)
            #print("  Received:", msg.ReceivedTime)           
            raw_body = msg.Body
            body_no_sig = strip_signature(raw_body)
            messagebodies.append(body_no_sig)

            #print("  Body (no signature):\n\n", body_no_sig)
            #print("-" * 40)
        except Exception as e:
            print("Error reading message:", e)
        if i >= count_to_read:
           break
    return messagebodies # return the list of email bodies for further processing