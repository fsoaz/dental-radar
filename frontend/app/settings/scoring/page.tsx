import { Suspense } from "react";

import { ScoringSettingsClient } from "@/components/scoring-settings-client";

export default function ScoringSettingsPage() {
  return (
    <Suspense
      fallback={
        <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground">
          Loading scoring settings…
        </div>
      }
    >
      <ScoringSettingsClient />
    </Suspense>
  );
}
