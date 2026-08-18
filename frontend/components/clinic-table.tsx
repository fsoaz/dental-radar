"use client";

import Link from "next/link";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";

import { PriorityTag } from "@/components/priority-tag";
import { ScoreBadge } from "@/components/score-badge";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ClinicListItem } from "@/lib/types";
import { formatGrowth } from "@/lib/utils";

interface ClinicTableProps {
  clinics: ClinicListItem[];
  listQuery?: string;
}

export function ClinicTable({ clinics, listQuery = "" }: ClinicTableProps) {
  if (clinics.length === 0) {
    return (
      <div className="rounded-lg border border-dashed bg-card p-12 text-center">
        <p className="text-lg font-medium">No clinics match your filters</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Try broadening your search or clearing filters to see more results.
        </p>
      </div>
    );
  }

  const querySuffix = listQuery ? `?${listQuery}` : "";
  const currentSort = new URLSearchParams(listQuery).get("sort") ?? "-score";

  function sortHref(sort: "name" | "score" | "-score"): string {
    const params = new URLSearchParams(listQuery);
    params.delete("page");
    if (sort === "-score") params.delete("sort");
    else params.set("sort", sort);
    const query = params.toString();
    return query ? `/clinics?${query}` : "/clinics";
  }

  return (
    <div className="rounded-lg border bg-card">
      <Table>
        <TableCaption className="sr-only">
          Ranked dental clinics with score, growth probability, and priority
        </TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead scope="col" aria-sort={currentSort === "name" ? "ascending" : "none"}>
              <Link className="inline-flex items-center gap-1 hover:text-foreground" href={sortHref("name")}>
                Clinic Name
                {currentSort === "name" ? <ArrowUp aria-hidden="true" className="h-3.5 w-3.5" /> : <ArrowUpDown aria-hidden="true" className="h-3.5 w-3.5" />}
              </Link>
            </TableHead>
            <TableHead scope="col">City</TableHead>
            <TableHead
              scope="col"
              aria-sort={
                currentSort === "score"
                  ? "ascending"
                  : currentSort === "-score"
                    ? "descending"
                    : "none"
              }
            >
              <Link
                className="inline-flex items-center gap-1 hover:text-foreground"
                href={sortHref(currentSort === "-score" ? "score" : "-score")}
              >
                Score
                {currentSort === "score" ? (
                  <ArrowUp aria-hidden="true" className="h-3.5 w-3.5" />
                ) : currentSort === "-score" ? (
                  <ArrowDown aria-hidden="true" className="h-3.5 w-3.5" />
                ) : (
                  <ArrowUpDown aria-hidden="true" className="h-3.5 w-3.5" />
                )}
              </Link>
            </TableHead>
            <TableHead scope="col">Growth Probability</TableHead>
            <TableHead scope="col">Priority Level</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {clinics.map((clinic) => (
            <TableRow key={clinic.id}>
              <TableCell>
                <Link
                  href={`/clinics/${clinic.id}${querySuffix}`}
                  className="font-medium text-primary hover:underline"
                >
                  {clinic.name}
                </Link>
              </TableCell>
              <TableCell>{clinic.city ?? "—"}</TableCell>
              <TableCell>
                <ScoreBadge score={clinic.score} priority={clinic.priority} />
              </TableCell>
              <TableCell className="tabular-nums">{formatGrowth(clinic.growth_probability)}</TableCell>
              <TableCell>
                <PriorityTag priority={clinic.priority} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
