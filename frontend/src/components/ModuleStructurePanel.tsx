import type { ModuleStructureResponse } from "../api/modules";

type Props = {
  structure: ModuleStructureResponse | null;
  isLoading: boolean;
};

export function ModuleStructurePanel({ structure, isLoading }: Props) {
  const totalGroups = structure?.groups.length ?? 0;
  return (
    <section className="structure-panel">
      <div className="structure-panel__header">
        <div>
          <p className="eyebrow">V1.1 Structure</p>
          <h2>模组结构视图</h2>
        </div>
        <span>{countItems(structure)} / {totalGroups}</span>
      </div>
      {isLoading ? <p className="sources__empty">正在读取结构...</p> : null}
      {!isLoading && (!structure || structure.groups.length === 0) ? (
        <p className="sources__empty">还没有结构信息。先上传模组资料。</p>
      ) : null}
      {structure?.groups.map((group) => (
        <div className="structure-group" key={group.content_type}>
          <div className="structure-group__title">
            <strong>{group.label}</strong>
            <span>{group.items.length}</span>
          </div>
          {group.items.map((item) => (
            <article className="structure-item" key={`${group.content_type}-${item.source}-${item.label}`}>
              <div>
                <strong>{item.label}</strong>
                <span>{item.source}</span>
              </div>
              <p>{item.preview || "无预览内容"}</p>
            </article>
          ))}
        </div>
      ))}
    </section>
  );
}

function countItems(structure: ModuleStructureResponse | null): number {
  if (!structure) {
    return 0;
  }
  return structure.groups.reduce((total, group) => total + group.items.length, 0);
}
