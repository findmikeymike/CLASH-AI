import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow, } from "../components/ui/table";
const meta = {
    title: "ui/Table",
    component: Table,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Default = {
    render: () => {
        return (_jsxs(Table, { children: [_jsx(TableCaption, { children: "A list of your recent invoices." }), _jsx(TableHeader, { children: _jsxs(TableRow, { children: [_jsx(TableHead, { className: "w-[100px]", children: "Invoice" }), _jsx(TableHead, { children: "Status" }), _jsx(TableHead, { children: "Method" }), _jsx(TableHead, { className: "text-right", children: "Amount" })] }) }), _jsxs(TableBody, { children: [_jsxs(TableRow, { children: [_jsx(TableCell, { className: "font-medium", children: "INV001" }), _jsx(TableCell, { children: "Paid" }), _jsx(TableCell, { children: "Credit Card" }), _jsx(TableCell, { className: "text-right", children: "$250.00" })] }, "INV001"), _jsxs(TableRow, { children: [_jsx(TableCell, { className: "font-medium", children: "INV002" }), _jsx(TableCell, { children: "Pending" }), _jsx(TableCell, { children: "PayPal" }), _jsx(TableCell, { className: "text-right", children: "$150.00" })] }, "INV002"), _jsxs(TableRow, { children: [_jsx(TableCell, { className: "font-medium", children: "INV003" }), _jsx(TableCell, { children: "Unpaid" }), _jsx(TableCell, { children: "Bank Transfer" }), _jsx(TableCell, { className: "text-right", children: "$450.00" })] }, "INV003"), _jsxs(TableRow, { children: [_jsx(TableCell, { className: "font-medium", children: "INV004" }), _jsx(TableCell, { children: "Pending" }), _jsx(TableCell, { children: "Stripe" }), _jsx(TableCell, { className: "text-right", children: "$250.00" })] }, "INV004"), _jsxs(TableRow, { children: [_jsx(TableCell, { className: "font-medium", children: "INV005" }), _jsx(TableCell, { children: "Paid" }), _jsx(TableCell, { children: "Credit Card" }), _jsx(TableCell, { className: "text-right", children: "$50.00" })] }, "INV005")] })] }));
    },
    args: {},
};
