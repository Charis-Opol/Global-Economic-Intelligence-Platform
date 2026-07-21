import { useState } from "react";
import type { FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Sparkles } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ApiError, api } from "@/lib/api-client";
import { FORECAST_DOMAINS, type ForecastDomain } from "@/types/api";

const DOMAIN_LABELS: Record<ForecastDomain, string> = {
  gdp: "GDP",
  inflation: "Inflation",
  exchange_rate: "Exchange Rate",
  crypto: "Crypto",
};

export function PredictionsPage() {
  const [domain, setDomain] = useState<ForecastDomain>("gdp");
  const [country, setCountry] = useState("UGA");
  const [base, setBase] = useState("USD");
  const [quote, setQuote] = useState("EUR");
  const [coinId, setCoinId] = useState("bitcoin");

  const mutation = useMutation({
    mutationFn: () =>
      api.predict({
        domain,
        country: domain === "gdp" || domain === "inflation" ? country : undefined,
        base: domain === "exchange_rate" ? base : undefined,
        quote: domain === "exchange_rate" ? quote : undefined,
        coin_id: domain === "crypto" ? coinId : undefined,
      }),
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }

  const chartData = mutation.data
    ? Object.entries(mutation.data.based_on).map(([key, value]) => ({ name: key, value: value ?? 0 }))
    : [];

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Run a forecast</CardTitle>
          <CardDescription>Calls the champion model deployed for the selected domain.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label>Domain</Label>
              <Select value={domain} onValueChange={(value) => setDomain(value as ForecastDomain)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {FORECAST_DOMAINS.map((d) => (
                    <SelectItem key={d} value={d}>
                      {DOMAIN_LABELS[d]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {(domain === "gdp" || domain === "inflation") && (
              <div className="space-y-2">
                <Label htmlFor="country">Country (ISO3)</Label>
                <Input id="country" value={country} onChange={(e) => setCountry(e.target.value)} required />
              </div>
            )}

            {domain === "exchange_rate" && (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label htmlFor="base">Base currency</Label>
                  <Input id="base" value={base} onChange={(e) => setBase(e.target.value)} required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="quote">Quote currency</Label>
                  <Input id="quote" value={quote} onChange={(e) => setQuote(e.target.value)} required />
                </div>
              </div>
            )}

            {domain === "crypto" && (
              <div className="space-y-2">
                <Label htmlFor="coin_id">Coin id</Label>
                <Input id="coin_id" value={coinId} onChange={(e) => setCoinId(e.target.value)} required />
              </div>
            )}

            {mutation.isError && (
              <Alert variant="destructive">
                <AlertDescription>
                  {mutation.error instanceof ApiError ? mutation.error.message : "Prediction failed."}
                </AlertDescription>
              </Alert>
            )}

            <Button type="submit" disabled={mutation.isPending} className="w-full">
              {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              Predict
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Result</CardTitle>
          <CardDescription>Predicted value and the features it was based on.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {mutation.data ? (
            <>
              <div className="flex items-center justify-between rounded-lg border p-4">
                <div>
                  <p className="text-sm text-muted-foreground">Predicted value</p>
                  <p className="text-2xl font-bold">{mutation.data.predicted_value.toLocaleString()}</p>
                </div>
                {mutation.data.model_version && <Badge variant="secondary">v{mutation.data.model_version}</Badge>}
              </div>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-15} textAnchor="end" height={60} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="value" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Run a forecast to see results here.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
