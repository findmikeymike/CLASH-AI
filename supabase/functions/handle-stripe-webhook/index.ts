import { corsHeaders } from "@shared/cors.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.6";

Deno.serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL") || "";
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_KEY") || "";
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Get the stripe webhook secret
    const stripeWebhookSecret = Deno.env.get("STRIPE_WEBHOOK_SECRET") || "";

    // Get the signature from the headers
    const signature = req.headers.get("stripe-signature");

    if (!signature) {
      return new Response(
        JSON.stringify({ error: "Missing stripe-signature header" }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 400,
        },
      );
    }

    // Get the raw body
    const body = await req.text();
    let event;

    // Verify the webhook signature
    try {
      // In a production environment, you would verify the signature here
      // For now, we'll just parse the JSON
      event = JSON.parse(body);
    } catch (err) {
      return new Response(
        JSON.stringify({ error: `Webhook Error: ${err.message}` }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 400,
        },
      );
    }

    // Handle the event
    if (event.type === "checkout.session.completed") {
      const session = event.data.object;

      // Extract user ID from client_reference_id or customer email
      const userId =
        session.client_reference_id || session.customer_email || "anonymous";

      // Extract minutes from metadata
      const minutes = parseInt(session.metadata?.minutes || "0", 10);

      if (minutes > 0) {
        // Update user minutes in the database
        await supabase.functions.invoke("user-minutes", {
          body: { userId, minutesAdded: minutes },
          method: "POST",
        });
      }
    }

    return new Response(JSON.stringify({ received: true }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: 200,
    });
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message || "Internal server error" }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 500,
      },
    );
  }
});
