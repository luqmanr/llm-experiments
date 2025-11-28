import json
import os

filename = './results/22102025 ATP.json'
json_data = json.loads(open(filename, 'r').read())

def sanitize_json(filename, json_data):
    for receipt_data in json_data:
        total_sales = receipt_data.get('total_sales', None)
        disc_item = receipt_data.get('disc_item', None)
        disc_total = receipt_data.get('disc_total', None)
        net_omset = receipt_data.get('net_omset', None)

        # check if net_omset == (total_sales - disc_item - disc_total)
        if net_omset != (total_sales - (disc_item + disc_total)):
            print(f'{net_omset} != {(total_sales - (disc_item + disc_total))}')
            print('value INCORRECT!!')
        else:
            print('value is correct!!')

    # preparation for database
    database_fields = [
        'total_sales',
        'net_omset',
        'operator',
        'date',
        'edc_seetle',
        'cash_in_hand',
        'voucher'
        ]

    for receipt_data in json_data:
        keys = receipt_data.keys()
        all_keys_found = True
        for dtf in database_fields:
            if dtf not in keys:
                all_keys_found = False
        print(all_keys_found)

        if all_keys_found is True:
            # insert to SQL database
            pass
        else:
            print(f'receipt dengan operator: {...} tanggal: {...} gagal.')
            print(f'akan dimasukkan ke tabel receipt gagal OCR')
