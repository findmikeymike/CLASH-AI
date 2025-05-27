import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { Skeleton } from "../components/ui/skeleton";
const meta = {
    title: "ui/Skeleton",
    component: Skeleton,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Default = {
    render: () => {
        return (_jsxs("div", { className: "flex items-center space-x-4", children: [_jsx(Skeleton, { className: "h-12 w-12 rounded-full" }), _jsxs("div", { className: "space-y-2", children: [_jsx(Skeleton, { className: "h-4 w-[250px]" }), _jsx(Skeleton, { className: "h-4 w-[200px]" })] })] }));
    },
    args: {},
};
