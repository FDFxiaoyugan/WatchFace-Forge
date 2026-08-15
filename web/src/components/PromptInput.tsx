"use client";

import { useState } from "react";

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

const EXAMPLE_PROMPTS = [
  "霓虹蓝赛博朋克风数字表盘",
  "极简白色细体表盘，大字号",
  "琥珀橙暖色表盘，显示电量和日期",
  "深紫色星空风格，霓虹紫时间",
];

export default function PromptInput({ onResult }: { onResult: (r: GenerateResult) => void }) {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<{ stage: string; progress: number; message: string } | null>(null);

  async function handleGenerate() {
    if (!prompt.trim() || loading) return;
    setLoading(true);
    setProgress({ stage: "starting", progress: 10, message: "正在启动..." });

    // 模拟进度 (WebSocket 在 dev 模式下可能不稳定)
    const stages = [
      { stage: "llm_generating", progress: 20, message: "正在调用 AI 生成表盘设计..." },
      { stage: "compiling", progress: 70, message: "正在编译 WFF XML..." },
      { stage: "building_apk", progress: 85, message: "正在构建 APK..." },
    ];

    let stageIdx = 0;
    const progressTimer = setInterval(() => {
      if (stageIdx < stages.length) {
        setProgress(stages[stageIdx]);
        stageIdx++;
      }
    }, 3000);

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();
      clearInterval(progressTimer);
      setProgress({ stage: "done", progress: 100, message: data.status === "success" ? "完成!" : "失败" });
      onResult(data);
    } catch (err) {
      clearInterval(progressTimer);
      setProgress({ stage: "failed", progress: 100, message: String(err) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-forge-card border border-forge-border rounded-xl p-6">
      <h2 className="text-xl font-bold mb-4 text-forge-accent">AI 生成表盘</h2>

      {/* Input */}
      <div className="flex gap-2 mb-3">
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
          placeholder="描述你想要的表盘..."
          disabled={loading}
          className="flex-1 px-4 py-3 bg-forge-bg border border-forge-border rounded-lg text-forge-text placeholder-forge-muted focus:border-forge-accent focus:outline-none"
        />
        <button
          onClick={handleGenerate}
          disabled={loading || !prompt.trim()}
          className="px-6 py-3 bg-forge-accent/20 border border-forge-accent text-forge-accent rounded-lg font-medium hover:bg-forge-accent/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "生成中..." : "生成"}
        </button>
      </div>

      {/* Example prompts */}
      {!loading && (
        <div className="flex flex-wrap gap-2 mb-4">
          {EXAMPLE_PROMPTS.map((p) => (
            <button
              key={p}
              onClick={() => setPrompt(p)}
              className="px-3 py-1 text-xs bg-forge-bg border border-forge-border rounded-full text-forge-muted hover:border-forge-accent/50 hover:text-forge-text transition-all"
            >
              {p}
            </button>
          ))}
        </div>
      )}

      {/* Progress */}
      {progress && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-forge-muted">{progress.message}</span>
            <span className="text-sm text-forge-accent">{progress.progress}%</span>
          </div>
          <div className="h-2 bg-forge-bg rounded-full overflow-hidden">
            <div
              className="h-full bg-forge-accent transition-all duration-500"
              style={{ width: `${progress.progress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
