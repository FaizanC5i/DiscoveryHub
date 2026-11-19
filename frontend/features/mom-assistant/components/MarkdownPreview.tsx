import type { ReactNode } from "react";

type Block =
  | { kind: "heading"; level: number; text: string }
  | { kind: "para"; text: string }
  | { kind: "bullet"; text: string; nested: boolean }
  | { kind: "number"; label: string; text: string }
  | { kind: "table"; headers: string[]; rows: string[][] };

function parse(markdown: string): Block[] {
  const lines = markdown.split("\n");
  const blocks: Block[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    const trimmed = line.trim();

    if (!trimmed) {
      index += 1;
      continue;
    }

    if (trimmed.startsWith("|")) {
      const rows: string[][] = [];
      while (index < lines.length && lines[index].trim().startsWith("|")) {
        const cells = lines[index].trim().replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim());
        if (!cells.every((cell) => /^:?-{2,}:?$/.test(cell))) rows.push(cells);
        index += 1;
      }
      if (rows.length > 0) blocks.push({ kind: "table", headers: rows[0], rows: rows.slice(1) });
      continue;
    }

    const heading = /^(#{1,6})\s+(.*)$/.exec(trimmed);
    if (heading) {
      blocks.push({ kind: "heading", level: heading[1].length, text: heading[2] });
    } else {
      const bullet = /^(\s*)-\s+(.*)$/.exec(line);
      const number = /^(\d+)\.\s+(.*)$/.exec(trimmed);
      const meta = /^_(.*)_$/.exec(trimmed);
      if (bullet) {
        blocks.push({ kind: "bullet", text: bullet[2], nested: bullet[1].length >= 2 });
      } else if (number) {
        blocks.push({ kind: "number", label: number[1], text: number[2] });
      } else {
        blocks.push({ kind: "para", text: meta ? meta[1] : trimmed });
      }
    }
    index += 1;
  }
  return blocks;
}

function inline(text: string): ReactNode[] {
  return text
    .split(/(\*\*[^*]+\*\*)/)
    .filter(Boolean)
    .map((part, index) =>
      part.length > 4 && part.startsWith("**") && part.endsWith("**") ? (
        <strong key={index} className="font-semibold text-fg">
          {part.slice(2, -2)}
        </strong>
      ) : (
        <span key={index}>{part}</span>
      ),
    );
}

const headingClass = (level: number) => {
  if (level <= 1) return "text-title-large font-semibold text-fg";
  if (level === 2) return "text-title-small font-semibold text-fg pt-3";
  return "text-body-large font-semibold text-fg pt-2";
};

/** Renders the server's Markdown preview with the application's typography and table styles. */
export function MarkdownPreview({ markdown }: { markdown: string }) {
  const blocks = parse(markdown);

  return (
    <article className="flex flex-col gap-3 rounded-card border border-border-subtle bg-page p-6 text-body-medium text-fg lg:p-8">
      {blocks.map((block, index) => {
        if (block.kind === "heading") {
          const Tag = block.level <= 1 ? "h2" : block.level === 2 ? "h3" : "h4";
          return (
            <Tag key={index} className={headingClass(block.level)}>
              {inline(block.text)}
            </Tag>
          );
        }
        if (block.kind === "para") {
          return (
            <p key={index} className="text-body-medium text-fg">
              {inline(block.text)}
            </p>
          );
        }
        if (block.kind === "bullet") {
          return (
            <ul key={index} className={block.nested ? "list-disc pl-10" : "list-disc pl-6"}>
              <li className="text-body-medium text-fg">{inline(block.text)}</li>
            </ul>
          );
        }
        if (block.kind === "number") {
          return (
            <p key={index} className="pl-6 text-body-medium text-fg">
              <span className="font-semibold">{block.label}.</span> {inline(block.text)}
            </p>
          );
        }
        return (
          <div key={index} className="overflow-x-auto">
            <table className="w-full border-collapse text-body-small">
              <thead>
                <tr className="bg-surface-muted">
                  {block.headers.map((header, cell) => (
                    <th key={cell} className="border border-border-subtle px-3 py-2 text-left font-semibold text-fg">
                      {inline(header)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {block.rows.map((row, rowIndex) => (
                  <tr key={rowIndex}>
                    {block.headers.map((_, cell) => (
                      <td key={cell} className="border border-border-subtle px-3 py-2 align-top text-fg">
                        {inline(row[cell] ?? "")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })}
    </article>
  );
}
