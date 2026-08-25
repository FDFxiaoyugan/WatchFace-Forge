/**
 * PropertyPanel — 属性面板
 * 根据选中元素渲染对应属性编辑器 (位置/字体/颜色/格式)
 */

"use client";

import { useState } from "react";
import { useEditorStore } from "@/stores/editorStore";
import {
  argbToHexRgb,
  cssToArgb,
  FontStyle,
  Position,
} from "@/lib/cdm/types";

// ─── 通用控件 ──────────────────────────────────────────

function NumField({
  label, value, min, max, step = 1, onChange,
}: {
  label: string; value: number; min: number; max: number; step?: number;
  onChange: (v: number) => void;
}) {
  return (
    <label className="flex items-center gap-2 text-xs">
      <span className="w-10 text-zinc-500">{label}</span>
      <input
        type="number"
        value={Math.round(value)}
        min={min} max={max} step={step}
        onChange={(e) => onChange(Number(e.target.value))}
        className="flex-1 bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-zinc-200 focus:border-sky-500 outline-none"
      />
    </label>
  );
}

function ColorField({
  label, argb, onChange,
}: {
  label: string; argb: string; onChange: (argb: string) => void;
}) {
  return (
    <label className="flex items-center gap-2 text-xs">
      <span className="w-10 text-zinc-500">{label}</span>
      <input
        type="color"
        value={argbToHexRgb(argb)}
        onChange={(e) => onChange(cssToArgb(e.target.value))}
        className="w-8 h-6 rounded cursor-pointer bg-transparent border border-zinc-700"
      />
      <span className="text-zinc-600 text-[10px] font-mono">{argb}</span>
    </label>
  );
}

function SelectField<T extends string>({
  label, value, options, onChange,
}: {
  label: string; value: T; options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <label className="flex items-center gap-2 text-xs">
      <span className="w-10 text-zinc-500">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as T)}
        className="flex-1 bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-zinc-200 focus:border-sky-500 outline-none"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </label>
  );
}

function TextField({
  label, value, onChange, placeholder,
}: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string;
}) {
  return (
    <label className="flex items-center gap-2 text-xs">
      <span className="w-10 text-zinc-500">{label}</span>
      <input
        type="text"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="flex-1 bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-zinc-200 focus:border-sky-500 outline-none"
      />
    </label>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <div className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wide">{title}</div>
      {children}
    </div>
  );
}

// ─── 位置编辑器 ────────────────────────────────────────

function PositionEditor({
  pos, onChange,
}: {
  pos: Position;
  onChange: (p: Position) => void;
}) {
  const align = (mode: "left" | "h-center" | "right" | "top" | "v-center" | "bottom") => {
    const next = { ...pos };
    if (mode === "left") next.x = 0;
    if (mode === "h-center") next.x = Math.round((450 - pos.width) / 2);
    if (mode === "right") next.x = 450 - pos.width;
    if (mode === "top") next.y = 0;
    if (mode === "v-center") next.y = Math.round((450 - pos.height) / 2);
    if (mode === "bottom") next.y = 450 - pos.height;
    onChange(next);
  };

  return (
    <Section title="位置与尺寸">
      <div className="grid grid-cols-2 gap-2">
        <NumField label="左" value={pos.x} min={0} max={450} onChange={(x) => onChange({ ...pos, x })} />
        <NumField label="顶" value={pos.y} min={0} max={450} onChange={(y) => onChange({ ...pos, y })} />
        <NumField label="宽" value={pos.width} min={1} max={450} onChange={(width) => onChange({ ...pos, width })} />
        <NumField label="高" value={pos.height} min={1} max={450} onChange={(height) => onChange({ ...pos, height })} />
      </div>
      <div className="flex items-center justify-between rounded bg-zinc-900 px-2 py-1 text-[10px] text-zinc-500">
        <span>中心 X: <b className="font-mono text-zinc-300">{Math.round(pos.x + pos.width / 2)}</b></span>
        <span>中心 Y: <b className="font-mono text-zinc-300">{Math.round(pos.y + pos.height / 2)}</b></span>
      </div>
      <div className="space-y-1.5 pt-1">
        <div className="flex items-center gap-2 text-xs">
          <span className="w-10 text-zinc-500">水平</span>
          <div className="grid flex-1 grid-cols-3 gap-1">
            <AlignButton label="左对齐" onClick={() => align("left")} />
            <AlignButton label="居中" onClick={() => align("h-center")} />
            <AlignButton label="右对齐" onClick={() => align("right")} />
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="w-10 text-zinc-500">垂直</span>
          <div className="grid flex-1 grid-cols-3 gap-1">
            <AlignButton label="顶对齐" onClick={() => align("top")} />
            <AlignButton label="居中" onClick={() => align("v-center")} />
            <AlignButton label="底对齐" onClick={() => align("bottom")} />
          </div>
        </div>
      </div>
    </Section>
  );
}

function AlignButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      className="rounded border border-zinc-700 bg-zinc-800 px-1 py-1 text-[10px] text-zinc-300 hover:border-sky-600 hover:text-sky-300"
      onClick={onClick}
    >
      {label}
    </button>
  );
}

// ─── 字体编辑器 ────────────────────────────────────────

function FontEditor({
  font, onChange, withWeight = true,
}: {
  font: FontStyle; onChange: (f: FontStyle) => void; withWeight?: boolean;
}) {
  return (
    <Section title="字体">
      <div className="flex items-center gap-2 text-xs">
        <span className="w-10 text-zinc-500">字体</span>
        <span className="flex-1 rounded border border-zinc-800 bg-zinc-900 px-2 py-1 text-zinc-400">
          跟随设备 (SYNC_TO_DEVICE)
        </span>
      </div>
      <NumField label="字号" value={font.size} min={8} max={200} onChange={(size) => onChange({ ...font, size })} />
      {withWeight && (
        <SelectField
          label="粗细"
          value={font.weight}
          options={[
            { value: "THIN", label: "细" },
            { value: "NORMAL", label: "常规" },
            { value: "BOLD", label: "粗" },
          ]}
          onChange={(weight) => onChange({ ...font, weight })}
        />
      )}
      <ColorField label="颜色" argb={font.color} onChange={(color) => onChange({ ...font, color })} />
    </Section>
  );
}

// ─── 主面板 ────────────────────────────────────────────

