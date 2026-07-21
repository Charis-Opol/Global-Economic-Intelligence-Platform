import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Loader2 } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { ProtectedRoute } from "@/components/protected-route";
import { LoginPage } from "@/pages/login-page";

// Lazy-loaded: keeps the initial bundle small and, more importantly, keeps
// heavy per-page dependencies (recharts on Predictions, the Superset
// embedded-sdk on Dashboards) out of every other route's chunk entirely.
const DashboardPage = lazy(() => import("@/pages/dashboard-page").then((m) => ({ default: m.DashboardPage })));
const GdpPage = lazy(() => import("@/pages/data/gdp-page").then((m) => ({ default: m.GdpPage })));
const InflationPage = lazy(() => import("@/pages/data/inflation-page").then((m) => ({ default: m.InflationPage })));
const ExchangePage = lazy(() => import("@/pages/data/exchange-page").then((m) => ({ default: m.ExchangePage })));
const WeatherPage = lazy(() => import("@/pages/data/weather-page").then((m) => ({ default: m.WeatherPage })));
const CryptoPage = lazy(() => import("@/pages/data/crypto-page").then((m) => ({ default: m.CryptoPage })));
const NewsPage = lazy(() => import("@/pages/data/news-page").then((m) => ({ default: m.NewsPage })));
const PredictionsPage = lazy(() =>
  import("@/pages/predictions-page").then((m) => ({ default: m.PredictionsPage })),
);
const SupersetDashboardsPage = lazy(() =>
  import("@/pages/superset-dashboards-page").then((m) => ({ default: m.SupersetDashboardsPage })),
);
const MonitoringPage = lazy(() => import("@/pages/monitoring-page").then((m) => ({ default: m.MonitoringPage })));
const SettingsPage = lazy(() => import("@/pages/settings-page").then((m) => ({ default: m.SettingsPage })));
const NotFoundPage = lazy(() => import("@/pages/not-found-page").then((m) => ({ default: m.NotFoundPage })));

function RouteFallback() {
  return (
    <div className="flex h-64 items-center justify-center">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route index element={<DashboardPage />} />
            <Route path="data/gdp" element={<GdpPage />} />
            <Route path="data/inflation" element={<InflationPage />} />
            <Route path="data/exchange" element={<ExchangePage />} />
            <Route path="data/weather" element={<WeatherPage />} />
            <Route path="data/crypto" element={<CryptoPage />} />
            <Route path="data/news" element={<NewsPage />} />
            <Route path="predictions" element={<PredictionsPage />} />
            <Route path="dashboards" element={<SupersetDashboardsPage />} />
            <Route path="monitoring" element={<MonitoringPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Route>

        <Route path="/404" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Routes>
    </Suspense>
  );
}
