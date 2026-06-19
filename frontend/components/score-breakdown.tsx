import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Score } from "@/lib/types";
import { ScoreBadge } from "@/components/score-badge";
import { PriorityTag } from "@/components/priority-tag";

interface ScoreBreakdownProps {
  score: Score | null;
}

export function ScoreBreakdown({ score }: ScoreBreakdownProps) {
  if (!score) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Rule-based score</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">This clinic has not been scored yet.</p>
        </CardContent>
      </Card>
    );
  }

  const entries = Object.entries(score.breakdown).sort(([, a], [, b]) => b - a);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <div>
          <CardTitle>Rule-based score</CardTitle>
          <p className="mt-1 text-sm text-muted-foreground">
            Config v{score.config_version ?? "—"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ScoreBadge score={score.total} priority={score.priority} />
          <PriorityTag priority={score.priority} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {entries.map(([type, points]) => (
            <div key={type} className="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
              <span>{type.replaceAll("_", " ")}</span>
              <span className="font-medium tabular-nums">+{points}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
