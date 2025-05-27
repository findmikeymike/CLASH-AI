import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { trackCallUsage, getRemainingMinutes, addMinutes, initializeUserMinutes } from "@/utils/usageTracking";
import { useToast } from "@/components/ui/use-toast";
import { Timer, Zap, Plus, Play, Square, RotateCcw, Database } from "lucide-react";

const TestUsageTracking: React.FC = () => {
  const { toast } = useToast();
  const [userId] = useState<string>(() => localStorage.getItem('test_user_id') || crypto.randomUUID());
  const [remainingMinutes, setRemainingMinutes] = useState<number>(0);
  const [isCallActive, setIsCallActive] = useState<boolean>(false);
  const [currentCallId, setCurrentCallId] = useState<string | null>(null);
  const [callStartTime, setCallStartTime] = useState<number | null>(null);
  const [callDuration, setCallDuration] = useState<number>(0);
  const [callHistory, setCallHistory] = useState<any[]>([]);

  // Save user ID to localStorage for persistence
  useEffect(() => {
    localStorage.setItem('test_user_id', userId);
  }, [userId]);

  // Initialize user minutes
  useEffect(() => {
    const initialize = async () => {
      try {
        const minutes = await initializeUserMinutes(userId);
        setRemainingMinutes(minutes);
        
        // Load call history from localStorage
        const history = JSON.parse(localStorage.getItem('call_sessions') || '[]');
        const userCalls = history.filter((call: any) => call.userId === userId);
        setCallHistory(userCalls);
      } catch (error) {
        console.error("Error initializing:", error);
      }
    };
    
    initialize();
  }, [userId]);

  // Update call duration timer
  useEffect(() => {
    let intervalId: number | null = null;
    
    if (isCallActive && callStartTime) {
      intervalId = window.setInterval(() => {
        const currentDuration = Math.floor((Date.now() - callStartTime) / 1000);
        setCallDuration(currentDuration);
      }, 1000);
    }
    
    return () => {
      if (intervalId !== null) {
        clearInterval(intervalId);
      }
    };
  }, [isCallActive, callStartTime]);

  // Start a call
  const handleStartCall = async () => {
    try {
      const result = await trackCallUsage(userId, "start", undefined, "test-character");
      
      if (!result?.canStart) {
        toast({
          title: "Insufficient Minutes",
          description: "You don't have enough minutes to start a call.",
          variant: "destructive",
        });
        return;
      }
      
      setCurrentCallId(result.callId);
      setRemainingMinutes(result.remainingMinutes);
      setIsCallActive(true);
      setCallStartTime(Date.now());
      setCallDuration(0);
      
      toast({
        title: "Call Started",
        description: "Call tracking has begun.",
      });
    } catch (error) {
      console.error("Error starting call:", error);
      toast({
        title: "Error",
        description: "Failed to start call tracking.",
        variant: "destructive",
      });
    }
  };

  // End a call
  const handleEndCall = async () => {
    if (!currentCallId) return;
    
    try {
      const result = await trackCallUsage(userId, "end", currentCallId);
      
      if (result) {
        setRemainingMinutes(result.remainingMinutes);
        
        toast({
          title: "Call Ended",
          description: `You used ${result.minutesUsed} minute${result.minutesUsed !== 1 ? 's' : ''}. You have ${result.remainingMinutes} minute${result.remainingMinutes !== 1 ? 's' : ''} remaining.`,
        });
        
        // Update call history
        const history = JSON.parse(localStorage.getItem('call_sessions') || '[]');
        const userCalls = history.filter((call: any) => call.userId === userId);
        setCallHistory(userCalls);
      }
    } catch (error) {
      console.error("Error ending call:", error);
      toast({
        title: "Error",
        description: "Failed to end call tracking.",
        variant: "destructive",
      });
    }
    
    setIsCallActive(false);
    setCurrentCallId(null);
    setCallStartTime(null);
  };

  // Add minutes
  const handleAddMinutes = async (minutes: number) => {
    try {
      const newTotal = await addMinutes(userId, minutes);
      setRemainingMinutes(newTotal);
      
      toast({
        title: "Minutes Added",
        description: `Added ${minutes} minute${minutes !== 1 ? 's' : ''}. You now have ${newTotal} minute${newTotal !== 1 ? 's' : ''}.`,
      });
    } catch (error) {
      console.error("Error adding minutes:", error);
      toast({
        title: "Error",
        description: "Failed to add minutes.",
        variant: "destructive",
      });
    }
  };

  // Reset user data (for testing)
  const handleReset = () => {
    localStorage.removeItem(`user_minutes_${userId}`);
    
    // Filter out this user's calls from call_sessions
    const allCalls = JSON.parse(localStorage.getItem('call_sessions') || '[]');
    const otherCalls = allCalls.filter((call: any) => call.userId !== userId);
    localStorage.setItem('call_sessions', JSON.stringify(otherCalls));
    
    setCallHistory([]);
    initializeUserMinutes(userId, 10).then(setRemainingMinutes);
    
    toast({
      title: "Reset Complete",
      description: "User data has been reset with 10 initial minutes.",
    });
  };

  // Format duration as MM:SS
  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="container mx-auto py-8">
      <Card className="max-w-2xl mx-auto bg-gray-900 border-gray-800 text-white">
        <CardHeader>
          <CardTitle className="text-2xl flex items-center">
            <Database className="mr-2 h-5 w-5 text-purple-400" />
            Usage Tracking Test
          </CardTitle>
          <CardDescription className="text-gray-400">
            Test the payment and usage tracking system
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* User Info */}
          <div className="bg-gray-800 p-4 rounded-md">
            <h3 className="text-lg font-medium mb-2">User Information</h3>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <p className="text-sm text-gray-400">User ID:</p>
                <p className="text-xs font-mono text-gray-300 truncate">{userId}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Remaining Minutes:</p>
                <div className="flex items-center">
                  <Zap className="h-4 w-4 text-yellow-400 mr-1" />
                  <p className="text-xl font-bold text-yellow-300">{remainingMinutes}</p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Call Controls */}
          <div className="bg-gray-800 p-4 rounded-md">
            <h3 className="text-lg font-medium mb-2">Call Controls</h3>
            <div className="flex items-center justify-between">
              <div>
                {isCallActive && (
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline" className="bg-red-900/30 text-red-400 border-red-700">
                      <span className="animate-pulse mr-1">●</span> LIVE
                    </Badge>
                    <div className="flex items-center">
                      <Timer className="h-4 w-4 text-gray-400 mr-1" />
                      <span className="text-gray-300">{formatDuration(callDuration)}</span>
                    </div>
                  </div>
                )}
              </div>
              <div className="flex space-x-2">
                {!isCallActive ? (
                  <Button 
                    onClick={handleStartCall} 
                    className="bg-green-600 hover:bg-green-700"
                    disabled={remainingMinutes <= 0}
                  >
                    <Play className="h-4 w-4 mr-1" /> Start Call
                  </Button>
                ) : (
                  <Button 
                    onClick={handleEndCall} 
                    className="bg-red-600 hover:bg-red-700"
                  >
                    <Square className="h-4 w-4 mr-1" /> End Call
                  </Button>
                )}
              </div>
            </div>
          </div>
          
          {/* Add Minutes */}
          <div className="bg-gray-800 p-4 rounded-md">
            <h3 className="text-lg font-medium mb-2">Add Minutes (Simulate Payment)</h3>
            <div className="flex flex-wrap gap-2">
              <Button 
                onClick={() => handleAddMinutes(10)} 
                variant="outline" 
                className="border-purple-700 text-purple-400 hover:bg-purple-900/30"
              >
                <Plus className="h-4 w-4 mr-1" /> 10 Minutes
              </Button>
              <Button 
                onClick={() => handleAddMinutes(30)} 
                variant="outline" 
                className="border-purple-700 text-purple-400 hover:bg-purple-900/30"
              >
                <Plus className="h-4 w-4 mr-1" /> 30 Minutes
              </Button>
              <Button 
                onClick={() => handleAddMinutes(60)} 
                variant="outline" 
                className="border-purple-700 text-purple-400 hover:bg-purple-900/30"
              >
                <Plus className="h-4 w-4 mr-1" /> 60 Minutes
              </Button>
            </div>
          </div>
          
          {/* Call History */}
          {callHistory.length > 0 && (
            <div className="bg-gray-800 p-4 rounded-md">
              <h3 className="text-lg font-medium mb-2">Call History</h3>
              <div className="space-y-2">
                {callHistory.map((call, index) => (
                  <div key={index} className="bg-gray-900 p-2 rounded border border-gray-700 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Call ID:</span>
                      <span className="text-gray-300 font-mono text-xs truncate max-w-[200px]">{call.id}</span>
                    </div>
                    {call.startTime && (
                      <div className="flex justify-between">
                        <span className="text-gray-400">Start:</span>
                        <span className="text-gray-300">{new Date(call.startTime).toLocaleTimeString()}</span>
                      </div>
                    )}
                    {call.endTime && (
                      <div className="flex justify-between">
                        <span className="text-gray-400">End:</span>
                        <span className="text-gray-300">{new Date(call.endTime).toLocaleTimeString()}</span>
                      </div>
                    )}
                    {call.minutesUsed && (
                      <div className="flex justify-between">
                        <span className="text-gray-400">Minutes Used:</span>
                        <span className="text-yellow-300 font-bold">{call.minutesUsed}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
        
        <CardFooter className="flex justify-between border-t border-gray-800 pt-4">
          <Button 
            onClick={handleReset} 
            variant="destructive"
            size="sm"
          >
            <RotateCcw className="h-4 w-4 mr-1" /> Reset Data
          </Button>
          <div className="text-xs text-gray-500">
            Test component for usage tracking
          </div>
        </CardFooter>
      </Card>
    </div>
  );
};

export default TestUsageTracking;
