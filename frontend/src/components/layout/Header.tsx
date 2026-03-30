"use client";

/**
 * Header — Flowra CRM
 *
 * Key architectural decision:
 *   The profile dropdown renders with `position: fixed` (coords calculated
 *   from the trigger button's getBoundingClientRect). This completely
 *   bypasses every CSS stacking context in the layout tree, so the menu
 *   always paints above dashboard cards, charts, and modals — no matter
 *   what z-index or overflow those containers use.
 */

import React, {
  useState,
  useRef,
  useEffect,
  useCallback,
  type ElementType,
} from "react";
import { usePathname } from "next/navigation";
import { Bell, Settings, LogOut, User, ChevronDown, Check } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import apiClient from "@/services/apiClient";
import { useAuth } from "@/hooks/useAuth";

// ─── Page metadata ───────────────────────────────────────────────────────────

const PAGE_META: Record<string, { title: string; subtitle: string }> = {
  "/dashboard":    { title: "Dashboard",    subtitle: "Overview of your sales pipeline"              },
  "/contacts":     { title: "Contacts",     subtitle: "Manage leads and customers"                   },
  "/deals":        { title: "Deals",        subtitle: "Track opportunities in your pipeline"         },
  "/tasks":        { title: "Tasks",        subtitle: "Stay on top of your to-dos and follow-ups"    },
  "/activity":     { title: "Activity",     subtitle: "Full audit trail of everything in your CRM"   },
  "/reports":      { title: "Reports",      subtitle: "Revenue analytics and pipeline performance"   },
  "/integrations": { title: "Integrations", subtitle: "Connect apps and automate your workflow"      },
  "/settings":     { title: "Settings",     subtitle: "Manage account and preferences"               },
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function getInitials(name?: string | null): string {
  if (!name) return "?";
  return name
    .split(" ")
    .filter(Boolean)
    .map((w) => w[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

// ─── UserAvatar ───────────────────────────────────────────────────────────────

interface AvatarProps { name?: string | null; size?: "xs" | "sm" | "md" }

function UserAvatar({ name, size = "sm" }: AvatarProps) {
  const dim: Record<string, string> = {
    xs: "w-6 h-6 text-[10px] rounded-lg",
    sm: "w-7 h-7 text-xs rounded-xl",
    md: "w-9 h-9 text-sm rounded-xl",
  };
  return (
    <div
      className={`${dim[size]} flex items-center justify-center font-bold text-white flex-shrink-0 select-none`}
      style={{
        background: "linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%)",
        letterSpacing: "0.02em",
      }}
    >
      {getInitials(name)}
    </div>
  );
}

// ─── NotificationBell ─────────────────────────────────────────────────────────

function NotificationBell({ count }: { count: number }) {
  return (
    <button
      aria-label="Notifications"
      className="relative w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-150"
      style={{ background: "#F9FAFB", border: "1px solid #E5E7EB", color: "#6B7280" }}
      onMouseEnter={(e) => {
        const el = e.currentTarget as HTMLElement;
        el.style.background    = "rgba(124,58,237,0.06)";
        el.style.borderColor   = "rgba(124,58,237,0.22)";
        el.style.color         = "#7C3AED";
      }}
      onMouseLeave={(e) => {
        const el = e.currentTarget as HTMLElement;
        el.style.background    = "#F9FAFB";
        el.style.borderColor   = "#E5E7EB";
        el.style.color         = "#6B7280";
      }}
    >
      <Bell style={{ width: 17, height: 17 }} />
      {count > 0 && (
        <span
          className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 rounded-full border-2 border-white flex items-center justify-center"
          style={{ background: "#EF4444", fontSize: 10, fontWeight: 700, color: "#fff", lineHeight: 1 }}
        >
          {count > 99 ? "99+" : count}
        </span>
      )}
    </button>
  );
}

// ─── DropdownItem ─────────────────────────────────────────────────────────────

interface DropdownItemProps {
  icon: ElementType;
  label: string;
  href?: string;
  danger?: boolean;
  onClick?: () => void;
}

function DropdownItem({ icon: Icon, label, href, danger = false, onClick }: DropdownItemProps) {
  const textColor = danger ? "#EF4444" : "#374151";
  const iconBg    = danger ? "rgba(239,68,68,0.08)"  : "rgba(124,58,237,0.08)";
  const iconColor = danger ? "#EF4444"               : "#7C3AED";
  const hoverBg   = danger ? "rgba(239,68,68,0.07)"  : "rgba(124,58,237,0.05)";

  const inner = (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-left transition-colors duration-100"
      style={{ color: textColor, background: "transparent" }}
      onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = hoverBg; }}
      onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = "transparent"; }}
    >
      <span
        className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
        style={{ background: iconBg }}
      >
        <Icon style={{ width: 14, height: 14, color: iconColor }} />
      </span>
      {label}
    </button>
  );

  if (href) {
    return (
      <Link href={href} onClick={onClick} style={{ display: "block" }}>
        {inner}
      </Link>
    );
  }
  return inner;
}

