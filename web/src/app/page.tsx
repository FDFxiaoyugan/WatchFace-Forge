"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/ui/AppShell";
import Icon from "@/components/ui/Icon";
import TemplateGallery from "@/components/TemplateGallery";
import PromptInput from "@/components/PromptInput";

type StudioTab = "ai" | "templates";

export default function HomePage() {
  const router = useRouter();
  const [tab, setTab] = useState<StudioTab>("ai");
  const studioRef = useRef<HTMLElement>(null);

  const openStudio = (next: StudioTab) => {
    setTab(next);
    requestAnimationFrame(() => studioRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }));
  };

  const features = [
    { phase: "二期 · AI", title: "一句话生成", text: "描述风格、色彩与信息布局，生成可继续编辑的 Wear OS 表盘。", icon: "spark" as const, action: () => openStudio("ai"), label: "开始生成" },
    { phase: "一期 · 模板", title: "快速模板", text: "从经过验证的模板开始，修改颜色、字号并直接构建 APK。", icon: "layers" as const, action: () => openStudio("templates"), label: "浏览模板" },
    { phase: "一期 · 编辑", title: "可视化编辑器", text: "精确控制图层、位置、字体、数据绑定与背景图片。", icon: "palette" as const, action: () => router.push("/editor"), label: "打开编辑器" },
    { phase: "高级 · CI", title: "Agent CI", text: "提交原生 WFF XML，完成官方校验、预览、内存分析与签名。", icon: "code" as const, action: () => router.push("/ci"), label: "进入工作台" },
  ];

  return <AppShell>
    <main className="md-page">
      <section className="md-hero">
        <div>
          <span className="md-eyebrow"><Icon name="spark" size={17} />Wear OS creation platform</span>
          <h1 className="md-display">把一个想法，锻造成你的<em>表盘</em></h1>
          <p className="md-lead">从自然语言和模板快速起步，在可视化编辑器中完成设计，再通过官方 WFF 工具链校验并构建可安装 APK。</p>
          <div className="md-actions">
            <button className="md-button md-button--filled" onClick={() => openStudio("ai")}><Icon name="spark" />AI 生成表盘</button>
            <button className="md-button" onClick={() => router.push("/editor")}><Icon name="palette" />打开编辑器</button>
          </div>
        </div>
        <div className="md-watch-stage" aria-label="Quiet Mono 表盘预览">
          <div className="md-watch">
            <span className="md-watch-date">9月11日 · FRI</span>
            <strong className="md-watch-time">10:08</strong>
            <span className="md-watch-info">🔋 85%</span>
          </div>
        </div>
      </section>

      <section className="md-section" aria-labelledby="features-title">
        <div className="md-section-heading"><div><h2 id="features-title">选择工作方式</h2><p>一期与二期功能现在都有独立入口。</p></div><span className="md-chip">4 个工作流</span></div>
        <div className="md-feature-grid">
          {features.map((feature) => <button key={feature.title} className="md-feature-card" onClick={feature.action}>
            <span className="md-feature-icon"><Icon name={feature.icon} size={25} /></span>
            <h3>{feature.title}</h3><p>{feature.text}</p>
            <span className="md-feature-footer"><span>{feature.phase}</span><span className="flex items-center gap-2">{feature.label}<Icon name="arrow" size={17} /></span></span>
          </button>)}
        </div>
      </section>

      <section className="md-section" id="create" ref={studioRef} aria-labelledby="create-title">
        <div className="md-section-heading"><div><h2 id="create-title">创建工作区</h2><p>AI 灵感生成与模板快速构建，共用一条可编辑、可交付的链路。</p></div></div>
        <div className="md-workspace">
          <div className="md-workspace-head">
            <div><strong>新建表盘</strong><div className="mt-1 text-xs text-forge-muted">选择最适合你的起点</div></div>
            <div className="md-segmented" role="tablist">
              <button className={tab === "ai" ? "is-active" : ""} onClick={() => setTab("ai")} role="tab"><span className="inline-flex items-center gap-2"><Icon name="spark" size={17}/>AI 生成</span></button>
              <button className={tab === "templates" ? "is-active" : ""} onClick={() => setTab("templates")} role="tab"><span className="inline-flex items-center gap-2"><Icon name="layers" size={17}/>快速模板</span></button>
            </div>
          </div>
          <div className="md-workspace-body">{tab === "ai" ? <PromptInput /> : <TemplateGallery />}</div>
        </div>
      </section>

      <footer className="md-footer"><span>WatchFace Forge · Material Design 3</span><span>WFF 校验 · 近似预览 · APK 构建</span></footer>
    </main>
  </AppShell>;
}
