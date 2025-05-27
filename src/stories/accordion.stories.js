import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger, } from "../components/ui/accordion";
const meta = {
    title: "ui/Accordion",
    component: Accordion,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Base = {
    render: (args) => (_jsxs(Accordion, { ...args, children: [_jsxs(AccordionItem, { value: "item-1", children: [_jsx(AccordionTrigger, { children: "Is it accessible?" }), _jsx(AccordionContent, { children: "Yes. It adheres to the WAI-ARIA design pattern." })] }), _jsxs(AccordionItem, { value: "item-2", children: [_jsx(AccordionTrigger, { children: "Is it styled?" }), _jsx(AccordionContent, { children: "Yes. It comes with default styles that matches the other components' aesthetic." })] }), _jsxs(AccordionItem, { value: "item-3", children: [_jsx(AccordionTrigger, { children: "Is it animated?" }), _jsx(AccordionContent, { children: "Yes. It's animated by default, but you can disable it if you prefer." })] })] })),
    args: {
        type: "single",
        collapsible: true,
    },
};
