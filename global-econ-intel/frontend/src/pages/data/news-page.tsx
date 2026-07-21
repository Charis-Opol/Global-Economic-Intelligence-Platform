import { DataExplorer, type ColumnDef } from "@/components/data/data-explorer";
import { api } from "@/lib/api-client";
import type { NewsArticle } from "@/types/api";

const columns: ColumnDef<NewsArticle>[] = [
  { key: "date", header: "Date" },
  { key: "source_name", header: "Source" },
  {
    key: "title",
    header: "Title",
    render: (row) => (
      <a href={row.url} target="_blank" rel="noreferrer" className="text-primary hover:underline">
        {row.title ?? row.url}
      </a>
    ),
  },
  { key: "author", header: "Author" },
];

export function NewsPage() {
  return (
    <DataExplorer
      title="News"
      description="Same-day article volume feature included, one row per article."
      queryKey="news"
      columns={columns}
      filters={[
        { name: "source", label: "Source", placeholder: "Reuters" },
        { name: "q", label: "Title contains" },
        { name: "date_from", label: "From date", type: "date" },
        { name: "date_to", label: "To date", type: "date" },
      ]}
      fetchPage={api.news}
      rowKey={(row) => row.url}
    />
  );
}
