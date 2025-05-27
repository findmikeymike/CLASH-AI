import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import React from "react";
import { ScrollArea } from "../components/ui/scroll-area";
import { Separator } from "../components/ui/separator";
const meta = {
    title: "ui/ScrollArea",
    component: ScrollArea,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: () => (_jsx(ScrollArea, { className: "h-72 w-48 rounded-md border border-slate-100 dark:border-slate-700", children: _jsxs("div", { className: "p-4", children: [_jsx("h4", { className: "mb-4 text-sm font-medium leading-none", children: "Tags" }), Array.from({ length: 50 })
                    .map((_, i, a) => `v1.2.0-beta.${a.length - i}`)
                    .map((tag) => (_jsxs(React.Fragment, { children: [_jsx("div", { className: "text-sm", children: tag }, tag), _jsx(Separator, { className: "my-2" })] })))] }) })),
    args: {},
};
