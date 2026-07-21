import { DataExplorer, type ColumnDef } from "@/components/data/data-explorer";
import { api } from "@/lib/api-client";
import type { Inflation } from "@/types/api";

const columns: ColumnDef<Inflation>[] = [
  { key: "country_iso3", header: "Country" },
  { key: "country_name", header: "Name" },
  { key: "year", header: "Year" },
  { key: "inflation_pct", header: "Inflation %" },
  { key: "inflation_trend", header: "Trend (pp)" },
  { key: "inflation_3yr_avg_pct", header: "3yr Avg %" },
];

export function InflationPage() {
  return (
    <DataExplorer
      title="Inflation"
      description="World Bank consumer-price inflation by country and year."
      queryKey="inflation"
      columns={columns}
      filters={[
        { name: "country", label: "Country (ISO3)", placeholder: "UGA" },
        { name: "year_min", label: "From year", type: "number" },
        { name: "year_max", label: "To year", type: "number" },
      ]}
      fetchPage={api.inflation}
      rowKey={(row) => `${row.country_iso3}-${row.year}`}
    />
  );
}
