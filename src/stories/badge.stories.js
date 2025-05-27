import { jsx as _jsx } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { Badge } from "../components/ui/badge";
const meta = {
    title: "ui/Badge",
    component: Badge,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: (args) => _jsx(Badge, { ...args, children: "Badge" }),
    args: {},
};
export const Secondary = {
    render: (args) => _jsx(Badge, { ...args, children: "Secondary" }),
    args: {
        variant: "secondary",
    },
};
export const Outline = {
    render: (args) => _jsx(Badge, { ...args, children: "Outline" }),
    args: {
        variant: "outline",
    },
};
export const Destructive = {
    render: (args) => _jsx(Badge, { ...args, children: "Destructive" }),
    args: {
        variant: "destructive",
    },
};
