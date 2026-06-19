import { Badge } from "@/components/ui/badge";
import type { PriorityLevel } from "@/lib/types";
import { cn, formatScore } from "@/lib/utils";

const priorityVariant: Record<PriorityLevel, "cold" | "warm" | "hot" | "immediate"> = {
  COLD: "cold",
  WARM: "warm",
  HOT: "hot",
  IMMEDIATE: "immediate",
};

interface ScoreBadgeProps {
  score: number | null;
  priority?: PriorityLevel | null;
  className?: string;
}

export function ScoreBadge({ score, priority, className }: ScoreBadgeProps) {
  const variant = priority ? priorityVariant[priority] : "secondary";

  return (
    <Badge variant={variant} className={cn("min-w-[3rem] justify-center tabular-nums", className)}>
      {formatScore(score)}
    </Badge>
  );
}
