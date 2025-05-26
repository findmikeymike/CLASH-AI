import { corsHeaders } from "@shared/cors.ts";

interface CreateCheckoutSessionRequest {
  priceId: string;
  successUrl: string;
  cancelUrl: string;
  customerEmail?: string;
}

// Fixed pricing bundles - server-side validation
const ALLOWED_PRICE_IDS = [
  "price_8USD", // $8 for 40 minutes
  "price_15USD", // $15 for 80 minutes
  "price_28USD", // $28 for 160 minutes
  "price_50USD", // $50 for 320 minutes
];

// Map price IDs to minutes for usage tracking
const PRICE_TO_MINUTES = {
  price_8USD: 40,
  price_15USD: 80,
  price_28USD: 160,
  price_50USD: 320,
};

Deno.serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const { priceId, successUrl, cancelUrl, customerEmail } =
      (await req.json()) as CreateCheckoutSessionRequest;

    // Server-side validation: only allow predefined price bundles
    if (!ALLOWED_PRICE_IDS.includes(priceId)) {
      return new Response(
        JSON.stringify({ error: "Invalid price selected. Purchase denied." }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 400,
        },
      );
    }

    if (!successUrl || !cancelUrl) {
      return new Response(
        JSON.stringify({ error: "Success URL and Cancel URL are required" }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 400,
        },
      );
    }

    // Prepare request body for Stripe Checkout Session
    const requestBody = {
      mode: "payment",
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      success_url: successUrl,
      cancel_url: cancelUrl,
      metadata: {
        minutes: PRICE_TO_MINUTES[priceId].toString(),
        price_id: priceId,
      },
    };

    // Add customer email if provided
    if (customerEmail) {
      requestBody.customer_email = customerEmail;
    }

    // Call the Pica passthrough endpoint to create a checkout session
    const response = await fetch(
      "https://api.picaos.com/v1/passthrough/v1/checkout/sessions",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-pica-secret": Deno.env.get("PICA_SECRET_KEY") || "",
          "x-pica-connection-key":
            Deno.env.get("PICA_STRIPE_CONNECTION_KEY") || "",
          "x-pica-action-id":
            "conn_mod_def::GCmLNSLWawg::Pj6pgAmnQhuqMPzB8fquRg",
        },
        body: JSON.stringify(requestBody),
      },
    );

    const data = await response.json();

    if (!response.ok) {
      return new Response(
        JSON.stringify({
          error: data.error || "Failed to create checkout session",
        }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: response.status,
        },
      );
    }

    return new Response(JSON.stringify(data), {
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
