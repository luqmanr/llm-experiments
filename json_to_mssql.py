import pymssql
import json
import os

SERVER = 'localhost'
PORT = 1433
USERNAME = 'sa'
PASSWORD = "passwordSEMENTARA!"
DB_NAME = 'receipt'

def _connect():
    con = pymssql.connect(
        server=SERVER,
        port=PORT,
        user=USERNAME,
        password=PASSWORD,
        database=DB_NAME,
        tds_version='7.0',
        autocommit=True
    )
    cur = con.cursor()
    return con, cur

def insert_to_receipt_idk(con, cur, data):
    statement = """
        INSERT INTO
            receipt_idk (
                total_sales,
                net_omset,
                date,
                operator,
                edc_settle,
                cash_in_hand,
                voucher,
                receipt_id
            )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    
    params = (
        data['total_sales'],
        data['net_omset'],
        data['date'],
        data['operator'],
        data['edc_seetle'],
        data['cash_in_hand'],
        data['voucher'],
        f'{data["operator"]}_{data["date"]}_{data["net_omset"]}'
    )
    try:
        cur.execute(statement, params)
        con.commit()
        print('success insert data')
        return True
    except Exception as e:
        print(f'failed to insert - error: {e}')
        return False

json_file = './results/22102025 ATP.json'
json_string = open(json_file, 'r').read().replace('```json','').replace('```', '')
print(json_string)
json_data = json.loads(json_string)
print(json_data)

con, cur = _connect()

for receipt in json_data:
    ok = insert_to_receipt_idk(con, cur, receipt)
    print(f'status insert: {ok}')
