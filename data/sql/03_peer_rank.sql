SELECT *,
  RANK() OVER (PARTITION BY fiscal_year ORDER BY ccc ASC) AS ccc_rank
FROM ratios_view
ORDER BY fiscal_year, ccc_rank;

