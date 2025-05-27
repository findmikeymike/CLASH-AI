import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from "react";
import CharacterGrid from "./CharacterGrid";
import DebateInterface from "./DebateInterface";
import PerformanceMetrics from "./PerformanceMetrics";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Info, Zap, Crown, Clock } from "lucide-react";
import TokenDisplay from "./TokenDisplay";
import TokenPurchaseModal from "./TokenPurchaseModal";
import { createClient } from "@supabase/supabase-js";
function Home() {
    const [selectedCharacter, setSelectedCharacter] = useState(null);
    const [showDebate, setShowDebate] = useState(false);
    const [showMetrics, setShowMetrics] = useState(false);
    const [metrics, setMetrics] = useState(null);
    const [showInfo, setShowInfo] = useState(false);
    const [tokenBalance, setTokenBalance] = useState(0); // Initialize with 0, will be updated from database
    const [showPurchaseModal, setShowPurchaseModal] = useState(false);
    const [userId, setUserId] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    // Initialize Supabase client
    const supabase = createClient(import.meta.env.VITE_SUPABASE_URL, import.meta.env.VITE_SUPABASE_ANON_KEY);
    const handleCharacterSelect = (character) => {
        setSelectedCharacter(character);
        setShowDebate(true);
        setShowMetrics(false);
        setShowInfo(false);
    };
    const handleBackToCharacters = () => {
        setShowDebate(false);
        setShowMetrics(false);
        setShowInfo(false);
    };
    const handleDebateEnd = (debateMetrics) => {
        setMetrics(debateMetrics);
        setShowDebate(false);
        setShowMetrics(true);
        setShowInfo(false);
        // Deduct tokens based on usage
        if (debateMetrics.tokenUsage) {
            setTokenBalance((prev) => Math.max(0, prev - debateMetrics.tokenUsage));
        }
    };
    const handleTokensUsed = async (amount) => {
        // Update local state immediately for responsive UI
        const newBalance = Math.max(0, tokenBalance - amount);
        setTokenBalance(newBalance);
        // Update the database in the background
        if (userId) {
            try {
                const { data, error } = await supabase.functions.invoke("supabase-functions-user-minutes", {
                    body: { userId, minutesUsed: amount },
                    method: "POST",
                });
                if (error) {
                    console.error("Error updating minutes:", error);
                }
                else if (data?.remainingMinutes !== undefined) {
                    // Sync with server value if different
                    if (data.remainingMinutes !== newBalance) {
                        setTokenBalance(data.remainingMinutes);
                    }
                }
            }
            catch (error) {
                console.error("Error calling user-minutes function:", error);
            }
        }
    };
    const handleShowInfo = () => {
        setShowInfo(true);
        setShowDebate(false);
        setShowMetrics(false);
    };
    // Function to fetch user minutes from the database
    const fetchUserMinutes = async (uid) => {
        try {
            const { data, error } = await supabase.functions.invoke("supabase-functions-user-minutes", {
                body: { userId: uid },
                method: "GET",
            });
            if (error) {
                console.error("Error fetching minutes:", error);
                return 0;
            }
            return data?.remainingMinutes || 0;
        }
        catch (error) {
            console.error("Error calling user-minutes function:", error);
            return 0;
        }
    };
    // Effect to check auth status and fetch user minutes on load
    useEffect(() => {
        const checkAuthAndFetchMinutes = async () => {
            setIsLoading(true);
            try {
                // Get current auth session
                const { data: { session }, error, } = await supabase.auth.getSession();
                let uid;
                if (session?.user?.id) {
                    // Authenticated user
                    uid = session.user.id;
                }
                else {
                    // Anonymous user - generate a consistent ID from browser fingerprint or localStorage
                    uid = localStorage.getItem("anonymousUserId");
                    if (!uid) {
                        uid = `anon_${Math.random().toString(36).substring(2, 15)}`;
                        localStorage.setItem("anonymousUserId", uid);
                    }
                }
                setUserId(uid);
                // Fetch user minutes
                const minutes = await fetchUserMinutes(uid);
                setTokenBalance(minutes);
            }
            catch (err) {
                console.error("Error checking auth status:", err);
            }
            finally {
                setIsLoading(false);
            }
        };
        checkAuthAndFetchMinutes();
        // Listen for auth state changes
        const { data: authListener } = supabase.auth.onAuthStateChange(async (event, session) => {
            if (event === "SIGNED_IN" || event === "SIGNED_OUT") {
                // Update userId and fetch minutes again
                const uid = session?.user?.id ||
                    localStorage.getItem("anonymousUserId") ||
                    `anon_${Math.random().toString(36).substring(2, 15)}`;
                setUserId(uid);
                const minutes = await fetchUserMinutes(uid);
                setTokenBalance(minutes);
            }
        });
        return () => {
            authListener?.subscription.unsubscribe();
        };
    }, []);
    return (_jsxs("div", { className: "min-h-screen bg-black text-white relative overflow-hidden", children: [_jsxs("div", { className: "absolute inset-0 z-0", children: [_jsx("div", { className: "absolute inset-0 bg-gradient-to-br from-purple-900/30 via-black to-pink-900/20 z-10" }), _jsx("div", { className: "absolute top-0 left-0 right-0 h-full bg-grid-pattern opacity-15" }), _jsx("div", { className: "absolute inset-0 bg-gradient-to-r from-purple-600/5 via-transparent to-red-600/5" })] }), !showDebate && (_jsxs("header", { className: "relative z-20 flex items-center justify-between p-6", children: [_jsxs("div", { className: "flex items-center space-x-4", children: [_jsx("h1", { className: "text-5xl font-black text-red-500 tracking-tighter italic", children: "CLASH" }), _jsxs("div", { className: "flex items-center space-x-2 bg-gradient-to-r from-yellow-500/20 to-yellow-400/20 px-3 py-1 rounded-full border border-yellow-500/30", children: [_jsx(Crown, { className: "h-4 w-4 text-yellow-500" }), _jsx("span", { className: "text-yellow-400 text-sm font-medium", children: "PRO" })] })] }), _jsxs("div", { className: "flex items-center space-x-4", children: [_jsx(TokenDisplay, { tokenBalance: tokenBalance, onPurchaseClick: () => setShowPurchaseModal(true) }), _jsxs(Button, { variant: "outline", size: "sm", onClick: handleShowInfo, className: "border-white/30 bg-black/50 text-white hover:bg-red-600 hover:border-red-500 hover:text-white transition-all duration-200 backdrop-blur-sm", children: [_jsx(Info, { className: "h-4 w-4 mr-2" }), "Info"] })] })] })), _jsxs(AnimatePresence, { mode: "wait", children: [!showDebate && !showMetrics && !showInfo && (_jsx(motion.div, { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 }, transition: { duration: 0.5 }, className: "relative z-10", children: _jsx(CharacterGrid, { onCharacterSelect: handleCharacterSelect }) }, "character-grid")), showInfo && (_jsx(motion.div, { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 }, transition: { duration: 0.5 }, className: "relative z-10 p-6", children: _jsx("div", { className: "max-w-4xl mx-auto", children: _jsxs("div", { className: "bg-gradient-to-br from-gray-900 to-black border border-gray-800 rounded-2xl p-8", children: [_jsx("h2", { className: "text-3xl font-bold text-white mb-8", children: "About CLASH AI" }), _jsxs("div", { className: "grid grid-cols-1 md:grid-cols-2 gap-8", children: [_jsx(Card, { className: "bg-gradient-to-br from-gray-800 to-black border border-gray-700", children: _jsxs(CardContent, { className: "p-6", children: [_jsxs("h3", { className: "text-xl font-bold text-white mb-4 flex items-center", children: [_jsx(Zap, { className: "h-5 w-5 mr-2 text-yellow-500" }), "How Minutes Work"] }), _jsx("p", { className: "text-gray-400 mb-4", children: "Understanding CLASH AI's minute-based system" }), _jsxs("div", { className: "space-y-4", children: [_jsxs("div", { className: "bg-gray-900 p-3 rounded-lg border border-gray-700", children: [_jsx("h4", { className: "text-white font-medium mb-2", children: "Purchasing Minutes" }), _jsx("p", { className: "text-gray-300 text-sm", children: "Buy minute packages through our secure payment system. Choose from 10, 30, or 60 minute bundles." })] }), _jsxs("div", { className: "bg-gray-900 p-3 rounded-lg border border-gray-700", children: [_jsx("h4", { className: "text-white font-medium mb-2", children: "Usage Tracking" }), _jsx("p", { className: "text-gray-300 text-sm", children: "Minutes are consumed during active conversations with AI characters. The timer at the top shows your current session length." })] }), _jsxs("div", { className: "bg-gray-900 p-3 rounded-lg border border-gray-700", children: [_jsx("h4", { className: "text-white font-medium mb-2", children: "Minute Balance" }), _jsx("p", { className: "text-gray-300 text-sm", children: "Your remaining minutes are displayed at the top of the screen. You'll need to purchase more when your balance reaches zero." })] })] })] }) }), _jsx(Card, { className: "bg-gradient-to-br from-gray-800 to-black border border-gray-700", children: _jsxs(CardContent, { className: "p-6", children: [_jsxs("h3", { className: "text-xl font-bold text-white mb-4 flex items-center", children: [_jsx(Clock, { className: "h-5 w-5 mr-2 text-blue-500" }), "How to Use CLASH AI"] }), _jsx("p", { className: "text-gray-400 mb-4", children: "Getting the most out of your experience" }), _jsxs("div", { className: "space-y-4", children: [_jsxs("div", { className: "bg-gray-900 p-3 rounded-lg border border-gray-700", children: [_jsx("h4", { className: "text-white font-medium mb-2", children: "Select a Character" }), _jsx("p", { className: "text-gray-300 text-sm", children: "Choose from our diverse cast of AI characters, each with unique perspectives and expertise." })] }), _jsxs("div", { className: "bg-gray-900 p-3 rounded-lg border border-gray-700", children: [_jsx("h4", { className: "text-white font-medium mb-2", children: "Voice Interaction" }), _jsx("p", { className: "text-gray-300 text-sm", children: "Speak naturally with your chosen character. Our advanced voice recognition understands natural conversation." })] }), _jsxs("div", { className: "bg-gray-900 p-3 rounded-lg border border-gray-700", children: [_jsx("h4", { className: "text-white font-medium mb-2", children: "Performance Metrics" }), _jsx("p", { className: "text-gray-300 text-sm", children: "After each debate, review detailed metrics about your conversation, including duration and response times." })] })] })] }) })] }), _jsx("div", { className: "mt-8 flex justify-center", children: _jsx(Button, { onClick: handleBackToCharacters, variant: "outline", className: "border-gray-700 text-white hover:bg-gray-800 hover:border-red-500/50", children: "Back to Dashboard" }) })] }) }) }, "info")), showDebate && selectedCharacter && (_jsx(motion.div, { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 }, transition: { duration: 0.5 }, className: "relative z-10", children: _jsx(DebateInterface, { character: selectedCharacter, onBack: handleBackToCharacters, onDebateEnd: handleDebateEnd, tokenBalance: tokenBalance, onTokensUsed: handleTokensUsed }) }, "debate-interface")), showMetrics && metrics && (_jsxs(motion.div, { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 }, transition: { duration: 0.5 }, className: "max-w-4xl mx-auto py-8 px-4 relative z-10", children: [_jsx(PerformanceMetrics, { metrics: metrics }), _jsx(motion.div, { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { delay: 0.5, duration: 0.5 }, className: "mt-8 flex justify-center", children: _jsxs("div", { className: "relative group", children: [_jsx("div", { className: "absolute -inset-1 bg-gradient-to-r from-red-600 to-red-500 rounded-lg blur opacity-70 group-hover:opacity-100 transition duration-200" }), _jsx("button", { onClick: handleBackToCharacters, className: "relative bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white font-bold py-4 px-8 rounded-lg text-lg transition-all duration-300 hover:scale-[1.02] shadow-xl border border-red-700/50", children: "RETURN TO DASHBOARD" })] }) })] }, "performance-metrics"))] }), _jsx(TokenPurchaseModal, { open: showPurchaseModal, onOpenChange: setShowPurchaseModal, onPurchaseComplete: (amount) => {
                    setTokenBalance((prev) => prev + amount);
                } })] }));
}
export default Home;
