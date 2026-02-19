import json
import csv
import re

def clean_amount(amount_str):
    """Cleans an amount string by removing non-numeric characters except for the decimal point, and handles comma as a decimal separator."""
    if isinstance(amount_str, (int, float)):
        return amount_str
    # Replace dot used as a thousand separator with nothing, and comma as a decimal separator with a dot
    cleaned_str = amount_str.replace('.', '').replace(',', '.')
    # Remove any characters that are not digits or a single decimal point
    cleaned_str = re.sub(r'[^\\d.]', '', cleaned_str)
    try:
        return float(cleaned_str)
    except ValueError:
        return None

def parse_financial_report(text_lines, page_number, block_number):
    data = {
        'receipt_type': 'FINANCIAL REPORT',
        'page_number': page_number,
        'block_number': block_number
    }
    for line in text_lines:
        if "Operator:" in line:
            data['operator'] = line.split("Operator:")[1].strip()
        elif "Date :" in line:
            data['date'] = line.split("Date :")[1].strip()
        elif "Location:" in line:
            data['location'] = line.split("Location:")[1].strip()
        elif "Kassa :" in line:
            data['kassa'] = line.split("Kassa :")[1].strip()
        elif "Total Sales" in line:
            data['total_sales'] = clean_amount(line.split("Total Sales")[1].strip())
        elif "Disc Item" in line:
            data['disc_item'] = clean_amount(line.split("Disc Item")[1].strip())
        elif "Disc Total" in line:
            data['disc_total'] = clean_amount(line.split("Disc Total")[1].strip())
        elif "Net Omset" in line:
            data['net_omset'] = clean_amount(line.split("Net Omset")[1].strip())
        elif "Tax" in line:
            data['tax'] = clean_amount(line.split("Tax")[1].strip())
        elif "Total Omset" in line and 'Net Omset' not in line: # To avoid re-matching Total Omset if already matched Net Omset
            data['total_omset'] = clean_amount(line.split("Total Omset")[1].strip())
        elif "Cash" in line and 'Cash In Hand' not in line and 'Cashier Cash' not in line and 'Total Cash Sales' not in line:
            data['cash'] = clean_amount(line.split("Cash")[1].strip())
        elif re.search(r"BCA\\s+([\\d.,]+)", line):
            match = re.search(r"BCA\\s+([\\d.,]+)", line)
            data['edc_bca'] = clean_amount(match.group(1))
        elif re.search(r"BNI\\s+([\\d.,]+)", line):
            match = re.search(r"BNI\\s+([\\d.,]+)", line)
            data['edc_bni'] = clean_amount(match.group(1))
        elif re.search(r"MANDIRI\\s+([\\d.,]+)", line):
            match = re.search(r"MANDIRI\\s+([\\d.,]+)", line)
            data['edc_mandiri'] = clean_amount(match.group(1))
        elif "EDC Seetle" in line:
            data['edc_settle'] = clean_amount(line.split("EDC Seetle")[1].strip())
        elif "TRANSFER ONLINE" in line:
            data['transfer_online'] = clean_amount(line.split("TRANSFER ONLINE")[1].strip())
        elif "Voucher" in line:
            data['voucher'] = clean_amount(line.split("Voucher")[1].strip())
        elif "Receive Amount" in line:
            data['receive_amount'] = clean_amount(line.split("Receive Amount")[1].strip())
        elif "Other Income" in line:
            data['other_income'] = clean_amount(line.split("Other Income")[1].strip())
        elif "Total Income" in line:
            data['total_income'] = clean_amount(line.split("Total Income")[1].strip())
        elif "Cash In Hand" in line:
            data['cash_in_hand'] = clean_amount(line.split("Cash In Hand")[1].strip())
        elif "Return" in line:
            data['return'] = clean_amount(line.split("Return")[1].strip())
        elif "Paid Out" in line:
            data['paid_out'] = clean_amount(line.split("Paid Out")[1].strip())
        elif "Total Outcome" in line:
            data['total_outcome'] = clean_amount(line.split("Total Outcome")[1].strip())
        elif "Total Cash Sales" in line:
            data['total_cash_sales'] = clean_amount(line.split("Total Cash Sales")[1].strip())
        elif "Cashier Cash" in line:
            data['cashier_cash'] = clean_amount(line.split("Cashier Cash")[1].strip())
        elif "Surplus" in line:
            data['surplus'] = clean_amount(line.split("Surplus")[1].strip())
    return data

