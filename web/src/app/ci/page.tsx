"use client";

import { ChangeEvent, useEffect, useMemo, useState } from "react";
import AppShell from "@/components/ui/AppShell";
import Icon from "@/components/ui/Icon";

const SAMPLE_XML = `<?xml version="1.0"?>
<WatchFace width="450" height="450">
  <Metadata key="CLOCK_TYPE" value="DIGITAL"/>
  <Metadata key="PREVIEW_TIME" value="10:08:32"/>
  <Scene backgroundColor="#ff050505">
    <DigitalClock x="0" y="0" width="450" height="450">
      <TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE" align="CENTER" x="0" y="145" width="450" height="110">
        <Variant mode="AMBIENT" target="alpha" value="0"/>
        <Font family="SYNC_TO_DEVICE" size="92" weight="NORMAL" color="#fff4f4f5"/>
      </TimeText>
    </DigitalClock>
  </Scene>
</WatchFace>`;

type Issue = { source: string; rule: string; severity: "error" | "warning"; element?: string | null; line?: number | null; message: string; hint?: string };
type ValidateResult = { valid: boolean; errors: Issue[]; stats: Record<string, string | number> };
type PreviewFrame = { time: string; mode: string; image: string };
type BuildResult = {
  build_id: string;
  apk: { url: string; size: number; sha256: string };
  memory: { source: string; total_bytes?: number; max_active_bytes?: number; max_ambient_bytes?: number; warning?: string };
  warnings: string[];
};

