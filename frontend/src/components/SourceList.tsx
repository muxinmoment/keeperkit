import type { ModuleSource } from "../api/modules";
import type { Source } from "../api/rules";

type Props = {
  isLoading: boolean;
  sources: Array<Source | ModuleSource>;
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
              <span>{getKnowledgeBase(source)} / {source.source}</span>
              {typeof source.score === "number" ? <span>{source.score.toFixed(4)}</span> : null}
            </div>
            <p>{source.title_path.join(" / ") || "Untitled section"}</p>
            {"content_type" in source ? <em>{source.content_type}</em> : null}
            <small>{source.content_preview}</small>
          </article>
        ))
      )}
    </aside>
  );
}

function getKnowledgeBase(source: Source | ModuleSource): string {
  if ("knowledge_base" in source) {
    return source.knowledge_base;
  }
  return "rules";
}
