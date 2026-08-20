/**
 * DataBindingPanel — 数据绑定面板
 * 为日期/信息行配置数据源 (时间/电量/心率等)
 */

"use client";

import { useEditorStore } from "@/stores/editorStore";
import { DataSource, DATA_SOURCE_META } from "@/lib/cdm/types";

const ALL_SOURCES = Object.keys(DATA_SOURCE_META) as DataSource[];

export default function DataBindingPanel() {
  const cdm = useEditorStore((s) => s.cdm);
  const selection = useEditorStore((s) => s.selection);
  const updateCDM = useEditorStore((s) => s.updateCDM);

  const isDate = selection?.kind === "element" && selection.key === "date_display";
  const isInfo = selection?.kind === "element" && selection.key === "info_line";

  if (!isDate && !isInfo) {
    return (
      <div className="p-4 text-sm text-zinc-500">
        选择「日期」或「信息行」图层后配置数据绑定
      </div>
    );
  }

  // 日期: 多选数据源 (%s 模板参数)
  if (isDate) {
    const params = cdm.date_display.params;
    return (
      <div className="p-3 space-y-3">
        <div className="text-[11px] font-semibold text-zinc-500 uppercase">
          日期模板参数 (按顺序替换 %s)
        </div>
        {/* 已选参数 (可排序展示) */}
        <div className="flex flex-wrap gap-1">
          {params.map((p, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 bg-sky-600/20 text-sky-300 rounded px-2 py-0.5 text-xs"
            >
              {DATA_SOURCE_META[p]?.label ?? p}
              <button
                className="opacity-60 hover:opacity-100"
                onClick={() =>
                  updateCDM((d) => {
                    d.date_display.params.splice(i, 1);
                    return d;
                  })
                }
              >
                ✕
              </button>
            </span>
          ))}
        </div>
        {/* 可添加的源 */}
        <div className="text-[11px] text-zinc-600">添加数据源:</div>
        <div className="flex flex-wrap gap-1">
          {ALL_SOURCES.filter((s) => !params.includes(s)).map((s) => (
            <button
              key={s}
              className="bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded px-2 py-0.5 text-xs"
              onClick={() =>
                updateCDM((d) => {
                  d.date_display.params.push(s);
                  return d;
                })
              }
            >
              ＋ {DATA_SOURCE_META[s].label}
            </button>
          ))}
        </div>
        {/* 模板预览 */}
        <div className="border-t border-zinc-800 pt-2 text-xs text-zinc-500">
          <div>模板: <span className="font-mono text-zinc-300">{cdm.date_display.format}</span></div>
          <div className="mt-1">
            预览:{" "}
            <span className="font-mono text-sky-300">
              {previewDate(cdm.date_display.format, params)}
            </span>
          </div>
        </div>
      </div>
    );
  }

  // 信息行: 单选数据源
  const current = cdm.info_line.data_source;
  return (
    <div className="p-3 space-y-2">
      <div className="text-[11px] font-semibold text-zinc-500 uppercase">信息行数据源</div>
      {ALL_SOURCES.map((s) => (
        <button
          key={s}
          className={`w-full flex items-center justify-between rounded px-2 py-1.5 text-xs transition-colors
            ${current === s
              ? "bg-sky-600/20 text-sky-300 border border-sky-600/40"
              : "bg-zinc-800/50 text-zinc-300 hover:bg-zinc-800 border border-transparent"}`}
          onClick={() =>
            updateCDM((d) => {
              d.info_line.data_source = s;
              return d;
            })
          }
        >
          <span>{DATA_SOURCE_META[s].label}</span>
          <span className="font-mono text-zinc-500">{DATA_SOURCE_META[s].sample}</span>
        </button>
      ))}
    </div>
  );
}

function previewDate(format: string, params: DataSource[]): string {
  const now = new Date();
  let out = format;
  params.forEach((p) => {
    let v = "?";
    switch (p) {
      case "MONTH": v = String(now.getMonth() + 1); break;
      case "MONTH_S": v = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"][now.getMonth()]; break;
      case "DAY": v = String(now.getDate()); break;
      case "DAY_Z": v = String(now.getDate()).padStart(2, "0"); break;
      case "DAY_OF_WEEK_S": v = ["SUN","MON","TUE","WED","THU","FRI","SAT"][now.getDay()]; break;
      case "YEAR": v = String(now.getFullYear()); break;
      default: v = DATA_SOURCE_META[p]?.sample ?? "?";
    }
    out = out.replace("%s", v);
  });
  return out;
}
