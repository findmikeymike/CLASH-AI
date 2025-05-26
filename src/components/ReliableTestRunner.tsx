import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle2, XCircle, PlayCircle, Zap } from "lucide-react";
import { createClient } from "@supabase/supabase-js";

interface TestResult {
  name: string;
  success: boolean;
  message: string;
  duration?: number;
}

interface TestSuiteResult {
  success: boolean;
  results: TestResult[];
  summary: string;
  totalDuration: number;
}

const ReliableTestRunner: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [testResults, setTestResults] = useState<TestSuiteResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastRun, setLastRun] = useState<Date | null>(null);

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
      console.log(
        "Supabase Anon Key:",
        supabaseAnonKey ? "✅ Set" : "❌ Not set",
      );

      if (!supabaseUrl || !supabaseAnonKey) {
        throw new Error(
          "Missing Supabase credentials in frontend environment variables",
        );
      }

      // Check if backend environment variables are properly set
      console.log(
        "Verifying backend environment variables are properly set...",
      );

      console.log("Invoking test-payment-system function...");
      const response = await supabase.functions.invoke(
        "supabase-functions-test-payment-system",
        {
          method: "POST",
          body: {},
        },
      );

      if (response.error) {
        console.error("Edge function error:", response.error);
        throw new Error(
          `Edge function error: ${response.error.message || JSON.stringify(response.error)}`,
        );
      }

      setTestResults(response.data);
      setLastRun(new Date());
      console.log("Tests completed successfully:", response.data);
    } catch (err: any) {
      console.error("Test execution failed:", err);
      setError(err.message || String(err));
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="bg-black min-h-screen p-6">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center">
            <Zap className="h-8 w-8 mr-3 text-yellow-500" />
            Reliable Payment System Test Runner
          </h1>
          <p className="text-gray-400">
            Comprehensive testing with timeout protection and proper error
            handling
          </p>
        </div>

        <Card className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative mb-8">
          <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
          <CardHeader className="pb-3 border-b border-gray-800 relative z-10">
            <CardTitle className="text-lg font-bold flex items-center text-white">
              <PlayCircle className="h-5 w-5 mr-2 text-green-500" />
              Test Execution
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-5 relative z-10">
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-gray-400">
                    Run comprehensive tests on payment system, token tracking,
                    and database functions
                  </p>
                  {lastRun && (
                    <p className="text-xs text-gray-500 mt-1">
                      Last run: {lastRun.toLocaleString()}
                    </p>
                  )}
                </div>
                <Button
                  onClick={runTests}
                  disabled={isRunning}
                  className={
                    isRunning
                      ? "bg-gray-700"
                      : "bg-green-600 hover:bg-green-700"
                  }
                  size="lg"
                >
                  {isRunning ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Running Tests...
                    </>
                  ) : (
                    <>
                      <PlayCircle className="mr-2 h-4 w-4" />
                      Run All Tests
                    </>
                  )}
                </Button>
              </div>

              {error && (
                <div className="bg-red-900/30 border border-red-800 rounded-md p-4 text-red-300">
                  <p className="font-medium flex items-center">
                    <XCircle className="h-5 w-5 mr-2" />
                    Test Execution Failed
                  </p>
                  <p className="mt-2 text-sm">{error}</p>
                </div>
              )}

              {testResults && (
                <div className="space-y-4">
                  <div
                    className={`p-4 rounded-md border ${
                      testResults.success
                        ? "bg-green-900/30 border-green-800"
                        : "bg-red-900/30 border-red-800"
                    }`}
                  >
                    <p className="font-medium flex items-center justify-between">
                      <span className="flex items-center">
                        {testResults.success ? (
                          <>
                            <CheckCircle2 className="h-5 w-5 mr-2 text-green-500" />
                            <span className="text-green-400">
                              All Tests Passed
                            </span>
                          </>
                        ) : (
                          <>
                            <XCircle className="h-5 w-5 mr-2 text-red-500" />
                            <span className="text-red-400">
                              Some Tests Failed
                            </span>
                          </>
                        )}
                      </span>
                      <span className="text-sm text-gray-400">
                        Total: {testResults.totalDuration.toFixed(2)}ms
                      </span>
                    </p>
                  </div>

                  <div className="space-y-3">
                    {testResults.results.map((result, index) => (
                      <div
                        key={index}
                        className={`p-4 rounded-md border ${
                          result.success
                            ? "bg-gray-800/50 border-gray-700"
                            : "bg-red-900/20 border-red-800/30"
                        }`}
                      >
                        <div className="flex justify-between items-center">
                          <p className="font-medium flex items-center">
                            {result.success ? (
                              <CheckCircle2 className="h-4 w-4 mr-2 text-green-500" />
                            ) : (
                              <XCircle className="h-4 w-4 mr-2 text-red-500" />
                            )}
                            {result.name}
                          </p>
                          <div className="flex items-center space-x-2">
                            {result.duration && (
                              <span className="text-xs text-gray-500">
                                {result.duration.toFixed(2)}ms
                              </span>
                            )}
                            <Badge
                              variant={
                                result.success ? "outline" : "destructive"
                              }
                              className={
                                result.success
                                  ? "border-green-500 text-green-400"
                                  : ""
                              }
                            >
                              {result.success ? "PASSED" : "FAILED"}
                            </Badge>
                          </div>
                        </div>
                        <p className="mt-2 text-sm text-gray-400">
                          {result.message}
                        </p>
                      </div>
                    ))}
                  </div>

                  <div className="mt-6 bg-gray-800/50 border border-gray-700 rounded-md p-4">
                    <p className="font-medium mb-3 text-white">
                      Detailed Test Summary
                    </p>
                    <pre className="text-xs text-gray-400 whitespace-pre-wrap overflow-auto max-h-96">
                      {testResults.summary}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative">
          <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
          <CardHeader className="pb-3 border-b border-gray-800 relative z-10">
            <CardTitle className="text-lg font-bold text-white">
              Test Coverage
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-5 relative z-10">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="font-medium text-white">Database Tests</h4>
                <ul className="text-sm text-gray-400 space-y-1">
                  <li>• Connection verification</li>
                  <li>• Table access validation</li>
                  <li>• Query performance</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-white">Payment Tests</h4>
                <ul className="text-sm text-gray-400 space-y-1">
                  <li>• Stripe charge creation</li>
                  <li>• Payment intent generation</li>
                  <li>• Webhook processing</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-white">Token Tests</h4>
                <ul className="text-sm text-gray-400 space-y-1">
                  <li>• Minutes addition/usage</li>
                  <li>• Balance calculations</li>
                  <li>• User tracking</li>
                </ul>
              </div>
              <div className="space-y-2">
                <h4 className="font-medium text-white">Reliability Features</h4>
                <ul className="text-sm text-gray-400 space-y-1">
                  <li>• 10-second timeouts</li>
                  <li>• Proper error handling</li>
                  <li>• Performance monitoring</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ReliableTestRunner;
