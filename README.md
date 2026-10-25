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

## Database Structure

The database has two core tables:

- `companies(company_id, ticker, name, fiscal_year_end_month)`
- `financials(company_id, fiscal_year, revenue, cogs, inventory, accounts_receivable, accounts_payable)`

The source CSV contains 20 company-year records: four years for each of five companies. The first year supplies the beginning balance needed to calculate average inventory, receivables, and payables. This produces 15 final ratio observations covering FY2023A through FY2025A.

## Python Data Loader

`data/load_database.py` converts the source CSV into a reproducible SQLite database using Python's standard-library `csv`, `sqlite3`, and `pathlib` modules. It does not require pandas and does not retrieve data from SEC EDGAR; sourcing and filing metadata are already stored in `source_financials.csv`.

The loader performs a clean rebuild each time:

1. Resolves the CSV and database paths relative to the script.
2. Deletes the existing generated database, if present.
3. Connects to a new SQLite database and enables foreign-key enforcement.
4. Creates the `companies` and `financials` tables.
5. Inserts the five company records and their fiscal-year-end months.
6. Reads each CSV row with `csv.DictReader`, converts IDs and financial values to the appropriate numeric types, and inserts the row with parameterized SQL.
7. Creates `ratios_view`, a persistent SQLite view containing the average-balance and working-capital ratio logic.
8. Commits the changes and closes the connection.

The CSV retains filing-level provenance that is not needed in the calculation tables, including accession numbers, filing URLs, dates, AR treatment notes, and XBRL tags. The generated `wc_benchmark.db` is intentionally excluded from version control because the loader can recreate it from the committed CSV.

## End-to-End Workflow

1. Collect revenue, COGS, inventory, receivables, and accounts payable from each company's Form 10-K.
2. Record the financial values and filing metadata in `source_financials.csv`.
3. Normalize company fiscal years into benchmark labels while retaining the original fiscal year and period end.
4. Run `load_database.py` to create the SQLite tables and reusable `ratios_view`.
5. Run `01_average_balances.sql` to review prior-year balances and calculated averages.
6. Run `02_ratios.sql` to calculate DIO, DSO, DPO, and CCC.
7. Run `03_peer_rank.sql` to rank companies by CCC within each fiscal year.
8. Present the results in the Excel dashboard and summarize the conclusion in the executive memo.

## Calculation Methodology

The calculation flow is:

1. Average inventory, AR, and AP are calculated with the prior year's ending balance and current year's ending balance using `LAG()`.
2. DIO = average inventory / COGS * 365.
3. DSO = average AR / revenue * 365.
4. DPO = average AP / COGS * 365.
5. CCC = DIO + DSO - DPO.
6. Companies are ranked by CCC within each fiscal year, with lower CCC ranked better.

`LAG()` retrieves the previous available fiscal-year balance within each company. The arithmetic `(current balance + prior balance) / 2.0` calculates the average. `RANK()` restarts the comparison for each fiscal year and preserves ties.

`03_peer_rank.sql` depends on `ratios_view`. A CTE exists only for the statement in which it is defined, so the loader creates the view as a persistent database object that the separate ranking query can reference.

## Receivables Caveat

DSO is not a primary operating lever for this peer set. Target does not break out a material trade receivables balance, so AR is set to zero for DSO. Walmart, Costco, and TJX disclose receivables lines, and Dollar General discloses credit/debit card receivables. Those balances are included where disclosed, but they are small relative to sales and should not be read like industrial trade receivables.

## Fiscal Year Alignment Caveat

Costco's fiscal year ends in late August or early September, while Target, Walmart, TJX, and Dollar General use January/February fiscal calendars. Costco's FY2025 therefore does not cover the same calendar months as Target's FY2025. This is a comparison limitation, not a calculation error.

## Key Findings

Target ranks first by CCC in FY2023A, FY2024A, and FY2025A. Its CCC is modestly negative because DPO slightly exceeds DIO, while DSO is zero under the receivables treatment above.

Costco and Walmart are the closest peers on cash efficiency, supported by faster inventory turns. Dollar General has the highest CCC in each benchmark year because DIO remains much higher than the rest of the peer set, even though its CCC improves over time.

For FY2025A, Target reported 60.5 DIO, 0.0 DSO, 62.1 DPO, and a -1.6-day CCC. Its DPO was 13.5 days above the next-highest peer, Dollar General at 48.6 days.

## Dashboard and Memo

The Excel workbook contains four tabs:

- `Dashboard`: CCC comparison, annual ranks, ratio detail, and a short working-capital diagnosis.
- `Ratios`: the 15 company-year DIO, DSO, DPO, and CCC observations.
- `Source Financials`: the 20 source records and filing metadata.
- `Checks`: formula-driven checks for source-row count, ratio-row count, and company count.

The one-page memo summarizes the benchmark, methodology, calendar and receivables caveats, and a recommendation to improve inventory productivity while preserving supplier-payment discipline.

## Validation

The database was rebuilt from the committed CSV and the ratio and ranking queries were rerun against the regenerated database. The SQL output matched all 15 rows in `ratio_output.csv`, and Target ranked first in FY2023A, FY2024A, and FY2025A. Selected ratios were also recalculated directly from the underlying balances.

## Limitations

- Costco's August/September fiscal year is not perfectly aligned with the January/February calendars used by the other companies.
- Retail receivables disclosures differ, so DSO is a secondary measure for this peer set.
- Beginning-and-ending averages do not capture quarterly or seasonal balance movements.
- DPO uses COGS as a consistent proxy for purchases.
- The model standardizes calculations to 365 days even when a retailer reports a 52- or 53-week year.
- The analysis identifies mathematical drivers of CCC differences but does not prove the operational cause of each ratio.

## Rebuild Instructions

From the project root:

```bash
python3 data/load_database.py
sqlite3 -header -csv data/wc_benchmark.db < data/sql/02_ratios.sql > data/ratio_output.csv
sqlite3 -header -column data/wc_benchmark.db < data/sql/03_peer_rank.sql
```

The `.db` file is intentionally ignored because it can be regenerated from `data/source_financials.csv`.
