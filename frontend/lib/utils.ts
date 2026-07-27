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

export function formatDetectedAt(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const detected = new Date(iso);
  if (Number.isNaN(detected.getTime())) return null;
  const diffMs = Date.now() - detected.getTime();
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (days <= 0) return "detected today";
  if (days === 1) return "detected 1 day ago";
  return `detected ${days} days ago`;
}

export function isStaleSignal(iso: string | null | undefined, thresholdDays = 90): boolean {
  if (!iso) return false;
  const detected = new Date(iso);
  if (Number.isNaN(detected.getTime())) return false;
  const diffMs = Date.now() - detected.getTime();
  return diffMs > thresholdDays * 24 * 60 * 60 * 1000;
}