// ─── ProfileTrigger ───────────────────────────────────────────────────────────

interface ProfileTriggerProps {
  name?: string | null;
  open: boolean;
  triggerRef: React.RefObject<HTMLButtonElement | null>;
  onClick: () => void;
}

function ProfileTrigger({ name, open, triggerRef, onClick }: ProfileTriggerProps) {
  return (
    <button
      ref={triggerRef}
      onClick={onClick}
      aria-expanded={open}
      aria-haspopup="menu"
      className="flex items-center gap-2 pl-1.5 pr-3 py-1.5 rounded-xl transition-all duration-150"
      style={{
        background:  open ? "rgba(124,58,237,0.06)" : "#F9FAFB",
        border:      open ? "1px solid rgba(124,58,237,0.28)" : "1px solid #E5E7EB",
        outline:     "none",
      }}
      onMouseEnter={(e) => {
        if (open) return;
        const el = e.currentTarget as HTMLElement;
        el.style.background  = "rgba(124,58,237,0.04)";
        el.style.borderColor = "rgba(124,58,237,0.18)";
      }}
      onMouseLeave={(e) => {
        if (open) return;
        const el = e.currentTarget as HTMLElement;
        el.style.background  = "#F9FAFB";
        el.style.borderColor = "#E5E7EB";
      }}
    >
      <UserAvatar name={name} size="sm" />
      <span
        className="text-sm font-semibold hidden sm:block max-w-[120px] truncate"
        style={{ color: "#1E1147" }}
      >
        {name}
      </span>
      <ChevronDown
        className="hidden sm:block"
        style={{
          width:      14,
          height:     14,
          color:      "#9CA3AF",
          flexShrink: 0,
          transform:  open ? "rotate(180deg)" : "rotate(0deg)",
          transition: "transform 0.2s ease",
        }}
      />
    </button>
  );
}

// ─── ProfileMenu (fixed → immune to stacking contexts) ───────────────────────

interface MenuPos { top: number; right: number }

interface ProfileMenuProps {
  menuRef: React.RefObject<HTMLDivElement | null>;
  pos: MenuPos;
  user: { name?: string | null; email?: string | null } | null;
  onClose: () => void;
  onLogout: () => void;
}

function ProfileMenu({ menuRef, pos, user, onClose, onLogout }: ProfileMenuProps) {
  return (
    <>
      {/* Invisible full-screen backdrop – click anywhere to close */}
      <div
        aria-hidden
        style={{ position: "fixed", inset: 0, zIndex: 9998 }}
        onClick={onClose}
      />

      {/* Menu panel */}
      <div
        ref={menuRef}
        role="menu"
        aria-label="User menu"
        className="animate-fade-in"
        style={{
          position:     "fixed",
          top:          pos.top,
          right:        pos.right,
          width:        248,
          zIndex:       9999,
          background:   "#ffffff",
          borderRadius: 18,
          border:       "1px solid #E9EAEC",
          boxShadow:
            "0 0 0 1px rgba(0,0,0,0.03), " +
            "0 4px 6px -1px rgba(0,0,0,0.06), " +
            "0 20px 48px -6px rgba(0,0,0,0.14)",
          overflow: "hidden",
        }}
      >
        {/* ── User card ── */}
        <div
          className="px-4 py-4 flex items-center gap-3"
          style={{
            background:   "linear-gradient(135deg, rgba(124,58,237,0.04) 0%, rgba(167,139,250,0.02) 100%)",
            borderBottom: "1px solid #F3F4F6",
          }}
        >
          <UserAvatar name={user?.name} size="md" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-bold truncate leading-snug" style={{ color: "#1E1147" }}>
              {user?.name ?? "—"}
            </p>
            <p className="text-xs truncate mt-0.5" style={{ color: "#9CA3AF" }}>
              {user?.email ?? ""}
            </p>
          </div>
          {/* Active pill */}
          <span
            className="flex items-center gap-1 flex-shrink-0 px-2 py-0.5 rounded-full font-semibold"
            style={{ fontSize: 10, background: "rgba(16,185,129,0.10)", color: "#059669" }}
          >
            <Check style={{ width: 9, height: 9 }} strokeWidth={3} />
            Active
          </span>
        </div>

        {/* ── Navigation ── */}
        <div className="p-2 space-y-0.5">
          <DropdownItem icon={User}     label="Profile"  href="/settings" onClick={onClose} />
          <DropdownItem icon={Settings} label="Settings" href="/settings" onClick={onClose} />
        </div>

        {/* Divider */}
        <div style={{ height: 1, background: "#F3F4F6", margin: "0 12px" }} />

        {/* ── Sign out ── */}
        <div className="p-2">
          <DropdownItem
            icon={LogOut}
            label="Sign out"
            danger
            onClick={() => { onClose(); onLogout(); }}
          />
        </div>
      </div>
    </>
  );
}

