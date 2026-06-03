-- 1. Top 5 funds by AUM
SELECT scheme_code, SUM(aum_amount) as total_aum FROM fact_aum GROUP BY scheme_code ORDER BY total_aum DESC LIMIT 5;

-- 2. Average NAV per month
SELECT strftime('%Y-%m', date) as month, AVG(nav) as avg_nav FROM fact_nav GROUP BY month;

-- 3. SIP Year-over-Year (YoY) Growth Calculation
SELECT 
    strftime('%Y', transaction_date) as current_year,
    SUM(amount) as current_year_sip_volume
FROM fact_transactions 
WHERE transaction_type = 'SIP'
GROUP BY current_year;

-- 4. Total Transactions sorted by State
SELECT state, COUNT(*) as total_transactions FROM fact_transactions GROUP BY state ORDER BY total_transactions DESC;

-- 5. Count of unique transaction types
SELECT transaction_type, COUNT(*) FROM fact_transactions GROUP BY transaction_type;

-- 6. Funds with expense ratio < 1%
SELECT scheme_code, expense_ratio FROM fact_performance WHERE expense_ratio < 1.0;

-- 7. High Return Funds (1 Year Return > 15%)
SELECT scheme_code, return_1y FROM fact_performance WHERE return_1y > 15.0;

-- 8. Total Redemption Amount processed
SELECT SUM(amount) as total_redemption FROM fact_transactions WHERE transaction_type = 'REDEMPTION';

-- 9. Schemes with their latest recorded NAV
SELECT scheme_code, MAX(date) as latest_date, nav FROM fact_nav GROUP BY scheme_code;

-- 10. Non-compliant KYC Transactions (Pending or Failed)
SELECT kyc_status, COUNT(*) as volume FROM fact_transactions WHERE kyc_status IN ('PENDING', 'FAILED') GROUP BY kyc_status;