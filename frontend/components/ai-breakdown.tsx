import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { Enrichment } from "@/lib/types";
import { formatGrowth } from "@/lib/utils";

interface AIBreakdownProps {
  enrichment: Enrichment | null;
}

const METRICS: { key: keyof Enrichment; label: string }[] = [
  { key: "growth_probability", label: "Growth probability" },
  { key: "technology_maturity", label: "Technology maturity" },
  { key: "marketing_sophistication", label: "Marketing sophistication" },
  { key: "expansion_probability", label: "Expansion probability" },
];

export function AIBreakdown({ enrichment }: AIBreakdownProps) {
  if (!enrichment) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>AI enrichment</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No AI enrichment yet. Run enrichment from the API or CLI to populate these scores.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>AI enrichment</CardTitle>
        <CardDescription>Advisory scores from the LLM layer — they augment, not override, rule-based scoring.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2">
          {METRICS.map(({ key, label }) => (
            <div key={key} className="rounded-md border bg-muted/30 p-3">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
              <p className="mt-1 text-2xl font-semibold tabular-nums">
                {formatGrowth(enrichment[key] as number | null)}
              </p>
            </div>
          ))}
        </div>
        {enrichment.explanation ? (
          <blockquote className="rounded-md border-l-4 border-primary bg-accent/40 px-4 py-3 text-sm">
            {enrichment.explanation}
          </blockquote>
        ) : null}
      </CardContent>
    </Card>
  );
}
