import type { LucideIcon } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export function StatCard({
  title,
  value,
  icon: Icon,
  isLoading,
  hint,
  tone = "default",
}: {
  title: string;
  value: string;
  icon: LucideIcon;
  isLoading?: boolean;
  hint?: string;
  tone?: "default" | "success" | "destructive" | "warning";
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon
          className={cn(
            "h-4 w-4",
            tone === "success" && "text-success",
            tone === "destructive" && "text-destructive",
            tone === "warning" && "text-warning",
            tone === "default" && "text-muted-foreground",
          )}
        />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-7 w-24" />
        ) : (
          <div className="text-2xl font-bold">{value}</div>
        )}
        {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
      </CardContent>
    </Card>
  );
}
