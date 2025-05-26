import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle2, XCircle, PlayCircle } from "lucide-react";
import { runPaymentTests } from "@/utils/paymentTests";

interface TestResult {
  name: string;
  success: boolean;
  message: string;
}

interface TestSuiteResult {
  success: boolean;
  results: TestResult[];
  summary: string;
}

const PaymentSystemTests: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [testResults, setTestResults] = useState<TestSuiteResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runTests = async () => {
    setIsRunning(true);
    setError(null);
    setTestResults(null);

    try {
      const results = await runPaymentTests();
      setTestResults(results);
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <Card className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative">
      <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
      <CardHeader className="pb-3 border-b border-gray-800 relative z-10">
        <CardTitle className="text-lg font-bold flex items-center text-white">
          <PlayCircle className="h-5 w-5 mr-2 text-purple-500" />
          Payment System & Token Tracking Tests
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-5 relative z-10">
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <p className="text-gray-400">
              Run tests to verify payment system and token tracking
              functionality
            </p>
            <Button
              onClick={runTests}
              disabled={isRunning}
              className={
                isRunning ? "bg-gray-700" : "bg-purple-600 hover:bg-purple-700"
              }
            >
              {isRunning ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Running Tests...
                </>
              ) : (
                <>Run All Tests</>
              )}
            </Button>
          </div>

          {error && (
            <div className="bg-red-900/30 border border-red-800 rounded-md p-4 text-red-300">
              <p className="font-medium flex items-center">
                <XCircle className="h-5 w-5 mr-2" />
                Error Running Tests
              </p>
              <p className="mt-2 text-sm">{error}</p>
            </div>
          )}

          {testResults && (
            <div className="space-y-4">
              <div
                className={`p-4 rounded-md border ${testResults.success ? "bg-green-900/30 border-green-800" : "bg-red-900/30 border-red-800"}`}
              >
                <p className="font-medium flex items-center">
                  {testResults.success ? (
                    <>
                      <CheckCircle2 className="h-5 w-5 mr-2 text-green-500" />
                      <span className="text-green-400">All Tests Passed</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-5 w-5 mr-2 text-red-500" />
                      <span className="text-red-400">Some Tests Failed</span>
                    </>
                  )}
                </p>
              </div>

              <div className="space-y-3">
                {testResults.results.map((result, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-md border ${result.success ? "bg-gray-800/50 border-gray-700" : "bg-red-900/20 border-red-800/30"}`}
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
                      <Badge
                        variant={result.success ? "outline" : "destructive"}
                        className={
                          result.success
                            ? "border-green-500 text-green-400"
                            : ""
                        }
                      >
                        {result.success ? "PASSED" : "FAILED"}
                      </Badge>
                    </div>
                    <p className="mt-2 text-sm text-gray-400">
                      {result.message}
                    </p>
                  </div>
                ))}
              </div>

              <div className="mt-4 bg-gray-800/50 border border-gray-700 rounded-md p-4">
                <p className="font-medium mb-2">Test Summary</p>
                <pre className="text-xs text-gray-400 whitespace-pre-wrap">
                  {testResults.summary}
                </pre>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default PaymentSystemTests;
