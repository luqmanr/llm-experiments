CREATE TABLE receipt_idk (
    total_sales INTEGER,
    net_omset INTEGER,
    date TEXT,
    operator TEXT,
    edc_settle INTEGER,
    cash_in_hand INTEGER,
    voucher INTEGER,
    receipt_id VARCHAR(50),

    CONSTRAINT receipt_pk PRIMARY KEY (receipt_id)
)
-- receipt_id = (operator, date, net_omset)

CREATE TABLE receipt_table_idk (
    receipt_id VARCHAR(50), -- (by python app, is combination of `batch_id` + `merch_id`)
    batch_id TEXT,
    merch_id VARCHAR(50),
    bank_name TEXT,
    datetime TEXT,
    debit_grand_total INTEGER,
    qris_grand_total INTEGER,
    credit_grand_total INTEGER,
    has_qris BIT,
    has_credit BIT,
    has_debit BIT,
    credit_issuer TEXT,
);
