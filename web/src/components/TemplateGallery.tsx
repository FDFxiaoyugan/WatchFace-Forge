"use client";

import { useState, useEffect } from "react";

interface Template {
  id: string;
  name: string;
  description: string;
  preview_color: string;
}

interface CDM {
  metadata: {
    name: string;
    package_name: string;
    version_code: number;
    version_name: string;
  };
  clock_type: string;
  background: { type: string; color: string };
  digital_time: {
    enabled: boolean;
    format: string;
    font: { size: number; weight: string; color: string };
    ambient_color: string;
  };
  date_display: {
    enabled: boolean;
    format: string;
    font: { size: number; color: string };
  };
  info_line: {
    enabled: boolean;
    label: string;
    data_source: string;
    font: { size: number; color: string };
  };
}

interface BuildResult {
  task_id: string;
  status: "success" | "failed";
  apk_filename: string | null;
  apk_size: number | null;
  download_url: string | null;
  error: string | null;
}

function ColorInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  // Convert #ffRRGGBB to #RRGGBB for color input
  const htmlColor = "#" + (value || "#ffffffff").slice(4);
  return (
    <div className="flex items-center gap-2">
      <label className="text-sm text-forge-muted w-24">{label}</label>
      <input
        type="color"
        value={htmlColor}
        onChange={(e) => onChange("#ff" + e.target.value.slice(1))}
        className="w-10 h-10 rounded cursor-pointer bg-transparent border border-forge-border"
      />
      <span className="text-xs text-forge-muted font-mono">{value}</span>
    </div>
  );
}

function SliderInput({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-sm text-forge-muted w-24">{label}</label>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="flex-1 accent-forge-accent"
      />
      <span className="text-xs text-forge-muted w-8 text-right">{value}</span>
    </div>
  );
}

