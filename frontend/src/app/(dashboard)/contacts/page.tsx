"use client";

/**
 * Contacts Page — Flowra CRM
 * Full CRUD table with lead_status lifecycle, source filters, bulk select,
 * AI rescore, and a slide-over drawer for create/edit.
 */

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus, Search, X, Users, Mail, Phone,
  Building2, Zap, Edit2, Trash2,
  TrendingUp, Star, Download, CheckCircle2,
  Filter, ChevronDown,
} from "lucide-react";
import apiClient from "@/services/apiClient";
import { Contact, LeadStatus } from "@/types";
import { toast } from "sonner";

// ─── Design tokens ─────────────────────────────────────────────────────────

const T = {
  accent:      "#7C3AED",
  accentLight: "rgba(124,58,237,0.07)",
  accentBorder:"rgba(124,58,237,0.18)",
  border:      "rgba(139,92,246,0.12)",
  borderSub:   "rgba(139,92,246,0.06)",
  text:        "var(--color-text)",
  textSub:     "var(--color-text-secondary)",
  textMuted:   "var(--color-text-muted)",
  surface:     "var(--color-surface)",
} as const;

// ─── Metadata maps ─────────────────────────────────────────────────────────

const SOURCE_META: Record<string, { label: string; color: string; bg: string }> = {
  manual:   { label: "Manual",   color: "#7C3AED", bg: "rgba(124,58,237,0.10)"  },
  import:   { label: "Import",   color: "#6B7280", bg: "rgba(107,114,128,0.10)" },
  whatsapp: { label: "WhatsApp", color: "#10B981", bg: "rgba(16,185,129,0.10)"  },
  gmail:    { label: "Gmail",    color: "#3B82F6", bg: "rgba(59,130,246,0.10)"  },
  web_form: { label: "Web Form", color: "#F59E0B", bg: "rgba(245,158,11,0.10)"  },
  referral: { label: "Referral", color: "#EC4899", bg: "rgba(236,72,153,0.10)"  },
};

const LEAD_STATUS_META: Record<LeadStatus, { label: string; color: string; bg: string; dot: string }> = {
  new:       { label: "New",       color: "#3B82F6", bg: "rgba(59,130,246,0.10)",  dot: "#3B82F6" },
  contacted: { label: "Contacted", color: "#8B5CF6", bg: "rgba(139,92,246,0.10)", dot: "#8B5CF6" },
  qualified: { label: "Qualified", color: "#F59E0B", bg: "rgba(245,158,11,0.10)",  dot: "#F59E0B" },
  converted: { label: "Converted", color: "#10B981", bg: "rgba(16,185,129,0.10)", dot: "#10B981" },
  lost:      { label: "Lost",      color: "#EF4444", bg: "rgba(239,68,68,0.10)",   dot: "#EF4444" },
};

const ALL_SOURCES    = ["all", ...Object.keys(SOURCE_META)];
const LEAD_STATUSES  = Object.keys(LEAD_STATUS_META) as LeadStatus[];

function scoreColor(s: number) {
  return s >= 70 ? "#10B981" : s >= 40 ? "#F59E0B" : "#EF4444";
}

// ─── Reusable atoms ────────────────────────────────────────────────────────

function ContactAvatar({ contact }: { contact: Contact }) {
  const src = SOURCE_META[contact.source]?.color ?? "#7C3AED";
  const initials = [contact.first_name, contact.last_name]
    .filter(Boolean).map(s => s![0].toUpperCase()).join("").slice(0, 2) || "?";
  return (
    <div
      className="w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold text-white flex-shrink-0 select-none"
      style={{ background: `linear-gradient(135deg, ${src}, #A78BFA)` }}
    >
      {initials}
    </div>
  );
}

