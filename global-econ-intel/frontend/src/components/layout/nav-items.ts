import {
  Activity,
  Bitcoin,
  CloudSun,
  LayoutDashboard,
  LayoutGrid,
  Newspaper,
  Percent,
  Repeat,
  Settings,
  Sparkles,
  TrendingUp,
} from "lucide-react";

export const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/data/gdp", label: "GDP", icon: TrendingUp, end: false },
  { to: "/data/inflation", label: "Inflation", icon: Percent, end: false },
  { to: "/data/exchange", label: "Exchange Rates", icon: Repeat, end: false },
  { to: "/data/weather", label: "Weather", icon: CloudSun, end: false },
  { to: "/data/crypto", label: "Crypto", icon: Bitcoin, end: false },
  { to: "/data/news", label: "News", icon: Newspaper, end: false },
  { to: "/predictions", label: "Predictions", icon: Sparkles, end: false },
  { to: "/dashboards", label: "Dashboards", icon: LayoutGrid, end: false },
  { to: "/monitoring", label: "Monitoring", icon: Activity, end: false },
  { to: "/settings", label: "Settings", icon: Settings, end: false },
] as const;
