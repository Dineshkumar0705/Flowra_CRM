"use client";

import React, { useState } from "react";
import {
  MessageSquare, Mail, Calendar, Bot, BellRing, IndianRupee,
  CheckCircle2, ArrowRight, ToggleRight, ToggleLeft,
  TrendingUp, RefreshCw, Settings2, Sparkles, Shield,
  Send, Layers, Link2, CreditCard, Bell
} from "lucide-react";

/* ─── Integration Data ──────────────────────────────────────── */
interface Integration {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: any;
  color: string;
  gradientFrom: string;
  gradientTo: string;
  status: "live" | "syncing" | "idle";
  stats: { label: string; value: string }[];
  features: string[];
  lastSync?: string;
}

const INTEGRATIONS: Integration[] = [
  {
    id: "whatsapp",
    name: "WhatsApp Business",
    description: "Send messages, automations & follow-ups directly from your CRM pipeline.",
    category: "Messaging",
    icon: MessageSquare,
    color: "#25D366",
    gradientFrom: "#25D366",
    gradientTo: "#128C7E",
    status: "live",
    stats: [
      { label: "Messages Sent", value: "1,284" },
      { label: "Open Rate", value: "98.2%" },
      { label: "Templates", value: "12" },
    ],
    features: ["Automated follow-ups", "Template messages", "Contact sync", "Read receipts"],
    lastSync: "Just now",
  },
  {
    id: "gmail",
    name: "Gmail",
    description: "Two-way email sync, automated sequences, and inbox-to-CRM contact capture.",
    category: "Email",
    icon: Mail,
    color: "#EA4335",
    gradientFrom: "#EA4335",
    gradientTo: "#FBBC05",
    status: "live",
    stats: [
      { label: "Emails Synced", value: "4,730" },
      { label: "Sequences", value: "8" },
      { label: "Open Rate", value: "42.1%" },
    ],
    features: ["Inbox sync", "Email sequences", "Lead capture", "Thread tracking"],
    lastSync: "2 min ago",
  },
  {
    id: "calendar",
    name: "Google Calendar",
    description: "Sync meetings, auto-create deal touchpoints, and schedule follow-ups with one click.",
    category: "Calendar",
    icon: Calendar,
    color: "#4285F4",
    gradientFrom: "#4285F4",
    gradientTo: "#34A853",
    status: "syncing",
    stats: [
      { label: "Events Synced", value: "312" },
      { label: "Meetings", value: "47" },
      { label: "Reminders", value: "89" },
    ],
    features: ["2-way calendar sync", "Meeting scheduling", "Deal touchpoints", "Team availability"],
    lastSync: "Syncing…",
  },
  {
    id: "autopilot",
    name: "Autopilot",
    description: "AI-powered automation engine — stale deal alerts, re-engagement flows, and smart routing.",
    category: "Automation",
    icon: Bot,
    color: "#7C3AED",
    gradientFrom: "#7C3AED",
    gradientTo: "#A78BFA",
    status: "live",
    stats: [
      { label: "Automations", value: "24" },
      { label: "Deals Revived", value: "37" },
      { label: "Time Saved", value: "18h/wk" },
    ],
    features: ["Stale deal alerts", "AI lead scoring", "Smart routing", "Re-engagement flows"],
    lastSync: "5 min ago",
  },
  {
    id: "razorpay",
    name: "Razorpay",
    description: "Track payments, invoices, and subscription revenue directly in your deal pipeline.",
    category: "Payments",
    icon: IndianRupee,
    color: "#2D8CFF",
    gradientFrom: "#2D8CFF",
    gradientTo: "#0050C8",
    status: "live",
    stats: [
      { label: "Revenue Tracked", value: "₹38.4L" },
      { label: "Invoices", value: "214" },
      { label: "Success Rate", value: "97.8%" },
    ],
    features: ["Payment tracking", "Invoice generation", "Subscription sync", "Refund handling"],
    lastSync: "12 min ago",
  },
  {
    id: "notifications",
    name: "In-App Notifications",
    description: "Real-time alerts for deal updates, contact activity, and pipeline changes.",
    category: "Notifications",
    icon: BellRing,
    color: "#F59E0B",
    gradientFrom: "#F59E0B",
    gradientTo: "#EF4444",
    status: "live",
    stats: [
      { label: "Sent Today", value: "143" },
      { label: "Read Rate", value: "91.4%" },
      { label: "Rules", value: "17" },
    ],
    features: ["Instant alerts", "Custom rules", "Push notifications", "Digest emails"],
    lastSync: "Live",
  },
];

