"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { buildClinicListQuery, clinicListQueryToSearchParams } from "@/lib/api";
import { PRIORITY_OPTIONS, SIGNAL_TYPE_OPTIONS, type ClinicListQuery, type PriorityLevel } from "@/lib/types";

interface FilterBarProps {
  onChange?: (query: ClinicListQuery) => void;
}

type DraftFilters = {
  q: string;
  state: string;
  priority: "" | PriorityLevel;
  min_score: string;
  max_score: string;
  has_website: string;
  signal_type: string;
};

function draftFromQuery(initial: ClinicListQuery): DraftFilters {
  return {
    q: initial.q ?? "",
    state: initial.state ?? "",
    priority: initial.priority ?? "",
    min_score: initial.min_score?.toString() ?? "",
    max_score: initial.max_score?.toString() ?? "",
    has_website: initial.has_website == null ? "" : String(initial.has_website),
    signal_type: initial.signal_type ?? "",
  };
}

export function FilterBar({ onChange }: FilterBarProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const searchParamsKey = searchParams.toString();
  const initial = buildClinicListQuery(searchParams);

  const [draft, setDraft] = useState<DraftFilters>(() => draftFromQuery(initial));

  useEffect(() => {
    setDraft(draftFromQuery(buildClinicListQuery(searchParams)));
  }, [searchParamsKey, searchParams]);

  function applyFilters(nextPage = 1) {
    const query: ClinicListQuery = {
      q: draft.q || undefined,
      state: draft.state || undefined,
      priority: (draft.priority as ClinicListQuery["priority"]) || undefined,
      min_score: draft.min_score ? Number(draft.min_score) : undefined,
      max_score: draft.max_score ? Number(draft.max_score) : undefined,
      has_website:
        draft.has_website === "true"
          ? true
          : draft.has_website === "false"
            ? false
            : undefined,
      signal_type: draft.signal_type || undefined,
      sort: "-score",
      page: nextPage,
      page_size: 20,
    };

    onChange?.(query);
    const params = clinicListQueryToSearchParams(query);
    router.push(`/clinics?${params.toString()}`);
  }

  function clearFilters() {
    setDraft({
      q: "",
      state: "",
      priority: "",
      min_score: "",
      max_score: "",
      has_website: "",
      signal_type: "",
    });
    router.push("/clinics");
  }

  return (
    <form
      className="grid gap-3 rounded-lg border bg-card p-4 md:grid-cols-2 xl:grid-cols-4"
      onSubmit={(event) => {
        event.preventDefault();
        applyFilters(1);
      }}
    >
      <div className="relative md:col-span-2 xl:col-span-2">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          aria-label="Search clinics"
          className="pl-9"
          placeholder="Search by clinic name or city"
          value={draft.q}
          onChange={(event) => setDraft((current) => ({ ...current, q: event.target.value }))}
        />
      </div>

      <Input
        aria-label="State filter"
        placeholder="State / region"
        value={draft.state}
        onChange={(event) => setDraft((current) => ({ ...current, state: event.target.value }))}
      />

      <Select
        value={draft.priority || "all"}
        onValueChange={(value) =>
          setDraft((current) => ({
            ...current,
            priority: value === "all" ? "" : (value as PriorityLevel),
          }))
        }
      >
        <SelectTrigger aria-label="Priority filter">
          <SelectValue placeholder="Priority" />
        </SelectTrigger>
        <SelectContent>
          {PRIORITY_OPTIONS.map((option) => (
            <SelectItem key={option.label} value={option.value || "all"}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Input
        aria-label="Minimum score"
        inputMode="numeric"
        placeholder="Min score"
        value={draft.min_score}
        onChange={(event) => setDraft((current) => ({ ...current, min_score: event.target.value }))}
      />

      <Input
        aria-label="Maximum score"
        inputMode="numeric"
        placeholder="Max score"
        value={draft.max_score}
        onChange={(event) => setDraft((current) => ({ ...current, max_score: event.target.value }))}
      />

      <Select
        value={draft.has_website || "all"}
        onValueChange={(value) =>
          setDraft((current) => ({
            ...current,
            has_website: value === "all" ? "" : value,
          }))
        }
      >
        <SelectTrigger aria-label="Website filter">
          <SelectValue placeholder="Website" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Any website</SelectItem>
          <SelectItem value="true">Has website</SelectItem>
          <SelectItem value="false">No website</SelectItem>
        </SelectContent>
      </Select>

      <Select
        value={draft.signal_type || "all"}
        onValueChange={(value) =>
          setDraft((current) => ({
            ...current,
            signal_type: value === "all" ? "" : value,
          }))
        }
      >
        <SelectTrigger aria-label="Signal type filter">
          <SelectValue placeholder="Signal type" />
        </SelectTrigger>
        <SelectContent>
          {SIGNAL_TYPE_OPTIONS.map((option) => (
            <SelectItem key={option.label} value={option.value || "all"}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <div className="flex gap-2 md:col-span-2 xl:col-span-4">
        <Button type="submit">Apply filters</Button>
        <Button type="button" variant="outline" onClick={clearFilters}>
          Clear
        </Button>
      </div>
    </form>
  );
}
