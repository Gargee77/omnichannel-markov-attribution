MVP Checklist

[ ] Download dataset (store in data/raw locally; do not push large files)
[ ] Create Postgres schema (sql/01_schema.sql)
[ ] Load raw data into Postgres (python/load_to_postgres.py)
[ ] Build journey tables/views (sql/02_journeys.sql)
[ ] Compute baseline attribution (sql/03_baseline_attribution.sql)
[ ] Compute Markov attribution (python/markov_attribution.py) and write results to Postgres
[ ] Build Power BI report (powerbi/omnichannel_markov.pbix)
[ ] Add screenshots to docs/
[ ] Finalize README