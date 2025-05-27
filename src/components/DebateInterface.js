import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Timer, Zap, AlertCircle } from "lucide-react";
import { motion } from "framer-motion";
import { useToast } from "@/components/ui/use-toast";
import { trackCallUsage, initializeUserMinutes } from "@/utils/usageTracking";
// Load ElevenLabs widget script
if (typeof window !== "undefined" &&
    !document.querySelector('script[src="https://elevenlabs.io/convai-widget/index.js"]')) {
    const script = document.createElement("script");
    script.src = "https://elevenlabs.io/convai-widget/index.js";
    script.async = true;
    script.type = "text/javascript";
    document.head.appendChild(script);
    // Add network request interceptor for tracking API calls
    const originalFetch = window.fetch;
    window.fetch = async function (...args) {
        const url = args[0];
        if (typeof url === "string" && url.includes("elevenlabs.io")) {
            const startTime = performance.now();
            console.log(`ElevenLabs API call started: ${url}`);
            try {
                const response = await originalFetch.apply(this, args);
                const endTime = performance.now();
                const duration = endTime - startTime;
                console.log(`ElevenLabs API call completed: ${url}, duration: ${duration}ms`);
                // Dispatch a custom event with the call duration
                window.dispatchEvent(new CustomEvent("elevenlabs-api-call", {
                    detail: { duration, url },
                }));
                return response;
            }
            catch (error) {
                console.error("Error intercepting ElevenLabs API call:", error);
                throw error;
            }
        }
        return originalFetch.apply(this, args);
    };
}
const DebateInterface = ({ character, onBack = () => { }, onDebateEnd = () => { }, tokenBalance = 0, // Default to 0 instead of 100
onTokensUsed = () => { }, }) => {
    const { toast } = useToast();
    const [isWidgetLoaded, setIsWidgetLoaded] = useState(false);
    const [isWidgetLoading, setIsWidgetLoading] = useState(true);
    const [sessionStartTime, setSessionStartTime] = useState(null);
    const [widgetLoadTime, setWidgetLoadTime] = useState(null);
    const [responseCount, setResponseCount] = useState(0);
    const [sessionDuration, setSessionDuration] = useState(0);
    const sessionTimerRef = useRef(null);
    const [isDebateActive, setIsDebateActive] = useState(false);
    const [isCallActive, setIsCallActive] = useState(false);
    const [apiCallTimes, setApiCallTimes] = useState([]);
    const [totalApiCallTime, setTotalApiCallTime] = useState(0);
    const [estimatedTokenUsage, setEstimatedTokenUsage] = useState(0);
    const [remainingMinutes, setRemainingMinutes] = useState(null);
    const [currentCallId, setCurrentCallId] = useState(null);
    const [insufficientMinutes, setInsufficientMinutes] = useState(false);
    const userId = useRef(crypto.randomUUID()); // Generate a temporary user ID if not authenticated
    // Initialize user minutes when component mounts
    useEffect(() => {
        const initMinutes = async () => {
            try {
                console.log("Initializing user minutes for ID:", userId.current);
                // Initialize user minutes and get the current balance
                const minutes = await initializeUserMinutes(userId.current);
                console.log("Minutes initialized:", minutes);
                setRemainingMinutes(minutes);
                // Store in localStorage as fallback
                localStorage.setItem(`user_minutes_${userId.current}`, String(minutes));
            }
            catch (error) {
                console.error("Error initializing minutes:", error);
                // If there's an error, we'll use the default value from local storage
                const localMinutes = localStorage.getItem(`user_minutes_${userId.current}`);
                if (localMinutes) {
                    setRemainingMinutes(parseInt(localMinutes, 10));
                }
                else {
                    // Default to 0 if no minutes are found
                    setRemainingMinutes(0);
                    localStorage.setItem(`user_minutes_${userId.current}`, "0");
                }
            }
        };
        initMinutes();
    }, []);
    // Placeholder for the actual widget load
    useEffect(() => {
        if (!character)
            return;
        const startTime = performance.now();
        setIsWidgetLoading(true);
        // Simulate widget loading
        const loadTimeout = setTimeout(() => {
            setIsWidgetLoaded(true);
            setIsWidgetLoading(false);
            const endTime = performance.now();
            setWidgetLoadTime(endTime - startTime);
        }, 2000); // Simulating 2 second load time
        return () => clearTimeout(loadTimeout);
    }, [character]);
    // Fetch user's remaining minutes when component mounts
    useEffect(() => {
        const fetchRemainingMinutes = async () => {
            try {
                // Initialize user with some minutes for testing if needed
                const minutes = await initializeUserMinutes(userId.current);
                setRemainingMinutes(minutes);
            }
            catch (error) {
                console.error("Error fetching minutes:", error);
                // Set a default value to prevent UI issues
                setRemainingMinutes(10);
            }
        };
        fetchRemainingMinutes();
    }, []);
    useEffect(() => {
        const handleApiCall = (event) => {
            const { duration, url } = event.detail;
            // Update API call times
            setApiCallTimes((prev) => [...prev, duration]);
            // Update total API call time
            setTotalApiCallTime((prev) => prev + duration);
            // Update response count if this is a new response
            if (url.includes("/history/") || url.includes("/stream")) {
                setResponseCount((prev) => prev + 1);
            }
            console.log(`API call to ${url} took ${duration}ms.`);
        };
        // Add event listener for our custom event
        window.addEventListener("elevenlabs-api-call", handleApiCall);
        return () => {
            window.removeEventListener("elevenlabs-api-call", handleApiCall);
        };
    }, []);
    // Start session timer when debate becomes active
    useEffect(() => {
        if (isDebateActive && !sessionStartTime) {
            setSessionStartTime(performance.now());
        }
        // Update session duration every second
        let intervalId = null;
        if (isDebateActive && sessionStartTime) {
            intervalId = window.setInterval(() => {
                const currentDuration = Math.floor((performance.now() - sessionStartTime) / 1000);
                setSessionDuration(currentDuration);
            }, 1000);
        }
        return () => {
            if (intervalId !== null) {
                clearInterval(intervalId);
            }
        };
    }, [isDebateActive, sessionStartTime]);
    // Handle call start and end with robust tracking
    useEffect(() => {
        const handleCallStateChange = async () => {
            if (!character)
                return;
            if (isCallActive && !currentCallId) {
                // Call started
                try {
                    // Use our utility that handles both Edge Function and local fallback
                    const result = await trackCallUsage(userId.current, "start", undefined, character.id);
                    if (!result?.canStart) {
                        // User doesn't have enough minutes
                        setInsufficientMinutes(true);
                        toast({
                            title: "Insufficient Minutes",
                            description: "You don't have enough minutes to start a call. Please purchase more minutes.",
                            variant: "destructive",
                        });
                        // Force end the call - this is a workaround since we can't directly control the widget
                        // In a production environment, you would use the ElevenLabs API directly
                        try {
                            const convaiElement = document.querySelector("elevenlabs-convai");
                            if (convaiElement && typeof convaiElement.endCall === "function") {
                                convaiElement.endCall();
                            }
                        }
                        catch (error) {
                            console.error("Error ending call:", error);
                        }
                        return;
                    }
                    setCurrentCallId(result.callId);
                    setRemainingMinutes(result.remainingMinutes);
                }
                catch (error) {
                    console.error("Error starting call tracking:", error);
                    // Set a default call ID to allow the call to proceed even if tracking fails
                    setCurrentCallId(crypto.randomUUID());
                }
            }
            else if (!isCallActive && currentCallId) {
                // Call ended
                try {
                    // Use our utility that handles both Edge Function and local fallback
                    const result = await trackCallUsage(userId.current, "end", currentCallId);
                    if (result) {
                        // Update remaining minutes
                        setRemainingMinutes(result.remainingMinutes);
                        // Notify parent component about minutes used
                        onTokensUsed(result.minutesUsed);
                        // Show toast with usage information
                        toast({
                            title: "Call Ended",
                            description: `You used ${result.minutesUsed} minute${result.minutesUsed !== 1 ? 's' : ''}. You have ${result.remainingMinutes} minute${result.remainingMinutes !== 1 ? 's' : ''} remaining.`,
                        });
                        // Reset current call ID
                        setCurrentCallId(null);
                    }
                }
                catch (error) {
                    console.error("Error ending call tracking:", error);
                    // Reset current call ID even if tracking fails
                    setCurrentCallId(null);
                }
            }
        };
        handleCallStateChange();
    }, [isCallActive, currentCallId, character, toast, onTokensUsed]);
    const handleEndDebate = async () => {
        // If there's an active call, end it first
        if (currentCallId) {
            try {
                // Use our utility that handles both Edge Function and local fallback
                const result = await trackCallUsage(userId.current, "end", currentCallId);
                if (result) {
                    setRemainingMinutes(result.remainingMinutes);
                    onTokensUsed(result.minutesUsed);
                }
            }
            catch (error) {
                console.error("Error ending call tracking:", error);
            }
        }
        // Calculate final metrics
        const metrics = {
            widgetLoadTime: widgetLoadTime || 0,
            sessionDuration,
            responseCount,
            averageResponseTime: responseCount > 0
                ? apiCallTimes.reduce((sum, time) => sum + time, 0) / responseCount
                : 0,
            tokenUsage: estimatedTokenUsage,
            totalApiCallTime,
        };
        // Call the onDebateEnd callback with metrics
        onDebateEnd(metrics);
        // Reset state for next debate
        setSessionStartTime(null);
        setSessionDuration(0);
        setResponseCount(0);
        setApiCallTimes([]);
        setTotalApiCallTime(0);
        setEstimatedTokenUsage(0);
        setCurrentCallId(null);
    };
    if (!character) {
        return (_jsxs("div", { className: "min-h-screen bg-black text-white flex items-center justify-center relative overflow-hidden", children: [_jsx("div", { className: "absolute inset-0 bg-gradient-to-br from-purple-900/30 via-black to-pink-900/20" }), _jsx("div", { className: "absolute inset-0 bg-grid-pattern opacity-15" }), _jsx(motion.div, { initial: { opacity: 0, scale: 0.9 }, animate: { opacity: 1, scale: 1 }, transition: { duration: 0.5 }, className: "relative z-10 w-full max-w-md", children: _jsx(Card, { className: "bg-gray-900 border border-purple-500/30 shadow-lg shadow-purple-500/10", children: _jsxs(CardContent, { className: "p-6", children: [_jsx("p", { className: "text-center text-gray-400", children: "No character selected. Please go back and select a character." }), _jsx(Button, { className: "w-full mt-4 bg-red-600 hover:bg-red-700 text-white font-bold border-2 border-red-500 shadow-lg", onClick: onBack, children: "Back to Characters" })] }) }) })] }));
    }
    return (_jsxs("div", { className: "min-h-screen bg-black text-white relative overflow-hidden", children: [_jsx("div", { className: "absolute inset-0 bg-gradient-to-br from-purple-900/30 via-black to-pink-900/20" }), _jsx("div", { className: "absolute inset-0 bg-grid-pattern opacity-15" }), _jsx("div", { className: "absolute inset-0 bg-gradient-to-r from-purple-600/5 via-transparent to-red-600/5" }), _jsxs("header", { className: "relative z-50 flex items-center justify-between p-6", children: [_jsx(Button, { variant: "outline", size: "icon", onClick: onBack, className: "bg-red-600 text-white border-red-600 hover:bg-red-700 hover:border-red-700 rounded-lg transition-colors shadow-xl z-50 relative", children: _jsx(ArrowLeft, { className: "h-5 w-5" }) }), _jsxs("div", { className: "flex items-center space-x-4", children: [_jsxs("div", { className: "flex items-center space-x-2 bg-gradient-to-r from-gray-900/80 to-black/80 backdrop-blur-sm px-4 py-2 rounded-lg border border-gray-800 shadow-md", children: [_jsx(Timer, { className: "h-4 w-4 text-gray-400" }), _jsxs("span", { className: "text-gray-400 text-sm", children: [Math.floor(sessionDuration / 60), ":", String(sessionDuration % 60).padStart(2, "0")] })] }), _jsxs("div", { className: "flex items-center space-x-2", children: [_jsx(Zap, { className: "h-4 w-4 text-yellow-400" }), _jsx("span", { className: `text-sm ${remainingMinutes !== null && remainingMinutes < 5 ? 'text-red-400' : 'text-gray-400'}`, children: remainingMinutes !== null
                                            ? `${remainingMinutes} minute${remainingMinutes !== 1 ? 's' : ''} left`
                                            : "Loading..." })] }), insufficientMinutes && (_jsxs("div", { className: "flex items-center space-x-2 ml-4", children: [_jsx(AlertCircle, { className: "h-4 w-4 text-red-500" }), _jsx("span", { className: "text-red-400 text-sm", children: "Insufficient minutes" })] }))] })] }), _jsxs("div", { className: "relative z-10 h-[calc(100vh-120px)]", children: [_jsx("div", { className: "absolute top-16 left-1/2 transform -translate-x-1/2 z-20", children: _jsx(motion.div, { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.5 }, className: "text-center", children: _jsxs("div", { className: "relative inline-block mb-8", children: [_jsx("div", { className: "absolute -inset-4 bg-gradient-to-r from-red-600 to-red-500 rounded-full blur opacity-70" }), _jsxs(Avatar, { className: "h-[48rem] w-[48rem] ring-8 ring-red-500/50 relative", children: [_jsx(AvatarImage, { src: character.avatarUrl, alt: character.name, className: "object-cover", style: { objectPosition: "center 20%" } }), _jsx(AvatarFallback, { className: "bg-gradient-to-br from-gray-800 to-gray-900 text-red-400 text-[12rem]", children: character.name.substring(0, 2).toUpperCase() })] })] }) }) }), _jsx("div", { className: "absolute top-[56rem] left-1/2 transform -translate-x-1/2 z-20", children: _jsxs(motion.div, { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.5, delay: 0.2 }, className: "text-center", children: [_jsx("h2", { className: "text-4xl font-bold mb-3 text-white", children: character.name }), _jsx("p", { className: "text-gray-400 text-center mb-4 max-w-lg mx-auto text-lg", children: character.description }), _jsx("div", { className: "flex flex-wrap gap-2 justify-center", children: character.expertise.slice(0, 3).map((skill, index) => (_jsx(Badge, { variant: "secondary", className: "text-sm bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors px-3 py-1", children: skill }, index))) })] }) }), _jsx("div", { className: "absolute inset-0 flex items-center justify-center", children: isWidgetLoading ? (_jsxs(motion.div, { initial: { opacity: 0 }, animate: { opacity: 1 }, transition: { duration: 0.5 }, className: "text-center", children: [_jsx("div", { className: "inline-block h-10 w-10 animate-spin rounded-full border-4 border-solid border-purple-500 border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" }), _jsx("p", { className: "mt-4 text-purple-300", children: "Loading voice interface..." })] })) : (_jsx(motion.div, { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.5 }, children: _jsx("elevenlabs-convai", { "agent-id": character.id === "1"
                                    ? "Q28tIEHppUH7QKPS9DDQ" // Caleb
                                    : character.id === "9"
                                        ? "I00LvO5VixzhKiPFbkZr" // Tom
                                        : character.id === "10"
                                            ? "5MNvV1hW3kIwuaOmTghn" // Zeek
                                            : character.id === "11"
                                                ? "WIKK4mk7sQrxtRQyTRFd" // Chad
                                                : character.id === "12"
                                                    ? "agent_01jw5d4dvkeh58e8g37cwbnq36" // Sarah - female voice
                                                    : character.id === "13"
                                                        ? "agent_01jw5dh60ae0ktf5s0m75rxhk3" // Karen - female voice
                                                        : character.id === "14"
                                                            ? "agent_01jw5ebv44fc7v1re4a3dzr0bf" // Theo
                                                            : character.id === "15"
                                                                ? "agent_01jw5f1qm1ft0rg27rdw1tjbec" // Father Augustine
                                                                : character.id === "16"
                                                                    ? "agent_01jw5g3rx6e9nsgmvtpzj478rk" // Lexi the Liberated
                                                                    : character.id === "17"
                                                                        ? "8x2LZsG2jkkgIW7fqlRK" // Professor Beckley
                                                                        : "5MNvV1hW3kIwuaOmTghn", onCallStart: async () => {
                                    console.log("ElevenLabs call started");
                                    setIsCallActive(true);
                                    // Check if user has minutes before starting call
                                    if (remainingMinutes !== null && remainingMinutes <= 0) {
                                        console.log("Insufficient minutes to start call:", remainingMinutes);
                                        toast({
                                            title: "Insufficient Minutes",
                                            description: "You don't have enough minutes to start a call. Please purchase more minutes to continue.",
                                            variant: "destructive",
                                        });
                                        setInsufficientMinutes(true);
                                        return;
                                    }
                                    // Track call start with our usage tracking system
                                    try {
                                        console.log("Tracking call start for user:", userId.current);
                                        const result = await trackCallUsage(userId.current, "start", undefined, character.id);
                                        console.log("Call start result:", result);
                                        if (!result?.canStart) {
                                            toast({
                                                title: "Insufficient Minutes",
                                                description: "You don't have enough minutes to start a call.",
                                                variant: "destructive",
                                            });
                                            setInsufficientMinutes(true);
                                            return;
                                        }
                                        setCurrentCallId(result.callId);
                                        setRemainingMinutes(result.remainingMinutes);
                                        // Update local storage with new minutes
                                        localStorage.setItem(`user_minutes_${userId.current}`, String(result.remainingMinutes));
                                        // Start the session timer
                                        setSessionStartTime(Date.now());
                                        setSessionDuration(0); // Reset timer to 0
                                        const timerInterval = setInterval(() => {
                                            setSessionDuration(prev => prev + 1);
                                        }, 1000);
                                        // Store the interval ID for cleanup
                                        sessionTimerRef.current = timerInterval;
                                    }
                                    catch (error) {
                                        console.error("Error tracking call start:", error);
                                        toast({
                                            title: "Error",
                                            description: "Failed to start call tracking.",
                                            variant: "destructive",
                                        });
                                    }
                                }, onCallEnd: async () => {
                                    console.log("ElevenLabs call ended");
                                    setIsCallActive(false);
                                    // Track call end with our usage tracking system
                                    if (currentCallId) {
                                        try {
                                            const result = await trackCallUsage(userId.current, "end", currentCallId);
                                            if (result) {
                                                setRemainingMinutes(result.remainingMinutes);
                                                toast({
                                                    title: "Call Ended",
                                                    description: `You used ${result.minutesUsed} minute${result.minutesUsed !== 1 ? 's' : ''}. You have ${result.remainingMinutes} minute${result.remainingMinutes !== 1 ? 's' : ''} remaining.`,
                                                });
                                            }
                                        }
                                        catch (error) {
                                            console.error("Error tracking call end:", error);
                                            toast({
                                                title: "Error",
                                                description: "Failed to end call tracking.",
                                                variant: "destructive",
                                            });
                                        }
                                        // Clear the session timer
                                        if (sessionTimerRef.current) {
                                            clearInterval(sessionTimerRef.current);
                                            sessionTimerRef.current = null;
                                        }
                                        setCurrentCallId(null);
                                    }
                                }, onError: (error) => {
                                    console.error("ElevenLabs call error:", error);
                                    toast({
                                        title: "Call Error",
                                        description: "There was an error with the voice call. Please try again.",
                                        variant: "destructive",
                                    });
                                } }) })) })] })] }));
};
export default DebateInterface;
