from google import genai
from google.genai import types
from dotenv import load_dotenv
import mimetypes
"""
python3 -m pip install google-genai

## For python 3.8, use the one below
python3 -m pip install git+https://github.com/lumeohq/generative-ai-python-3.8.git
"""
import os

# Ensure the API key is available
load_dotenv()
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
client = genai.Client()
filename = "22102025 ATP.pdf"
pdf_bytes = open(filename, "rb").read()
mime_type, encoding = mimetypes.guess_type(filename)
print(f'mime_type: {mime_type}')
pdf_part = types.Part.from_bytes(
    data=pdf_bytes,
    mime_type=mime_type
)

ocr_prompt = """
tell me how many receipts are there in each page of this PDF file.
"""
print(f'uploading...')
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=[pdf_part, ocr_prompt]
)

print(response.text)

f = open(f'./results/{filename.replace(".png", ".json").replace(".pdf", ".json")}', 'w')
f.write(response.text)
f.close()