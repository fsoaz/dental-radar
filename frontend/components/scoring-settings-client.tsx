"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  ApiRequestError,
  fetchRescoreJob,
  fetchScoringConfig,
  updateScoringConfig,
} from "@/lib/api";
import type { PriorityLevel, RescoreJob, ScoreBand, ScoringConfig } from "@/lib/types";

const SIGNAL_KEYS = [
  "HIRING",
  "ADVERTISING",
  "WEBSITE_QUALITY",
  "MULTI_LOCATION",
  "HIGH_TICKET",
] as const;

const DEFAULT_BANDS: ScoreBand[] = [
  { name: "COLD", min: 0, max: 50 },
  { name: "WARM", min: 51, max: 100 },
  { name: "HOT", min: 101, max: 150 },
  { name: "IMMEDIATE", min: 151, max: null },
];

function validateSettings(weights: Record<string, number>, bands: ScoreBand[]): string[] {
  const errors: string[] = [];
  for (const key of SIGNAL_KEYS) {
    const value = weights[key];
    if (!Number.isInteger(value) || value < 0 || value > 1000) {
      errors.push(`${key.replaceAll("_", " ")} must be a whole number from 0 to 1000.`);
    }
  }
  if (bands[0]?.min !== 0) errors.push("The first band must start at 0.");
  bands.forEach((band, index) => {
    if (!Number.isInteger(band.min) || band.min < 0) {
      errors.push(`${band.name} minimum must be a non-negative whole number.`);
    }
    if (index === bands.length - 1) {
      if (band.max !== null) errors.push("The final band must be unbounded.");
      return;
    }
    if (band.max === null || !Number.isInteger(band.max) || band.max < band.min) {
      errors.push(`${band.name} maximum must be a whole number at least ${band.min}.`);
      return;
    }
    const next = bands[index + 1];
    if (next && next.min !== band.max + 1) {
      const kind = next.min > band.max + 1 ? "gap" : "overlap";
      errors.push(
        `${band.name} and ${next.name} have ${kind === "overlap" ? "an" : "a"} ${kind}; ${next.name} must start at ${band.max + 1}.`,
      );
    }
  });
  return errors;
}

