import type { Source } from "../api/rules";

type Props = {
  isLoading: boolean;
  sources: Source[];
};

export function SourceList({ isLoading, sources }: Props) {
  return (
    <aside className="sources">
      <div className="sources__header">
        <h2>Sources</h2>
        <span>{sources.length}</span>
      </div>
      {sources.length === 0 ? (
        <p className="sources__empty">{isLoading ? "正在检索..." : "No sources yet"}</p>
      ) : (
        sources.map((source, index) => (
          <article className="source" key={`${source.source}-${index}`}>
            <div className="source__meta">
              <span>{source.source}</span>
              {typeof source.score === "number" ? <span>{source.score.toFixed(4)}</span> : null}
            </div>
            <p>{source.title_path.join(" / ") || "Untitled section"}</p>
            <small>{source.content_preview}</small>
          </article>
        ))
      )}
    </aside>
  );
}
