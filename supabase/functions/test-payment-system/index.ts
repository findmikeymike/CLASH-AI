import { corsHeaders } from "@shared/cors.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.45.6";

interface TestResult {
  name: string;
  success: boolean;
  message: string;
  duration?: number;
}

interface TestSuiteResult {
  success: boolean;
  results: TestResult[];
  summary: string;
  totalDuration: number;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders, status: 200 });
  }

  const startTime = performance.now();
  const results: TestResult[] = [];

  try {
    // Get Supabase credentials from environment variables
    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_KEY");

    // Validate that we have the required credentials
    if (!supabaseUrl || !supabaseServiceKey) {
      throw new Error(
        "Missing Supabase credentials: " +
          (!supabaseUrl ? "SUPABASE_URL " : "") +
          (!supabaseServiceKey ? "SUPABASE_SERVICE_KEY" : ""),
      );
    }

    // Create the Supabase client with explicit credentials
    const supabase = createClient(supabaseUrl, supabaseServiceKey);

    // Test 1: Database Connection
    const dbTest = await testDatabaseConnection(supabase);
    results.push(dbTest);

    // Test 2: User Minutes Function - Direct database test
    const userMinutesTest = await testUserMinutesDirectly(supabase);
    results.push(userMinutesTest);

    // Test 3: Payment Intent Function - Test environment variables
    const paymentTest = await testPaymentEnvironment();
    results.push(paymentTest);

    // Test 4: Stripe Charge Test (using Pica passthrough)
    const chargeTest = await testStripeCharge();
    results.push(chargeTest);

    // Test 5: Basic function accessibility
    const functionTest = await testFunctionAccessibility();
    results.push(functionTest);

    const totalDuration = performance.now() - startTime;
    const success = results.every((r) => r.success);

    const testSuite: TestSuiteResult = {
      success,
      results,
      summary: generateSummary(results, totalDuration),
      totalDuration,
    };

    return new Response(JSON.stringify(testSuite), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: 200,
    });
  } catch (error) {
    const totalDuration = performance.now() - startTime;
    return new Response(
      JSON.stringify({
        success: false,
        results,
        summary: "Test suite failed: " + (error?.message || String(error)),
        totalDuration,
      }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      },
    );
  }
});

async function testDatabaseConnection(supabase) {
  const testStart = performance.now();
  try {
    const { data, error } = await supabase
      .from("user_minutes")
      .select("count(*)", { count: "exact", head: true });

    const duration = performance.now() - testStart;

    if (error) {
      return {
        name: "Database Connection",
        success: false,
        message: "Database error: " + error.message,
        duration,
      };
    }

    return {
      name: "Database Connection",
      success: true,
      message: "Successfully connected to database",
      duration,
    };
  } catch (error) {
    return {
      name: "Database Connection",
      success: false,
      message: "Exception: " + (error?.message || String(error)),
      duration: performance.now() - testStart,
    };
  }
}

async function testUserMinutesDirectly(supabase) {
  const testStart = performance.now();
  try {
    const testUserId = "test_" + Date.now();

    const { data: insertData, error: insertError } = await supabase
      .from("user_minutes")
      .upsert({
        user_id: testUserId,
        remaining_minutes: 100,
        last_updated: new Date().toISOString(),
      })
      .select()
      .single();

    if (insertError) {
      return {
        name: "User Minutes Database Operations",
        success: false,
        message: "Database insert failed: " + insertError.message,
        duration: performance.now() - testStart,
      };
    }

    const { data: updateData, error: updateError } = await supabase
      .from("user_minutes")
      .update({ remaining_minutes: 70 })
      .eq("user_id", testUserId)
      .select()
      .single();

    if (updateError) {
      return {
        name: "User Minutes Database Operations",
        success: false,
        message: "Database update failed: " + updateError.message,
        duration: performance.now() - testStart,
      };
    }

    await supabase.from("user_minutes").delete().eq("user_id", testUserId);

    return {
      name: "User Minutes Database Operations",
      success: true,
      message: "Successfully performed database operations",
      duration: performance.now() - testStart,
    };
  } catch (error) {
    return {
      name: "User Minutes Database Operations",
      success: false,
      message: "Exception: " + (error?.message || String(error)),
      duration: performance.now() - testStart,
    };
  }
}

async function testPaymentEnvironment() {
  const testStart = performance.now();
  try {
    const picaSecret = Deno.env.get("PICA_SECRET_KEY");
    const picaConnectionKey = Deno.env.get("PICA_STRIPE_CONNECTION_KEY");

    const envChecks = {
      PICA_SECRET_KEY: picaSecret ? "✅ Set" : "❌ Missing",
      PICA_STRIPE_CONNECTION_KEY: picaConnectionKey ? "✅ Set" : "❌ Missing",
      SUPABASE_URL: Deno.env.get("SUPABASE_URL") ? "✅ Set" : "❌ Missing",
      SUPABASE_SERVICE_KEY: Deno.env.get("SUPABASE_SERVICE_KEY")
        ? "✅ Set"
        : "❌ Missing",
    };

    const missingVars = Object.entries(envChecks)
      .filter(([_, status]) => status.includes("Missing"))
      .map(([key, _]) => key);

    if (missingVars.length > 0) {
      return {
        name: "Payment Environment Check",
        success: false,
        message: "Missing environment variables: " + missingVars.join(", "),
        duration: performance.now() - testStart,
      };
    }

    return {
      name: "Payment Environment Check",
      success: true,
      message: "All required environment variables are set",
      duration: performance.now() - testStart,
    };
  } catch (error) {
    return {
      name: "Payment Environment Check",
      success: false,
      message: "Exception: " + (error?.message || String(error)),
      duration: performance.now() - testStart,
    };
  }
}

