import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { BellIcon, CheckIcon } from "@radix-ui/react-icons";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle, } from "../components/ui/card";
import { Switch } from "../components/ui/switch";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue, } from "../components/ui/select";
const meta = {
    title: "ui/Card",
    component: Card,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: () => {
        return (_jsxs(Card, { className: "w-[350px]", children: [_jsxs(CardHeader, { children: [_jsx(CardTitle, { children: "Create project" }), _jsx(CardDescription, { children: "Deploy your new project in one-click." })] }), _jsx(CardContent, { children: _jsx("form", { children: _jsxs("div", { className: "grid w-full items-center gap-4", children: [_jsxs("div", { className: "flex flex-col space-y-1.5", children: [_jsx(Label, { htmlFor: "name", children: "Name" }), _jsx(Input, { id: "name", placeholder: "Name of your project" })] }), _jsxs("div", { className: "flex flex-col space-y-1.5", children: [_jsx(Label, { htmlFor: "framework", children: "Framework" }), _jsxs(Select, { children: [_jsx(SelectTrigger, { id: "framework", children: _jsx(SelectValue, { placeholder: "Select" }) }), _jsxs(SelectContent, { position: "popper", children: [_jsx(SelectItem, { value: "next", children: "Next.js" }), _jsx(SelectItem, { value: "sveltekit", children: "SvelteKit" }), _jsx(SelectItem, { value: "astro", children: "Astro" }), _jsx(SelectItem, { value: "nuxt", children: "Nuxt.js" })] })] })] })] }) }) }), _jsxs(CardFooter, { className: "flex justify-between", children: [_jsx(Button, { variant: "outline", children: "Cancel" }), _jsx(Button, { children: "Deploy" })] })] }));
    },
    args: {},
};
export const Notifications = {
    render: () => {
        return (_jsxs(Card, { className: "w-[380px]", children: [_jsxs(CardHeader, { children: [_jsx(CardTitle, { children: "Notifications" }), _jsx(CardDescription, { children: "You have 3 unread messages." })] }), _jsxs(CardContent, { className: "grid gap-4", children: [_jsxs("div", { className: " flex items-center space-x-4 rounded-md border p-4", children: [_jsx(BellIcon, {}), _jsxs("div", { className: "flex-1 space-y-1", children: [_jsx("p", { className: "text-sm font-medium leading-none", children: "Push Notifications" }), _jsx("p", { className: "text-sm text-muted-foreground", children: "Send notifications to device." })] }), _jsx(Switch, {})] }), _jsxs("div", { className: "mb-4 grid grid-cols-[25px_1fr] items-start pb-4 last:mb-0 last:pb-0", children: [_jsx("span", { className: "flex h-2 w-2 translate-y-1 rounded-full bg-sky-500" }), _jsxs("div", { className: "space-y-1", children: [_jsx("p", { className: "text-sm font-medium leading-none", children: "Your call has been confirmed." }), _jsx("p", { className: "text-sm text-muted-foreground", children: "1 hour ago" })] })] }, 1), _jsxs("div", { className: "mb-4 grid grid-cols-[25px_1fr] items-start pb-4 last:mb-0 last:pb-0", children: [_jsx("span", { className: "flex h-2 w-2 translate-y-1 rounded-full bg-sky-500" }), _jsxs("div", { className: "space-y-1", children: [_jsx("p", { className: "text-sm font-medium leading-none", children: "You have a new message!" }), _jsx("p", { className: "text-sm text-muted-foreground", children: "1 hour ago" })] })] }, 1), _jsxs("div", { className: "mb-4 grid grid-cols-[25px_1fr] items-start pb-4 last:mb-0 last:pb-0", children: [_jsx("span", { className: "flex h-2 w-2 translate-y-1 rounded-full bg-sky-500" }), _jsxs("div", { className: "space-y-1", children: [_jsx("p", { className: "text-sm font-medium leading-none", children: "Your subscription is expiring soon!" }), _jsx("p", { className: "text-sm text-muted-foreground", children: "2 hours ago" })] })] }, 1)] }), _jsx(CardFooter, { children: _jsxs(Button, { className: "w-full", children: [_jsx(CheckIcon, { className: "mr-2 h-4 w-4" }), " Mark all as read"] }) })] }));
    },
    args: {
        mode: "single",
        className: "rounded-md border",
    },
};
