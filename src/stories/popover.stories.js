import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { Settings2 } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Popover, PopoverContent, PopoverTrigger, } from "../components/ui/popover";
const meta = {
    title: "ui/Popover",
    component: Popover,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: () => (_jsxs(Popover, { children: [_jsx(PopoverTrigger, { asChild: true, children: _jsxs(Button, { variant: "outline", className: "w-10 rounded-full p-0", children: [_jsx(Settings2, { className: "h-4 w-4" }), _jsx("span", { className: "sr-only", children: "Open popover" })] }) }), _jsx(PopoverContent, { className: "w-80", children: _jsxs("div", { className: "grid gap-4", children: [_jsxs("div", { className: "space-y-2", children: [_jsx("h4", { className: "font-medium leading-none", children: "Dimensions" }), _jsx("p", { className: "text-sm text-slate-500 dark:text-slate-400", children: "Set the dimensions for the layer." })] }), _jsxs("div", { className: "grid gap-2", children: [_jsxs("div", { className: "grid grid-cols-3 items-center gap-4", children: [_jsx(Label, { htmlFor: "width", children: "Width" }), _jsx(Input, { id: "width", defaultValue: "100%", className: "col-span-2 h-8" })] }), _jsxs("div", { className: "grid grid-cols-3 items-center gap-4", children: [_jsx(Label, { htmlFor: "maxWidth", children: "Max. width" }), _jsx(Input, { id: "maxWidth", defaultValue: "300px", className: "col-span-2 h-8" })] }), _jsxs("div", { className: "grid grid-cols-3 items-center gap-4", children: [_jsx(Label, { htmlFor: "height", children: "Height" }), _jsx(Input, { id: "height", defaultValue: "25px", className: "col-span-2 h-8" })] }), _jsxs("div", { className: "grid grid-cols-3 items-center gap-4", children: [_jsx(Label, { htmlFor: "maxHeight", children: "Max. height" }), _jsx(Input, { id: "maxHeight", defaultValue: "none", className: "col-span-2 h-8" })] })] })] }) })] })),
    args: {},
};
