"use client";

import React, { useState, useEffect } from "react";
import { Deal, Pipeline } from "@/types";
import { X, TrendingUp, Flame, AlertCircle, Circle, ArrowUpRight } from "lucide-react";
import { dealService } from "@/services/dealService";
import { pipelineService } from "@/services/pipelineService";
import { contactService } from "@/services/contactService";
import { toast } from "sonner";

interface DealDrawerProps {
  open: boolean;
  onClose: () => void;
  deal?: Deal;
  onSave: () => void;
  pipelineId?: string;
}

const PRIORITY_META: Record<string, { color: string; bg: string }> = {
  low:    { color: "#6B7280", bg: "rgba(107,114,128,0.10)" },
  medium: { color: "#3B82F6", bg: "rgba(59,130,246,0.10)"  },
  high:   { color: "#F59E0B", bg: "rgba(245,158,11,0.10)"  },
  urgent: { color: "#EF4444", bg: "rgba(239,68,68,0.10)"   },
};

const STAGE_COLORS = [
  "#7C3AED","#3B82F6","#10B981","#F59E0B","#EF4444","#EC4899","#8B5CF6",
];

export default function DealDrawer({
  open, onClose, deal, onSave, pipelineId,
}: DealDrawerProps) {
  const [form, setForm] = useState({
    title:       "",
    pipeline_id: pipelineId || "",
    stage_id:    "",
    contact_id:  "",
    value:       "",
    priority:    "medium",
    notes:       "",
  });
  const [isLoading, setIsLoading]   = useState(false);
  const [pipelines, setPipelines]   = useState<Pipeline[]>([]);
  const [contacts, setContacts]     = useState<any[]>([]);
  const [stages, setStages]         = useState<any[]>([]);
  const [errors, setErrors]         = useState<Record<string, string>>({});

  useEffect(() => {
    if (open) loadData();
  }, [open]);

  useEffect(() => {
    if (deal) {
      setForm({
        title:       deal.title,
        pipeline_id: deal.pipeline_id,
        stage_id:    deal.stage_id,
        contact_id:  deal.contact_id || "",
        value:       deal.value?.toString() || "",
        priority:    deal.priority,
        notes:       deal.notes || "",
      });
    } else {
      setForm({
        title: "", pipeline_id: pipelineId || "",
        stage_id: "", contact_id: "", value: "",
        priority: "medium", notes: "",
      });
    }
    setErrors({});
  }, [deal, open, pipelineId]);

  const loadData = async () => {
    try {
      const [plRes, cRes] = await Promise.all([
        pipelineService.getPipelines(),
        contactService.getContacts({ page_size: 100 }),
      ]);
      setPipelines(plRes.data);
      setContacts(cRes.data);
      if (plRes.data.length > 0 && !form.pipeline_id) {
        const first = plRes.data[0];
        setForm(f => ({ ...f, pipeline_id: first.id, stage_id: first.stages?.[0]?.id ?? "" }));
        setStages(first.stages ?? []);
      } else if (form.pipeline_id) {
        const current = plRes.data.find((p: Pipeline) => p.id === form.pipeline_id);
        if (current) setStages(current.stages ?? []);
      }
    } catch {
      toast.error("Failed to load pipeline data");
    }
  };

  const handlePipelineChange = (id: string) => {
    const pl = pipelines.find(p => p.id === id);
    setStages(pl?.stages ?? []);
    setForm(f => ({ ...f, pipeline_id: id, stage_id: pl?.stages?.[0]?.id ?? "" }));
  };

  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!form.title.trim())   errs.title = "Required";
    if (!form.pipeline_id)    errs.pipeline_id = "Required";
    if (!form.stage_id)       errs.stage_id = "Required";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setIsLoading(true);
    try {
      const data = {
        title:       form.title.trim(),
        pipeline_id: form.pipeline_id,
        stage_id:    form.stage_id,
        contact_id:  form.contact_id || undefined,
        value:       form.value ? parseInt(form.value) : undefined,
        priority:    form.priority,
      };
      if (deal) {
        await dealService.updateDeal(deal.id, data);
        toast.success("Deal updated");
      } else {
        await dealService.createDeal(data);
        toast.success("Deal created");
      }
      onSave();
      onClose();
    } catch (err: any) {
      toast.error(err.response?.data?.message || "Failed to save deal");
    } finally {
      setIsLoading(false);
    }
  };

  const inputBase = "w-full px-3.5 py-2.5 rounded-xl text-sm transition-all focus:outline-none focus:ring-2 focus:ring-violet-400/40";
  const inputStyle: React.CSSProperties = {
    background: "rgba(242,238,255,0.85)",
    border: "1px solid rgba(139,92,246,0.18)",
    color: "var(--color-text)",
  };

  const SL = ({ children }: { children: string }) => (
    <p className="text-[10px] font-bold uppercase tracking-widest mb-3"
      style={{ color: "var(--color-text-secondary)" }}>{children}</p>
  );

  if (!open) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/25 backdrop-blur-sm z-30" onClick={onClose} />
      <div
        className="fixed right-0 top-0 h-screen w-[440px] flex flex-col z-40"
        style={{
          background: "#f9f6ff",
          backdropFilter: "blur(24px)",
          borderLeft: "1px solid rgba(139,92,246,0.14)",
          boxShadow: "-24px 0 64px rgba(26,15,58,0.18)",
        }}
      >
        {/* header */}
        <div className="flex items-center justify-between px-6 py-5"
          style={{ borderBottom: "1px solid rgba(139,92,246,0.10)" }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(124,58,237,0.12)" }}>
              <TrendingUp className="w-4 h-4" style={{ color: "#7C3AED" }} />
            </div>
            <div>
              <h2 className="font-bold text-base leading-none" style={{ color: "var(--color-text)" }}>
                {deal ? "Edit Deal" : "New Deal"}
              </h2>
              <p className="text-xs mt-0.5" style={{ color: "var(--color-text-secondary)" }}>
                {deal ? "Update deal details" : "Add to your pipeline"}
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

        {/* form */}
        <form id="deal-drawer-form" onSubmit={handleSubmit}
          className="flex-1 overflow-y-auto px-6 py-5 space-y-5">

          <div>
            <SL>Deal Info</SL>
            <div>
              <label className="block text-xs font-semibold mb-1.5"
                style={{ color: "var(--color-text-secondary)" }}>
                Title<span className="text-red-400 ml-0.5">*</span>
              </label>
              <input
                placeholder="e.g. Website redesign for Acme"
                value={form.title}
                onChange={e => set("title", e.target.value)}
                required
                className={inputBase}
                style={{ ...inputStyle, borderColor: errors.title ? "#EF4444" : "rgba(139,92,246,0.18)" }}
              />
              {errors.title && <p className="text-xs mt-1 text-red-500">{errors.title}</p>}
            </div>
          </div>

          <div>
            <SL>Pipeline & Stage</SL>
            <div className="space-y-3">
              {pipelines.length > 1 && (
                <div>
                  <label className="block text-xs font-semibold mb-1.5"
                    style={{ color: "var(--color-text-secondary)" }}>Pipeline</label>
                  <select
                    value={form.pipeline_id}
                    onChange={e => handlePipelineChange(e.target.value)}
                    className={inputBase} style={inputStyle}
                  >
                    {pipelines.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold mb-2"
                  style={{ color: "var(--color-text-secondary)" }}>
                  Stage<span className="text-red-400 ml-0.5">*</span>
                </label>
                {stages.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {stages.map((s: any, i: number) => {
                      const color = s.color || STAGE_COLORS[i % STAGE_COLORS.length];
                      const active = form.stage_id === s.id;
                      return (
                        <button key={s.id} type="button"
                          onClick={() => set("stage_id", s.id)}
                          className="text-[11px] px-2.5 py-1 rounded-full font-semibold transition-all"
                          style={{
                            background: active ? color : `${color}18`,
                            color:      active ? "#fff" : color,
                            border:     `1px solid ${active ? color : "transparent"}`,
                          }}>
                          {s.name}
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-xs" style={{ color: "var(--color-text-muted)" }}>
                    Loading stages…
                  </p>
                )}
                {errors.stage_id && <p className="text-xs mt-1 text-red-500">{errors.stage_id}</p>}
              </div>
            </div>
          </div>

          <div>
            <SL>Value & Priority</SL>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold mb-1.5"
                  style={{ color: "var(--color-text-secondary)" }}>Value (₹)</label>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-sm font-semibold"
                    style={{ color: "var(--color-text-muted)" }}>₹</span>
                  <input
                    type="number"
                    placeholder="50000"
                    value={form.value}
                    onChange={e => set("value", e.target.value)}
                    className={inputBase}
                    style={{ ...inputStyle, paddingLeft: "1.75rem" }}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold mb-2"
                  style={{ color: "var(--color-text-secondary)" }}>Priority</label>
                <div className="flex gap-2">
                  {Object.entries(PRIORITY_META).map(([k, v]) => {
                    const active = form.priority === k;
                    return (
                      <button key={k} type="button"
                        onClick={() => set("priority", k)}
                        className="flex-1 py-2 rounded-xl text-xs font-bold transition-all"
                        style={{
                          background: active ? v.color : v.bg,
                          color:      active ? "#fff"   : v.color,
                          border:     `1px solid ${active ? v.color : "transparent"}`,
                        }}>
                        {k.charAt(0).toUpperCase() + k.slice(1)}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Contact */}
          {contacts.length > 0 && (
            <div>
              <SL>Link Contact</SL>
              <select
                value={form.contact_id}
                onChange={e => set("contact_id", e.target.value)}
                className={inputBase} style={inputStyle}
              >
                <option value="">— No contact —</option>
                {contacts.map((c: any) => (
                  <option key={c.id} value={c.id}>
                    {c.first_name}{c.last_name ? ` ${c.last_name}` : ""}
                    {c.company_name ? ` · ${c.company_name}` : ""}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <SL>Notes</SL>
            <textarea
              placeholder="Any deal-specific notes…"
              value={form.notes}
              onChange={e => set("notes", e.target.value)}
              rows={3}
              className="w-full px-3.5 py-2.5 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-violet-400/40"
              style={inputStyle}
            />
          </div>
        </form>

        {/* footer */}
        <div className="px-6 py-4 flex gap-3"
          style={{ borderTop: "1px solid rgba(139,92,246,0.10)" }}>
          <button type="button" onClick={onClose}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-all"
            style={{ border: "1px solid rgba(139,92,246,0.20)", color: "var(--color-text-secondary)" }}
            onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "rgba(139,92,246,0.05)"}
            onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "transparent"}>
            Cancel
          </button>
          <button type="submit" form="deal-drawer-form" disabled={isLoading}
            className="flex-1 py-2.5 rounded-xl text-sm font-bold text-white disabled:opacity-60 transition-all"
            style={{ background: "linear-gradient(135deg, #7C3AED, #A78BFA)" }}>
            {isLoading ? "Saving…" : deal ? "Save Changes" : "Create Deal"}
          </button>
        </div>
      </div>
    </>
  );
}
