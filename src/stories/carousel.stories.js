import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Card, CardContent } from "../components/ui/card";
import { Carousel, CarouselContent, CarouselItem, CarouselNext, CarouselPrevious, } from "../components/ui/carousel";
const meta = {
    title: "ui/Carousel",
    component: Carousel,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: (args) => (_jsxs(Carousel, { ...args, className: "mx-12 w-full max-w-xs", children: [_jsx(CarouselContent, { children: Array.from({ length: 5 }).map((_, index) => (_jsx(CarouselItem, { children: _jsx("div", { className: "p-1", children: _jsx(Card, { children: _jsx(CardContent, { className: "flex aspect-square items-center justify-center p-6", children: _jsx("span", { className: "text-4xl font-semibold", children: index + 1 }) }) }) }) }, index))) }), _jsx(CarouselPrevious, {}), _jsx(CarouselNext, {})] })),
    args: {},
};
export const Size = {
    render: (args) => (_jsxs(Carousel, { ...args, className: "mx-12 w-full max-w-xs", children: [_jsx(CarouselContent, { children: Array.from({ length: 5 }).map((_, index) => (_jsx(CarouselItem, { className: "basis-1/3", children: _jsx("div", { className: "p-1", children: _jsx(Card, { children: _jsx(CardContent, { className: "flex aspect-square items-center justify-center p-6", children: _jsx("span", { className: "text-4xl font-semibold", children: index + 1 }) }) }) }) }, index))) }), _jsx(CarouselPrevious, {}), _jsx(CarouselNext, {})] })),
    args: {},
};
