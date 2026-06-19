"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import { ClinicTable } from "@/components/clinic-table";
import { FilterBar } from "@/components/filter-bar";
import { Button } from "@/components/ui/button";
import { ApiRequestError, buildClinicListQuery, fetchClinics } from "@/lib/api";
import type { ClinicListResponse } from "@/lib/types";

export function ClinicsPageClient() {
  const searchParams = useSearchParams();
  const searchParamsKey = searchParams.toString();
  const query = buildClinicListQuery(searchParams);
  const [data, setData] = useState<ClinicListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const query = buildClinicListQuery(searchParams);
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetchClinics(query);
        if (!cancelled) setData(response);
      } catch (err) {
        if (!cancelled) {
          setData(null);
          setError(err instanceof ApiRequestError ? err.message : "Failed to load clinics");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [searchParamsKey, searchParams]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  const currentPage = data?.page ?? query.page ?? 1;

  function goToPage(page: number) {
    const params = new URLSearchParams(searchParams.toString());
    if (page <= 1) params.delete("page");
    else params.set("page", String(page));
    window.location.href = `/clinics?${params.toString()}`;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Clinic radar</h1>
        <p className="mt-2 text-muted-foreground">
          Ranked dental clinics by purchase propensity — search, filter, and drill into signals.
        </p>
      </div>

      <FilterBar />

      {loading ? (
        <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground">
          Loading clinics…
        </div>
      ) : null}

      {!loading && error ? (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-8 text-center">
          <p className="font-medium text-destructive">{error}</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Check that the API is running and `NEXT_PUBLIC_API_URL` is configured.
          </p>
        </div>
      ) : null}

      {!loading && !error && data ? (
        <>
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Showing {data.data.length} of {data.total} clinics
            </span>
            <span>Sorted by score (high to low)</span>
          </div>
          <ClinicTable clinics={data.data} />
          <div className="flex items-center justify-between">
            <Button
              variant="outline"
              disabled={currentPage <= 1}
              onClick={() => goToPage(currentPage - 1)}
            >
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="outline"
              disabled={currentPage >= totalPages}
              onClick={() => goToPage(currentPage + 1)}
            >
              Next
            </Button>
          </div>
        </>
      ) : null}
    </div>
  );
}
