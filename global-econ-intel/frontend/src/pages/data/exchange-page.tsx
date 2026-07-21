import { DataExplorer, type ColumnDef } from "@/components/data/data-explorer";
import { api } from "@/lib/api-client";
import type { ExchangeRate } from "@/types/api";

const columns: ColumnDef<ExchangeRate>[] = [
  { key: "date", header: "Date" },
  { key: "base_code", header: "Base" },
  { key: "currency", header: "Quote" },
  { key: "rate", header: "Rate" },
  { key: "exchange_momentum", header: "Momentum" },
  { key: "rate_7d_avg", header: "7d Avg" },
];

export function ExchangePage() {
  return (
    <DataExplorer
      title="Exchange Rates"
      description="Daily exchange rates with day-over-day momentum and a 7-day rolling average."
      queryKey="exchange"
      columns={columns}
      filters={[
        { name: "base", label: "Base currency", placeholder: "USD" },
        { name: "quote", label: "Quote currency", placeholder: "EUR" },
        { name: "date_from", label: "From date", type: "date" },
        { name: "date_to", label: "To date", type: "date" },
      ]}
      fetchPage={api.exchangeRates}
      rowKey={(row) => `${row.base_code}-${row.currency}-${row.date}`}
    />
  );
}