export default function CIPage() {
  const [apiKey, setApiKey] = useState("");
  const [xml, setXml] = useState(SAMPLE_XML);
  const [assets, setAssets] = useState<File[]>([]);
  const [validation, setValidation] = useState<ValidateResult | null>(null);
  const [frames, setFrames] = useState<PreviewFrame[]>([]);
  const [build, setBuild] = useState<BuildResult | null>(null);
  const [busy, setBusy] = useState<"validate" | "preview" | "build" | null>(null);
  const [message, setMessage] = useState("");
  const [elapsed, setElapsed] = useState<number | null>(null);

  useEffect(() => setApiKey(sessionStorage.getItem("wff_api_key") || ""), []);
  useEffect(() => {
    if (apiKey) sessionStorage.setItem("wff_api_key", apiKey);
    else sessionStorage.removeItem("wff_api_key");
  }, [apiKey]);

  const issueCounts = useMemo(() => ({
    errors: validation?.errors.filter((item) => item.severity === "error").length || 0,
    warnings: validation?.errors.filter((item) => item.severity === "warning").length || 0,
  }), [validation]);

  function formData() {
    const form = new FormData();
    form.append("xml", new Blob([xml], { type: "application/xml" }), "watchface.xml");
    assets.forEach((asset) => form.append("assets", asset));
    return form;
  }

  async function request<T>(operation: "validate" | "preview" | "build", extra?: Record<string, string>): Promise<T> {
    if (!apiKey.trim()) throw new Error("请先填写 X-API-Key");
    const form = formData();
    Object.entries(extra || {}).forEach(([key, value]) => form.append(key, value));
    setBusy(operation);
    setMessage("");
    const started = performance.now();
    try {
      const response = await fetch(`/api/v1/wff/${operation}`, { method: "POST", headers: { "X-API-Key": apiKey.trim() }, body: form });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload?.error?.message || `HTTP ${response.status}`);
      return payload as T;
    } finally {
      setElapsed((performance.now() - started) / 1000);
      setBusy(null);
    }
  }

  async function validate() {
    try {
      const result = await request<ValidateResult>("validate");
      setValidation(result);
      setMessage(result.valid ? "三层校验通过" : "校验未通过，请按错误提示修复");
    } catch (error) { setMessage(error instanceof Error ? error.message : "校验失败"); }
  }

  async function preview() {
    try {
      const result = await request<{ frames: PreviewFrame[]; warnings: string[] }>("preview", {
        times: '["10:08:32","23:59:59"]', modes: '["active","ambient"]', shape: "round", size: "384",
      });
      setFrames(result.frames);
      setMessage(result.warnings.join("；"));
    } catch (error) { setMessage(error instanceof Error ? error.message : "预览失败"); }
  }

  async function buildApk() {
    try {
      const result = await request<BuildResult>("build", { name: "Agent CI Watch Face", package: "com.watchfaceforge.agentci", version: "1" });
      setBuild(result);
      setMessage(result.warnings.length ? result.warnings.join("；") : "APK 构建和官方内存评估通过");
    } catch (error) { setMessage(error instanceof Error ? error.message : "构建失败"); }
  }

  async function loadXml(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) setXml(await file.text());
  }

  return <AppShell><main className="md-page">
    <header className="mb-8 flex flex-wrap items-end justify-between gap-6">
      <div><span className="md-eyebrow"><Icon name="code" size={17}/>Advanced workflow</span><h1 className="mt-3 text-4xl font-medium tracking-[-.04em]">Agent CI 工作台</h1><p className="mt-3 text-forge-muted">从 WFF XML 到可安装 APK，一处完成校验、预览与内存分析。</p></div>
      <div className="w-full max-w-md"><label className="md-label">X-API-Key · 仅当前标签页</label><input type="password" value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder="wff_…" className="md-field font-mono text-sm" /></div>
    </header>

    <section className="grid gap-5 lg:grid-cols-[1.25fr_.75fr]">
      <div className="rounded-[22px] border border-forge-border bg-[#15191e] p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3"><div><span className="md-label">SOURCE</span><h2 className="font-medium">watchface.xml</h2></div><div className="flex gap-2 text-xs"><label className="md-button cursor-pointer"><Icon name="upload" size={16}/>导入 XML<input type="file" accept=".xml,application/xml" onChange={loadXml} className="hidden" /></label><button onClick={() => setXml(SAMPLE_XML)} className="md-button">恢复示例</button></div></div>
        <textarea value={xml} onChange={(event) => setXml(event.target.value)} spellCheck={false} className="h-[520px] w-full resize-y rounded-xl border border-forge-border bg-[#090c10] p-5 font-mono text-xs leading-5 text-slate-300 outline-none focus:border-forge-accent" />
        <label className="md-label mt-4">素材 assets[]</label><input type="file" multiple onChange={(event) => setAssets(Array.from(event.target.files || []))} className="w-full rounded-xl border border-forge-border bg-[#101318] p-3 text-xs" />
        {assets.length > 0 && <p className="mt-2 text-xs text-forge-muted">{assets.map((file) => `${file.name} (${Math.ceil(file.size / 1024)}KB)`).join(" · ")}</p>}
      </div>

      <div className="space-y-5">
        <div className="rounded-[22px] border border-forge-border bg-[#15191e] p-5"><span className="md-label">PIPELINE</span><div className="grid grid-cols-3 gap-2">
          {([["validate", "校验", validate], ["preview", "预览", preview], ["build", "构建 APK", buildApk]] as const).map(([id, label, action], index) => <button key={id} onClick={action} disabled={busy !== null} className={index === 2 ? "md-button md-button--filled px-2" : "md-button md-button--tonal px-2"}>{busy === id ? "处理中…" : label}</button>)}
        </div><div className="mt-4 min-h-12 rounded-xl bg-[#090c10] p-3 text-xs text-slate-300"><span className="mr-2 inline-block h-2 w-2 rounded-full bg-forge-accent"/>{message || "等待提交"}{elapsed !== null && <span className="ml-2 text-forge-muted">{elapsed.toFixed(3)}s</span>}</div></div>

        {validation && <div className="rounded-[22px] border border-forge-border bg-[#15191e] p-5"><div className="mb-3 flex items-center justify-between"><h2 className="font-medium">校验日志</h2><span className={validation.valid ? "text-emerald-400" : "text-red-400"}>{issueCounts.errors} errors · {issueCounts.warnings} warnings</span></div><div className="max-h-72 space-y-2 overflow-auto">
          {validation.errors.length === 0 ? <p className="text-sm text-emerald-400">XSD · Google validator · lint 全部通过</p> : validation.errors.map((item, index) => <div key={`${item.source}-${item.rule}-${index}`} className="rounded border border-forge-border bg-[#080c16] p-3 text-xs"><div className={item.severity === "error" ? "text-red-400" : "text-amber-300"}>{item.source} / {item.rule}{item.line ? ` · line ${item.line}` : ""}</div><p className="mt-1 text-slate-300">{item.message}</p>{item.hint && <p className="mt-1 text-forge-muted">建议：{item.hint}</p>}</div>)}
        </div></div>}

        {frames.length > 0 && <div className="rounded-[22px] border border-forge-border bg-[#15191e] p-5"><h2 className="mb-3 font-medium">预览帧 <span className="text-xs font-normal text-amber-300">近似渲染，非设备真相</span></h2><div className="grid grid-cols-2 gap-3">{frames.map((frame) => <figure key={`${frame.time}-${frame.mode}`}><img src={frame.image} alt={`${frame.time} ${frame.mode}`} className="aspect-square w-full rounded-full bg-black" /><figcaption className="mt-1 text-center text-xs text-forge-muted">{frame.time} · {frame.mode}</figcaption></figure>)}</div></div>}

        {build && <div className="rounded-[22px] border border-emerald-800/60 bg-emerald-950/20 p-5 text-sm"><div className="flex items-center justify-between"><h2 className="font-medium text-emerald-300">构建成功</h2><span className="font-mono text-xs text-forge-muted">{build.build_id}</span></div><dl className="mt-3 grid grid-cols-2 gap-2 text-xs"><dt className="text-forge-muted">APK</dt><dd>{(build.apk.size / 1024).toFixed(1)} KB</dd><dt className="text-forge-muted">Active 内存</dt><dd>{build.memory.max_active_bytes ? `${(build.memory.max_active_bytes / 1048576).toFixed(2)} MB` : "不可用"}</dd><dt className="text-forge-muted">Ambient 内存</dt><dd>{build.memory.max_ambient_bytes ? `${(build.memory.max_ambient_bytes / 1048576).toFixed(2)} MB` : "不可用"}</dd></dl><p className="mt-3 break-all font-mono text-[10px] text-forge-muted">SHA-256 {build.apk.sha256}</p><a href={build.apk.url} className="md-button md-button--filled mt-4"><Icon name="download" size={17}/>直接下载 APK</a></div>}
      </div>
    </section>
  </main></AppShell>;
}
