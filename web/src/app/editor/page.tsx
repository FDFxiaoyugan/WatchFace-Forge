/**
 * 编辑器页面 — Phase 3 可视化编辑器
 *
 * 布局: 顶栏 (撤销重做/导入导出/编译) + 左图层面板 + 中画布 + 右属性面板 + 预览抽屉
 * 入口: /editor?task_id=xxx (从生成结果跳转) 或空白模板
 */

"use client";

import { useEffect, useState, Suspense, useCallback, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { useEditorStore, useCanUndo, useCanRedo } from "@/stores/editorStore";
import FabricCanvas, { defaultTimeText } from "@/components/editor/FabricCanvas";
import LayerPanel from "@/components/editor/LayerPanel";
import PropertyPanel from "@/components/editor/PropertyPanel";
import DataBindingPanel from "@/components/editor/DataBindingPanel";
import PreviewDevice from "@/components/editor/PreviewDevice";
import WatchFaceSettings from "@/components/editor/WatchFaceSettings";
import AppShell from "@/components/ui/AppShell";
import Icon from "@/components/ui/Icon";

export default function EditorPage() {
  return (
    <Suspense fallback={<div className="grid min-h-screen place-items-center text-forge-muted">加载编辑器…</div>}>
      <EditorInner />
    </Suspense>
  );
}

function EditorInner() {
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
    <AppShell compact><div className="flex h-[calc(100vh-64px)] flex-col bg-[#101318] text-forge-text">
      {/* 顶栏 */}
      <header className="flex min-h-16 items-center gap-2 border-b border-forge-border bg-[#15191e] px-4">
        <div className="mr-2 min-w-0"><span className="md-label mb-0">VISUAL EDITOR</span><span className="block max-w-[200px] truncate text-sm font-medium">{cdm.metadata.name}</span></div>

        <div className="flex-1" />

        <button
          onClick={undo}
          disabled={!canUndo}
          className="md-icon-button disabled:opacity-30"
          title="撤销 (Ctrl+Z)"
        >
          <Icon name="undo" size={19}/>
        </button>
        <button
          onClick={redo}
          disabled={!canRedo}
          className="md-icon-button disabled:opacity-30"
          title="重做 (Ctrl+Shift+Z)"
        >
          <Icon name="redo" size={19}/>
        </button>
        <div className="h-6 w-px bg-forge-border" />
        <div className="flex items-center rounded-full bg-[#292d32] px-1 text-xs">
          <button className="md-icon-button h-8 w-8" onClick={() => setZoom((z) => Math.max(0.5, z - 0.1))}><Icon name="zoomOut" size={16}/></button>
          <button className="min-w-12 px-1 py-1 text-forge-muted hover:text-forge-accent" onClick={() => setZoom(1)}>{Math.round(zoom * 100)}%</button>
          <button className="md-icon-button h-8 w-8" onClick={() => setZoom((z) => Math.min(1.5, z + 0.1))}><Icon name="zoomIn" size={16}/></button>
        </div>
        <div className="h-6 w-px bg-forge-border" />
        <button
          onClick={validateCDM}
          disabled={busy}
          className="md-button h-9 min-h-9 px-4 disabled:opacity-50"
        >
          校验
        </button>
        <input ref={importRef} type="file" accept="application/json,.json" className="hidden"
          onChange={(e) => importCDM(e.target.files?.[0])} />
        <button
          onClick={() => importRef.current?.click()}
          className="md-button h-9 min-h-9 px-4"
        >
          导入 CDM
        </button>
        <button
          onClick={exportCDM}
          className="md-button h-9 min-h-9 px-4"
        >
          导出 CDM
        </button>
        <button
          onClick={() => setShowPreview((v) => !v)}
          className="md-button md-button--tonal h-9 min-h-9 px-4"
        >
          <Icon name="preview" size={16}/>{showPreview ? "隐藏预览" : "设备预览"}
        </button>
        <button
          onClick={buildAPK}
          disabled={busy}
          className="md-button md-button--filled h-9 min-h-9 px-4 disabled:opacity-50"
        >
          <Icon name="download" size={16}/>{busy ? "构建中…" : "编译 APK"}
        </button>
      </header>

      {/* 主体三栏 */}
      <div className="flex-1 flex min-h-0">
        {/* 左: 图层 */}
        <aside className="flex w-60 flex-col border-r border-forge-border bg-[#15191e]">
          <LayerPanel />
        </aside>

        {/* 中: 画布 */}
        <main className="flex flex-1 items-center justify-center overflow-auto bg-[radial-gradient(circle_at_center,#26384f_0%,#101318_48%,#090b0e_100%)]">
          <div className="shrink-0" style={{ width: 450 * zoom, height: 450 * zoom }}>
            <div className="relative w-[450px] h-[450px] overflow-hidden rounded-full"
              style={{ transform: `scale(${zoom})`, transformOrigin: "top left" }}>
              <FabricCanvas cdm={cdm} timeText={timeText} />
              <div className="pointer-events-none absolute inset-0 z-10 rounded-full border border-dashed border-[#a8c7fa]/30" />
            </div>
          </div>
        </main>

        {/* 右: 属性 / 数据 */}
        <aside className="flex w-80 flex-col border-l border-forge-border bg-[#15191e]">
          <div className="flex border-b border-forge-border px-2 pt-2">
            <button
              className={`flex-1 rounded-t-xl py-2.5 text-xs ${
                rightTab === "props" ? "border-b-2 border-forge-accent bg-[#263e60]/40 text-forge-accent" : "text-forge-muted hover:bg-[#292d32]"
              }`}
              onClick={() => setRightTab("props")}
            >
              属性
            </button>
            <button
              className={`flex-1 py-2 text-xs ${
                rightTab === "data" ? "border-b-2 border-forge-accent bg-[#263e60]/40 text-forge-accent" : "text-forge-muted hover:bg-[#292d32]"
              }`}
              onClick={() => setRightTab("data")}
            >
              数据绑定
            </button>
            <button
              className={`flex-1 py-2 text-xs ${
                rightTab === "settings" ? "border-b-2 border-forge-accent bg-[#263e60]/40 text-forge-accent" : "text-forge-muted hover:bg-[#292d32]"
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
          <aside className="w-[520px] overflow-y-auto border-l border-forge-border bg-[#15191e]">
            <PreviewDevice />
          </aside>
        )}
      </div>

      {/* Toast */}
      {toast && (
        <div className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-2xl border border-forge-border bg-[#292d32] px-5 py-3 text-sm shadow-xl">
          {toast}
        </div>
      )}
    </div></AppShell>
  );
}