def parse_settlement_report(text_lines, page_number, block_number, bank_name):
    data = {
        'receipt_type': f'SETTLEMENT REPORT ({bank_name})',
        'page_number': page_number,
        'block_number': block_number,
        'bank': bank_name
    }

    # Common fields
    for line in text_lines:
        if "TID:" in line:
            data['tid'] = line.split("TID:")[1].split(" ")[0].strip()
        elif "MID:" in line:
            data['mid'] = line.split("MID:")[1].split(" ")[0].strip()
        elif "DATE/TIME" in line:
            data['date_time'] = line.split("DATE/TIME")[1].strip()
        elif "DATE:" in line and "TIME:" in line: # For Mandiri/BNI format
            date_time_match = re.search(r"DATE:\\s*([\\d/]+)\\s*TIME:\\s*([\\d:]+)", line)
            if date_time_match:
                data['date_time'] = f"{date_time_match.group(1)} {date_time_match.group(2)}"
            else:
                date_time_match = re.search(r"DATE:\\s*([\\d/]+)\\s*SETTLEMENT TIME:\\s*([\\d:]+)", line)
                if date_time_match:
                    data['date_time'] = f"{date_time_match.group(1)} {date_time_match.group(2)}"
        elif "BATCH:" in line:
            data['batch'] = line.split("BATCH:")[1].split(" ")[0].strip()

    # Extracting transaction details
    current_section = None
    for line in text_lines:
        if "TRANSACTION SUMMARY" in line:
            current_section = "TRANSACTION SUMMARY"
            continue
        elif "TRANSACTION DETAIL" in line:
            current_section = "TRANSACTION DETAIL"
            continue
        elif "GRAND TOTAL" in line and current_section != "TRANSACTION TOTAL BY ISSUER":
            current_section = "GRAND TOTAL"
            continue
        elif "*** TRANSACTION TOTAL BY ISSUER ***" in line:
            current_section = "TRANSACTION TOTAL BY ISSUER"
            continue


        if current_section == "TRANSACTION SUMMARY" or current_section == "GRAND TOTAL" or current_section == "TRANSACTION TOTAL BY ISSUER":
            if "SALE" in line and "Rp." in line:
                match = re.search(r"SALE\\s+\\d+\\s+Rp\\.?([\\d.,]+)", line)
                if match:
                    sale_amount = clean_amount(match.group(1))
                    if "DEBIT" in line and "ISSUER" not in line: # Prioritize Debit sale if specified
                        data['debit_sale'] = sale_amount
                    elif "QRIS SWITCHING" in line:
                        data['qris_switching_sale'] = sale_amount
                    elif "QRIS DEBIT" in line:
                        data['qris_debit_sale'] = sale_amount
                    elif "SALE" in line and "GRAND TOTAL" in current_section:
                        data['grand_total_sale'] = sale_amount
                    elif "SALE" in line and "BRAND TOTAL" in current_section: # For brand total sale
                        data['brand_total_sale'] = sale_amount
                    else:
                        data['sale'] = sale_amount
            if "TOTAL" in line and "Rp." in line:
                match = re.search(r"TOTAL\\s+\\d+\\s+Rp\\.?([\\d.,]+)", line)
                if match:
                    total_amount = clean_amount(match.group(1))
                    if "GRAND TOTAL" in current_section:
                        data['grand_total_amount'] = total_amount
                    else:
                        data['total_amount'] = total_amount

            if "REFUND" in line and "Rp." in line:
                match = re.search(r"REFUND\\s+\\d+\\s+Rp\\.?([\\d.,-]+)", line)
                if match:
                    refund_amount = clean_amount(match.group(1))
                    data['refund'] = refund_amount
            elif "VOID" in line and ("-RP" in line or "-RP O" in line or "-RP Q" in line):
                 match = re.search(r"VOID\\s+\\d+\\s+-RP\\s*([\\d.,]*)\\", line)
                 if match:
                     data['void'] = clean_amount(match.group(1))

    return data


