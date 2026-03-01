-- Database Foundation (Tables and Indexes)
-- Purpose: Create core tables to store marketing events, conversions, and attribution outputs.

CREATE TABLE IF NOT EXISTS message_events (
  event_id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  event_ts TIMESTAMP NOT NULL,
  channel TEXT NOT NULL,         -- (email/sms/push)
  event_type TEXT NOT NULL,      -- (delivered/opened/clicked/unsubscribed)
  campaign_id TEXT,
  message_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_message_events_user_ts
  ON message_events (user_id, event_ts);

CREATE TABLE IF NOT EXISTS conversions (
  conversion_id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  conversion_ts TIMESTAMP NOT NULL,
  conversion_type TEXT,        -- (purchase/signup)
  value NUMERIC                -- revenue
);

CREATE INDEX IF NOT EXISTS idx_conversions_user_ts
  ON conversions (user_id, conversion_ts);

-- Stores model outputs (last_touch and markov runs)
CREATE TABLE IF NOT EXISTS attribution_results (
  run_id TEXT NOT NULL,
  model_name TEXT NOT NULL,         -- (last_touch/markov)
  channel TEXT NOT NULL,            -- email/sms/push
  contribution NUMERIC NOT NULL,    -- revenue contribution (or credit)
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (run_id, model_name, channel)
);