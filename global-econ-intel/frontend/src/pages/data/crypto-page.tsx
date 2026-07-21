import { DataExplorer, type ColumnDef } from "@/components/data/data-explorer";
import { api } from "@/lib/api-client";
import type { Crypto } from "@/types/api";

const columns: ColumnDef<Crypto>[] = [
  { key: "date", header: "Date" },
  { key: "coin_id", header: "Coin" },
  { key: "symbol", header: "Symbol" },
  { key: "price_usd", header: "Price (USD)" },
  { key: "price_change_pct_24h", header: "24h Change %" },
  { key: "volatility_7d", header: "7d Volatility" },
];

export function CryptoPage() {
  return (
    <DataExplorer
      title="Crypto"
      description="Daily CoinGecko prices with 24h change and trailing 7-day volatility."
      queryKey="crypto"
      columns={columns}
      filters={[
        { name: "coin_id", label: "Coin id", placeholder: "bitcoin" },
        { name: "date_from", label: "From date", type: "date" },
        { name: "date_to", label: "To date", type: "date" },
      ]}
      fetchPage={api.crypto}
      rowKey={(row) => `${row.coin_id}-${row.date}`}
    />
  );
}
