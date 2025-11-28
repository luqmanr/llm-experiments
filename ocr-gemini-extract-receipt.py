import os
import mimetypes
import json
import io

# External Libraries (Must be installed locally)
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from pdf2image import convert_from_path

# --- 1. CONFIGURATION ---
load_dotenv()
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
PDF_FILE_NAME = '22102025 ATP.pdf'
OUTPUT_DIR = 'extracted_receipts_padded' # New output directory name
DPI_RESOLUTION = 300 

# Path to the Poppler 'bin' directory. Set to None if Poppler is in your system PATH.
# Example: POPPLER_PATH = r'C:\Program Files\poppler-23.01.0\bin'
POPPLER_PATH = None 

# PADDING CONFIGURATION
# Normalized padding applied to all four sides of the bounding box. 
# 10 units = 1% of the page dimension (width/height). 
# A value of 20 here means 2% padding on all sides.
PADDING_PERCENTAGE = 20 # Add 2% padding on each side (20 units on a 0-1000 scale)

# --- 2. JSON SCHEMA FOR LLM RESPONSE (FIXED) ---
# This schema explicitly enforces the 3D structure: Pages -> Receipts -> Coordinates.
BOUNDING_BOX_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "bboxes": types.Schema(
            type=types.Type.ARRAY,
            description="A list of pages, where each page contains a list of receipts/bounding boxes.",
            items=types.Schema( # PAGE LEVEL: An array of receipts
                type=types.Type.ARRAY,
                description="A list of normalized bounding boxes for a single page.",
                items=types.Schema( # RECEIPT LEVEL: A single bounding box (array of 4 numbers)
                    type=types.Type.ARRAY, 
                    description="The bounding box [x_min, y_min, x_max, y_max] normalized from 0 to 1000.",
                    items=types.Schema( # COORDINATE LEVEL: A single number
                        type=types.Type.NUMBER,
                        description="A single normalized coordinate value (0-1000)."
                    )
                )
            )
        )
    }
)

# --- 3. HELPER FUNCTIONS ---

def normalize_and_crop(image, normalized_coords, padding):
    """
    Applies padding to the normalized coordinates, converts them to pixel coordinates, 
    and crops the image using PIL.
    """
    if not isinstance(normalized_coords, list) or len(normalized_coords) != 4:
        raise ValueError("Coordinates must be a list of 4 elements: [x_min, y_min, x_max, y_max]")
        
    width, height = image.size
    x_min_norm, y_min_norm, x_max_norm, y_max_norm = normalized_coords

    # 1. Apply Padding (in normalized units 0-1000)
    # Ensure coordinates stay within the [0, 1000] range
    x_min_padded = max(0, x_min_norm - padding)
    y_min_padded = max(0, y_min_norm - padding)
    x_max_padded = min(1000, x_max_norm + padding)
    y_max_padded = min(1000, y_max_norm + padding)

    # 2. Convert padded normalized coordinates to actual pixel coordinates
    x_min = int(x_min_padded * width / 1000)
    y_min = int(y_min_padded * height / 1000)
    x_max = int(x_max_padded * width / 1000)
    y_max = int(y_max_padded * height / 1000)

    # Ensure the box is valid (x_max > x_min and y_max > y_min)
    if x_max <= x_min or y_max <= y_min:
        print(f"  -> WARNING: Invalid padded bounding box calculated: {[x_min, y_min, x_max, y_max]}. Skipping crop.")
        # Return a small placeholder image or raise an error instead of crashing
        return Image.new('RGB', (1, 1), color = 'red') 

    # 3. Crop the image using (x_min, y_min, x_max, y_max)
    cropped_image = image.crop((x_min, y_min, x_max, y_max))
    return cropped_image

