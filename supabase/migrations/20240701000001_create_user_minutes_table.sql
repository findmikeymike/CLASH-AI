-- Create user_minutes table to store remaining minutes
CREATE TABLE IF NOT EXISTS user_minutes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id TEXT NOT NULL,
  remaining_minutes INTEGER NOT NULL DEFAULT 0,
  last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id)
);

-- Enable row level security
ALTER TABLE user_minutes ENABLE ROW LEVEL SECURITY;

-- Create policies for access control
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'user_minutes' AND policyname = 'Users can view their own minutes') THEN
    DROP POLICY "Users can view their own minutes" ON user_minutes;
  END IF;
END $$;

CREATE POLICY "Users can view their own minutes"
ON user_minutes FOR SELECT
USING (auth.uid()::text = user_id);

DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'user_minutes' AND policyname = 'Users can update their own minutes') THEN
    DROP POLICY "Users can update their own minutes" ON user_minutes;
  END IF;
END $$;

CREATE POLICY "Users can update their own minutes"
ON user_minutes FOR UPDATE
USING (auth.uid()::text = user_id);

-- Enable realtime
alter publication supabase_realtime add table user_minutes;