"use client";

import React, { useState } from "react";
import { Contact } from "@/types";
import { Edit2, Trash2, Zap, Mail, Phone, Building2, CheckCircle2 } from "lucide-react";

interface ContactsTableProps {
  contacts: Contact[];
  onEdit: (contact: Contact) => void;
  onDelete: (id: string) => void;
  onRescore: (id: string) => void;
  isLoading?: boolean;
}

const SOURCE_META: Record<string, { label: string; color: string; bg: string }> = {
  manual:   { label: "Manual",   color: "#7C3AED", bg: "rgba(124,58,237,0.10)"  },
  import:   { label: "Import",   color: "#6B7280", bg: "rgba(107,114,128,0.10)" },
  whatsapp: { label: "WhatsApp", color: "#10B981", bg: "rgba(16,185,129,0.10)"  },
  gmail:    { label: "Gmail",    color: "#3B82F6", bg: "rgba(59,130,246,0.10)"  },
  web_form: { label: "Web Form", color: "#F59E0B", bg: "rgba(245,158,11,0.10)"  },
  referral: { label: "Referral", color: "#EC4899", bg: "rgba(236,72,153,0.10)"  },
};

function scoreColor(s: number) {
  return s >= 70 ? "#10B981" : s >= 40 ? "#F59E0B" : "#EF4444";
}

function ContactAvatar({ contact }: { contact: Contact }) {
  const color = SOURCE_META[contact.source]?.color ?? "#7C3AED";
  const initials = [contact.first_name, contact.last_name]
    .filter(Boolean).map(s => s![0].toUpperCase()).join("").slice(0, 2) || "?";
  return (
    <div
      className="w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold text-white flex-shrink-0 select-none"
      style={{ background: `linear-gradient(135deg, ${color}, #A78BFA)` }}
    >
      {initials}
    </div>
  );
}

function ScoreBar({ score }: { score: number }) {
  const c = scoreColor(score);
  return (
    <div className="flex items-center gap-2 min-w-[90px]">
      <div className="flex-1 h-1.5 rounded-full overflow-hidden"
        style={{ background: "rgba(139,92,246,0.1)" }}>
        <div className="h-full rounded-full"
          style={{ width: `${score}%`, background: `linear-gradient(90deg, ${c}88, ${c})` }} />
      </div>
      <span className="text-xs font-bold tabular-nums w-6 text-right" style={{ color: c }}>{score}</span>
    </div>
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

function ActionBtn({ icon: Icon, title, hoverColor, onClick }: {
  icon: any; title: string; hoverColor: string; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className="w-7 h-7 rounded-lg flex items-center justify-center transition-all duration-150"
      style={{ color: "var(--color-text-muted)" }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLElement).style.background = `${hoverColor}18`;
        (e.currentTarget as HTMLElement).style.color = hoverColor;
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLElement).style.background = "transparent";
        (e.currentTarget as HTMLElement).style.color = "var(--color-text-muted)";
      }}
    >
      <Icon className="w-3.5 h-3.5" />
    </button>
  );
}

function SkeletonRow() {
  return (
    <tr style={{ borderBottom: "1px solid rgba(139,92,246,0.06)" }}>
      {[16, 140, 120, 100, 90, 80, 80, 60].map((w, i) => (
        <td key={i} className="px-5 py-4">
          <div className="h-3.5 rounded-full animate-pulse"
            style={{ width: w, background: "rgba(139,92,246,0.08)" }} />
        </td>
      ))}
    </tr>
  );
}

