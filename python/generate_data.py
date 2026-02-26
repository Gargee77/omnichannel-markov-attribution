import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def generate_data(
    n_users: int = 2000,
    start_date: str = "2025-01-01",
    days: int = 60,
    seed: int = 42,
    out_dir: str = "data/generated"
):
    rng = np.random.default_rng(seed)
    start = datetime.fromisoformat(start_date)
    end = start + timedelta(days=days)

    os.makedirs(out_dir, exist_ok=True)

    users = [f"user_{i:06d}" for i in range(1, n_users + 1)]
    channels = np.array(["email", "sms", "push"])
    channel_probs = np.array([0.55, 0.25, 0.20])

    touches_per_user = rng.integers(3, 26, size=n_users)

    rows = []

    for i, (u, k) in enumerate(zip(users, touches_per_user), start=1):

        # progress indicator (so it never feels stuck)
        if i % 500 == 0:
            print(f"Generated users: {i}/{n_users}")

        ts_offsets = rng.random(k)
        ts_list = [start + (end - start) * float(x) for x in ts_offsets]
        ts_list.sort()

        for t in ts_list:
            ch = rng.choice(channels, p=channel_probs)

            if ch == "email":
                event_type = rng.choice(
                    ["delivered", "opened", "clicked", "unsubscribed"],
                    p=[0.55, 0.30, 0.13, 0.02]
                )
            elif ch == "sms":
                event_type = rng.choice(
                    ["delivered", "clicked", "unsubscribed"],
                    p=[0.78, 0.20, 0.02]
                )
            else:
                event_type = rng.choice(
                    ["delivered", "opened", "clicked"],
                    p=[0.70, 0.22, 0.08]
                )

            campaign_id = f"camp_{rng.integers(1, 151):03d}"
            message_id = f"msg_{rng.integers(1, 2_000_000):07d}"

            rows.append([
                u,
                t,
                ch,
                event_type,
                campaign_id,
                message_id
            ])

    events = pd.DataFrame(
        rows,
        columns=[
            "user_id",
            "event_ts",
            "channel",
            "event_type",
            "campaign_id",
            "message_id"
        ]
    )

    # --- conversions ---
    events_sorted = events.sort_values(["user_id", "event_ts"])
    events_sorted["is_click"] = (events_sorted["event_type"] == "clicked").astype(int)

    conversions = []

    for u in users:
        u_ev = events_sorted[events_sorted["user_id"] == u]
        if u_ev.empty:
            continue

        clicks = u_ev["is_click"].sum()
        base_p = 0.03
        p = min(0.35, base_p + 0.01 * clicks)

        if rng.random() < p:
            last_ts = u_ev["event_ts"].max()
            conv_ts = last_ts + timedelta(days=float(rng.random() * 5))
            conv_type = rng.choice(["purchase", "signup"], p=[0.75, 0.25])
            value = float(max(5.0, np.round(rng.normal(80, 35), 2)))

            conversions.append([u, conv_ts, conv_type, value])

    conv_df = pd.DataFrame(
        conversions,
        columns=["user_id", "conversion_ts", "conversion_type", "value"]
    )

    events_path = os.path.join(out_dir, "message_events.csv")
    conv_path = os.path.join(out_dir, "conversions.csv")

    events.to_csv(events_path, index=False)
    conv_df.to_csv(conv_path, index=False)

    print(f"\nSaved: {events_path} ({len(events):,} rows)")
    print(f"Saved: {conv_path} ({len(conv_df):,} rows)")


if __name__ == "__main__":
    generate_data()