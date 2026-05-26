import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";

import {
  askModule,
  createModule,
  deleteModule,
  generateModuleFullPrep,
  getModulePrepMap,
  getModulePrepSummary,
  getModuleStructure,
  getModuleTimeline,
  ingestModule,
  listModules,
  type ModuleSource,
  type ModulePrepMapResponse,
  type ModulePrepSummaryResponse,
  type ModuleStructureResponse,
  type ModuleTimelineResponse,
  type ModuleSummary,
  uploadModuleDocument
} from "../api/modules";
import { API_BASE_URL } from "../api/rules";
import { ModulePrepPanel } from "./ModulePrepPanel";
import { ModuleStructurePanel } from "./ModuleStructurePanel";
import { SourceList } from "./SourceList";

type Message = {
  role: "user" | "assistant";
  content: string;
};

const MESSAGE_STORAGE_PREFIX = "keeperkit.module.messages.";

type WorkbenchTab = "ask" | "prep" | "structure" | "sources";

const TABS: Array<{ id: WorkbenchTab; label: string; hint: string }> = [
  { id: "ask", label: "模组问答", hint: "AI 检索与回答" },
  { id: "prep", label: "备团助手", hint: "时间线 / NPC / 线索" },
  { id: "structure", label: "结构视图", hint: "文件与内容索引" },
  { id: "sources", label: "来源依据", hint: "本轮问答引用" }
];

