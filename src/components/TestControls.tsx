import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  simulateElevenLabsApiCall,
  listenForApiCallEvents,
} from "@/utils/testApiCall";
import { Beaker, AlertCircle } from "lucide-react";

interface TestControlsProps {
  onMetricsUpdate?: (metrics: any) => void;
}

const TestControls: React.FC<TestControlsProps> = ({ onMetricsUpdate }) => {
  const [duration, setDuration] = useState<number>(500);
  const [testResults, setTestResults] = useState<
    Array<{ time: string; message: string }>
  >([]);
  const [isListening, setIsListening] = useState<boolean>(false);
  const [removeListener, setRemoveListener] = useState<(() => void) | null>(
    null,
  );

  const runTest = async () => {
    try {
      addTestResult(
        "Starting API call simulation with duration: " + duration + "ms",
      );
      await simulateElevenLabsApiCall(duration);
      addTestResult("Simulation completed. Check for events in the console.");
    } catch (error) {
      addTestResult(
        "Error: " + (error instanceof Error ? error.message : String(error)),
      );
    }
  };

  const toggleEventListener = () => {
    if (isListening) {
      // Remove the listener if it exists
      if (removeListener) {
        removeListener();
        setRemoveListener(null);
      }
      setIsListening(false);
      addTestResult("Event listener removed");
    } else {
      // Add a new listener
      const remove = listenForApiCallEvents((event: CustomEvent) => {
        const { duration, url } = event.detail;
        addTestResult(`Event received: ${url} took ${duration}ms`);

        // If onMetricsUpdate is provided, call it with mock metrics
        if (onMetricsUpdate) {
          const estimatedTokens = Math.ceil(duration / 100); // Same formula as in DebateInterface
          onMetricsUpdate({
            widgetLoadTime: 1200,
            sessionDuration: 60,
            responseCount: 1,
            averageResponseTime: duration / 1000,
            tokenUsage: estimatedTokens,
            totalApiCallTime: duration,
          });
        }
      });

      setRemoveListener(() => remove);
      setIsListening(true);
      addTestResult("Event listener added. Run a test to see events.");
    }
  };

  const addTestResult = (message: string) => {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    setTestResults((prev) =>
      [{ time: timeString, message }, ...prev].slice(0, 10),
    );
  };

  const clearResults = () => {
    setTestResults([]);
  };

  return (
    <Card className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative">
      <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
      <CardHeader className="pb-3 border-b border-gray-800 relative z-10">
        <CardTitle className="text-lg font-bold flex items-center text-white">
          <Beaker className="h-5 w-5 mr-2 text-purple-500" />
          ElevenLabs API Test Controls
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-5 relative z-10">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="duration">API Call Duration (ms)</Label>
              <Input
                id="duration"
                type="number"
                value={duration}
                onChange={(e) => {
                  const newValue = e.target.value;
                  console.log("Input changed to:", newValue);
                  setDuration(newValue === "" ? 0 : parseInt(newValue) || 500);
                }}
                className="bg-gray-800 border-gray-700 text-white"
                min="0"
                step="100"
                placeholder="Enter duration in ms"
              />
            </div>
            <div className="flex items-end">
              <Button
                onClick={runTest}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white"
              >
                Simulate API Call
              </Button>
            </div>
          </div>

          <div className="flex justify-between">
            <Button
              onClick={toggleEventListener}
              variant={isListening ? "destructive" : "outline"}
              className={
                isListening
                  ? "bg-red-600 hover:bg-red-700"
                  : "border-purple-500 text-purple-500"
              }
            >
              {isListening ? "Stop Listening" : "Start Event Listener"}
            </Button>

            <Button
              onClick={clearResults}
              variant="outline"
              className="border-gray-700 text-gray-400 hover:text-white"
            >
              Clear Results
            </Button>
          </div>

          <div className="mt-4">
            <h3 className="text-sm font-medium text-gray-400 mb-2">
              Test Results:
            </h3>
            <div className="bg-gray-900 border border-gray-800 rounded-md p-3 max-h-60 overflow-y-auto">
              {testResults.length > 0 ? (
                <div className="space-y-2">
                  {testResults.map((result, index) => (
                    <div key={index} className="text-sm">
                      <span className="text-gray-500">[{result.time}]</span>{" "}
                      {result.message}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center justify-center py-4 text-gray-500">
                  <AlertCircle className="h-4 w-4 mr-2" />
                  No test results yet
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default TestControls;
