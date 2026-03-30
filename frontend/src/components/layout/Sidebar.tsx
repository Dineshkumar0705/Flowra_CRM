"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Users, TrendingUp, Settings,
  LogOut, Zap, ChevronRight, Puzzle, Crown,
  CheckSquare, Activity, BarChart2,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

const NAV_GROUPS = [
  {
    label: "Main Menu",
    items: [
      { label: "Dashboard",    icon: LayoutDashboard, href: "/dashboard"    },
      { label: "Contacts",     icon: Users,            href: "/contacts"     },
      { label: "Deals",        icon: TrendingUp,       href: "/deals"        },
    ],
  },
  {
    label: "Productivity",
    items: [
      { label: "Tasks",        icon: CheckSquare,      href: "/tasks"        },
      { label: "Activity",     icon: Activity,         href: "/activity"     },
      { label: "Reports",      icon: BarChart2,        href: "/reports"      },
    ],
  },
  {
    label: "System",
    items: [
      { label: "Integrations", icon: Puzzle,           href: "/integrations" },
      { label: "Settings",     icon: Settings,         href: "/settings"     },
    ],
  },
];

function initials(name?: string | null) {
  if (!name) return "?";
  return name.split(" ").map(w => w[0]).slice(0, 2).join("").toUpperCase();
}

export default function Sidebar() {
  const pathname = usePathname();
  const { user, workspace, logout } = useAuth();

  return (
    <aside
      className="w-[220px] flex-shrink-0 flex flex-col"
      style={{
        background: "var(--color-sidebar)",
        borderRadius: "20px",
        boxShadow: "0 8px 32px rgba(26,15,58,0.28), 0 2px 8px rgba(124,58,237,0.12)",
        border: "1px solid rgba(196,181,253,0.10)",
        overflow: "hidden",
      }}
    >
      {/* Logo */}
      <div
        className="px-5 py-5 flex items-center gap-2.5"
        style={{ borderBottom: "1px solid rgba(196,181,253,0.08)" }}
      >
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: "linear-gradient(135deg, #7C3AED, #A78BFA)" }}
        >
          <Zap className="w-4 h-4 text-white" fill="white" />
        </div>
        <div>
          <p className="text-white font-bold text-base leading-none">Flowra</p>
          {workspace && (
            <p
              className="text-[10px] mt-0.5 truncate max-w-[120px]"
              style={{ color: "rgba(196,181,253,0.5)" }}
            >
              {workspace.name}
            </p>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 overflow-y-auto py-2 space-y-4">
        {NAV_GROUPS.map(group => (
          <div key={group.label}>
            <p
              className="text-[9px] font-bold tracking-widest uppercase px-3 mb-1"
              style={{ color: "rgba(196,181,253,0.35)" }}
            >
              {group.label}
            </p>
            <div className="space-y-0.5">
              {group.items.map(({ label, icon: Icon, href }) => {
                const active = pathname.startsWith(href);
                return (
                  <Link
                    key={href}
                    href={href}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 relative"
                    style={{
                      color: active ? "#fff" : "var(--color-sidebar-text-muted)",
                      background: active ? "var(--color-sidebar-active)" : "transparent",
                    }}
                    onMouseEnter={e => {
                      if (!active) {
                        (e.currentTarget as HTMLElement).style.background = "var(--color-sidebar-hover)";
                        (e.currentTarget as HTMLElement).style.color = "var(--color-sidebar-text)";
                      }
                    }}
                    onMouseLeave={e => {
                      if (!active) {
                        (e.currentTarget as HTMLElement).style.background = "transparent";
                        (e.currentTarget as HTMLElement).style.color = "var(--color-sidebar-text-muted)";
                      }
                    }}
                  >
                    {active && (
                      <span
                        className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full"
                        style={{ background: "#A78BFA" }}
                      />
                    )}
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    <span className="flex-1">{label}</span>
                    {active && <ChevronRight className="w-3 h-3 opacity-50" />}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Pro plan badge */}
      <div
        className="mx-3 mb-3 px-3 py-3 rounded-xl"
        style={{
          background: "linear-gradient(135deg, rgba(124,58,237,0.25), rgba(167,139,250,0.15))",
          border: "1px solid rgba(167,139,250,0.35)",
        }}
      >
        <div className="flex items-center gap-1.5 mb-1.5">
          <Crown className="w-3.5 h-3.5" style={{ color: "#A78BFA" }} />
          <span className="text-[11px] font-bold tracking-wide" style={{ color: "#C4B5FD" }}>
            Pro Plan
          </span>
        </div>
        <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.1)" }}>
          <div
            className="h-full rounded-full"
            style={{ width: "42%", background: "linear-gradient(90deg, #7C3AED, #A78BFA)" }}
          />
        </div>
        <p className="text-[10px] mt-1.5" style={{ color: "rgba(196,181,253,0.6)" }}>
          42% of limits used
        </p>
      </div>

      {/* User row */}
      <div
        className="px-3 py-3"
        style={{ borderTop: "1px solid rgba(196,181,253,0.08)" }}
      >
        <div
          className="flex items-center gap-2.5 px-2 py-2 rounded-xl"
          style={{ background: "rgba(255,255,255,0.05)" }}
        >
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
            style={{ background: "linear-gradient(135deg, #7C3AED, #A78BFA)" }}
          >
            {initials(user?.name)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-white truncate">{user?.name ?? "User"}</p>
            <p className="text-[10px] truncate" style={{ color: "rgba(196,181,253,0.5)" }}>
              {user?.email}
            </p>
          </div>
          <button
            onClick={logout}
            title="Logout"
            className="p-1.5 rounded-lg transition-all"
            style={{ color: "rgba(196,181,253,0.4)" }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.background = "rgba(239,68,68,0.15)";
              (e.currentTarget as HTMLElement).style.color = "#F87171";
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.background = "transparent";
              (e.currentTarget as HTMLElement).style.color = "rgba(196,181,253,0.4)";
            }}
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </aside>
  );
}