export function ModuleWorkbench() {
  const [modules, setModules] = useState<ModuleSummary[]>([]);
  const [selectedModuleId, setSelectedModuleId] = useState("");
  const [activeTab, setActiveTab] = useState<WorkbenchTab>("ask");
  const [newModuleId, setNewModuleId] = useState("demo_module");
  const [newModuleTitle, setNewModuleTitle] = useState("演示模组");
  const [question, setQuestion] = useState("这个模组的开场场景是什么？");
  const [messages, setMessages] = useState<Message[]>([]);
  const [sources, setSources] = useState<ModuleSource[]>([]);
  const [structure, setStructure] = useState<ModuleStructureResponse | null>(null);
  const [timeline, setTimeline] = useState<ModuleTimelineResponse | null>(null);
  const [prepSummary, setPrepSummary] = useState<ModulePrepSummaryResponse | null>(null);
  const [prepMap, setPrepMap] = useState<ModulePrepMapResponse | null>(null);
  const [prepAiBrief, setPrepAiBrief] = useState<string | null>(null);
  const [prepAiBriefMeta, setPrepAiBriefMeta] = useState<string | null>(null);
  const [status, setStatus] = useState("Ready");
  const [error, setError] = useState<string | null>(null);
  const [structureCount, setStructureCount] = useState(0);
  const isBusy = status !== "Ready";

  const selectedModule = useMemo(
    () => modules.find((item) => item.id === selectedModuleId) ?? null,
    [modules, selectedModuleId]
  );

  useEffect(() => {
    void refreshModules();
  }, []);

  useEffect(() => {
    if (!selectedModuleId) {
      setStructure(null);
      setTimeline(null);
      setPrepSummary(null);
      setPrepMap(null);
      setPrepAiBrief(null);
      setPrepAiBriefMeta(null);
      setMessages([]);
      setSources([]);
      return;
    }
    setMessages(loadMessages(selectedModuleId));
    setSources([]);
    setPrepAiBrief(null);
    setPrepAiBriefMeta(null);
    void refreshStructure(selectedModuleId);
    void refreshPrepArtifacts(selectedModuleId);
  }, [selectedModuleId]);

  useEffect(() => {
    if (!selectedModuleId) {
      return;
    }
    saveMessages(selectedModuleId, messages);
  }, [messages, selectedModuleId]);

  async function refreshModules(nextSelectedId?: string) {
    const nextModules = await listModules();
    setModules(nextModules);
    if (nextSelectedId) {
      setSelectedModuleId(nextSelectedId);
      return;
    }
    if (!selectedModuleId && nextModules.length > 0) {
      setSelectedModuleId(nextModules[0].id);
    }
  }

  async function refreshStructure(moduleId: string) {
    try {
      const nextStructure = await getModuleStructure(moduleId);
      setStructure(nextStructure);
      setStructureCount(nextStructure.groups.reduce((total, group) => total + group.items.length, 0));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unknown request error");
    }
  }

  async function refreshPrepArtifacts(moduleId: string) {
    try {
      const [nextTimeline, nextPrepSummary, nextPrepMap] = await Promise.all([
        getModuleTimeline(moduleId),
        getModulePrepSummary(moduleId),
        getModulePrepMap(moduleId)
      ]);
      setTimeline(nextTimeline);
      setPrepSummary(nextPrepSummary);
      setPrepMap(nextPrepMap);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unknown request error");
    }
  }

  async function handleCreateModule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const id = newModuleId.trim();
    const title = newModuleTitle.trim();
    if (!id || !title) {
      setError("模组 ID 和名称不能为空。");
      return;
    }

    await runTask("Creating", async () => {
      const module = await createModule({
        id,
        title,
        system: "coc7",
        language: "zh",
        spoiler_level: "keeper_only"
      });
      await refreshModules(module.id);
    });
  }

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || !selectedModuleId) {
      return;
    }

    await runTask("Uploading", async () => {
      await uploadModuleDocument(selectedModuleId, file);
      await refreshModules(selectedModuleId);
      await refreshStructure(selectedModuleId);
      await refreshPrepArtifacts(selectedModuleId);
    });
  }

  async function handleIngest() {
    if (!selectedModuleId) {
      setError("请先选择一个模组。");
      return;
    }

    await runTask("Indexing", async () => {
      await ingestModule(selectedModuleId);
      await refreshModules(selectedModuleId);
      await refreshStructure(selectedModuleId);
      await refreshPrepArtifacts(selectedModuleId);
    });
  }

  async function handleDeleteModule() {
    if (!selectedModuleId) {
      return;
    }

    const confirmed = window.confirm(`确定删除模组「${selectedModule?.title ?? selectedModuleId}」吗？`);
    if (!confirmed) {
      return;
    }

    await runTask("Deleting", async () => {
      await deleteModule(selectedModuleId);
      setMessages([]);
      setSources([]);
      setStructure(null);
      setTimeline(null);
      setPrepSummary(null);
      setPrepMap(null);
      setPrepAiBrief(null);
      setPrepAiBriefMeta(null);
      setStructureCount(0);
      setSelectedModuleId("");
      await refreshModules();
    });
  }

  async function handleAsk(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!selectedModuleId || !trimmed) {
      return;
    }

    await runTask("Consulting", async () => {
      setSources([]);
      setMessages((current) => [...current, { role: "user", content: trimmed }]);
      const response = await askModule(selectedModuleId, {
        question: trimmed,
        top_k: 8,
        rerank_top_k: 3
      });
      setMessages((current) => [...current, { role: "assistant", content: response.answer }]);
      setSources(response.sources);
    });
  }

  async function handleGeneratePrepBrief() {
    if (!selectedModuleId) {
      setError("请先选择一个模组。");
      return;
    }

    await runTask("AI Prep", async () => {
      const response = await generateModuleFullPrep(selectedModuleId);
      setPrepAiBrief(response.answer);
      setPrepAiBriefMeta(`${response.document_count} files / ${response.character_count} chars / full text`);
      setSources(response.sources);
    });
  }

  async function runTask(nextStatus: string, task: () => Promise<void>) {
    setStatus(nextStatus);
    setError(null);
    try {
      await task();
    } catch (taskError) {
      setError(taskError instanceof Error ? taskError.message : "Unknown request error");
    } finally {
      setStatus("Ready");
    }
  }

  return (
    <main className="workbench">
      <aside className="module-nav">
        <div className="module-nav__header">
          <p className="eyebrow">KeeperKit V1.2</p>
          <h1>备团工作台</h1>
          <span className="endpoint">{API_BASE_URL}</span>
        </div>

        <form className="module-form" onSubmit={handleCreateModule}>
          <label>
            <span>模组 ID</span>
            <input value={newModuleId} onChange={(event) => setNewModuleId(event.target.value)} />
          </label>
          <label>
            <span>模组名称</span>
            <input value={newModuleTitle} onChange={(event) => setNewModuleTitle(event.target.value)} />
          </label>
          <button type="submit">创建模组</button>
        </form>

        <div className="module-list">
          {modules.length === 0 ? (
            <p className="sources__empty">还没有模组，先创建一个。</p>
          ) : (
            modules.map((module) => (
              <button
                className={module.id === selectedModuleId ? "module-card module-card--active" : "module-card"}
                key={module.id}
                onClick={() => setSelectedModuleId(module.id)}
                type="button"
              >
                <strong>{module.title}</strong>
                <span>{module.id}</span>
                <small>
                  {module.document_count} files / {module.index_ready ? "indexed" : "not indexed"} / {module.has_documents ? "ready" : "empty"}
                </small>
              </button>
            ))
          )}
        </div>
      </aside>

      <section className="workspace">
        <section className="workspace-hero">
          <div>
            <p className="eyebrow">Module Command Desk</p>
            <h2>{selectedModule?.title ?? "选择一个模组"}</h2>
            {selectedModule ? (
              <p className="module-stats">
                {selectedModule.document_count} files / {selectedModule.index_ready ? "indexed" : "not indexed"} / {structureCount} structure items
              </p>
            ) : (
              <p className="module-stats">先创建或选择模组，再上传 PDF、Markdown 或 TXT 资料。</p>
            )}
          </div>
          <div className="workspace-actions">
            <span className="status">{status}</span>
            <label className="upload-button">
              上传资料
              <input accept=".md,.markdown,.txt,.pdf" disabled={!selectedModuleId} onChange={handleUpload} type="file" />
            </label>
            <button className="ghost-button" disabled={!selectedModuleId} onClick={handleIngest} type="button">
              建立索引
            </button>
            <button className="delete-button" disabled={!selectedModuleId} onClick={handleDeleteModule} type="button">
              删除模组
            </button>
          </div>
        </section>

        <nav className="workspace-tabs" aria-label="模组功能区">
          {TABS.map((tab) => (
            <button
              className={activeTab === tab.id ? "workspace-tab workspace-tab--active" : "workspace-tab"}
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              type="button"
            >
              <span>{tab.label}</span>
              <small>{tab.hint}</small>
            </button>
          ))}
        </nav>

        <section className="tab-surface">
          {activeTab === "ask" ? (
            <section className="console">
              <div className="console__header">
                <div>
                  <p className="eyebrow">Module QA</p>
                  <h2>问当前模组</h2>
                </div>
                <span className="mini-pill">{messages.length} messages</span>
              </div>

              <div className="messages">
                {messages.length === 0 ? (
                  <div className="empty">
                    <p>上传资料并建立索引后，可以直接问开场、线索、NPC 动机或规则相关问题。</p>
                  </div>
                ) : (
                  messages.map((message, index) => (
                    <article className={`message message--${message.role}`} key={`${message.role}-${index}`}>
                      <span>{message.role === "user" ? "You" : "Assistant"}</span>
                      <p>{message.content}</p>
                    </article>
                  ))
                )}
                {error ? <p className="error">{error}</p> : null}
              </div>

              <form className="prompt" onSubmit={handleAsk}>
                <div className="prompt__row">
                  <input
                    disabled={!selectedModuleId}
                    onChange={(event) => setQuestion(event.target.value)}
                    placeholder="围绕当前模组提问"
                    value={question}
                  />
                  <button disabled={!selectedModuleId || isBusy} type="submit">
                    Ask
                  </button>
                </div>
              </form>
            </section>
          ) : null}

          {activeTab === "prep" ? (
            <ModulePrepPanel
              aiBrief={prepAiBrief}
              aiBriefMeta={prepAiBriefMeta}
              canGenerateAiBrief={Boolean(selectedModuleId)}
              isLoading={isBusy}
              onGenerateAiBrief={handleGeneratePrepBrief}
              prepMap={prepMap}
              summary={prepSummary}
              timeline={timeline}
            />
          ) : null}

          {activeTab === "structure" ? (
            <ModuleStructurePanel isLoading={isBusy} structure={structure} />
          ) : null}

          {activeTab === "sources" ? (
            <SourceList isLoading={isBusy} sources={sources} />
          ) : null}
        </section>
      </section>
    </main>
  );
}

function loadMessages(moduleId: string): Message[] {
  try {
    const rawValue = window.localStorage.getItem(`${MESSAGE_STORAGE_PREFIX}${moduleId}`);
    if (!rawValue) {
      return [];
    }
    const parsed = JSON.parse(rawValue);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter(isMessage);
  } catch {
    return [];
  }
}

function saveMessages(moduleId: string, messages: Message[]) {
  window.localStorage.setItem(`${MESSAGE_STORAGE_PREFIX}${moduleId}`, JSON.stringify(messages));
}

function isMessage(value: unknown): value is Message {
  if (!value || typeof value !== "object") {
    return false;
  }
  const candidate = value as Partial<Message>;
  return (candidate.role === "user" || candidate.role === "assistant") && typeof candidate.content === "string";
}
