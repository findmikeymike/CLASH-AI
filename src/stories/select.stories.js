import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectSeparator, SelectTrigger, SelectValue, } from "../components/ui/select";
const meta = {
    title: "ui/Select",
    component: Select,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: () => (_jsxs(Select, { children: [_jsx(SelectTrigger, { className: "w-[180px]", children: _jsx(SelectValue, { placeholder: "Select a fruit" }) }), _jsxs(SelectContent, { children: [_jsxs(SelectGroup, { children: [_jsx(SelectLabel, { children: "Fruits" }), _jsx(SelectItem, { value: "apple", children: "Apple" }), _jsx(SelectItem, { value: "banana", children: "Banana" }), _jsx(SelectItem, { value: "blueberry", children: "Blueberry" }), _jsx(SelectItem, { value: "grapes", children: "Grapes" }), _jsx(SelectItem, { value: "pineapple", children: "Pineapple" })] }), _jsx(SelectSeparator, {}), _jsxs(SelectGroup, { children: [_jsx(SelectLabel, { children: "Vegetables" }), _jsx(SelectItem, { value: "aubergine", children: "Aubergine" }), _jsx(SelectItem, { value: "broccoli", children: "Broccoli" }), _jsx(SelectItem, { value: "carrot", disabled: true, children: "Carrot" }), _jsx(SelectItem, { value: "courgette", children: "Courgette" }), _jsx(SelectItem, { value: "leek", children: "Leek" })] }), _jsx(SelectSeparator, {}), _jsxs(SelectGroup, { children: [_jsx(SelectLabel, { children: "Meat" }), _jsx(SelectItem, { value: "beef", children: "Beef" }), _jsx(SelectItem, { value: "chicken", children: "Chicken" }), _jsx(SelectItem, { value: "lamb", children: "Lamb" }), _jsx(SelectItem, { value: "pork", children: "Pork" })] })] })] })),
    args: {},
};
