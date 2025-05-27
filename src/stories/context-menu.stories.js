import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { ContextMenu, ContextMenuCheckboxItem, ContextMenuContent, ContextMenuItem, ContextMenuLabel, ContextMenuRadioGroup, ContextMenuRadioItem, ContextMenuSeparator, ContextMenuShortcut, ContextMenuSub, ContextMenuSubContent, ContextMenuSubTrigger, ContextMenuTrigger, } from "../components/ui/context-menu";
const meta = {
    title: "ui/ContextMenu",
    component: ContextMenu,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: () => (_jsxs(ContextMenu, { children: [_jsx(ContextMenuTrigger, { className: "flex h-[150px] w-[300px] items-center justify-center rounded-md border border-dashed border-slate-200 text-sm dark:border-slate-700", children: "Right click here" }), _jsxs(ContextMenuContent, { className: "w-64", children: [_jsxs(ContextMenuItem, { inset: true, children: ["Back", _jsx(ContextMenuShortcut, { children: "\u2318[" })] }), _jsxs(ContextMenuItem, { inset: true, disabled: true, children: ["Forward", _jsx(ContextMenuShortcut, { children: "\u2318]" })] }), _jsxs(ContextMenuItem, { inset: true, children: ["Reload", _jsx(ContextMenuShortcut, { children: "\u2318R" })] }), _jsxs(ContextMenuSub, { children: [_jsx(ContextMenuSubTrigger, { inset: true, children: "More Tools" }), _jsxs(ContextMenuSubContent, { className: "w-48", children: [_jsxs(ContextMenuItem, { children: ["Save Page As...", _jsx(ContextMenuShortcut, { children: "\u21E7\u2318S" })] }), _jsx(ContextMenuItem, { children: "Create Shortcut..." }), _jsx(ContextMenuItem, { children: "Name Window..." }), _jsx(ContextMenuSeparator, {}), _jsx(ContextMenuItem, { children: "Developer Tools" })] })] }), _jsx(ContextMenuSeparator, {}), _jsxs(ContextMenuCheckboxItem, { checked: true, children: ["Show Bookmarks Bar", _jsx(ContextMenuShortcut, { children: "\u2318\u21E7B" })] }), _jsx(ContextMenuCheckboxItem, { children: "Show Full URLs" }), _jsx(ContextMenuSeparator, {}), _jsxs(ContextMenuRadioGroup, { value: "pedro", children: [_jsx(ContextMenuLabel, { inset: true, children: "People" }), _jsx(ContextMenuSeparator, {}), _jsx(ContextMenuRadioItem, { value: "pedro", children: "Pedro Duarte" }), _jsx(ContextMenuRadioItem, { value: "colm", children: "Colm Tuite" })] })] })] })),
    args: {},
};
