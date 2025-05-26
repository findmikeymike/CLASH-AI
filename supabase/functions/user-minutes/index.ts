import { corsHeaders } from "@shared/cors.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.6";

interface GetMinutesRequest {
  userId: string;
}

interface UpdateMinutesRequest {
  userId: string;
  minutesUsed?: number;
  minutesAdded?: number;
}

Deno.serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL") || "";
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_KEY") || "";
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // GET request to fetch remaining minutes
    if (req.method === "GET") {
      const url = new URL(req.url);
      const userId = url.searchParams.get("userId");

      if (!userId) {
        return new Response(JSON.stringify({ error: "User ID is required" }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 400,
        });
      }

      // Get user minutes from database
      const { data, error } = await supabase
        .from("user_minutes")
        .select("remaining_minutes")
        .eq("user_id", userId)
        .single();

      if (error && error.code !== "PGRST116") {
        // PGRST116 is "no rows returned" error
        return new Response(JSON.stringify({ error: error.message }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 500,
        });
      }

      // Return 0 if no record found
      const remainingMinutes = data?.remaining_minutes || 0;

      return new Response(JSON.stringify({ remainingMinutes }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      });
    }

    // POST request to update minutes (add or use)
    if (req.method === "POST") {
      const { userId, minutesUsed, minutesAdded } =
        (await req.json()) as UpdateMinutesRequest;

      if (!userId) {
        return new Response(JSON.stringify({ error: "User ID is required" }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 400,
        });
      }

      if (minutesUsed === undefined && minutesAdded === undefined) {
        return new Response(
          JSON.stringify({
            error: "Either minutesUsed or minutesAdded must be provided",
          }),
          {
            headers: { ...corsHeaders, "Content-Type": "application/json" },
            status: 400,
          },
        );
      }

      // Get current minutes
      const { data: currentData, error: fetchError } = await supabase
        .from("user_minutes")
        .select("remaining_minutes")
        .eq("user_id", userId)
        .single();

      let currentMinutes = currentData?.remaining_minutes || 0;
      let newMinutes = currentMinutes;

      // Calculate new minutes
      if (minutesAdded !== undefined) {
        newMinutes += minutesAdded;
      }

      if (minutesUsed !== undefined) {
        newMinutes = Math.max(0, newMinutes - minutesUsed);
      }

      // Upsert the record
      const { data, error } = await supabase
        .from("user_minutes")
        .upsert({
          user_id: userId,
          remaining_minutes: newMinutes,
          last_updated: new Date().toISOString(),
        })
        .select("remaining_minutes")
        .single();

      if (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 500,
        });
      }

      return new Response(
        JSON.stringify({ remainingMinutes: data.remaining_minutes }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 200,
        },
      );
    }

    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: 405,
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
