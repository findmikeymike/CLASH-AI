-- Complete Payment and Usage Tracking System Migration
-- Following nuclear logging principles with detailed tracking and rollback capability

-- Create a function to log migration steps
CREATE OR REPLACE FUNCTION log_migration_step(step_name TEXT, status TEXT, details JSONB DEFAULT NULL)
RETURNS VOID AS $$
BEGIN
  INSERT INTO public.migration_logs (migration_name, step_name, status, details)
  VALUES ('complete_payment_system', step_name, status, details);
EXCEPTION WHEN OTHERS THEN
  -- If the migration_logs table doesn't exist yet, we'll create it first
  IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'migration_logs') THEN
    CREATE TABLE public.migration_logs (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      migration_name TEXT NOT NULL,
      step_name TEXT NOT NULL,
      status TEXT NOT NULL,
      details JSONB,
      created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    
    INSERT INTO public.migration_logs (migration_name, step_name, status, details)
    VALUES ('complete_payment_system', step_name, status, details);
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Log the start of migration
SELECT log_migration_step('migration_start', 'STARTED');

-- Create operation_logs table for comprehensive logging
SELECT log_migration_step('create_operation_logs', 'STARTED');

CREATE TABLE IF NOT EXISTS public.operation_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  operation_type TEXT NOT NULL,
  details JSONB,
  status TEXT NOT NULL,
  error JSONB,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT log_migration_step('create_operation_logs', 'COMPLETED');

-- Create user_minutes table if it doesn't exist
SELECT log_migration_step('create_user_minutes', 'STARTED');

CREATE TABLE IF NOT EXISTS public.user_minutes (
  user_id TEXT PRIMARY KEY,
  remaining_minutes INTEGER NOT NULL DEFAULT 0,
  total_minutes_purchased INTEGER NOT NULL DEFAULT 0,
  total_minutes_used INTEGER NOT NULL DEFAULT 0,
  last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT log_migration_step('create_user_minutes', 'COMPLETED');

-- Create call_sessions table
SELECT log_migration_step('create_call_sessions', 'STARTED');

CREATE TABLE IF NOT EXISTS public.call_sessions (
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
CREATE INDEX IF NOT EXISTS call_sessions_user_id_idx ON public.call_sessions(user_id);
CREATE INDEX IF NOT EXISTS call_sessions_character_id_idx ON public.call_sessions(character_id);

SELECT log_migration_step('create_call_sessions', 'COMPLETED');

-- Create payments table to track Stripe payments
SELECT log_migration_step('create_payments', 'STARTED');

CREATE TABLE IF NOT EXISTS public.payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  stripe_session_id TEXT,
  stripe_payment_intent_id TEXT,
  amount INTEGER NOT NULL, -- in cents
  minutes_purchased INTEGER NOT NULL,
  status TEXT NOT NULL, -- 'pending', 'completed', 'failed'
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS payments_user_id_idx ON public.payments(user_id);
CREATE INDEX IF NOT EXISTS payments_stripe_session_id_idx ON public.payments(stripe_session_id);

SELECT log_migration_step('create_payments', 'COMPLETED');

-- Create RLS policies for user_minutes table
SELECT log_migration_step('create_rls_policies_user_minutes', 'STARTED');

ALTER TABLE public.user_minutes ENABLE ROW LEVEL SECURITY;

-- Policy for users to read only their own minutes
DROP POLICY IF EXISTS user_minutes_select_policy ON public.user_minutes;
CREATE POLICY user_minutes_select_policy ON public.user_minutes
  FOR SELECT USING (auth.uid() = user_id);

-- Policy for users to update only their own minutes (service role will bypass this)
DROP POLICY IF EXISTS user_minutes_update_policy ON public.user_minutes;
CREATE POLICY user_minutes_update_policy ON public.user_minutes
  FOR UPDATE USING (auth.uid() = user_id);

SELECT log_migration_step('create_rls_policies_user_minutes', 'COMPLETED');

-- Create RLS policies for call_sessions table
SELECT log_migration_step('create_rls_policies_call_sessions', 'STARTED');

ALTER TABLE public.call_sessions ENABLE ROW LEVEL SECURITY;

-- Policy for users to read only their own call sessions
DROP POLICY IF EXISTS call_sessions_select_policy ON public.call_sessions;
CREATE POLICY call_sessions_select_policy ON public.call_sessions
  FOR SELECT USING (auth.uid() = user_id);

-- Policy for users to insert only their own call sessions
DROP POLICY IF EXISTS call_sessions_insert_policy ON public.call_sessions;
CREATE POLICY call_sessions_insert_policy ON public.call_sessions
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy for users to update only their own call sessions
DROP POLICY IF EXISTS call_sessions_update_policy ON public.call_sessions;
CREATE POLICY call_sessions_update_policy ON public.call_sessions
  FOR UPDATE USING (auth.uid() = user_id);

SELECT log_migration_step('create_rls_policies_call_sessions', 'COMPLETED');

-- Create RLS policies for payments table
SELECT log_migration_step('create_rls_policies_payments', 'STARTED');

ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;

-- Policy for users to read only their own payments
DROP POLICY IF EXISTS payments_select_policy ON public.payments;
CREATE POLICY payments_select_policy ON public.payments
  FOR SELECT USING (auth.uid() = user_id);

-- Policy for users to insert only their own payments
DROP POLICY IF EXISTS payments_insert_policy ON public.payments;
CREATE POLICY payments_insert_policy ON public.payments
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy for users to update only their own payments
DROP POLICY IF EXISTS payments_update_policy ON public.payments;
CREATE POLICY payments_update_policy ON public.payments
  FOR UPDATE USING (auth.uid() = user_id);

SELECT log_migration_step('create_rls_policies_payments', 'COMPLETED');

-- Create functions for managing minutes

-- Function to get user's remaining minutes
SELECT log_migration_step('create_function_get_user_minutes', 'STARTED');

CREATE OR REPLACE FUNCTION get_user_minutes(p_user_id TEXT)
RETURNS TABLE (remaining_minutes INTEGER) SECURITY DEFINER AS $$
BEGIN
  -- Log operation start
  INSERT INTO public.operation_logs (operation_type, details, status)
  VALUES ('GET_USER_MINUTES', jsonb_build_object('user_id', p_user_id), 'STARTED');

  -- Return remaining minutes or 0 if no record exists
  RETURN QUERY
  SELECT COALESCE(um.remaining_minutes, 0)
  FROM public.user_minutes um
  WHERE um.user_id = p_user_id;

  -- If no rows returned, return 0
  IF NOT FOUND THEN
    RETURN QUERY SELECT 0;
  END IF;

  -- Log operation completion
  INSERT INTO public.operation_logs (operation_type, details, status)
  VALUES ('GET_USER_MINUTES', jsonb_build_object('user_id', p_user_id), 'COMPLETED');
EXCEPTION WHEN OTHERS THEN
  -- Log error
  INSERT INTO public.operation_logs (operation_type, details, status, error)
  VALUES (
    'GET_USER_MINUTES',
    jsonb_build_object('user_id', p_user_id),
    'ERROR',
    jsonb_build_object('message', SQLERRM, 'state', SQLSTATE)
  );
  
  -- Re-raise the exception
  RAISE;
END;
$$ LANGUAGE plpgsql;

SELECT log_migration_step('create_function_get_user_minutes', 'COMPLETED');

-- Function to add minutes to user's account
SELECT log_migration_step('create_function_add_user_minutes', 'STARTED');

CREATE OR REPLACE FUNCTION add_user_minutes(p_user_id TEXT, p_minutes_to_add INTEGER)
RETURNS TABLE (remaining_minutes INTEGER) SECURITY DEFINER AS $$
DECLARE
  v_current_minutes INTEGER;
BEGIN
  -- Log operation start
  INSERT INTO public.operation_logs (operation_type, details, status)
  VALUES (
    'ADD_USER_MINUTES',
    jsonb_build_object('user_id', p_user_id, 'minutes_to_add', p_minutes_to_add),
    'STARTED'
  );

  -- Get current minutes
  SELECT COALESCE(remaining_minutes, 0), COALESCE(total_minutes_purchased, 0)
  INTO v_current_minutes
  FROM public.user_minutes
  WHERE user_id = p_user_id;

  -- Insert or update user_minutes record
  INSERT INTO public.user_minutes (
    user_id,
    remaining_minutes,
    total_minutes_purchased,
    last_updated
  )
  VALUES (
    p_user_id,
    COALESCE(v_current_minutes, 0) + p_minutes_to_add,
    COALESCE((SELECT total_minutes_purchased FROM public.user_minutes WHERE user_id = p_user_id), 0) + p_minutes_to_add,
    NOW()
  )
  ON CONFLICT (user_id)
  DO UPDATE SET
    remaining_minutes = public.user_minutes.remaining_minutes + p_minutes_to_add,
    total_minutes_purchased = public.user_minutes.total_minutes_purchased + p_minutes_to_add,
    last_updated = NOW();

  -- Return updated remaining minutes
  RETURN QUERY
  SELECT um.remaining_minutes
  FROM public.user_minutes um
  WHERE um.user_id = p_user_id;

  -- Log operation completion
  INSERT INTO public.operation_logs (operation_type, details, status)
  VALUES (
    'ADD_USER_MINUTES',
    jsonb_build_object(
      'user_id', p_user_id,
      'minutes_to_add', p_minutes_to_add,
      'new_total', (SELECT remaining_minutes FROM public.user_minutes WHERE user_id = p_user_id)
    ),
    'COMPLETED'
  );
EXCEPTION WHEN OTHERS THEN
  -- Log error
  INSERT INTO public.operation_logs (operation_type, details, status, error)
  VALUES (
    'ADD_USER_MINUTES',
    jsonb_build_object('user_id', p_user_id, 'minutes_to_add', p_minutes_to_add),
    'ERROR',
    jsonb_build_object('message', SQLERRM, 'state', SQLSTATE)
  );
  
  -- Re-raise the exception
  RAISE;
END;
$$ LANGUAGE plpgsql;

SELECT log_migration_step('create_function_add_user_minutes', 'COMPLETED');

-- Function to use minutes from user's account
SELECT log_migration_step('create_function_use_user_minutes', 'STARTED');

CREATE OR REPLACE FUNCTION use_user_minutes(p_user_id TEXT, p_minutes_to_use INTEGER)
RETURNS TABLE (remaining_minutes INTEGER, minutes_used INTEGER) SECURITY DEFINER AS $$
DECLARE
  v_current_minutes INTEGER;
  v_minutes_used INTEGER;
BEGIN
  -- Log operation start
  INSERT INTO public.operation_logs (operation_type, details, status)
  VALUES (
    'USE_USER_MINUTES',
    jsonb_build_object('user_id', p_user_id, 'minutes_to_use', p_minutes_to_use),
    'STARTED'
  );

  -- Get current minutes
  SELECT COALESCE(remaining_minutes, 0)
  INTO v_current_minutes
  FROM public.user_minutes
  WHERE user_id = p_user_id;

  -- Calculate minutes that can be used
  v_minutes_used := LEAST(COALESCE(v_current_minutes, 0), p_minutes_to_use);

  -- Update user_minutes record if it exists
  UPDATE public.user_minutes
  SET
    remaining_minutes = GREATEST(0, remaining_minutes - v_minutes_used),
    total_minutes_used = COALESCE(total_minutes_used, 0) + v_minutes_used,
    last_updated = NOW()
  WHERE user_id = p_user_id;

  -- Insert record if it doesn't exist
  IF NOT FOUND THEN
    INSERT INTO public.user_minutes (
      user_id,
      remaining_minutes,
      total_minutes_used,
      last_updated
    )
    VALUES (
      p_user_id,
      0,
      v_minutes_used,
      NOW()
    );
  END IF;

  -- Return updated remaining minutes and minutes used
  RETURN QUERY
  SELECT
    um.remaining_minutes,
    v_minutes_used
  FROM public.user_minutes um
  WHERE um.user_id = p_user_id;

  -- Log operation completion
  INSERT INTO public.operation_logs (operation_type, details, status)
  VALUES (
    'USE_USER_MINUTES',
    jsonb_build_object(
      'user_id', p_user_id,
      'minutes_requested', p_minutes_to_use,
      'minutes_used', v_minutes_used,
      'remaining_minutes', (SELECT remaining_minutes FROM public.user_minutes WHERE user_id = p_user_id)
    ),
    'COMPLETED'
  );
EXCEPTION WHEN OTHERS THEN
  -- Log error
  INSERT INTO public.operation_logs (operation_type, details, status, error)
  VALUES (
    'USE_USER_MINUTES',
    jsonb_build_object('user_id', p_user_id, 'minutes_to_use', p_minutes_to_use),
    'ERROR',
    jsonb_build_object('message', SQLERRM, 'state', SQLSTATE)
  );
  
  -- Re-raise the exception
  RAISE;
END;
$$ LANGUAGE plpgsql;

SELECT log_migration_step('create_function_use_user_minutes', 'COMPLETED');

-- Function to process Stripe webhook events
SELECT log_migration_step('create_function_process_stripe_webhook', 'STARTED');

CREATE OR REPLACE FUNCTION process_stripe_webhook(
  p_event_type TEXT,
  p_event_data JSONB
)
RETURNS VOID SECURITY DEFINER AS $$
DECLARE
  v_session_id TEXT;
  v_payment_intent_id TEXT;
  v_user_id TEXT;
  v_minutes INTEGER;
  v_amount INTEGER;
BEGIN
  -- Log operation start
  INSERT INTO public.operation_logs (operation_type, details, status)
  VALUES (
    'PROCESS_STRIPE_WEBHOOK',
    jsonb_build_object('event_type', p_event_type, 'event_data', p_event_data),
    'STARTED'
  );

  -- Handle checkout.session.completed event
  IF p_event_type = 'checkout.session.completed' THEN
    -- Extract data from event
    v_session_id := p_event_data->'data'->'object'->>'id';
    v_payment_intent_id := p_event_data->'data'->'object'->>'payment_intent';
    v_user_id := COALESCE(
      p_event_data->'data'->'object'->>'client_reference_id',
      p_event_data->'data'->'object'->>'customer_email',
      'anonymous'
    );
    v_minutes := (p_event_data->'data'->'object'->'metadata'->>'minutes')::INTEGER;
    v_amount := (p_event_data->'data'->'object'->>'amount_total')::INTEGER;

    -- Update payment record
    UPDATE public.payments
    SET
      status = 'completed',
      stripe_payment_intent_id = v_payment_intent_id,
      updated_at = NOW()
    WHERE stripe_session_id = v_session_id;

    -- If no payment record exists, create one
    IF NOT FOUND THEN
      INSERT INTO public.payments (
        user_id,
        stripe_session_id,
        stripe_payment_intent_id,
        amount,
        minutes_purchased,
        status
      )
      VALUES (
        v_user_id,
        v_session_id,
        v_payment_intent_id,
        v_amount,
        v_minutes,
        'completed'
      );
    END IF;

    -- Add minutes to user's account
    PERFORM add_user_minutes(v_user_id, v_minutes);
  END IF;

  -- Log operation completion
  INSERT INTO public.operation_logs (operation_type, details, status)
  VALUES (
    'PROCESS_STRIPE_WEBHOOK',
    jsonb_build_object(
      'event_type', p_event_type,
      'user_id', v_user_id,
      'minutes_added', v_minutes
    ),
    'COMPLETED'
  );
EXCEPTION WHEN OTHERS THEN
  -- Log error
  INSERT INTO public.operation_logs (operation_type, details, status, error)
  VALUES (
    'PROCESS_STRIPE_WEBHOOK',
    jsonb_build_object('event_type', p_event_type),
    'ERROR',
    jsonb_build_object('message', SQLERRM, 'state', SQLSTATE)
  );
  
  -- Re-raise the exception
  RAISE;
END;
$$ LANGUAGE plpgsql;

SELECT log_migration_step('create_function_process_stripe_webhook', 'COMPLETED');

-- Log the completion of migration
SELECT log_migration_step('migration_complete', 'COMPLETED', jsonb_build_object(
  'tables_created', jsonb_build_array('operation_logs', 'user_minutes', 'call_sessions', 'payments'),
  'functions_created', jsonb_build_array('get_user_minutes', 'add_user_minutes', 'use_user_minutes', 'process_stripe_webhook')
));
