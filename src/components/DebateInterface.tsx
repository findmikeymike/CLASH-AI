import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Timer, Zap } from "lucide-react";
import { motion } from "framer-motion";

// Load ElevenLabs widget script
if (
  typeof window !== "undefined" &&
  !document.querySelector(
    'script[src="https://elevenlabs.io/convai-widget/index.js"]',
  )
) {
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

        console.log(
          `ElevenLabs API call completed: ${url}, duration: ${duration}ms`,
        );

        // Dispatch a custom event with the call duration
        window.dispatchEvent(
          new CustomEvent("elevenlabs-api-call", {
            detail: { duration, url },
          }),
        );

        return response;
      } catch (error) {
        console.error("Error intercepting ElevenLabs API call:", error);
        throw error;
      }
    }
    return originalFetch.apply(this, args);
  };
}

interface Character {
  id: string;
  name: string;
  description: string;
  expertise: string[];
  avatarUrl: string;
}

interface DebateInterfaceProps {
  character?: Character;
  onBack?: () => void;
  onDebateEnd?: (metrics: PerformanceMetrics) => void;
  tokenBalance?: number;
  onTokensUsed?: (amount: number) => void;
}

interface PerformanceMetrics {
  widgetLoadTime: number;
  sessionDuration: number;
  responseCount: number;
  averageResponseTime: number;
  tokenUsage?: number;
  totalApiCallTime?: number;
}

