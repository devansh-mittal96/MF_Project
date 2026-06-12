-- Bluestock MF Capstone — 10 Analytical SQL Queries
-- Location: sql/queries.sql
-- Run: sqlite3 data/db/bluestock_mf.db < sql/queries.sql

-- 1. Top 5 fund houses by total transaction volume
SELECT fund_house, SUM(t.amount_inr) AS total_volume
FROM fact_transactions t
JOIN dim_fund f ON t.amfi_code = f.amfi_code
GROUP BY fund_house
ORDER BY total_volume DESC
LIMIT 5;

-- 2. Average NAV per month
SELECT strftime('%Y-%m', date) AS month, ROUND(AVG(nav), 4) AS avg_nav
FROM fact_nav
GROUP BY month
ORDER BY month;

-- 3. SIP year-over-year growth
SELECT
    strftime('%Y', transaction_date) AS yr,
    SUM(amount_inr) AS sip_volume
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY yr
ORDER BY yr;

-- 4. Transactions by state
SELECT state, COUNT(*) AS txn_count, SUM(amount_inr) AS total_amount
FROM fact_transactions
GROUP BY state
ORDER BY txn_count DESC;

-- 5. Transaction type distribution
SELECT transaction_type, COUNT(*) AS cnt, ROUND(AVG(amount_inr), 2) AS avg_amount
FROM fact_transactions
GROUP BY transaction_type;

-- 6. Funds with expense ratio below 1%
SELECT amfi_code, scheme_name, expense_ratio
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE expense_ratio < 1.0;

-- 7. High 1-year return funds (> 15%)
SELECT amfi_code, return_1y
FROM fact_performance
WHERE return_1y > 15.0;

-- 8. Total redemption amount
SELECT SUM(amount_inr) AS total_redemption
FROM fact_transactions
WHERE transaction_type = 'Redemption';

-- 9. Latest NAV per scheme
SELECT n.amfi_code, f.scheme_name, n.date AS latest_date, n.nav
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
JOIN (
    SELECT amfi_code, MAX(date) AS max_date
    FROM fact_nav
    GROUP BY amfi_code
) latest ON n.amfi_code = latest.amfi_code AND n.date = latest.max_date;

-- 10. Non-compliant KYC transactions
SELECT kyc_status, COUNT(*) AS volume
FROM fact_transactions
WHERE kyc_status IN ('Pending', 'Failed')
GROUP BY kyc_status;
