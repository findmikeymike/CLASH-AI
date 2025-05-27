import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle2, XCircle, PlayCircle } from "lucide-react";
import { runPaymentTests } from "@/utils/paymentTests";
const PaymentSystemTests = () => {
    const [isRunning, setIsRunning] = useState(false);
    const [testResults, setTestResults] = useState(null);
    const [error, setError] = useState(null);
    const runTests = async () => {
        setIsRunning(true);
        setError(null);
        setTestResults(null);
        try {
            const results = await runPaymentTests();
            setTestResults(results);
        }
        catch (err) {
            setError(err.message || String(err));
        }
        finally {
            setIsRunning(false);
        }
    };
    return (_jsxs(Card, { className: "bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative", children: [_jsx("div", { className: "absolute inset-0 bg-grid-pattern opacity-5" }), _jsx(CardHeader, { className: "pb-3 border-b border-gray-800 relative z-10", children: _jsxs(CardTitle, { className: "text-lg font-bold flex items-center text-white", children: [_jsx(PlayCircle, { className: "h-5 w-5 mr-2 text-purple-500" }), "Payment System & Token Tracking Tests"] }) }), _jsx(CardContent, { className: "pt-5 relative z-10", children: _jsxs("div", { className: "space-y-6", children: [_jsxs("div", { className: "flex justify-between items-center", children: [_jsx("p", { className: "text-gray-400", children: "Run tests to verify payment system and token tracking functionality" }), _jsx(Button, { onClick: runTests, disabled: isRunning, className: isRunning ? "bg-gray-700" : "bg-purple-600 hover:bg-purple-700", children: isRunning ? (_jsxs(_Fragment, { children: [_jsx(Loader2, { className: "mr-2 h-4 w-4 animate-spin" }), "Running Tests..."] })) : (_jsx(_Fragment, { children: "Run All Tests" })) })] }), error && (_jsxs("div", { className: "bg-red-900/30 border border-red-800 rounded-md p-4 text-red-300", children: [_jsxs("p", { className: "font-medium flex items-center", children: [_jsx(XCircle, { className: "h-5 w-5 mr-2" }), "Error Running Tests"] }), _jsx("p", { className: "mt-2 text-sm", children: error })] })), testResults && (_jsxs("div", { className: "space-y-4", children: [_jsx("div", { className: `p-4 rounded-md border ${testResults.success ? "bg-green-900/30 border-green-800" : "bg-red-900/30 border-red-800"}`, children: _jsx("p", { className: "font-medium flex items-center", children: testResults.success ? (_jsxs(_Fragment, { children: [_jsx(CheckCircle2, { className: "h-5 w-5 mr-2 text-green-500" }), _jsx("span", { className: "text-green-400", children: "All Tests Passed" })] })) : (_jsxs(_Fragment, { children: [_jsx(XCircle, { className: "h-5 w-5 mr-2 text-red-500" }), _jsx("span", { className: "text-red-400", children: "Some Tests Failed" })] })) }) }), _jsx("div", { className: "space-y-3", children: testResults.results.map((result, index) => (_jsxs("div", { className: `p-4 rounded-md border ${result.success ? "bg-gray-800/50 border-gray-700" : "bg-red-900/20 border-red-800/30"}`, children: [_jsxs("div", { className: "flex justify-between items-center", children: [_jsxs("p", { className: "font-medium flex items-center", children: [result.success ? (_jsx(CheckCircle2, { className: "h-4 w-4 mr-2 text-green-500" })) : (_jsx(XCircle, { className: "h-4 w-4 mr-2 text-red-500" })), result.name] }), _jsx(Badge, { variant: result.success ? "outline" : "destructive", className: result.success
                                                            ? "border-green-500 text-green-400"
                                                            : "", children: result.success ? "PASSED" : "FAILED" })] }), _jsx("p", { className: "mt-2 text-sm text-gray-400", children: result.message })] }, index))) }), _jsxs("div", { className: "mt-4 bg-gray-800/50 border border-gray-700 rounded-md p-4", children: [_jsx("p", { className: "font-medium mb-2", children: "Test Summary" }), _jsx("pre", { className: "text-xs text-gray-400 whitespace-pre-wrap", children: testResults.summary })] })] }))] }) })] }));
};
export default PaymentSystemTests;
