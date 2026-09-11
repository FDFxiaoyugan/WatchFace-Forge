"use client";

import { useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Icon from "./Icon";

const nav = [
  { href: "/", label: "工作台", icon: "home" as const },
  { href: "/editor", label: "可视化编辑", icon: "palette" as const },
  { href: "/ci", label: "Agent CI", icon: "code" as const },
  { href: "/settings", label: "AI 设置", icon: "settings" as const },
];

export default function AppShell({ children, compact = false }: { children: React.ReactNode; compact?: boolean }) {
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);

  return <div className={compact ? "md-app md-app--compact" : "md-app"}>
    <header className="md-topbar">
      <button className="md-icon-button md-mobile-only" onClick={() => setOpen(!open)} aria-label="打开导航"><Icon name={open ? "close" : "menu"} /></button>
      <button className="md-brand" onClick={() => router.push("/")} aria-label="WatchFace Forge 首页">
        <span className="md-brand-mark"><Icon name="watch" size={22} /></span>
        <span><strong>WatchFace</strong> Forge</span>
      </button>
      <nav className={open ? "md-nav md-nav--open" : "md-nav"}>
        {nav.map((item) => <button key={item.href} onClick={() => { router.push(item.href); setOpen(false); }} className={`md-nav-item ${pathname === item.href ? "is-active" : ""}`}>
          <Icon name={item.icon} size={18} /><span>{item.label}</span>
        </button>)}
      </nav>
      <div className="md-topbar-meta"><span className="md-status-dot" />WFF v1</div>
    </header>
    {children}
  </div>;
}
