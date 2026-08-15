import TemplateGallery from "@/components/TemplateGallery";

export default function HomePage() {
  return (
    <main className="container mx-auto max-w-4xl px-4 py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-3">
          <span className="text-forge-accent">WatchFace</span> Forge
        </h1>
        <p className="text-forge-muted text-lg">
          选择模板，一键生成你的 Wear OS 表盘
        </p>
      </div>

      {/* Template Gallery */}
      <TemplateGallery />

      {/* Footer */}
      <footer className="mt-16 text-center text-forge-muted text-sm">
        <p>Phase 1 — MVP · WFF 构建引擎已验证</p>
      </footer>
    </main>
  );
}
