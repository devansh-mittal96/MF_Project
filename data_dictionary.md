### 1. dim_fund (Dimension Table)
* `scheme_code`: Unique identifier for the mutual fund scheme (Primary Key).
* `scheme_name`: Complete legal name of the fund.
* `fund_house`: Name of the Asset Management Company (AMC).

### 2. fact_nav (Fact Table)
* `date`: Calendar date of the NAV entry (Composite Primary Key).
* `scheme_code`: Foreign key mapping back to `dim_fund`.
* `nav`: Cleaned Net Asset Value for that day (Forward-filled for holidays).

### 3. fact_transactions (Fact Table)
* `transaction_id`: Unique identifier for each entry (Primary Key).
* `transaction_type`: Standardized values containing SIP, LUMPSUM, or REDEMPTION.
* `amount`: Financial value of the transaction (Validated > 0).
* `kyc_status`: Compliance enum values (VALID, PENDING, FAILED).