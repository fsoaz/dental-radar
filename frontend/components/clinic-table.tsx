"use client";

import Link from "next/link";

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

  return (
    <div className="rounded-lg border bg-card">
      <Table>
        <TableCaption className="sr-only">
          Ranked dental clinics with score, growth probability, and priority
        </TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead scope="col">Clinic Name</TableHead>
            <TableHead scope="col">City</TableHead>
            <TableHead scope="col">Score</TableHead>
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
