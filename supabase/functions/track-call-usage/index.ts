import { corsHeaders } from "@shared/cors.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.6";

interface TrackCallRequest {
  userId: string;
  action: "start" | "end";
  callId?: string;
  characterId?: string;
}

interface CallSession {
  id: string;
  user_id: string;
  character_id: string;
  start_time: string;
  end_time?: string;
  duration_seconds?: number;
  minutes_used?: number;
}

// Nuclear logging function for comprehensive debugging
const logOperation = async (supabase, operation, details, status, error = null) => {
  try {
    await supabase.from("operation_logs").insert({
      operation_type: operation,
      details: JSON.stringify(details),
      status: status,
      error: error ? JSON.stringify(error) : null,
      timestamp: new Date().toISOString()
    });
  } catch (logError) {
    // If logging fails, we still want the main function to continue
    console.error("Logging error:", logError);
  }
};

Deno.serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL") || "";
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_KEY") || "";
    
    if (!supabaseUrl || !supabaseServiceKey) {
      return new Response(
        JSON.stringify({ error: "Missing Supabase configuration" }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 500,
        }
      );
    }
    
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Only allow POST requests
    if (req.method !== "POST") {
      return new Response(JSON.stringify({ error: "Method not allowed" }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 405,
      });
    }

    const { userId, action, callId, characterId } = await req.json() as TrackCallRequest;

    // Validate required fields
    if (!userId) {
      return new Response(JSON.stringify({ error: "User ID is required" }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 400,
      });
    }

    if (!action || !["start", "end"].includes(action)) {
      return new Response(JSON.stringify({ error: "Valid action (start or end) is required" }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 400,
      });
    }

    // Log the operation start
    await logOperation(supabase, "TRACK_CALL", { userId, action, callId, characterId }, "STARTED");

    // Handle call start
    if (action === "start") {
      if (!characterId) {
        return new Response(JSON.stringify({ error: "Character ID is required for call start" }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 400,
        });
      }

      // Check if user has enough minutes
      const { data: minutesData, error: minutesError } = await supabase
        .from("user_minutes")
        .select("remaining_minutes")
        .eq("user_id", userId)
        .single();

      if (minutesError && minutesError.code !== "PGRST116") {
        await logOperation(supabase, "TRACK_CALL", { userId, action }, "ERROR", minutesError);
        return new Response(JSON.stringify({ error: "Failed to check remaining minutes" }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 500,
        });
      }

      const remainingMinutes = minutesData?.remaining_minutes || 0;

      // If user has no minutes, don't allow call to start
      if (remainingMinutes <= 0) {
        await logOperation(supabase, "TRACK_CALL", { userId, action, remainingMinutes }, "REJECTED");
        return new Response(JSON.stringify({ 
          error: "Insufficient minutes", 
          remainingMinutes: 0,
          canStart: false 
        }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 403,
        });
      }

      // Create a new call session
      const newCallId = crypto.randomUUID();
      const { data: callData, error: callError } = await supabase
        .from("call_sessions")
        .insert({
          id: newCallId,
          user_id: userId,
          character_id: characterId,
          start_time: new Date().toISOString(),
        })
        .select()
        .single();

      if (callError) {
        await logOperation(supabase, "TRACK_CALL", { userId, action }, "ERROR", callError);
        return new Response(JSON.stringify({ error: "Failed to create call session" }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 500,
        });
      }

      await logOperation(supabase, "TRACK_CALL", { userId, action, callId: newCallId }, "SUCCESS");
      return new Response(JSON.stringify({ 
        callId: newCallId, 
        remainingMinutes,
        canStart: true
      }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      });
    }

    // Handle call end
    if (action === "end") {
      if (!callId) {
        return new Response(JSON.stringify({ error: "Call ID is required for call end" }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 400,
        });
      }

      // Get the call session
      const { data: callData, error: callError } = await supabase
        .from("call_sessions")
        .select("*")
        .eq("id", callId)
        .eq("user_id", userId)
        .single();

      if (callError) {
        await logOperation(supabase, "TRACK_CALL", { userId, action, callId }, "ERROR", callError);
        return new Response(JSON.stringify({ error: "Failed to find call session" }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 404,
        });
      }

      const callSession = callData as CallSession;
      const endTime = new Date();
      const startTime = new Date(callSession.start_time);
      
      // Calculate duration in seconds
      const durationSeconds = Math.round((endTime.getTime() - startTime.getTime()) / 1000);
      
      // Calculate minutes used (round up to nearest minute, minimum 1 minute)
      const minutesUsed = Math.max(1, Math.ceil(durationSeconds / 60));

      // Update the call session
      const { error: updateError } = await supabase
        .from("call_sessions")
        .update({
          end_time: endTime.toISOString(),
          duration_seconds: durationSeconds,
          minutes_used: minutesUsed,
        })
        .eq("id", callId);

      if (updateError) {
        await logOperation(supabase, "TRACK_CALL", { userId, action, callId }, "ERROR", updateError);
        return new Response(JSON.stringify({ error: "Failed to update call session" }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 500,
        });
      }

      // Deduct minutes from user's account
      const { data: minutesData, error: minutesError } = await supabase.functions.invoke("user-minutes", {
        body: { userId, minutesUsed },
        method: "POST",
      });

      if (minutesError) {
        await logOperation(supabase, "TRACK_CALL", { userId, action, callId, minutesUsed }, "ERROR", minutesError);
        return new Response(JSON.stringify({ error: "Failed to update user minutes" }), {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
          status: 500,
        });
      }

      await logOperation(
        supabase, 
        "TRACK_CALL", 
        { userId, action, callId, durationSeconds, minutesUsed }, 
        "SUCCESS"
      );
      
      return new Response(JSON.stringify({ 
        durationSeconds,
        minutesUsed,
        remainingMinutes: minutesData.remainingMinutes
      }), {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      });
    }

    return new Response(JSON.stringify({ error: "Invalid action" }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: 400,
    });
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message || "Internal server error" }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 500,
      }
    );
  }
});
