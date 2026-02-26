-- 03_last_touch.sql
-- Purpose:
-- Baseline model to compare against Markov.
-- Assign each conversion to the most recent engagement event (opened/clicked).

CREATE OR REPLACE VIEW v_last_touch_attribution AS
WITH last_touch AS (
  SELECT
    conversion_id,
    user_id,
    conversion_ts,
    conversion_type,
    value,
    channel,
    event_ts,
    ROW_NUMBER() OVER (PARTITION BY conversion_id ORDER BY event_ts DESC) AS rn
  FROM v_conversion_journeys
  WHERE event_type IN ('clicked', 'opened')
)
SELECT
  conversion_id,
  user_id,
  conversion_ts,
  conversion_type,
  value,
  channel AS last_touch_channel,
  event_ts AS last_touch_ts
FROM last_touch
WHERE rn = 1;

-- Summarize last-touch performance by channel (Power BI-friendly).
CREATE OR REPLACE VIEW v_last_touch_channel_summary AS
SELECT
  last_touch_channel AS channel,
  COUNT(*) AS conversions,
  SUM(COALESCE(value, 0)) AS revenue
FROM v_last_touch_attribution
GROUP BY 1
ORDER BY revenue DESC;