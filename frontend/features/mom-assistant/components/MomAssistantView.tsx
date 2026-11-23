"use client";

import { useRef, useState, type ChangeEvent, type DragEvent } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeftIcon } from "@/components/icons";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Spinner } from "@/components/ui/Spinner";
import { Textarea } from "@/components/ui/Textarea";
import { ROUTES } from "@/lib/constants";
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
import { AttachToProjects } from "./AttachToProjects";
import { MarkdownPreview } from "./MarkdownPreview";

const ACCEPT = ".txt,.md,.vtt,.srt,.docx,.pdf,.html,.htm,.rtf,.json,.csv,.log";
const BLOCKED_EXTENSIONS = /\.(doc|png|jpe?g|gif|bmp|webp|zip|rar|7z|exe|dll|mp3|mp4|mov|wav|avi|xlsx|xls|pptx|ppt)$/i;

const OUTPUT_TABS: { kind: DocumentKind; label: string }[] = [
  { kind: "mom", label: "Minutes of Meeting" },
  { kind: "detailed-summary", label: "Detailed Meeting Summary" },
];

const INPUT_MODES: { key: "upload" | "paste"; label: string }[] = [
  { key: "upload", label: "Upload files" },
  { key: "paste", label: "Paste text" },
];

const DOWNLOADS: { format: DownloadFormat; label: string }[] = [
  { format: "docx", label: "Word (.docx)" },
  { format: "md", label: "Markdown (.md)" },
  { format: "json", label: "JSON (.json)" },
];

type Notice = { tone: "success" | "error"; text: string };
type Stage = "uploading" | "minutes" | "detailed" | null;

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

const segmentClass = (active: boolean) =>
  cn(
    "h-9 rounded-control px-4 text-body-medium font-semibold transition-colors",
    "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-border-brand-strong",
    active ? "bg-surface text-fg-brand" : "text-fg hover:text-fg-muted",
  );