export default function PropertyPanel() {
  const cdm = useEditorStore((s) => s.cdm);
  const selection = useEditorStore((s) => s.selection);
  const updateCDM = useEditorStore((s) => s.updateCDM);
  const [imageBusy, setImageBusy] = useState(false);
  const [imageError, setImageError] = useState<string | null>(null);

  const uploadBackground = async (file: File | undefined) => {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setImageError("请选择 PNG、JPEG 或 WebP 图片");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setImageError("图片不能超过 10MB");
      return;
    }
    setImageBusy(true);
    setImageError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("remove_bg", "false");
      form.append("auto_crop", "false");
      form.append("max_size", "1024");
      const response = await fetch("/api/editor/image/upload", { method: "POST", body: form });
      const result = await response.json();
      if (!response.ok || !result.success) throw new Error(result.detail ?? "图片处理失败");
      updateCDM((d) => {
        d.background.type = "image";
        d.background.image_resource = "background";
        d.background.image_data = `data:image/png;base64,${result.image_b64}`;
        d.background.image_fit = d.background.image_fit ?? "cover";
        d.background.image_opacity = d.background.image_opacity ?? 100;
        return d;
      });
    } catch (error) {
      setImageError(error instanceof Error ? error.message : "图片上传失败");
    } finally {
      setImageBusy(false);
    }
  };

  if (!selection) {
    return (
      <div className="p-4 text-sm text-zinc-500">
        点击画布元素或图层面板选择要编辑的对象
      </div>
    );
  }

  if (selection.kind === "element" && selection.key === "background") {
    return (
      <div className="p-3 space-y-4">
        <Section title="背景类型">
          <SelectField
            label="类型"
            value={cdm.background.type}
            options={[
              { value: "solid", label: "纯色" },
              { value: "gradient", label: "渐变" },
              { value: "image", label: "图片" },
            ]}
            onChange={(type) => updateCDM((d) => {
              d.background.type = type;
              if (type === "gradient") {
                d.background.gradient_start ??= d.background.color;
                d.background.gradient_end ??= "#ffffffff";
              }
              return d;
            })}
          />
        </Section>
        {cdm.background.type === "solid" && (
          <ColorField
            label="颜色"
            argb={cdm.background.color}
            onChange={(color) => updateCDM((d) => { d.background.color = color; return d; })}
          />
        )}
        {cdm.background.type === "gradient" && (
          <>
            <ColorField
              label="起点"
              argb={cdm.background.gradient_start ?? "#ff000000"}
              onChange={(c) => updateCDM((d) => { d.background.gradient_start = c; return d; })}
            />
            <ColorField
              label="终点"
              argb={cdm.background.gradient_end ?? "#ff000000"}
              onChange={(c) => updateCDM((d) => { d.background.gradient_end = c; return d; })}
            />
          </>
        )}
        {cdm.background.type === "image" && (
          <Section title="背景图片">
            {cdm.background.image_data && (
              <div className="overflow-hidden rounded-lg border border-zinc-700 bg-black">
                <img src={cdm.background.image_data} alt="背景预览" className="h-28 w-full object-cover" />
              </div>
            )}
            <label className="block cursor-pointer rounded border border-dashed border-zinc-600 px-3 py-2 text-center text-xs text-zinc-400 hover:border-sky-500 hover:text-sky-300">
              {imageBusy ? "处理中..." : cdm.background.image_data ? "替换图片" : "选择图片"}
              <input type="file" accept="image/png,image/jpeg,image/webp" className="hidden" disabled={imageBusy}
                onChange={(e) => { uploadBackground(e.target.files?.[0]); e.target.value = ""; }} />
            </label>
            {imageError && <p className="text-xs text-red-400">{imageError}</p>}
            <SelectField
              label="填充"
              value={cdm.background.image_fit ?? "cover"}
              options={[
                { value: "cover", label: "覆盖（裁切）" },
                { value: "contain", label: "完整显示" },
                { value: "stretch", label: "拉伸" },
              ]}
              onChange={(image_fit) => updateCDM((d) => { d.background.image_fit = image_fit; return d; })}
            />
            <NumField label="透明" value={cdm.background.image_opacity ?? 100} min={0} max={100}
              onChange={(image_opacity) => updateCDM((d) => { d.background.image_opacity = image_opacity; return d; })} />
            {cdm.background.image_data && (
              <button type="button" className="w-full rounded bg-red-950/40 px-3 py-1.5 text-xs text-red-300 hover:bg-red-900/50"
                onClick={() => updateCDM((d) => {
                  d.background.type = "solid";
                  d.background.image_resource = null;
                  d.background.image_data = null;
                  return d;
                })}>
                移除背景图
              </button>
            )}
          </Section>
        )}
      </div>
    );
  }

  if (selection.kind === "element" && selection.key === "digital_time") {
    const dt = cdm.digital_time;
    return (
      <div className="p-3 space-y-4">
        <Section title="时间格式">
          <SelectField
            label="格式"
            value={dt.format}
            options={[
              { value: "HH:mm", label: "24小时 (14:05)" },
              { value: "hh:mm", label: "12小时 (2:05)" },
              { value: "HH:mm:ss", label: "含秒 (14:05:08)" },
            ]}
            onChange={(format) => updateCDM((d) => { d.digital_time.format = format; return d; })}
          />
        </Section>
        <PositionEditor
          pos={dt.position}
          onChange={(position) => updateCDM((d) => { d.digital_time.position = position; return d; })}
        />
        <FontEditor
          font={dt.font}
          onChange={(font) => updateCDM((d) => { d.digital_time.font = font; return d; })}
        />
        <Section title="暗屏模式">
          <ColorField
            label="暗色"
            argb={dt.ambient_color}
            onChange={(ambient_color) => updateCDM((d) => { d.digital_time.ambient_color = ambient_color; return d; })}
          />
        </Section>
      </div>
    );
  }

  if (selection.kind === "element" && selection.key === "analog_time") {
    const at = cdm.analog_time;
    return (
      <div className="p-3 space-y-4">
        <Section title="表盘中心">
          <div className="grid grid-cols-2 gap-2">
            <NumField label="X" value={at.center_x} min={0} max={450}
              onChange={(center_x) => updateCDM((d) => { d.analog_time.center_x = center_x; return d; })} />
            <NumField label="Y" value={at.center_y} min={0} max={450}
              onChange={(center_y) => updateCDM((d) => { d.analog_time.center_y = center_y; return d; })} />
          </div>
        </Section>
        <Section title="指针颜色 / 长度">
          <ColorField label="时针" argb={at.hour_hand_color}
            onChange={(c) => updateCDM((d) => { d.analog_time.hour_hand_color = c; return d; })} />
          <NumField label="长度" value={at.hour_hand_length} min={10} max={200}
            onChange={(v) => updateCDM((d) => { d.analog_time.hour_hand_length = v; return d; })} />
          <ColorField label="分针" argb={at.minute_hand_color}
            onChange={(c) => updateCDM((d) => { d.analog_time.minute_hand_color = c; return d; })} />
          <NumField label="长度" value={at.minute_hand_length} min={10} max={200}
            onChange={(v) => updateCDM((d) => { d.analog_time.minute_hand_length = v; return d; })} />
          <ColorField label="秒针" argb={at.second_hand_color}
            onChange={(c) => updateCDM((d) => { d.analog_time.second_hand_color = c; return d; })} />
          <NumField label="长度" value={at.second_hand_length} min={10} max={200}
            onChange={(v) => updateCDM((d) => { d.analog_time.second_hand_length = v; return d; })} />
        </Section>
      </div>
    );
  }

  if (selection.kind === "element" && selection.key === "date_display") {
    const dd = cdm.date_display;
    return (
      <div className="p-3 space-y-4">
        <Section title="日期格式">
          <TextField
            label="模板"
            value={dd.format}
            placeholder="%s/%s"
            onChange={(format) => updateCDM((d) => { d.date_display.format = format; return d; })}
          />
          <p className="text-[10px] text-zinc-600">{"%s 依次替换为下方数据源的值"}</p>
        </Section>
        <PositionEditor
          pos={dd.position}
          onChange={(position) => updateCDM((d) => { d.date_display.position = position; return d; })}
        />
        <FontEditor
          font={dd.font}
          onChange={(font) => updateCDM((d) => { d.date_display.font = font; return d; })}
        />
      </div>
    );
  }

  if (selection.kind === "element" && selection.key === "info_line") {
    const il = cdm.info_line;
    return (
      <div className="p-3 space-y-4">
        <Section title="信息行">
          <TextField label="标签" value={il.label}
            onChange={(label) => updateCDM((d) => { d.info_line.label = label; return d; })} />
          <TextField label="后缀" value={il.suffix}
            onChange={(suffix) => updateCDM((d) => { d.info_line.suffix = suffix; return d; })} />
          <SelectField
            label="对齐"
            value={il.align}
            options={[
              { value: "LEFT", label: "左对齐" },
              { value: "CENTER", label: "居中" },
              { value: "RIGHT", label: "右对齐" },
            ]}
            onChange={(align) => updateCDM((d) => { d.info_line.align = align; return d; })}
          />
        </Section>
        <PositionEditor
          pos={il.position}
          onChange={(position) => updateCDM((d) => { d.info_line.position = position; return d; })}
        />
        <FontEditor
          font={il.font}
          onChange={(font) => updateCDM((d) => { d.info_line.font = font; return d; })}
        />
        <DataBindingHint />
      </div>
    );
  }

  if (selection.kind === "complication") {
    const comp = cdm.complications[selection.index];
    if (!comp) return null;
    return (
      <div className="p-3 space-y-4">
        <Section title={`槽位 ${selection.index + 1}`}>
          <SelectField
            label="类型"
            value={comp.slot_type}
            options={[
              { value: "SHORT_TEXT", label: "短文本" },
              { value: "LONG_TEXT", label: "长文本" },
              { value: "RANGED_VALUE", label: "范围值" },
              { value: "ICON", label: "图标" },
            ]}
            onChange={(slot_type) => updateCDM((d) => {
              d.complications[selection.index].slot_type = slot_type;
              return d;
            })}
          />
          <ColorField
            label="着色"
            argb={comp.tint_color}
            onChange={(tint_color) => updateCDM((d) => {
              d.complications[selection.index].tint_color = tint_color;
              return d;
            })}
          />
        </Section>
        <PositionEditor
          pos={comp.position}
          onChange={(position) => updateCDM((d) => {
            d.complications[selection.index].position = position;
            return d;
          })}
        />
        <p className="text-xs text-zinc-500">
          槽位内容由 Wear OS 系统填充 (电量/心率/天气等)
        </p>
      </div>
    );
  }

  return null;
}

function DataBindingHint() {
  return (
    <div className="text-[10px] text-zinc-600 border-t border-zinc-800 pt-2">
      数据源绑定请使用「数据」面板
    </div>
  );
}
