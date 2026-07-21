import { DataExplorer, type ColumnDef } from "@/components/data/data-explorer";
import { api } from "@/lib/api-client";
import type { Weather } from "@/types/api";

const columns: ColumnDef<Weather>[] = [
  { key: "date", header: "Date" },
  { key: "latitude", header: "Lat" },
  { key: "longitude", header: "Lon" },
  { key: "temp_max_c", header: "Max °C" },
  { key: "temp_min_c", header: "Min °C" },
  { key: "precipitation_mm", header: "Precip (mm)" },
  { key: "rainfall_anomaly_mm", header: "Anomaly (mm)" },
];

export function WeatherPage() {
  return (
    <DataExplorer
      title="Weather"
      description="Daily temperature and precipitation, with a rainfall anomaly feature."
      queryKey="weather"
      columns={columns}
      filters={[
        { name: "latitude", label: "Latitude", type: "number" },
        { name: "longitude", label: "Longitude", type: "number" },
        { name: "date_from", label: "From date", type: "date" },
        { name: "date_to", label: "To date", type: "date" },
      ]}
      fetchPage={api.weather}
      rowKey={(row) => `${row.latitude}-${row.longitude}-${row.date}`}
    />
  );
}
