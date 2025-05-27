import { createClient } from "@supabase/supabase-js";
// Initialize Supabase client
const supabase = createClient(import.meta.env.VITE_SUPABASE_URL, import.meta.env.VITE_SUPABASE_ANON_KEY);
// Nuclear logging for comprehensive debugging
const logOperation = async (operation, details, status, error = null) => {
    console.log(`[${operation}] [${status}]`, details, error ? `ERROR: ${error}` : '');
    try {
        // If connected to Supabase, log to the operation_logs table
        if (supabase) {
            await supabase.from("operation_logs").insert({
                operation_type: operation,
                details,
                status,
                error: error ? JSON.stringify(error) : null,
                timestamp: new Date().toISOString()
            });
        }
    }
    catch (logError) {
        // If logging fails, log to console but don't disrupt the main flow
        console.error("Logging error:", logError);
    }
};
// Local fallback for tracking call usage when Edge Functions aren't available
export const trackCallUsage = async (userId, action, callId, characterId) => {
    try {
        // Log the operation start
        await logOperation("TRACK_CALL_LOCAL", { userId, action, callId, characterId }, "STARTED");
        // Try to use the Edge Function first
        try {
            const { data, error } = await supabase.functions.invoke("track-call-usage", {
                body: {
                    userId,
                    action,
                    callId,
                    characterId,
                },
            });
            if (error) {
                throw new Error(`Edge Function error: ${error.message}`);
            }
            await logOperation("TRACK_CALL_LOCAL", { userId, action, result: data }, "SUCCESS");
            return data;
        }
        catch (edgeFunctionError) {
            console.warn("Edge Function not available, using local fallback:", edgeFunctionError);
            // Local fallback implementation
            if (action === 'start') {
                // Generate a new call ID
                const newCallId = crypto.randomUUID();
                // Store call start in localStorage
                const callData = {
                    id: newCallId,
                    userId,
                    characterId,
                    startTime: new Date().toISOString(),
                };
                // Save to localStorage
                const existingCalls = JSON.parse(localStorage.getItem('call_sessions') || '[]');
                localStorage.setItem('call_sessions', JSON.stringify([...existingCalls, callData]));
                // Get remaining minutes from localStorage
                const userMinutes = JSON.parse(localStorage.getItem(`user_minutes_${userId}`) || '{"remaining_minutes": 0}');
                // Log the minutes value for debugging
                console.log(`[LOCAL_FALLBACK] User ${userId} has ${userMinutes.remaining_minutes} minutes remaining`);
                await logOperation("TRACK_CALL_LOCAL", { userId, action, callId: newCallId }, "SUCCESS");
                return {
                    callId: newCallId,
                    remainingMinutes: userMinutes.remaining_minutes,
                    canStart: userMinutes.remaining_minutes > 0
                };
            }
            else if (action === 'end' && callId) {
                // Get call data from localStorage
                const existingCalls = JSON.parse(localStorage.getItem('call_sessions') || '[]');
                const callIndex = existingCalls.findIndex((call) => call.id === callId);
                if (callIndex === -1) {
                    throw new Error('Call session not found');
                }
                const callSession = existingCalls[callIndex];
                const endTime = new Date();
                const startTime = new Date(callSession.startTime);
                // Calculate duration in seconds
                const durationSeconds = Math.round((endTime.getTime() - startTime.getTime()) / 1000);
                // Calculate minutes used (round up to nearest minute, minimum 1 minute)
                const minutesUsed = Math.max(1, Math.ceil(durationSeconds / 60));
                // Update call session
                callSession.endTime = endTime.toISOString();
                callSession.durationSeconds = durationSeconds;
                callSession.minutesUsed = minutesUsed;
                // Update localStorage
                existingCalls[callIndex] = callSession;
                localStorage.setItem('call_sessions', JSON.stringify(existingCalls));
                // Update user minutes
                const userMinutes = JSON.parse(localStorage.getItem(`user_minutes_${userId}`) || '{"remaining_minutes": 100, "total_minutes_used": 0}');
                userMinutes.remaining_minutes = Math.max(0, userMinutes.remaining_minutes - minutesUsed);
                userMinutes.total_minutes_used = (userMinutes.total_minutes_used || 0) + minutesUsed;
                userMinutes.last_updated = new Date().toISOString();
                localStorage.setItem(`user_minutes_${userId}`, JSON.stringify(userMinutes));
                await logOperation("TRACK_CALL_LOCAL", { userId, action, callId, durationSeconds, minutesUsed }, "SUCCESS");
                return {
                    durationSeconds,
                    minutesUsed,
                    remainingMinutes: userMinutes.remaining_minutes
                };
            }
        }
    }
    catch (error) {
        await logOperation("TRACK_CALL_LOCAL", { userId, action, callId, characterId }, "ERROR", error);
        throw error;
    }
};
// Get user's remaining minutes
export const getRemainingMinutes = async (userId) => {
    try {
        // Log the operation start
        await logOperation("GET_MINUTES_LOCAL", { userId }, "STARTED");
        // Try to use the Edge Function first
        try {
            const { data, error } = await supabase.functions.invoke("user-minutes", {
                method: "GET",
                body: { userId },
            });
            if (error) {
                throw new Error(`Edge Function error: ${error.message}`);
            }
            await logOperation("GET_MINUTES_LOCAL", { userId, result: data }, "SUCCESS");
            return data.remainingMinutes;
        }
        catch (edgeFunctionError) {
            console.warn("Edge Function not available, using local fallback:", edgeFunctionError);
            // Local fallback implementation
            const userMinutes = JSON.parse(localStorage.getItem(`user_minutes_${userId}`) || '{"remaining_minutes": 0}');
            // Log the minutes value for debugging
            console.log(`[LOCAL_FALLBACK] User ${userId} has ${userMinutes.remaining_minutes} minutes remaining`);
            await logOperation("GET_MINUTES_LOCAL", { userId, remainingMinutes: userMinutes.remaining_minutes }, "SUCCESS");
            return userMinutes.remaining_minutes;
        }
    }
    catch (error) {
        await logOperation("GET_MINUTES_LOCAL", { userId }, "ERROR", error);
        return 0; // Default to 0 minutes on error
    }
};
// Add minutes to user's account (simulates successful payment)
export const addMinutes = async (userId, minutesToAdd) => {
    try {
        // Log the operation start
        await logOperation("ADD_MINUTES_LOCAL", { userId, minutesToAdd }, "STARTED");
        // Try to use the Edge Function first
        try {
            const { data, error } = await supabase.functions.invoke("user-minutes", {
                method: "POST",
                body: { userId, minutesAdded: minutesToAdd },
            });
            if (error) {
                throw new Error(`Edge Function error: ${error.message}`);
            }
            await logOperation("ADD_MINUTES_LOCAL", { userId, minutesToAdd, result: data }, "SUCCESS");
            return data.remainingMinutes;
        }
        catch (edgeFunctionError) {
            console.warn("Edge Function not available, using local fallback:", edgeFunctionError);
            // Local fallback implementation
            const userMinutes = JSON.parse(localStorage.getItem(`user_minutes_${userId}`) || '{"remaining_minutes": 0, "total_minutes_purchased": 0}');
            userMinutes.remaining_minutes = (userMinutes.remaining_minutes || 0) + minutesToAdd;
            userMinutes.total_minutes_purchased = (userMinutes.total_minutes_purchased || 0) + minutesToAdd;
            userMinutes.last_updated = new Date().toISOString();
            localStorage.setItem(`user_minutes_${userId}`, JSON.stringify(userMinutes));
            await logOperation("ADD_MINUTES_LOCAL", { userId, minutesToAdd, remainingMinutes: userMinutes.remaining_minutes }, "SUCCESS");
            return userMinutes.remaining_minutes;
        }
    }
    catch (error) {
        await logOperation("ADD_MINUTES_LOCAL", { userId, minutesToAdd }, "ERROR", error);
        throw error;
    }
};
// Initialize user minutes if they don't exist
export const initializeUserMinutes = async (userId, initialMinutes = 0) => {
    try {
        const minutes = await getRemainingMinutes(userId);
        // If minutes are 0, add some initial minutes for testing
        if (minutes === 0) {
            await addMinutes(userId, initialMinutes);
            console.log(`Initialized user ${userId} with ${initialMinutes} minutes for testing`);
        }
        return minutes;
    }
    catch (error) {
        console.error("Error initializing user minutes:", error);
        return 0;
    }
};
