import { useMemo, useState } from "react";
import type { ReactNode } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { FilterBar, type FilterField } from "@/components/data/filter-bar";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ApiError } from "@/lib/api-client";
import type { Page } from "@/types/api";

export interface ColumnDef<T> {
  key: string;
  header: string;
  render?: (row: T) => ReactNode;
  className?: string;
}

interface DataExplorerProps<T> {
  title: string;
  description?: string;
  queryKey: string;
  columns: ColumnDef<T>[];
  filters?: FilterField[];
  fetchPage: (params: Record<string, string | number>) => Promise<Page<T>>;
  rowKey: (row: T) => string;
  pageSize?: number;
}

export function DataExplorer<T>({
  title,
  description,
  queryKey,
  columns,
  filters = [],
  fetchPage,
  rowKey,
  pageSize = 20,
}: DataExplorerProps<T>) {
  const [filterValues, setFilterValues] = useState<Record<string, string>>({});
  const [offset, setOffset] = useState(0);

  const params = useMemo(() => {
    const cleaned: Record<string, string | number> = { limit: pageSize, offset };
    for (const [key, value] of Object.entries(filterValues)) {
      if (value) cleaned[key] = value;
    }
    return cleaned;
  }, [filterValues, offset, pageSize]);

  const { data, isLoading, isError, error, isFetching } = useQuery({
    queryKey: [queryKey, params],
    queryFn: () => fetchPage(params),
    placeholderData: keepPreviousData,
  });

  function handleFilterChange(name: string, value: string) {
    setOffset(0);
    setFilterValues((prev) => ({ ...prev, [name]: value }));
  }

  const total = data?.total ?? 0;
  const showingFrom = total === 0 ? 0 : offset + 1;
  const showingTo = Math.min(offset + pageSize, total);

  return (
    <Card>
      <CardHeader className="gap-4">
        <div>
          <CardTitle>{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </div>
        <FilterBar fields={filters} values={filterValues} onChange={handleFilterChange} />
      </CardHeader>
      <CardContent className="space-y-4">
        {isError && (
          <Alert variant="destructive">
            <AlertDescription>
              {error instanceof ApiError ? error.message : "Failed to load data."}
            </AlertDescription>
          </Alert>
        )}

        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map((col) => (
                  <TableHead key={col.key} className={col.className}>
                    {col.header}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.items.length ? (
                data.items.map((row) => (
                  <TableRow key={rowKey(row)}>
                    {columns.map((col) => (
                      <TableCell key={col.key} className={col.className}>
                        {col.render ? col.render(row) : formatValue((row as Record<string, unknown>)[col.key])}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={columns.length} className="py-8 text-center text-muted-foreground">
                    No results.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}

        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {total > 0 ? `Showing ${showingFrom}-${showingTo} of ${total}` : "No results"}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setOffset((o) => Math.max(0, o - pageSize))}
              disabled={offset === 0 || isFetching}
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setOffset((o) => o + pageSize)}
              disabled={offset + pageSize >= total || isFetching}
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function formatValue(value: unknown): ReactNode {
  if (value === null || value === undefined) return <span className="text-muted-foreground">—</span>;
  if (typeof value === "number") return value.toLocaleString();
  return String(value);
}
