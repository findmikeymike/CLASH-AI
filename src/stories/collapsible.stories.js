import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { ChevronsUpDown } from "lucide-react";
import { Button } from "../components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger, } from "../components/ui/collapsible";
const meta = {
    title: "ui/Collapsible",
    component: Collapsible,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Closed = {
    render: (args) => (_jsxs(Collapsible, { ...args, className: "w-[350px] space-y-2", children: [_jsxs("div", { className: "flex items-center justify-between space-x-4 px-4", children: [_jsx("h4", { className: "text-sm font-semibold", children: "@peduarte starred 3 repositories" }), _jsx(CollapsibleTrigger, { asChild: true, children: _jsxs(Button, { variant: "ghost", size: "sm", className: "w-9 p-0", children: [_jsx(ChevronsUpDown, { className: "h-4 w-4" }), _jsx("span", { className: "sr-only", children: "Toggle" })] }) })] }), _jsx("div", { className: "rounded-md border border-slate-200 px-4 py-3 font-mono text-sm dark:border-slate-700", children: "@radix-ui/primitives" }), _jsxs(CollapsibleContent, { className: "space-y-2", children: [_jsx("div", { className: "rounded-md border border-slate-200 px-4 py-3 font-mono text-sm dark:border-slate-700", children: "@radix-ui/colors" }), _jsx("div", { className: "rounded-md border border-slate-200 px-4 py-3 font-mono text-sm dark:border-slate-700", children: "@stitches/react" })] })] })),
    args: {
        open: false,
        onOpenChange: () => null,
    },
};
export const Open = {
    render: (args) => (_jsxs(Collapsible, { ...args, className: "w-[350px] space-y-2", children: [_jsxs("div", { className: "flex items-center justify-between space-x-4 px-4", children: [_jsx("h4", { className: "text-sm font-semibold", children: "@peduarte starred 3 repositories" }), _jsx(CollapsibleTrigger, { asChild: true, children: _jsxs(Button, { variant: "ghost", size: "sm", className: "w-9 p-0", children: [_jsx(ChevronsUpDown, { className: "h-4 w-4" }), _jsx("span", { className: "sr-only", children: "Toggle" })] }) })] }), _jsx("div", { className: "rounded-md border border-slate-200 px-4 py-3 font-mono text-sm dark:border-slate-700", children: "@radix-ui/primitives" }), _jsxs(CollapsibleContent, { className: "space-y-2", children: [_jsx("div", { className: "rounded-md border border-slate-200 px-4 py-3 font-mono text-sm dark:border-slate-700", children: "@radix-ui/colors" }), _jsx("div", { className: "rounded-md border border-slate-200 px-4 py-3 font-mono text-sm dark:border-slate-700", children: "@stitches/react" })] })] })),
    args: {
        open: true,
        onOpenChange: () => null,
    },
};
