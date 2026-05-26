import type { ModulePrepMapNode, ModulePrepMapResponse } from "../api/modules";

type Props = {
  prepMap: ModulePrepMapResponse | null;
};

const KIND_LABELS: Record<string, string> = {
  module: "模组",
  scene: "场景",
  timeline: "时间线",
  npc: "NPC",
  clue: "线索",
  location: "地点",
  trigger: "触发",
  document: "资料"
};

const CHILD_KINDS = ["timeline", "scene", "npc", "clue", "location", "trigger"];

export function ModulePrepMap({ prepMap }: Props) {
  if (!prepMap || prepMap.nodes.length === 0) {
    return (
      <div className="prep-map prep-map--empty">
        <p>还没有可视化地图。上传资料后，系统会把场景、NPC、线索和地点整理成结构图。</p>
      </div>
    );
  }

  const root = prepMap.nodes.find((node) => node.kind === "module") ?? prepMap.nodes[0];
  const byKind = groupNodes(prepMap.nodes.filter((node) => node.id !== root.id));

  return (
    <div className="prep-map">
      <section className="prep-map__root">
        <small>{KIND_LABELS[root.kind] ?? root.kind}</small>
        <strong>{root.label}</strong>
        {root.summary ? <p>{root.summary}</p> : null}
      </section>

      <div className="prep-map__branches">
        {CHILD_KINDS.map((kind) => {
          const nodes = byKind.get(kind) ?? [];
          if (nodes.length === 0) {
            return null;
          }
          return (
            <section className={`prep-map__branch prep-map__branch--${kind}`} key={kind}>
              <div className="prep-map__branch-title">
                <span>{KIND_LABELS[kind] ?? kind}</span>
                <small>{nodes.length}</small>
              </div>
              {nodes.slice(0, 8).map((node) => (
                <article className="prep-map__node" key={node.id}>
                  <strong>{node.label}</strong>
                  {node.source ? <small>{node.source}</small> : null}
                  {node.summary ? <p>{node.summary}</p> : null}
                  <EdgeList node={node} prepMap={prepMap} />
                </article>
              ))}
            </section>
          );
        })}
      </div>
    </div>
  );
}

function EdgeList({ node, prepMap }: { node: ModulePrepMapNode; prepMap: ModulePrepMapResponse }) {
  const edges = prepMap.edges.filter((edge) => edge.source_id === node.id || edge.target_id === node.id).slice(0, 4);
  if (edges.length === 0) {
    return null;
  }

  const labels = edges.map((edge) => edge.label);
  return <em>{Array.from(new Set(labels)).join(" / ")}</em>;
}

function groupNodes(nodes: ModulePrepMapNode[]): Map<string, ModulePrepMapNode[]> {
  const results = new Map<string, ModulePrepMapNode[]>();
  for (const node of nodes) {
    const items = results.get(node.kind) ?? [];
    items.push(node);
    results.set(node.kind, items);
  }
  return results;
}
