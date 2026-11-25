"use client";

import { useEffect, useState } from "react";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { apiRequest } from "@/lib/api/client";
import { API_PATHS } from "@/lib/api/endpoints";
import type { Project } from "@/types/project";
import { attachToProjects } from "../services/momService";
import type { DocumentKind, GeneratedDocument } from "../types/mom";

interface AttachToProjectsProps {
  mom: GeneratedDocument | null;
  detailed: GeneratedDocument | null;
  sourceName: string | null;
}

/** Choose projects and save the MoM or detailed summary into their context libraries. */
export function AttachToProjects({ mom, detailed, sourceName }: AttachToProjectsProps) {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const [busy, setBusy] = useState<DocumentKind | null>(null);
  const [message, setMessage] = useState<{ tone: "success" | "error"; text: string } | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    apiRequest<Project[]>(API_PATHS.projects.list)
      .then(setProjects)
      .catch(() => setLoadError("Could not load your projects."));
  }, []);

  if (!mom && !detailed) return null;

  function toggle(projectId: number) {
    setSelected((current) =>
      current.includes(projectId) ? current.filter((id) => id !== projectId) : [...current, projectId],
    );
  }

  async function attach(kind: DocumentKind) {
    const source = kind === "mom" ? mom : detailed;
    if (!source || selected.length === 0 || busy) return;
    setBusy(kind);
    setMessage(null);
    try {
      const { results } = await attachToProjects(kind, source.output, selected, source.project_name || null, sourceName);
      const failed = results.filter((result) => !result.ok);
      const names = (projects ?? []).reduce<Record<number, string>>((map, project) => {
        map[project.id] = project.name;
        return map;
      }, {});
      if (failed.length === 0) {
        setMessage({
          tone: "success",
          text: `Added to ${results.length} ${results.length === 1 ? "project" : "projects"}: ${results
            .map((result) => names[result.project_id] ?? `#${result.project_id}`)
            .join(", ")}.`,
        });
      } else {
        setMessage({
          tone: "error",
          text: failed
            .map((result) => `${names[result.project_id] ?? `#${result.project_id}`}: ${result.error}`)
            .join(" "),
        });
      }
    } catch (error) {
      setMessage({ tone: "error", text: error instanceof Error ? error.message : "Could not add to projects." });
    } finally {
      setBusy(null);
    }
  }

  return (
    <Card className="flex flex-col gap-5 p-6 lg:p-8">
      <div className="flex flex-col gap-1">
        <h2 className="text-title-small font-semibold text-fg">Add to project context</h2>
        <p className="text-body-medium text-fg-muted">
          The document is saved as a note in each selected project&apos;s context library, where it is mapped like any other source.
        </p>
      </div>

      {projects === null && !loadError ? <Spinner label="Loading your projects…" /> : null}
      {loadError ? <Alert>{loadError}</Alert> : null}

      {projects && projects.length === 0 ? (
        <p className="text-body-medium text-fg-muted">You have no projects yet. Create one to attach this document.</p>
      ) : null}

      {projects && projects.length > 0 ? (
        <ul className="grid gap-2 sm:grid-cols-2">
          {projects.map((project) => (
            <li key={project.id}>
              <label className="flex cursor-pointer items-center gap-3 rounded-card border border-border-subtle bg-page p-3">
                <input
                  type="checkbox"
                  checked={selected.includes(project.id)}
                  onChange={() => toggle(project.id)}
                  disabled={busy !== null}
                  className="size-4 accent-fg-brand"
                />
                <span className="truncate text-body-medium text-fg">{project.name}</span>
              </label>
            </li>
          ))}
        </ul>
      ) : null}

      <div className="flex flex-wrap gap-3">
        {mom ? (
          <Button
            variant="secondary"
            disabled={selected.length === 0 || busy !== null}
            loading={busy === "mom"}
            onClick={() => void attach("mom")}
          >
            Add Minutes of Meeting
          </Button>
        ) : null}
        {detailed ? (
          <Button
            variant="secondary"
            disabled={selected.length === 0 || busy !== null}
            loading={busy === "detailed-summary"}
            onClick={() => void attach("detailed-summary")}
          >
            Add detailed summary
          </Button>
        ) : null}
      </div>

      {message?.tone === "error" ? <Alert>{message.text}</Alert> : null}
      {message?.tone === "success" ? (
        <p role="status" className="text-body-small text-badge-success-fg">
          {message.text}
        </p>
      ) : null}
    </Card>
  );
}
