from google import genai
from google.genai import types
import mimetypes
from dotenv import load_dotenv
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
Extract all text from these receipts.
there are multiple receipts, so please extract all of them
output the response ONLY as JSON.
remove dots from sales numbers so that all numbers become integers.
each receipt will have these json fields.
make all fields lowercase, and replace space with underscore

There are multiple types of receipts:

Type 1. if the receipt type is financial report, extract these fields:
```
{
    "operator": string,
    "date": string,
    "tanggal": string,
    "total_sales": integer,
    "disc_item": integer,
    "disc_total": integer,
    "net_omset": integer,
    "voucher": integer,
    "cash_in_hand": integer,
    "total_omset": integer,
    "cash": integer,
    "edc_debit": {},
    "edc_seetle": integer,
    "cashier_cash": integer,
    "surplus": integer
}
```

Type 2. if the receipt type is settlement receipt, extract these fields:

```
{
"batch_id": string,
"merch_id": string,
"bank_name": string,
"datetime": string,
"debit": {
    "grand_total": integer,
    "sale": integer,
    },
"credit": {
    "grand_total": integer,
    "sale": integer,
    "issuer": string
    },
"qris": {
    "grand_total": integer,
    "sale": integer
    }
}   
```

if you don't find the fields I've requested inside the receipt,
then output the default value as `null`
remove the ```json at the start, and the ``` at the end of your response
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