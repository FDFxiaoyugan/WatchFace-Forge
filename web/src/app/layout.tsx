import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WatchFace Forge · Wear OS 表盘工作台",
  description: "AI 驱动的 Wear OS 表盘生成平台",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>
        {children}
      </body>
    </html>
  );
}
