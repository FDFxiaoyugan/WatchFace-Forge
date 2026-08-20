/**
 * FabricCanvas — Fabric.js v6 画布封装
 *
 * 职责:
 *  - 将 CDM 渲染为可交互对象 (时间文本/日期/信息行/复杂功能槽位/模拟表针)
 *  - 拖拽/缩放 → 回写 CDM position
 *  - 选中状态同步 store
 *  - 450x450 逻辑坐标, 视口自适应缩放
 */

"use client";

import { useEffect, useRef, useCallback } from "react";
import * as fabric from "fabric";
import { useEditorStore, Selection, ElementKey } from "@/stores/editorStore";
import {
  WatchFaceCDM,
  argbToCss,
  CANVAS_SIZE,
} from "@/lib/cdm/types";

// 对象 ↔ CDM 元素映射 (v6 无 index signature, 用 set/get 封装)
const OBJ_ID_KEY = "cdmId";

function getObjId(obj: fabric.FabricObject | undefined | null): string | undefined {
  if (!obj) return undefined;
  return (obj as unknown as Record<string, unknown>)[OBJ_ID_KEY] as string | undefined;
}
function setObjId(obj: fabric.FabricObject, id: string) {
  (obj as unknown as Record<string, unknown>)[OBJ_ID_KEY] = id;
}

interface Props {
  /** 渲染用 CDM (预览模式下可能是模拟时间的副本) */
  cdm: WatchFaceCDM;
  /** 只读模式 (预览面板用) */
  readOnly?: boolean;
  /** 外部时间文本 (预览模拟), 为空时用当前时间 */
  timeText?: { time: string; date: string; info: string };
  onSelectionChange?: (sel: Selection) => void;
}

