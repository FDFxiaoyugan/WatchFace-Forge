"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Icon from "@/components/ui/Icon";
import { loadAIConfig, toAIRequestConfig, UserAIConfig, EMPTY_AI_CONFIG } from "@/lib/aiConfig";

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

export default function PromptInput({ onResult }: { onResult?: (r: GenerateResult) => void }) {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<{ stage: string; progress: number; message: string } | null>(null);
  const [result, setResult] = useState<GenerateResult | null>(null);
  const [aiConfig, setAIConfig] = useState<UserAIConfig>(EMPTY_AI_CONFIG);

  useEffect(() => setAIConfig(loadAIConfig()), []);

  async function handleGenerate() {
    if (!prompt.trim() || loading) return;
    setLoading(true);
    setResult(null);
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
        body: JSON.stringify({ prompt, ai_config: toAIRequestConfig(aiConfig) }),
      });
      const data = await res.json();
      clearInterval(progressTimer);
      setProgress({ stage: "done", progress: 100, message: data.status === "success" ? "完成!" : "失败" });
      setResult(data);
      onResult?.(data);
    } catch (err) {
      clearInterval(progressTimer);
      setProgress({ stage: "failed", progress: 100, message: String(err) });
      setResult({ task_id: "", status: "failed", error: err instanceof Error ? err.message : String(err) });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1.15fr_.85fr]">
      <div className="rounded-[20px] bg-[#15191e] p-6 md:p-8">
        <div className="mb-6 flex items-start gap-4">
          <span className="md-feature-icon"><Icon name="spark" size={24}/></span>
          <div><h2 className="text-xl font-semibold">描述你的表盘</h2><p className="mt-1 text-sm text-forge-muted">AI 会生成结构化 CDM，并自动完成 WFF 编译与 APK 构建。</p></div>
        </div>

        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-forge-border bg-[#101318] px-4 py-3 text-sm">
          <span className="flex items-center gap-2 text-forge-muted"><Icon name="settings" size={17}/><span className={`h-2 w-2 rounded-full ${aiConfig.apiKey ? "bg-emerald-400" : "bg-amber-300"}`}/>{aiConfig.apiKey ? `自定义 API · ${aiConfig.model || "gpt-4o"}` : "使用服务端默认 AI"}</span>
          <button type="button" className="text-forge-accent hover:underline" onClick={() => router.push("/settings")}>配置 AI 服务</button>
        </div>

      {/* Input */}
      <div className="mb-3 flex flex-col gap-3 sm:flex-row">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleGenerate(); } }}
          placeholder="例如：黑色极简数字表盘，时间使用大号细体，显示日期和电量…"
          disabled={loading}
          rows={3}
          className="md-field min-h-[104px] flex-1 resize-none"
        />
        <button
          onClick={handleGenerate}
          disabled={loading || !prompt.trim()}
          className="md-button md-button--filled self-stretch sm:self-auto"
        >
          <Icon name="spark" size={18}/>{loading ? "生成中…" : "生成表盘"}
        </button>
      </div>

      {/* Example prompts */}
      {!loading && (
        <div className="flex flex-wrap gap-2 mb-4">
          {EXAMPLE_PROMPTS.map((p) => (
            <button
              key={p}
              onClick={() => setPrompt(p)}
              className="md-chip cursor-pointer bg-transparent transition-colors hover:border-forge-accent hover:text-forge-accent"
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
          <div className="md-progress">
            <div
              className="h-full bg-forge-accent transition-all duration-500"
              style={{ width: `${progress.progress}%` }}
            />
          </div>
        </div>
      )}
      </div>

      <aside className="rounded-[20px] border border-forge-border bg-[#101318] p-6 md:p-8">
        <span className="md-label">生成流程</span>
        <ol className="mt-5 space-y-5">
          {["理解设计描述", "生成并校验 CDM", "编译 WFF XML", "签名并交付 APK"].map((item, index) => <li key={item} className="flex items-center gap-3 text-sm"><span className="grid h-7 w-7 place-items-center rounded-full bg-[#263e60] text-xs text-[#d3e3fd]">{index + 1}</span><span className="text-forge-muted">{item}</span></li>)}
        </ol>
        {!result && <div className="mt-8 rounded-2xl bg-[#1b1f24] p-4 text-sm leading-6 text-forge-muted">生成结果可直接下载，也能带入可视化编辑器继续调整。</div>}
        {result && <div className={`mt-8 rounded-2xl border p-4 ${result.status === "success" ? "border-emerald-800 bg-emerald-950/20" : "border-red-900 bg-red-950/20"}`}>
          <strong className={result.status === "success" ? "text-emerald-300" : "text-red-300"}>{result.status === "success" ? "生成完成" : "生成失败"}</strong>
          {result.status === "success" ? <div className="mt-4 flex flex-wrap gap-2">
            {result.download_url && <a className="md-button md-button--filled" href={result.download_url}><Icon name="download" size={17}/>下载 APK</a>}
            {result.task_id && <button className="md-button" onClick={() => router.push(`/editor?task_id=${result.task_id}`)}><Icon name="palette" size={17}/>继续编辑</button>}
          </div> : <p className="mt-2 text-sm text-red-200/80">{result.error || "AI 服务暂不可用，请检查模型配置。"}</p>}
        </div>}
      </aside>
    </div>
  );
}
