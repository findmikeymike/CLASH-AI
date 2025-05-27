import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { Checkbox } from "../components/ui/checkbox";
const meta = {
    title: "ui/Checkbox",
    component: Checkbox,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: (args) => (_jsxs("div", { className: "items-top flex space-x-2", children: [_jsx(Checkbox, { ...args, id: "terms1" }), _jsxs("div", { className: "grid gap-1.5 leading-none", children: [_jsx("label", { htmlFor: "terms1", className: "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70", children: "Accept terms and conditions" }), _jsx("p", { className: "text-sm text-slate-500 dark:text-slate-400", children: "You agree to our Terms of Service and Privacy Policy." })] })] })),
    args: {},
};
export const Disabled = {
    render: (args) => (_jsxs("div", { className: "flex items-center space-x-2", children: [_jsx(Checkbox, { ...args, id: "terms2" }), _jsx("label", { htmlFor: "terms2", className: "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70", children: "Accept terms and conditions" })] })),
    args: {
        disabled: true,
    },
};