// ─── Header (root export) ─────────────────────────────────────────────────────

export default function Header() {
  const pathname         = usePathname();
  const { user, logout } = useAuth();

  const [open, setOpen]       = useState(false);
  const [menuPos, setMenuPos] = useState<MenuPos>({ top: 0, right: 0 });

  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef    = useRef<HTMLDivElement>(null);

  const page = PAGE_META[pathname] ?? { title: "Flowra", subtitle: "" };

  // Notification count
  const { data: notifData } = useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn:  async () => {
      const res = await apiClient.get("/notifications/unread-count");
      return res.data;
    },
    staleTime: 60_000,
    retry:     false,
  });
  const unread = (notifData?.data?.count ?? 0) as number;

  // Toggle: calculate fixed position from the trigger's bounding rect
  const handleToggle = useCallback(() => {
    if (triggerRef.current) {
      const r = triggerRef.current.getBoundingClientRect();
      setMenuPos({
        top:   Math.round(r.bottom + 8),
        right: Math.round(window.innerWidth - r.right),
      });
    }
    setOpen((v) => !v);
  }, []);

  const handleClose = useCallback(() => setOpen(false), []);

  // Escape key
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") handleClose(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, handleClose]);

  // Re-anchor on scroll / resize so the panel follows the button
  useEffect(() => {
    if (!open) return;
    const reposition = () => {
      if (!triggerRef.current) return;
      const r = triggerRef.current.getBoundingClientRect();
      setMenuPos({
        top:   Math.round(r.bottom + 8),
        right: Math.round(window.innerWidth - r.right),
      });
    };
    window.addEventListener("scroll", reposition, true);
    window.addEventListener("resize", reposition);
    return () => {
      window.removeEventListener("scroll", reposition, true);
      window.removeEventListener("resize", reposition);
    };
  }, [open]);

  return (
    <>
      {/* ── Header bar ─────────────────────────────────────────────── */}
      <header
        className="flex items-center justify-between px-5 flex-shrink-0"
        style={{
          height:       60,
          background:   "#ffffff",
          borderRadius: 16,
          border:       "1px solid #E5E7EB",
          boxShadow:    "0 1px 3px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.02)",
        }}
      >
        {/* Page title */}
        <div>
          <h1 className="text-base font-bold leading-none tracking-tight" style={{ color: "#1E1147" }}>
            {page.title}
          </h1>
          {page.subtitle && (
            <p className="text-xs mt-0.5 font-medium" style={{ color: "#9CA3AF" }}>
              {page.subtitle}
            </p>
          )}
        </div>

        {/* Right controls */}
        <div className="flex items-center gap-2">
          <NotificationBell count={unread} />
          <ProfileTrigger
            name={user?.name}
            open={open}
            triggerRef={triggerRef}
            onClick={handleToggle}
          />
        </div>
      </header>

      {/* ── Dropdown — fixed position, above everything ─────────────── */}
      {open && (
        <ProfileMenu
          menuRef={menuRef}
          pos={menuPos}
          user={user}
          onClose={handleClose}
          onLogout={logout}
        />
      )}
    </>
  );
}
