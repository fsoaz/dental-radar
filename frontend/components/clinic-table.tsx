"use client";

import Link from "next/link";

import { PriorityTag } from "@/components/priority-tag";
import { ScoreBadge } from "@/components/score-badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { ClinicListItem } from "@/lib/types";
import { formatGrowth } from "@/lib/utils";

interface ClinicTableProps {
  clinics: ClinicListItem[];
}

export function ClinicTable({ clinics }: ClinicTableProps) {
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

  return (
    <div className="rounded-lg border bg-card">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Clinic Name</TableHead>
            <TableHead>City</TableHead>
            <TableHead>Score</TableHead>
            <TableHead>Growth Probability</TableHead>
            <TableHead>Priority Level</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {clinics.map((clinic) => (
            <TableRow key={clinic.id}>
              <TableCell>
                <Link
                  href={`/clinics/${clinic.id}`}
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
