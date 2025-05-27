import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { Loader2, Mail } from "lucide-react";
import { Button } from "../components/ui/button";
const meta = {
    title: "ui/Button",
    component: Button,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: (args) => _jsx(Button, { ...args, children: "Button" }),
    args: {},
};
export const Outline = {
    render: (args) => _jsx(Button, { ...args, children: "Button" }),
    args: {
        variant: "outline",
    },
};
export const Ghost = {
    render: (args) => _jsx(Button, { ...args, children: "Button" }),
    args: {
        variant: "ghost",
    },
};
export const Secondary = {
    render: (args) => _jsx(Button, { ...args, children: "Button" }),
    args: {
        variant: "secondary",
    },
};
export const Link = {
    render: (args) => _jsx(Button, { ...args, children: "Button" }),
    args: {
        variant: "link",
    },
};
export const Loading = {
    render: (args) => (_jsxs(Button, { ...args, children: [_jsx(Loader2, { className: "mr-2 h-4 w-4 animate-spin" }), "Button"] })),
    args: {
        variant: "outline",
    },
};
export const WithIcon = {
    render: (args) => (_jsxs(Button, { ...args, children: [_jsx(Mail, { className: "mr-2 h-4 w-4" }), " Login with Email Button"] })),
    args: {
        variant: "secondary",
    },
};
