import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPriority(priority: string | null | undefined): string {
  if (!priority) return "—";
  return priority.charAt(0) + priority.slice(1).toLowerCase();
}

export function formatScore(score: number | null | undefined): string {
  if (score == null) return "—";
  return String(score);
}

export function formatGrowth(growth: number | null | undefined): string {
  if (growth == null) return "—";
  return `${growth}%`;
}