def get_bboxes_from_gemini(pdf_path):
    """
    Uploads the PDF to the Gemini model and requests bounding box coordinates.
    """
    print("Connecting to Gemini API...")
    if not os.getenv("GEMINI_API_KEY"):
         print("FATAL ERROR: GEMINI_API_KEY is not set. Please check your .env file or environment variables.")
         return None
         
    try:
        client = genai.Client()
    except Exception as e:
        print(f"Error initializing Gemini client: {e}")
        print("Please ensure your GEMINI_API_KEY is set correctly.")
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
        ocr_prompt = """
        Analyze the uploaded PDF document. Identify every distinct financial receipt, settlement report, or financial summary block on each page. 
        For each identified block, provide its normalized bounding box coordinates [x_min, y_min, x_max, y_max], 
        where coordinates are scaled from 0 to 1000 across the page width and height. 
        Output the result as a single JSON object matching the provided schema exactly.
        """
        
        print("Sending PDF to Gemini for bounding box detection...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[pdf_part, ocr_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=BOUNDING_BOX_SCHEMA
            )
        )
        
        # Parse the JSON response
        json_text = response.text.strip()
        print("Bounding boxes successfully received from Gemini.")
        return json.loads(json_text)

    except Exception as e:
        print(f"An error occurred during Gemini API call: {e}")
        return None

def extract_and_save_receipts(pdf_path, bounds_data, output_dir, dpi, poppler_path, padding):
    """
    Renders the PDF pages using pdf2image and crops the receipts using PIL based on LLM output.
    """
    print(f"\nStarting image extraction using pdf2image (DPI={dpi}) with {padding} normalized units of padding...")

    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 1. Convert PDF pages to PIL Image objects
        images = convert_from_path(
            pdf_path, 
            dpi=dpi, 
            poppler_path=poppler_path
        )
        
        bounds_list = bounds_data.get("bboxes", [])
        print(f"Total pages rendered: {len(images)}")
        
        if len(images) != len(bounds_list):
             print(f"Warning: Rendered {len(images)} pages but received bounding boxes for {len(bounds_list)} pages. Truncating bounding boxes to match rendered pages.")

        # Limit iteration to the minimum of rendered pages and received bounding box pages
        num_pages_to_process = min(len(images), len(bounds_list))
        
        for page_index in range(num_pages_to_process):
            page_num = page_index + 1
            img = images[page_index]
            bounds_on_page = bounds_list[page_index]

            print(f"Processing Page {page_num} with {len(bounds_on_page)} potential receipts...")
                
            for receipt_index, coords in enumerate(bounds_on_page):
                
                # Validate that the coordinate entry is a list/tuple of 4 numbers
                if not isinstance(coords, list) or len(coords) != 4 or not all(isinstance(c, (int, float)) for c in coords):
                    print(f"  -> WARNING: Skipping malformed coordinates for P{page_num} Receipt {receipt_index + 1}. Expected list of 4 numbers, got: {coords}")
                    continue

                receipt_name = f"P{page_num}_Receipt_{receipt_index + 1}"
                
                # Crop the PIL Image object, applying the padding
                receipt_image = normalize_and_crop(img, coords, padding)
                output_path = os.path.join(output_dir, f"{receipt_name}.png")
                
                # Save the cropped image
                receipt_image.save(output_path)
                print(f"  -> Saved {receipt_name}.png")

    except ImportError:
        print("\nFATAL ERROR: The 'pdf2image' library is not installed. Please run 'pip install pdf2image' in your environment.")
        print("Note: You also need the Poppler library installed on your system.")
    except Exception as e:
        print(f"\nAn error occurred during PDF conversion or processing: {e}")
        if 'poppler' in str(e).lower():
             print("\nSuggestion: If you see an error related to 'poppler', ensure the Poppler binary is installed and its path is correctly set.")

    print("\nExtraction process finished.")


# --- 5. MAIN EXECUTION ---
if __name__ == "__main__":
    # 1. Get Bounding Boxes from Gemini
    # This call analyzes the PDF and returns the coordinates.
    extracted_data = get_bboxes_from_gemini(PDF_FILE_NAME)

    if extracted_data:
        # 2. Extract and Save Receipts based on Bounding Boxes
        extract_and_save_receipts(
            PDF_FILE_NAME, 
            extracted_data, 
            OUTPUT_DIR, 
            DPI_RESOLUTION, 
            POPPLER_PATH,
            PADDING_PERCENTAGE # Pass the padding value
        )
    else:
        print("Could not retrieve bounding box data. Aborting image extraction.")