# Working Capital & Cash Conversion Cycle Benchmark

This project compares Target Corporation against Walmart, Costco, TJX, and Dollar General on working capital efficiency. The analysis uses a SQLite database, three standalone SQL query files, and an Excel dashboard to calculate DIO, DSO, DPO, and Cash Conversion Cycle (CCC).

Lower CCC indicates better cash efficiency because the company recovers cash from inventory and sales before paying suppliers.

## Repository Contents

- `data/source_financials.csv`: raw 10-K financial data in USD millions, with SEC filing metadata, source URLs, and XBRL tags.
- `data/load_database.py`: rebuilds `data/wc_benchmark.db` from the CSV.
- `data/sql/01_average_balances.sql`: calculates average inventory, AR, and AP with `LAG()`.
- `data/sql/02_ratios.sql`: calculates DIO, DSO, DPO, and CCC.
- `data/sql/03_peer_rank.sql`: ranks companies by CCC with a `RANK()` window function.
- `model/WC_Benchmark_Dashboard.xlsx`: Excel benchmark dashboard.
- `model/WC_Benchmark_Memo.docx`: one-page executive memo.

## Data Sources

All peer data was pulled from SEC EDGAR Form 10-K filings. The CSV retains the source filing URL, accession number, filing date, fiscal period end date, and XBRL tag for each row.

Target FY2023 cost of sales uses the comparable, reclassified amount reported in Target's FY2024 Form 10-K. That filing moved $92 million of FY2023 expense from SG&A to cost of sales without changing operating income; the CSV therefore cites the later filing for that one value.

| Company | CIK | Source |
|---|---:|---|
| Target Corporation | 0000027419 | SEC EDGAR Form 10-K filings |
| Walmart Inc. | 0000104169 | SEC EDGAR Form 10-K filings |
| Costco Wholesale Corporation | 0000909832 | SEC EDGAR Form 10-K filings |
| TJX Companies Inc. | 0000109198 | SEC EDGAR Form 10-K filings |
| Dollar General Corporation | 0000029534 | SEC EDGAR Form 10-K filings |

Amounts are stored in USD millions. The database uses normalized benchmark labels `FY2022A` through `FY2025A` so the peer-rank query compares five companies in each benchmark year. The raw CSV also keeps each company's source fiscal year and fiscal period end date.

## Methodology

The database has two core tables:

- `companies(company_id, ticker, name, fiscal_year_end_month)`
- `financials(company_id, fiscal_year, revenue, cogs, inventory, accounts_receivable, accounts_payable)`

The calculation flow is:

1. Average inventory, AR, and AP are calculated with the prior year's ending balance and current year's ending balance using `LAG()`.
2. DIO = average inventory / COGS * 365.
3. DSO = average AR / revenue * 365.
4. DPO = average AP / COGS * 365.
5. CCC = DIO + DSO - DPO.
6. Companies are ranked by CCC within each fiscal year, with lower CCC ranked better.

## Receivables Caveat

DSO is not a primary operating lever for this peer set. Target does not break out a material trade receivables balance, so AR is set to zero for DSO. Walmart, Costco, and TJX disclose receivables lines, and Dollar General discloses credit/debit card receivables. Those balances are included where disclosed, but they are small relative to sales and should not be read like industrial trade receivables.

## Fiscal Year Alignment Caveat

Costco's fiscal year ends in late August or early September, while Target, Walmart, TJX, and Dollar General use January/February fiscal calendars. Costco's FY2025 therefore does not cover the same calendar months as Target's FY2025. This is a comparison limitation, not a calculation error.

## Key Findings

Target ranks first by CCC in FY2023A, FY2024A, and FY2025A. Its CCC is modestly negative because DPO slightly exceeds DIO, while DSO is zero under the receivables treatment above.

Costco and Walmart are the closest peers on cash efficiency, supported by faster inventory turns. Dollar General has the highest CCC in each benchmark year because DIO remains much higher than the rest of the peer set, even though its CCC improves over time.

## Rebuild Instructions

From the project root:

```bash
python3 data/load_database.py
sqlite3 -header -csv data/wc_benchmark.db < data/sql/02_ratios.sql > data/ratio_output.csv
sqlite3 -header -column data/wc_benchmark.db < data/sql/03_peer_rank.sql
```

The `.db` file is intentionally ignored because it can be regenerated from `data/source_financials.csv`.
