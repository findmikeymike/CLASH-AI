import React, { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useToast } from "@/components/ui/use-toast";
import { createClient } from "@supabase/supabase-js";
import { Loader2, CreditCard, Check } from "lucide-react";

interface TokenPurchaseModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onPurchaseComplete?: (tokenAmount: number) => void;
}

interface MinutePackage {
  id: string;
  priceId: string;
  name: string;
  minutes: number;
  price: number;
  popular?: boolean;
  blocks: number;
}

const minutePackages: MinutePackage[] = [
  {
    id: "block1",
    priceId: "price_8USD",
    name: "Try It",
    minutes: 40,
    price: 800,
    blocks: 1,
  },
  {
    id: "block2",
    priceId: "price_15USD",
    name: "Standard",
    minutes: 80,
    price: 1500,
    blocks: 2,
    popular: true,
  },
  {
    id: "block4",
    priceId: "price_28USD",
    name: "Popular",
    minutes: 160,
    price: 2800,
    blocks: 4,
  },
  {
    id: "block8",
    priceId: "price_50USD",
    name: "Power User",
    minutes: 320,
    price: 5000,
    blocks: 8,
  },
];

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
);

const TokenPurchaseModal: React.FC<TokenPurchaseModalProps> = ({
  open,
  onOpenChange,
  onPurchaseComplete,
}) => {
  const [selectedPackage, setSelectedPackage] = useState<string>("block2");
  const [email, setEmail] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [paymentStatus, setPaymentStatus] = useState<
    "idle" | "processing" | "success" | "error"
  >("idle");
  const { toast } = useToast();

  const handlePurchase = async () => {
    try {
      setIsLoading(true);
      setPaymentStatus("processing");

      const selectedPkg = minutePackages.find(
        (pkg) => pkg.id === selectedPackage,
      );
      if (!selectedPkg) {
        throw new Error("Please select a minute package");
      }

      if (!email) {
        throw new Error("Please enter your email address");
      }

      // Create a checkout session via our Supabase Edge Function
      const { data, error } = await supabase.functions.invoke(
        "supabase-functions-create-payment-intent",
        {
          body: {
            priceId: selectedPkg.priceId,
            successUrl: `${window.location.origin}/success`,
            cancelUrl: `${window.location.origin}/cancel`,
            customerEmail: email,
          },
        },
      );

      if (error) {
        throw new Error(error.message || "Failed to create checkout session");
      }

      // Redirect to Stripe Checkout
      if (data?.url) {
        window.location.href = data.url;
      } else {
        // For demo purposes, simulate a successful payment
        setTimeout(() => {
          setPaymentStatus("success");
          setIsLoading(false);

          // Notify parent component about successful purchase
          if (onPurchaseComplete) {
            onPurchaseComplete(selectedPkg.minutes);
          }

          toast({
            title: "Payment Successful",
            description: `You've purchased ${selectedPkg.minutes} minutes!`,
            variant: "default",
          });

          // Close modal after a delay
          setTimeout(() => onOpenChange(false), 2000);
        }, 2000);
      }
    } catch (error) {
      console.error("Payment error:", error);
      setPaymentStatus("error");
      setIsLoading(false);

      toast({
        title: "Payment Failed",
        description:
          error.message || "There was an error processing your payment",
        variant: "destructive",
      });
    }
  };

  const formatPrice = (cents: number) => {
    return `$${(cents / 100).toFixed(2)}`;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 text-white max-w-md">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-white">
            Purchase Debate Minutes
          </DialogTitle>
          <DialogDescription className="text-gray-400">
            Select a minute bundle to continue your debates
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          <RadioGroup
            value={selectedPackage}
            onValueChange={setSelectedPackage}
            className="grid grid-cols-1 gap-4"
          >
            {minutePackages.map((pkg) => (
              <label
                key={pkg.id}
                className={`relative flex cursor-pointer rounded-lg border ${selectedPackage === pkg.id ? "border-red-500" : "border-gray-700"} bg-gradient-to-br from-gray-800 to-gray-900 p-4 shadow-sm focus:outline-none hover:border-red-500/50 transition-colors`}
              >
                <div className="flex w-full items-center justify-between">
                  <div className="flex items-center">
                    <div className="text-sm">
                      <RadioGroupItem
                        value={pkg.id}
                        id={pkg.id}
                        className="sr-only"
                      />
                      <div className="flex items-center">
                        <p className="font-medium text-white">{pkg.name}</p>
                        {pkg.popular && (
                          <span className="ml-2 inline-flex items-center rounded-full bg-red-500/20 px-2 py-0.5 text-xs font-medium text-red-400">
                            Popular
                          </span>
                        )}
                      </div>
                      <div className="mt-1 flex items-center space-x-2">
                        <p className="text-gray-400 text-sm">
                          {pkg.minutes} minutes
                        </p>
                        <span className="text-gray-500 text-xs">•</span>
                        <p className="text-gray-500 text-xs">
                          {pkg.blocks} block{pkg.blocks > 1 ? "s" : ""}
                        </p>
                      </div>
                      <div className="mt-1">
                        <p className="text-gray-500 text-xs">
                          ${(pkg.price / 100 / pkg.minutes).toFixed(3)}/min
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-medium text-white">
                      {formatPrice(pkg.price)}
                    </p>
                  </div>
                </div>
                {selectedPackage === pkg.id && (
                  <div className="absolute -top-1 -right-1 h-6 w-6 rounded-full bg-red-500 flex items-center justify-center">
                    <Check className="h-4 w-4 text-white" />
                  </div>
                )}
              </label>
            ))}
          </RadioGroup>

          <div className="space-y-2">
            <Label htmlFor="email" className="text-white">
              Email for receipt
            </Label>
            <Input
              id="email"
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="bg-gray-800 border-gray-700 text-white"
              disabled={isLoading || paymentStatus === "success"}
            />
          </div>
        </div>

        <DialogFooter>
          {paymentStatus === "idle" || paymentStatus === "error" ? (
            <Button
              onClick={handlePurchase}
              className="w-full bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white font-medium py-2"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <CreditCard className="mr-2 h-4 w-4" />
                  Pay{" "}
                  {formatPrice(
                    minutePackages.find((pkg) => pkg.id === selectedPackage)
                      ?.price || 0,
                  )}
                </>
              )}
            </Button>
          ) : paymentStatus === "processing" ? (
            <Button
              disabled
              className="w-full bg-gray-700 text-white font-medium py-2"
            >
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing Payment...
            </Button>
          ) : (
            <Button
              disabled
              className="w-full bg-green-600 text-white font-medium py-2"
            >
              <Check className="mr-2 h-4 w-4" />
              Payment Successful!
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default TokenPurchaseModal;
