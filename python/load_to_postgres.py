import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def main():
    load_dotenv()  # reads .env in repo root if it's to be run from repo root
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        raise RuntimeError("DATABASE_URL not found. Put it in .env (repo root).")

    engine = create_engine(db_url)

    events_path = "data/generated/message_events.csv"
    conv_path = "data/generated/conversions.csv"

    if not os.path.exists(events_path) or not os.path.exists(conv_path):
        raise RuntimeError("Generated CSVs not found. Run python/generate_data.py first.")

    events = pd.read_csv(events_path, parse_dates=["event_ts"])
    conv = pd.read_csv(conv_path, parse_dates=["conversion_ts"])

    with engine.begin() as conn:
        # Clean load (MVP): wipe & reload
        conn.execute(text("TRUNCATE TABLE message_events RESTART IDENTITY;"))
        conn.execute(text("TRUNCATE TABLE conversions RESTART IDENTITY;"))

    # Bulk insert
    events.to_sql("message_events", engine, if_exists="append", index=False, method="multi", chunksize=5000)
    conv.to_sql("conversions", engine, if_exists="append", index=False, method="multi", chunksize=5000)

    # Verify counts
    with engine.connect() as conn:
        ev_count = conn.execute(text("SELECT COUNT(*) FROM message_events;")).scalar()
        cv_count = conn.execute(text("SELECT COUNT(*) FROM conversions;")).scalar()

    print(f"Loaded message_events: {ev_count:,}")
    print(f"Loaded conversions: {cv_count:,}")

if __name__ == "__main__":
    main()