export default function TemplateGallery() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [building, setBuilding] = useState<string | null>(null);
  const [result, setResult] = useState<BuildResult | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [cdm, setCdm] = useState<CDM | null>(null);

  useEffect(() => {
    fetch("/api/templates")
      .then((r) => r.json())
      .then((data) => {
        setTemplates(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  async function handleSelectTemplate(id: string) {
    setSelectedTemplate(id);
    setResult(null);
    const res = await fetch(`/api/templates/${id}`);
    const data = await res.json();
    setCdm(data.cdm);
  }

  function updateCDM(path: string, value: any) {
    if (!cdm) return;
    const parts = path.split(".");
    const newCdm = { ...cdm } as any;
    let obj = newCdm;
    for (let i = 0; i < parts.length - 1; i++) {
      obj[parts[i]] = { ...obj[parts[i]] };
      obj = obj[parts[i]];
    }
    obj[parts[parts.length - 1]] = value;
    setCdm(newCdm);
  }

  async function handleBuild() {
    if (!cdm) return;
    setBuilding(cdm.metadata.name);
    setResult(null);
    try {
      const res = await fetch("/api/build", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cdm }),
      });
      const data = await res.json();
      if (data.status === "error" || data.status === "failed") {
        setResult({
          task_id: data.task_id || "",
          status: "failed",
          apk_filename: null,
          apk_size: null,
          download_url: null,
          error: data.error || data.message || JSON.stringify(data.errors || "Build failed"),
        });
      } else {
        setResult(data);
      }
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

  // Template selection view
  if (!selectedTemplate) {
    return (
      <div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {templates.map((tmpl) => (
            <div
              key={tmpl.id}
              className="bg-forge-card border border-forge-border rounded-xl p-6 hover:border-forge-accent/50 transition-all cursor-pointer"
              onClick={() => handleSelectTemplate(tmpl.id)}
            >
              <div className="flex justify-center mb-4">
                <div
                  className="watch-preview w-32 h-32 flex items-center justify-center"
                  style={{
                    background: `radial-gradient(circle, ${tmpl.preview_color}22 0%, #000 100%)`,
                    border: `2px solid ${tmpl.preview_color}`,
                  }}
                >
                  <span className="text-2xl font-bold" style={{ color: tmpl.preview_color }}>
                    10:08
                  </span>
                </div>
              </div>
              <h3 className="text-lg font-semibold text-center mb-1">{tmpl.name}</h3>
              <p className="text-sm text-forge-muted text-center mb-4">{tmpl.description}</p>
              <button className="w-full py-2 rounded-lg font-medium transition-all"
                style={{ background: `${tmpl.preview_color}22`, border: `1px solid ${tmpl.preview_color}55`, color: tmpl.preview_color }}>
                选择此模板
              </button>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Customization view
  if (cdm) {
    return (
      <div>
        {/* Back button */}
        <button
          onClick={() => { setSelectedTemplate(null); setCdm(null); setResult(null); }}
          className="mb-6 text-forge-muted hover:text-forge-accent text-sm"
        >
          ← 返回模板列表
        </button>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Left: Customization Panel */}
          <div className="bg-forge-card border border-forge-border rounded-xl p-6 space-y-4">
            <h2 className="text-xl font-semibold mb-4">自定义表盘</h2>

            {/* Time Color */}
            <ColorInput
              label="时间颜色"
              value={cdm.digital_time.font.color}
              onChange={(v) => updateCDM("digital_time.font.color", v)}
            />

            {/* Time Size */}
            <SliderInput
              label="时间字号"
              value={cdm.digital_time.font.size}
              min={40}
              max={150}
              onChange={(v) => updateCDM("digital_time.font.size", v)}
            />

            {/* Background Color */}
            <ColorInput
              label="背景颜色"
              value={cdm.background.color}
              onChange={(v) => updateCDM("background.color", v)}
            />

            {/* Date Color */}
            {cdm.date_display.enabled && (
              <ColorInput
                label="日期颜色"
                value={cdm.date_display.font.color}
                onChange={(v) => updateCDM("date_display.font.color", v)}
              />
            )}

            {/* Info Color */}
            {cdm.info_line.enabled && (
              <ColorInput
                label="信息颜色"
                value={cdm.info_line.font.color}
                onChange={(v) => updateCDM("info_line.font.color", v)}
              />
            )}

            {/* Build Button */}
            <button
              onClick={handleBuild}
              disabled={building !== null}
              className="w-full py-3 mt-4 rounded-lg font-medium transition-all disabled:opacity-50 bg-forge-accent/20 border border-forge-accent text-forge-accent hover:bg-forge-accent/30"
            >
              {building ? "构建中..." : "构建 APK"}
            </button>
          </div>

          {/* Right: Preview + Result */}
          <div className="space-y-6">
            {/* Live Preview */}
            <div className="bg-forge-card border border-forge-border rounded-xl p-6 text-center">
              <h3 className="text-sm text-forge-muted mb-4">预览</h3>
              <div
                className="watch-preview w-48 h-48 mx-auto flex flex-col items-center justify-center"
                style={{
                  background: `radial-gradient(circle, ${cdm.background.color.slice(4)}22 0%, #000 100%)`,
                  border: `2px solid ${cdm.digital_time.font.color.slice(4)}`,
                }}
              >
                <span
                  className="font-bold"
                  style={{
                    color: cdm.digital_time.font.color,
                    fontSize: `${Math.min(cdm.digital_time.font.size * 0.4, 48)}px`,
                  }}
                >
                  10:08
                </span>
                {cdm.date_display.enabled && (
                  <span className="text-xs mt-1" style={{ color: cdm.date_display.font.color }}>
                    08/15
                  </span>
                )}
                {cdm.info_line.enabled && (
                  <span className="text-xs mt-1" style={{ color: cdm.info_line.font.color }}>
                    {cdm.info_line.label} 85%
                  </span>
                )}
              </div>
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
                      APK: {(result.apk_size! / 1024).toFixed(1)} KB
                    </div>
                    <a
                      href={result.download_url!}
                      download
                      className="inline-block px-6 py-3 bg-forge-accent/20 border border-forge-accent text-forge-accent rounded-lg font-medium hover:bg-forge-accent/30"
                    >
                      下载 APK
                    </a>
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
                  </div>
                ) : (
                  <div className="text-center">
                    <div className="text-red-400 text-lg font-semibold mb-2">
                      ❌ 构建失败
                    </div>
                    <div className="text-red-300 text-sm font-mono break-all">
                      {result.error}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return null;
}
