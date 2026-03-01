An end-to-end analytics project that reconstructs user journeys across messaging channels and compares heuristic vs Markov multi-touch attribution using PostgreSQL, Python, and Power BI.

Omnichannel Attribution: Last-Touch vs Markov 

Marketing teams rarely get a clean 'ad → click → purchase' story. Customers bounce between channels (email, SMS, push), and different attribution methods can tell very different stories about what’s working.

This project reconstructs conversion journeys and compares a simple baseline (last-touch) to a probabilistic multi-touch model (Markov attribution) to show how channel credit shifts when you account for assist value.

What this answers:
- Which channels appear to drive revenue under last-touch attribution?
- How does channel credit change under Markov (multi-touch) attribution?
- What does engagement (opens/clicks) look like by channel?

Dashboard:
Screenshots:

1. Overview: docs/Power BI Dashboard.png 
2. Attribution comparison: docs/Attribution Comparison.png

Data:
Real marketing journey data isn’t typically public, so I generated event-level data:
- message_events: delivered/opened/clicked across email/SMS/push
- conversions: purchase/signup events with revenue

The goal is not perfect realism, it’s to model the same analytics problems teams face in DTC/e-commerce acquisition: multi-touch journeys, attribution bias, and revenue credit assignment.

How it works (high level):

1. Generate data (Python)  
   Creates marketing event logs + conversions.

2) Load to Postgres (Python → Neon Postgres) 
   Data is inserted into message_events and conversions.

3) Model journeys (SQL)
   Builds a 14-day pre-conversion journey per conversion and aggregates channel paths.

4) Attribution
   - Last-touch (SQL): assigns each conversion to the last engagement touch
   - Markov (Python): builds a transition model from paths and computes removal effects

5) Visualize in Power BI
   Power BI reads curated views to display KPIs, attribution comparison, and engagement.

Repo structure:

- python/   - data generation, loading, Markov attribution
- sql/      - schema, journeys, baseline attribution, Power BI views, checks
- docs/     - screenshots 
