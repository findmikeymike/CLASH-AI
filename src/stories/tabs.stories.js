import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger, } from "../components/ui/tabs";
const meta = {
    title: "ui/Tabs",
    component: Tabs,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: (args) => (_jsxs(Tabs, { ...args, className: "w-[400px]", children: [_jsxs(TabsList, { children: [_jsx(TabsTrigger, { value: "account", children: "Account" }), _jsx(TabsTrigger, { value: "password", children: "Password" })] }), _jsxs(TabsContent, { value: "account", children: [_jsx("p", { className: "text-sm text-slate-500 dark:text-slate-400", children: "Make changes to your account here. Click save when you're done." }), _jsxs("div", { className: "grid gap-2 py-4", children: [_jsxs("div", { className: "space-y-1", children: [_jsx(Label, { htmlFor: "name", children: "Name" }), _jsx(Input, { id: "name", defaultValue: "Pedro Duarte" })] }), _jsxs("div", { className: "space-y-1", children: [_jsx(Label, { htmlFor: "username", children: "Username" }), _jsx(Input, { id: "username", defaultValue: "@peduarte" })] })] }), _jsx("div", { className: "flex", children: _jsx(Button, { children: "Save changes" }) })] }), _jsxs(TabsContent, { value: "password", children: [_jsx("p", { className: "text-sm text-slate-500 dark:text-slate-400", children: "Change your password here. After saving, you'll be logged out." }), _jsxs("div", { className: "grid gap-2 py-4", children: [_jsxs("div", { className: "space-y-1", children: [_jsx(Label, { htmlFor: "current", children: "Current password" }), _jsx(Input, { id: "current", type: "password" })] }), _jsxs("div", { className: "space-y-1", children: [_jsx(Label, { htmlFor: "new", children: "New password" }), _jsx(Input, { id: "new", type: "password" })] })] }), _jsx("div", { className: "flex", children: _jsx(Button, { children: "Save password" }) })] })] })),
    args: {
        defaultValue: "account",
    },
};
