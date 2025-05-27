import { createClient } from "@supabase/supabase-js";

// Initialize Supabase client
const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
);

/**
 * Check the health of the payment system components
 * Now uses the reliable Edge Function test runner for comprehensive health checks
 */
export const checkPaymentSystemHealth = async () => {
  try {
    console.log("Starting payment system health check via Edge Function...");

    const { data, error } = await supabase.functions.invoke(
      "supabase-functions-test-payment-system",
      {
        method: "POST",
      },
    );

    if (error) {
      console.error("Error running health check:", error);
      return {
        healthy: false,
        results: [],
        summary: `Health check failed: ${error.message || JSON.stringify(error)}`,
      };
    }

    // Convert test results to health check format
    const healthResults = data.results.map((result: any) => ({
      component: result.name,
      healthy: result.success,
      message:
        result.message +
        (result.duration ? ` (${result.duration.toFixed(2)}ms)` : ""),
    }));

    console.log("Health check completed:", data);
    return {
      healthy: data.success,
      results: healthResults,
      summary: data.summary,
    };
  } catch (error) {
    console.error("Exception running health check:", error);
    return {
      healthy: false,
      results: [],
      summary:
        "Health check failed with an unexpected error: " +
        (error.message || String(error)),
    };
  }
};

/**
 * Check database connection
 */
async function checkDatabaseConnection(): Promise<HealthCheckResult> {
  try {
    // Simple query to check if we can connect to the database
    const { data, error } = await supabase
      .from("user_minutes")
      .select("count(*)", { count: "exact", head: true });

    if (error) {
      return {
        component: "Database Connection",
        healthy: false,
        message: `Error connecting to database: ${error.message}`,
      };
    }

    return {
      component: "Database Connection",
      healthy: true,
      message: "Successfully connected to database",
    };
  } catch (error) {
    return {
      component: "Database Connection",
      healthy: false,
      message: `Exception: ${error.message || String(error)}`,
    };
  }
}

/**
 * Check payment intent function
 */
async function checkPaymentIntentFunction(): Promise<HealthCheckResult> {
  try {
    // Simple ping to check if the function is accessible
    const { data, error } = await supabase.functions.invoke(
      "supabase-functions-create-payment-intent",
      {
        body: { ping: true },
        method: "GET",
      },
    );

    // For GET request, we just care that it doesn't error
    if (error) {
      return {
        component: "Create Payment Intent Function",
        healthy: false,
        message: `Error accessing function: ${error.message}`,
      };
    }

    return {
      component: "Create Payment Intent Function",
      healthy: true,
      message: "Function is accessible",
    };
  } catch (error) {
    return {
      component: "Create Payment Intent Function",
      healthy: false,
      message: `Exception: ${error.message || String(error)}`,
    };
  }
}

/**
 * Check user minutes function
 */
async function checkUserMinutesFunction(): Promise<HealthCheckResult> {
  try {
    // Simple ping to check if the function is accessible
    const { data, error } = await supabase.functions.invoke(
      "supabase-functions-user-minutes",
      {
        body: { ping: true },
        method: "GET",
      },
    );

    // For GET request, we just care that it doesn't error
    if (error) {
      return {
        component: "User Minutes Function",
        healthy: false,
        message: `Error accessing function: ${error.message}`,
      };
    }

    return {
      component: "User Minutes Function",
      healthy: true,
      message: "Function is accessible",
    };
  } catch (error) {
    return {
      component: "User Minutes Function",
      healthy: false,
      message: `Exception: ${error.message || String(error)}`,
    };
  }
}

/**
 * Check webhook function
 */
async function checkWebhookFunction(): Promise<HealthCheckResult> {
  try {
    // Simple ping to check if the function is accessible
    const { data, error } = await supabase.functions.invoke(
      "supabase-functions-handle-stripe-webhook",
      {
        body: { ping: true },
        method: "GET",
      },
    );

    // For GET request, we just care that it doesn't error
    if (error) {
      return {
        component: "Webhook Handler Function",
        healthy: false,
        message: `Error accessing function: ${error.message}`,
      };
    }

    return {
      component: "Webhook Handler Function",
      healthy: true,
      message: "Function is accessible",
    };
  } catch (error) {
    return {
      component: "Webhook Handler Function",
      healthy: false,
      message: `Exception: ${error.message || String(error)}`,
    };
  }
}

/**
 * Generate a summary of health check results
 */
function generateHealthSummary(results: HealthCheckResult[]): string {
  const totalChecks = results.length;
  const healthyChecks = results.filter((r) => r.healthy).length;

  let summary = `${healthyChecks}/${totalChecks} components healthy\n\n`;

  results.forEach((result) => {
    summary += `${result.healthy ? "✅" : "❌"} ${result.component}: ${result.message}\n`;
  });

  return summary;
}

/**
 * Health check result interface
 */
interface HealthCheckResult {
  component: string;
  healthy: boolean;
  message: string;
}
