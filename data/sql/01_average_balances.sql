WITH avg_balances AS (
  SELECT
    f.company_id,
    f.fiscal_year,
    f.inventory,
    LAG(f.inventory) OVER (PARTITION BY f.company_id ORDER BY f.fiscal_year) AS prior_inventory,
    f.accounts_receivable,
    LAG(f.accounts_receivable) OVER (PARTITION BY f.company_id ORDER BY f.fiscal_year) AS prior_ar,
    f.accounts_payable,
    LAG(f.accounts_payable) OVER (PARTITION BY f.company_id ORDER BY f.fiscal_year) AS prior_ap
  FROM financials f
)
SELECT *,
  (inventory + prior_inventory) / 2.0 AS avg_inventory,
  (accounts_receivable + prior_ar) / 2.0 AS avg_ar,
  (accounts_payable + prior_ap) / 2.0 AS avg_ap
FROM avg_balances
WHERE prior_inventory IS NOT NULL;

