/**
 * CDM (Canonical Data Model) TypeScript 类型定义
 * 严格对齐后端 schema/cdm/models.py (Pydantic)
 * 画布坐标系: 450x450 (WFF 标准)
 */

// ─── 枚举 ─────────────────────────────────────────────

export type ClockType = "DIGITAL" | "ANALOG";
export type FontWeight = "THIN" | "NORMAL" | "BOLD";
export type HorizontalAlign = "LEFT" | "CENTER" | "RIGHT";
export type DataSource =
  | "HOUR_0_23"
  | "HOUR_1_12"
  | "MINUTE_Z"
  | "SECOND_Z"
  | "AMPM_STRING"
  | "DAY"
  | "DAY_Z"
  | "DAY_OF_WEEK_S"
  | "MONTH"
  | "MONTH_S"
  | "YEAR"
  | "BATTERY_PERCENT"
  | "HEART_RATE";

/** 数据源元信息 (供绑定面板展示) */
export const DATA_SOURCE_META: Record<
  DataSource,
  { label: string; sample: string }
> = {
  HOUR_0_23: { label: "小时 (0-23)", sample: "14" },
  HOUR_1_12: { label: "小时 (1-12)", sample: "2" },
  MINUTE_Z: { label: "分钟 (补零)", sample: "05" },
  SECOND_Z: { label: "秒 (补零)", sample: "08" },
  AMPM_STRING: { label: "上午/下午", sample: "PM" },
  DAY: { label: "日", sample: "20" },
  DAY_Z: { label: "日 (补零)", sample: "08" },
  DAY_OF_WEEK_S: { label: "星期 (缩写)", sample: "THU" },
  MONTH: { label: "月 (数字)", sample: "8" },
  MONTH_S: { label: "月 (缩写)", sample: "AUG" },
  YEAR: { label: "年", sample: "2026" },
  BATTERY_PERCENT: { label: "电量 %", sample: "85" },
  HEART_RATE: { label: "心率", sample: "72" },
};

// ─── 子模型 ────────────────────────────────────────────

export interface Position {
  x: number; // 0-450
  y: number; // 0-450
  width: number; // 1-450
  height: number; // 1-450
}

export interface FontStyle {
  family: string; // 默认 "SYNC_TO_DEVICE"
  size: number; // 8-200
  weight: FontWeight;
  color: string; // 8位 ARGB: #ffRRGGBB
}

export interface Background {
  type: "solid" | "gradient" | "image";
  color: string;
  gradient_start?: string | null;
  gradient_end?: string | null;
  image_resource?: string | null;
}

export interface DigitalTime {
  enabled: boolean;
  format: string; // "HH:mm" | "hh:mm" | "HH:mm:ss"
  position: Position;
  font: FontStyle;
  align: HorizontalAlign;
  ambient_color: string;
}

export interface AnalogTime {
  enabled: boolean;
  center_x: number; // 0-450
  center_y: number;
  hour_hand_color: string;
  minute_hand_color: string;
  second_hand_color: string;
  hour_hand_length: number; // 10-200
  minute_hand_length: number;
  second_hand_length: number;
}

export interface DateDisplay {
  enabled: boolean;
  format: string; // "%s/%s"
  position: Position;
  font: FontStyle;
  align: HorizontalAlign;
  params: DataSource[];
}

export interface InfoLine {
  enabled: boolean;
  label: string;
  data_source: DataSource;
  suffix: string;
  position: Position;
  font: FontStyle;
  align: HorizontalAlign;
}

export interface ComplicationSlot {
  enabled: boolean;
  slot_type: "SHORT_TEXT" | "LONG_TEXT" | "RANGED_VALUE" | "ICON";
  position: Position;
  tint_color: string;
}

export interface WatchFaceMetadata {
  name: string; // 1-50 字符
  package_name: string; // com.example.xxx
  version_code: number; // >=1
  version_name: string;
  author: string;
  preview_time: string;
}

