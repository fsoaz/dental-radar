import { Suspense } from "react";

import { ClinicsPageClient } from "@/components/clinics-page-client";

export default function ClinicsPage() {
  return (
    <Suspense
      fallback={
        <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground">
          Loading clinics…
        </div>
      }
    >
      <ClinicsPageClient />
    </Suspense>
  );
}
