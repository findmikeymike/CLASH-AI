import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { CalendarDays } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "../components/ui/avatar";
import { Button } from "../components/ui/button";
import { HoverCard, HoverCardContent, HoverCardTrigger, } from "../components/ui/hover-card";
const meta = {
    title: "ui/HoverCard",
    component: HoverCard,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: () => (_jsxs(HoverCard, { children: [_jsx(HoverCardTrigger, { asChild: true, children: _jsx(Button, { variant: "link", children: "@nextjs" }) }), _jsx(HoverCardContent, { className: "w-80", children: _jsxs("div", { className: "flex justify-between space-x-4", children: [_jsxs(Avatar, { children: [_jsx(AvatarImage, { src: "https://github.com/vercel.png" }), _jsx(AvatarFallback, { children: "VC" })] }), _jsxs("div", { className: "space-y-1", children: [_jsx("h4", { className: "text-sm font-semibold", children: "@nextjs" }), _jsx("p", { className: "text-sm", children: "The React Framework \u2013 created and maintained by @vercel." }), _jsxs("div", { className: "flex items-center pt-2", children: [_jsx(CalendarDays, { className: "mr-2 h-4 w-4 opacity-70" }), " ", _jsx("span", { className: "text-xs text-slate-500 dark:text-slate-400", children: "Joined December 2021" })] })] })] }) })] })),
    args: {},
};
