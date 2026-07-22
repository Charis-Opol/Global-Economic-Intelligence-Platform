import { useEffect, useRef, useState } from "react";
import { embedDashboard } from "@superset-ui/embedded-sdk";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, api } from "@/lib/api-client";

const SUPERSET_DOMAIN = import.meta.env.VITE_SUPERSET_DOMAIN;

/**
 * Embeds one Superset dashboard via Superset's official Embedded SDK.
 * The SDK's `id` has to be the dashboard's *embedded* uuid (Superset
 * generates this separately from the dashboard's own uuid the first time
 * embedding is enabled), so it's read off the guest-token response rather
 * than a locally hardcoded id. `fetchGuestToken` is called by the SDK
 * itself whenever the iframe's guest token needs refreshing (they're
 * short-lived by design - see superset/superset_config.py's
 * GUEST_TOKEN_JWT_EXP_SECONDS), so it always hits the backend for a fresh
 * one rather than reusing whatever was fetched on mount.
 */
export function SupersetEmbed({ dashboard }: { dashboard: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const container = containerRef.current;
    if (!container) return;

    setIsLoading(true);
    setError(null);

    api
      .supersetGuestToken(dashboard)
      .then(({ dashboard_id }) => {
        if (cancelled) return;
        return embedDashboard({
          id: dashboard_id,
          supersetDomain: SUPERSET_DOMAIN,
          mountPoint: container,
          fetchGuestToken: () => api.supersetGuestToken(dashboard).then((r) => r.token),
          dashboardUiConfig: { hideTitle: true },
        });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load this dashboard.");
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
      if (container) container.innerHTML = "";
    };
  }, [dashboard]);

  return (
    <div className="relative min-h-[600px] w-full">
      {isLoading && <Skeleton className="absolute inset-0" />}
      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <div
        ref={containerRef}
        className="h-[600px] w-full [&>iframe]:h-full [&>iframe]:w-full [&>iframe]:border-0"
      />
    </div>
  );
}
