import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Pagination, PaginationContent, PaginationEllipsis, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious, } from "../components/ui/pagination";
const meta = {
    title: "ui/Pagination",
    component: Pagination,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: (args) => (_jsx(Pagination, { ...args, children: _jsxs(PaginationContent, { children: [_jsx(PaginationItem, { children: _jsx(PaginationPrevious, { href: "#" }) }), _jsx(PaginationItem, { children: _jsx(PaginationLink, { href: "#", children: "1" }) }), _jsx(PaginationItem, { children: _jsx(PaginationLink, { href: "#", children: "2" }) }), _jsx(PaginationItem, { children: _jsx(PaginationLink, { href: "#", children: "3" }) }), _jsx(PaginationItem, { children: _jsx(PaginationEllipsis, {}) }), _jsx(PaginationItem, { children: _jsx(PaginationNext, { href: "#" }) })] }) })),
    args: {},
};
