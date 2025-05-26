/**
 * Utility function to simulate ElevenLabs API calls for testing
 * This helps verify that our fetch interceptor is working correctly
 */
export const simulateElevenLabsApiCall = async (
  duration: number = 500,
): Promise<void> => {
  // Create a mock URL that includes elevenlabs.io to trigger our interceptor
  const mockUrl = "https://api.elevenlabs.io/v1/test-endpoint";

  // Create a mock response
  const mockResponse = new Response(JSON.stringify({ success: true }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });

  // Store the original fetch
  const originalFetch = window.fetch;

  try {
    // Temporarily replace fetch with our own implementation for this test
    window.fetch = async () => {
      // Simulate API call duration
      await new Promise((resolve) => setTimeout(resolve, duration));
      return mockResponse;
    };

    // Make the fake API call that will trigger our interceptor
    await fetch(mockUrl);

    console.log(
      `Test API call simulation completed with duration ~${duration}ms`,
    );
  } finally {
    // Restore the original fetch
    window.fetch = originalFetch;
  }
};

/**
 * Utility function to add a listener for the elevenlabs-api-call event
 * This helps verify that our custom event is being dispatched correctly
 */
export const listenForApiCallEvents = (
  callback: (event: CustomEvent) => void,
): (() => void) => {
  const handler = (event: Event) => {
    callback(event as CustomEvent);
  };

  window.addEventListener("elevenlabs-api-call", handler);

  // Return a function to remove the listener
  return () => {
    window.removeEventListener("elevenlabs-api-call", handler);
  };
};
