import React, { useState, useEffect } from "react";
import CharacterGrid from "./CharacterGrid";
import DebateInterface from "./DebateInterface";
import PerformanceMetrics from "./PerformanceMetrics";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Info, Zap, Crown, Clock, CreditCard, User } from "lucide-react";
import TokenDisplay from "./TokenDisplay";
import TokenPurchaseModal from "./TokenPurchaseModal";
import { createClient } from "@supabase/supabase-js";

interface Character {
  id: string;
  name: string;
  description: string;
  expertise: string[];
  avatarUrl: string;
}

interface PerformanceMetrics {
  widgetLoadTime: number;
  sessionDuration: number;
  responseCount: number;
  averageResponseTime: number;
  tokenUsage?: number;
  totalApiCallTime?: number;
}

function Home() {
  const [selectedCharacter, setSelectedCharacter] = useState<Character | null>(
    null,
  );
  const [showDebate, setShowDebate] = useState(false);
  const [showMetrics, setShowMetrics] = useState(false);
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [showInfo, setShowInfo] = useState(false);
  const [tokenBalance, setTokenBalance] = useState(0); // Initialize with 0, will be updated from database
  const [showPurchaseModal, setShowPurchaseModal] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize Supabase client
  const supabase = createClient(
    import.meta.env.VITE_SUPABASE_URL,
    import.meta.env.VITE_SUPABASE_ANON_KEY,
  );

  const handleCharacterSelect = (character: Character) => {
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

  const handleDebateEnd = (debateMetrics: PerformanceMetrics) => {
    setMetrics(debateMetrics);
    setShowDebate(false);
    setShowMetrics(true);
    setShowInfo(false);

    // Deduct tokens based on usage
    if (debateMetrics.tokenUsage) {
      setTokenBalance((prev) => Math.max(0, prev - debateMetrics.tokenUsage));
    }
  };

  const handleTokensUsed = async (amount: number) => {
    // Update local state immediately for responsive UI
    const newBalance = Math.max(0, tokenBalance - amount);
    setTokenBalance(newBalance);

    // Update the database in the background
    if (userId) {
      try {
        const { data, error } = await supabase.functions.invoke(
          "supabase-functions-user-minutes",
          {
            body: { userId, minutesUsed: amount },
            method: "POST",
          },
        );

        if (error) {
          console.error("Error updating minutes:", error);
        } else if (data?.remainingMinutes !== undefined) {
          // Sync with server value if different
          if (data.remainingMinutes !== newBalance) {
            setTokenBalance(data.remainingMinutes);
          }
        }
      } catch (error) {
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
  const fetchUserMinutes = async (uid: string) => {
    try {
      const { data, error } = await supabase.functions.invoke(
        "supabase-functions-user-minutes",
        {
          body: { userId: uid },
          method: "GET",
        },
      );

      if (error) {
        console.error("Error fetching minutes:", error);
        return 0;
      }

      return data?.remainingMinutes || 0;
    } catch (error) {
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
        const {
          data: { session },
          error,
        } = await supabase.auth.getSession();

        let uid;
        if (session?.user?.id) {
          // Authenticated user
          uid = session.user.id;
        } else {
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
      } catch (err) {
        console.error("Error checking auth status:", err);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthAndFetchMinutes();

    // Listen for auth state changes
    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (event === "SIGNED_IN" || event === "SIGNED_OUT") {
          // Update userId and fetch minutes again
          const uid =
            session?.user?.id ||
            localStorage.getItem("anonymousUserId") ||
            `anon_${Math.random().toString(36).substring(2, 15)}`;
          setUserId(uid);
          const minutes = await fetchUserMinutes(uid);
          setTokenBalance(minutes);
        }
      },
    );

    return () => {
      authListener?.subscription.unsubscribe();
    };
  }, []);

  return (
    <div className="min-h-screen bg-black text-white relative overflow-hidden">
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/30 via-black to-pink-900/20 z-10"></div>
        <div className="absolute top-0 left-0 right-0 h-full bg-grid-pattern opacity-15"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-purple-600/5 via-transparent to-red-600/5"></div>
      </div>

      {/* Header */}
      {!showDebate && (
        <header className="relative z-20 flex items-center justify-between p-6">
          <div className="flex items-center space-x-4">
            <h1 className="text-5xl font-black text-red-500 tracking-tighter italic">
              CLASH
            </h1>
            <div className="flex items-center space-x-2 bg-gradient-to-r from-red-600/20 to-red-500/20 px-3 py-1 rounded-full border border-red-500/30">
              <Zap className="h-4 w-4 text-red-500" />
              <span className="text-red-400 text-sm font-medium">AI</span>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <TokenDisplay
              tokenBalance={tokenBalance}
              onPurchaseClick={() => setShowPurchaseModal(true)}
            />
            <Button
              variant="outline"
              size="sm"
              onClick={handleShowInfo}
              className="border-white/30 bg-black/50 text-white hover:bg-red-600 hover:border-red-500 hover:text-white transition-all duration-200 backdrop-blur-sm"
            >
              <Info className="h-4 w-4 mr-2" />
              Info
            </Button>
          </div>
        </header>
      )}

      <AnimatePresence mode="wait">
        {!showDebate && !showMetrics && !showInfo && (
          <motion.div
            key="character-grid"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="relative z-10"
          >
            <CharacterGrid onCharacterSelect={handleCharacterSelect} />
          </motion.div>
        )}

        {showInfo && (
          <motion.div
            key="info"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="relative z-10 p-6"
          >
            <div className="max-w-4xl mx-auto">
              <div className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 rounded-2xl p-8">
                <h2 className="text-3xl font-bold text-white mb-8">About CLASH AI</h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <Card className="bg-gradient-to-br from-gray-800 to-black border border-gray-700">
                    <CardContent className="p-6">
                      <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                        <Zap className="h-5 w-5 mr-2 text-yellow-500" />
                        How Minutes Work
                      </h3>
                      <p className="text-gray-400 mb-4">
                        Understanding CLASH AI's minute-based system
                      </p>
                      <div className="space-y-4">
                        <div className="bg-gray-900 p-3 rounded-lg border border-gray-700">
                          <h4 className="text-white font-medium mb-2">Purchasing Minutes</h4>
                          <p className="text-gray-300 text-sm">Buy minute packages through our secure payment system. Choose from 10, 30, or 60 minute bundles.</p>
                        </div>
                        <div className="bg-gray-900 p-3 rounded-lg border border-gray-700">
                          <h4 className="text-white font-medium mb-2">Usage Tracking</h4>
                          <p className="text-gray-300 text-sm">Minutes are consumed during active conversations with AI characters. The timer at the top shows your current session length.</p>
                        </div>
                        <div className="bg-gray-900 p-3 rounded-lg border border-gray-700">
                          <h4 className="text-white font-medium mb-2">Minute Balance</h4>
                          <p className="text-gray-300 text-sm">Your remaining minutes are displayed at the top of the screen. You'll need to purchase more when your balance reaches zero.</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-gradient-to-br from-gray-800 to-black border border-gray-700">
                    <CardContent className="p-6">
                      <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                        <Clock className="h-5 w-5 mr-2 text-blue-500" />
                        How to Use CLASH AI
                      </h3>
                      <p className="text-gray-400 mb-4">
                        Getting the most out of your experience
                      </p>
                      <div className="space-y-4">
                        <div className="bg-gray-900 p-3 rounded-lg border border-gray-700">
                          <h4 className="text-white font-medium mb-2">Select a Character</h4>
                          <p className="text-gray-300 text-sm">Choose from our diverse cast of AI characters, each with unique perspectives and expertise.</p>
                        </div>
                        <div className="bg-gray-900 p-3 rounded-lg border border-gray-700">
                          <h4 className="text-white font-medium mb-2">Voice Interaction</h4>
                          <p className="text-gray-300 text-sm">Speak naturally with your chosen character. Our advanced voice recognition understands natural conversation.</p>
                        </div>
                        <div className="bg-gray-900 p-3 rounded-lg border border-gray-700">
                          <h4 className="text-white font-medium mb-2">Call Duration</h4>
                          <p className="text-gray-300 text-sm">The timer at the top tracks your current conversation length. Your minutes are deducted based on actual usage time.</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <div className="mt-8 flex justify-center">
                  <Button
                    onClick={handleBackToCharacters}
                    variant="outline"
                    className="border-gray-700 text-white hover:bg-gray-800 hover:border-red-500/50 bg-gray-900 py-2 px-4 text-base"
                    size="lg"
                  >
                    Back to Dashboard
                  </Button>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {showDebate && selectedCharacter && (
          <motion.div
            key="debate-interface"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="relative z-10"
          >
            <DebateInterface
              character={selectedCharacter}
              onBack={handleBackToCharacters}
              onDebateEnd={handleDebateEnd}
              tokenBalance={tokenBalance}
              onTokensUsed={handleTokensUsed}
            />
          </motion.div>
        )}

        {showMetrics && metrics && (
          <motion.div
            key="performance-metrics"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="max-w-4xl mx-auto py-8 px-4 relative z-10"
          >
            <PerformanceMetrics metrics={metrics} />
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.5 }}
              className="mt-8 flex justify-center"
            >
              <div className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-red-600 to-red-500 rounded-lg blur opacity-70 group-hover:opacity-100 transition duration-200"></div>
                <button
                  onClick={handleBackToCharacters}
                  className="relative bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white font-bold py-4 px-8 rounded-lg text-lg transition-all duration-300 hover:scale-[1.02] shadow-xl border border-red-700/50"
                >
                  RETURN TO DASHBOARD
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Token Purchase Modal */}
      <TokenPurchaseModal
        open={showPurchaseModal}
        onOpenChange={setShowPurchaseModal}
        onPurchaseComplete={(amount) => {
          setTokenBalance((prev) => prev + amount);
        }}
      />
    </div>
  );
}

export default Home;
