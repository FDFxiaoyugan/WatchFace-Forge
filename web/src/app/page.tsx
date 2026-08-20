"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import TemplateGallery from "@/components/TemplateGallery";
import PromptInput from "@/components/PromptInput";

type Tab = "templates" | "ai";

interface GenerateResult {
  task_id: string;
  status: "success" | "failed";
  cdm?: any;
  fixes?: string[];
  backend?: string;
  attempts?: number;
  apk_filename?: string;
  apk_size?: number;
  download_url?: string;
  error?: string;
}

export default function HomePage() {
  const [tab, setTab] = useState<Tab>("templates");
  const router = useRouter();

  return (
    <main className="container mx-auto max-w-4xl px-4 py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-3">
          <span className="text-forge-accent">WatchFace</span> Forge
        </h1>
        <p className="text-forge-muted text-lg">
          AI 驱动的 Wear OS 表盘生成平台
        </p>
        <button
          onClick={() => router.push("/editor")}
          className="mt-4 px-5 py-2 rounded-lg border border-forge-accent text-forge-accent hover:bg-forge-accent/10 transition-all text-sm font-medium"
        >
          🎨 打开可视化编辑器
        </button>
      </div>

      {/* Tab Switch */}
      <div className="flex justify-center gap-2 mb-8">
        <button
          onClick={() => setTab("templates")}
          className={`px-6 py-2 rounded-lg font-medium transition-all ${
            tab === "templates"
              ? "bg-forge-accent/20 border border-forge-accent text-forge-accent"
              : "border border-forge-border text-forge-muted hover:text-forge-text"
          }`}
        >
          模板选择
        </button>
        <button
          onClick={() => setTab("ai")}
          className={`px-6 py-2 rounded-lg font-medium transition-all ${
            tab === "ai"
              ? "bg-forge-accent/20 border border-forge-accent text-forge-accent"
              : "border border-forge-border text-forge-muted hover:text-forge-text"
          }`}
        >
          AI 生成
        </button>
      </div>

      {/* Content */}
      {tab === "templates" ? <TemplateGallery /> : <PromptInput onResult={() => {}} />}

      {/* Footer */}
      <footer className="mt-16 text-center text-forge-muted text-sm">
        <p>Phase 3 — 可视化编辑 · Fabric.js + Celery 异步管线</p>
      </footer>
    </main>
  );
}
