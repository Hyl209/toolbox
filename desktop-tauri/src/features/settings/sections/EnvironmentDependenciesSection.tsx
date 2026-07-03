import { useEffect, useState } from "react";
import { runTool, type ToolResult } from "../../../api/tauri";
import { DEPENDENCY_DEFINITIONS } from "../dependencies";

type DependencyRow = {
  id: string;
  label: string;
  available: boolean | null;
  detail: string;
  relatedTools: readonly string[];
};

function statusText(available: boolean | null): string {
  if (available === null) {
    return "检测中";
  }
  return available ? "可用" : "缺失";
}

function statusTone(available: boolean | null): "checking" | "available" | "missing" {
  if (available === null) {
    return "checking";
  }
  return available ? "available" : "missing";
}

function initialRows(): DependencyRow[] {
  return DEPENDENCY_DEFINITIONS.map((definition) => ({
    id: definition.id,
    label: definition.label,
    available: null,
    detail: "正在检测…",
    relatedTools: definition.relatedTools,
  }));
}

function errorText(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return typeof error === "string" ? error : JSON.stringify(error);
}

function resultData(result: ToolResult): ToolResult {
  return (result.data ?? result) as ToolResult;
}

export default function EnvironmentDependenciesSection() {
  const [rows, setRows] = useState<DependencyRow[]>(() => initialRows());

  useEffect(() => {
    let cancelled = false;

    Promise.all(
      DEPENDENCY_DEFINITIONS.map(async (definition) => {
        try {
          const result = await runTool(definition.toolId, {
            task_id: `${definition.toolId}-${definition.probeAction}-${Date.now()}`,
            action: definition.probeAction,
            payload: {},
          });
          const status = definition.readProbe(resultData(result));
          return {
            id: definition.id,
            label: definition.label,
            available: status.available,
            detail: status.detail,
            relatedTools: definition.relatedTools,
          } satisfies DependencyRow;
        } catch (caught) {
          return {
            id: definition.id,
            label: definition.label,
            available: false,
            detail: errorText(caught),
            relatedTools: definition.relatedTools,
          } satisfies DependencyRow;
        }
      }),
    ).then((nextRows) => {
      if (!cancelled) {
        setRows(nextRows);
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="settings-card settings-wide-card">
      <span>环境依赖</span>
      <p>所有外部运行时和后端依赖统一在这里检测，工具页不再重复显示。</p>

      <div className="settings-group-card">
        <header className="settings-subsection-head">
          <strong>依赖状态</strong>
          <p>集中查看依赖是否可用、当前路径或返回消息，以及关联工具。</p>
        </header>

        <div className="settings-dependency-grid">
          {rows.map((row) => (
            <article className="settings-field-card dependency-card" key={row.id}>
              <div className="dependency-card-head">
                <strong>{row.label}</strong>
                <span className="dependency-status-pill" data-status={statusTone(row.available)}>
                  {statusText(row.available)}
                </span>
              </div>
              <p className="dependency-detail">{row.detail}</p>
              <div className="dependency-tool-list">
                {row.relatedTools.map((tool) => (
                  <span className="dependency-tool-chip" key={`${row.id}-${tool}`}>
                    {tool}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
