import os
import mimetypes
from dotenv import load_dotenv
from google import genai
from google.genai import types

# -------------------------------------------------
# Load GEMINI API key from the .env file located in this directory
# -------------------------------------------------
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# The API key is expected under the name GEMINI_API_KEY
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

# -------------------------------------------------
# Configuration
# -------------------------------------------------
PDF_FILE_NAME = "22102025 ATP.pdf"  # The PDF you want to analyse – must be present in the same folder as this script or give an absolute path.
OUTPUT_CSV = "results/22102025_ATP.csv"
GENERATION_TEMPERATURE = 0.1  # low temperature for deterministic output

# -------------------------------------------------
# Prompt – ask Gemini to return a CSV. The header reflects the fields we are interested in.
# -------------------------------------------------
CSV_PROMPT = """
You are a deterministic data extraction bot. Read the provided PDF (attached as binary) and extract each receipt block as a row in a CSV table.

The CSV must have the following columns (in this exact order):
receipt_type,page_number,block_number,operator,date,location,kassa,total_sales,disc_item,disc_total,net_omset,tax,total_omset,cash,edc_bca,edc_bni,edc_mandiri,edc_settle,transfer_online,voucher,receive_amount,other_income,total_income,cash_in_hand,return,paid_out,total_outcome,total_cash_sales,cashier_cash,surplus,tid,mid,date_time,batch

For rows that do not contain a particular field, leave the cell empty (do not write the string "None").

**IMPORTANT**: Output ONLY the CSV text – no extra explanations, markdown fences, or surrounding JSON. The first line must be the header exactly as shown above, followed by one line per receipt block.
"""

def extract_csv_via_gemini(pdf_path: str, temperature: float) -> str:
    """Send the PDF to Gemini and request CSV output.
    Returns the raw CSV string (including the header) or an empty string on failure.
    """
    if not os.getenv("GEMINI_API_KEY"):
        print("[ERROR] GEMINI_API_KEY not set. Check your .env file.")
        return ""

    try:
        client = genai.Client()
    except Exception as e:
        print(f"[ERROR] Unable to initialise Gemini client: {e}")
        return ""

    if not os.path.exists(pdf_path):
        print(f"[ERROR] PDF not found at {pdf_path}")
        return ""

    # Load PDF bytes
    pdf_bytes = open(pdf_path, "rb").read()
    mime_type, _ = mimetypes.guess_type(pdf_path)
    pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type=mime_type)

    # Build request – we ask for plain text (CSV) output
    generation_config = types.GenerateContentConfig(
        response_mime_type="text/plain",
        temperature=temperature,
    )

    # Send request with exponential back‑off
    max_retries = 5
    base_delay = 2
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[pdf_part, CSV_PROMPT],
                config=generation_config,
            )
            # The response text should be the CSV itself
            csv_text = response.text.strip()
            # Basic sanity check – must start with the header we defined
            if csv_text.startswith("receipt_type"):
                return csv_text
            else:
                # If Gemini returned something else (e.g., JSON), just return what we got – the caller can decide.
                return csv_text
        except Exception as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                print(f"[WARN] Attempt {attempt+1} failed ({e}), retrying in {delay}s …")
                import time
                time.sleep(delay)
            else:
                print(f"[ERROR] All {max_retries} attempts failed: {e}")
                return ""

def save_csv(csv_content: str, output_path: str):
    """Write the CSV string to a file, creating parent directories if needed."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(csv_content + "\n")
    print(f"[INFO] CSV saved to {output_path}")

if __name__ == "__main__":
    # Resolve PDF path relative to this script if a relative path is used
    pdf_path = os.path.join(os.path.dirname(__file__), PDF_FILE_NAME)
    csv_result = extract_csv_via_gemini(pdf_path, GENERATION_TEMPERATURE)
    if csv_result:
        save_csv(csv_result, os.path.join(os.path.dirname(__file__), OUTPUT_CSV))
    else:
        print("[ERROR] No CSV output received from Gemini.")
