import { Badge } from "@/components/ui/badge";
import type { PriorityLevel } from "@/lib/types";
import { formatPriority } from "@/lib/utils";

const priorityVariant: Record<PriorityLevel, "cold" | "warm" | "hot" | "immediate"> = {
  COLD: "cold",
  WARM: "warm",
  HOT: "hot",
  IMMEDIATE: "immediate",
};

interface PriorityTagProps {
  priority: PriorityLevel | null | undefined;
}

export function PriorityTag({ priority }: PriorityTagProps) {
  if (!priority) {
    return <span className="text-sm text-muted-foreground">—</span>;
  }

  return <Badge variant={priorityVariant[priority]}>{formatPriority(priority)}</Badge>;
}
