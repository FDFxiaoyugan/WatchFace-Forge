type IconName =
  | "home" | "spark" | "palette" | "code" | "layers" | "check"
  | "download" | "arrow" | "upload" | "preview" | "undo" | "redo"
  | "zoomIn" | "zoomOut" | "menu" | "close" | "api" | "watch";

const paths: Record<IconName, React.ReactNode> = {
  home: <path d="M3 10.8 12 3l9 7.8V21h-6v-6H9v6H3V10.8Z" />,
  spark: <path d="m12 2 1.55 5.45L19 9l-5.45 1.55L12 16l-1.55-5.45L5 9l5.45-1.55L12 2Zm6 13 .85 3.15L22 19l-3.15.85L18 23l-.85-3.15L14 19l3.15-.85L18 15Z" />,
  palette: <path d="M12 3a9 9 0 0 0 0 18h1.5a2.5 2.5 0 0 0 0-5H12a1.5 1.5 0 0 1 0-3h3a6 6 0 0 0 0-12h-3Zm-5 8a1.25 1.25 0 1 1 0-2.5A1.25 1.25 0 0 1 7 11Zm2-4.5A1.25 1.25 0 1 1 9 4a1.25 1.25 0 0 1 0 2.5Zm4 0A1.25 1.25 0 1 1 13 4a1.25 1.25 0 0 1 0 2.5Zm4 3A1.25 1.25 0 1 1 17 7a1.25 1.25 0 0 1 0 2.5Z" />,
  code: <path d="m8.5 6-6 6 6 6M15.5 6l6 6-6 6M14 3l-4 18" />,
  layers: <path d="m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5" />,
  check: <path d="m5 12 4 4L19 6" />,
  download: <path d="M12 3v12m0 0 5-5m-5 5-5-5M4 20h16" />,
  arrow: <path d="M5 12h14m-5-5 5 5-5 5" />,
  upload: <path d="M12 17V5m0 0L7 10m5-5 5 5M4 20h16" />,
  preview: <><path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"/><circle cx="12" cy="12" r="2.5"/></>,
  undo: <path d="M9 7 4 12l5 5M5 12h8a6 6 0 0 1 6 6" />,
  redo: <path d="m15 7 5 5-5 5m4-5h-8a6 6 0 0 0-6 6" />,
  zoomIn: <><circle cx="10.5" cy="10.5" r="6.5"/><path d="M10.5 7v7m-3.5-3.5h7M16 16l5 5"/></>,
  zoomOut: <><circle cx="10.5" cy="10.5" r="6.5"/><path d="M7 10.5h7M16 16l5 5"/></>,
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  close: <path d="m6 6 12 12M18 6 6 18" />,
  api: <path d="M7 7h10v10H7V7Zm-4 3h4m10 0h4M3 14h4m10 0h4M10 3v4m4-4v4m-4 10v4m4-4v4" />,
  watch: <><rect x="6" y="5" width="12" height="14" rx="4"/><path d="m9 5 1-3h4l1 3m-6 14 1 3h4l1-3M12 9v3l2 1"/></>,
};

export default function Icon({ name, size = 20, className = "" }: { name: IconName; size?: number; className?: string }) {
  return <svg aria-hidden="true" viewBox="0 0 24 24" width={size} height={size} className={className} fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}
