/**
 * LayerPanel — 图层面板
 * 列出所有可编辑图层, 支持选中/显隐切换
 */

"use client";

import { ElementKey, useEditorStore } from "@/stores/editorStore";

const LAYER_DEFS = [
  { key: "background", label: "背景", icon: "🖼️" },
  { key: "digital_time", label: "数字时间", icon: "⏰" },
  { key: "analog_time", label: "模拟表针", icon: "🕐" },
  { key: "date_display", label: "日期", icon: "📅" },
  { key: "info_line", label: "信息行", icon: "📊" },
] as const;

export default function LayerPanel() {
  const cdm = useEditorStore((s) => s.cdm);
  const selection = useEditorStore((s) => s.selection);
  const select = useEditorStore((s) => s.select);
  const updateCDM = useEditorStore((s) => s.updateCDM);
  const addComplication = useEditorStore((s) => s.addComplication);
  const removeComplication = useEditorStore((s) => s.removeComplication);

  const isSel = (key: string) =>
    selection?.kind === "element" && selection.key === key;

  const isEnabled = (key: string): boolean => {
    switch (key) {
      case "background": return true;
      case "digital_time": return cdm.clock_type === "DIGITAL" && cdm.digital_time.enabled;
      case "analog_time": return cdm.clock_type === "ANALOG" && cdm.analog_time.enabled;
      case "date_display": return cdm.date_display.enabled;
      case "info_line": return cdm.info_line.enabled;
      default: return false;
    }
  };

  const toggleEnabled = (key: string) => {
    updateCDM((draft) => {
      switch (key) {
        case "digital_time":
          draft.digital_time.enabled = !draft.digital_time.enabled;
          break;
        case "analog_time":
          draft.analog_time.enabled = !draft.analog_time.enabled;
          break;
        case "date_display":
          draft.date_display.enabled = !draft.date_display.enabled;
          break;
        case "info_line":
          draft.info_line.enabled = !draft.info_line.enabled;
          break;
      }
      return draft;
    });
  };

  const removeLayer = (key: ElementKey) => {
    updateCDM((draft) => {
      if (key === "digital_time") draft.digital_time.enabled = false;
      if (key === "analog_time") draft.analog_time.enabled = false;
      if (key === "date_display") draft.date_display.enabled = false;
      if (key === "info_line") draft.info_line.enabled = false;
      return draft;
    });
    select({ kind: "element", key: "background" });
  };

  const addLayer = (key: Exclude<ElementKey, "background" | "complications">) => {
    updateCDM((draft) => {
      if (key === "digital_time") {
        draft.clock_type = "DIGITAL";
        draft.digital_time.enabled = true;
      }
      if (key === "analog_time") {
        draft.clock_type = "ANALOG";
        draft.analog_time.enabled = true;
      }
      if (key === "date_display") draft.date_display.enabled = true;
      if (key === "info_line") draft.info_line.enabled = true;
      return draft;
    });
    select({ kind: "element", key });
  };

  const visibleLayers = LAYER_DEFS.filter(({ key }) => key === "background" || isEnabled(key));
  const addableLayers = LAYER_DEFS.filter(({ key }) => key !== "background" && !isEnabled(key));

  return (
    <div className="flex flex-col h-full">
      <div className="px-3 py-2 text-xs font-semibold text-zinc-400 border-b border-zinc-800">
        图层
      </div>
      <div className="flex-1 overflow-y-auto">
        {visibleLayers.map(({ key, label, icon }) => {
          return (
            <div
              key={key}
              className={`flex items-center gap-2 px-3 py-2 text-sm cursor-pointer transition-colors
                ${isSel(key) ? "bg-sky-600/20 text-sky-300" : "text-zinc-300 hover:bg-zinc-800/50"}
                `}
              onClick={() => select({ kind: "element", key: key as ElementKey })}
            >
              <span>{icon}</span>
              <span className="flex-1">{label}</span>
              {key !== "background" && (
                <button
                  className="text-xs opacity-70 hover:opacity-100"
                  onClick={(e) => { e.stopPropagation(); toggleEnabled(key); }}
                  title="隐藏"
                >
                  👁️
                </button>
              )}
              {key !== "background" && (
                <button
                  className="text-xs text-red-400 hover:text-red-300"
                  onClick={(e) => { e.stopPropagation(); removeLayer(key as ElementKey); }}
                  title="删除图层"
                >
                  ✕
                </button>
              )}
            </div>
          );
        })}

        {addableLayers.length > 0 && (
          <div className="mt-2 border-t border-zinc-800 pt-1">
            <div className="px-3 py-1 text-[11px] text-zinc-500">添加图层</div>
            {addableLayers.map(({ key, label, icon }) => (
              <button
                key={key}
                className="w-full px-3 py-2 text-sm text-zinc-400 hover:text-sky-300 hover:bg-zinc-800/50 text-left"
                onClick={() => addLayer(key as Exclude<ElementKey, "background" | "complications">)}
              >
                ＋ {icon} {label}
              </button>
            ))}
          </div>
        )}

        {/* 复杂功能槽位 */}
        <div className="px-3 py-1 text-[11px] text-zinc-500 mt-2">
          复杂功能 ({cdm.complications.length}/4)
        </div>
        {cdm.complications.map((comp, i) => (
          <div
            key={i}
            className={`flex items-center gap-2 px-3 py-2 text-sm cursor-pointer transition-colors
              ${selection?.kind === "complication" && selection.index === i
                ? "bg-sky-600/20 text-sky-300"
                : "text-zinc-300 hover:bg-zinc-800/50"}`}
            onClick={() => select({ kind: "complication", index: i })}
          >
            <span>🎯</span>
            <span className="flex-1">Slot {i + 1}</span>
            <button
              className="text-xs text-red-400 hover:text-red-300"
              onClick={(e) => {
                e.stopPropagation();
                removeComplication(i);
              }}
              title="删除"
            >
              ✕
            </button>
          </div>
        ))}
        {cdm.complications.length < 4 && (
          <button
            className="w-full px-3 py-2 text-sm text-zinc-400 hover:text-sky-300 hover:bg-zinc-800/50 text-left"
            onClick={addComplication}
          >
            ＋ 添加槽位
          </button>
        )}
      </div>
    </div>
  );
}
