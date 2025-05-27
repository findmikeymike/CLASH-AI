# CLASH AI Payment and Usage Tracking System

This document provides a comprehensive overview of the payment and usage tracking system implemented for CLASH AI. It follows nuclear debugging principles with detailed logging and error handling at every step.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Schema](#database-schema)
3. [Edge Functions](#edge-functions)
4. [Client-Side Integration](#client-side-integration)
5. [Stripe Integration](#stripe-integration)
6. [Usage Tracking](#usage-tracking)
7. [Error Handling](#error-handling)
8. [Testing](#testing)
9. [Deployment](#deployment)
10. [Maintenance](#maintenance)

## System Architecture

The payment and usage tracking system consists of:

1. **Supabase Database**: Stores user minutes, call sessions, and payment information
2. **Supabase Edge Functions**: Handle API requests for payments and usage tracking
3. **Stripe Integration**: Processes payments and webhooks
4. **Client-Side Components**: Interface with the backend services

The system follows a methodical, sequential approach where each component is built and tested individually before being integrated into the whole.

## Database Schema

### Tables

1. **user_minutes**
   ```sql
   CREATE TABLE public.user_minutes (
     user_id TEXT PRIMARY KEY,
     remaining_minutes INTEGER NOT NULL DEFAULT 0,
     total_minutes_purchased INTEGER NOT NULL DEFAULT 0,
     total_minutes_used INTEGER NOT NULL DEFAULT 0,
     last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW()
   );
   ```

2. **call_sessions**
   ```sql
   CREATE TABLE public.call_sessions (
     id UUID PRIMARY KEY,
     user_id TEXT NOT NULL,
     character_id TEXT NOT NULL,
     start_time TIMESTAMPTZ NOT NULL,
     end_time TIMESTAMPTZ,
     duration_seconds INTEGER,
     minutes_used INTEGER,
     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
   );
   ```

3. **payments**
   ```sql
   CREATE TABLE public.payments (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     user_id TEXT NOT NULL,
     stripe_session_id TEXT,
     stripe_payment_intent_id TEXT,
     amount INTEGER NOT NULL,
     minutes_purchased INTEGER NOT NULL,
     status TEXT NOT NULL,
     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
     updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
   );
   ```

4. **operation_logs**
   ```sql
   CREATE TABLE public.operation_logs (
     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
     operation_type TEXT NOT NULL,
     details JSONB,
     status TEXT NOT NULL,
     error JSONB,
     timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
   );
   ```

### Database Functions

1. **get_user_minutes**: Retrieves a user's remaining minutes
2. **add_user_minutes**: Adds minutes to a user's account
3. **use_user_minutes**: Deducts minutes from a user's account
4. **process_stripe_webhook**: Processes Stripe webhook events

### Row Level Security (RLS)

All tables have RLS policies to ensure users can only access their own data:

```sql
-- Example RLS policy for user_minutes
CREATE POLICY user_minutes_select_policy ON public.user_minutes
  FOR SELECT USING (auth.uid()::text = user_id);
```

## Edge Functions

### 1. create-payment-intent

Handles the creation of Stripe checkout sessions for purchasing minute packages.

**Endpoint**: `/functions/v1/create-payment-intent`

**Request**:
```json
{
  "priceId": "price_1OvCXKGLCcFoteZDOQYPGvHB",
  "userId": "user123",
  "returnUrl": "https://letsclash.app/payment-success"
}
```

**Response**:
```json
{
  "url": "https://checkout.stripe.com/..."
}
```

### 2. handle-stripe-webhook

Processes Stripe webhook events to update user minutes upon successful payments.

**Endpoint**: `/functions/v1/handle-stripe-webhook`

**Webhook Event**: `checkout.session.completed`

### 3. user-minutes

Manages user minute balances, allowing retrieval and updates.

**Endpoint**: `/functions/v1/user-minutes`

**Methods**:
- GET: Retrieve user minutes
- POST: Add minutes to user account
- PUT: Initialize user minutes

### 4. track-call-usage

Tracks call start and end events, calculating the duration of calls and updating user minutes accordingly.

**Endpoint**: `/functions/v1/track-call-usage`

**Request (Start Call)**:
```json
{
  "userId": "user123",
  "action": "start",
  "characterId": "character456"
}
```

**Response**:
```json
{
  "canStart": true,
  "callId": "call789",
  "remainingMinutes": 10
}
```

**Request (End Call)**:
```json
{
  "userId": "user123",
  "action": "end",
  "callId": "call789"
}
```

**Response**:
```json
{
  "callId": "call789",
  "durationSeconds": 120,
  "minutesUsed": 2,
  "remainingMinutes": 8
}
```

## Client-Side Integration

### Components

1. **TokenPurchaseModal.tsx**: Displays available minute packages and handles checkout
2. **DebateInterface.tsx**: Integrates with ElevenLabs widget and tracks call usage
3. **TestUsageTracking.tsx**: Test component for verifying the system

### Utilities

1. **usageTracking.ts**: Client-side utilities for tracking call usage

```typescript
// Key functions in usageTracking.ts
export async function trackCallUsage(
  userId: string,
  action: "start" | "end",
  callId?: string,
  characterId?: string
) {
  // Implementation details...
}

export async function getRemainingMinutes(userId: string) {
  // Implementation details...
}

export async function addMinutes(userId: string, minutes: number) {
  // Implementation details...
}

export async function initializeUserMinutes(userId: string, initialMinutes?: number) {
  // Implementation details...
}
```

## Stripe Integration

### Configuration

1. **Environment Variables**:
   - `STRIPE_SECRET_KEY`: Stripe API key for server-side operations
   - `STRIPE_WEBHOOK_SECRET`: Secret for verifying webhook signatures
   - `VITE_STRIPE_PRICE_10MIN`, `VITE_STRIPE_PRICE_30MIN`, `VITE_STRIPE_PRICE_60MIN`: Price IDs for minute packages

2. **Webhook Configuration**:
   - URL: `https://letsclash.app/functions/v1/handle-stripe-webhook`
   - Events: `checkout.session.completed`

### Minute Packages

| Package | Minutes | Price ID | Price |
|---------|---------|----------|-------|
| Try It | 40 | price_1OvCXKGLCcFoteZDOQYPGvHB | $8.00 |
| Standard | 80 | price_1OvCXkGLCcFoteZDnPvtTqhB | $15.00 |
| Popular | 160 | price_1OvCY9GLCcFoteZDfgvHOFzD | $28.00 |
| Power User | 320 | price_1OvCYaGLCcFoteZDdgvJYhzP | $50.00 |

## Usage Tracking

### Call Lifecycle

1. **Call Start**:
   - User initiates a call through the ElevenLabs widget
   - `trackCallUsage` is called with `action: "start"`
   - System verifies user has sufficient minutes
   - A new call session is created in the database
   - Call ID is returned to the client

2. **During Call**:
   - Client tracks call duration locally
   - ElevenLabs widget handles voice interaction

3. **Call End**:
   - User ends the call through the ElevenLabs widget
   - `trackCallUsage` is called with `action: "end"`
   - System calculates call duration and minutes used
   - User's remaining minutes are updated
   - Call session is updated with end time and duration

### Minute Calculation

- Minutes are calculated by rounding up the call duration to the nearest minute
- Example: A call lasting 1 minute and 10 seconds counts as 2 minutes

## Error Handling

The system implements nuclear debugging principles with comprehensive error handling:

1. **Client-Side Fallbacks**:
   - Local storage backup for tracking minutes
   - Graceful degradation when Edge Functions are unavailable

2. **Server-Side Logging**:
   - All operations are logged in the `operation_logs` table
   - Detailed error information is captured for debugging

3. **User Feedback**:
   - Clear error messages for insufficient minutes
   - Toast notifications for successful/failed operations

## Testing

A dedicated test component (`TestUsageTracking.tsx`) allows verification of:

1. User minute balance retrieval
2. Starting and ending calls
3. Adding minutes (simulating payments)
4. Viewing call history

Access this component at: `https://letsclash.app/test-usage`

## Deployment

The system is deployed on:

1. **Database**: Supabase project `mlaxmbzffcxspvgabkog`
2. **Edge Functions**: Deployed to Supabase
3. **Frontend**: Deployed to Netlify at `https://letsclash.app`

### Environment Variables

1. **Supabase**:
   - `SUPABASE_URL`: `https://mlaxmbzffcxspvgabkog.supabase.co`
   - `SUPABASE_SERVICE_KEY`: Service role key for Edge Functions

2. **Netlify**:
   - `VITE_SUPABASE_URL`: `https://mlaxmbzffcxspvgabkog.supabase.co`
   - `VITE_SUPABASE_ANON_KEY`: Anonymous key for client-side operations
   - `VITE_STRIPE_PRICE_10MIN`, `VITE_STRIPE_PRICE_30MIN`, `VITE_STRIPE_PRICE_60MIN`: Price IDs

## Maintenance

### Monitoring

1. **Database Usage**:
   - Monitor the `operation_logs` table for errors
   - Check user minute balances and payment status

2. **Stripe Dashboard**:
   - Monitor payments and webhook events
   - Check for failed payments or webhook delivery issues

### Updates

When updating the system:

1. Follow the methodical, sequential approach
2. Test each component individually before integration
3. Maintain comprehensive logging for all operations
4. Deploy changes through the established CI/CD pipeline

### Troubleshooting

Common issues and solutions:

1. **Webhook Failures**:
   - Verify webhook URL and secret
   - Check Stripe dashboard for delivery attempts
   - Inspect `operation_logs` for detailed error information

2. **Payment Issues**:
   - Verify Stripe API keys and price IDs
   - Check for changes in Stripe API
   - Test with Stripe test cards

3. **Minute Tracking Issues**:
   - Verify Edge Function deployment
   - Check database functions and RLS policies
   - Inspect call session records for discrepancies

---

This documentation follows nuclear debugging principles with detailed information about each component of the payment and usage tracking system. It provides a comprehensive reference for maintaining and extending the system in the future.