const ALL_CATEGORIES = ["All", "Messaging", "Email", "Calendar", "Automation", "Payments", "Notifications"];

const CATEGORY_ICONS: Record<string, any> = {
  All: Layers,
  Messaging: MessageSquare,
  Email: Mail,
  Calendar: Calendar,
  Automation: Bot,
  Payments: CreditCard,
  Notifications: Bell,
};

const HOW_IT_WORKS = [
  {
    step: "01",
    icon: Link2,
    title: "Connect Your Apps",
    desc: "Securely authenticate each integration with OAuth or API keys. Zero code required.",
    color: "#7C3AED",
  },
  {
    step: "02",
    icon: RefreshCw,
    title: "Auto-Sync Data",
    desc: "Contacts, deals, emails, and calendar events flow in real time into your CRM.",
    color: "#3B82F6",
  },
  {
    step: "03",
    icon: Bot,
    title: "Autopilot Runs Rules",
    desc: "AI triggers automations — follow-ups, alerts, and re-engagements — automatically.",
    color: "#10B981",
  },
  {
    step: "04",
    icon: TrendingUp,
    title: "Watch Revenue Grow",
    desc: "Every touchpoint tracked, every deal accelerated. Close faster with less manual work.",
    color: "#F59E0B",
  },
];

const ACTIVITY = [
  { icon: MessageSquare, color: "#25D366", text: "WhatsApp follow-up sent to Arjun Sharma", time: "Just now" },
  { icon: Bot,           color: "#7C3AED", text: "Autopilot revived 3 stale deals",          time: "4m ago"  },
  { icon: Mail,          color: "#EA4335", text: "Gmail sequence triggered for Priya Nair",  time: "11m ago" },
  { icon: IndianRupee,   color: "#2D8CFF", text: "Razorpay payment ₹2.4L confirmed",         time: "23m ago" },
  { icon: Calendar,      color: "#4285F4", text: "Google Calendar meeting synced — Infosys", time: "1h ago"  },
  { icon: BellRing,      color: "#F59E0B", text: "Notification rule triggered — hot lead",   time: "2h ago"  },
];

