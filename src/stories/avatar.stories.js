import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { Avatar, AvatarFallback, AvatarImage } from "../components/ui/avatar";
const meta = {
    title: "ui/Avatar",
    component: Avatar,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: () => (_jsxs(Avatar, { children: [_jsx(AvatarImage, { src: "https://github.com/shadcn.png" }), _jsx(AvatarFallback, { children: "CN" })] })),
    args: {},
};