/** Upload or paste a transcript, then one click creates the Minutes of Meeting and the detailed summary. */
export function MomAssistantView() {
  const router = useRouter();
  const [inputMode, setInputMode] = useState<"upload" | "paste">("upload");
  const [files, setFiles] = useState<File[]>([]);
  const [pastedText, setPastedText] = useState("");
  const [transcript, setTranscript] = useState<TranscriptResult | null>(null);
  const [mom, setMom] = useState<GeneratedDocument | null>(null);
  const [detailed, setDetailed] = useState<GeneratedDocument | null>(null);
  const [tab, setTab] = useState<DocumentKind>("mom");
  const [uploadPercent, setUploadPercent] = useState<number | null>(null);
  const [stage, setStage] = useState<Stage>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const replacing = useRef(false);

  const sourceName = transcript?.files[0]?.name ?? files[0]?.name ?? null;
  const isBusy = stage !== null;
  const canGenerate = inputMode === "upload" ? files.length > 0 : pastedText.trim().length > 0;

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

  function onPasteChange(text: string) {
    setPastedText(text);
    clearResults();
  }

  /** One click: read the transcript, then create the MoM, then the detailed summary from it. */
  async function handleGenerate() {
    if (!canGenerate || isBusy) return;
    setNotice(null);
    clearResults();
    setTab("mom");

    try {
      let source: TranscriptResult;
      if (inputMode === "paste") {
        source = { transcript: pastedText.trim(), files: [] };
      } else {
        setStage("uploading");
        setUploadPercent(0);
        source = await uploadTranscripts(files, setUploadPercent);
        setUploadPercent(null);
      }
      setTranscript(source);

      setStage("minutes");
      const minutes = await generateMinutes(source.transcript);
      setMom(minutes);

      setStage("detailed");
      try {
        setDetailed(await generateDetailedSummary(source.transcript, minutes.output));
        setNotice({ tone: "success", text: "Minutes of Meeting and detailed summary generated." });
      } catch (error) {
        setNotice({
          tone: "error",
          text: `The Minutes of Meeting is ready, but the detailed summary failed: ${messageOf(error)}`,
        });
      }
    } catch (error) {
      setNotice({ tone: "error", text: messageOf(error) });
    } finally {
      setUploadPercent(null);
      setStage(null);
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

  function goBack() {
    if (window.history.length > 1) {
      router.back();
    } else {
      router.push(ROUTES.dashboard);
    }
  }

  const hasResults = mom !== null || detailed !== null || stage !== null;

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col gap-4">
        <div>
          <Button variant="outline" size="sm" onClick={goBack}>
            <ChevronLeftIcon className="size-4" />
            Back
          </Button>
        </div>
        <div className="flex flex-col gap-2">
          <h1 className="text-title-large font-semibold text-fg">MOM Assistant</h1>
          <p className="max-w-3xl text-body-large text-fg-muted">
            Upload or paste a meeting transcript. One click creates the Minutes of Meeting and a detailed summary.
            Download either one as Word, Markdown or JSON.
          </p>
        </div>
      </header>

      <Card className="flex flex-col gap-6 p-6 lg:p-8">
        <div className="flex flex-col gap-4">
          <h2 className="text-title-small font-semibold text-fg">Meeting Transcript</h2>
          <div role="group" aria-label="Transcript input" className="flex w-fit rounded-control bg-surface-muted p-1">
            {INPUT_MODES.map((mode) => (
              <button
                key={mode.key}
                type="button"
                aria-pressed={inputMode === mode.key}
                disabled={isBusy}
                onClick={() => setInputMode(mode.key)}
                className={segmentClass(inputMode === mode.key)}
              >
                {mode.label}
              </button>
            ))}
          </div>
        </div>

        {inputMode === "upload" ? (
          <>
            <p className="text-body-medium text-fg-muted">
              Supported formats: {TRANSCRIPT_FORMATS}. Several files are read as one meeting.
            </p>

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
          </>
        ) : (
          <div className="flex flex-col gap-2">
            <Textarea
              value={pastedText}
              onChange={(event) => onPasteChange(event.target.value)}
              disabled={isBusy}
              rows={10}
              placeholder="Paste the meeting transcript here…"
              aria-label="Meeting transcript text"
            />
            <p className="text-caption text-fg-muted">
              {pastedText.trim().length === 0 ? "No text pasted yet." : `${pastedText.trim().length} characters`}
            </p>
          </div>
        )}

        {stage === "uploading" && uploadPercent !== null ? (
          <ProgressBar value={uploadPercent} label={`Uploading transcripts… ${uploadPercent}%`} />
        ) : null}
        {stage === "minutes" ? <Spinner label="Generating the Minutes of Meeting. This can take a minute." /> : null}
        {stage === "detailed" ? <Spinner label="Generating the detailed meeting summary…" /> : null}

        {notice?.tone === "error" ? <Alert>{notice.text}</Alert> : null}
        {notice?.tone === "success" ? (
          <p role="status" className="text-body-small text-badge-success-fg">
            {notice.text}
          </p>
        ) : null}

        <div>
          <Button disabled={!canGenerate || isBusy} loading={isBusy} onClick={() => void handleGenerate()}>
            Generate Meeting Minutes
          </Button>
        </div>
      </Card>

      {hasResults ? (
        <Card className="flex flex-col gap-6 p-6 lg:p-8">
          <div role="group" aria-label="Meeting output" className="flex w-fit flex-wrap rounded-control bg-surface-muted p-1">
            {OUTPUT_TABS.map((item) => (
              <button
                key={item.kind}
                type="button"
                aria-pressed={tab === item.kind}
                onClick={() => setTab(item.kind)}
                className={segmentClass(tab === item.kind)}
              >
                {item.label}
              </button>
            ))}
          </div>

          <OutputPanel
            doc={tab === "mom" ? mom : detailed}
            kind={tab}
            emptyText={
              tab === "mom"
                ? "The Minutes of Meeting will appear here once it is generated."
                : "The detailed meeting summary will appear here once it is generated."
            }
            downloading={downloading}
            onDownload={handleDownload}
          />
        </Card>
      ) : null}

      <AttachToProjects mom={mom} detailed={detailed} sourceName={sourceName} />
    </div>
  );
}

interface OutputPanelProps {
  doc: GeneratedDocument | null;
  kind: DocumentKind;
  emptyText: string;
  downloading: string | null;
  onDownload: (kind: DocumentKind, format: DownloadFormat) => void;
}

function OutputPanel({ doc, kind, emptyText, downloading, onDownload }: OutputPanelProps) {
  if (!doc) {
    return <p className="text-body-medium text-fg-muted">{emptyText}</p>;
  }

  return (
    <div className="flex flex-col gap-4">
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
      <MarkdownPreview markdown={doc.preview} />
    </div>
  );
}
