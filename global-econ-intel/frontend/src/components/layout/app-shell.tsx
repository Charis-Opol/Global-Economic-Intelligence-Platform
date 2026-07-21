import { Outlet } from "react-router-dom";

import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";

export function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden bg-muted/30">
      <aside className="hidden w-64 shrink-0 border-r bg-background md:block">
        <Sidebar />
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
