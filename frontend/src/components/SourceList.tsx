import type { Source } from "../api/rules";

type Props = {
  sources: Source[];
};

export function SourceList({ sources }: Props) {
  if (sources.length === 0) {
    return null;
  }

  return (
    <aside className="sources">
      <h2>Sources</h2>
      {sources.map((source, index) => (
        <article className="source" key={`${source.source}-${index}`}>
          <div className="source__meta">
            <span>{source.source}</span>
            {typeof source.score === "number" ? <span>{source.score.toFixed(4)}</span> : null}
          </div>
          <p>{source.title_path.join(" / ") || "Untitled section"}</p>
          <small>{source.content_preview}</small>
        </article>
      ))}
    </aside>
  );
}
