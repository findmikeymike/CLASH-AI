import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Clock, Zap, MessageCircle, BarChart3 } from "lucide-react";
import { motion } from "framer-motion";
const PerformanceMetrics = ({ metrics = {
    widgetLoadTime: 1200,
    sessionDuration: 180,
    responseCount: 12,
    averageResponseTime: 15,
    tokenUsage: 150,
    totalApiCallTime: 8000,
}, }) => {
    // Calculate performance scores (simplified example)
    const loadTimeScore = Math.max(0, 100 - metrics.widgetLoadTime / 50);
    const responseTimeScore = Math.max(0, 100 - metrics.averageResponseTime * 2);
    // Format time in seconds with ms
    const formatTime = (ms) => {
        if (ms < 1000)
            return `${ms.toFixed(0)}ms`;
        return `${(ms / 1000).toFixed(2)}s`;
    };
    // Format duration in minutes and seconds
    const formatDuration = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}m ${secs}s`;
    };
    const cardVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: (i) => ({
            opacity: 1,
            y: 0,
            transition: {
                delay: i * 0.1,
                duration: 0.5,
            },
        }),
    };
    return (_jsxs("div", { className: "w-full bg-black text-white p-6 relative overflow-hidden", children: [_jsxs("div", { className: "absolute inset-0 z-0", children: [_jsx("div", { className: "absolute inset-0 bg-gradient-to-br from-purple-900/30 via-black to-pink-900/20 z-10" }), _jsx("div", { className: "absolute top-0 left-0 right-0 h-full bg-grid-pattern opacity-15" }), _jsx("div", { className: "absolute inset-0 bg-gradient-to-r from-purple-600/5 via-transparent to-red-600/5" })] }), _jsxs("div", { className: "relative z-10", children: [_jsxs("div", { className: "bg-gradient-to-br from-gray-900 to-black border border-gray-800 rounded-2xl p-10 mb-12 shadow-2xl relative overflow-hidden", children: [_jsx("div", { className: "absolute inset-0 bg-grid-pattern opacity-5" }), _jsxs("div", { className: "relative z-10", children: [_jsx(motion.h2, { initial: { opacity: 0, y: -20 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.6 }, className: "text-4xl md:text-6xl font-black mb-4 text-center text-white", children: "Debate Performance" }), _jsx("p", { className: "text-xl text-gray-400 text-center", children: "Your battle statistics and achievements" })] })] }), _jsxs("div", { className: "grid grid-cols-1 md:grid-cols-2 gap-6", children: [_jsx(motion.div, { custom: 0, initial: "hidden", animate: "visible", variants: cardVariants, children: _jsxs(Card, { className: "bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative group hover:border-red-500/30 transition-colors duration-300", children: [_jsx("div", { className: "absolute inset-0 bg-grid-pattern opacity-5" }), _jsx(CardHeader, { className: "pb-3 border-b border-gray-800 relative z-10", children: _jsxs(CardTitle, { className: "text-sm font-bold flex items-center text-white", children: [_jsx("div", { className: "bg-yellow-500/10 p-1.5 rounded-md mr-2", children: _jsx(Zap, { className: "h-4 w-4 text-yellow-500" }) }), "Widget Load Time"] }) }), _jsxs(CardContent, { className: "pt-5 relative z-10", children: [_jsx("div", { className: "text-3xl font-bold text-white mb-3", children: formatTime(metrics.widgetLoadTime) }), _jsx(Progress, { className: "h-2 mt-2", value: loadTimeScore, className: "bg-gray-800 h-2 mt-2 rounded-full", indicatorClassName: "bg-gradient-to-r from-yellow-500 to-yellow-400 rounded-full" }), _jsx("p", { className: "text-sm text-gray-400 mt-3 font-medium", children: loadTimeScore >= 80
                                                        ? "Excellent"
                                                        : loadTimeScore >= 60
                                                            ? "Good"
                                                            : "Needs improvement" })] })] }) }), _jsx(motion.div, { custom: 1, initial: "hidden", animate: "visible", variants: cardVariants, children: _jsxs(Card, { className: "bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative group hover:border-red-500/30 transition-colors duration-300", children: [_jsx("div", { className: "absolute inset-0 bg-grid-pattern opacity-5" }), _jsx(CardHeader, { className: "pb-3 border-b border-gray-800 relative z-10", children: _jsxs(CardTitle, { className: "text-sm font-bold flex items-center text-white", children: [_jsx("div", { className: "bg-blue-500/10 p-1.5 rounded-md mr-2", children: _jsx(Clock, { className: "h-4 w-4 text-blue-500" }) }), "Session Duration"] }) }), _jsxs(CardContent, { className: "pt-5 relative z-10", children: [_jsx("div", { className: "text-3xl font-bold text-white mb-3", children: formatDuration(metrics.sessionDuration) }), _jsx("div", { className: "text-sm text-gray-400 font-medium", children: "Total debate time" })] })] }) }), _jsx(motion.div, { custom: 2, initial: "hidden", animate: "visible", variants: cardVariants, children: _jsxs(Card, { className: "bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative group hover:border-red-500/30 transition-colors duration-300", children: [_jsx("div", { className: "absolute inset-0 bg-grid-pattern opacity-5" }), _jsx(CardHeader, { className: "pb-3 border-b border-gray-800 relative z-10", children: _jsxs(CardTitle, { className: "text-sm font-bold flex items-center text-white", children: [_jsx("div", { className: "bg-green-500/10 p-1.5 rounded-md mr-2", children: _jsx(MessageCircle, { className: "h-4 w-4 text-green-500" }) }), "AI Responses"] }) }), _jsxs(CardContent, { className: "pt-5 relative z-10", children: [_jsx("div", { className: "text-3xl font-bold text-white mb-3", children: metrics.responseCount }), _jsx("div", { className: "text-sm text-gray-400 font-medium", children: "Total responses from AI" })] })] }) }), _jsx(motion.div, { custom: 3, initial: "hidden", animate: "visible", variants: cardVariants, children: _jsxs(Card, { className: "bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative group hover:border-red-500/30 transition-colors duration-300", children: [_jsx("div", { className: "absolute inset-0 bg-grid-pattern opacity-5" }), _jsx(CardHeader, { className: "pb-3 border-b border-gray-800 relative z-10", children: _jsxs(CardTitle, { className: "text-sm font-bold flex items-center text-white", children: [_jsx("div", { className: "bg-red-500/10 p-1.5 rounded-md mr-2", children: _jsx(BarChart3, { className: "h-4 w-4 text-red-500" }) }), "Avg. Response Time"] }) }), _jsxs(CardContent, { className: "pt-5 relative z-10", children: [_jsxs("div", { className: "text-3xl font-bold text-white mb-3", children: [metrics.averageResponseTime.toFixed(1), "s"] }), _jsx(Progress, { className: "h-2 mt-2", value: responseTimeScore, className: "bg-gray-800 h-2 mt-2 rounded-full", indicatorClassName: "bg-gradient-to-r from-red-500 to-red-400 rounded-full" }), _jsx("p", { className: "text-sm text-gray-400 mt-3 font-medium", children: responseTimeScore >= 80
                                                        ? "Excellent"
                                                        : responseTimeScore >= 60
                                                            ? "Good"
                                                            : "Needs improvement" })] })] }) }), _jsx(motion.div, { custom: 4, initial: "hidden", animate: "visible", variants: cardVariants, children: _jsxs(Card, { className: "bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative group hover:border-red-500/30 transition-colors duration-300", children: [_jsx("div", { className: "absolute inset-0 bg-grid-pattern opacity-5" }), _jsx(CardHeader, { className: "pb-3 border-b border-gray-800 relative z-10", children: _jsxs(CardTitle, { className: "text-sm font-bold flex items-center text-white", children: [_jsx("div", { className: "bg-purple-500/10 p-1.5 rounded-md mr-2", children: _jsx(Zap, { className: "h-4 w-4 text-purple-500" }) }), "Token Usage"] }) }), _jsxs(CardContent, { className: "pt-5 relative z-10", children: [_jsx("div", { className: "text-3xl font-bold text-white mb-3", children: metrics.tokenUsage || 0 }), _jsx("div", { className: "text-sm text-gray-400 font-medium", children: "Estimated tokens used" })] })] }) }), _jsx(motion.div, { custom: 5, initial: "hidden", animate: "visible", variants: cardVariants, children: _jsxs(Card, { className: "bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative group hover:border-red-500/30 transition-colors duration-300", children: [_jsx("div", { className: "absolute inset-0 bg-grid-pattern opacity-5" }), _jsx(CardHeader, { className: "pb-3 border-b border-gray-800 relative z-10", children: _jsxs(CardTitle, { className: "text-sm font-bold flex items-center text-white", children: [_jsx("div", { className: "bg-blue-500/10 p-1.5 rounded-md mr-2", children: _jsx(Clock, { className: "h-4 w-4 text-blue-500" }) }), "API Call Time"] }) }), _jsxs(CardContent, { className: "pt-5 relative z-10", children: [_jsx("div", { className: "text-3xl font-bold text-white mb-3", children: formatTime(metrics.totalApiCallTime || 0) }), _jsx("div", { className: "text-sm text-gray-400 font-medium", children: "Total API processing time" })] })] }) })] })] })] }));
};
export default PerformanceMetrics;
