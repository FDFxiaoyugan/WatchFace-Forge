"use client";

import { useEditorStore } from "@/stores/editorStore";

const inputClass = "w-full rounded border border-zinc-700 bg-zinc-800 px-2 py-1.5 text-xs text-zinc-200 outline-none focus:border-sky-500";

export default function WatchFaceSettings() {
  const cdm = useEditorStore((s) => s.cdm);
  const updateCDM = useEditorStore((s) => s.updateCDM);
  const meta = cdm.metadata;

  return (
    <div className="space-y-4 p-3">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-zinc-500">表盘信息</div>
      <Field label="名称">
        <input className={inputClass} value={meta.name} maxLength={50}
          onChange={(e) => updateCDM((d) => { d.metadata.name = e.target.value; return d; })} />
      </Field>
      <Field label="包名">
        <input className={`${inputClass} font-mono`} value={meta.package_name}
          onChange={(e) => updateCDM((d) => { d.metadata.package_name = e.target.value.toLowerCase(); return d; })} />
        <p className="mt-1 text-[10px] text-zinc-600">例：com.example.mywatch</p>
      </Field>
      <Field label="作者">
        <input className={inputClass} value={meta.author}
          onChange={(e) => updateCDM((d) => { d.metadata.author = e.target.value; return d; })} />
      </Field>
      <div className="grid grid-cols-2 gap-2">
        <Field label="版本号">
          <input type="number" min={1} className={inputClass} value={meta.version_code}
            onChange={(e) => updateCDM((d) => { d.metadata.version_code = Math.max(1, Number(e.target.value)); return d; })} />
        </Field>
        <Field label="版本名">
          <input className={inputClass} value={meta.version_name}
            onChange={(e) => updateCDM((d) => { d.metadata.version_name = e.target.value; return d; })} />
        </Field>
      </div>
      <Field label="时钟类型">
        <select className={inputClass} value={cdm.clock_type}
          onChange={(e) => updateCDM((d) => {
            d.clock_type = e.target.value as "DIGITAL" | "ANALOG";
            d.digital_time.enabled = d.clock_type === "DIGITAL";
            d.analog_time.enabled = d.clock_type === "ANALOG";
            return d;
          })}>
          <option value="DIGITAL">数字时钟</option>
          <option value="ANALOG">模拟指针</option>
        </select>
      </Field>
      <label className="flex items-center gap-2 text-xs text-zinc-400">
        <input type="checkbox" checked={cdm.ambient_dim_mode}
          onChange={(e) => updateCDM((d) => { d.ambient_dim_mode = e.target.checked; return d; })}
          className="accent-sky-500" />
        暗屏模式降低亮度
      </label>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="block text-xs text-zinc-500"><span className="mb-1 block">{label}</span>{children}</label>;
}
