import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { Plus } from "lucide-react";
import { Button } from "../components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider, } from "../components/ui/tooltip";
const meta = {
    title: "ui/Tooltip",
    component: Tooltip,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: () => (_jsx(TooltipProvider, { children: _jsxs(Tooltip, { children: [_jsx(TooltipTrigger, { asChild: true, children: _jsxs(Button, { variant: "outline", className: "w-10 rounded-full p-0", children: [_jsx(Plus, { className: "h-4 w-4" }), _jsx("span", { className: "sr-only", children: "Add" })] }) }), _jsx(TooltipContent, { children: _jsx("p", { children: "Add to library" }) })] }) })),
    args: {},
};
