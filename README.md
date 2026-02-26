# omnichannel-markov-attribution
An end-to-end analytics project that reconstructs user journeys across messaging channels and compares heuristic vs Markov multi-touch attribution using PostgreSQL, Python, and Power BI.

🧠 SQL & Attribution Pipeline — How the Analysis Works

This project models a real-world omnichannel marketing attribution problem, where customers interact with multiple channels (Email, SMS, Push) before converting. The goal is to understand which channels truly contribute to revenue, beyond simplistic last-touch attribution.

Below is a step-by-step explanation of the SQL pipeline used in this project.

1. Database Schema (sql/01_schema.sql)

This script defines the core tables used throughout the analysis:

message_events
Stores raw marketing interaction logs.
Each row represents a single event (delivered, opened, clicked) for a user on a specific channel.

conversions
Stores conversion events (e.g., purchase or signup).
Each row represents a completed conversion with an associated revenue value.

attribution_results
Stores attribution outputs from different models (last-touch and Markov), allowing model comparisons over time.

Indexes are created on (user_id, timestamp) columns to support efficient journey reconstruction.

2. Conversion Journeys & Paths (sql/02_journeys.sql)

This step reconstructs customer journeys leading up to a conversion.

v_conversion_journeys
For each conversion, all marketing events for the same user in the 14-day window prior to conversion are selected and ordered chronologically.

This produces a step-by-step view of how a user moved through channels before converting.

v_paths_per_conversion
Aggregates each journey into a single ordered channel path, e.g.
email > sms > push

These paths are the direct input for Markov attribution.

3. Baseline Last-Touch Attribution (sql/03_last_touch.sql)

This represents the industry-standard baseline used by many analytics teams.

v_last_touch_attribution
Assigns each conversion to the most recent engagement event (opened or clicked) before conversion.

v_last_touch_channel_summary
Aggregates conversions and revenue by channel using last-touch logic.

This baseline is later compared against Markov attribution to highlight bias and over/under-crediting.

4. Power BI–Ready Views (sql/04_powerbi_views.sql)

These views are designed specifically for clean and stable dashboarding:

v_kpi_topline
Provides executive-level KPIs (users touched, events, conversions, revenue).

v_channel_event_summary
Summarizes channel engagement (events, opens, clicks, click-through rate).

v_attribution_latest
Exposes the most recent attribution results per channel and model, enabling direct comparison between last-touch and Markov attribution.

5. Data Quality & Sanity Checks (sql/05_checks.sql)

This file contains validation queries used throughout the project to ensure correctness:

Row count checks after data ingestion

Verification that journeys and paths are non-empty

Confirmation that attribution results exist for all channels and models

These checks reflect real-world “data detective” practices used to validate analytical pipelines.

6. Markov Attribution (Python)

The Markov attribution model is implemented in Python (python/markov_attribution.py) and works as follows:

Reads conversion paths from v_paths_per_conversion

Builds a first-order Markov transition matrix

Computes removal effects by simulating the removal of each channel

Allocates revenue proportionally based on each channel’s impact on conversion probability

Writes results back into attribution_results

This allows a direct comparison between heuristic (last-touch) and probabilistic (Markov) attribution models.

🔑 Key Insight

This pipeline demonstrates how different attribution models can produce materially different conclusions about channel performance, highlighting why multi-touch attribution is critical for informed marketing and financial decision-making.