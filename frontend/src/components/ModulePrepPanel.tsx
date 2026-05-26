import { useEffect, useState, type ReactNode } from "react";

import type {
  ModulePrepClueItem,
  ModulePrepFullSection,
  ModulePrepMapResponse,
  ModulePrepNpcItem,
  ModulePrepStructuredData,
  ModulePrepSummaryResponse,
  ModulePrepTimelineItem,
  ModuleTimelineResponse,
  ModulePrepWorkflowStep
} from "../api/modules";

type Props = {
  summary: ModulePrepSummaryResponse | null;
  timeline: ModuleTimelineResponse | null;
  prepMap: ModulePrepMapResponse | null;
  isLoading: boolean;
  aiBrief: string | null;
  aiBriefMeta: string | null;
  aiBriefSections: ModulePrepFullSection[];
  structured: ModulePrepStructuredData | null;
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
  structured,
  canGenerateAiBrief,
  onGenerateAiBrief,
  onSaveSections,
  onReviseSection
}: Props) {
  const hasStructured = Boolean(structured && !isStructuredEmpty(structured));

  return (
    <section className="prep-panel">
      <div className="prep-panel__header">
        <div>
          <p className="eyebrow">V1.2 Prep</p>
          <h2>备团助手</h2>
        </div>
        <div className="prep-panel__actions">
          <span>{aiBriefMeta ?? `${timeline?.events.length ?? 0} events`}</span>
          <button disabled={!canGenerateAiBrief || isLoading} onClick={onGenerateAiBrief} type="button">
            打开备团会话
          </button>
        </div>
      </div>

      {isLoading ? <p className="sources__empty">正在整理备团信息...</p> : null}
      {!isLoading && !hasStructured ? (
        <p className="sources__empty">点击“打开备团会话”，AI 会读取全文并返回 JSON 结构化备团数据。</p>
      ) : null}

      {structured && hasStructured ? (
        <>
          <section className="prep-hero-summary">
            <div>
              <p className="eyebrow">Structured Draft</p>
              <h3>{structured.overview || "备团总览"}</h3>
            </div>
            <ul>
              {structured.must_know.slice(0, 5).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>

          <StructuredBlock
            section={findSection(aiBriefSections, "workflow")}
            title="备团结构地图"
            onReviseSection={onReviseSection}
          >
            <WorkflowMap steps={structured.workflow} />
          </StructuredBlock>

          <StructuredBlock
            section={findSection(aiBriefSections, "timeline")}
            title="时间线思维导图"
            onReviseSection={onReviseSection}
          >
            <TimelineMap items={structured.timeline} />
          </StructuredBlock>

          <section className="prep-grid">
            <StructuredBlock
              section={findSection(aiBriefSections, "npcs")}
              title="NPC 卡片"
              onReviseSection={onReviseSection}
            >
              <NpcCards npcs={structured.npcs} />
            </StructuredBlock>

            <StructuredBlock
              section={findSection(aiBriefSections, "clues")}
              title="重要线索卡片"
              onReviseSection={onReviseSection}
            >
              <ClueCards clues={structured.clues} />
            </StructuredBlock>
          </section>

          <section className="prep-grid">
            <StructuredBlock
              section={findSection(aiBriefSections, "locations")}
              title="地点与手牌"
              onReviseSection={onReviseSection}
            >
              <SimpleCards items={structured.locations} label="地点" />
            </StructuredBlock>

            <StructuredBlock
              section={findSection(aiBriefSections, "risks")}
              title="可能卡住的地方"
              onReviseSection={onReviseSection}
            >
              <SimpleCards items={structured.risks} label="风险" />
            </StructuredBlock>
          </section>

          <StructuredBlock
            section={findSection(aiBriefSections, "checklist")}
            title="跑团前检查清单"
            onReviseSection={onReviseSection}
          >
            <Checklist items={structured.checklist} />
          </StructuredBlock>

          <section className="prep-board">
            <div className="prep-board__header">
              <strong>JSON 草稿编辑</strong>
              <small>需要手动改 JSON 时使用，保存后会更新结构化视图</small>
            </div>
            <div className="prep-draft-accordion">
              {aiBriefSections.map((section) => (
                <details key={section.id}>
                  <summary>{section.title}</summary>
                  <SectionEditor
                    isLoading={isLoading}
                    onReviseSection={onReviseSection}
                    onSaveSections={onSaveSections}
                    section={section}
                    sections={aiBriefSections}
                  />
                </details>
              ))}
            </div>
          </section>
        </>
      ) : null}

      {!hasStructured && prepMap?.warnings.length ? (
        <div className="prep-block">
          <strong>地图提醒</strong>
          {prepMap.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      ) : null}

      {!hasStructured && summary?.warnings.length ? (
        <div className="prep-block">
          <strong>提醒</strong>
          {summary.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function StructuredBlock({
  title,
  section,
  children,
  onReviseSection
}: {
  title: string;
  section: ModulePrepFullSection | null;
  children: ReactNode;
  onReviseSection: (sectionId: string, instruction: string) => void;
}) {
  const [instruction, setInstruction] = useState("");

  function handleRevise() {
    if (!section || !instruction.trim()) {
      return;
    }
    onReviseSection(section.id, instruction.trim());
    setInstruction("");
  }

  return (
    <section className="prep-structured">
      <div className="prep-structured__header">
        <strong>{title}</strong>
        {section ? <small>{section.id}</small> : null}
      </div>
      {children}
      {section ? (
        <div className="structured-controls">
          <input
            onChange={(event) => setInstruction(event.target.value)}
            placeholder={`告诉 AI 怎么重整「${title}」`}
            value={instruction}
          />
          <button disabled={!instruction.trim()} onClick={handleRevise} type="button">
            AI 重整
          </button>
        </div>
      ) : null}
    </section>
  );
}

function WorkflowMap({ steps }: { steps: ModulePrepWorkflowStep[] }) {
  return (
    <div className="workflow-map">
      {steps.map((step, index) => (
        <article className="workflow-card" key={step.id || `${step.title}-${index}`}>
          <span>{(index + 1).toString().padStart(2, "0")}</span>
          <strong>{step.title}</strong>
          <p>{step.goal}</p>
          {step.next_steps.length ? <small>{step.next_steps.join(" -> ")}</small> : null}
        </article>
      ))}
    </div>
  );
}

function TimelineMap({ items }: { items: ModulePrepTimelineItem[] }) {
  return (
    <div className="timeline-map">
      <div className="timeline-map__root">时间线</div>
      <div className="timeline-map__lanes">
        {items.map((item, index) => (
          <article className="timeline-node" key={item.id || `${item.title}-${index}`}>
            <span>{item.date || `${index + 1}`}</span>
            <strong>{item.title}</strong>
            <p>{item.summary}</p>
            {item.source ? <small>{item.source}</small> : null}
          </article>
        ))}
      </div>
    </div>
  );
}

function NpcCards({ npcs }: { npcs: ModulePrepNpcItem[] }) {
  return (
    <div className="structured-card-grid">
      {npcs.map((npc) => (
        <article className="structured-card structured-card--npc" key={npc.id || npc.name}>
          <span>NPC</span>
          <strong>{npc.name}</strong>
          {npc.role ? <small>{npc.role}</small> : null}
          {npc.location ? <p>地点：{npc.location}</p> : null}
          {npc.motivation ? <p>动机：{npc.motivation}</p> : null}
          {npc.notes ? <p>{npc.notes}</p> : null}
        </article>
      ))}
    </div>
  );
}

function ClueCards({ clues }: { clues: ModulePrepClueItem[] }) {
  return (
    <div className="structured-card-grid">
      {clues.map((clue) => (
        <article className="structured-card structured-card--clue" key={clue.id || clue.title}>
          <span>线索</span>
          <strong>{clue.title}</strong>
          {clue.location ? <p>地点：{clue.location}</p> : null}
          {clue.reveal_condition ? <p>获得：{clue.reveal_condition}</p> : null}
          {clue.points_to ? <p>指向：{clue.points_to}</p> : null}
          {clue.notes ? <small>{clue.notes}</small> : null}
        </article>
      ))}
    </div>
  );
}

function SimpleCards({ items, label }: { items: string[]; label: string }) {
  return (
    <div className="structured-card-grid">
      {items.map((item) => (
        <article className="structured-card" key={item}>
          <span>{label}</span>
          <p>{item}</p>
        </article>
      ))}
    </div>
  );
}

function Checklist({ items }: { items: string[] }) {
  return (
    <div className="checklist-grid">
      {items.map((item) => (
        <label key={item}>
          <input type="checkbox" />
          <span>{item}</span>
        </label>
      ))}
    </div>
  );
}

function SectionEditor({
  section,
  sections,
  isLoading,
  onSaveSections,
  onReviseSection
}: {
  section: ModulePrepFullSection;
  sections: ModulePrepFullSection[];
  isLoading: boolean;
  onSaveSections: (sections: ModulePrepFullSection[]) => void;
  onReviseSection: (sectionId: string, instruction: string) => void;
}) {
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
    if (!instruction.trim()) {
      return;
    }
    onReviseSection(section.id, instruction.trim());
    setInstruction("");
  }

  return (
    <article className="prep-section">
      <textarea
        aria-label={`${section.title} JSON 内容`}
        onChange={(event) => setDraftContent(event.target.value)}
        value={draftContent}
      />
      <div className="prep-section__revise">
        <button disabled={isLoading || draftContent === section.content} onClick={handleSave} type="button">
          保存
        </button>
        <input
          onChange={(event) => setInstruction(event.target.value)}
          placeholder="告诉 AI 这一段 JSON 怎么改"
          value={instruction}
        />
        <button disabled={isLoading || !instruction.trim()} onClick={handleRevise} type="button">
          AI 修改
        </button>
      </div>
    </article>
  );
}

function findSection(sections: ModulePrepFullSection[], id: string): ModulePrepFullSection | null {
  return sections.find((section) => section.id === id) ?? null;
}

function isStructuredEmpty(structured: ModulePrepStructuredData): boolean {
  return !(
    structured.overview ||
    structured.must_know.length ||
    structured.timeline.length ||
    structured.workflow.length ||
    structured.npcs.length ||
    structured.clues.length ||
    structured.locations.length ||
    structured.risks.length ||
    structured.checklist.length
  );
}
