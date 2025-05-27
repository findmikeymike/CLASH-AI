import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { CalendarIcon, EnvelopeClosedIcon, FaceIcon, GearIcon, PersonIcon, RocketIcon, } from "@radix-ui/react-icons";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator, CommandShortcut, } from "../components/ui/command";
const meta = {
    title: "ui/Command",
    component: Command,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: () => {
        return (_jsxs(Command, { className: "rounded-lg border shadow-md", children: [_jsx(CommandInput, { placeholder: "Type a command or search..." }), _jsxs(CommandList, { children: [_jsx(CommandEmpty, { children: "No results found." }), _jsxs(CommandGroup, { heading: "Suggestions", children: [_jsxs(CommandItem, { children: [_jsx(CalendarIcon, { className: "mr-2 h-4 w-4" }), _jsx("span", { children: "Calendar" })] }), _jsxs(CommandItem, { children: [_jsx(FaceIcon, { className: "mr-2 h-4 w-4" }), _jsx("span", { children: "Search Emoji" })] }), _jsxs(CommandItem, { children: [_jsx(RocketIcon, { className: "mr-2 h-4 w-4" }), _jsx("span", { children: "Launch" })] })] }), _jsx(CommandSeparator, {}), _jsxs(CommandGroup, { heading: "Settings", children: [_jsxs(CommandItem, { children: [_jsx(PersonIcon, { className: "mr-2 h-4 w-4" }), _jsx("span", { children: "Profile" }), _jsx(CommandShortcut, { children: "\u2318P" })] }), _jsxs(CommandItem, { children: [_jsx(EnvelopeClosedIcon, { className: "mr-2 h-4 w-4" }), _jsx("span", { children: "Mail" }), _jsx(CommandShortcut, { children: "\u2318B" })] }), _jsxs(CommandItem, { children: [_jsx(GearIcon, { className: "mr-2 h-4 w-4" }), _jsx("span", { children: "Settings" }), _jsx(CommandShortcut, { children: "\u2318S" })] })] })] })] }));
    },
    args: {},
};
