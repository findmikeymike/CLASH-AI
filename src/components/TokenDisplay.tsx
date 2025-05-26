import React from "react";
import { Button } from "@/components/ui/button";
import { CreditCard, Zap } from "lucide-react";

interface TokenDisplayProps {
  tokenBalance: number;
  onPurchaseClick: () => void;
}

const TokenDisplay: React.FC<TokenDisplayProps> = ({
  tokenBalance = 0,
  onPurchaseClick,
}) => {
  return (
    <div className="flex items-center space-x-2 bg-gradient-to-r from-gray-900/80 to-black/80 backdrop-blur-sm px-4 py-2 rounded-lg border border-gray-800 shadow-md">
      <div className="flex items-center">
        <Zap className="h-4 w-4 text-yellow-500 mr-1" />
        <span className="text-sm font-bold text-white">{tokenBalance}</span>
        <span className="text-xs text-gray-400 ml-1">min</span>
      </div>
      <Button
        variant="outline"
        size="sm"
        onClick={onPurchaseClick}
        className="border-white/30 bg-black/50 text-white hover:bg-yellow-600 hover:border-yellow-500 hover:text-black transition-all duration-200 backdrop-blur-sm"
      >
        <CreditCard className="h-3 w-3 mr-1" />
        Buy
      </Button>
    </div>
  );
};

export default TokenDisplay;
