import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Clock, Zap, MessageCircle, BarChart3 } from "lucide-react";
import { motion } from "framer-motion";

interface PerformanceMetricsProps {
  metrics?: {
    widgetLoadTime: number;
    sessionDuration: number;
    responseCount: number;
    averageResponseTime: number;
    tokenUsage?: number;
    totalApiCallTime?: number;
  };
}

const PerformanceMetrics = ({
  metrics = {
    widgetLoadTime: 1200,
    sessionDuration: 180,
    responseCount: 12,
    averageResponseTime: 15,
    tokenUsage: 150,
    totalApiCallTime: 8000,
  },
}: PerformanceMetricsProps) => {
  // Calculate performance scores (simplified example)
  const loadTimeScore = Math.max(0, 100 - metrics.widgetLoadTime / 50);
  const responseTimeScore = Math.max(0, 100 - metrics.averageResponseTime * 2);

  // Format time in seconds with ms
  const formatTime = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  // Format duration in minutes and seconds
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: (i: number) => ({
      opacity: 1,
      y: 0,
      transition: {
        delay: i * 0.1,
        duration: 0.5,
      },
    }),
  };

  return (
    <div className="w-full bg-black text-white p-6 relative overflow-hidden">
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/30 via-black to-pink-900/20 z-10"></div>
        <div className="absolute top-0 left-0 right-0 h-full bg-grid-pattern opacity-15"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-purple-600/5 via-transparent to-red-600/5"></div>
      </div>

      <div className="relative z-10">
        <div className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 rounded-2xl p-10 mb-12 shadow-2xl relative overflow-hidden">
          <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
          <div className="relative z-10">
            <motion.h2
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-4xl md:text-6xl font-black mb-4 text-center text-white"
            >
              Debate Performance
            </motion.h2>
            <p className="text-xl text-gray-400 text-center">
              Your battle statistics and achievements
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Widget Load Time */}
          <motion.div
            custom={0}
            initial="hidden"
            animate="visible"
            variants={cardVariants}
          >
            <Card className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative group hover:border-red-500/30 transition-colors duration-300">
              <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
              <CardHeader className="pb-3 border-b border-gray-800 relative z-10">
                <CardTitle className="text-sm font-bold flex items-center text-white">
                  <div className="bg-yellow-500/10 p-1.5 rounded-md mr-2">
                    <Zap className="h-4 w-4 text-yellow-500" />
                  </div>
                  Widget Load Time
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-5 relative z-10">
                <div className="text-3xl font-bold text-white mb-3">
                  {formatTime(metrics.widgetLoadTime)}
                </div>
                <Progress
                  value={loadTimeScore}
                  className="bg-gray-800 h-2 mt-2 rounded-full"
                />
                <p className="text-sm text-gray-400 mt-3 font-medium">
                  {loadTimeScore >= 80
                    ? "Excellent"
                    : loadTimeScore >= 60
                      ? "Good"
                      : "Needs improvement"}
                </p>
              </CardContent>
            </Card>
          </motion.div>

          {/* Session Duration */}
          <motion.div
            custom={1}
            initial="hidden"
            animate="visible"
            variants={cardVariants}
          >
            <Card className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative group hover:border-red-500/30 transition-colors duration-300">
              <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
              <CardHeader className="pb-3 border-b border-gray-800 relative z-10">
                <CardTitle className="text-sm font-bold flex items-center text-white">
                  <div className="bg-blue-500/10 p-1.5 rounded-md mr-2">
                    <Clock className="h-4 w-4 text-blue-500" />
                  </div>
                  Session Duration
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-5 relative z-10">
                <div className="text-3xl font-bold text-white mb-3">
                  {formatDuration(metrics.sessionDuration)}
                </div>
                <div className="text-sm text-gray-400 font-medium">
                  Total debate time
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Response Count */}
          <motion.div
            custom={2}
            initial="hidden"
            animate="visible"
            variants={cardVariants}
          >
            <Card className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative group hover:border-red-500/30 transition-colors duration-300">
              <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
              <CardHeader className="pb-3 border-b border-gray-800 relative z-10">
                <CardTitle className="text-sm font-bold flex items-center text-white">
                  <div className="bg-green-500/10 p-1.5 rounded-md mr-2">
                    <MessageCircle className="h-4 w-4 text-green-500" />
                  </div>
                  AI Responses
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-5 relative z-10">
                <div className="text-3xl font-bold text-white mb-3">
                  {metrics.responseCount}
                </div>
                <div className="text-sm text-gray-400 font-medium">
                  Total responses from AI
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Average Response Time */}
          <motion.div
            custom={3}
            initial="hidden"
            animate="visible"
            variants={cardVariants}
          >
            <Card className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative group hover:border-red-500/30 transition-colors duration-300">
              <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
              <CardHeader className="pb-3 border-b border-gray-800 relative z-10">
                <CardTitle className="text-sm font-bold flex items-center text-white">
                  <div className="bg-red-500/10 p-1.5 rounded-md mr-2">
                    <BarChart3 className="h-4 w-4 text-red-500" />
                  </div>
                  Avg. Response Time
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-5 relative z-10">
                <div className="text-3xl font-bold text-white mb-3">
                  {metrics.averageResponseTime.toFixed(1)}s
                </div>
                <Progress
                  value={responseTimeScore}
                  className="bg-gray-800 h-2 mt-2 rounded-full"
                />
                <p className="text-sm text-gray-400 mt-3 font-medium">
                  {responseTimeScore >= 80
                    ? "Excellent"
                    : responseTimeScore >= 60
                      ? "Good"
                      : "Needs improvement"}
                </p>
              </CardContent>
            </Card>
          </motion.div>

          {/* Token Usage */}
          <motion.div
            custom={4}
            initial="hidden"
            animate="visible"
            variants={cardVariants}
          >
            <Card className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative group hover:border-red-500/30 transition-colors duration-300">
              <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
              <CardHeader className="pb-3 border-b border-gray-800 relative z-10">
                <CardTitle className="text-sm font-bold flex items-center text-white">
                  <div className="bg-purple-500/10 p-1.5 rounded-md mr-2">
                    <Zap className="h-4 w-4 text-purple-500" />
                  </div>
                  Token Usage
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-5 relative z-10">
                <div className="text-3xl font-bold text-white mb-3">
                  {metrics.tokenUsage || 0}
                </div>
                <div className="text-sm text-gray-400 font-medium">
                  Estimated tokens used
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* API Call Time */}
          <motion.div
            custom={5}
            initial="hidden"
            animate="visible"
            variants={cardVariants}
          >
            <Card className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative group hover:border-red-500/30 transition-colors duration-300">
              <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
              <CardHeader className="pb-3 border-b border-gray-800 relative z-10">
                <CardTitle className="text-sm font-bold flex items-center text-white">
                  <div className="bg-blue-500/10 p-1.5 rounded-md mr-2">
                    <Clock className="h-4 w-4 text-blue-500" />
                  </div>
                  API Call Time
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-5 relative z-10">
                <div className="text-3xl font-bold text-white mb-3">
                  {formatTime(metrics.totalApiCallTime || 0)}
                </div>
                <div className="text-sm text-gray-400 font-medium">
                  Total API processing time
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceMetrics;
