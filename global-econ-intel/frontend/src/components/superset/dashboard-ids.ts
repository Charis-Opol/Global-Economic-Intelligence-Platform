/**
 * Mirrors backend/app/superset_client.py's DASHBOARD_UUIDS exactly. Kept in
 * sync by hand, same as src/types/api.ts mirrors the Pydantic schemas - the
 * backend has no dependency on the frontend, and vice versa.
 */
export const DASHBOARD_IDS: Record<string, string> = {
  gdp: "fdbf5d8b-5077-4ba7-8421-3f0be46f14d8",
  inflation: "8259bc55-e18d-4198-b68e-27c89029b54e",
  weather: "b7cbc5fc-a0cf-4a5f-88f9-749a4ac9478c",
  crypto: "778e0eb8-3168-4b4b-99fd-59899b3e7c58",
  exchange: "7950e4cc-2853-4334-ab19-aa5e50005f6b",
  forecasts: "2366b86b-7c92-441a-b33f-596ae1d7b56e",
};
