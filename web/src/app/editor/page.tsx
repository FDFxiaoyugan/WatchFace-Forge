/**
 * 编辑器页面 — Phase 3 可视化编辑器
 *
 * 布局: 顶栏 (撤销重做/导入导出/编译) + 左图层面板 + 中画布 + 右属性面板 + 预览抽屉
 * 入口: /editor?task_id=xxx (从生成结果跳转) 或空白模板
 */

"use client";

import { useEffect, useState, Suspense, useCallback, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEditorStore, useCanUndo, useCanRedo } from "@/stores/editorStore";
import FabricCanvas, { defaultTimeText } from "@/components/editor/FabricCanvas";
import LayerPanel from "@/components/editor/LayerPanel";
import PropertyPanel from "@/components/editor/PropertyPanel";
import DataBindingPanel from "@/components/editor/DataBindingPanel";
import PreviewDevice from "@/components/editor/PreviewDevice";
import WatchFaceSettings from "@/components/editor/WatchFaceSettings";

export default function EditorPage() {
  return (
    <Suspense fallback={<div className="p-8 text-zinc-500">加载编辑器...</div>}>
      <EditorInner />
    </Suspense>
  );
}

function EditorInner() {
  const router = useRouter();
  const params = useSearchParams();
  const taskId = params.get("task_id");

  const cdm = useEditorStore((s) => s.cdm);
  const loadCDM = useEditorStore((s) => s.loadCDM);
  const undo = useEditorStore((s) => s.undo);
  const redo = useEditorStore((s) => s.redo);
  const nudgeSelection = useEditorStore((s) => s.nudgeSelection);
  const deleteSelection = useEditorStore((s) => s.deleteSelection);
  const canUndo = useCanUndo();
  const canRedo = useCanRedo();

  const [rightTab, setRightTab] = useState<"props" | "data" | "settings">("props");
  const [showPreview, setShowPreview] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [zoom, setZoom] = useState(1);
  const importRef = useRef<HTMLInputElement>(null);

  const flash = useCallback((msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  }, []);

  // 加载生成任务的 CDM
  useEffect(() => {
    if (!taskId) return;
    fetch(`/api/editor/cdm/${taskId}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((data) => {
        loadCDM(data.cdm);
        flash("已导入生成结果");
      })
      .catch((e) => {
        console.error("load CDM failed", e);
        flash("CDM 加载失败, 使用默认模板");
      });
  }, [taskId, loadCDM, flash]);

  // 键盘快捷键: 撤销/重做、方向键微调、删除图层
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const editing = target?.matches("input, textarea, select, [contenteditable=true]");
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
        e.preventDefault();
        if (e.shiftKey) redo();
        else undo();
      } else if (!editing && ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)) {
        e.preventDefault();
        const step = e.shiftKey ? 10 : 1;
        nudgeSelection(
          e.key === "ArrowLeft" ? -step : e.key === "ArrowRight" ? step : 0,
          e.key === "ArrowUp" ? -step : e.key === "ArrowDown" ? step : 0
        );
      } else if (!editing && (e.key === "Delete" || e.key === "Backspace")) {
        e.preventDefault();
        deleteSelection();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [undo, redo, nudgeSelection, deleteSelection]);

  const importCDM = async (file: File | undefined) => {
    if (!file) return;
    try {
      const parsed = JSON.parse(await file.text());
      const res = await fetch("/api/editor/cdm/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cdm: parsed }),
      });
      const result = await res.json();
      if (!result.valid) throw new Error(result.errors?.[0] ?? "CDM 格式无效");
      loadCDM(parsed);
      flash("✓ CDM 已导入");
    } catch (error) {
      flash(`✕ ${error instanceof Error ? error.message : "导入失败"}`);
    } finally {
      if (importRef.current) importRef.current.value = "";
    }
  };

  // ─── 导出 CDM ──────────────────────────────────────
  const exportCDM = () => {
    const blob = new Blob([JSON.stringify(cdm, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${cdm.metadata.name.replace(/\s+/g, "_").toLowerCase()}.cdm.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // ─── 校验 CDM ──────────────────────────────────────
  const validateCDM = async () => {
    setBusy(true);
    try {
      const res = await fetch("/api/editor/cdm/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cdm }),
      });
      const data = await res.json();
      if (data.valid) {
        flash(data.warnings?.length ? `✓ 有效 (${data.warnings.length} 个警告)` : "✓ CDM 有效");
      } else {
        flash(`✕ ${data.errors[0]}`);
      }
    } catch {
      flash("校验请求失败");
    } finally {
      setBusy(false);
    }
  };

  // ─── 编译 APK ──────────────────────────────────────
  const buildAPK = async () => {
    setBusy(true);
    try {
      const res = await fetch("/api/build", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cdm, task_id: `edit-${Date.now()}` }),
      });
      const data = await res.json();
      if (data.download_url) {
        flash("✓ APK 构建成功");
        window.open(data.download_url, "_blank");
      } else {
        flash(`✕ ${data.error ?? data.detail ?? "构建失败"}`);
      }
    } catch {
      flash("构建请求失败");
    } finally {
      setBusy(false);
    }
  };

  const timeText = defaultTimeText(cdm);

  return (
    <div className="h-screen flex flex-col bg-zinc-950 text-zinc-200">
      {/* 顶栏 */}
      <header className="flex items-center gap-2 px-4 h-12 border-b border-zinc-800 bg-zinc-900/50">
        <button
          className="text-zinc-400 hover:text-zinc-200 text-sm"
          onClick={() => router.push("/")}
        >
          ← 返回
        </button>
        <div className="h-4 w-px bg-zinc-800" />
        <span className="text-sm font-medium truncate max-w-[200px]">
          {cdm.metadata.name}
        </span>

        <div className="flex-1" />

        <button
          onClick={undo}
          disabled={!canUndo}
          className="px-2 py-1 text-sm rounded bg-zinc-800 hover:bg-zinc-700 disabled:opacity-30 disabled:hover:bg-zinc-800"
          title="撤销 (Ctrl+Z)"
        >
          ↩
        </button>
        <button
          onClick={redo}
          disabled={!canRedo}
          className="px-2 py-1 text-sm rounded bg-zinc-800 hover:bg-zinc-700 disabled:opacity-30 disabled:hover:bg-zinc-800"
          title="重做 (Ctrl+Shift+Z)"
        >
          ↪
        </button>
        <div className="h-4 w-px bg-zinc-800" />
        <div className="flex items-center rounded bg-zinc-800 text-xs">
          <button className="px-2 py-1 hover:text-sky-300" onClick={() => setZoom((z) => Math.max(0.5, z - 0.1))}>−</button>
          <button className="min-w-12 px-1 py-1 text-zinc-400 hover:text-sky-300" onClick={() => setZoom(1)}>{Math.round(zoom * 100)}%</button>
          <button className="px-2 py-1 hover:text-sky-300" onClick={() => setZoom((z) => Math.min(1.5, z + 0.1))}>＋</button>
        </div>
        <div className="h-4 w-px bg-zinc-800" />
        <button
          onClick={validateCDM}
          disabled={busy}
          className="px-3 py-1 text-xs rounded bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50"
        >
          校验
        </button>
        <input ref={importRef} type="file" accept="application/json,.json" className="hidden"
          onChange={(e) => importCDM(e.target.files?.[0])} />
        <button
          onClick={() => importRef.current?.click()}
          className="px-3 py-1 text-xs rounded bg-zinc-800 hover:bg-zinc-700"
        >
          导入 CDM
        </button>
        <button
          onClick={exportCDM}
          className="px-3 py-1 text-xs rounded bg-zinc-800 hover:bg-zinc-700"
        >
          导出 CDM
        </button>
        <button
          onClick={() => setShowPreview((v) => !v)}
          className="px-3 py-1 text-xs rounded bg-zinc-800 hover:bg-zinc-700"
        >
          {showPreview ? "隐藏预览" : "设备预览"}
        </button>
        <button
          onClick={buildAPK}
          disabled={busy}
          className="px-3 py-1 text-xs rounded bg-sky-600 hover:bg-sky-500 text-white disabled:opacity-50"
        >
          {busy ? "构建中..." : "编译 APK"}
        </button>
      </header>

      {/* 主体三栏 */}
      <div className="flex-1 flex min-h-0">
        {/* 左: 图层 */}
        <aside className="w-56 border-r border-zinc-800 bg-zinc-900/30 flex flex-col">
          <LayerPanel />
        </aside>

        {/* 中: 画布 */}
        <main className="flex-1 flex items-center justify-center overflow-auto bg-[radial-gradient(circle_at_center,#1a1a2e_0%,#0a0a0f_100%)]">
          <div className="shrink-0" style={{ width: 450 * zoom, height: 450 * zoom }}>
            <div className="relative w-[450px] h-[450px] overflow-hidden rounded-full"
              style={{ transform: `scale(${zoom})`, transformOrigin: "top left" }}>
              <FabricCanvas cdm={cdm} timeText={timeText} />
              <div className="pointer-events-none absolute inset-0 z-10 border border-dashed border-white/20 rounded-full" />
            </div>
          </div>
        </main>

        {/* 右: 属性 / 数据 */}
        <aside className="w-72 border-l border-zinc-800 bg-zinc-900/30 flex flex-col">
          <div className="flex border-b border-zinc-800">
            <button
              className={`flex-1 py-2 text-xs ${
                rightTab === "props" ? "text-sky-300 border-b-2 border-sky-500" : "text-zinc-500"
              }`}
              onClick={() => setRightTab("props")}
            >
              属性
            </button>
            <button
              className={`flex-1 py-2 text-xs ${
                rightTab === "data" ? "text-sky-300 border-b-2 border-sky-500" : "text-zinc-500"
              }`}
              onClick={() => setRightTab("data")}
            >
              数据绑定
            </button>
            <button
              className={`flex-1 py-2 text-xs ${
                rightTab === "settings" ? "text-sky-300 border-b-2 border-sky-500" : "text-zinc-500"
              }`}
              onClick={() => setRightTab("settings")}
            >
              表盘
            </button>
          </div>
          <div className="flex-1 overflow-y-auto">
            {rightTab === "props" ? <PropertyPanel /> : rightTab === "data" ? <DataBindingPanel /> : <WatchFaceSettings />}
          </div>
        </aside>

        {/* 预览抽屉 */}
        {showPreview && (
          <aside className="w-[520px] border-l border-zinc-800 bg-zinc-900/50 overflow-y-auto">
            <PreviewDevice />
          </aside>
        )}
      </div>

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg bg-zinc-800 border border-zinc-700 text-sm shadow-xl z-50">
          {toast}
        </div>
      )}
    </div>
  );
}
