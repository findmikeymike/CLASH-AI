import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle2, XCircle, Activity } from "lucide-react";
import { checkPaymentSystemHealth } from "@/utils/paymentSystemHealth";

interface HealthCheckResult {
  component: string;
  healthy: boolean;
  message: string;
}

interface HealthCheckSummary {
  healthy: boolean;
  results: HealthCheckResult[];
  summary: string;
}

const PaymentSystemHealth: React.FC = () => {
  const [isChecking, setIsChecking] = useState(false);
  const [healthStatus, setHealthStatus] = useState<HealthCheckSummary | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

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
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <Card className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 shadow-xl overflow-hidden relative">
      <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>
      <CardHeader className="pb-3 border-b border-gray-800 relative z-10">
        <CardTitle className="text-lg font-bold flex items-center text-white">
          <Activity className="h-5 w-5 mr-2 text-blue-500" />
          Payment System Health
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-5 relative z-10">
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-gray-400">System health status</p>
              {lastChecked && (
                <p className="text-xs text-gray-500 mt-1">
                  Last checked: {lastChecked.toLocaleTimeString()}
                </p>
              )}
            </div>
            <Button
              onClick={runHealthCheck}
              disabled={isChecking}
              className={
                isChecking ? "bg-gray-700" : "bg-blue-600 hover:bg-blue-700"
              }
              size="sm"
            >
              {isChecking ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Checking...
                </>
              ) : (
                <>Refresh Status</>
              )}
            </Button>
          </div>

          {error && (
            <div className="bg-red-900/30 border border-red-800 rounded-md p-4 text-red-300">
              <p className="font-medium flex items-center">
                <XCircle className="h-5 w-5 mr-2" />
                Error Checking Health
              </p>
              <p className="mt-2 text-sm">{error}</p>
            </div>
          )}

          {healthStatus && (
            <div className="space-y-4">
              <div
                className={`p-4 rounded-md border ${healthStatus.healthy ? "bg-green-900/30 border-green-800" : "bg-red-900/30 border-red-800"}`}
              >
                <p className="font-medium flex items-center">
                  {healthStatus.healthy ? (
                    <>
                      <CheckCircle2 className="h-5 w-5 mr-2 text-green-500" />
                      <span className="text-green-400">
                        All Systems Operational
                      </span>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-5 w-5 mr-2 text-red-500" />
                      <span className="text-red-400">
                        System Degradation Detected
                      </span>
                    </>
                  )}
                </p>
              </div>

              <div className="space-y-3">
                {healthStatus.results.map((result, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-md border ${result.healthy ? "bg-gray-800/50 border-gray-700" : "bg-red-900/20 border-red-800/30"}`}
                  >
                    <div className="flex justify-between items-center">
                      <p className="font-medium flex items-center">
                        {result.healthy ? (
                          <CheckCircle2 className="h-4 w-4 mr-2 text-green-500" />
                        ) : (
                          <XCircle className="h-4 w-4 mr-2 text-red-500" />
                        )}
                        {result.component}
                      </p>
                      <Badge
                        variant={result.healthy ? "outline" : "destructive"}
                        className={
                          result.healthy
                            ? "border-green-500 text-green-400"
                            : ""
                        }
                      >
                        {result.healthy ? "HEALTHY" : "DEGRADED"}
                      </Badge>
                    </div>
                    <p className="mt-2 text-sm text-gray-400">
                      {result.message}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default PaymentSystemHealth;
