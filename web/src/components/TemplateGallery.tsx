"use client";

import { useState, useEffect } from "react";

interface Template {
  id: string;
  name: string;
  description: string;
  preview_color: string;
}

interface BuildResult {
  task_id: string;
  status: "success" | "failed";
  apk_filename: string | null;
  apk_size: number | null;
  download_url: string | null;
  error: string | null;
}

export default function TemplateGallery() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [building, setBuilding] = useState<string | null>(null);
  const [result, setResult] = useState<BuildResult | null>(null);

  useEffect(() => {
    fetch("/api/templates")
      .then((r) => r.json())
      .then((data) => {
        setTemplates(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load templates:", err);
        setLoading(false);
      });
  }, []);

  async function handleBuild(templateId: string) {
    setBuilding(templateId);
    setResult(null);

    try {
      // 1. 获取模板 CDM
      const tmplRes = await fetch(`/api/templates/${templateId}`);
      const tmplData = await tmplRes.json();

      // 2. 构建 APK
      const buildRes = await fetch("/api/build", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cdm: tmplData.cdm }),
      });
      const buildData: BuildResult = await buildRes.json();
      setResult(buildData);
    } catch (err) {
      setResult({
        task_id: "",
        status: "failed",
        apk_filename: null,
        apk_size: null,
        download_url: null,
        error: String(err),
      });
    } finally {
      setBuilding(null);
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="text-forge-muted">加载模板中...</div>
      </div>
    );
  }

  return (
    <div>
      {/* Template Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {templates.map((tmpl) => (
          <div
            key={tmpl.id}
            className="bg-forge-card border border-forge-border rounded-xl p-6 hover:border-forge-accent/50 transition-all"
          >
            {/* Preview Circle */}
            <div className="flex justify-center mb-4">
              <div
                className="watch-preview w-32 h-32 flex items-center justify-center"
                style={{
                  background: `radial-gradient(circle, ${tmpl.preview_color}22 0%, #000 100%)`,
                  border: `2px solid ${tmpl.preview_color}`,
                }}
              >
                <span
                  className="text-2xl font-bold"
                  style={{ color: tmpl.preview_color }}
                >
                  10:08
                </span>
              </div>
            </div>

            {/* Info */}
            <h3 className="text-lg font-semibold text-center mb-1">
              {tmpl.name}
            </h3>
            <p className="text-sm text-forge-muted text-center mb-4">
              {tmpl.description}
            </p>

            {/* Build Button */}
            <button
              onClick={() => handleBuild(tmpl.id)}
              disabled={building !== null}
              className="w-full py-2 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                background:
                  building === tmpl.id
                    ? "#374151"
                    : `${tmpl.preview_color}22`,
                border: `1px solid ${tmpl.preview_color}`,
                color: tmpl.preview_color,
              }}
            >
              {building === tmpl.id ? "构建中..." : "构建 APK"}
            </button>
          </div>
        ))}
      </div>

      {/* Build Result */}
      {result && (
        <div className="bg-forge-card border border-forge-border rounded-xl p-6">
          {result.status === "success" ? (
            <div className="text-center">
              <div className="text-green-400 text-lg font-semibold mb-2">
                ✅ 构建成功
              </div>
              <div className="text-forge-muted text-sm mb-4">
                APK 大小: {(result.apk_size! / 1024).toFixed(1)} KB · Task:{" "}
                {result.task_id}
              </div>
              <a
                href={result.download_url!}
                download
                className="inline-block px-6 py-3 bg-forge-accent/20 border border-forge-accent text-forge-accent rounded-lg font-medium hover:bg-forge-accent/30 transition-all"
              >
                下载 APK
              </a>

              {/* QR Code */}
              <div className="mt-6 flex flex-col items-center">
                <img
                  src={`/api/qrcode${result.download_url!.replace("/api/download", "")}`}
                  alt="QR Code"
                  className="w-40 h-40 rounded-lg bg-white p-2"
                />
                <p className="text-xs text-forge-muted mt-2">
                  手表扫码下载安装
                </p>
              </div>

              <p className="text-xs text-forge-muted mt-4">
                或使用 ADB: adb install -r xxx.apk
              </p>
            </div>
          ) : (
            <div className="text-center">
              <div className="text-red-400 text-lg font-semibold mb-2">
                ❌ 构建失败
              </div>
              <div className="text-red-300 text-sm font-mono">
                {result.error}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
