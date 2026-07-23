import { useQuery } from "@tanstack/react-query";
import { Bitcoin, Globe2, Repeat, Sparkles } from "lucide-react";

import { StatCard } from "@/components/dashboard/stat-card";
import { api } from "@/lib/api-client";

export function DashboardPage() {
  const countries = useQuery({ queryKey: ["countries", "count"], queryFn: () => api.countries({ limit: 1 }) });
  const exchangeRates = useQuery({
    queryKey: ["exchange", "latest"],
    queryFn: () => api.exchangeRates({ limit: 1 }),
  });
  const crypto = useQuery({ queryKey: ["crypto", "latest"], queryFn: () => api.crypto({ limit: 1 }) });
  const models = useQuery({ queryKey: ["models"], queryFn: api.models });

  const latestRate = exchangeRates.data?.items[0];
  const latestCoin = crypto.data?.items[0];
  const championCount = models.data?.filter((m) => m.champion_version).length ?? 0;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Countries tracked"
          value={String(countries.data?.total ?? "—")}
          icon={Globe2}
          isLoading={countries.isLoading}
        />
        <StatCard
          title={latestRate ? `${latestRate.base_code}/${latestRate.currency}` : "Latest exchange rate"}
          value={latestRate ? latestRate.rate?.toFixed(4) ?? "—" : "—"}
          icon={Repeat}
          isLoading={exchangeRates.isLoading}
          hint={latestRate?.date}
        />
        <StatCard
          title={latestCoin ? `${latestCoin.symbol?.toUpperCase()} price` : "Latest crypto price"}
          value={latestCoin?.price_usd ? `$${latestCoin.price_usd.toLocaleString()}` : "—"}
          icon={Bitcoin}
          isLoading={crypto.isLoading}
          hint={latestCoin?.date}
        />
        <StatCard
          title="Models deployed"
          value={String(championCount)}
          icon={Sparkles}
          isLoading={models.isLoading}
          tone={championCount > 0 ? "success" : "default"}
          hint={`${models.data?.length ?? 0} registered`}
        />
      </div>
    </div>
  );
}
