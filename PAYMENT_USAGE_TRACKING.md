# CLASH AI - Payment and Usage Tracking System

This document provides a comprehensive guide to the payment and usage tracking system implemented in CLASH AI. The system allows users to purchase minutes and tracks their usage when interacting with AI characters through the ElevenLabs voice interface.

## System Overview

The payment and usage tracking system consists of these key components:

1. **Stripe Integration** - Handles payment processing for minute packages
2. **Usage Tracking** - Monitors and calculates minutes used during AI conversations
3. **Database Tables** - Stores user minutes and call session data
4. **Edge Functions** - Serverless functions that handle payment processing and usage tracking

## Database Schema

The system uses these Supabase tables:

### user_minutes
- `user_id` (TEXT, PRIMARY KEY) - Unique identifier for the user
- `remaining_minutes` (INTEGER) - Minutes available for use
- `total_minutes_purchased` (INTEGER) - Total minutes purchased
- `total_minutes_used` (INTEGER) - Total minutes used
- `last_updated` (TIMESTAMPTZ) - Timestamp of last update

### call_sessions
- `id` (UUID, PRIMARY KEY) - Unique identifier for the call session
- `user_id` (TEXT) - User who initiated the call
- `character_id` (TEXT) - Character the user is talking to
- `start_time` (TIMESTAMPTZ) - When the call started
- `end_time` (TIMESTAMPTZ) - When the call ended
- `duration_seconds` (INTEGER) - Duration in seconds
- `minutes_used` (INTEGER) - Minutes charged for the call
- `created_at` (TIMESTAMPTZ) - Record creation timestamp

### operation_logs
- `id` (UUID, PRIMARY KEY) - Unique identifier for the log entry
- `operation_type` (TEXT) - Type of operation (e.g., TRACK_CALL, PAYMENT)
- `details` (JSONB) - Detailed information about the operation
- `status` (TEXT) - Status of the operation (e.g., STARTED, SUCCESS, ERROR)
- `error` (JSONB) - Error information if applicable
- `timestamp` (TIMESTAMPTZ) - When the log entry was created

## Edge Functions

### create-payment-intent
Handles Stripe checkout session creation for purchasing minute packages.

**Input:**
- `priceId` - ID of the minute package
- `successUrl` - URL to redirect after successful payment
- `cancelUrl` - URL to redirect after cancelled payment
- `customerEmail` - Email for the receipt

**Output:**
- `url` - Stripe checkout URL

### handle-stripe-webhook
Processes Stripe webhook events for completed payments.

**Events Handled:**
- `checkout.session.completed` - Updates user's minutes after successful payment

### user-minutes
Manages user minute balances.

**GET Request:**
- Retrieves remaining minutes for a user

**POST Request:**
- Updates user minutes (add purchased minutes or deduct used minutes)

### track-call-usage
Tracks call start/end and calculates minutes used.

**Actions:**
- `start` - Begins tracking a new call session
- `end` - Ends a call session and calculates minutes used

## Client Integration

The client-side integration is primarily in the `DebateInterface.tsx` component, which:

1. Fetches the user's remaining minutes on component mount
2. Tracks call start/end events from the ElevenLabs widget
3. Calls the track-call-usage Edge Function to record usage
4. Updates the UI with remaining minutes
5. Shows notifications for insufficient minutes

## Setup Instructions

1. **Set up Supabase tables:**
   - Run the SQL migration in `supabase/migrations/20250526_call_tracking/call_tracking_tables.sql`

2. **Configure environment variables:**
   - Copy `supabase/.env.example` to `supabase/.env`
   - Fill in your Supabase service key and other credentials

3. **Deploy Edge Functions:**
   ```bash
   cd supabase
   supabase functions deploy create-payment-intent --no-verify-jwt
   supabase functions deploy handle-stripe-webhook --no-verify-jwt
   supabase functions deploy user-minutes --no-verify-jwt
   supabase functions deploy track-call-usage --no-verify-jwt
   ```

4. **Set up Stripe webhook:**
   - Create a Stripe webhook pointing to your Supabase Edge Function URL
   - Configure it to listen for `checkout.session.completed` events
   - Add the webhook secret to your environment variables

## Usage Flow

1. User selects a minute package and completes payment via Stripe
2. Stripe webhook notifies the system of successful payment
3. Minutes are added to the user's account
4. When the user starts a call with an AI character:
   - System checks if user has sufficient minutes
   - If yes, call tracking begins
   - If no, call is prevented and user is prompted to purchase minutes
5. When the call ends:
   - System calculates minutes used (minimum 1 minute, rounded up)
   - Minutes are deducted from the user's account
   - Usage details are displayed to the user

## Troubleshooting

### Common Issues

1. **Edge Function errors:**
   - Check Supabase logs for detailed error messages
   - Verify environment variables are correctly set

2. **Stripe payment issues:**
   - Confirm Stripe webhook is properly configured
   - Check webhook logs in Stripe dashboard

3. **Usage tracking problems:**
   - Review operation_logs table for detailed error information
   - Ensure ElevenLabs widget events are firing correctly

## Nuclear Logging

The system implements comprehensive nuclear logging for all operations:

- Every payment and usage operation is logged with detailed information
- Logs include operation type, status, timestamps, and error details
- All database operations have proper error handling and logging
- Logs can be used for auditing, debugging, and rollback if needed

This logging approach ensures that any issues can be quickly identified and resolved, maintaining the reliability and integrity of the payment and usage tracking system.
