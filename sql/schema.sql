-- Bluestock MF Capstone — Star Schema DDL
-- Location: sql/schema.sql

CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code       INTEGER PRIMARY KEY,
    scheme_code     INTEGER,
    scheme_name     TEXT NOT NULL,
    fund_house      TEXT,
    category        TEXT,
    sub_category    TEXT,
    risk_grade      TEXT,
    expense_ratio_pct REAL
);

CREATE TABLE IF NOT EXISTS dim_date (
    date        TEXT PRIMARY KEY,
    year        INTEGER,
    month       INTEGER,
    day         INTEGER,
    quarter     INTEGER,
    is_weekday  INTEGER
);

CREATE TABLE IF NOT EXISTS fact_nav (
    date            TEXT NOT NULL,
    amfi_code       INTEGER NOT NULL,
    scheme_code     INTEGER,
    nav             REAL NOT NULL,
    daily_return    REAL,
    PRIMARY KEY (date, amfi_code),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id      INTEGER PRIMARY KEY,
    investor_id         TEXT,
    transaction_date    TEXT,
    amfi_code           INTEGER,
    transaction_type    TEXT,
    amount_inr          REAL,
    state               TEXT,
    city                TEXT,
    city_tier           TEXT,
    age_group           TEXT,
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,
    kyc_status          TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code       INTEGER PRIMARY KEY,
    return_1y       REAL,
    return_3y       REAL,
    return_5y       REAL,
    sharpe_ratio    REAL,
    expense_ratio   REAL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_aum (
    fund_house      TEXT,
    quarter         TEXT,
    aum_crore       REAL,
    num_schemes     INTEGER
);

CREATE TABLE IF NOT EXISTS fact_sip_industry (
    month                   TEXT PRIMARY KEY,
    sip_inflow_crore        REAL,
    active_sip_accounts_crore REAL,
    new_sip_accounts_lakh   REAL
);

CREATE INDEX IF NOT EXISTS idx_fact_nav_date ON fact_nav(date);
CREATE INDEX IF NOT EXISTS idx_fact_nav_amfi ON fact_nav(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_tx_date ON fact_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_fact_tx_state ON fact_transactions(state);
