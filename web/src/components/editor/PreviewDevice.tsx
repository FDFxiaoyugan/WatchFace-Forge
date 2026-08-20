/**
 * PreviewDevice — 设备预览
 * 圆形 (Galaxy Watch) / 方形 (Pixel Watch) 外观 + 时间模拟器
 * 复用 FabricCanvas readOnly 模式
 */

"use client";

import { useMemo, useState, useEffect } from "react";
import { useEditorStore } from "@/stores/editorStore";
import FabricCanvas, { defaultTimeText } from "./FabricCanvas";
import { WatchFaceCDM, CANVAS_SIZE } from "@/lib/cdm/types";

type Shape = "round" | "square";

export default function PreviewDevice() {
  const cdm = useEditorStore((s) => s.cdm);
  const previewMs = useEditorStore((s) => s.previewMs);
  const setPreviewMs = useEditorStore((s) => s.setPreviewMs);
  const [shape, setShape] = useState<Shape>("round");
  const [simulating, setSimulating] = useState(false);

  // 时间模拟器: 每秒推进
  useEffect(() => {
    if (!simulating) return;
    const t = setInterval(() => {
      setPreviewMs((previewMs + 1000) % 86400_000);
    }, 1000);
    return () => clearInterval(t);
  }, [simulating, previewMs, setPreviewMs]);

  // 由 previewMs 生成模拟时间文本
  const timeText = useMemo(() => {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    d.setMilliseconds(previewMs);
    const h24 = d.getHours();
    const h12 = h24 % 12 === 0 ? 12 : h24 % 12;
    const mm = String(d.getMinutes()).padStart(2, "0");
    const ss = String(d.getSeconds()).padStart(2, "0");

    let time = `${String(h24).padStart(2, "0")}:${mm}`;
    if (cdm.digital_time.format === "hh:mm") time = `${String(h12).padStart(2, "0")}:${mm}`;
    if (cdm.digital_time.format === "HH:mm:ss") time += `:${ss}`;

    const dateParts = cdm.date_display.params.map((p) => {
      switch (p) {
        case "MONTH": return String(d.getMonth() + 1);
        case "MONTH_S": return ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"][d.getMonth()];
        case "DAY": return String(d.getDate());
        case "DAY_Z": return String(d.getDate()).padStart(2, "0");
        case "DAY_OF_WEEK_S": return ["SUN","MON","TUE","WED","THU","FRI","SAT"][d.getDay()];
        case "YEAR": return String(d.getFullYear());
        default: return "?";
      }
    });
    let date = cdm.date_display.format;
    dateParts.forEach((v) => (date = date.replace("%s", v)));

    const info = `${cdm.info_line.label} 85${cdm.info_line.suffix === "%%" ? "%" : cdm.info_line.suffix}`;
    return { time, date, info };
  }, [previewMs, cdm]);

  const hhmm = `${String(Math.floor(previewMs / 3600_000)).padStart(2, "0")}:${String(
    Math.floor((previewMs % 3600_000) / 60_000)
  ).padStart(2, "0")}`;

  return (
    <div className="flex flex-col items-center gap-3 p-4">
      {/* 形状切换 */}
      <div className="flex gap-1 bg-zinc-800 rounded-lg p-1">
        <button
          className={`px-3 py-1 rounded text-xs transition-colors ${
            shape === "round" ? "bg-sky-600 text-white" : "text-zinc-400 hover:text-zinc-200"
          }`}
          onClick={() => setShape("round")}
        >
          ● 圆形
        </button>
        <button
          className={`px-3 py-1 rounded text-xs transition-colors ${
            shape === "square" ? "bg-sky-600 text-white" : "text-zinc-400 hover:text-zinc-200"
          }`}
          onClick={() => setShape("square")}
        >
          ■ 方形
        </button>
      </div>

      {/* 设备外观 */}
      <div
        className="relative bg-zinc-900 shadow-2xl"
        style={{
          width: CANVAS_SIZE + 24,
          height: CANVAS_SIZE + 24,
          borderRadius: shape === "round" ? "50%" : 28,
          padding: 12,
          border: "4px solid #3f3f46",
        }}
      >
        <div
          className="overflow-hidden"
          style={{
            width: CANVAS_SIZE,
            height: CANVAS_SIZE,
            borderRadius: shape === "round" ? "50%" : 20,
          }}
        >
          <FabricCanvas cdm={cdm} readOnly timeText={timeText} />
        </div>
        {/* 表冠装饰 */}
        <div
          className="absolute bg-zinc-600 rounded-full"
          style={{ width: 10, height: 28, right: -7, top: "40%" }}
        />
      </div>

      {/* 时间模拟器 */}
      <div className="w-full max-w-xs space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500 font-mono w-12">{hhmm}</span>
          <input
            type="range"
            min={0}
            max={86399_000}
            step={60_000}
            value={previewMs}
            onChange={(e) => setPreviewMs(Number(e.target.value))}
            className="flex-1 accent-sky-500"
          />
          <button
            className={`text-xs px-2 py-1 rounded ${
              simulating ? "bg-sky-600 text-white" : "bg-zinc-800 text-zinc-300"
            }`}
            onClick={() => setSimulating(!simulating)}
          >
            {simulating ? "⏸" : "▶"}
          </button>
        </div>
        <div className="flex gap-1 justify-center">
          {[0, 6, 10, 12, 18, 22].map((h) => (
            <button
              key={h}
              className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 hover:text-sky-300"
              onClick={() => setPreviewMs(h * 3600_000)}
            >
              {String(h).padStart(2, "0")}:00
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
