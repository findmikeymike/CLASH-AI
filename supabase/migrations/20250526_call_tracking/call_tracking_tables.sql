-- Create tables for call tracking and usage calculation
-- Following nuclear logging principles with detailed tracking and rollback capability

-- Create operation_logs table for comprehensive logging
CREATE TABLE IF NOT EXISTS operation_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  operation_type TEXT NOT NULL,
  details JSONB,
  status TEXT NOT NULL,
  error JSONB,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Log the start of migration
INSERT INTO operation_logs (operation_type, details, status)
VALUES ('DB_MIGRATION', '{"migration": "call_tracking_tables", "action": "start"}', 'STARTED');

-- Create user_minutes table if it doesn't exist
CREATE TABLE IF NOT EXISTS user_minutes (
  user_id TEXT PRIMARY KEY,
  remaining_minutes INTEGER NOT NULL DEFAULT 0,
  total_minutes_purchased INTEGER NOT NULL DEFAULT 0,
  total_minutes_used INTEGER NOT NULL DEFAULT 0,
  last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create call_sessions table
CREATE TABLE IF NOT EXISTS call_sessions (
  id UUID PRIMARY KEY,
  user_id TEXT NOT NULL,
  character_id TEXT NOT NULL,
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ,
  duration_seconds INTEGER,
  minutes_used INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS call_sessions_user_id_idx ON call_sessions(user_id);
CREATE INDEX IF NOT EXISTS call_sessions_character_id_idx ON call_sessions(character_id);

-- Create RLS policies for user_minutes table
ALTER TABLE user_minutes ENABLE ROW LEVEL SECURITY;

-- Policy for users to read only their own minutes
DROP POLICY IF EXISTS user_minutes_select_policy ON user_minutes;
CREATE POLICY user_minutes_select_policy ON user_minutes
  FOR SELECT USING (auth.uid() = user_id);

-- Policy for users to update only their own minutes (service role will bypass this)
DROP POLICY IF EXISTS user_minutes_update_policy ON user_minutes;
CREATE POLICY user_minutes_update_policy ON user_minutes
  FOR UPDATE USING (auth.uid() = user_id);

-- Create RLS policies for call_sessions table
ALTER TABLE call_sessions ENABLE ROW LEVEL SECURITY;

-- Policy for users to read only their own call sessions
DROP POLICY IF EXISTS call_sessions_select_policy ON call_sessions;
CREATE POLICY call_sessions_select_policy ON call_sessions
  FOR SELECT USING (auth.uid() = user_id);

-- Policy for users to insert only their own call sessions
DROP POLICY IF EXISTS call_sessions_insert_policy ON call_sessions;
CREATE POLICY call_sessions_insert_policy ON call_sessions
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy for users to update only their own call sessions
DROP POLICY IF EXISTS call_sessions_update_policy ON call_sessions;
CREATE POLICY call_sessions_update_policy ON call_sessions
  FOR UPDATE USING (auth.uid() = user_id);

-- Log the completion of migration
INSERT INTO operation_logs (operation_type, details, status)
VALUES ('DB_MIGRATION', '{"migration": "call_tracking_tables", "action": "complete"}', 'SUCCESS');
