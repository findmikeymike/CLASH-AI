import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { FontItalicIcon, FontBoldIcon } from "@radix-ui/react-icons";
import { Toggle } from "../components/ui/toggle";
const meta = {
    title: "ui/Toggle",
    component: Toggle,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Default = {
    render: () => (_jsx(Toggle, { "aria-label": "Toggle bold", children: _jsx(FontBoldIcon, { className: "h-4 w-4" }) })),
    args: {},
};
export const Outline = {
    render: () => (_jsx(Toggle, { "aria-label": "Toggle italic", variant: "outline", children: _jsx(FontItalicIcon, { className: "h-4 w-4" }) })),
    args: {},
};
export const WithText = {
    render: () => (_jsxs(Toggle, { "aria-label": "Toggle italic", children: [_jsx(FontItalicIcon, { className: "h-4 w-4" }), "Italic"] })),
    args: {},
};
export const Small = {
    render: () => (_jsx(Toggle, { size: "sm", "aria-label": "Toggle bold", children: _jsx(FontBoldIcon, { className: "h-4 w-4" }) })),
    args: {},
};
export const Large = {
    render: () => (_jsx(Toggle, { size: "lg", "aria-label": "Toggle bold", children: _jsx(FontBoldIcon, { className: "h-4 w-4" }) })),
    args: {},
};
export const Destructive = {
    render: () => (_jsx(Toggle, { "aria-label": "Toggle bold", disabled: true, children: _jsx(FontBoldIcon, { className: "h-4 w-4" }) })),
    args: {
        variant: "destructive",
    },
};
