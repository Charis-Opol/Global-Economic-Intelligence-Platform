import { Info } from "lucide-react";

import { SupersetEmbed } from "@/components/superset/superset-embed";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const DASHBOARDS = [
  { key: "gdp", label: "GDP" },
  { key: "inflation", label: "Inflation" },
  { key: "weather", label: "Weather" },
  { key: "crypto", label: "Crypto" },
  { key: "exchange", label: "Exchange" },
  { key: "forecasts", label: "Forecasts" },
] as const;

export function SupersetDashboardsPage() {
  return (
    <div className="space-y-4">
      <Alert>
        <Info className="h-4 w-4" />
        <AlertTitle>Import the dashboard definitions first</AlertTitle>
        <AlertDescription>
          These embeds expect Superset to already have the six dashboards from{" "}
          <code>superset/dashboards/</code> imported (see that folder's README) and embedding enabled via{" "}
          <code>superset/superset_config.py</code>. The dashboard YAML was authored without a live Superset
          instance to validate against, so double-check the import succeeds before relying on it.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle>Dashboards</CardTitle>
          <CardDescription>Embedded Superset dashboards, one per domain.</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="gdp">
            <TabsList>
              {DASHBOARDS.map((d) => (
                <TabsTrigger key={d.key} value={d.key}>
                  {d.label}
                </TabsTrigger>
              ))}
            </TabsList>
            {DASHBOARDS.map((d) => (
              <TabsContent key={d.key} value={d.key}>
                <SupersetEmbed dashboard={d.key} />
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