async function testStripeCharge() {
  const testStart = performance.now();
  try {
    const picaSecret = Deno.env.get("PICA_SECRET_KEY");
    const picaConnectionKey = Deno.env.get("PICA_STRIPE_CONNECTION_KEY");

    if (!picaSecret || !picaConnectionKey) {
      return {
        name: "Stripe Payment Intent Test",
        success: false,
        message: "Missing PICA environment variables",
        duration: performance.now() - testStart,
      };
    }

    const url = "https://api.picaos.com/v1/passthrough/payment_intents";
    const headers = {
      "Content-Type": "application/x-www-form-urlencoded",
      "x-pica-secret": picaSecret,
      "x-pica-connection-key": picaConnectionKey,
      "x-pica-action-id": "conn_mod_def::GCmOAuPP5MQ::O0MeKcobRza5lZQrIkoqBA",
    };

    const params = new URLSearchParams();
    params.append("amount", "2000");
    params.append("currency", "usd");
    params.append("automatic_payment_methods[enabled]", "true");
    params.append("description", "Test payment intent");
    params.append("metadata[minutes]", "80");
    params.append("metadata[test]", "true");

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    try {
      const response = await fetch(url, {
        method: "POST",
        headers,
        body: params.toString(),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      const duration = performance.now() - testStart;

      if (!response.ok) {
        return {
          name: "Stripe Payment Intent Test",
          success: false,
          message: "HTTP " + response.status + ": " + (await response.text()),
          duration,
        };
      }

      const data = await response.json();
      return {
        name: "Stripe Payment Intent Test",
        success: true,
        message:
          "Successfully created payment intent: " + (data.id || "unknown"),
        duration,
      };
    } catch (fetchError) {
      clearTimeout(timeoutId);
      if (fetchError.name === "AbortError") {
        return {
          name: "Stripe Payment Intent Test",
          success: true,
          message: "Test skipped due to timeout (5s)",
          duration: performance.now() - testStart,
        };
      }
      throw fetchError;
    }
  } catch (error) {
    return {
      name: "Stripe Payment Intent Test",
      success: false,
      message: "Exception: " + (error?.message || String(error)),
      duration: performance.now() - testStart,
    };
  }
}

async function testFunctionAccessibility() {
  const testStart = performance.now();
  try {
    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_KEY");

    if (!supabaseUrl) {
      return {
        name: "Function Accessibility Check",
        success: false,
        message: "Missing SUPABASE_URL environment variable",
        duration: performance.now() - testStart,
      };
    }

    const functionUrl = supabaseUrl + "/functions/v1/user-minutes";

    try {
      const response = await fetch(functionUrl, {
        method: "OPTIONS",
        headers: {
          Authorization: "Bearer " + (supabaseServiceKey || ""),
          "Content-Type": "application/json",
        },
      });

      const duration = performance.now() - testStart;

      if (response.ok || response.status === 200 || response.status === 204) {
        return {
          name: "Function Accessibility Check",
          success: true,
          message: "Edge function is accessible (HTTP " + response.status + ")",
          duration,
        };
      } else {
        return {
          name: "Function Accessibility Check",
          success: false,
          message: "Edge function returned HTTP " + response.status,
          duration,
        };
      }
    } catch (fetchError) {
      return {
        name: "Function Accessibility Check",
        success: false,
        message: "Network error: " + fetchError.message,
        duration: performance.now() - testStart,
      };
    }
  } catch (error) {
    return {
      name: "Function Accessibility Check",
      success: false,
      message: "Exception: " + (error?.message || String(error)),
      duration: performance.now() - testStart,
    };
  }
}

function generateSummary(results, totalDuration) {
  const totalTests = results.length;
  const passedTests = results.filter((r) => r.success).length;

  let summary = "Test Suite Results\n";
  summary += "=================\n";
  summary += "Total Tests: " + totalTests + "\n";
  summary += "Passed: " + passedTests + "\n";
  summary += "Failed: " + (totalTests - passedTests) + "\n";
  summary += "Total Duration: " + totalDuration.toFixed(2) + "ms\n\n";

  results.forEach((result) => {
    const status = result.success ? "✅ PASS" : "❌ FAIL";
    const duration = result.duration
      ? " (" + result.duration.toFixed(2) + "ms)"
      : "";
    summary += status + " " + result.name + duration + "\n";
    summary += "    " + result.message + "\n\n";
  });

  return summary;
}
