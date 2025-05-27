import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Button } from "../components/ui/button";
import { Drawer, DrawerClose, DrawerContent, DrawerDescription, DrawerFooter, DrawerHeader, DrawerTitle, DrawerTrigger, } from "../components/ui/drawer";
const meta = {
    title: "ui/Drawer",
    component: Drawer,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: (args) => (_jsxs(Drawer, { ...args, children: [_jsx(DrawerTrigger, { children: "Open" }), _jsxs(DrawerContent, { children: [_jsxs(DrawerHeader, { children: [_jsx(DrawerTitle, { children: "Are you sure absolutely sure?" }), _jsx(DrawerDescription, { children: "This action cannot be undone." })] }), _jsxs(DrawerFooter, { children: [_jsx(Button, { children: "Submit" }), _jsx(DrawerClose, { children: _jsx(Button, { variant: "outline", children: "Cancel" }) })] })] })] })),
    args: {},
};
