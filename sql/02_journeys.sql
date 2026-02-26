-- 02_journeys.sql
-- Purpose:
-- 1) Build a conversion-centric event sequence ("journey") per conversion.
-- 2) Create a compact "path string" per conversion to feed Markov attribution.

-- Journeys: all relevant events within 14 days before each conversion, ordered in time.
CREATE OR REPLACE VIEW v_conversion_journeys AS
WITH ev AS (
  SELECT
    e.user_id,
    e.event_ts,
    e.channel,
    e.event_type,
    e.campaign_id,
    e.message_id
  FROM message_events e
  -- Keep engagement-type events for marketing journeys
  WHERE e.event_type IN ('delivered', 'opened', 'clicked')
),
joined AS (
  SELECT
    c.conversion_id,
    c.user_id,
    c.conversion_ts,
    c.conversion_type,
    c.value,
    e.event_ts,
    e.channel,
    e.event_type,
    e.campaign_id,
    e.message_id,
    EXTRACT(EPOCH FROM (c.conversion_ts - e.event_ts)) / 3600.0 AS hours_before_conversion
  FROM conversions c
  JOIN ev e
    ON e.user_id = c.user_id
   AND e.event_ts <= c.conversion_ts
   AND e.event_ts >= c.conversion_ts - INTERVAL '14 days'
),
sequenced AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY conversion_id ORDER BY event_ts) AS step_n
  FROM joined
)
SELECT *
FROM sequenced;

-- Paths: one row per conversion with a readable ordered channel sequence.
CREATE OR REPLACE VIEW v_paths_per_conversion AS
SELECT
  conversion_id,
  user_id,
  conversion_ts,
  conversion_type,
  value,
  STRING_AGG(channel, ' > ' ORDER BY step_n) AS path
FROM v_conversion_journeys
GROUP BY 1,2,3,4,5;