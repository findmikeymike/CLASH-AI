import { jsx as _jsx } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { Label } from "../components/ui/label";
const meta = {
    title: "ui/Label",
    component: Label,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: () => _jsx(Label, { htmlFor: "email", children: "Your email address" }),
    args: {},
};
