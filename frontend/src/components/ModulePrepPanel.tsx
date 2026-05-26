import type { ModulePrepMapResponse, ModulePrepSummaryResponse, ModuleTimelineResponse } from "../api/modules";
import { ModulePrepMap } from "./ModulePrepMap";

type Props = {
  summary: ModulePrepSummaryResponse | null;
  timeline: ModuleTimelineResponse | null;
  prepMap: ModulePrepMapResponse | null;
  isLoading: boolean;
  aiBrief: string | null;
  aiBriefMeta: string | null;
  canGenerateAiBrief: boolean;
  onGenerateAiBrief: () => void;
};

export function ModulePrepPanel({
  summary,
  timeline,
  prepMap,
  isLoading,
  aiBrief,
  aiBriefMeta,
  canGenerateAiBrief,
  onGenerateAiBrief
}: Props) {
  return (
    <section className="prep-panel">
      <div className="prep-panel__header">
        <div>
          <p className="eyebrow">V1.2 Prep</p>
          <h2>备团助手</h2>
        </div>
        <div className="prep-panel__actions">
          <span>{timeline?.events.length ?? 0} events</span>
          <button disabled={!canGenerateAiBrief || isLoading} onClick={onGenerateAiBrief} type="button">
            AI 全文备团
          </button>
        </div>
      </div>
      {isLoading ? <p className="sources__empty">正在整理备团信息...</p> : null}
      {!isLoading && !summary && !timeline ? (
        <p className="sources__empty">还没有备团信息，先上传并建立索引。</p>
      ) : null}

      {prepMap?.warnings.length ? (
        <div className="prep-block">
          <strong>地图提醒</strong>
          {prepMap.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      ) : null}

      <div className="prep-block prep-block--map">
        <strong>备团结构地图</strong>
        <ModulePrepMap prepMap={prepMap} />
      </div>

      {aiBrief ? (
        <div className="prep-block prep-block--ai">
          <strong>AI 备团提纲</strong>
          {aiBriefMeta ? <small>{aiBriefMeta}</small> : null}
          <p>{aiBrief}</p>
        </div>
      ) : null}

      {summary?.warnings.length ? (
        <div className="prep-block">
          <strong>提醒</strong>
          {summary.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      ) : null}

      {summary ? (
        <div className="prep-block">
          <strong>关键线索</strong>
          {summary.clues.slice(0, 4).map((item) => (
            <article className="prep-item" key={`${item.source}-${item.title}`}>
              <span>{item.title}</span>
              <small>{item.source}</small>
              <p>{item.preview}</p>
            </article>
          ))}
        </div>
      ) : null}

      {summary ? (
        <div className="prep-block">
          <strong>NPC 摘要</strong>
          {summary.npcs.slice(0, 4).map((item) => (
            <article className="prep-item" key={`${item.source}-${item.title}`}>
              <span>{item.title}</span>
              <small>{item.source}</small>
              <p>{item.preview}</p>
            </article>
          ))}
        </div>
      ) : null}

      {timeline ? (
        <div className="prep-block">
          <strong>时间线</strong>
          {timeline.events.map((event) => (
            <article className="timeline-item" key={`${event.order}-${event.source}`}>
              <div className="timeline-item__meta">
                <span>{event.order}. {event.title}</span>
                <small>{event.content_type}</small>
              </div>
              <p>{event.location ? `地点：${event.location} ` : ""}{event.preview}</p>
            </article>
          ))}
        </div>
      ) : null}
    </section>
  );
}
