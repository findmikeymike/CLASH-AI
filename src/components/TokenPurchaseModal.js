import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useToast } from "@/components/ui/use-toast";
import { createClient } from "@supabase/supabase-js";
import { Loader2, CreditCard, Check } from "lucide-react";
const minutePackages = [
    {
        id: "block1",
        priceId: import.meta.env.VITE_STRIPE_PRICE_10MIN || 'price_1OvCXKGLCcFoteZDOQYPGvHB',
        name: "Try It",
        minutes: 40,
        price: 800,
        blocks: 1,
    },
    {
        id: "block2",
        priceId: import.meta.env.VITE_STRIPE_PRICE_30MIN || 'price_1OvCXkGLCcFoteZDnPvtTqhB',
        name: "Standard",
        minutes: 80,
        price: 1500,
        blocks: 2,
        popular: true,
    },
    {
        id: "block4",
        priceId: import.meta.env.VITE_STRIPE_PRICE_60MIN || 'price_1OvCY9GLCcFoteZDfgvHOFzD',
        name: "Popular",
        minutes: 160,
        price: 2800,
        blocks: 4,
    },
    {
        id: "block8",
        priceId: "price_1OvCYaGLCcFoteZDdgvJYhzP", // Using a fixed price ID for the largest package
        name: "Power User",
        minutes: 320,
        price: 5000,
        blocks: 8,
    },
];
const supabase = createClient(import.meta.env.VITE_SUPABASE_URL, import.meta.env.VITE_SUPABASE_ANON_KEY);
const TokenPurchaseModal = ({ open, onOpenChange, onPurchaseComplete, }) => {
    const [selectedPackage, setSelectedPackage] = useState("block2");
    const [email, setEmail] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [paymentStatus, setPaymentStatus] = useState("idle");
    const { toast } = useToast();
    const handlePurchase = async () => {
        try {
            setIsLoading(true);
            setPaymentStatus("processing");
            const selectedPkg = minutePackages.find((pkg) => pkg.id === selectedPackage);
            if (!selectedPkg) {
                throw new Error("Please select a minute package");
            }
            if (!email) {
                throw new Error("Please enter your email address");
            }
            // Create a checkout session via our Supabase Edge Function
            const { data, error } = await supabase.functions.invoke("supabase-functions-create-payment-intent", {
                body: {
                    priceId: selectedPkg.priceId,
                    successUrl: `${window.location.origin}/success`,
                    cancelUrl: `${window.location.origin}/cancel`,
                    customerEmail: email,
                },
            });
            if (error) {
                throw new Error(error.message || "Failed to create checkout session");
            }
            // Redirect to Stripe Checkout
            if (data?.url) {
                window.location.href = data.url;
            }
            else {
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
        }
        catch (error) {
            console.error("Payment error:", error);
            setPaymentStatus("error");
            setIsLoading(false);
            toast({
                title: "Payment Failed",
                description: error.message || "There was an error processing your payment",
                variant: "destructive",
            });
        }
    };
    const formatPrice = (cents) => {
        return `$${(cents / 100).toFixed(2)}`;
    };
    return (_jsx(Dialog, { open: open, onOpenChange: onOpenChange, children: _jsxs(DialogContent, { className: "bg-gradient-to-br from-gray-900 to-black border border-gray-800 text-white max-w-md", children: [_jsxs(DialogHeader, { children: [_jsx(DialogTitle, { className: "text-2xl font-bold text-white", children: "Purchase Debate Minutes" }), _jsx(DialogDescription, { className: "text-gray-400", children: "Select a minute bundle to continue your debates" })] }), _jsxs("div", { className: "space-y-6", children: [_jsx(RadioGroup, { value: selectedPackage, onValueChange: setSelectedPackage, className: "grid grid-cols-1 gap-4", children: minutePackages.map((pkg) => (_jsxs("label", { className: `relative flex cursor-pointer rounded-lg border ${selectedPackage === pkg.id ? "border-red-500" : "border-gray-700"} bg-gradient-to-br from-gray-800 to-gray-900 p-4 shadow-sm focus:outline-none hover:border-red-500/50 transition-colors`, children: [_jsxs("div", { className: "flex w-full items-center justify-between", children: [_jsx("div", { className: "flex items-center", children: _jsxs("div", { className: "text-sm", children: [_jsx(RadioGroupItem, { value: pkg.id, id: pkg.id, className: "sr-only" }), _jsxs("div", { className: "flex items-center", children: [_jsx("p", { className: "font-medium text-white", children: pkg.name }), pkg.popular && (_jsx("span", { className: "ml-2 inline-flex items-center rounded-full bg-red-500/20 px-2 py-0.5 text-xs font-medium text-red-400", children: "Popular" }))] }), _jsxs("div", { className: "mt-1 flex items-center space-x-2", children: [_jsxs("p", { className: "text-gray-400 text-sm", children: [pkg.minutes, " minutes"] }), _jsx("span", { className: "text-gray-500 text-xs", children: "\u2022" }), _jsxs("p", { className: "text-gray-500 text-xs", children: [pkg.blocks, " block", pkg.blocks > 1 ? "s" : ""] })] }), _jsx("div", { className: "mt-1", children: _jsxs("p", { className: "text-gray-500 text-xs", children: ["$", (pkg.price / 100 / pkg.minutes).toFixed(3), "/min"] }) })] }) }), _jsx("div", { className: "text-right", children: _jsx("p", { className: "text-lg font-medium text-white", children: formatPrice(pkg.price) }) })] }), selectedPackage === pkg.id && (_jsx("div", { className: "absolute -top-1 -right-1 h-6 w-6 rounded-full bg-red-500 flex items-center justify-center", children: _jsx(Check, { className: "h-4 w-4 text-white" }) }))] }, pkg.id))) }), _jsxs("div", { className: "space-y-2", children: [_jsx(Label, { htmlFor: "email", className: "text-white", children: "Email for receipt" }), _jsx(Input, { id: "email", type: "email", placeholder: "your@email.com", value: email, onChange: (e) => setEmail(e.target.value), className: "bg-gray-800 border-gray-700 text-white", disabled: isLoading || paymentStatus === "success" })] })] }), _jsx(DialogFooter, { children: paymentStatus === "idle" || paymentStatus === "error" ? (_jsx(Button, { onClick: handlePurchase, className: "w-full bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white font-medium py-2", disabled: isLoading, children: isLoading ? (_jsxs(_Fragment, { children: [_jsx(Loader2, { className: "mr-2 h-4 w-4 animate-spin" }), "Processing..."] })) : (_jsxs(_Fragment, { children: [_jsx(CreditCard, { className: "mr-2 h-4 w-4" }), "Pay", " ", formatPrice(minutePackages.find((pkg) => pkg.id === selectedPackage)
                                    ?.price || 0)] })) })) : paymentStatus === "processing" ? (_jsxs(Button, { disabled: true, className: "w-full bg-gray-700 text-white font-medium py-2", children: [_jsx(Loader2, { className: "mr-2 h-4 w-4 animate-spin" }), "Processing Payment..."] })) : (_jsxs(Button, { disabled: true, className: "w-full bg-green-600 text-white font-medium py-2", children: [_jsx(Check, { className: "mr-2 h-4 w-4" }), "Payment Successful!"] })) })] }) }));
};
export default TokenPurchaseModal;