function ScoreBar({ score }: { score: number }) {
  const c = scoreColor(score);
  return (
    <div className="flex items-center gap-2 min-w-[90px]">
      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(139,92,246,0.1)" }}>
        <div
          className="h-full rounded-full"
          style={{ width: `${score}%`, background: `linear-gradient(90deg, ${c}88, ${c})` }}
        />
      </div>
      <span className="text-xs font-bold tabular-nums w-6 text-right" style={{ color: c }}>{score}</span>
    </div>
  );
}

function SourceChip({ source }: { source: string }) {
  const m = SOURCE_META[source] ?? SOURCE_META.manual;
  return (
    <span className="text-[11px] px-2.5 py-1 rounded-full font-semibold whitespace-nowrap"
      style={{ background: m.bg, color: m.color }}>
      {m.label}
    </span>
  );
}

function LeadStatusBadge({ status }: { status: LeadStatus }) {
  const m = LEAD_STATUS_META[status] ?? LEAD_STATUS_META.new;
  return (
    <span
      className="inline-flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-full font-semibold whitespace-nowrap"
      style={{ background: m.bg, color: m.color }}
    >
      <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: m.dot }} />
      {m.label}
    </span>
  );
}

function TagChip({ label }: { label: string }) {
  return (
    <span className="text-[10px] px-2 py-0.5 rounded-full font-medium"
      style={{ background: "rgba(124,58,237,0.09)", color: "var(--color-primary)" }}>
      {label}
    </span>
  );
}

function StatPill({ icon: Icon, label, value, color }: { icon: any; label: string; value: string | number; color: string }) {
  return (
    <div
      className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl"
      style={{ background: T.surface, border: `1px solid ${T.border}` }}
    >
      <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: `${color}15` }}>
        <Icon className="w-3.5 h-3.5" style={{ color }} />
      </div>
      <div>
        <p className="text-sm font-extrabold leading-none" style={{ color: T.text }}>{value}</p>
        <p className="text-[10px] mt-0.5 font-medium" style={{ color: T.textSub }}>{label}</p>
      </div>
    </div>
  );
}

function ActionBtn({ icon: Icon, title, hoverColor, onClick }: { icon: any; title: string; hoverColor: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      title={title}
      className="w-7 h-7 rounded-lg flex items-center justify-center transition-all duration-150"
      style={{ color: T.textMuted }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLElement).style.background = `${hoverColor}18`;
        (e.currentTarget as HTMLElement).style.color = hoverColor;
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLElement).style.background = "transparent";
        (e.currentTarget as HTMLElement).style.color = T.textMuted as string;
      }}
    >
      <Icon className="w-3.5 h-3.5" />
    </button>
  );
}

function SkeletonRow() {
  return (
    <tr style={{ borderBottom: `1px solid ${T.borderSub}` }}>
      {[10, 140, 100, 110, 90, 80, 90, 80, 60].map((w, i) => (
        <td key={i} className="px-4 py-4">
          <div className="h-3 rounded-full animate-pulse" style={{ width: i === 0 ? 16 : w, background: "rgba(139,92,246,0.08)" }} />
        </td>
      ))}
    </tr>
  );
}

// ─── ContactDrawer ─────────────────────────────────────────────────────────

interface DrawerProps {
  contact?: Contact | null;
  onClose: () => void;
  onSave: (data: any) => void;
}

