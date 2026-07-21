import { DataExplorer, type ColumnDef } from "@/components/data/data-explorer";
import { api } from "@/lib/api-client";
import type { GDPRecord } from "@/types/api";

const columns: ColumnDef<GDPRecord>[] = [
  { key: "country_iso3", header: "Country" },
  { key: "country_name", header: "Name" },
  { key: "year", header: "Year" },
  { key: "gdp_usd", header: "GDP (USD)" },
  { key: "gdp_growth_rate", header: "Growth Rate" },
  { key: "gdp_3yr_avg_usd", header: "3yr Avg (USD)" },
];

export function GdpPage() {
  return (
    <DataExplorer
      title="GDP"
      description="World Bank GDP by country and year, with growth rate and rolling-average features."
      queryKey="gdp"
      columns={columns}
      filters={[
        { name: "country", label: "Country (ISO3)", placeholder: "UGA" },
        { name: "year_min", label: "From year", type: "number" },
        { name: "year_max", label: "To year", type: "number" },
      ]}
      fetchPage={api.gdp}
      rowKey={(row) => `${row.country_iso3}-${row.year}`}
    />
  );
}