const DebateInterface = ({
  character,
  onBack = () => {},
  onDebateEnd = () => {},
  tokenBalance = 100,
  onTokensUsed = () => {},
}: DebateInterfaceProps) => {
  const [isWidgetLoaded, setIsWidgetLoaded] = useState(false);
  const [isWidgetLoading, setIsWidgetLoading] = useState(true);
  const [sessionStartTime, setSessionStartTime] = useState<number | null>(null);
  const [widgetLoadTime, setWidgetLoadTime] = useState<number | null>(null);
  const [responseCount, setResponseCount] = useState(0);
  const [sessionDuration, setSessionDuration] = useState(0);
  const [isDebateActive, setIsDebateActive] = useState(false);
  const [isCallActive, setIsCallActive] = useState(false);
  const [apiCallTimes, setApiCallTimes] = useState<number[]>([]);
  const [totalApiCallTime, setTotalApiCallTime] = useState(0);
  const [estimatedTokenUsage, setEstimatedTokenUsage] = useState(0);
  const [remainingTokens, setRemainingTokens] = useState<number | null>(null);

  // Placeholder for the actual widget load
  useEffect(() => {
    if (!character) return;

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

  // Update remaining tokens when tokenBalance changes
  useEffect(() => {
    setRemainingTokens(tokenBalance - estimatedTokenUsage);
  }, [tokenBalance, estimatedTokenUsage]);

  // Listen for ElevenLabs API calls
  useEffect(() => {
    const handleApiCall = (
      event: CustomEvent<{ duration: number; url: string }>,
    ) => {
      const { duration, url } = event.detail;
      console.log(`ElevenLabs API call to ${url} took ${duration}ms`);

      // Update API call metrics
      setApiCallTimes((prev) => [...prev, duration]);
      setTotalApiCallTime((prev) => prev + duration);
      setResponseCount((prev) => prev + 1);

      // Estimate token usage based on call duration
      // This is a simplified estimation - adjust the formula based on actual usage patterns
      const estimatedTokens = Math.ceil(duration / 100); // Example: 1 token per 100ms
      console.log(
        `Estimated token usage for this call: ${estimatedTokens} tokens`,
      );

      // Update token usage and remaining balance
      setEstimatedTokenUsage((prev) => {
        const newTotal = prev + estimatedTokens;
        // Notify parent component about token usage
        onTokensUsed(estimatedTokens);
        return newTotal;
      });

      // Calculate remaining tokens locally for immediate UI feedback
      setRemainingTokens(tokenBalance - estimatedTokenUsage - estimatedTokens);

      // Simulate AI response for UI updates
      simulateAIResponse();
    };

    // Add event listener for our custom event
    window.addEventListener(
      "elevenlabs-api-call",
      handleApiCall as EventListener,
    );

    return () => {
      window.removeEventListener(
        "elevenlabs-api-call",
        handleApiCall as EventListener,
      );
    };
  }, []);

  // Start session timer when call becomes active
  useEffect(() => {
    if (isCallActive && !sessionStartTime) {
      const startTime = Date.now();
      setSessionStartTime(startTime);
      setIsDebateActive(true);
      console.log("Call started at:", new Date(startTime).toISOString());
    } else if (!isCallActive && sessionStartTime) {
      console.log("Call ended at:", new Date().toISOString());
      setIsDebateActive(false);
    }
  }, [isCallActive, sessionStartTime]);

  // Update session duration
  useEffect(() => {
    if (!isDebateActive || !sessionStartTime) return;

    const intervalId = setInterval(() => {
      setSessionDuration(Math.floor((Date.now() - sessionStartTime) / 1000));
    }, 1000);

    return () => clearInterval(intervalId);
  }, [isDebateActive, sessionStartTime]);

  const handleEndDebate = () => {
    setIsDebateActive(false);

    // Calculate metrics
    const metrics: PerformanceMetrics = {
      widgetLoadTime: widgetLoadTime || 0,
      sessionDuration,
      responseCount,
      averageResponseTime:
        responseCount > 0 ? sessionDuration / responseCount : 0,
      tokenUsage: estimatedTokenUsage,
      totalApiCallTime: totalApiCallTime,
    };

    console.log("Debate ended with metrics:", metrics);
    onDebateEnd(metrics);
  };

  // Simulate AI response
  const simulateAIResponse = () => {
    setResponseCount((prev) => prev + 1);
  };

  if (!character) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/30 via-black to-pink-900/20"></div>
        <div className="absolute inset-0 bg-grid-pattern opacity-15"></div>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="relative z-10 w-full max-w-md"
        >
          <Card className="bg-gray-900 border border-purple-500/30 shadow-lg shadow-purple-500/10">
            <CardContent className="p-6">
              <p className="text-center text-gray-400">
                No character selected. Please go back and select a character.
              </p>
              <Button
                className="w-full mt-4 bg-red-600 hover:bg-red-700 text-white font-bold border-2 border-red-500 shadow-lg"
                onClick={onBack}
              >
                Back to Characters
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white relative overflow-hidden">
      {/* Background gradients */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-900/30 via-black to-pink-900/20"></div>
      <div className="absolute inset-0 bg-grid-pattern opacity-15"></div>
      <div className="absolute inset-0 bg-gradient-to-r from-purple-600/5 via-transparent to-red-600/5"></div>

      {/* Header with back button and timer */}
      <header className="relative z-50 flex items-center justify-between p-6">
        <Button
          variant="outline"
          size="icon"
          onClick={onBack}
          className="bg-red-600 text-white border-red-600 hover:bg-red-700 hover:border-red-700 rounded-lg transition-colors shadow-xl z-50 relative"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-gradient-to-r from-gray-900/80 to-black/80 backdrop-blur-sm px-4 py-2 rounded-lg border border-gray-800 shadow-md">
            <Timer className="h-4 w-4 text-red-500" />
            <span className="text-sm font-bold text-white">
              {Math.floor(sessionDuration / 60)}:
              {String(sessionDuration % 60).padStart(2, "0")}
            </span>
          </div>

          <div className="flex items-center space-x-2 bg-gradient-to-r from-gray-900/80 to-black/80 backdrop-blur-sm px-4 py-2 rounded-lg border border-gray-800 shadow-md">
            <Zap className="h-4 w-4 text-yellow-500" />
            <span className="text-sm font-bold text-white">
              {remainingTokens !== null ? remainingTokens : tokenBalance}
            </span>
            <span className="text-xs text-gray-400">min</span>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="relative z-10 h-[calc(100vh-120px)]">
        {/* Character profile - positioned closer to center with massive image */}
        <div className="absolute top-16 left-1/2 transform -translate-x-1/2 z-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <div className="relative inline-block mb-8">
              <div className="absolute -inset-4 bg-gradient-to-r from-red-600 to-red-500 rounded-full blur opacity-70"></div>
              <Avatar className="h-[48rem] w-[48rem] ring-8 ring-red-500/50 relative">
                <AvatarImage
                  src={character.avatarUrl}
                  alt={character.name}
                  className="object-cover"
                  style={{ objectPosition: "center 20%" }}
                />
                <AvatarFallback className="bg-gradient-to-br from-gray-800 to-gray-900 text-red-400 text-[12rem]">
                  {character.name.substring(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
            </div>
          </motion.div>
        </div>

        {/* Character info - positioned below avatar to prevent overlap */}
        <div className="absolute top-[56rem] left-1/2 transform -translate-x-1/2 z-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-center"
          >
            <h2 className="text-4xl font-bold mb-3 text-white">
              {character.name}
            </h2>
            <p className="text-gray-400 text-center mb-4 max-w-lg mx-auto text-lg">
              {character.description}
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {character.expertise.slice(0, 3).map((skill, index) => (
                <Badge
                  key={index}
                  variant="secondary"
                  className="text-sm bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors px-3 py-1"
                >
                  {skill}
                </Badge>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Widget area - absolutely centered */}
        <div className="absolute inset-0 flex items-center justify-center">
          {isWidgetLoading ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
              className="text-center"
            >
              <div className="inline-block h-10 w-10 animate-spin rounded-full border-4 border-solid border-purple-500 border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]"></div>
              <p className="mt-4 text-purple-300">Loading voice interface...</p>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <elevenlabs-convai
                agent-id={
                  character.id === "1"
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
                                      : "5MNvV1hW3kIwuaOmTghn"
                }
                onCallStart={() => {
                  console.log("ElevenLabs call started");
                  setIsCallActive(true);
                }}
                onCallEnd={() => {
                  console.log("ElevenLabs call ended");
                  setIsCallActive(false);
                }}
              ></elevenlabs-convai>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DebateInterface;
