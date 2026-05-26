import { useEffect, useState } from "react";

import type {
  ModulePrepFullSection,
  ModulePrepMapResponse,
  ModulePrepSummaryResponse,
  ModuleTimelineResponse
} from "../api/modules";
import { ModulePrepMap } from "./ModulePrepMap";

type Props = {
  summary: ModulePrepSummaryResponse | null;
  timeline: ModuleTimelineResponse | null;
  prepMap: ModulePrepMapResponse | null;
  isLoading: boolean;
  aiBrief: string | null;
  aiBriefMeta: string | null;
  aiBriefSections: ModulePrepFullSection[];
  canGenerateAiBrief: boolean;
  onGenerateAiBrief: () => void;
  onSaveSections: (sections: ModulePrepFullSection[]) => void;
  onReviseSection: (sectionId: string, instruction: string) => void;
};

export function ModulePrepPanel({
  summary,
  timeline,
  prepMap,
  isLoading,
  aiBrief,
  aiBriefMeta,
  aiBriefSections,
  canGenerateAiBrief,
  onGenerateAiBrief,
  onSaveSections,
  onReviseSection
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
          {aiBriefSections.length > 0 ? (
            <div className="prep-sections">
              {aiBriefSections.map((section) => (
                <PrepSectionEditor
                  isLoading={isLoading}
                  key={section.id}
                  onReviseSection={onReviseSection}
                  onSaveSections={onSaveSections}
                  section={section}
                  sections={aiBriefSections}
                />
              ))}
            </div>
          ) : (
            <p>{aiBrief}</p>
          )}
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

type SectionEditorProps = {
  section: ModulePrepFullSection;
  sections: ModulePrepFullSection[];
  isLoading: boolean;
  onSaveSections: (sections: ModulePrepFullSection[]) => void;
  onReviseSection: (sectionId: string, instruction: string) => void;
};

function PrepSectionEditor({
  section,
  sections,
  isLoading,
  onSaveSections,
  onReviseSection
}: SectionEditorProps) {
  const [draftContent, setDraftContent] = useState(section.content);
  const [instruction, setInstruction] = useState("");

  useEffect(() => {
    setDraftContent(section.content);
  }, [section.content]);

  function handleSave() {
    onSaveSections(
      sections.map((item) => (item.id === section.id ? { ...item, content: draftContent } : item))
    );
  }

  function handleRevise() {
    const trimmed = instruction.trim();
    if (!trimmed) {
      return;
    }
    onReviseSection(section.id, trimmed);
    setInstruction("");
  }

  return (
    <article className="prep-section">
      <div className="prep-section__header">
        <h3>{section.title}</h3>
        <button disabled={isLoading || draftContent === section.content} onClick={handleSave} type="button">
          保存
        </button>
      </div>
      <textarea
        aria-label={`${section.title} 章节内容`}
        onChange={(event) => setDraftContent(event.target.value)}
        value={draftContent}
      />
      <div className="prep-section__revise">
        <input
          onChange={(event) => setInstruction(event.target.value)}
          placeholder="告诉 AI 这一节怎么改"
          value={instruction}
        />
        <button disabled={isLoading || !instruction.trim()} onClick={handleRevise} type="button">
          AI 修改
        </button>
      </div>
    </article>
  );
}
