import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle2, XCircle, Activity } from "lucide-react";
import { checkPaymentSystemHealth } from "@/utils/paymentSystemHealth";
const PaymentSystemHealth = () => {
    const [isChecking, setIsChecking] = useState(false);
    const [healthStatus, setHealthStatus] = useState(null);
    const [error, setError] = useState(null);
    const [lastChecked, setLastChecked] = useState(null);
    // Run health check on component mount
    useEffect(() => {
        runHealthCheck();
    }, []);
    const runHealthCheck = async () => {
        setIsChecking(true);
        setError(null);
        try {
            const status = await checkPaymentSystemHealth();
            setHealthStatus(status);
            setLastChecked(new Date());
        }
        catch (err) {
            setError(err.message || String(err));
        }
        finally {
            setIsChecking(false);
        }
    };
    return (_jsxs(Card, { className: "bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative", children: [_jsx("div", { className: "absolute inset-0 bg-grid-pattern opacity-5" }), _jsx(CardHeader, { className: "pb-3 border-b border-gray-800 relative z-10", children: _jsxs(CardTitle, { className: "text-lg font-bold flex items-center text-white", children: [_jsx(Activity, { className: "h-5 w-5 mr-2 text-blue-500" }), "Payment System Health"] }) }), _jsx(CardContent, { className: "pt-5 relative z-10", children: _jsxs("div", { className: "space-y-6", children: [_jsxs("div", { className: "flex justify-between items-center", children: [_jsxs("div", { children: [_jsx("p", { className: "text-gray-400", children: "System health status" }), lastChecked && (_jsxs("p", { className: "text-xs text-gray-500 mt-1", children: ["Last checked: ", lastChecked.toLocaleTimeString()] }))] }), _jsx(Button, { onClick: runHealthCheck, disabled: isChecking, className: isChecking ? "bg-gray-700" : "bg-blue-600 hover:bg-blue-700", size: "sm", children: isChecking ? (_jsxs(_Fragment, { children: [_jsx(Loader2, { className: "mr-2 h-4 w-4 animate-spin" }), "Checking..."] })) : (_jsx(_Fragment, { children: "Refresh Status" })) })] }), error && (_jsxs("div", { className: "bg-red-900/30 border border-red-800 rounded-md p-4 text-red-300", children: [_jsxs("p", { className: "font-medium flex items-center", children: [_jsx(XCircle, { className: "h-5 w-5 mr-2" }), "Error Checking Health"] }), _jsx("p", { className: "mt-2 text-sm", children: error })] })), healthStatus && (_jsxs("div", { className: "space-y-4", children: [_jsx("div", { className: `p-4 rounded-md border ${healthStatus.healthy ? "bg-green-900/30 border-green-800" : "bg-red-900/30 border-red-800"}`, children: _jsx("p", { className: "font-medium flex items-center", children: healthStatus.healthy ? (_jsxs(_Fragment, { children: [_jsx(CheckCircle2, { className: "h-5 w-5 mr-2 text-green-500" }), _jsx("span", { className: "text-green-400", children: "All Systems Operational" })] })) : (_jsxs(_Fragment, { children: [_jsx(XCircle, { className: "h-5 w-5 mr-2 text-red-500" }), _jsx("span", { className: "text-red-400", children: "System Degradation Detected" })] })) }) }), _jsx("div", { className: "space-y-3", children: healthStatus.results.map((result, index) => (_jsxs("div", { className: `p-4 rounded-md border ${result.healthy ? "bg-gray-800/50 border-gray-700" : "bg-red-900/20 border-red-800/30"}`, children: [_jsxs("div", { className: "flex justify-between items-center", children: [_jsxs("p", { className: "font-medium flex items-center", children: [result.healthy ? (_jsx(CheckCircle2, { className: "h-4 w-4 mr-2 text-green-500" })) : (_jsx(XCircle, { className: "h-4 w-4 mr-2 text-red-500" })), result.component] }), _jsx(Badge, { variant: result.healthy ? "outline" : "destructive", className: result.healthy
                                                            ? "border-green-500 text-green-400"
                                                            : "", children: result.healthy ? "HEALTHY" : "DEGRADED" })] }), _jsx("p", { className: "mt-2 text-sm text-gray-400", children: result.message })] }, index))) })] }))] }) })] }));
};
export default PaymentSystemHealth;
