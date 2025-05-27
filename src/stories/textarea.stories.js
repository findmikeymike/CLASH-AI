import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { Button } from "../components/ui/button";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
const meta = {
    title: "ui/Textarea",
    component: Textarea,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Default = {
    render: (args) => _jsx(Textarea, { ...args }),
    args: {
        placeholder: "Type your message here.",
    },
};
export const Disabled = {
    render: (args) => _jsx(Textarea, { ...args }),
    args: {
        ...Default.args,
        disabled: true,
    },
};
export const WithLabel = {
    render: (args) => (_jsxs("div", { className: "grid w-full gap-1.5", children: [_jsx(Label, { htmlFor: "message", children: "Your message" }), _jsx(Textarea, { ...args, id: "message" })] })),
    args: { ...Default.args },
};
export const WithText = {
    render: (args) => (_jsxs("div", { className: "grid w-full gap-1.5", children: [_jsx(Label, { htmlFor: "message-2", children: "Your Message" }), _jsx(Textarea, { ...args, id: "message-2" }), _jsx("p", { className: "text-sm text-slate-500", children: "Your message will be copied to the support team." })] })),
    args: { ...Default.args },
};
export const WithButton = {
    render: (args) => (_jsxs("div", { className: "grid w-full gap-2", children: [_jsx(Textarea, { ...args }), _jsx(Button, { children: "Send message" })] })),
    args: { ...Default.args },
};