export function ScoringSettingsClient() {
  const [weights, setWeights] = useState<Record<string, number>>({});
  const [bands, setBands] = useState<ScoreBand[]>(DEFAULT_BANDS);
  const [version, setVersion] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeJob, setActiveJob] = useState<RescoreJob | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const config = await fetchScoringConfig();
        if (!cancelled) {
          applyConfig(config);
          setActiveJob(config.rescore_job ?? null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiRequestError ? err.message : "Failed to load scoring config");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!activeJob || !["queued", "running"].includes(activeJob.status)) return;
    let cancelled = false;
    const timer = window.setInterval(() => {
      void fetchRescoreJob(activeJob.id)
        .then((job) => {
          if (cancelled) return;
          setActiveJob(job);
          if (job.status === "succeeded") {
            setMessage(`Rescore complete: ${job.rescored ?? 0} clinics updated.`);
          } else if (job.status === "failed") {
            setError(job.message ?? "Rescore failed. Please try again.");
          }
        })
        .catch((err) => {
          if (!cancelled) {
            setError(err instanceof ApiRequestError ? err.message : "Failed to check rescore status");
          }
        });
    }, 2000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [activeJob]);

  function applyConfig(config: ScoringConfig) {
    setVersion(config.version);
    setWeights({ ...config.weights });
    setBands(
      config.bands.length
        ? config.bands.map((band) => ({ ...band, name: band.name as PriorityLevel }))
        : DEFAULT_BANDS,
    );
  }

  async function save(rescore: boolean) {
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const result = await updateScoringConfig({
        weights: Object.fromEntries(
          SIGNAL_KEYS.map((key) => [key, Number(weights[key] ?? 0)]),
        ),
        bands: bands.map((band, index) => ({
          name: band.name,
          min: Number(band.min),
          max: index === bands.length - 1 ? null : Number(band.max),
        })),
        rescore,
      });
      applyConfig(result);
      setActiveJob(result.rescore_job ?? null);
      setMessage(
        result.rescore_job
          ? `Saved version ${result.version}; rescore queued.`
          : `Saved version ${result.version}.`,
      );
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Failed to save scoring config");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="rounded-lg border bg-card p-8 text-center text-muted-foreground">
        Loading scoring settings…
      </div>
    );
  }

  const validationErrors = version == null ? [] : validateSettings(weights, bands);
  const jobRunning = activeJob && ["queued", "running"].includes(activeJob.status);
  const actionsDisabled = saving || validationErrors.length > 0 || Boolean(jobRunning);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Scoring settings</h1>
        <p className="mt-2 text-muted-foreground">
          Tune signal weights and priority bands. Write access is provided by the operator-only
          application server.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Weights{version != null ? ` (v${version})` : ""}</CardTitle>
          <CardDescription>Each signal type must have a weight from 0 to 1000.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {SIGNAL_KEYS.map((key) => (
            <label key={key} className="space-y-1 text-sm">
              <span className="font-medium">{key.replaceAll("_", " ")}</span>
              <Input
                type="number"
                min={0}
                max={1000}
                step={1}
                aria-invalid={validationErrors.length > 0}
                aria-describedby={validationErrors.length ? "scoring-validation-errors" : undefined}
                value={weights[key] ?? 0}
                onChange={(event) =>
                  setWeights((current) => ({
                    ...current,
                    [key]: Number(event.target.value),
                  }))
                }
              />
            </label>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Priority bands</CardTitle>
          <CardDescription>
            Bands must start at 0, be contiguous, and end unbounded (leave the last max blank).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {bands.map((band, index) => (
            <div key={band.name} className="grid gap-2 sm:grid-cols-3">
              <Input value={band.name} readOnly aria-label={`${band.name} band name`} />
              <Input
                type="number"
                min={0}
                step={1}
                aria-label={`${band.name} min`}
                aria-invalid={validationErrors.length > 0}
                aria-describedby={validationErrors.length ? "scoring-validation-errors" : undefined}
                value={band.min}
                onChange={(event) => {
                  const next = [...bands];
                  next[index] = { ...band, min: Number(event.target.value) };
                  setBands(next);
                }}
              />
              <Input
                type="number"
                min={0}
                step={1}
                aria-label={`${band.name} max`}
                aria-invalid={validationErrors.length > 0}
                aria-describedby={validationErrors.length ? "scoring-validation-errors" : undefined}
                placeholder={index === bands.length - 1 ? "unbounded" : "max"}
                value={band.max ?? ""}
                disabled={index === bands.length - 1}
                onChange={(event) => {
                  const next = [...bands];
                  next[index] = {
                    ...band,
                    max: event.target.value === "" ? null : Number(event.target.value),
                  };
                  setBands(next);
                }}
              />
            </div>
          ))}
          {validationErrors.length ? (
            <div
              id="scoring-validation-errors"
              role="alert"
              className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive"
            >
              <p className="font-medium">Fix these settings before saving:</p>
              <ul className="mt-1 list-disc space-y-1 pl-5">
                {validationErrors.map((validationError) => (
                  <li key={validationError}>{validationError}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <div className="flex flex-wrap gap-2" aria-live="polite">
        <Button type="button" disabled={actionsDisabled} onClick={() => void save(false)}>
          {saving ? "Saving…" : "Save"}
        </Button>
        <Button type="button" variant="secondary" disabled={actionsDisabled} onClick={() => void save(true)}>
          {saving ? "Saving…" : "Save & rescore"}
        </Button>
      </div>

      {jobRunning ? (
        <p className="text-sm text-muted-foreground" aria-live="polite">
          Rescore {activeJob.status === "queued" ? "queued" : "running"} for version {activeJob.config_version}…
        </p>
      ) : null}

      {message ? <p className="text-sm text-muted-foreground">{message}</p> : null}
      {error ? (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </div>
  );
}
