import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { trackCallUsage, addMinutes, initializeUserMinutes } from "@/utils/usageTracking";
import { useToast } from "@/components/ui/use-toast";
import { Timer, Zap, Plus, Play, Square, RotateCcw, Database } from "lucide-react";
const TestUsageTracking = () => {
    const { toast } = useToast();
    const [userId] = useState(() => localStorage.getItem('test_user_id') || crypto.randomUUID());
    const [remainingMinutes, setRemainingMinutes] = useState(0);
    const [isCallActive, setIsCallActive] = useState(false);
    const [currentCallId, setCurrentCallId] = useState(null);
    const [callStartTime, setCallStartTime] = useState(null);
    const [callDuration, setCallDuration] = useState(0);
    const [callHistory, setCallHistory] = useState([]);
    // Save user ID to localStorage for persistence
    useEffect(() => {
        localStorage.setItem('test_user_id', userId);
    }, [userId]);
    // Initialize user minutes
    useEffect(() => {
        const initialize = async () => {
            try {
                const minutes = await initializeUserMinutes(userId);
                setRemainingMinutes(minutes);
                // Load call history from localStorage
                const history = JSON.parse(localStorage.getItem('call_sessions') || '[]');
                const userCalls = history.filter((call) => call.userId === userId);
                setCallHistory(userCalls);
            }
            catch (error) {
                console.error("Error initializing:", error);
            }
        };
        initialize();
    }, [userId]);
    // Update call duration timer
    useEffect(() => {
        let intervalId = null;
        if (isCallActive && callStartTime) {
            intervalId = window.setInterval(() => {
                const currentDuration = Math.floor((Date.now() - callStartTime) / 1000);
                setCallDuration(currentDuration);
            }, 1000);
        }
        return () => {
            if (intervalId !== null) {
                clearInterval(intervalId);
            }
        };
    }, [isCallActive, callStartTime]);
    // Start a call
    const handleStartCall = async () => {
        try {
            const result = await trackCallUsage(userId, "start", undefined, "test-character");
            if (!result?.canStart) {
                toast({
                    title: "Insufficient Minutes",
                    description: "You don't have enough minutes to start a call.",
                    variant: "destructive",
                });
                return;
            }
            setCurrentCallId(result.callId);
            setRemainingMinutes(result.remainingMinutes);
            setIsCallActive(true);
            setCallStartTime(Date.now());
            setCallDuration(0);
            toast({
                title: "Call Started",
                description: "Call tracking has begun.",
            });
        }
        catch (error) {
            console.error("Error starting call:", error);
            toast({
                title: "Error",
                description: "Failed to start call tracking.",
                variant: "destructive",
            });
        }
    };
    // End a call
    const handleEndCall = async () => {
        if (!currentCallId)
            return;
        try {
            const result = await trackCallUsage(userId, "end", currentCallId);
            if (result) {
                setRemainingMinutes(result.remainingMinutes);
                toast({
                    title: "Call Ended",
                    description: `You used ${result.minutesUsed} minute${result.minutesUsed !== 1 ? 's' : ''}. You have ${result.remainingMinutes} minute${result.remainingMinutes !== 1 ? 's' : ''} remaining.`,
                });
                // Update call history
                const history = JSON.parse(localStorage.getItem('call_sessions') || '[]');
                const userCalls = history.filter((call) => call.userId === userId);
                setCallHistory(userCalls);
            }
        }
        catch (error) {
            console.error("Error ending call:", error);
            toast({
                title: "Error",
                description: "Failed to end call tracking.",
                variant: "destructive",
            });
        }
        setIsCallActive(false);
        setCurrentCallId(null);
        setCallStartTime(null);
    };
    // Add minutes
    const handleAddMinutes = async (minutes) => {
        try {
            const newTotal = await addMinutes(userId, minutes);
            setRemainingMinutes(newTotal);
            toast({
                title: "Minutes Added",
                description: `Added ${minutes} minute${minutes !== 1 ? 's' : ''}. You now have ${newTotal} minute${newTotal !== 1 ? 's' : ''}.`,
            });
        }
        catch (error) {
            console.error("Error adding minutes:", error);
            toast({
                title: "Error",
                description: "Failed to add minutes.",
                variant: "destructive",
            });
        }
    };
    // Reset user data (for testing)
    const handleReset = () => {
        localStorage.removeItem(`user_minutes_${userId}`);
        // Filter out this user's calls from call_sessions
        const allCalls = JSON.parse(localStorage.getItem('call_sessions') || '[]');
        const otherCalls = allCalls.filter((call) => call.userId !== userId);
        localStorage.setItem('call_sessions', JSON.stringify(otherCalls));
        setCallHistory([]);
        initializeUserMinutes(userId, 10).then(setRemainingMinutes);
        toast({
            title: "Reset Complete",
            description: "User data has been reset with 10 initial minutes.",
        });
    };
    // Format duration as MM:SS
    const formatDuration = (seconds) => {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    };
    return (_jsx("div", { className: "container mx-auto py-8", children: _jsxs(Card, { className: "max-w-2xl mx-auto bg-gray-900 border-gray-800 text-white", children: [_jsxs(CardHeader, { children: [_jsxs(CardTitle, { className: "text-2xl flex items-center", children: [_jsx(Database, { className: "mr-2 h-5 w-5 text-purple-400" }), "Usage Tracking Test"] }), _jsx(CardDescription, { className: "text-gray-400", children: "Test the payment and usage tracking system" })] }), _jsxs(CardContent, { className: "space-y-6", children: [_jsxs("div", { className: "bg-gray-800 p-4 rounded-md", children: [_jsx("h3", { className: "text-lg font-medium mb-2", children: "User Information" }), _jsxs("div", { className: "grid grid-cols-2 gap-2", children: [_jsxs("div", { children: [_jsx("p", { className: "text-sm text-gray-400", children: "User ID:" }), _jsx("p", { className: "text-xs font-mono text-gray-300 truncate", children: userId })] }), _jsxs("div", { children: [_jsx("p", { className: "text-sm text-gray-400", children: "Remaining Minutes:" }), _jsxs("div", { className: "flex items-center", children: [_jsx(Zap, { className: "h-4 w-4 text-yellow-400 mr-1" }), _jsx("p", { className: "text-xl font-bold text-yellow-300", children: remainingMinutes })] })] })] })] }), _jsxs("div", { className: "bg-gray-800 p-4 rounded-md", children: [_jsx("h3", { className: "text-lg font-medium mb-2", children: "Call Controls" }), _jsxs("div", { className: "flex items-center justify-between", children: [_jsx("div", { children: isCallActive && (_jsxs("div", { className: "flex items-center space-x-2", children: [_jsxs(Badge, { variant: "outline", className: "bg-red-900/30 text-red-400 border-red-700", children: [_jsx("span", { className: "animate-pulse mr-1", children: "\u25CF" }), " LIVE"] }), _jsxs("div", { className: "flex items-center", children: [_jsx(Timer, { className: "h-4 w-4 text-gray-400 mr-1" }), _jsx("span", { className: "text-gray-300", children: formatDuration(callDuration) })] })] })) }), _jsx("div", { className: "flex space-x-2", children: !isCallActive ? (_jsxs(Button, { onClick: handleStartCall, className: "bg-green-600 hover:bg-green-700", disabled: remainingMinutes <= 0, children: [_jsx(Play, { className: "h-4 w-4 mr-1" }), " Start Call"] })) : (_jsxs(Button, { onClick: handleEndCall, className: "bg-red-600 hover:bg-red-700", children: [_jsx(Square, { className: "h-4 w-4 mr-1" }), " End Call"] })) })] })] }), _jsxs("div", { className: "bg-gray-800 p-4 rounded-md", children: [_jsx("h3", { className: "text-lg font-medium mb-2", children: "Add Minutes (Simulate Payment)" }), _jsxs("div", { className: "flex flex-wrap gap-2", children: [_jsxs(Button, { onClick: () => handleAddMinutes(10), variant: "outline", className: "border-purple-700 text-purple-400 hover:bg-purple-900/30", children: [_jsx(Plus, { className: "h-4 w-4 mr-1" }), " 10 Minutes"] }), _jsxs(Button, { onClick: () => handleAddMinutes(30), variant: "outline", className: "border-purple-700 text-purple-400 hover:bg-purple-900/30", children: [_jsx(Plus, { className: "h-4 w-4 mr-1" }), " 30 Minutes"] }), _jsxs(Button, { onClick: () => handleAddMinutes(60), variant: "outline", className: "border-purple-700 text-purple-400 hover:bg-purple-900/30", children: [_jsx(Plus, { className: "h-4 w-4 mr-1" }), " 60 Minutes"] })] })] }), callHistory.length > 0 && (_jsxs("div", { className: "bg-gray-800 p-4 rounded-md", children: [_jsx("h3", { className: "text-lg font-medium mb-2", children: "Call History" }), _jsx("div", { className: "space-y-2", children: callHistory.map((call, index) => (_jsxs("div", { className: "bg-gray-900 p-2 rounded border border-gray-700 text-sm", children: [_jsxs("div", { className: "flex justify-between", children: [_jsx("span", { className: "text-gray-400", children: "Call ID:" }), _jsx("span", { className: "text-gray-300 font-mono text-xs truncate max-w-[200px]", children: call.id })] }), call.startTime && (_jsxs("div", { className: "flex justify-between", children: [_jsx("span", { className: "text-gray-400", children: "Start:" }), _jsx("span", { className: "text-gray-300", children: new Date(call.startTime).toLocaleTimeString() })] })), call.endTime && (_jsxs("div", { className: "flex justify-between", children: [_jsx("span", { className: "text-gray-400", children: "End:" }), _jsx("span", { className: "text-gray-300", children: new Date(call.endTime).toLocaleTimeString() })] })), call.minutesUsed && (_jsxs("div", { className: "flex justify-between", children: [_jsx("span", { className: "text-gray-400", children: "Minutes Used:" }), _jsx("span", { className: "text-yellow-300 font-bold", children: call.minutesUsed })] }))] }, index))) })] }))] }), _jsxs(CardFooter, { className: "flex justify-between border-t border-gray-800 pt-4", children: [_jsxs(Button, { onClick: handleReset, variant: "destructive", size: "sm", children: [_jsx(RotateCcw, { className: "h-4 w-4 mr-1" }), " Reset Data"] }), _jsx("div", { className: "text-xs text-gray-500", children: "Test component for usage tracking" })] })] }) }));
};
export default TestUsageTracking;
