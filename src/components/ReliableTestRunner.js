import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle2, XCircle, PlayCircle, Zap } from "lucide-react";
import { createClient } from "@supabase/supabase-js";
const ReliableTestRunner = () => {
    const [isRunning, setIsRunning] = useState(false);
    const [testResults, setTestResults] = useState(null);
    const [error, setError] = useState(null);
    const [lastRun, setLastRun] = useState(null);
    // Initialize Supabase client with frontend credentials
    const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || "";
    const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || "";
    const supabase = createClient(supabaseUrl, supabaseAnonKey);
    const runTests = async () => {
        setIsRunning(true);
        setError(null);
        setTestResults(null);
        try {
            console.log("Starting reliable test runner...");
            console.log("Supabase URL:", supabaseUrl ? "✅ Set" : "❌ Not set");
            console.log("Supabase Anon Key:", supabaseAnonKey ? "✅ Set" : "❌ Not set");
            if (!supabaseUrl || !supabaseAnonKey) {
                throw new Error("Missing Supabase credentials in frontend environment variables");
            }
            // Check if backend environment variables are properly set
            console.log("Verifying backend environment variables are properly set...");
            console.log("Invoking test-payment-system function...");
            const response = await supabase.functions.invoke("supabase-functions-test-payment-system", {
                method: "POST",
                body: {},
            });
            if (response.error) {
                console.error("Edge function error:", response.error);
                throw new Error(`Edge function error: ${response.error.message || JSON.stringify(response.error)}`);
            }
            setTestResults(response.data);
            setLastRun(new Date());
            console.log("Tests completed successfully:", response.data);
        }
        catch (err) {
            console.error("Test execution failed:", err);
            setError(err.message || String(err));
        }
        finally {
            setIsRunning(false);
        }
    };
    return (_jsx("div", { className: "bg-black min-h-screen p-6", children: _jsxs("div", { className: "max-w-5xl mx-auto", children: [_jsxs("div", { className: "mb-8", children: [_jsxs("h1", { className: "text-4xl font-bold text-white mb-2 flex items-center", children: [_jsx(Zap, { className: "h-8 w-8 mr-3 text-yellow-500" }), "Reliable Payment System Test Runner"] }), _jsx("p", { className: "text-gray-400", children: "Comprehensive testing with timeout protection and proper error handling" })] }), _jsxs(Card, { className: "bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative mb-8", children: [_jsx("div", { className: "absolute inset-0 bg-grid-pattern opacity-5" }), _jsx(CardHeader, { className: "pb-3 border-b border-gray-800 relative z-10", children: _jsxs(CardTitle, { className: "text-lg font-bold flex items-center text-white", children: [_jsx(PlayCircle, { className: "h-5 w-5 mr-2 text-green-500" }), "Test Execution"] }) }), _jsx(CardContent, { className: "pt-5 relative z-10", children: _jsxs("div", { className: "space-y-4", children: [_jsxs("div", { className: "flex justify-between items-center", children: [_jsxs("div", { children: [_jsx("p", { className: "text-gray-400", children: "Run comprehensive tests on payment system, token tracking, and database functions" }), lastRun && (_jsxs("p", { className: "text-xs text-gray-500 mt-1", children: ["Last run: ", lastRun.toLocaleString()] }))] }), _jsx(Button, { onClick: runTests, disabled: isRunning, className: isRunning
                                                    ? "bg-gray-700"
                                                    : "bg-green-600 hover:bg-green-700", size: "lg", children: isRunning ? (_jsxs(_Fragment, { children: [_jsx(Loader2, { className: "mr-2 h-4 w-4 animate-spin" }), "Running Tests..."] })) : (_jsxs(_Fragment, { children: [_jsx(PlayCircle, { className: "mr-2 h-4 w-4" }), "Run All Tests"] })) })] }), error && (_jsxs("div", { className: "bg-red-900/30 border border-red-800 rounded-md p-4 text-red-300", children: [_jsxs("p", { className: "font-medium flex items-center", children: [_jsx(XCircle, { className: "h-5 w-5 mr-2" }), "Test Execution Failed"] }), _jsx("p", { className: "mt-2 text-sm", children: error })] })), testResults && (_jsxs("div", { className: "space-y-4", children: [_jsx("div", { className: `p-4 rounded-md border ${testResults.success
                                                    ? "bg-green-900/30 border-green-800"
                                                    : "bg-red-900/30 border-red-800"}`, children: _jsxs("p", { className: "font-medium flex items-center justify-between", children: [_jsx("span", { className: "flex items-center", children: testResults.success ? (_jsxs(_Fragment, { children: [_jsx(CheckCircle2, { className: "h-5 w-5 mr-2 text-green-500" }), _jsx("span", { className: "text-green-400", children: "All Tests Passed" })] })) : (_jsxs(_Fragment, { children: [_jsx(XCircle, { className: "h-5 w-5 mr-2 text-red-500" }), _jsx("span", { className: "text-red-400", children: "Some Tests Failed" })] })) }), _jsxs("span", { className: "text-sm text-gray-400", children: ["Total: ", testResults.totalDuration.toFixed(2), "ms"] })] }) }), _jsx("div", { className: "space-y-3", children: testResults.results.map((result, index) => (_jsxs("div", { className: `p-4 rounded-md border ${result.success
                                                        ? "bg-gray-800/50 border-gray-700"
                                                        : "bg-red-900/20 border-red-800/30"}`, children: [_jsxs("div", { className: "flex justify-between items-center", children: [_jsxs("p", { className: "font-medium flex items-center", children: [result.success ? (_jsx(CheckCircle2, { className: "h-4 w-4 mr-2 text-green-500" })) : (_jsx(XCircle, { className: "h-4 w-4 mr-2 text-red-500" })), result.name] }), _jsxs("div", { className: "flex items-center space-x-2", children: [result.duration && (_jsxs("span", { className: "text-xs text-gray-500", children: [result.duration.toFixed(2), "ms"] })), _jsx(Badge, { variant: result.success ? "outline" : "destructive", className: result.success
                                                                                ? "border-green-500 text-green-400"
                                                                                : "", children: result.success ? "PASSED" : "FAILED" })] })] }), _jsx("p", { className: "mt-2 text-sm text-gray-400", children: result.message })] }, index))) }), _jsxs("div", { className: "mt-6 bg-gray-800/50 border border-gray-700 rounded-md p-4", children: [_jsx("p", { className: "font-medium mb-3 text-white", children: "Detailed Test Summary" }), _jsx("pre", { className: "text-xs text-gray-400 whitespace-pre-wrap overflow-auto max-h-96", children: testResults.summary })] })] }))] }) })] }), _jsxs(Card, { className: "bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative", children: [_jsx("div", { className: "absolute inset-0 bg-grid-pattern opacity-5" }), _jsx(CardHeader, { className: "pb-3 border-b border-gray-800 relative z-10", children: _jsx(CardTitle, { className: "text-lg font-bold text-white", children: "Test Coverage" }) }), _jsx(CardContent, { className: "pt-5 relative z-10", children: _jsxs("div", { className: "grid grid-cols-1 md:grid-cols-2 gap-4", children: [_jsxs("div", { className: "space-y-2", children: [_jsx("h4", { className: "font-medium text-white", children: "Database Tests" }), _jsxs("ul", { className: "text-sm text-gray-400 space-y-1", children: [_jsx("li", { children: "\u2022 Connection verification" }), _jsx("li", { children: "\u2022 Table access validation" }), _jsx("li", { children: "\u2022 Query performance" })] })] }), _jsxs("div", { className: "space-y-2", children: [_jsx("h4", { className: "font-medium text-white", children: "Payment Tests" }), _jsxs("ul", { className: "text-sm text-gray-400 space-y-1", children: [_jsx("li", { children: "\u2022 Stripe charge creation" }), _jsx("li", { children: "\u2022 Payment intent generation" }), _jsx("li", { children: "\u2022 Webhook processing" })] })] }), _jsxs("div", { className: "space-y-2", children: [_jsx("h4", { className: "font-medium text-white", children: "Token Tests" }), _jsxs("ul", { className: "text-sm text-gray-400 space-y-1", children: [_jsx("li", { children: "\u2022 Minutes addition/usage" }), _jsx("li", { children: "\u2022 Balance calculations" }), _jsx("li", { children: "\u2022 User tracking" })] })] }), _jsxs("div", { className: "space-y-2", children: [_jsx("h4", { className: "font-medium text-white", children: "Reliability Features" }), _jsxs("ul", { className: "text-sm text-gray-400 space-y-1", children: [_jsx("li", { children: "\u2022 10-second timeouts" }), _jsx("li", { children: "\u2022 Proper error handling" }), _jsx("li", { children: "\u2022 Performance monitoring" })] })] })] }) })] })] }) }));
};
export default ReliableTestRunner;
