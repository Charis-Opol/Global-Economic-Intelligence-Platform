import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, RefreshCw, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from "@/lib/api-client";
import { cn } from "@/lib/utils";

function dagStateBadge(state: string | null) {
  if (!state) return <Badge variant="outline">Never run</Badge>;
  const tone =
    state === "success" ? "success" : state === "failed" ? "destructive" : state === "running" ? "warning" : "outline";
  return <Badge variant={tone as "success" | "destructive" | "warning" | "outline"}>{state}</Badge>;
}

export function MonitoringPage() {
  const health = useQuery({ queryKey: ["monitoring", "services"], queryFn: api.serviceHealth, refetchInterval: 30_000 });
  const pipelines = useQuery({
    queryKey: ["monitoring", "pipelines"],
    queryFn: api.pipelineStatus,
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>Service health</CardTitle>
            <CardDescription>MinIO, MLflow, Airflow, and this API - checked every 30s.</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={() => health.refetch()} disabled={health.isFetching}>
            <RefreshCw className={cn("h-4 w-4", health.isFetching && "animate-spin")} />
            Refresh
          </Button>
        </CardHeader>
        <CardContent>
          {health.isLoading ? (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-16" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {health.data?.map((entry) => (
                <div key={entry.service} className="flex items-center gap-2 rounded-lg border p-3">
                  {entry.healthy ? (
                    <CheckCircle2 className="h-5 w-5 shrink-0 text-success" />
                  ) : (
                    <XCircle className="h-5 w-5 shrink-0 text-destructive" />
                  )}
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium capitalize">{entry.service}</p>
                    {!entry.healthy && entry.detail && (
                      <p className="truncate text-xs text-muted-foreground" title={entry.detail}>
                        {entry.detail}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Nightly training pipelines</CardTitle>
          <CardDescription>Latest Airflow run per forecast model (Day 2, Step 5).</CardDescription>
        </CardHeader>
        <CardContent>
          {pipelines.isLoading ? (
            <Skeleton className="h-32 w-full" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>DAG</TableHead>
                  <TableHead>State</TableHead>
                  <TableHead>Execution date</TableHead>
                  <TableHead>Start</TableHead>
                  <TableHead>End</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pipelines.data?.map((entry) => (
                  <TableRow key={entry.dag_id}>
                    <TableCell className="font-medium">{entry.dag_id}</TableCell>
                    <TableCell>{dagStateBadge(entry.state)}</TableCell>
                    <TableCell>{entry.execution_date ?? "—"}</TableCell>
                    <TableCell>{entry.start_date ?? "—"}</TableCell>
                    <TableCell>{entry.end_date ?? "—"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
