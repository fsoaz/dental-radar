import { Suspense } from "react";

import { ClinicDetailView } from "@/components/clinic-detail-view";

interface ClinicDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function ClinicDetailPage({ params }: ClinicDetailPageProps) {
  const { id } = await params;
  return (
    <Suspense
      fallback={
        <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground">
          Loading clinic…
        </div>
      }
    >
      <ClinicDetailView clinicId={id} />
    </Suspense>
  );
}
