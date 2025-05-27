import { createClient } from "@supabase/supabase-js";
// Initialize Supabase client
const supabase = createClient(import.meta.env.VITE_SUPABASE_URL, import.meta.env.VITE_SUPABASE_ANON_KEY);
/**
 * Test suite for payment system and token tracking
 * Now uses the reliable Edge Function test runner
 */
export const runPaymentTests = async () => {
    try {
        console.log("Starting payment system tests via Edge Function...");
        const { data, error } = await supabase.functions.invoke("supabase-functions-test-payment-system", {
            method: "POST",
        });
        if (error) {
            console.error("Error running tests:", error);
            return {
                success: false,
                results: [],
                summary: `Test execution failed: ${error.message || JSON.stringify(error)}`,
            };
        }
        console.log("Tests completed successfully:", data);
        return data;
    }
    catch (error) {
        console.error("Exception running payment tests:", error);
        return {
            success: false,
            results: [],
            summary: "Test suite failed with an unexpected error: " +
                (error.message || String(error)),
        };
    }
};
/**
 * Test creating a payment intent
 */
async function testCreatePaymentIntent() {
    try {
        console.log("Testing create-payment-intent function...");
        const testData = {
            priceId: "price_15USD",
            successUrl: "https://example.com/success",
            cancelUrl: "https://example.com/cancel",
            customerEmail: "test@example.com",
        };
        const { data, error } = await supabase.functions.invoke("supabase-functions-create-payment-intent", {
            body: testData,
        });
        if (error) {
            return {
                name: "Create Payment Intent",
                success: false,
                message: `Error: ${error.message || JSON.stringify(error)}`,
            };
        }
        // Check if the response contains expected fields
        if (!data || !data.id || !data.url) {
            return {
                name: "Create Payment Intent",
                success: false,
                message: `Invalid response format: ${JSON.stringify(data)}`,
            };
        }
        return {
            name: "Create Payment Intent",
            success: true,
            message: `Successfully created payment intent with ID: ${data.id}`,
        };
    }
    catch (error) {
        return {
            name: "Create Payment Intent",
            success: false,
            message: `Exception: ${error.message || String(error)}`,
        };
    }
}
/**
 * Test fetching user minutes
 */
async function testFetchUserMinutes() {
    try {
        console.log("Testing user-minutes GET function...");
        // Generate a test user ID
        const testUserId = `test_${Math.random().toString(36).substring(2, 15)}`;
        const { data, error } = await supabase.functions.invoke("supabase-functions-user-minutes", {
            body: { userId: testUserId },
            method: "GET",
        });
        if (error) {
            return {
                name: "Fetch User Minutes",
                success: false,
                message: `Error: ${error.message || JSON.stringify(error)}`,
            };
        }
        // For a new test user, we expect 0 minutes
        if (data.remainingMinutes !== 0 && data.remainingMinutes !== undefined) {
            return {
                name: "Fetch User Minutes",
                success: false,
                message: `Expected 0 minutes for new user, got: ${data.remainingMinutes}`,
            };
        }
        return {
            name: "Fetch User Minutes",
            success: true,
            message: `Successfully fetched user minutes: ${data.remainingMinutes}`,
        };
    }
    catch (error) {
        return {
            name: "Fetch User Minutes",
            success: false,
            message: `Exception: ${error.message || String(error)}`,
        };
    }
}
/**
 * Test updating user minutes
 */
async function testUpdateUserMinutes() {
    try {
        console.log("Testing user-minutes POST function...");
        // Generate a test user ID
        const testUserId = `test_${Math.random().toString(36).substring(2, 15)}`;
        // First, add minutes
        const addResult = await supabase.functions.invoke("supabase-functions-user-minutes", {
            body: { userId: testUserId, minutesAdded: 100 },
            method: "POST",
        });
        if (addResult.error) {
            return {
                name: "Update User Minutes",
                success: false,
                message: `Error adding minutes: ${addResult.error.message || JSON.stringify(addResult.error)}`,
            };
        }
        // Verify minutes were added
        if (addResult.data.remainingMinutes !== 100) {
            return {
                name: "Update User Minutes",
                success: false,
                message: `Expected 100 minutes after adding, got: ${addResult.data.remainingMinutes}`,
            };
        }
        // Now, use some minutes
        const useResult = await supabase.functions.invoke("supabase-functions-user-minutes", {
            body: { userId: testUserId, minutesUsed: 30 },
            method: "POST",
        });
        if (useResult.error) {
            return {
                name: "Update User Minutes",
                success: false,
                message: `Error using minutes: ${useResult.error.message || JSON.stringify(useResult.error)}`,
            };
        }
        // Verify minutes were deducted
        if (useResult.data.remainingMinutes !== 70) {
            return {
                name: "Update User Minutes",
                success: false,
                message: `Expected 70 minutes after using 30, got: ${useResult.data.remainingMinutes}`,
            };
        }
        return {
            name: "Update User Minutes",
            success: true,
            message: "Successfully added and used minutes",
        };
    }
    catch (error) {
        return {
            name: "Update User Minutes",
            success: false,
            message: `Exception: ${error.message || String(error)}`,
        };
    }
}
/**
 * Test webhook handler
 */
async function testWebhookHandler() {
    try {
        console.log("Testing handle-stripe-webhook function...");
        // Create a mock checkout.session.completed event
        const mockEvent = {
            type: "checkout.session.completed",
            data: {
                object: {
                    client_reference_id: `test_${Math.random().toString(36).substring(2, 15)}`,
                    customer_email: "test@example.com",
                    metadata: {
                        minutes: "80",
                    },
                },
            },
        };
        const { data, error } = await supabase.functions.invoke("supabase-functions-handle-stripe-webhook", {
            body: mockEvent,
            headers: {
                "stripe-signature": "mock_signature_for_test",
            },
        });
        if (error) {
            return {
                name: "Webhook Handler",
                success: false,
                message: `Error: ${error.message || JSON.stringify(error)}`,
            };
        }
        // Check if the response indicates success
        if (!data || !data.received) {
            return {
                name: "Webhook Handler",
                success: false,
                message: `Invalid response format: ${JSON.stringify(data)}`,
            };
        }
        return {
            name: "Webhook Handler",
            success: true,
            message: "Successfully processed webhook event",
        };
    }
    catch (error) {
        return {
            name: "Webhook Handler",
            success: false,
            message: `Exception: ${error.message || String(error)}`,
        };
    }
}
/**
 * Generate a summary of test results
 */
function generateSummary(results) {
    const totalTests = results.length;
    const passedTests = results.filter((r) => r.success).length;
    let summary = `${passedTests}/${totalTests} tests passed\n\n`;
    results.forEach((result) => {
        summary += `${result.success ? "✅" : "❌"} ${result.name}: ${result.message}\n`;
    });
    return summary;
}
