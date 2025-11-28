import os
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = '/home/luqmanr/bin/tesseract'

def ocr_pdf_page_by_page_pdf2image(pdf_path, poppler_path=None):
    if not os.path.exists(pdf_path):
        return f"Error: PDF file not found at '{pdf_path}'"

    full_text = []

    try:
        images = convert_from_path(
            pdf_path, 
            dpi=300, 
            poppler_path=poppler_path
        )
        
        print(f"Total pages to process: {len(images)}")

        for page_number, img in enumerate(images):
            print(f"Processing Page {page_number + 1}...")

            page_text = pytesseract.image_to_string(img)
            
            full_text.append(f"\n--- PAGE {page_number + 1} START ---\n")
            full_text.append(page_text)
            full_text.append(f"\n--- PAGE {page_number + 1} END ---\n")

        return "".join(full_text)

    except pytesseract.TesseractNotFoundError:
        return "Error: Tesseract is not found. Check the path set in 'pytesseract.pytesseract.tesseract_cmd'."
    except Exception as e:
        return f"An unexpected error occurred during PDF processing (Check Poppler installation): {e}"

def extract_text_from_image(image_path):
    if not os.path.exists(image_path):
        return f"Error: Image file not found at '{image_path}'"

    try:
        img = Image.open(image_path)
        # Note: AppImages often include the necessarequires it.
        text = pytesseract.image_to_string(img)
        return text

    except pytesseract.TesseractNotFoundError:
        return "Error: Tesseract is not installed or the specified path is incorrect."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

    except pytesseract.TesseractNotFoundError:
        return "Error: Tesseract is not found. Check the path set in 'pytesseract.pytesseract.tesseract_cmd'."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

if __name__ == "__main__":
    image_file = '22102025 ATP.png' 
    print(f"--- Starting OCR for image: {image_file} ---")
    extracted_text = extract_text_from_image(image_file)
    
    # pdf_file = 'sample_document.pdf' 
    # extracted_text = ocr_pdf_page_by_page_pdf2image(pdf_file)
    # print(f"--- Starting OCR for PDF: {pdf_file} ---")

    print("\n--- Extracted Text ---")
    print(extracted_text)
    print("----------------------")
