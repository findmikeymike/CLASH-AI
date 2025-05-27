import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
// [build] library: 'shadcn'
import { RocketIcon } from "@radix-ui/react-icons";
import { ExclamationTriangleIcon } from "@radix-ui/react-icons";
import { Alert, AlertDescription, AlertTitle } from "../components/ui/alert";
const meta = {
    title: "ui/Alert",
    component: Alert,
    tags: ["autodocs"],
    argTypes: {},
};
export default meta;
export const Default = {
    render: () => {
        return (_jsxs(Alert, { children: [_jsx(RocketIcon, { className: "h-4 w-4" }), _jsx(AlertTitle, { children: "Heads up!" }), _jsx(AlertDescription, { children: "You can add components to your app using the cli." })] }));
    },
    args: {},
};
export const Destructive = {
    render: () => {
        return (_jsxs(Alert, { variant: "destructive", children: [_jsx(ExclamationTriangleIcon, { className: "h-4 w-4" }), _jsx(AlertTitle, { children: "Error" }), _jsx(AlertDescription, { children: "Your session has expired. Please log in again." })] }));
    },
    args: {},
};
