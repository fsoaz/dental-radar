"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowLeft, ExternalLink, MapPin, Phone, Star } from "lucide-react";

import { AIBreakdown } from "@/components/ai-breakdown";
import { ScoreBreakdown } from "@/components/score-breakdown";
import { SignalList } from "@/components/signal-list";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiRequestError, fetchClinicDetail } from "@/lib/api";
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
  const [clinic, setClinic] = useState<ClinicDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
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

    void load();
    return () => {
      cancelled = true;
    };
  }, [clinicId]);

  if (loading) {
    return <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground">Loading clinic…</div>;
  }

  if (error || !clinic) {
    return (
      <div className="space-y-4">
        <Button asChild variant="outline">
          <Link href="/clinics">
            <ArrowLeft className="h-4 w-4" />
            Back to list
          </Link>
        </Button>
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-8 text-center">
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
          <Link href="/clinics">
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
