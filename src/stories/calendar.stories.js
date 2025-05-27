import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { Calendar } from "../components/ui/calendar";
import { CalendarIcon } from "@radix-ui/react-icons";
import { Popover, PopoverContent, PopoverTrigger, } from "../components/ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue, } from "../components/ui/select";
import { Button } from "../components/ui/button";
import { useState } from "react";
import { addDays, format } from "date-fns";
const meta = {
    title: "ui/Calendar",
    component: Calendar,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: (args) => _jsx(Calendar, { ...args, children: "Calendar" }),
    args: {
        mode: "single",
        className: "rounded-md border",
    },
};
export const DatePicker = {
    render: () => {
        return (_jsxs(Popover, { children: [_jsx(PopoverTrigger, { asChild: true, children: _jsxs(Button, { variant: "outline", className: "w-[240px] justify-start text-left font-normal", children: [_jsx(CalendarIcon, { className: "mr-2 h-4 w-4" }), _jsx("span", { children: "Pick a date" })] }) }), _jsx(PopoverContent, { className: "w-auto p-0", align: "start", children: _jsx(Calendar, { mode: "single", initialFocus: true }) })] }));
    },
    args: {
        date: Date.parse("2023-11-3000"),
    },
};
export const DatePickerRange = {
    render: () => {
        const [date, setDate] = useState({
            from: new Date(2023, 0, 20),
            to: addDays(new Date(2023, 0, 20), 20),
        });
        return (_jsx("div", { className: "grid gap-2", children: _jsxs(Popover, { children: [_jsx(PopoverTrigger, { asChild: true, children: _jsxs(Button, { id: "date", variant: "outline", className: "w-[300px] justify-start text-left font-normal", children: [_jsx(CalendarIcon, { className: "mr-2 h-4 w-4" }), date?.from ? (date.to ? (_jsxs(_Fragment, { children: [format(date.from, "LLL dd, y"), " -", " ", format(date.to, "LLL dd, y")] })) : (format(date.from, "LLL dd, y"))) : (_jsx("span", { children: "Pick a date" }))] }) }), _jsx(PopoverContent, { className: "w-auto p-0", align: "start", children: _jsx(Calendar, { initialFocus: true, mode: "range", defaultMonth: date?.from, selected: date, onSelect: setDate, numberOfMonths: 2 }) })] }) }));
    },
    args: {},
};
export const DatePickerWithPresets = {
    render: () => {
        const [date, setDate] = useState(new Date(2023, 0, 20));
        return (_jsxs(Popover, { children: [_jsx(PopoverTrigger, { asChild: true, children: _jsxs(Button, { variant: "outline", className: "w-[240px] justify-start text-left font-normal", children: [_jsx(CalendarIcon, { className: "mr-2 h-4 w-4" }), date ? format(date, "LLL dd, y") : _jsx("span", { children: "Pick a date" })] }) }), _jsxs(PopoverContent, { align: "start", className: "flex w-auto flex-col space-y-2 p-2", children: [_jsxs(Select, { onValueChange: (value) => {
                                const newDate = new Date();
                                newDate.setDate(newDate.getDate() + parseInt(value));
                                setDate(newDate);
                            }, children: [_jsx(SelectTrigger, { children: _jsx(SelectValue, { placeholder: "Select" }) }), _jsxs(SelectContent, { position: "popper", children: [_jsx(SelectItem, { value: "0", children: "Today" }), _jsx(SelectItem, { value: "1", children: "Tomorrow" }), _jsx(SelectItem, { value: "3", children: "In 3 days" }), _jsx(SelectItem, { value: "7", children: "In a week" })] })] }), _jsx("div", { className: "rounded-md border", children: _jsx(Calendar, { initialFocus: true, mode: "single", defaultMonth: date, selected: date, onSelect: setDate }) })] })] }));
    },
    args: {},
};
