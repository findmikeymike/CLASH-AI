import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import PaymentSystemTests from "@/components/PaymentSystemTests";
import PaymentSystemHealth from "@/components/PaymentSystemHealth";
import TestControls from "@/components/TestControls";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, TestTube2, Zap } from "lucide-react";
const PaymentDashboard = () => {
    const [activeTab, setActiveTab] = useState("health");
    return (_jsx("div", { className: "bg-black min-h-screen p-6", children: _jsxs("div", { className: "max-w-5xl mx-auto", children: [_jsxs("div", { className: "mb-8", children: [_jsx("h1", { className: "text-4xl font-bold text-white mb-2", children: "Payment System Dashboard" }), _jsx("p", { className: "text-gray-400", children: "Monitor and test the payment system and token tracking functionality" })] }), _jsxs(Tabs, { defaultValue: "health", value: activeTab, onValueChange: setActiveTab, className: "space-y-6", children: [_jsxs(TabsList, { className: "bg-gray-900 border border-gray-800", children: [_jsxs(TabsTrigger, { value: "health", className: activeTab === "health"
                                        ? "data-[state=active]:bg-purple-600"
                                        : "", children: [_jsx(Activity, { className: "h-4 w-4 mr-2" }), "System Health"] }), _jsxs(TabsTrigger, { value: "tests", className: activeTab === "tests" ? "data-[state=active]:bg-purple-600" : "", children: [_jsx(TestTube2, { className: "h-4 w-4 mr-2" }), "Run Tests"] }), _jsxs(TabsTrigger, { value: "token-usage", className: activeTab === "token-usage"
                                        ? "data-[state=active]:bg-purple-600"
                                        : "", children: [_jsx(Zap, { className: "h-4 w-4 mr-2" }), "Token Usage"] })] }), _jsxs(TabsContent, { value: "health", className: "space-y-6", children: [_jsx(PaymentSystemHealth, {}), _jsxs(Card, { className: "bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative", children: [_jsx("div", { className: "absolute inset-0 bg-grid-pattern opacity-5" }), _jsx(CardHeader, { className: "pb-3 border-b border-gray-800 relative z-10", children: _jsx(CardTitle, { className: "text-lg font-bold text-white", children: "System Architecture" }) }), _jsx(CardContent, { className: "pt-5 relative z-10", children: _jsx("div", { className: "bg-gray-800/50 border border-gray-700 rounded-md p-4", children: _jsx("pre", { className: "text-xs text-gray-400 whitespace-pre-wrap overflow-auto max-h-96", children: `Payment System Architecture:

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  React Frontend │────▶│  Edge Functions │────▶│  Stripe API     │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                      │
         │                       │                      │
         ▼                       ▼                      ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  User Interface │     │  Supabase DB    │     │  Webhook Events │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘

Components:

1. Frontend Components:
   - TokenPurchaseModal: User interface for purchasing tokens
   - TokenDisplay: Shows user's current token balance
   - DebateInterface: Tracks token usage during debates

2. Edge Functions:
   - create-payment-intent: Creates Stripe checkout sessions
   - handle-stripe-webhook: Processes webhook events from Stripe
   - user-minutes: Manages user token balance (GET/POST)

3. Database:
   - user_minutes table: Stores user token balances
   - Row-level security policies for data protection
   - Realtime enabled for instant updates

4. External Services:
   - Stripe API: Payment processing
   - ElevenLabs API: Voice synthesis (token consumption)` }) }) })] })] }), _jsx(TabsContent, { value: "tests", className: "space-y-6", children: _jsx(PaymentSystemTests, {}) }), _jsx(TabsContent, { value: "token-usage", className: "space-y-6", children: _jsx(TestControls, { onMetricsUpdate: () => { } }) })] })] }) }));
};
export default PaymentDashboard;