/* ─── IntegrationCard ────────────────────────────────────────── */
function IntegrationCard({ intg }: { intg: Integration }) {
  const [enabled, setEnabled] = useState(true);
  const Icon = intg.icon;
  const statusColor = intg.status === "live" ? "#10B981" : intg.status === "syncing" ? "#3B82F6" : "#9CA3AF";
  const statusLabel = intg.status === "live" ? "Live" : intg.status === "syncing" ? "Syncing" : "Idle";

  return (
    <div
      className="rounded-2xl overflow-hidden transition-all duration-300 cursor-default"
      style={{
        background: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        boxShadow: "0 2px 12px rgba(26,15,58,0.04)",
      }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLElement).style.boxShadow = `0 12px 40px ${intg.color}22, 0 2px 12px rgba(26,15,58,0.06)`;
        (e.currentTarget as HTMLElement).style.transform = "translateY(-2px)";
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLElement).style.boxShadow = "0 2px 12px rgba(26,15,58,0.04)";
        (e.currentTarget as HTMLElement).style.transform = "translateY(0)";
      }}
    >
      {/* Gradient top accent */}
      <div className="h-1 w-full" style={{ background: `linear-gradient(90deg, ${intg.gradientFrom}, ${intg.gradientTo})` }} />

      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div
              className="w-11 h-11 rounded-2xl flex items-center justify-center flex-shrink-0 relative"
              style={{
                background: `linear-gradient(135deg, ${intg.gradientFrom}20, ${intg.gradientTo}15)`,
                border: `1.5px solid ${intg.color}30`,
              }}
            >
              <Icon className="w-5 h-5" style={{ color: intg.color }} />
              <span
                className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full border-2 border-white"
                style={{ background: "#10B981" }}
              />
            </div>
            <div>
              <p className="font-bold text-sm" style={{ color: "var(--color-text)" }}>{intg.name}</p>
              <span
                className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                style={{ background: `${intg.color}15`, color: intg.color }}
              >
                {intg.category}
              </span>
            </div>
          </div>
          <button
            onClick={() => setEnabled(!enabled)}
            className="transition-all"
            style={{ color: enabled ? "#10B981" : "#9CA3AF" }}
          >
            {enabled
              ? <ToggleRight className="w-6 h-6" />
              : <ToggleLeft className="w-6 h-6" />
            }
          </button>
        </div>

        <p className="text-xs leading-relaxed mb-4" style={{ color: "var(--color-text-secondary)" }}>
          {intg.description}
        </p>

        {/* Stats */}
        <div
          className="grid grid-cols-3 gap-2 mb-4 p-3 rounded-xl"
          style={{ background: `${intg.color}08`, border: `1px solid ${intg.color}15` }}
        >
          {intg.stats.map(s => (
            <div key={s.label} className="text-center">
              <p className="text-sm font-extrabold" style={{ color: intg.color }}>{s.value}</p>
              <p className="text-[10px] mt-0.5" style={{ color: "var(--color-text-secondary)" }}>{s.label}</p>
            </div>
          ))}
        </div>

        {/* Feature chips */}
        <div className="flex flex-wrap gap-1.5 mb-4">
          {intg.features.map(f => (
            <span
              key={f}
              className="text-[10px] font-medium px-2 py-1 rounded-lg"
              style={{
                background: "rgba(139,92,246,0.07)",
                color: "var(--color-text-secondary)",
                border: "1px solid rgba(139,92,246,0.12)",
              }}
            >
              {f}
            </span>
          ))}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-3" style={{ borderTop: "1px solid var(--color-border)" }}>
          <div className="flex items-center gap-1.5">
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: statusColor, boxShadow: `0 0 6px ${statusColor}` }}
            />
            <span className="text-xs font-medium" style={{ color: statusColor }}>{statusLabel}</span>
            {intg.lastSync && (
              <span className="text-xs" style={{ color: "var(--color-text-muted)" }}>· {intg.lastSync}</span>
            )}
          </div>
          <button
            className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all"
            style={{ background: `${intg.color}15`, color: intg.color, border: `1px solid ${intg.color}25` }}
            onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = `${intg.color}28`}
            onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = `${intg.color}15`}
          >
            <Settings2 className="w-3 h-3" /> Configure
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─── Page ───────────────────────────────────────────────────── */
export default function IntegrationsPage() {
  const [activeCategory, setActiveCategory] = useState("All");

  const filtered = activeCategory === "All"
    ? INTEGRATIONS
    : INTEGRATIONS.filter(i => i.category === activeCategory);

  return (
    <div className="space-y-5 animate-fade-in">

      {/* ── Hero ────────────────────────────────────────────────── */}
      <div
        className="rounded-2xl overflow-hidden relative"
        style={{
          background: "linear-gradient(135deg, #1A0F3A 0%, #2D1B69 50%, #1e1040 100%)",
          border: "1px solid rgba(167,139,250,0.2)",
          boxShadow: "0 20px 60px rgba(124,58,237,0.2)",
        }}
      >
        <div className="absolute top-0 right-0 w-64 h-64 rounded-full opacity-20 blur-3xl" style={{ background: "#7C3AED" }} />
        <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full opacity-15 blur-3xl" style={{ background: "#3B82F6" }} />

        <div className="relative px-6 py-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-7 h-7 rounded-xl flex items-center justify-center" style={{ background: "rgba(167,139,250,0.2)" }}>
                <Sparkles className="w-3.5 h-3.5" style={{ color: "#C4B5FD" }} />
              </div>
              <span className="text-xs font-semibold" style={{ color: "#A78BFA" }}>
                Pro Plan · All Integrations Unlocked
              </span>
            </div>
            <h2 className="text-xl font-extrabold text-white tracking-tight">Connected Ecosystem</h2>
            <p className="text-sm mt-1" style={{ color: "rgba(196,181,253,0.7)" }}>
              6 apps running in harmony — your CRM on autopilot.
            </p>
          </div>

          <div className="flex flex-wrap gap-2.5">
            {[
              { label: "Active Apps",      value: "6/6",     icon: CheckCircle2, color: "#10B981" },
              { label: "Messages/day",     value: "847",     icon: Send,         color: "#25D366" },
              { label: "Automations live", value: "24",      icon: Bot,          color: "#A78BFA" },
              { label: "Revenue tracked",  value: "₹38.4L",  icon: IndianRupee,  color: "#2D8CFF" },
            ].map(({ label, value, icon: Icon, color }) => (
              <div
                key={label}
                className="px-3 py-2 rounded-xl flex items-center gap-2"
                style={{ background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.12)" }}
              >
                <Icon className="w-3.5 h-3.5 flex-shrink-0" style={{ color }} />
                <div>
                  <p className="text-xs font-bold text-white">{value}</p>
                  <p className="text-[10px]" style={{ color: "rgba(196,181,253,0.6)" }}>{label}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Category Tabs ────────────────────────────────────────── */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {ALL_CATEGORIES.map(cat => {
          const CatIcon = CATEGORY_ICONS[cat];
          const isActive = cat === activeCategory;
          const count = cat === "All" ? INTEGRATIONS.length : INTEGRATIONS.filter(i => i.category === cat).length;
          return (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all duration-200 flex-shrink-0"
              style={{
                background: isActive ? "linear-gradient(135deg, #7C3AED, #A78BFA)" : "var(--color-surface)",
                color: isActive ? "#fff" : "var(--color-text-secondary)",
                border: isActive ? "1px solid transparent" : "1px solid var(--color-border)",
                boxShadow: isActive ? "0 4px 14px rgba(124,58,237,0.3)" : "none",
              }}
            >
              <CatIcon className="w-3.5 h-3.5" />
              {cat}
              <span
                className="px-1.5 py-0.5 rounded-full text-[10px] font-bold"
                style={{
                  background: isActive ? "rgba(255,255,255,0.25)" : "rgba(139,92,246,0.1)",
                  color: isActive ? "#fff" : "#7C3AED",
                }}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* ── Integration Cards Grid ───────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map(intg => (
          <IntegrationCard key={intg.id} intg={intg} />
        ))}
      </div>

      {/* ── How It Works ─────────────────────────────────────────── */}
      <div
        className="rounded-2xl p-6"
        style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)" }}
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="font-bold text-base" style={{ color: "var(--color-text)" }}>How Your Integrations Work</h3>
            <p className="text-xs mt-0.5" style={{ color: "var(--color-text-secondary)" }}>
              Everything runs automatically once connected
            </p>
          </div>
          <div
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold"
            style={{ background: "rgba(16,185,129,0.1)", color: "#10B981", border: "1px solid rgba(16,185,129,0.2)" }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            All systems live
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 relative">
          {/* connector line */}
          <div
            className="absolute top-8 left-[14%] right-[14%] h-px hidden lg:block"
            style={{ background: "linear-gradient(90deg, #7C3AED44, #A78BFA88, #3B82F644, #10B98144)" }}
          />

          {HOW_IT_WORKS.map((step, i) => {
            const StepIcon = step.icon;
            return (
              <div key={step.step} className="flex flex-col items-center text-center relative z-10">
                <div
                  className="w-14 h-14 rounded-2xl flex items-center justify-center mb-3 relative"
                  style={{
                    background: `linear-gradient(135deg, ${step.color}18, ${step.color}0a)`,
                    border: `2px solid ${step.color}35`,
                  }}
                >
                  <StepIcon className="w-5 h-5" style={{ color: step.color }} />
                  <span
                    className="absolute -top-2 -right-2 w-5 h-5 rounded-full flex items-center justify-center text-[9px] font-black text-white"
                    style={{ background: step.color }}
                  >
                    {step.step}
                  </span>
                </div>
                <p className="font-bold text-sm mb-1.5" style={{ color: "var(--color-text)" }}>{step.title}</p>
                <p className="text-xs leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>{step.desc}</p>
                {i < HOW_IT_WORKS.length - 1 && (
                  <ArrowRight
                    className="absolute right-0 top-7 w-4 h-4 hidden lg:block -mr-3"
                    style={{ color: "rgba(139,92,246,0.35)" }}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Bottom Row ───────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Activity Feed */}
        <div
          className="lg:col-span-2 rounded-2xl p-5"
          style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)" }}
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-bold text-base" style={{ color: "var(--color-text)" }}>Integration Activity</h3>
              <p className="text-xs mt-0.5" style={{ color: "var(--color-text-secondary)" }}>Real-time events across all connected apps</p>
            </div>
            <span
              className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full"
              style={{ background: "rgba(16,185,129,0.1)", color: "#10B981" }}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Live
            </span>
          </div>

          <div>
            {ACTIVITY.map((item, i) => {
              const ItemIcon = item.icon;
              return (
                <div
                  key={i}
                  className="flex items-center gap-3 py-2.5 border-b last:border-0"
                  style={{ borderColor: "var(--color-border)" }}
                >
                  <div
                    className="w-7 h-7 rounded-xl flex items-center justify-center flex-shrink-0"
                    style={{ background: `${item.color}15`, border: `1px solid ${item.color}25` }}
                  >
                    <ItemIcon className="w-3.5 h-3.5" style={{ color: item.color }} />
                  </div>
                  <p className="flex-1 text-xs" style={{ color: "var(--color-text)" }}>{item.text}</p>
                  <span className="text-xs flex-shrink-0" style={{ color: "var(--color-text-muted)" }}>{item.time}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Security & Trust */}
        <div
          className="rounded-2xl p-5 flex flex-col"
          style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)" }}
        >
          <div className="flex items-center gap-2 mb-4">
            <div
              className="w-8 h-8 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(16,185,129,0.12)", border: "1px solid rgba(16,185,129,0.2)" }}
            >
              <Shield className="w-4 h-4" style={{ color: "#10B981" }} />
            </div>
            <div>
              <h3 className="font-bold text-sm" style={{ color: "var(--color-text)" }}>Security & Trust</h3>
              <p className="text-[10px]" style={{ color: "var(--color-text-secondary)" }}>Enterprise-grade protection</p>
            </div>
          </div>

          {[
            "OAuth 2.0 Authentication",
            "AES-256 Encryption",
            "GDPR Compliant",
            "API Rate Limiting",
            "Audit Logs",
            "Data Residency (India)",
          ].map(label => (
            <div
              key={label}
              className="flex items-center gap-2.5 py-2 border-b last:border-0"
              style={{ borderColor: "var(--color-border)" }}
            >
              <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" style={{ color: "#10B981" }} />
              <span className="text-xs" style={{ color: "var(--color-text-secondary)" }}>{label}</span>
            </div>
          ))}

          <div
            className="mt-auto pt-4 p-3 rounded-xl text-center"
            style={{
              background: "linear-gradient(135deg, rgba(124,58,237,0.1), rgba(167,139,250,0.07))",
              border: "1px solid rgba(124,58,237,0.15)",
            }}
          >
            <p className="text-xs font-bold" style={{ color: "#7C3AED" }}>ISO 27001 Certified</p>
            <p className="text-[10px] mt-0.5" style={{ color: "var(--color-text-secondary)" }}>
              Your data is safe and compliant
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
