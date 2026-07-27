"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, ExternalLink, MapPin, Phone, Star } from "lucide-react";

import { AIBreakdown } from "@/components/ai-breakdown";
import { ScoreBreakdown } from "@/components/score-breakdown";
import { SignalList } from "@/components/signal-list";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ApiRequestError,
  detectClinicSignals,
  enrichClinic,
  fetchClinicDetail,
  scoreClinic,
} from "@/lib/api";
import type { ClinicDetail } from "@/lib/types";

interface ClinicDetailViewProps {
  clinicId: string;
}

function safeWebsiteHref(website: string | null): string | null {
  if (!website) return null;
  try {
    const url = new URL(website);
    return url.protocol === "http:" || url.protocol === "https:" ? url.toString() : null;
  } catch {
    return null;
  }
}

export function ClinicDetailView({ clinicId }: ClinicDetailViewProps) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const listQuery = searchParams.toString();
  const backHref = listQuery ? `/clinics?${listQuery}` : "/clinics";

  const [clinic, setClinic] = useState<ClinicDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<"detect" | "enrich" | "score" | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchClinicDetail(clinicId);
      setClinic(response);
    } catch (err) {
      setClinic(null);
      setError(err instanceof ApiRequestError ? err.message : "Failed to load clinic");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function run() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetchClinicDetail(clinicId);
        if (!cancelled) setClinic(response);
      } catch (err) {
        if (!cancelled) {
          setClinic(null);
          setError(err instanceof ApiRequestError ? err.message : "Failed to load clinic");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void run();
    return () => {
      cancelled = true;
    };
  }, [clinicId]);

  async function runAction(action: "detect" | "enrich" | "score") {
    setBusyAction(action);
    setActionMessage(null);
    setActionError(null);
    try {
      if (action === "detect") {
        await detectClinicSignals(clinicId);
        await scoreClinic(clinicId);
        setActionMessage("Signals re-detected and score updated.");
      } else if (action === "enrich") {
        await enrichClinic(clinicId, true);
        setActionMessage("Enrichment refreshed.");
      } else {
        await scoreClinic(clinicId);
        setActionMessage("Score recomputed.");
      }
      await load();
      router.refresh();
    } catch (err) {
      setActionError(err instanceof ApiRequestError ? err.message : "Action failed");
    } finally {
      setBusyAction(null);
    }
  }

  if (loading) {
    return <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground">Loading clinic…</div>;
  }

  if (error || !clinic) {
    return (
      <div className="space-y-4">
        <Button asChild variant="outline">
          <Link href={backHref}>
            <ArrowLeft className="h-4 w-4" />
            Back to list
          </Link>
        </Button>
        <div role="alert" className="rounded-lg border border-destructive/30 bg-destructive/5 p-8 text-center">
          <p className="font-medium text-destructive">{error ?? "Clinic not found"}</p>
        </div>
      </div>
    );
  }

  const addressLine = [
    clinic.address?.street,
    clinic.address?.city,
    clinic.address?.state,
    clinic.address?.postal_code,
  ]
    .filter(Boolean)
    .join(", ");

  const websiteHref = safeWebsiteHref(clinic.website);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Button asChild variant="outline">
          <Link href={backHref}>
            <ArrowLeft className="h-4 w-4" />
            Back to list
          </Link>
        </Button>
        {websiteHref ? (
          <Button asChild variant="secondary">
            <a href={websiteHref} target="_blank" rel="noreferrer">
              Visit website
              <ExternalLink className="h-4 w-4" />
            </a>
          </Button>
        ) : null}
      </div>

      <div>
        <h1 className="text-3xl font-semibold tracking-tight">{clinic.name}</h1>
        <p className="mt-2 text-muted-foreground">Place ID: {clinic.place_id}</p>
      </div>

      <div className="flex flex-wrap gap-2" aria-live="polite">
        <Button
          type="button"
          variant="outline"
          disabled={busyAction !== null}
          onClick={() => void runAction("detect")}
        >
          {busyAction === "detect" ? "Re-detecting…" : "Re-detect signals"}
        </Button>
        <Button
          type="button"
          variant="outline"
          disabled={busyAction !== null}
          onClick={() => void runAction("score")}
        >
          {busyAction === "score" ? "Scoring…" : "Recompute score"}
        </Button>
        <Button
          type="button"
          variant="outline"
          disabled={busyAction !== null}
          onClick={() => void runAction("enrich")}
        >
          {busyAction === "enrich" ? "Enriching…" : "Re-enrich"}
        </Button>
      </div>
      {actionMessage ? <p className="text-sm text-muted-foreground">{actionMessage}</p> : null}
      {actionError ? (
        <p role="alert" className="text-sm text-destructive">
          {actionError}
        </p>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Profile</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {addressLine ? (
              <div className="flex gap-2">
                <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                <span>{addressLine}</span>
              </div>
            ) : null}
            {clinic.phone ? (
              <div className="flex gap-2">
                <Phone className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                <span>{clinic.phone}</span>
              </div>
            ) : null}
            <div className="flex gap-2">
              <Star className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <span>
                {clinic.google_rating ?? "—"} · {clinic.google_review_count} Google reviews
              </span>
            </div>
            <p>
              <span className="font-medium">Locations:</span> {clinic.locations_count}
            </p>
          </CardContent>
        </Card>

        <div className="space-y-6 lg:col-span-2">
          <ScoreBreakdown score={clinic.score} />
          <AIBreakdown enrichment={clinic.enrichment} />
          <SignalList signals={clinic.signals} />
        </div>
      </div>
    </div>
  );
}
