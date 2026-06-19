import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Signal } from "@/lib/types";

interface SignalListProps {
  signals: Signal[];
}

export function SignalList({ signals }: SignalListProps) {
  if (signals.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Buying signals</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No signals detected yet for this clinic.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Buying signals</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {signals.map((signal) => (
          <div key={`${signal.type}-${signal.evidence ?? "none"}`} className="rounded-md border p-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="secondary">{signal.type.replaceAll("_", " ")}</Badge>
              <span className="text-sm font-medium tabular-nums">+{signal.applied_weight} pts</span>
              <span className="text-sm text-muted-foreground">
                confidence {(signal.confidence * 100).toFixed(0)}%
              </span>
            </div>
            {signal.evidence ? (
              <p className="mt-2 text-sm text-foreground">{signal.evidence}</p>
            ) : (
              <p className="mt-2 text-sm text-muted-foreground">No evidence captured.</p>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
