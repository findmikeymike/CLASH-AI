import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { ResizableHandle, ResizablePanel, ResizablePanelGroup, } from "../components/ui/resizable";
const meta = {
    title: "ui/ResizablePanelGroup",
    component: ResizablePanelGroup,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: (args) => (_jsxs(ResizablePanelGroup, { ...args, direction: "horizontal", className: "max-w-md rounded-lg border", children: [_jsx(ResizablePanel, { defaultSize: 50, children: _jsx("div", { className: "flex h-[200px] items-center justify-center p-6", children: _jsx("span", { className: "font-semibold", children: "One" }) }) }), _jsx(ResizableHandle, {}), _jsx(ResizablePanel, { defaultSize: 50, children: _jsxs(ResizablePanelGroup, { direction: "vertical", children: [_jsx(ResizablePanel, { defaultSize: 25, children: _jsx("div", { className: "flex h-full items-center justify-center p-6", children: _jsx("span", { className: "font-semibold", children: "Two" }) }) }), _jsx(ResizableHandle, {}), _jsx(ResizablePanel, { defaultSize: 75, children: _jsx("div", { className: "flex h-full items-center justify-center p-6", children: _jsx("span", { className: "font-semibold", children: "Three" }) }) })] }) })] })),
    args: {},
};
