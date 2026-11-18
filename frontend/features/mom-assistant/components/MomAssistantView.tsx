"use client";

import { useRef, useState, type ChangeEvent, type DragEvent, type ReactNode } from "react";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";
import {
  downloadDocument,
  generateDetailedSummary,
  generateMinutes,
  saveBlob,
  uploadTranscripts,
} from "../services/momService";
import {
  MAX_UPLOAD_BYTES,
  TRANSCRIPT_FORMATS,
  type DocumentKind,
  type DownloadFormat,
  type GeneratedDocument,
  type TranscriptResult,
} from "../types/mom";
import { MarkdownPreview } from "./MarkdownPreview";

const ACCEPT = ".txt,.md,.vtt,.srt,.docx,.pdf,.html,.htm,.rtf,.json,.csv,.log";
const BLOCKED_EXTENSIONS = /\.(doc|png|jpe?g|gif|bmp|webp|zip|rar|7z|exe|dll|mp3|mp4|mov|wav|avi|xlsx|xls|pptx|ppt)$/i;

const TABS: { kind: DocumentKind; label: string }[] = [
  { kind: "mom", label: "Minutes of Meeting" },
  { kind: "detailed-summary", label: "Detailed Meeting Summary" },
];

const DOWNLOADS: { format: DownloadFormat; label: string }[] = [
  { format: "docx", label: "Word (.docx)" },
  { format: "md", label: "Markdown (.md)" },
  { format: "json", label: "JSON (.json)" },
];

type Notice = { tone: "success" | "error"; text: string };

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function extensionOf(name: string): string {
  const dot = name.lastIndexOf(".");
  return dot === -1 ? "FILE" : name.slice(dot + 1).toUpperCase();
}

