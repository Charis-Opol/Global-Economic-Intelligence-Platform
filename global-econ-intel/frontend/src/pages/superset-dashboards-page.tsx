import { SupersetEmbed } from "@/components/superset/superset-embed";
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
