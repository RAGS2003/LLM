import streamlit as st
import pandas as pd
import os
from google import genai
from google.genai import types
from fpdf import FPDF
import tempfile
import re

def safe_filename(name):
    return re.sub(r'[^A-Za-z0-9]+', '_', name).strip('_')

def summary_to_pdf(summary_markdown, filename="summary.pdf"):
    text = summary_markdown.replace("**", "")
    lines = text.split("\n")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in lines:
        if line.strip():
            pdf.multi_cell(0, 10, line.strip())
        else:
            pdf.ln(3)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        tmp.seek(0)
        data = tmp.read()
    return data

# ---------- CONFIGURATION -----------
os.environ["GEMINI_API_KEY"] = "AIzaSyC904tuXOVbxw3FFRgNt004R7YIkAO7tBk"  # <-- your Gemini API key
CSV_FILE = "emails_data.csv"

st.set_page_config(page_title="SheBrewsDaily", page_icon="☕", layout="centered")

# ---------- CSS: Pink Funky Centered -----------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Pacifico&family=Quicksand:wght@400;600;700&display=swap" rel="stylesheet">
<style>
html, body, .stApp {
    background: #f8e7db !important;
    min-height: 100vh;
    font-family: 'Quicksand', 'Poppins', sans-serif !important;
    position: relative;
}
.headline {
    font-family: 'Pacifico', cursive;
    font-size: 2.7em;
    color: #e35284;
    font-weight: bold;
    text-align: center;
    margin-top: 1.2em;
    margin-bottom: 0.15em;
    letter-spacing: 2px;
    z-index: 2;
}
.subtitle, .section-header {
    font-family: 'Pacifico', cursive !important;
    color: #e35284 !important;
    text-align: center;
    font-size: 1.35em;
    font-weight: 600;
    margin: 0.5em 0 0.5em 0;
    letter-spacing: 1.2px;
}
.small-desc {
    font-family: 'Quicksand', sans-serif;
    color: #db3b77;
    text-align: center;
    font-size: 1.15em;
    margin-bottom: 2.1em;
    margin-top: 0.25em;
    letter-spacing: 1.5px;
}
.stButton button, .stDownloadButton button {
    background: linear-gradient(90deg, #e35284 20%, #f8b3d4 100%);
    color: #fff;
    font-size: 1.13em;
    border: none;
    border-radius: 15px;
    padding: 0.8em 2.2em;
    font-weight: 700;
    box-shadow: 0 2px 18px #e3528442;
    font-family: 'Quicksand', sans-serif !important;
    transition: 0.2s;
    display: block;
    margin: 0 auto;
}
.stButton button:hover, .stDownloadButton button:hover {
    background: #c14573;
    color: #fff;
    transform: scale(1.04);
}
.stSelectbox {
    background: transparent !important;
    text-align: center !important;
}
.stSelectbox > div {
    justify-content: center !important;
}
.stSelectbox label {
    display: none !important; /* Hide the built-in label */
}
.st-c6, .st-c7 {
    background: #f8b3d4 !important;
    border-radius: 15px !important;
}
.stSelectbox [data-baseweb="select"] > div {
    background: #f8b3d4 !important;
    border-radius: 12px !important;
    color: #db3b77 !important;
    font-weight: 600 !important;
}
.stSelectbox [data-baseweb="select"] .css-1wa3eu0-placeholder {
    color: #db3b77 !important;
    font-family: 'Quicksand', sans-serif !important;
    font-size: 1.07em !important;
    font-weight: 700 !important;
    letter-spacing: 0.7px;
}
.custom-card {
    background: #fffbe8;
    border-radius: 16px;
    box-shadow: 0 3px 14px rgba(211, 178, 108, 0.11);
    padding: 1.7em 1.5em;
    margin: 1.5em auto;
    color: #111 !important;
    font-family: 'Quicksand', sans-serif !important;
}
.summary-card {
    background: #fffbe8ee;
    border-radius: 18px;
    box-shadow: 0 3px 14px #dbbb8d24;
    padding: 2em 2em 1.2em 2em;
    margin: 2em auto;
    color: #181818 !important;
    font-family: 'Quicksand', 'Poppins', sans-serif !important;
    font-size: 1.11em;
    line-height: 2;
    max-width: 700px;
    text-align: left;
}
.summary-card strong {
    color: #e35284;
    font-weight: 700;
}
.center-block {display: flex; justify-content: center;}
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("<div class='headline'>SheBrewsDaily</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Every HR's choice</div>", unsafe_allow_html=True)
st.markdown("<div class='small-desc'>Mail Summarizer</div>", unsafe_allow_html=True)

# --- Load Data ---
df = pd.read_csv(CSV_FILE)
df['Name'] = df['From'].apply(lambda x: x.split('<')[0].strip())
df['Email'] = df['From'].apply(lambda x: x.split('<')[1].replace('>', '').strip() if '<' in x else x)
all_names = sorted(df['Name'].unique())

# --- Select Name (no label above selectbox, pink & centered) ---
st.markdown(
    '<div class="section-header">⭐ Select Applicant Name</div>',
    unsafe_allow_html=True
)
selected_name = st.selectbox(
    "",  # no label
    [""] + all_names,
    key="name_selector",
    index=0
)

mail_to_analyze = None
if selected_name:
    filtered_df = df[df['Name'] == selected_name]
    if len(filtered_df) == 0:
        st.info("No emails found for this name.")
    elif len(filtered_df) == 1:
        mail_row = filtered_df.iloc[0]
        st.markdown(f"""
            <div class='custom-card'>
                <b>From:</b> {mail_row['Name']} ({mail_row['Email']})<br>
                <b>Subject:</b> {mail_row['Subject']}<br>
                <b>Body:</b><br><pre style='font-family:inherit;font-size:1.05em;background:transparent;color:#181818;'>{mail_row['Body']}</pre>
            </div>
        """, unsafe_allow_html=True)
        mail_to_analyze = mail_row
    else:
        mail_subjects = filtered_df['Subject'].tolist()
        selected_subject = st.selectbox(
            "",  # no label for subject dropdown
            mail_subjects,
            key="subject_selector"
        )
        mail_row = filtered_df[filtered_df['Subject'] == selected_subject].iloc[0]
        st.markdown(f"""
            <div class='custom-card'>
                <b>From:</b> {mail_row['Name']} ({mail_row['Email']})<br>
                <b>Subject:</b> {mail_row['Subject']}<br>
                <b>Body:</b><br><pre style='font-family:inherit;font-size:1.05em;background:transparent;color:#181818;'>{mail_row['Body']}</pre>
            </div>
        """, unsafe_allow_html=True)
        mail_to_analyze = mail_row

# --- Analysis Section ---
st.markdown(
    '<div class="section-header">⭐ Get Instant Cover Letter Summary</div>',
    unsafe_allow_html=True
)

if mail_to_analyze is not None:
    col_center = st.columns([2, 2, 2])
    with col_center[1]:
        summary_button = st.button("✨ Summarize This Cover Letter", use_container_width=True)
    if summary_button:
        
        api_key = os.environ["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        model = "gemini-2.5-pro-exp-03-25"

        prompt_text = (
            "You are an HR assistant. Read the following job application or cover letter email. Extract the details below and present in markdown. "
            "Put EACH field heading and its content on a separate line. NEVER merge Name, Email, or Address on the same line. "
            "ONLY show the Address field if an address is actually found in the email (otherwise skip the line completely).\n\n"
            "- **Credentials:** [Highest degree or current program and institute. Skip if not found.]\n"
            "- **Name:** [Full name. Skip if not found.]\n"
            "- **Email:** [Email address. Skip if not found.]\n"
            "- [If address found, show this line: '**Address:** [address]']\n"
            "- **Work Summary:**\n"
            "    [2-3 sentences on background, experience, projects.]\n"
            "- **Key Skills:** [Relevant skills, comma-separated.]\n"
            "- **Summary:**\n"
            "    [Why this person is a strong candidate.]\n\n"
            "Never combine fields on one line. Never show a field if not present in the email. Output markdown exactly as shown, with bold headings, no extra commentary. Strictly return only markdown."
        )

        email_content = (
            f"From: {mail_to_analyze['From']}\n"
            f"Subject: {mail_to_analyze['Subject']}\n"
            f"Body:\n{mail_to_analyze['Body']}"
        )

        contents = [
            types.Content(
                role="user",
                parts=[types.Part(text=email_content)],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            response_mime_type="text/plain",
            system_instruction=[types.Part(text=prompt_text)],
        )
        result = ""
        with st.spinner("Analyzing cover letter..."):
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if hasattr(chunk, "text"):
                    result += chunk.text
                elif isinstance(chunk, str):
                    result += chunk

            # Show the summary INSIDE the card

# 1) Ensure each bold heading starts on its own line
        formatted = re.sub(
            r"\s*\*\*([A-Za-z ]+?:\*\*)",
            r"\n**\1",
            result
        ).strip()

        # 2) Convert **bold** markdown into HTML <strong>…</strong>
        html = re.sub(
            r"\*\*(.+?)\*\*",
            r"<strong>\1</strong>",
            formatted
        )

        # 3) Render line breaks as <br><br>
        html_result = html.replace("\n", "<br><br>")

        # 4) Inject into your pink card as before
        st.markdown(
            f"<div class='summary-card'>{html_result}</div>",
            unsafe_allow_html=True
        )
        
        
        # PDF download button, centered and pink with star
        col_dl = st.columns([2, 2, 2])
        with col_dl[1]:
            file_base = safe_filename(mail_to_analyze['Name'])
            file_name = f"{file_base}.pdf" if file_base else "summary.pdf"
            pdf_bytes = summary_to_pdf(result)
            st.download_button(
                label="⭐ Download Summary as PDF",
                data=pdf_bytes,
                file_name=file_name,
                mime="application/pdf",
                use_container_width=True
            )