def process_receipt_blocks(json_data):
    all_receipts_data = []

    for page in json_data['pages']:
        page_number = page['page_number']
        for block in page['receipt_blocks']:
            block_number = block['block_number']
            text_lines = block['text_lines']

            receipt_type = None
            bank_name = None

            # Check for FINANCIAL REPORT
            if any("FINANCIAL REPORT" in line for line in text_lines):
                receipt_type = "FINANCIAL REPORT"
            # Check for SETTLEMENT reports with specific bank names
            elif any("SETTLEMENT" in line.upper() for line in text_lines) or any(bank in line.upper() for line in text_lines[:5] for bank in ["BCA", "MANDIRI", "BNI", "BRI"]):
                # Determine bank name from the beginning of the block (first few lines)
                upper_first_five = [line.upper() for line in text_lines[:5]]
                if any("BCA" in line for line in upper_first_five):
                    receipt_type = "SETTLEMENT_BCA"
                    bank_name = "BCA"
                elif any("MANDIRI" in line for line in upper_first_five):
                    receipt_type = "SETTLEMENT_MANDIRI"
                    bank_name = "Mandiri"
                elif any("BNI" in line for line in upper_first_five):
                    receipt_type = "SETTLEMENT_BNI"
                    bank_name = "BNI"
                elif any("BRI" in line for line in upper_first_five):
                    receipt_type = "SETTLEMENT_BRI"
                    bank_name = "BRI"
                else:
                    # Fallback when settlement keyword is present but bank not identified
                    receipt_type = "SETTLEMENT_UNKNOWN"
                    bank_name = None

            if receipt_type == "FINANCIAL REPORT":
                all_receipts_data.append(parse_financial_report(text_lines, page_number, block_number))
            elif receipt_type in ["SETTLEMENT_BCA", "SETTLEMENT_MANDIRI", "SETTLEMENT_BNI", "SETTLEMENT_BRI", "SETTLEMENT_UNKNOWN"]:
                # Pass the detected bank name (may be None for unknown) to the parser
                all_receipts_data.append(parse_settlement_report(text_lines, page_number, block_number, bank_name))
            else:
                # Fallback for unhandled types, just store raw text lines
                all_receipts_data.append({
                    'receipt_type': 'UNKNOWN',
                    'page_number': page_number,
                    'block_number': block_number,
                    'raw_text_lines': "\\n".join(text_lines)
                })
    return all_receipts_data

def write_to_csv(data, filename="receipts_output.csv"):
    if not data:
        print("No data to write to CSV.")
        return

    # Collect all possible headers
    headers = set()
    for row in data:
        headers.update(row.keys())
    
    # Define a consistent order for primary headers
    ordered_headers = [
        'receipt_type', 'page_number', 'block_number', 'bank', 'operator', 'date', 'location', 'kassa',
        'total_sales', 'disc_item', 'disc_total', 'net_omset', 'tax', 'total_omset', 'cash',
        'edc_bca', 'edc_bni', 'edc_mandiri', 'transfer_online', 'edc_settle', 'voucher',
        'receive_amount', 'other_income', 'total_income', 'cash_in_hand', 'return', 'paid_out',
        'total_outcome', 'total_cash_sales', 'cashier_cash', 'surplus',
        'tid', 'mid', 'date_time', 'batch', 'debit_sale', 'qris_switching_sale', 'qris_debit_sale',
        'grand_total_sale', 'brand_total_sale', 'sale', 'refund', 'void', 'total_amount', 'grand_total_amount',
        'raw_text_lines' # For unknown types
    ]

    # Add any new headers that aren't in the ordered_headers but were found in data
    for header in sorted(list(headers)):
        if header not in ordered_headers:
            ordered_headers.append(header)

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=ordered_headers)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print(f"Data successfully written to {filename}")

# Main execution
if __name__ == "__main__":
    json_filepath = "results/22102025 ATP.json"
    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_filepath}")
        exit()
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_filepath}. Please ensure it's valid JSON.")
        exit()

    processed_data = process_receipt_blocks(json_data)
    write_to_csv(processed_data)