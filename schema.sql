CREATE TABLE dim_fund (
    scheme_code INTEGER PRIMARY KEY,
    scheme_name TEXT,
    fund_house TEXT,
    category TEXT,
    sub_category TEXT
);

CREATE TABLE fact_nav (
    date TEXT,
    scheme_code INTEGER,
    nav REAL,
    PRIMARY KEY (date, scheme_code),
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code)
);

CREATE TABLE fact_transactions (
    transaction_id INTEGER PRIMARY KEY,
    scheme_code INTEGER,
    transaction_type TEXT,
    amount REAL,
    transaction_date TEXT,
    kyc_status TEXT,
    state TEXT,
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code)
);

CREATE TABLE fact_performance (
    scheme_code INTEGER PRIMARY KEY,
    return_1y REAL,
    return_3y REAL,
    return_5y REAL,
    expense_ratio REAL,
    FOREIGN KEY (scheme_code) REFERENCES dim_fund(scheme_code)
);