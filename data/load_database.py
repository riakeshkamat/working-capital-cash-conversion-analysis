import csv
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "source_financials.csv"
DB_PATH = BASE_DIR / "wc_benchmark.db"

COMPANIES = [
    (1, "TGT", "Target Corporation", 1),
    (2, "WMT", "Walmart Inc.", 1),
    (3, "COST", "Costco Wholesale Corporation", 8),
    (4, "TJX", "TJX Companies Inc.", 1),
    (5, "DG", "Dollar General Corporation", 1),
]


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE companies (
          company_id INTEGER PRIMARY KEY,
          ticker TEXT,
          name TEXT,
          fiscal_year_end_month INTEGER
        );

        CREATE TABLE financials (
          company_id INTEGER,
          fiscal_year TEXT,
          revenue REAL,
          cogs REAL,
          inventory REAL,
          accounts_receivable REAL,
          accounts_payable REAL,
          FOREIGN KEY (company_id) REFERENCES companies(company_id)
        );
        """
    )
    cur.executemany(
        "INSERT INTO companies (company_id, ticker, name, fiscal_year_end_month) VALUES (?, ?, ?, ?)",
        COMPANIES,
    )

    with CSV_PATH.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            cur.execute(
                """
                INSERT INTO financials (
                  company_id, fiscal_year, revenue, cogs, inventory,
                  accounts_receivable, accounts_payable
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(row["company_id"]),
                    row["benchmark_fiscal_year"],
                    float(row["revenue"]),
                    float(row["cogs"]),
                    float(row["inventory"]),
                    float(row["accounts_receivable"]),
                    float(row["accounts_payable"]),
                ),
            )

    cur.executescript(
        """
        CREATE VIEW ratios_view AS
        WITH avg_balances AS (
          SELECT
            f.company_id,
            f.fiscal_year,
            f.inventory,
            LAG(f.inventory) OVER (PARTITION BY f.company_id ORDER BY f.fiscal_year) AS prior_inventory,
            f.accounts_receivable,
            LAG(f.accounts_receivable) OVER (PARTITION BY f.company_id ORDER BY f.fiscal_year) AS prior_ar,
            f.accounts_payable,
            LAG(f.accounts_payable) OVER (PARTITION BY f.company_id ORDER BY f.fiscal_year) AS prior_ap,
            (f.inventory + LAG(f.inventory) OVER (PARTITION BY f.company_id ORDER BY f.fiscal_year)) / 2.0 AS avg_inventory,
            (f.accounts_receivable + LAG(f.accounts_receivable) OVER (PARTITION BY f.company_id ORDER BY f.fiscal_year)) / 2.0 AS avg_ar,
            (f.accounts_payable + LAG(f.accounts_payable) OVER (PARTITION BY f.company_id ORDER BY f.fiscal_year)) / 2.0 AS avg_ap
          FROM financials f
        ),
        ratios AS (
          SELECT
            c.ticker,
            c.name,
            ab.fiscal_year,
            ROUND(ab.avg_inventory / f.cogs * 365, 1) AS dio,
            ROUND(ab.avg_ar / f.revenue * 365, 1) AS dso,
            ROUND(ab.avg_ap / f.cogs * 365, 1) AS dpo
          FROM avg_balances ab
          JOIN financials f ON f.company_id = ab.company_id AND f.fiscal_year = ab.fiscal_year
          JOIN companies c ON c.company_id = ab.company_id
          WHERE ab.prior_inventory IS NOT NULL
        )
        SELECT *, ROUND(dio + dso - dpo, 1) AS ccc
        FROM ratios;
        """
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()