/** The MoM Assistant: upload transcripts, generate the MoM and detailed summary, preview and download. */
export function MomAssistantView() {
  const [files, setFiles] = useState<File[]>([]);
  const [transcript, setTranscript] = useState<TranscriptResult | null>(null);
  const [mom, setMom] = useState<GeneratedDocument | null>(null);
  const [detailed, setDetailed] = useState<GeneratedDocument | null>(null);
  const [tab, setTab] = useState<DocumentKind>("mom");
  const [uploadPercent, setUploadPercent] = useState<number | null>(null);
  const [busy, setBusy] = useState<"generate" | "detailed" | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const replacing = useRef(false);

  const sourceName = transcript?.files[0]?.name ?? files[0]?.name ?? null;
  const isBusy = busy !== null || uploadPercent !== null;

  function clearResults() {
    setTranscript(null);
    setMom(null);
    setDetailed(null);
  }

  function addFiles(incoming: FileList | File[], replace: boolean) {
    const problems: string[] = [];
    const valid = Array.from(incoming).filter((file) => {
      if (file.size === 0) {
        problems.push(`${file.name} is empty.`);
        return false;
      }
      if (file.size > MAX_UPLOAD_BYTES) {
        problems.push(`${file.name} is larger than 25 MB.`);
        return false;
      }
      if (BLOCKED_EXTENSIONS.test(file.name)) {
        problems.push(`${file.name} is not a supported transcript. Use one of: ${TRANSCRIPT_FORMATS}.`);
        return false;
      }
      return true;
    });

    if (valid.length > 0) {
      setFiles((current) => (replace ? valid : [...current, ...valid]));
      clearResults();
    }
    setNotice(problems.length > 0 ? { tone: "error", text: problems.join(" ") } : null);
  }

  function removeFile(index: number) {
    setFiles((current) => current.filter((_, position) => position !== index));
    clearResults();
  }

  function onInputChange(event: ChangeEvent<HTMLInputElement>) {
    if (event.target.files && event.target.files.length > 0) {
      addFiles(event.target.files, replacing.current);
    }
    replacing.current = false;
    event.target.value = "";
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    if (event.dataTransfer.files.length > 0) addFiles(event.dataTransfer.files, false);
  }

  async function handleGenerate() {
    if (files.length === 0 || isBusy) return;
    setNotice(null);
    setBusy("generate");
    try {
      let source = transcript;
      if (!source) {
        setUploadPercent(0);
        source = await uploadTranscripts(files, setUploadPercent);
        setTranscript(source);
        setUploadPercent(null);
      }
      const result = await generateMinutes(source.transcript);
      setMom(result);
      setDetailed(null);
      setTab("mom");
      setNotice({ tone: "success", text: "Minutes of Meeting generated." });
    } catch (error) {
      setNotice({ tone: "error", text: messageOf(error) });
    } finally {
      setUploadPercent(null);
      setBusy(null);
    }
  }

  async function handleDetailed() {
    if (!transcript || !mom || isBusy) return;
    setNotice(null);
    setBusy("detailed");
    try {
      setDetailed(await generateDetailedSummary(transcript.transcript, mom.output));
      setNotice({ tone: "success", text: "Detailed meeting summary generated." });
    } catch (error) {
      setNotice({ tone: "error", text: messageOf(error) });
    } finally {
      setBusy(null);
    }
  }

  async function handleDownload(kind: DocumentKind, format: DownloadFormat) {
    const source = kind === "mom" ? mom : detailed;
    if (!source || downloading) return;
    setDownloading(`${kind}:${format}`);
    try {
      const { blob, filename } = await downloadDocument(
        kind,
        format,
        source.output,
        source.project_name || null,
        sourceName,
      );
      saveBlob(blob, filename);
    } catch (error) {
      setNotice({ tone: "error", text: messageOf(error) });
    } finally {
      setDownloading(null);
    }
  }

  const hasResults = transcript !== null || mom !== null;

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-2">
        <h1 className="text-title-large font-semibold text-fg">MOM Assistant</h1>
        <p className="max-w-3xl text-body-large text-fg-muted">
          Upload a meeting transcript to generate Minutes of Meeting and a detailed summary. Download either one as
          Word, Markdown or JSON.
        </p>
      </header>

      <Card className="flex flex-col gap-6 p-6 lg:p-8">
        <div className="flex flex-col gap-1">
          <h2 className="text-title-small font-semibold text-fg">Upload Meeting Transcript</h2>
          <p className="text-body-medium text-fg-muted">
            Supported formats: {TRANSCRIPT_FORMATS}. Several files are read as one meeting.
          </p>
        </div>

        <div
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={cn(
            "flex flex-col items-center gap-3 rounded-card border-2 border-dashed p-8 text-center transition-colors",
            dragging ? "border-border-brand bg-surface-brand-subtle" : "border-border bg-page",
          )}
        >
          <p className="text-body-medium text-fg">Drag and drop transcript files here</p>
          <div className="flex flex-wrap justify-center gap-3">
            <Button variant="secondary" size="sm" disabled={isBusy} onClick={() => inputRef.current?.click()}>
              Browse files
            </Button>
            {files.length > 0 ? (
              <Button
                variant="outline"
                size="sm"
                disabled={isBusy}
                onClick={() => {
                  replacing.current = true;
                  inputRef.current?.click();
                }}
              >
                Replace files
              </Button>
            ) : null}
          </div>
          <input
            ref={inputRef}
            type="file"
            multiple
            accept={ACCEPT}
            onChange={onInputChange}
            className="sr-only"
            aria-label="Choose meeting transcript files"
          />
        </div>

        {files.length === 0 ? (
          <p className="rounded-card bg-surface-muted p-4 text-body-medium text-fg-muted">
            No transcript uploaded yet.
          </p>
        ) : (
          <ul className="flex flex-col divide-y divide-border-subtle rounded-card border border-border-subtle">
            {files.map((file, index) => (
              <li key={`${file.name}-${index}`} className="flex flex-wrap items-center justify-between gap-3 p-4">
                <div className="flex min-w-0 flex-col gap-1">
                  <span className="truncate text-body-medium font-semibold text-fg">{file.name}</span>
                  <span className="text-caption text-fg-muted">
                    {extensionOf(file.name)} · {formatBytes(file.size)}
                  </span>
                </div>
                <Button variant="subtle" size="sm" disabled={isBusy} onClick={() => removeFile(index)}>
                  Remove
                </Button>
              </li>
            ))}
          </ul>
        )}

        {uploadPercent !== null ? (
          <ProgressBar value={uploadPercent} label={`Uploading transcripts… ${uploadPercent}%`} />
        ) : null}
        {busy === "generate" && uploadPercent === null ? (
          <Spinner label="Generating the Minutes of Meeting. This can take a minute." />
        ) : null}

        {notice?.tone === "error" ? <Alert>{notice.text}</Alert> : null}
        {notice?.tone === "success" ? (
          <p role="status" className="text-body-small text-badge-success-fg">
            {notice.text}
          </p>
        ) : null}

        <div>
          <Button
            disabled={files.length === 0 || isBusy}
            loading={busy === "generate"}
            onClick={() => void handleGenerate()}
          >
            Generate Meeting Minutes
          </Button>
        </div>
      </Card>

      {hasResults ? (
        <Card className="flex flex-col gap-6 p-6 lg:p-8">
          <div role="group" aria-label="Meeting output" className="flex w-fit flex-wrap rounded-control bg-surface-muted p-1">
            {TABS.map((item) => (
              <button
                key={item.kind}
                type="button"
                aria-pressed={tab === item.kind}
                onClick={() => setTab(item.kind)}
                className={cn(
                  "h-9 rounded-control px-4 text-body-medium font-semibold transition-colors",
                  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-brand-strong",
                  tab === item.kind ? "bg-surface text-fg-brand" : "text-fg hover:text-fg-muted",
                )}
              >
                {item.label}
              </button>
            ))}
          </div>

          {tab === "mom" ? (
            <OutputPanel
              doc={mom}
              kind="mom"
              emptyText="Generate Meeting Minutes above to create the MoM from this transcript."
              downloading={downloading}
              onDownload={handleDownload}
            />
          ) : (
            <OutputPanel
              doc={detailed}
              kind="detailed-summary"
              emptyText={
                mom
                  ? "Create the detailed meeting summary from the transcript and the Minutes of Meeting."
                  : "Generate the Minutes of Meeting first. The detailed summary builds on it."
              }
              downloading={downloading}
              onDownload={handleDownload}
              action={
                mom ? (
                  <Button
                    variant="secondary"
                    disabled={isBusy}
                    loading={busy === "detailed"}
                    onClick={() => void handleDetailed()}
                  >
                    {detailed ? "Regenerate detailed summary" : "Generate detailed summary"}
                  </Button>
                ) : null
              }
            />
          )}
        </Card>
      ) : null}
    </div>
  );
}

interface OutputPanelProps {
  doc: GeneratedDocument | null;
  kind: DocumentKind;
  emptyText: string;
  downloading: string | null;
  onDownload: (kind: DocumentKind, format: DownloadFormat) => void;
  action?: ReactNode;
}

function OutputPanel({ doc, kind, emptyText, downloading, onDownload, action }: OutputPanelProps) {
  if (!doc) {
    return (
      <div className="flex flex-col items-start gap-4">
        <p className="text-body-medium text-fg-muted">{emptyText}</p>
        {action}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          {DOWNLOADS.map((item) => (
            <Button
              key={item.format}
              variant="outline"
              size="sm"
              disabled={downloading !== null}
              loading={downloading === `${kind}:${item.format}`}
              onClick={() => onDownload(kind, item.format)}
            >
              {item.label}
            </Button>
          ))}
        </div>
        {action}
      </div>
      <MarkdownPreview markdown={doc.preview} />
    </div>
  );
}
