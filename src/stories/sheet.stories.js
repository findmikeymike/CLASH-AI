import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger, } from "../components/ui/sheet";
const meta = {
    title: "ui/Sheet",
    component: Sheet,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Default = {
    render: (args) => {
        return (_jsxs(Sheet, { children: [_jsx(SheetTrigger, { children: "Open Right" }), _jsx(SheetContent, { side: args.side, children: _jsxs(SheetHeader, { children: [_jsx(SheetTitle, { children: "Are you sure absolutely sure?" }), _jsx(SheetDescription, { children: "This action cannot be undone. This will permanently delete your account and remove your data from our servers." })] }) })] }));
    },
    args: {
        side: "right",
    },
};
export const Left = {
    render: (args) => {
        return (_jsxs(Sheet, { children: [_jsx(SheetTrigger, { children: "Open Left" }), _jsx(SheetContent, { side: args.side, children: _jsxs(SheetHeader, { children: [_jsx(SheetTitle, { children: "Are you sure absolutely sure?" }), _jsx(SheetDescription, { children: "This action cannot be undone. This will permanently delete your account and remove your data from our servers." })] }) })] }));
    },
    args: {
        side: "left",
    },
};
export const Top = {
    render: (args) => {
        return (_jsxs(Sheet, { children: [_jsx(SheetTrigger, { children: "Open Top" }), _jsx(SheetContent, { side: args.side, children: _jsxs(SheetHeader, { children: [_jsx(SheetTitle, { children: "Are you sure absolutely sure?" }), _jsx(SheetDescription, { children: "This action cannot be undone. This will permanently delete your account and remove your data from our servers." })] }) })] }));
    },
    args: {
        side: "top",
    },
};
export const Bottom = {
    render: (args) => {
        return (_jsxs(Sheet, { children: [_jsx(SheetTrigger, { children: "Open Bottom" }), _jsx(SheetContent, { side: args.side, children: _jsxs(SheetHeader, { children: [_jsx(SheetTitle, { children: "Are you sure absolutely sure?" }), _jsx(SheetDescription, { children: "This action cannot be undone. This will permanently delete your account and remove your data from our servers." })] }) })] }));
    },
    args: {
        side: "bottom",
    },
};
