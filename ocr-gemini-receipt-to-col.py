import os
import mimetypes
import json
import time

# External Libraries (Must be installed locally)
from dotenv import load_dotenv
from google import genai
from google.genai import types
# import json # Already imported above

# --- 1. CONFIGURATION ---
load_dotenv()
# Set API Key from environment variable
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

PDF_FILE_NAME = '22102025 ATP.pdf'

# GENERATION CONFIGURATION FOR LLM
# A low temperature (0.1) is used for deterministic, structured output.
GENERATION_TEMPERATURE = 0.1

# --- 2. JSON SCHEMA FOR LLM RESPONSE ---
# This schema defines the structure for extracting text into pages, blocks (columns), and lines (rows).
RECEIPT_TEXT_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "pages": types.Schema(
            type=types.Type.ARRAY,
            description="A list of pages from the PDF.",
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "page_number": types.Schema(
                        type=types.Type.INTEGER, 
                        description="The 1-based index of the page."
                    ),
                    "receipt_blocks": types.Schema(
                        type=types.Type.ARRAY,
                        description="A list of distinct receipt or report blocks identified on this page (columns).",
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "block_number": types.Schema(
                                    type=types.Type.INTEGER, 
                                    description="A sequential index for the block on the page."
                                ),
                                "text_lines": types.Schema(
                                    type=types.Type.ARRAY,
                                    description="The lines of text within this block, preserved in order (rows).",
                                    items=types.Schema(type=types.Type.STRING)
                                )
                            },
                            required=["block_number", "text_lines"]
                        )
                    )
                },
                required=["page_number", "receipt_blocks"]
            )
        )
    },
    required=["pages"]
)

# --- 3. MAIN FUNCTION ---

def extract_structured_text_from_gemini(pdf_path, temperature):
    """
    Uploads the PDF to the Gemini model and requests structured text extraction.
    """
    print("Connecting to Gemini API...")
    if not os.getenv("GEMINI_API_KEY"):
         print("FATAL ERROR: GEMINI_API_KEY is not set. Please check your .env file or environment variables.")
         return None
         
    try:
        # Initialize client with a simple retry mechanism
        client = genai.Client()
    except Exception as e:
        print(f"Error initializing Gemini client: {e}")
        return None

    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return None

    try:
        # Load PDF bytes
        pdf_bytes = open(pdf_path, "rb").read()
        mime_type, _ = mimetypes.guess_type(pdf_path)
        
        # Create Part from bytes
        pdf_part = types.Part.from_bytes(
            data=pdf_bytes,
            mime_type=mime_type
        )

        # Define the prompt for structured extraction
        ocr_prompt = f"""
        You are a highly deterministic document analysis bot. Your sole output must be a JSON object conforming exactly to the provided schema.

        **Task Instructions for Text Extraction:**
        1. **Page Iteration:** Process the entire PDF page by page.
        2. **Block Identification (Columns):** On each page, identify distinct, non-overlapping vertical report or receipt blocks. Treat these blocks as separate columns.
        3. **Line Extraction (Rows):** For each block identified, extract all lines of text. Preserve the original order of the lines.
        4. **Strict Output:** Provide the extracted text data in the JSON structure below. **Do not include any introductory text, reasoning, or additional comments outside of the final JSON.**
        """
        
        print("Sending PDF to Gemini for structured text extraction...")

        # Implement exponential backoff for API robustness
        max_retries = 5
        base_delay = 2 # seconds
        
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[pdf_part, ocr_prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=RECEIPT_TEXT_SCHEMA,
                        temperature=temperature 
                    )
                )
                
                # Parse the JSON response
                json_text = response.text.strip()
                print("Structured text successfully received from Gemini.")
                return json.loads(json_text)

            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(f"Attempt {attempt + 1} failed with error: {e}. Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print(f"Failed to get response after {max_retries} attempts.")
                    print(f"Last error: {e}")
                    return None

    except Exception as e:
        print(f"An unexpected error occurred during API call preparation: {e}")
        return None


# --- 4. MAIN EXECUTION ---
if __name__ == "__main__":
    # 1. Get Structured Text from Gemini
    extracted_data = extract_structured_text_from_gemini(PDF_FILE_NAME, GENERATION_TEMPERATURE)

    if extracted_data:
        # 2. Print the final structured JSON output beautifully
        print("\n" + "="*50)
        print("FINAL STRUCTURED TEXT OUTPUT")
        print("="*50)
        print(json.dumps(extracted_data, indent=2))
        print("="*50)
        f = open(f'./results/{PDF_FILE_NAME.replace(".png", ".json").replace(".pdf", ".json")}', 'w')
        f.write(json.dumps(extracted_data, indent=2))
        f.close()
    else:
        print("\nCould not retrieve structured text data. Aborting execution.")