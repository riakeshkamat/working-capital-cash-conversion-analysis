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
FROM ratios
ORDER BY ticker, fiscal_year;