function ContactDrawer({ contact, onClose, onSave }: DrawerProps) {
  const [form, setForm] = useState({
    first_name:   contact?.first_name   ?? "",
    last_name:    contact?.last_name    ?? "",
    email:        contact?.email        ?? "",
    phone:        contact?.phone        ?? "",
    company_name: contact?.company_name ?? "",
    job_title:    contact?.job_title    ?? "",
    source:       contact?.source       ?? "manual",
    lead_status:  (contact?.lead_status ?? "new") as LeadStatus,
    tags:         contact?.tags?.join(", ") ?? "",
  });

  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));

  const inputStyle: React.CSSProperties = {
    background: "rgba(242,238,255,0.85)",
    border: "1px solid rgba(139,92,246,0.18)",
    color: "var(--color-text)",
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.first_name.trim()) return;
    onSave({
      first_name:   form.first_name.trim(),
      last_name:    form.last_name.trim()    || undefined,
      email:        form.email               || undefined,
      phone:        form.phone               || undefined,
      company_name: form.company_name        || undefined,
      job_title:    form.job_title           || undefined,
      source:       form.source,
      lead_status:  form.lead_status,
      tags:         form.tags.split(",").map((t: string) => t.trim()).filter(Boolean),
    });
  };

  const SectionLabel = ({ children }: { children: string }) => (
    <p className="text-[10px] font-bold uppercase tracking-widest mb-3"
      style={{ color: "var(--color-text-secondary)" }}>{children}</p>
  );

  const Field = ({ label, fieldKey, placeholder, type = "text", required = false }: {
    label: string; fieldKey: string; placeholder?: string; type?: string; required?: boolean;
  }) => (
    <div>
      <label className="block text-xs font-semibold mb-1.5" style={{ color: "var(--color-text-secondary)" }}>
        {label}{required && <span className="text-red-400 ml-0.5">*</span>}
      </label>
      <input
        type={type}
        placeholder={placeholder}
        value={(form as any)[fieldKey]}
        onChange={e => set(fieldKey, e.target.value)}
        required={required}
        className="w-full px-3.5 py-2.5 rounded-xl text-sm transition-all focus:outline-none focus:ring-2 focus:ring-violet-400/40"
        style={inputStyle}
      />
    </div>
  );

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-black/25 backdrop-blur-sm" onClick={onClose} />
      <div
        className="w-[440px] h-full flex flex-col"
        style={{
          background: "#f9f6ff",
          borderLeft: "1px solid rgba(139,92,246,0.14)",
          boxShadow: "-24px 0 64px rgba(26,15,58,0.18)",
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5"
          style={{ borderBottom: "1px solid rgba(139,92,246,0.10)" }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(124,58,237,0.12)" }}>
              <Users className="w-4 h-4" style={{ color: "#7C3AED" }} />
            </div>
            <div>
              <h2 className="font-bold text-base leading-none" style={{ color: "var(--color-text)" }}>
                {contact ? "Edit Contact" : "New Contact"}
              </h2>
              <p className="text-xs mt-0.5" style={{ color: "var(--color-text-secondary)" }}>
                {contact ? "Update contact details" : "Add to your CRM"}
              </p>
            </div>
          </div>
          <button onClick={onClose}
            className="w-8 h-8 rounded-xl flex items-center justify-center transition-all"
            style={{ background: "rgba(139,92,246,0.08)" }}
            onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "rgba(239,68,68,0.10)"}
            onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "rgba(139,92,246,0.08)"}>
            <X className="w-4 h-4" style={{ color: "var(--color-text-secondary)" }} />
          </button>
        </div>

        {/* Form */}
        <form id="contact-form" onSubmit={handleSubmit}
          className="flex-1 overflow-y-auto px-6 py-5 space-y-5">

          <div>
            <SectionLabel>Basic Info</SectionLabel>
            <div className="grid grid-cols-2 gap-3">
              <Field label="First Name" fieldKey="first_name" placeholder="Arjun" required />
              <Field label="Last Name"  fieldKey="last_name"  placeholder="Sharma" />
            </div>
          </div>

          <div>
            <SectionLabel>Contact Info</SectionLabel>
            <div className="space-y-3">
              <Field label="Email" fieldKey="email" placeholder="arjun@company.com" type="email" />
              <Field label="Phone" fieldKey="phone" placeholder="+91 98765 43210" />
            </div>
          </div>

          <div>
            <SectionLabel>Work Details</SectionLabel>
            <div className="space-y-3">
              <Field label="Company"   fieldKey="company_name" placeholder="Tata Consultancy" />
              <Field label="Job Title" fieldKey="job_title"    placeholder="Product Manager" />
            </div>
          </div>

          <div>
            <SectionLabel>CRM Details</SectionLabel>
            <div className="space-y-4">

              {/* Lead Status */}
              <div>
                <label className="block text-xs font-semibold mb-2"
                  style={{ color: "var(--color-text-secondary)" }}>
                  Lead Status
                </label>
                <div className="flex flex-wrap gap-2">
                  {LEAD_STATUSES.map(s => {
                    const m = LEAD_STATUS_META[s];
                    const active = form.lead_status === s;
                    return (
                      <button
                        key={s}
                        type="button"
                        onClick={() => set("lead_status", s)}
                        className="flex items-center gap-1.5 text-[11px] px-2.5 py-1.5 rounded-full font-semibold transition-all"
                        style={{
                          background: active ? m.color : m.bg,
                          color:      active ? "#fff"  : m.color,
                          border:     `1px solid ${active ? m.color : "transparent"}`,
                        }}
                      >
                        <span className="w-1.5 h-1.5 rounded-full" style={{ background: active ? "#fff" : m.dot }} />
                        {m.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Source */}
              <div>
                <label className="block text-xs font-semibold mb-2"
                  style={{ color: "var(--color-text-secondary)" }}>
                  Source
                </label>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(SOURCE_META).map(([k, v]) => (
                    <button
                      key={k}
                      type="button"
                      onClick={() => set("source", k)}
                      className="text-[11px] px-2.5 py-1 rounded-full font-semibold transition-all"
                      style={{
                        background: form.source === k ? v.color : v.bg,
                        color:      form.source === k ? "#fff"   : v.color,
                        border:     `1px solid ${form.source === k ? v.color : "transparent"}`,
                      }}
                    >
                      {v.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tags */}
              <div>
                <label className="block text-xs font-semibold mb-1.5"
                  style={{ color: "var(--color-text-secondary)" }}>
                  Tags <span className="font-normal opacity-60">(comma separated)</span>
                </label>
                <input
                  type="text"
                  placeholder="vip, hot-lead, enterprise"
                  value={form.tags}
                  onChange={e => set("tags", e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl text-sm transition-all focus:outline-none focus:ring-2 focus:ring-violet-400/40"
                  style={inputStyle}
                />
                {form.tags && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {form.tags.split(",").map(t => t.trim()).filter(Boolean).map(t => (
                      <TagChip key={t} label={t} />
                    ))}
                  </div>
                )}
              </div>

            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="px-6 py-4 flex gap-3"
          style={{ borderTop: "1px solid rgba(139,92,246,0.10)" }}>
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-all"
            style={{ border: "1px solid rgba(139,92,246,0.20)", color: "var(--color-text-secondary)" }}
            onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "rgba(139,92,246,0.05)"}
            onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "transparent"}
          >
            Cancel
          </button>
          <button
            type="submit"
            form="contact-form"
            className="flex-1 py-2.5 rounded-xl text-sm font-bold text-white transition-all"
            style={{ background: "linear-gradient(135deg, #7C3AED, #A78BFA)" }}
            onMouseEnter={e => (e.currentTarget as HTMLElement).style.opacity = "0.88"}
            onMouseLeave={e => (e.currentTarget as HTMLElement).style.opacity = "1"}
          >
            {contact ? "Save Changes" : "Add Contact"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Page ──────────────────────────────────────────────────────────────────

export default function ContactsPage() {
  const qc = useQueryClient();
  const [search,        setSearch]    = useState("");
  const [sourceFilter,  setSource]    = useState("all");
  const [statusFilter,  setStatus]    = useState<"all" | LeadStatus>("all");
  const [selected,      setSelected]  = useState<Set<string>>(new Set());
  const [drawerOpen,    setDrawerOpen]= useState(false);
  const [editing,       setEditing]   = useState<Contact | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["contacts", search],
    queryFn: async () => {
      const r = await apiClient.get("/contacts", { params: { search, page_size: 200 } });
      return r.data?.data as Contact[];
    },
    staleTime: 30_000,
  });

  const contacts: Contact[] = data ?? [];

  // Client-side filtering
  const visible = contacts.filter(c => {
    if (sourceFilter !== "all" && c.source !== sourceFilter) return false;
    if (statusFilter !== "all" && c.lead_status !== statusFilter) return false;
    return true;
  });

  // Counts for filter pills
  const sourceCounts = Object.keys(SOURCE_META).reduce((acc, s) => {
    acc[s] = contacts.filter(c => c.source === s).length;
    return acc;
  }, {} as Record<string, number>);

  const statusCounts = LEAD_STATUSES.reduce((acc, s) => {
    acc[s] = contacts.filter(c => c.lead_status === s).length;
    return acc;
  }, {} as Record<string, number>);

  const avgScore = visible.length ? Math.round(visible.reduce((a, c) => a + c.lead_score, 0) / visible.length) : 0;
  const hotLeads = visible.filter(c => c.lead_score >= 70).length;

  // Mutations
  const createMut = useMutation({
    mutationFn: (d: any) => apiClient.post("/contacts", d),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["contacts"] }); setDrawerOpen(false); toast.success("Contact added!"); },
    onError: () => toast.error("Failed to add contact"),
  });
  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => apiClient.patch(`/contacts/${id}`, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["contacts"] }); setEditing(null); toast.success("Contact updated!"); },
    onError: () => toast.error("Failed to update"),
  });
  const deleteMut = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/contacts/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["contacts"] }); toast.success("Deleted"); },
    onError: () => toast.error("Failed to delete"),
  });
  const rescoreMut = useMutation({
    mutationFn: (id: string) => apiClient.post(`/contacts/${id}/rescore`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["contacts"] }); toast.success("AI rescore complete!"); },
  });

  // Bulk select helpers
  const allSelected = visible.length > 0 && visible.every(c => selected.has(c.id));
  const toggleAll   = () => setSelected(allSelected ? new Set() : new Set(visible.map(c => c.id)));
  const toggleOne   = (id: string) => setSelected(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n; });

  const TH = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <th className={`px-4 py-3.5 text-left text-[11px] font-bold uppercase tracking-wider ${className}`}
      style={{ color: "var(--color-text-secondary)" }}>
      {children}
    </th>
  );

  const openCreate = () => { setEditing(null); setDrawerOpen(true); };
  const openEdit   = (c: Contact) => { setEditing(c); setDrawerOpen(true); };
  const closeDrawer = () => { setDrawerOpen(false); setEditing(null); };

  return (
    <div className="space-y-4 animate-fade-in">

      {/* ── Top bar ─────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-extrabold" style={{ color: T.text }}>Contacts</h2>
          <p className="text-xs mt-0.5" style={{ color: T.textSub }}>
            {visible.length} contact{visible.length !== 1 ? "s" : ""}
            {statusFilter !== "all" && ` · ${LEAD_STATUS_META[statusFilter]?.label}`}
            {sourceFilter !== "all" && ` · ${SOURCE_META[sourceFilter]?.label}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="flex items-center gap-2 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all"
            style={{ background: T.surface, border: `1px solid ${T.border}`, color: T.textSub }}
            onMouseEnter={e => (e.currentTarget as HTMLElement).style.borderColor = "rgba(124,58,237,0.4)"}
            onMouseLeave={e => (e.currentTarget as HTMLElement).style.borderColor = T.border as string}
          >
            <Download className="w-4 h-4" /> Export
          </button>
          <button
            onClick={openCreate}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold text-white transition-all"
            style={{ background: "linear-gradient(135deg, #7C3AED, #A78BFA)" }}
            onMouseEnter={e => (e.currentTarget as HTMLElement).style.opacity = "0.88"}
            onMouseLeave={e => (e.currentTarget as HTMLElement).style.opacity = "1"}
          >
            <Plus className="w-4 h-4" /> New Contact
          </button>
        </div>
      </div>

      {/* ── Stat pills ─────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-3">
        <StatPill icon={Users}        label="Total Contacts"  value={contacts.length}                          color="#7C3AED" />
        <StatPill icon={Star}         label="Avg Lead Score"  value={avgScore}                                 color="#F59E0B" />
        <StatPill icon={TrendingUp}   label="Hot Leads (70+)" value={hotLeads}                                 color="#10B981" />
        <StatPill icon={CheckCircle2} label="Converted"       value={contacts.filter(c=>c.lead_status==="converted").length} color="#3B82F6" />
      </div>

      {/* ── Search ─────────────────────────────────────────────── */}
      <div
        className="flex items-center gap-2 px-4 py-2.5 rounded-xl"
        style={{ background: T.surface, border: `1px solid ${T.border}` }}
      >
        <Search className="w-4 h-4 flex-shrink-0" style={{ color: T.textMuted }} />
        <input
          placeholder="Search name, email, company, tag…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="flex-1 bg-transparent text-sm focus:outline-none"
          style={{ color: T.text }}
        />
        {search && (
          <button onClick={() => setSearch("")}>
            <X className="w-3.5 h-3.5" style={{ color: T.textMuted }} />
          </button>
        )}
      </div>

      {/* ── Lead Status filter tabs ─────────────────────────────── */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: T.textMuted }}>Status:</span>
        <button
          onClick={() => setStatus("all")}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all"
          style={{
            background: statusFilter === "all" ? "#7C3AED" : T.surface,
            color:      statusFilter === "all" ? "#fff"    : T.textSub,
            border:     `1px solid ${statusFilter === "all" ? "transparent" : T.border}`,
          }}
        >
          All
          <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold"
            style={{ background: statusFilter === "all" ? "rgba(255,255,255,0.25)" : "rgba(139,92,246,0.1)", color: statusFilter === "all" ? "#fff" : "#7C3AED" }}>
            {contacts.length}
          </span>
        </button>
        {LEAD_STATUSES.map(s => {
          const m = LEAD_STATUS_META[s];
          const active = statusFilter === s;
          return (
            <button
              key={s}
              onClick={() => setStatus(s)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all"
              style={{
                background: active ? m.color : m.bg,
                color:      active ? "#fff"   : m.color,
                border:     `1px solid ${active ? m.color : "transparent"}`,
              }}
            >
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: active ? "#fff" : m.dot }} />
              {m.label}
              <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold"
                style={{ background: active ? "rgba(255,255,255,0.25)" : "rgba(0,0,0,0.10)", color: active ? "#fff" : m.color }}>
                {statusCounts[s] ?? 0}
              </span>
            </button>
          );
        })}
      </div>

      {/* ── Source filter chips ─────────────────────────────────── */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: T.textMuted }}>Source:</span>
        {ALL_SOURCES.map(s => {
          const active = sourceFilter === s;
          const meta   = SOURCE_META[s];
          const count  = s === "all" ? contacts.length : (sourceCounts[s] ?? 0);
          return (
            <button
              key={s}
              onClick={() => setSource(s)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all"
              style={{
                background: active ? (s === "all" ? "#7C3AED" : meta.color) : T.surface,
                color:      active ? "#fff" : T.textSub,
                border:     `1px solid ${active ? "transparent" : T.border}`,
              }}
            >
              {s === "all" ? "All" : meta.label}
              <span className="text-[10px] px-1.5 py-0.5 rounded-full font-bold"
                style={{ background: active ? "rgba(255,255,255,0.25)" : "rgba(139,92,246,0.1)", color: active ? "#fff" : "#7C3AED" }}>
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* ── Bulk action bar ─────────────────────────────────────── */}
      {selected.size > 0 && (
        <div className="flex items-center justify-between px-5 py-3 rounded-xl"
          style={{ background: "rgba(124,58,237,0.07)", border: "1px solid rgba(124,58,237,0.18)" }}>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" style={{ color: "#7C3AED" }} />
            <span className="text-sm font-semibold" style={{ color: "#7C3AED" }}>{selected.size} selected</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="text-xs px-3 py-1.5 rounded-lg font-medium"
              style={{ background: "rgba(239,68,68,0.10)", color: "#EF4444" }}
              onClick={() => {
                if (!confirm(`Delete ${selected.size} contact(s)?`)) return;
                selected.forEach(id => deleteMut.mutate(id));
                setSelected(new Set());
              }}
            >
              Delete selected
            </button>
            <button className="text-xs px-3 py-1.5 rounded-lg font-medium" style={{ color: T.textSub }}
              onClick={() => setSelected(new Set())}>
              Clear
            </button>
          </div>
        </div>
      )}

      {/* ── Table ───────────────────────────────────────────────── */}
      <div
        className="rounded-2xl overflow-hidden"
        style={{ background: T.surface, border: `1px solid ${T.border}`, boxShadow: "0 4px 24px rgba(124,58,237,0.06)" }}
      >
        {isLoading ? (
          <table className="w-full"><tbody>{[1,2,3,4,5].map(i => <SkeletonRow key={i} />)}</tbody></table>

        ) : visible.length === 0 ? (
          <div className="py-20 text-center">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
              style={{ background: "rgba(124,58,237,0.08)" }}>
              <Users className="w-7 h-7" style={{ color: "rgba(124,58,237,0.35)" }} />
            </div>
            <p className="text-base font-bold" style={{ color: T.text }}>No contacts found</p>
            <p className="text-sm mt-1" style={{ color: T.textSub }}>
              {search ? "Try a different search term" : "Add your first contact to get started"}
            </p>
            {!search && (
              <button
                onClick={openCreate}
                className="mt-4 inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold text-white"
                style={{ background: "linear-gradient(135deg, #7C3AED, #A78BFA)" }}
              >
                <Plus className="w-4 h-4" /> Add Contact
              </button>
            )}
          </div>

        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[960px]">
              <thead>
                <tr style={{ borderBottom: `1px solid ${T.border}`, background: "rgba(139,92,246,0.025)" }}>
                  <th className="px-4 py-3.5 w-10">
                    <input type="checkbox" checked={allSelected} onChange={toggleAll}
                      className="w-4 h-4 rounded accent-violet-600 cursor-pointer" />
                  </th>
                  <TH>Contact</TH>
                  <TH>Company</TH>
                  <TH>Contact Info</TH>
                  <TH>Lead Status</TH>
                  <TH>Lead Score</TH>
                  <TH>Source</TH>
                  <TH>Tags</TH>
                  <TH className="text-right">Actions</TH>
                </tr>
              </thead>
              <tbody>
                {visible.map((c, idx) => {
                  const isSel = selected.has(c.id);
                  const rowBg = isSel ? "rgba(124,58,237,0.06)" : idx % 2 === 0 ? "transparent" : "rgba(139,92,246,0.012)";
                  return (
                    <tr
                      key={c.id}
                      style={{ borderBottom: `1px solid ${T.borderSub}`, background: rowBg, transition: "background 0.12s" }}
                      onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = "rgba(139,92,246,0.032)"; }}
                      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = rowBg; }}
                    >
                      {/* Checkbox */}
                      <td className="px-4 py-3.5">
                        <input type="checkbox" checked={isSel} onChange={() => toggleOne(c.id)}
                          className="w-4 h-4 rounded accent-violet-600 cursor-pointer" />
                      </td>

                      {/* Contact */}
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-3">
                          <ContactAvatar contact={c} />
                          <div>
                            <p className="text-sm font-semibold leading-tight" style={{ color: T.text }}>
                              {c.first_name}{c.last_name ? ` ${c.last_name}` : ""}
                            </p>
                            {c.job_title && (
                              <p className="text-xs mt-0.5 leading-tight" style={{ color: T.textMuted }}>{c.job_title}</p>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Company */}
                      <td className="px-4 py-3.5">
                        {c.company_name ? (
                          <div className="flex items-center gap-1.5">
                            <Building2 className="w-3.5 h-3.5 flex-shrink-0" style={{ color: T.textMuted }} />
                            <span className="text-sm" style={{ color: T.textSub }}>{c.company_name}</span>
                          </div>
                        ) : <span style={{ color: T.textMuted }}>—</span>}
                      </td>

                      {/* Contact info */}
                      <td className="px-4 py-3.5">
                        <div className="space-y-1">
                          {c.email && (
                            <div className="flex items-center gap-1.5">
                              <Mail className="w-3 h-3 flex-shrink-0" style={{ color: T.textMuted }} />
                              <a href={`mailto:${c.email}`} className="text-xs hover:underline" style={{ color: T.textSub }}>
                                {c.email}
                              </a>
                            </div>
                          )}
                          {c.phone && (
                            <div className="flex items-center gap-1.5">
                              <Phone className="w-3 h-3 flex-shrink-0" style={{ color: T.textMuted }} />
                              <span className="text-xs" style={{ color: T.textSub }}>{c.phone}</span>
                            </div>
                          )}
                          {!c.email && !c.phone && <span style={{ color: T.textMuted }}>—</span>}
                        </div>
                      </td>

                      {/* Lead Status — NEW COLUMN */}
                      <td className="px-4 py-3.5">
                        <LeadStatusBadge status={c.lead_status ?? "new"} />
                      </td>

                      {/* Lead Score */}
                      <td className="px-4 py-3.5"><ScoreBar score={c.lead_score} /></td>

                      {/* Source */}
                      <td className="px-4 py-3.5"><SourceChip source={c.source} /></td>

                      {/* Tags */}
                      <td className="px-4 py-3.5">
                        {c.tags?.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {c.tags.slice(0, 2).map(t => <TagChip key={t} label={t} />)}
                            {c.tags.length > 2 && (
                              <span className="text-[10px] font-semibold" style={{ color: T.textMuted }}>
                                +{c.tags.length - 2}
                              </span>
                            )}
                          </div>
                        ) : <span style={{ color: T.textMuted }}>—</span>}
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3.5">
                        <div className="flex items-center justify-end gap-0.5">
                          <ActionBtn icon={Zap}    title="AI Rescore" hoverColor="#F59E0B" onClick={() => rescoreMut.mutate(c.id)} />
                          <ActionBtn icon={Edit2}  title="Edit"       hoverColor="#3B82F6" onClick={() => openEdit(c)} />
                          <ActionBtn icon={Trash2} title="Delete"     hoverColor="#EF4444" onClick={() => { if (confirm("Delete this contact?")) deleteMut.mutate(c.id); }} />
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* Table footer */}
            <div className="px-5 py-3 flex items-center justify-between"
              style={{ borderTop: `1px solid ${T.border}`, background: "rgba(139,92,246,0.015)" }}>
              <p className="text-xs" style={{ color: T.textMuted }}>
                Showing {visible.length} of {contacts.length} contacts
              </p>
              <p className="text-xs" style={{ color: T.textMuted }}>
                {selected.size > 0 ? `${selected.size} selected` : ""}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* ── Drawer ─────────────────────────────────────────────── */}
      {drawerOpen && (
        <ContactDrawer
          contact={editing}
          onClose={closeDrawer}
          onSave={(d) => editing
            ? updateMut.mutate({ id: editing.id, data: d })
            : createMut.mutate(d)
          }
        />
      )}
    </div>
  );
}
