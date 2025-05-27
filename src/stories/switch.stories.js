import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
const meta = {
    title: "ui/Switch",
    component: Switch,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: () => (_jsxs("div", { className: "flex items-center space-x-2", children: [_jsx(Switch, { id: "airplane-mode" }), _jsx(Label, { htmlFor: "airplane-mode", children: "Airplane Mode" })] })),
    args: {},
};
