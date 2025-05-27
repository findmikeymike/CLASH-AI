import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { Suspense } from "react";
import { useRoutes, Routes, Route } from "react-router-dom";
import Home from "./components/home";
import LandingPage from "./components/LandingPage";
import TestUsageTracking from "./components/TestUsageTracking";
import routes from "tempo-routes";
function App() {
    return (_jsx(Suspense, { fallback: _jsx("p", { children: "Loading..." }), children: _jsxs(_Fragment, { children: [import.meta.env.VITE_TEMPO === "true" && useRoutes(routes), _jsxs(Routes, { children: [_jsx(Route, { path: "/", element: _jsx(LandingPage, {}) }), _jsx(Route, { path: "/debate", element: _jsx(Home, {}) }), _jsx(Route, { path: "/test-usage", element: _jsx(TestUsageTracking, {}) }), import.meta.env.VITE_TEMPO === "true" && (_jsx(Route, { path: "/tempobook/*" }))] })] }) }));
}
export default App;