export default function ContactsTable({
  contacts, onEdit, onDelete, onRescore, isLoading,
}: ContactsTableProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const allSelected = contacts.length > 0 && contacts.every(c => selected.has(c.id));
  const toggleAll = () =>
    setSelected(allSelected ? new Set() : new Set(contacts.map(c => c.id)));
  const toggleOne = (id: string) =>
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const TH = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
    <th className={`px-5 py-3.5 text-left text-[11px] font-bold uppercase tracking-wider ${className}`}
      style={{ color: "var(--color-text-secondary)" }}>
      {children}
    </th>
  );

  if (isLoading) {
    return (
      <table className="w-full">
        <tbody>{[1, 2, 3, 4, 5].map(i => <SkeletonRow key={i} />)}</tbody>
      </table>
    );
  }

  if (contacts.length === 0) {
    return (
      <div className="py-16 text-center">
        <p className="text-sm font-medium" style={{ color: "var(--color-text-secondary)" }}>
          No contacts found
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* bulk bar */}
      {selected.size > 0 && (
        <div
          className="flex items-center justify-between px-5 py-3 mb-2 rounded-xl"
          style={{ background: "rgba(124,58,237,0.07)", border: "1px solid rgba(124,58,237,0.18)" }}
        >
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" style={{ color: "#7C3AED" }} />
            <span className="text-sm font-semibold" style={{ color: "var(--color-primary)" }}>
              {selected.size} selected
            </span>
          </div>
          <button
            className="text-xs px-3 py-1.5 rounded-lg font-medium"
            style={{ color: "var(--color-text-secondary)" }}
            onClick={() => setSelected(new Set())}
          >
            Clear
          </button>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[860px]">
          <thead>
            <tr style={{
              borderBottom: "1px solid rgba(139,92,246,0.10)",
              background: "rgba(139,92,246,0.025)",
            }}>
              <th className="px-5 py-3.5 w-10">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={toggleAll}
                  className="w-4 h-4 rounded accent-violet-600 cursor-pointer"
                />
              </th>
              <TH>Contact</TH>
              <TH>Company</TH>
              <TH>Contact Info</TH>
              <TH>Lead Score</TH>
              <TH>Source</TH>
              <TH>Tags</TH>
              <TH className="text-right">Actions</TH>
            </tr>
          </thead>
          <tbody>
            {contacts.map((c, idx) => {
              const isSel = selected.has(c.id);
              const rowBg = isSel
                ? "rgba(124,58,237,0.06)"
                : idx % 2 === 0 ? "transparent" : "rgba(139,92,246,0.012)";
              const sm = SOURCE_META[c.source] ?? SOURCE_META.manual;
              return (
                <tr
                  key={c.id}
                  style={{ borderBottom: "1px solid rgba(139,92,246,0.06)", background: rowBg, transition: "background 0.12s" }}
                  onMouseEnter={e => { if (!isSel) (e.currentTarget as HTMLElement).style.background = "rgba(139,92,246,0.032)"; }}
                  onMouseLeave={e => { if (!isSel) (e.currentTarget as HTMLElement).style.background = rowBg; }}
                >
                  <td className="px-5 py-3.5">
                    <input
                      type="checkbox"
                      checked={isSel}
                      onChange={() => toggleOne(c.id)}
                      className="w-4 h-4 rounded accent-violet-600 cursor-pointer"
                    />
                  </td>

                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-3">
                      <ContactAvatar contact={c} />
                      <div>
                        <p className="text-sm font-semibold leading-tight" style={{ color: "var(--color-text)" }}>
                          {c.first_name}{c.last_name ? ` ${c.last_name}` : ""}
                        </p>
                        {c.job_title && (
                          <p className="text-xs mt-0.5" style={{ color: "var(--color-text-muted)" }}>
                            {c.job_title}
                          </p>
                        )}
                      </div>
                    </div>
                  </td>

                  <td className="px-5 py-3.5">
                    {c.company_name ? (
                      <div className="flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5" style={{ color: "var(--color-text-muted)" }} />
                        <span className="text-sm" style={{ color: "var(--color-text-secondary)" }}>
                          {c.company_name}
                        </span>
                      </div>
                    ) : <span style={{ color: "var(--color-text-muted)" }}>—</span>}
                  </td>

                  <td className="px-5 py-3.5">
                    <div className="space-y-1">
                      {c.email && (
                        <div className="flex items-center gap-1.5">
                          <Mail className="w-3 h-3" style={{ color: "var(--color-text-muted)" }} />
                          <a href={`mailto:${c.email}`} className="text-xs hover:underline"
                            style={{ color: "var(--color-text-secondary)" }}>
                            {c.email}
                          </a>
                        </div>
                      )}
                      {c.phone && (
                        <div className="flex items-center gap-1.5">
                          <Phone className="w-3 h-3" style={{ color: "var(--color-text-muted)" }} />
                          <span className="text-xs" style={{ color: "var(--color-text-secondary)" }}>
                            {c.phone}
                          </span>
                        </div>
                      )}
                      {!c.email && !c.phone && <span style={{ color: "var(--color-text-muted)" }}>—</span>}
                    </div>
                  </td>

                  <td className="px-5 py-3.5"><ScoreBar score={c.lead_score} /></td>

                  <td className="px-5 py-3.5">
                    <span className="text-[11px] px-2.5 py-1 rounded-full font-semibold whitespace-nowrap"
                      style={{ background: sm.bg, color: sm.color }}>
                      {sm.label}
                    </span>
                  </td>

                  <td className="px-5 py-3.5">
                    {c.tags?.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {c.tags.slice(0, 3).map(t => <TagChip key={t} label={t} />)}
                        {c.tags.length > 3 && (
                          <span className="text-[10px] font-semibold" style={{ color: "var(--color-text-muted)" }}>
                            +{c.tags.length - 3}
                          </span>
                        )}
                      </div>
                    ) : <span style={{ color: "var(--color-text-muted)" }}>—</span>}
                  </td>

                  <td className="px-5 py-3.5">
                    <div className="flex items-center justify-end gap-0.5">
                      <ActionBtn icon={Zap}    title="AI Rescore" hoverColor="#F59E0B" onClick={() => onRescore(c.id)} />
                      <ActionBtn icon={Edit2}  title="Edit"       hoverColor="#3B82F6" onClick={() => onEdit(c)} />
                      <ActionBtn icon={Trash2} title="Delete"     hoverColor="#EF4444" onClick={() => onDelete(c.id)} />
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
