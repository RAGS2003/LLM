# Import Required Modules
import imaplib
import email
from email.header import decode_header
import os 
import csv 

# Email Credentials
EMAIL = "ragini29203@gmail.com"
APP_PASSWORD = "oftiqbkehfhnsjih"

SAVE_FOLDER = "attachments"
CSV_FILE = "emails_data.csv"

# Utility: Decode any encoded email header
def decode_header_field(field):
    if not field:
        return ""
    decoded_parts = decode_header(field)
    result = ""
    for part, enc in decoded_parts:
        if isinstance(part, bytes):
            result += part.decode(enc or "utf-8", errors="replace")
        else:
            result += part
    return result

# Utility: Decode email part safely
def decode_part(part):
    try:
        charset = part.get_content_charset()
        return part.get_payload(decode=True).decode(charset or "utf-8", errors="replace")
    except:
        return "(Could not decode part)"

# Connect to Gmail IMAP Server
imap = imaplib.IMAP4_SSL("imap.gmail.com")
imap.login(EMAIL, APP_PASSWORD)

# Select Inbox & Fetch Emails
imap.select("inbox")
status, messages = imap.search(None, "ALL")
email_ids = messages[0].split()
print(f"📨 Total emails found: {len(email_ids)}")

# Ensure attachment folder exists
os.makedirs(SAVE_FOLDER, exist_ok=True)

# Prepare list to store email data
email_data = []

# Fetch and parse last 5 emails
for num in email_ids:
    res, msg_data = imap.fetch(num, "(RFC822)")
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])

            # Decode subject & sender
            subject = decode_header_field(msg["Subject"]).strip()
            from_ = decode_header_field(msg.get("From")).strip()

            body = ""
            attachments = []

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    # Extract plain text body
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        body = decode_part(part)
                        break  # Prefer plain text

                    # Fallback to HTML if plain text not found
                    elif content_type == "text/html" and not body:
                        body = decode_part(part)

                    # Extract attachments
                    if "attachment" in content_disposition:
                        filename = part.get_filename()
                        if filename:
                            filename = decode_header_field(filename)
                            filepath = os.path.join(SAVE_FOLDER, filename)
                            with open(filepath, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            attachments.append(filename)
            else:
                body = decode_part(msg)

            # Clean the body for CSV
            cleaned_body = body.strip().replace("\n", " ").replace("\r", " ")

            # Add to CSV data
            email_data.append({
                "From": from_,
                "Subject": subject,
                "Body": cleaned_body,
                "Attachments": ", ".join(attachments)
            })

# Write to CSV
with open(CSV_FILE, "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["From", "Subject", "Body", "Attachments"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(email_data)

print(f"\n✅ Email data written to {CSV_FILE}")
print(f"📎 Attachments saved to {SAVE_FOLDER}/")

# Logout
imap.logout()

            