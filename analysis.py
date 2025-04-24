import csv
import os

# SET YOUR GEMINI API KEY
os.environ["GEMINI_API_KEY"] = "AIzaSyC904tuXOVbxw3FFRgNt004R7YIkAO7tBk"   

from google import genai
from google.genai import types

# SETTINGS
CSV_FILE = "emails_data.csv"

def get_emails_by_name(csv_file, search_term):
    emails = []
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if search_term in row["From"].lower():
                emails.append(row)
    return emails

def main():
    search_term = input("Enter a name or email to filter: ").strip().lower()
    filtered_emails = get_emails_by_name(CSV_FILE, search_term)

    if not filtered_emails:
        print("No emails found for that name or email.")
        return

    print(f"\n{len(filtered_emails)} emails found for '{search_term}':\n")
    for i, e in enumerate(filtered_emails):
        print(f"[{i}] {e['From'][:40]} | {e['Subject'][:60]}")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Please set your GEMINI_API_KEY environment variable.")
        return

    # Use correct model name for Gemini 1.5 Flash
    model = "gemini-1.5-flash-latest"

    prompt_text = (
        "You are an HR assistant. Read the following job application or cover letter email. Extract the details below and present in markdown. "
        "Put EACH field heading and its content on a separate line. NEVER merge Name, Email, or Address on the same line. "
        "ONLY show the Address field if an address is actually found in the email (otherwise skip the line completely)."
        "\n\n"
        "Credentials: [Highest degree or current program and institute. Skip if not found.]\n"
        "Name: [Full name. Skip if not found.]\n"
        "Email: [Email address. Skip if not found.]\n"
        "[If address found, show this line: '**Address:** [address]']\n"
        "Work Summary:\n"
        "[2-3 sentences on background, experience, projects.]\n"
        "Key Skills: [Relevant skills, comma-separated.]\n"
        "Summary \n" 
        "[Why this person is a strong candidate.]\n"
        "\n"
        "Never combine fields on one line. Never show a field if not present in the email. Output markdown exactly as shown, with bold headings, no extra commentary."
        "Make the Credentials, Name, Email, Work summary, Key skills bold and as a list"
        "Strictily return in the markdown format. Do not add any extra text or explanation."
    )


    client = genai.Client(api_key=api_key)

    for i, email in enumerate(filtered_emails):
        print(f"\n\n=== Analyzing Email [{i}] ===")
        email_content = f"From: {email['From']}\nSubject: {email['Subject']}\nBody:\n{email['Body']}"

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(text=email_content),
                ],
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            response_mime_type="text/plain",
            system_instruction=[types.Part(text=prompt_text)],
        )

        print("Sending to Gemini... Please wait.\n")
        result = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            print(chunk.text, end="")
            result += chunk.text

        print("\n--- End of analysis for this email ---")

    print("\n\n✅ All analysis complete!")

if __name__ == "__main__":
    main()