// ─── 顶层模型 ──────────────────────────────────────────

export interface WatchFaceCDM {
  schema_version: string;
  metadata: WatchFaceMetadata;
  clock_type: ClockType;
  background: Background;
  digital_time: DigitalTime;
  analog_time: AnalogTime;
  date_display: DateDisplay;
  info_line: InfoLine;
  complications: ComplicationSlot[];
  ambient_dim_mode: boolean;
}

// ─── 工厂函数 (默认值对齐 Pydantic default_factory) ────

export const CANVAS_SIZE = 450;

export function defaultPosition(partial?: Partial<Position>): Position {
  return { x: 0, y: 0, width: 450, height: 50, ...partial };
}

export function defaultFontStyle(partial?: Partial<FontStyle>): FontStyle {
  return {
    family: "SYNC_TO_DEVICE",
    size: 48,
    weight: "NORMAL",
    color: "#ffffffff",
    ...partial,
  };
}

export function defaultCDM(): WatchFaceCDM {
  return {
    schema_version: "1.0",
    metadata: {
      name: "My Watch Face",
      package_name: "com.watchforge.preview",
      version_code: 1,
      version_name: "1.0.0",
      author: "WatchFace Forge",
      preview_time: "10:08:32",
    },
    clock_type: "DIGITAL",
    background: { type: "solid", color: "#ff000000" },
    digital_time: {
      enabled: true,
      format: "HH:mm",
      position: defaultPosition({ y: 120, height: 120 }),
      font: defaultFontStyle({ size: 100, weight: "BOLD", color: "#ff00F5FF" }),
      align: "CENTER",
      ambient_color: "#ff888888",
    },
    analog_time: {
      enabled: false,
      center_x: 225,
      center_y: 225,
      hour_hand_color: "#ffffffff",
      minute_hand_color: "#ff00F5FF",
      second_hand_color: "#ffFF6B6B",
      hour_hand_length: 120,
      minute_hand_length: 160,
      second_hand_length: 180,
    },
    date_display: {
      enabled: true,
      format: "%s/%s",
      position: defaultPosition({ y: 260, height: 50 }),
      font: defaultFontStyle({ size: 32, color: "#ffAAAAAA" }),
      align: "CENTER",
      params: ["MONTH", "DAY"],
    },
    info_line: {
      enabled: true,
      label: "BAT",
      data_source: "BATTERY_PERCENT",
      suffix: "%%",
      position: defaultPosition({ y: 320, height: 50 }),
      font: defaultFontStyle({ size: 28, color: "#ffFF6B6B" }),
      align: "CENTER",
    },
    complications: [],
    ambient_dim_mode: true,
  };
}

// ─── 颜色工具 ──────────────────────────────────────────

/** ARGB(#ffRRGGBB) → CSS rgba() */
export function argbToCss(argb: string): string {
  const m = argb.match(/^#([0-9a-fA-F]{8})$/);
  if (!m) return argb;
  const hex = m[1];
  const a = parseInt(hex.slice(0, 2), 16) / 255;
  const r = parseInt(hex.slice(2, 4), 16);
  const g = parseInt(hex.slice(4, 6), 16);
  const b = parseInt(hex.slice(6, 8), 16);
  return `rgba(${r}, ${g}, ${b}, ${a})`;
}

/** CSS rgba() / #RRGGBB → ARGB */
export function cssToArgb(css: string): string {
  const m = css.match(/^#([0-9a-fA-F]{6})$/);
  if (m) return `#ff${m[1]}`;
  const m2 = css.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)$/);
  if (m2) {
    const a = Math.round(parseFloat(m2[4] ?? "1") * 255)
      .toString(16)
      .padStart(2, "0");
    const r = parseInt(m2[1]).toString(16).padStart(2, "0");
    const g = parseInt(m2[2]).toString(16).padStart(2, "0");
    const b = parseInt(m2[3]).toString(16).padStart(2, "0");
    return `#${a}${r}${g}${b}`;
  }
  return css;
}
