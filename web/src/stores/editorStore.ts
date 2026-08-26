/**
 * 编辑器 Store — Zustand
 *
 * 职责:
 *  - CDM 状态管理 (深层不可变更新)
 *  - 选中元素管理 (时间/日期/信息行/复杂功能/背景)
 *  - 撤销/重做 (历史快照栈, 上限 50)
 *  - 预览时间模拟
 */

"use client";

import { create } from "zustand";
import {
  WatchFaceCDM,
  defaultCDM,
  ComplicationSlot,
} from "@/lib/cdm/types";

// ─── 类型 ──────────────────────────────────────────────

export type ElementKey =
  | "background"
  | "digital_time"
  | "analog_time"
  | "date_display"
  | "info_line"
  | "complications"; // complications 用 comp:{index}

export type Selection =
  | { kind: "element"; key: ElementKey }
  | { kind: "complication"; index: number }
  | null;

interface EditorState {
  cdm: WatchFaceCDM;
  selection: Selection;
  history: WatchFaceCDM[]; // 撤销栈
  future: WatchFaceCDM[]; // 重做栈
  dirty: boolean; // 有未保存修改
  previewMs: number; // 预览时间 (当日毫秒偏移)

  // 动作
  loadCDM: (cdm: WatchFaceCDM) => void;
  select: (sel: Selection) => void;
  updateCDM: (mutator: (draft: WatchFaceCDM) => WatchFaceCDM, snapshot?: boolean) => void;
  undo: () => void;
  redo: () => void;
  markSaved: () => void;
  setPreviewMs: (ms: number) => void;
  addComplication: () => void;
  removeComplication: (index: number) => void;
  nudgeSelection: (dx: number, dy: number) => void;
  deleteSelection: () => void;
}

const MAX_HISTORY = 50;

/** 深拷贝 (CDM 是纯 JSON 结构) */
function deepCopy<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

export const useEditorStore = create<EditorState>((set, get) => ({
  cdm: defaultCDM(),
  selection: null,
  history: [],
  future: [],
  dirty: false,
  previewMs: 10 * 3600_000 + 8 * 60_000 + 32 * 1000, // 10:08:32

  loadCDM: (cdm) =>
    set({
      cdm: deepCopy(cdm),
      selection: null,
      history: [],
      future: [],
      dirty: false,
    }),

  select: (sel) => set({ selection: sel }),

  updateCDM: (mutator, snapshot = true) => {
    const { cdm, history } = get();
    const prev = snapshot ? deepCopy(cdm) : null;
    const next = deepCopy(cdm);
    const result = mutator(next);
    // mutator 可能返回新对象或原地修改 draft
    const finalCdm = result ?? next;
    set({
      cdm: finalCdm,
      history: prev ? [...history.slice(-(MAX_HISTORY - 1)), prev] : history,
      future: snapshot ? [] : get().future,
      dirty: true,
    });
  },

  undo: () => {
    const { history, future, cdm } = get();
    if (history.length === 0) return;
    const prev = history[history.length - 1];
    set({
      cdm: prev,
      history: history.slice(0, -1),
      future: [deepCopy(cdm), ...future].slice(0, MAX_HISTORY),
      dirty: true,
    });
  },

  redo: () => {
    const { history, future, cdm } = get();
    if (future.length === 0) return;
    const next = future[0];
    set({
      cdm: next,
      history: [...history.slice(-(MAX_HISTORY - 1)), deepCopy(cdm)],
      future: future.slice(1),
      dirty: true,
    });
  },

  markSaved: () => set({ dirty: false }),

  setPreviewMs: (ms) => set({ previewMs: ms }),

  addComplication: () => {
    const { cdm, updateCDM } = get();
    if (cdm.complications.length >= 4) return;
    updateCDM((draft) => {
      const corners = [
        { x: 30, y: 30 },
        { x: 290, y: 30 },
        { x: 30, y: 290 },
        { x: 290, y: 290 },
      ];
      const pos = corners[draft.complications.length];
      const slot: ComplicationSlot = {
        enabled: true,
        slot_type: "SHORT_TEXT",
        position: { x: pos.x, y: pos.y, width: 130, height: 130 },
        tint_color: "#ffffffff",
      };
      draft.complications.push(slot);
      return draft;
    });
    set({ selection: { kind: "complication", index: get().cdm.complications.length - 1 } });
  },

  removeComplication: (index) => {
    const { updateCDM } = get();
    updateCDM((draft) => {
      draft.complications.splice(index, 1);
      return draft;
    });
    set({ selection: null });
  },

  nudgeSelection: (dx, dy) => {
    const { selection, updateCDM } = get();
    if (!selection || (selection.kind === "element" && selection.key === "background")) return;
    updateCDM((draft) => {
      const move = (pos: { x: number; y: number; width: number; height: number }) => {
        pos.x = Math.max(0, Math.min(450 - pos.width, pos.x + dx));
        pos.y = Math.max(0, Math.min(450 - pos.height, pos.y + dy));
      };
      if (selection.kind === "complication") {
        const slot = draft.complications[selection.index];
        if (slot) move(slot.position);
      } else if (selection.key === "digital_time") move(draft.digital_time.position);
      else if (selection.key === "date_display") move(draft.date_display.position);
      else if (selection.key === "info_line") move(draft.info_line.position);
      else if (selection.key === "analog_time") {
        draft.analog_time.center_x = Math.max(0, Math.min(450, draft.analog_time.center_x + dx));
        draft.analog_time.center_y = Math.max(0, Math.min(450, draft.analog_time.center_y + dy));
      }
      return draft;
    });
  },

  deleteSelection: () => {
    const { selection, updateCDM } = get();
    if (!selection || (selection.kind === "element" && selection.key === "background")) return;
    updateCDM((draft) => {
      if (selection.kind === "complication") draft.complications.splice(selection.index, 1);
      else if (selection.key === "digital_time") draft.digital_time.enabled = false;
      else if (selection.key === "analog_time") draft.analog_time.enabled = false;
      else if (selection.key === "date_display") draft.date_display.enabled = false;
      else if (selection.key === "info_line") draft.info_line.enabled = false;
      return draft;
    });
    set({ selection: { kind: "element", key: "background" } });
  },
}));

// ─── 便捷 hooks ────────────────────────────────────────

export function useCanUndo() {
  return useEditorStore((s) => s.history.length > 0);
}
export function useCanRedo() {
  return useEditorStore((s) => s.future.length > 0);
}