export default function FabricCanvas({
  cdm,
  readOnly = false,
  timeText,
  onSelectionChange,
}: Props) {
  const canvasElRef = useRef<HTMLCanvasElement>(null);
  const fabricRef = useRef<fabric.Canvas | null>(null);
  const cdmRef = useRef(cdm);
  cdmRef.current = cdm;
  const suppressEvent = useRef(false);

  const updateCDM = useEditorStore((s) => s.updateCDM);
  const select = useEditorStore((s) => s.select);

  // ─── 初始化画布 ────────────────────────────────────
  useEffect(() => {
    if (!canvasElRef.current || fabricRef.current) return;

    const canvas = new fabric.Canvas(canvasElRef.current, {
      width: CANVAS_SIZE,
      height: CANVAS_SIZE,
      backgroundColor: argbToCss(cdmRef.current.background.color),
      selection: false, // 禁用框选
      preserveObjectStacking: true,
    });
    fabricRef.current = canvas;

    // 对象修改 → 回写 CDM
    const onObjectModified = (e: { target?: fabric.FabricObject }) => {
      if (readOnly) return;
      const obj = e.target;
      const id = getObjId(obj);
      if (!obj || !id) return;

      const x = Math.round(obj.left ?? 0);
      const y = Math.round(obj.top ?? 0);
      // Fabric 缩放: 显示宽高 = 原始 × scale
      const w = Math.round((obj.width ?? 1) * (obj.scaleX ?? 1));
      const h = Math.round((obj.height ?? 1) * (obj.scaleY ?? 1));

      updateCDM((draft) => {
        applyPosition(draft, id, {
          x: clamp(x, 0, CANVAS_SIZE),
          y: clamp(y, 0, CANVAS_SIZE),
          width: clamp(w, 1, CANVAS_SIZE),
          height: clamp(h, 1, CANVAS_SIZE),
        });
        return draft;
      });
    };

    const onSelectionCreated = (e: { selected?: fabric.FabricObject[]; target?: fabric.FabricObject; deselected?: fabric.FabricObject[] }) => {
      if (readOnly) return;
      const obj = e.selected?.[0] ?? e.target;
      const id = getObjId(obj);
      if (id) {
        suppressEvent.current = true;
        const sel = idToSelection(id);
        if (sel) {
          select(sel);
          onSelectionChange?.(sel);
        }
        suppressEvent.current = false;
      }
    };

    const onSelectionCleared = () => {
      if (readOnly) return;
      if (!suppressEvent.current) {
        select(null);
        onSelectionChange?.(null);
      }
    };

    canvas.on("object:modified", onObjectModified);
    canvas.on("selection:created", onSelectionCreated);
    canvas.on("selection:updated", onSelectionCreated);
    canvas.on("selection:cleared", onSelectionCleared);

    return () => {
      canvas.dispose();
      fabricRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ─── CDM → 画布渲染 ────────────────────────────────
  useEffect(() => {
    const canvas = fabricRef.current;
    if (!canvas) return;

    // 记住当前选中
    const activeId = getObjId(canvas.getActiveObject());

    canvas.clear();
    canvas.backgroundColor = argbToCss(cdm.background.color);

    // 背景渐变
    if (cdm.background.type === "gradient" && cdm.background.gradient_start && cdm.background.gradient_end) {
      const grad = new fabric.Gradient({
        type: "linear",
        coords: { x1: 0, y1: 0, x2: CANVAS_SIZE, y2: CANVAS_SIZE },
        colorStops: [
          { offset: 0, color: argbToCss(cdm.background.gradient_start) },
          { offset: 1, color: argbToCss(cdm.background.gradient_end) },
        ],
      });
      canvas.backgroundColor = grad;
    }

    const t = timeText ?? defaultTimeText(cdm);
    const objs: fabric.Object[] = [];

    // 复杂功能槽位 (虚线框示意)
    cdm.complications.forEach((comp, i) => {
      if (!comp.enabled) return;
      const rect = new fabric.Rect({
        left: comp.position.x,
        top: comp.position.y,
        width: comp.position.width,
        height: comp.position.height,
        fill: "rgba(255,255,255,0.06)",
        stroke: argbToCss(comp.tint_color),
        strokeWidth: 1.5,
        strokeDashArray: [6, 4],
        rx: 12,
        ry: 12,
        hasControls: true,
      });
      setObjId(rect, `complications:${i}`);
      const label = new fabric.Text(`SLOT ${i + 1}`, {
        left: comp.position.x + comp.position.width / 2,
        top: comp.position.y + comp.position.height / 2 - 8,
        fontSize: 16,
        fill: argbToCss(comp.tint_color),
        originX: "center",
        originY: "center",
        selectable: false,
        evented: false,
      });
      objs.push(rect, label);
    });

    // 数字时间
    if (cdm.clock_type === "DIGITAL" && cdm.digital_time.enabled) {
      const dt = cdm.digital_time;
      const time = new fabric.Text(t.time, {
        left: dt.position.x,
        top: dt.position.y,
        width: dt.position.width,
        fontSize: dt.font.size,
        fontWeight: dt.font.weight === "BOLD" ? "bold" : dt.font.weight === "THIN" ? "100" : "normal",
        fill: argbToCss(dt.font.color),
        textAlign: dt.align.toLowerCase() as "left" | "center" | "right",
        fontFamily: "monospace",
      });
      setObjId(time, "digital_time");
      objs.push(time);
    }

    // 模拟表针
    if (cdm.clock_type === "ANALOG" && cdm.analog_time.enabled) {
      const at = cdm.analog_time;
      const { hourAngle, minuteAngle, secondAngle } = parseTimeForAngles(t.time);
      const cx = at.center_x;
      const cy = at.center_y;
      // 表盘中心点作为组的 position
      const mkHand = (angle: number, length: number, color: string, width: number) => {
        const rad = (angle - 90) * (Math.PI / 180);
        const line = new fabric.Line(
          [cx, cy, cx + Math.cos(rad) * length, cy + Math.sin(rad) * length],
          { stroke: argbToCss(color), strokeWidth: width, strokeLineCap: "round", selectable: false, evented: false }
        );
        return line;
      };
      objs.push(mkHand(hourAngle, at.hour_hand_length, at.hour_hand_color, 7));
      objs.push(mkHand(minuteAngle, at.minute_hand_length, at.minute_hand_color, 4.5));
      objs.push(mkHand(secondAngle, at.second_hand_length, at.second_hand_color, 2));
      const center = new fabric.Circle({
        left: cx - 6, top: cy - 6, radius: 6,
        fill: argbToCss(at.second_hand_color), selectable: false, evented: false,
      });
      objs.push(center);
    }

    // 日期
    if (cdm.date_display.enabled) {
      const dd = cdm.date_display;
      const date = new fabric.Text(t.date, {
        left: dd.position.x,
        top: dd.position.y,
        width: dd.position.width,
        fontSize: dd.font.size,
        fontWeight: dd.font.weight === "BOLD" ? "bold" : "normal",
        fill: argbToCss(dd.font.color),
        textAlign: dd.align.toLowerCase() as "left" | "center" | "right",
      });
      setObjId(date, "date_display");
      objs.push(date);
    }

    // 信息行
    if (cdm.info_line.enabled) {
      const il = cdm.info_line;
      const info = new fabric.Text(t.info, {
        left: il.position.x,
        top: il.position.y,
        width: il.position.width,
        fontSize: il.font.size,
        fontWeight: il.font.weight === "BOLD" ? "bold" : "normal",
        fill: argbToCss(il.font.color),
        textAlign: il.align.toLowerCase() as "left" | "center" | "right",
      });
      setObjId(info, "info_line");
      objs.push(info);
    }

    objs.forEach((o) => {
      if (!readOnly) {
        o.set({ lockRotation: true });
      } else {
        o.selectable = false;
        o.evented = false;
      }
      canvas.add(o);
    });

    // 恢复选中
    if (activeId && !readOnly) {
      const found = canvas.getObjects().find((o) => getObjId(o) === activeId);
      if (found) {
        canvas.setActiveObject(found);
      }
    }

    canvas.requestRenderAll();
  }, [cdm, timeText, readOnly]);

  return (
    <canvas
      ref={canvasElRef}
      style={{
        width: CANVAS_SIZE,
        height: CANVAS_SIZE,
        maxWidth: "100%",
        borderRadius: 8,
        touchAction: "none",
        cursor: readOnly ? "default" : "move",
      }}
    />
  );
}

// ─── 工具函数 ──────────────────────────────────────────

function clamp(v: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, v));
}

function idToSelection(id: string): Selection | null {
  if (id.startsWith("complications:")) {
    return { kind: "complication", index: parseInt(id.split(":")[1], 10) };
  }
  if (["digital_time", "date_display", "info_line"].includes(id)) {
    return { kind: "element", key: id as ElementKey };
  }
  return null;
}

function applyPosition(
  draft: WatchFaceCDM,
  id: string,
  pos: { x: number; y: number; width: number; height: number }
) {
  if (id.startsWith("complications:")) {
    const i = parseInt(id.split(":")[1], 10);
    if (draft.complications[i]) draft.complications[i].position = pos;
  } else if (id === "digital_time") {
    draft.digital_time.position = pos;
  } else if (id === "date_display") {
    draft.date_display.position = pos;
  } else if (id === "info_line") {
    draft.info_line.position = pos;
  }
}

/** 生成默认预览文本 (当前时间) */
export function defaultTimeText(cdm: WatchFaceCDM) {
  const now = new Date();
  const h24 = now.getHours();
  const h12 = h24 % 12 === 0 ? 12 : h24 % 12;
  const mm = String(now.getMinutes()).padStart(2, "0");
  const ss = String(now.getSeconds()).padStart(2, "0");

  let time = `${String(h24).padStart(2, "0")}:${mm}`;
  if (cdm.digital_time.format === "hh:mm") time = `${String(h12).padStart(2, "0")}:${mm}`;
  if (cdm.digital_time.format === "HH:mm:ss") time += `:${ss}`;

  // 日期: 用 %s 模板 + params
  const dateParts = cdm.date_display.params.map((p) => {
    switch (p) {
      case "MONTH": return String(now.getMonth() + 1);
      case "MONTH_S": return ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"][now.getMonth()];
      case "DAY": return String(now.getDate());
      case "DAY_Z": return String(now.getDate()).padStart(2, "0");
      case "DAY_OF_WEEK_S": return ["SUN","MON","TUE","WED","THU","FRI","SAT"][now.getDay()];
      case "YEAR": return String(now.getFullYear());
      default: return "?";
    }
  });
  let date = cdm.date_display.format;
  dateParts.forEach((v) => (date = date.replace("%s", v)));

  const info = `${cdm.info_line.label} 85${cdm.info_line.suffix === "%%" ? "%" : cdm.info_line.suffix}`;
  return { time, date, info };
}

function parseTimeForAngles(timeText: string) {
  // "14:05" 或 "14:05:08" 或 "2:05"
  const parts = timeText.split(":").map(Number);
  const h = parts[0] ?? 10;
  const m = parts[1] ?? 8;
  const s = parts[2] ?? 32;
  const hourAngle = ((h % 12) + m / 60) * 30;
  const minuteAngle = (m + s / 60) * 6;
  const secondAngle = s * 6;
  return { hourAngle, minuteAngle, secondAngle };
}
