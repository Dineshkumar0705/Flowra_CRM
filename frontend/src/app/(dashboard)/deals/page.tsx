"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus, IndianRupee, X, TrendingUp, Target,
  Flame, ChevronDown, Grip, Star,
  AlertCircle, Circle, ArrowUpRight, Users,
} from "lucide-react";
import {
  DndContext, DragEndEvent, DragOverlay, DragStartEvent,
  closestCenter, PointerSensor, useSensor, useSensors, useDroppable,
} from "@dnd-kit/core";
import {
  SortableContext, useSortable, verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import apiClient from "@/services/apiClient";
import { Deal, Pipeline, Stage } from "@/types";
import { toast } from "sonner";

/* ─── helpers ─────────────────────────────────────────────────── */
const fmtINR = (n?: number) =>
  n
    ? new Intl.NumberFormat("en-IN", {
        style: "currency", currency: "INR", maximumFractionDigits: 0,
      }).format(n)
    : "—";

const fmtINRCompact = (n: number) =>
  n >= 10_000_000 ? `₹${(n / 10_000_000).toFixed(1)}Cr`
  : n >= 100_000   ? `₹${(n / 100_000).toFixed(1)}L`
  : n >= 1_000     ? `₹${(n / 1_000).toFixed(1)}K`
  : `₹${n}`;

/* ─── priority meta ───────────────────────────────────────────── */
const PRIORITY: Record<string, { color: string; bg: string; icon: any }> = {
  urgent: { color: "#EF4444", bg: "rgba(239,68,68,0.10)",  icon: Flame    },
  high:   { color: "#F59E0B", bg: "rgba(245,158,11,0.10)", icon: AlertCircle },
  medium: { color: "#3B82F6", bg: "rgba(59,130,246,0.10)", icon: Circle   },
  low:    { color: "#6B7280", bg: "rgba(107,114,128,0.10)",icon: ArrowUpRight },
};

const STAGE_COLORS = [
  "#7C3AED","#3B82F6","#10B981","#F59E0B","#EF4444","#EC4899","#8B5CF6",
];

/* ─── Deal Card ───────────────────────────────────────────────── */
function DealCard({ deal, ghost }: { deal: Deal; ghost?: boolean }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: deal.id });
  const p = PRIORITY[deal.priority] ?? PRIORITY.medium;
  const PIcon = p.icon;

  return (
    <div
      ref={setNodeRef}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0 : ghost ? 0.45 : 1,
      }}
      className="group rounded-xl mb-2 cursor-grab active:cursor-grabbing select-none"
      {...attributes}
      {...listeners}
    >
      <div
        className="p-3.5 rounded-xl transition-all duration-150"
        style={{
          background: "var(--color-surface-solid, #fff)",
          border: "1px solid rgba(139,92,246,0.12)",
          boxShadow: "0 2px 8px rgba(124,58,237,0.05)",
        }}
        onMouseEnter={e =>
          (e.currentTarget as HTMLElement).style.boxShadow = "0 6px 20px rgba(124,58,237,0.12)"
        }
        onMouseLeave={e =>
          (e.currentTarget as HTMLElement).style.boxShadow = "0 2px 8px rgba(124,58,237,0.05)"
        }
      >
        {/* drag handle + priority */}
        <div className="flex items-start justify-between gap-2 mb-2.5">
          <div className="flex items-start gap-2 flex-1 min-w-0">
            <Grip className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 opacity-0 group-hover:opacity-40 transition-opacity"
              style={{ color: "var(--color-text-muted)" }} />
            <p className="text-sm font-semibold leading-snug" style={{ color: "var(--color-text)" }}>
              {deal.title}
            </p>
          </div>
          <span
            className="flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full flex-shrink-0"
            style={{ background: p.bg, color: p.color }}
          >
            <PIcon className="w-2.5 h-2.5" />
            {deal.priority}
          </span>
        </div>

        {/* value */}
        {deal.value ? (
          <div
            className="flex items-center gap-1 text-xs font-bold mb-2"
            style={{ color: "var(--color-primary)" }}
          >
            <IndianRupee className="w-3 h-3" />
            {fmtINR(deal.value)}
          </div>
        ) : null}

        {/* footer */}
        <div className="flex items-center justify-between">
          <span className="text-[10px]" style={{ color: "var(--color-text-muted)" }}>
            {new Date(deal.created_at).toLocaleDateString("en-IN", {
              day: "numeric", month: "short",
            })}
          </span>
          {deal.contact_id && (
            <div className="w-5 h-5 rounded-full flex items-center justify-center"
              style={{ background: "rgba(124,58,237,0.12)" }}>
              <Users className="w-2.5 h-2.5" style={{ color: "#7C3AED" }} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── Droppable column wrapper ────────────────────────────────── */
function DroppableColumn({
  stageId, children,
}: { stageId: string; children: React.ReactNode }) {
  const { setNodeRef, isOver } = useDroppable({ id: stageId });
  return (
    <div
      ref={setNodeRef}
      className="flex-1 min-h-[80px] rounded-xl transition-all"
      style={{
        background: isOver ? "rgba(124,58,237,0.04)" : "transparent",
        outline: isOver ? "2px dashed rgba(124,58,237,0.25)" : "none",
      }}
    >
      {children}
    </div>
  );
}

/* ─── New Deal Drawer ─────────────────────────────────────────── */
function NewDealDrawer({
  onClose, pipelines, defaultPipelineId,
}: {
  onClose: () => void;
  pipelines: Pipeline[];
  defaultPipelineId: string;
}) {
  const qc = useQueryClient();

  const firstPipeline = pipelines.find(p => p.id === defaultPipelineId) ?? pipelines[0];
  const [selectedPipelineId, setPipelineId] = useState(firstPipeline?.id ?? "");
  const currentPipeline = pipelines.find(p => p.id === selectedPipelineId) ?? firstPipeline;
  const stages: Stage[] = currentPipeline?.stages ?? [];

  const [form, setForm] = useState({
    title:    "",
    value:    "",
    priority: "medium",
    stage_id: stages[0]?.id ?? "",
    notes:    "",
  });
  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));

  const mut = useMutation({
    mutationFn: (d: any) => apiClient.post("/deals", d),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["board"] });
      qc.invalidateQueries({ queryKey: ["deals-stats"] });
      onClose();
      toast.success("Deal created!");
    },
    onError: (err: any) =>
      toast.error(err?.response?.data?.message ?? "Failed to create deal"),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) return;
    if (!form.stage_id) { toast.error("Please select a stage"); return; }
    mut.mutate({
      title:       form.title.trim(),
      value:       form.value ? Number(form.value) : undefined,
      priority:    form.priority,
      stage_id:    form.stage_id,
      pipeline_id: selectedPipelineId,
      notes:       form.notes || undefined,
    });
  };

  const inputBase = "w-full px-3.5 py-2.5 rounded-xl text-sm transition-all focus:outline-none focus:ring-2 focus:ring-violet-400/40";
  const inputStyle: React.CSSProperties = {
    background: "rgba(242,238,255,0.85)",
    border: "1px solid rgba(139,92,246,0.18)",
    color: "var(--color-text)",
  };

  const SectionLabel = ({ children }: { children: string }) => (
    <p className="text-[10px] font-bold uppercase tracking-widest mb-3"
      style={{ color: "var(--color-text-secondary)" }}>
      {children}
    </p>
  );

  const Field = ({
    label, fieldKey, placeholder, type = "text", required = false,
  }: {
    label: string; fieldKey: string; placeholder?: string;
    type?: string; required?: boolean;
  }) => (
    <div>
      <label className="block text-xs font-semibold mb-1.5"
        style={{ color: "var(--color-text-secondary)" }}>
        {label}{required && <span className="text-red-400 ml-0.5">*</span>}
      </label>
      <input
        type={type}
        placeholder={placeholder}
        value={(form as any)[fieldKey]}
        onChange={e => set(fieldKey, e.target.value)}
        required={required}
        className={inputBase}
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
                New Deal
              </h2>
              <p className="text-xs mt-0.5" style={{ color: "var(--color-text-secondary)" }}>
                Add to your pipeline
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
        <form id="new-deal-form" onSubmit={handleSubmit}
          className="flex-1 overflow-y-auto px-6 py-5 space-y-5">

          <div>
            <SectionLabel>Deal Info</SectionLabel>
            <Field label="Deal Title" fieldKey="title"
              placeholder="e.g. Website redesign for Acme" required />
          </div>

          <div>
            <SectionLabel>Pipeline & Stage</SectionLabel>
            <div className="space-y-3">
              {/* Pipeline */}
              {pipelines.length > 1 && (
                <div>
                  <label className="block text-xs font-semibold mb-1.5"
                    style={{ color: "var(--color-text-secondary)" }}>
                    Pipeline
                  </label>
                  <select
                    value={selectedPipelineId}
                    onChange={e => {
                      setPipelineId(e.target.value);
                      const pl = pipelines.find(p => p.id === e.target.value);
                      set("stage_id", pl?.stages?.[0]?.id ?? "");
                    }}
                    className={inputBase}
                    style={inputStyle}
                  >
                    {pipelines.map(p => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* Stage as pills */}
              <div>
                <label className="block text-xs font-semibold mb-2"
                  style={{ color: "var(--color-text-secondary)" }}>
                  Stage{stages.length === 0 && <span className="ml-1 text-red-400">(no stages found)</span>}
                </label>
                {stages.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {stages.map((s, i) => {
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
                    No stages available for this pipeline
                  </p>
                )}
              </div>
            </div>
          </div>

          <div>
            <SectionLabel>Deal Value & Priority</SectionLabel>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold mb-1.5"
                  style={{ color: "var(--color-text-secondary)" }}>
                  Value (₹)
                </label>
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

              {/* Priority pills */}
              <div>
                <label className="block text-xs font-semibold mb-2"
                  style={{ color: "var(--color-text-secondary)" }}>
                  Priority
                </label>
                <div className="flex gap-2">
                  {Object.entries(PRIORITY).map(([k, v]) => {
                    const active = form.priority === k;
                    return (
                      <button key={k} type="button"
                        onClick={() => set("priority", k)}
                        className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-bold transition-all"
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

          <div>
            <SectionLabel>Notes</SectionLabel>
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
          <button type="submit" form="new-deal-form" disabled={mut.isPending}
            className="flex-1 py-2.5 rounded-xl text-sm font-bold text-white transition-all disabled:opacity-60"
            style={{ background: "linear-gradient(135deg, #7C3AED, #A78BFA)" }}>
            {mut.isPending ? "Creating…" : "Create Deal"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─── Stat pill ───────────────────────────────────────────────── */
function StatPill({
  icon: Icon, label, value, color,
}: { icon: any; label: string; value: string; color: string }) {
  return (
    <div className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl"
      style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)" }}>
      <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
        style={{ background: `${color}15` }}>
        <Icon className="w-3.5 h-3.5" style={{ color }} />
      </div>
      <div>
        <p className="text-sm font-extrabold leading-none" style={{ color: "var(--color-text)" }}>{value}</p>
        <p className="text-[10px] mt-0.5 font-medium" style={{ color: "var(--color-text-secondary)" }}>{label}</p>
      </div>
    </div>
  );
}

/* ─── Skeleton column ─────────────────────────────────────────── */
function SkeletonColumn() {
  return (
    <div className="w-[260px] flex-shrink-0 rounded-2xl overflow-hidden"
      style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)" }}>
      <div className="px-4 pt-4 pb-3" style={{ borderBottom: "1px solid rgba(139,92,246,0.08)" }}>
        <div className="h-4 w-24 rounded-full animate-pulse mb-2"
          style={{ background: "rgba(139,92,246,0.08)" }} />
        <div className="h-3 w-16 rounded-full animate-pulse"
          style={{ background: "rgba(139,92,246,0.05)" }} />
      </div>
      <div className="p-3 space-y-2.5">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-20 rounded-xl animate-pulse"
            style={{ background: "rgba(139,92,246,0.05)" }} />
        ))}
      </div>
    </div>
  );
}

/* ─── Page ────────────────────────────────────────────────────── */
export default function DealsPage() {
  const qc = useQueryClient();
  const [activeDeal, setActiveDeal]       = useState<Deal | null>(null);
  const [showDrawer, setShowDrawer]       = useState(false);
  const [selectedPipeline, setSelected]  = useState<string>("");

  /* pipelines */
  const { data: pipelines = [] } = useQuery({
    queryKey: ["pipelines"],
    queryFn: async () => {
      const r = await apiClient.get("/pipelines");
      return r.data?.data as Pipeline[];
    },
    staleTime: 300_000,
  });

  const currentId = selectedPipeline || pipelines[0]?.id || "";

  /* board */
  const { data: board, isLoading } = useQuery({
    queryKey: ["board", currentId],
    queryFn: async () => {
      const r = await apiClient.get(`/pipelines/${currentId}/board`);
      return r.data?.data;
    },
    enabled: !!currentId,
    staleTime: 30_000,
  });

  /* move stage */
  const moveMut = useMutation({
    mutationFn: ({ dealId, stageId }: { dealId: string; stageId: string }) =>
      apiClient.post(`/deals/${dealId}/move-stage`, { stage_id: stageId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["board"] }),
    onError: () => toast.error("Failed to move deal"),
  });

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  );

  const handleDragStart = (e: DragStartEvent) => {
    const all = (board?.stages ?? []).flatMap((s: any) => s.deals ?? []);
    setActiveDeal(all.find((d: Deal) => d.id === e.active.id) ?? null);
  };

  const handleDragEnd = (e: DragEndEvent) => {
    setActiveDeal(null);
    if (!e.over) return;
    const overId = String(e.over.id);
    const stage = (board?.stages ?? []).find(
      (s: any) => s.id === overId || s.deals?.some((d: any) => d.id === overId)
    );
    if (stage && e.active.id !== e.over.id) {
      moveMut.mutate({ dealId: String(e.active.id), stageId: stage.id });
    }
  };

  /* stats */
  const allDeals: Deal[] = (board?.stages ?? []).flatMap((s: any) => s.deals ?? []);
  const totalValue = allDeals.reduce((s, d) => s + (d.value ?? 0), 0);
  const urgentCount = allDeals.filter(d => d.priority === "urgent").length;
  const highCount   = allDeals.filter(d => d.priority === "high").length;

  return (
    <div className="h-full flex flex-col gap-4 animate-fade-in">

      {/* ── Top bar ─────────────────────────────────────────────── */}
      <div className="flex-shrink-0 flex flex-col sm:flex-row sm:items-center gap-3">
        <div className="flex items-center gap-3 flex-1">
          <div>
            <h2 className="text-lg font-extrabold" style={{ color: "var(--color-text)" }}>
              Deals
            </h2>
            <p className="text-xs mt-0.5" style={{ color: "var(--color-text-secondary)" }}>
              {allDeals.length} deal{allDeals.length !== 1 ? "s" : ""} in pipeline
            </p>
          </div>

          {/* pipeline selector */}
          {pipelines.length > 1 && (
            <div className="relative">
              <select
                value={currentId}
                onChange={e => setSelected(e.target.value)}
                className="appearance-none pl-3.5 pr-8 py-2 rounded-xl text-sm font-medium focus:outline-none cursor-pointer"
                style={{
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  color: "var(--color-text)",
                }}
              >
                {pipelines.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 pointer-events-none"
                style={{ color: "var(--color-text-muted)" }} />
            </div>
          )}
        </div>

        <button
          onClick={() => setShowDrawer(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold text-white flex-shrink-0 transition-all"
          style={{ background: "linear-gradient(135deg, #7C3AED, #A78BFA)" }}
          onMouseEnter={e => (e.currentTarget as HTMLElement).style.opacity = "0.88"}
          onMouseLeave={e => (e.currentTarget as HTMLElement).style.opacity = "1"}
        >
          <Plus className="w-4 h-4" /> New Deal
        </button>
      </div>

      {/* ── Stats row ───────────────────────────────────────────── */}
      <div className="flex-shrink-0 flex flex-wrap gap-3">
        <StatPill icon={TrendingUp}   label="Total Deals"     value={String(allDeals.length)}           color="#7C3AED" />
        <StatPill icon={IndianRupee}  label="Pipeline Value"  value={fmtINRCompact(totalValue)}         color="#10B981" />
        <StatPill icon={Flame}        label="Urgent"          value={String(urgentCount)}                color="#EF4444" />
        <StatPill icon={AlertCircle}  label="High Priority"   value={String(highCount)}                  color="#F59E0B" />
        <StatPill icon={Target}       label="Stages"          value={String(board?.stages?.length ?? 0)} color="#3B82F6" />
      </div>

      {/* ── Kanban board ────────────────────────────────────────── */}
      <div className="flex-1 overflow-hidden">
        {isLoading ? (
          <div className="flex gap-4 overflow-x-auto pb-2 h-full">
            {[1, 2, 3, 4].map(i => <SkeletonColumn key={i} />)}
          </div>

        ) : !board || !board.stages?.length ? (
          <div className="h-full flex items-center justify-center rounded-2xl"
            style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)" }}>
            <div className="text-center py-16">
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
                style={{ background: "rgba(124,58,237,0.08)" }}>
                <TrendingUp className="w-7 h-7" style={{ color: "rgba(124,58,237,0.35)" }} />
              </div>
              <p className="text-base font-bold" style={{ color: "var(--color-text)" }}>
                No pipeline found
              </p>
              <p className="text-sm mt-1" style={{ color: "var(--color-text-secondary)" }}>
                Create a pipeline with stages to manage your deals
              </p>
            </div>
          </div>

        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
          >
            <div className="flex gap-3 overflow-x-auto pb-4 h-full">
              {board.stages.map((stage: any, idx: number) => {
                const deals: Deal[] = stage.deals ?? [];
                const total = deals.reduce((s: number, d: Deal) => s + (d.value ?? 0), 0);
                const color = stage.color || STAGE_COLORS[idx % STAGE_COLORS.length];

                return (
                  <div
                    key={stage.id}
                    className="w-[260px] flex-shrink-0 flex flex-col rounded-2xl overflow-hidden"
                    style={{
                      background: "var(--color-surface)",
                      border: "1px solid var(--color-border)",
                      boxShadow: "0 4px 16px rgba(124,58,237,0.05)",
                    }}
                  >
                    {/* column header */}
                    <div className="px-4 pt-0 pb-0">
                      {/* colored top bar */}
                      <div className="h-1 rounded-b-full mb-3.5" style={{ background: color }} />
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full flex-shrink-0"
                            style={{ background: color }} />
                          <span className="text-xs font-bold" style={{ color: "var(--color-text)" }}>
                            {stage.name}
                          </span>
                        </div>
                        <span
                          className="text-xs font-bold px-2 py-0.5 rounded-full"
                          style={{ background: `${color}18`, color }}
                        >
                          {deals.length}
                        </span>
                      </div>
                      {total > 0 && (
                        <p className="text-[10px] font-semibold mb-2.5 ml-4"
                          style={{ color: "var(--color-text-secondary)" }}>
                          {fmtINRCompact(total)}
                        </p>
                      )}
                    </div>

                    {/* cards */}
                    <div className="flex-1 px-3 pb-3 overflow-y-auto">
                      <SortableContext
                        items={deals.map(d => d.id)}
                        strategy={verticalListSortingStrategy}
                      >
                        <DroppableColumn stageId={stage.id}>
                          {deals.map(d => (
                            <DealCard key={d.id} deal={d} ghost={activeDeal?.id === d.id} />
                          ))}
                          {deals.length === 0 && (
                            <div
                              className="mt-1 py-8 text-center rounded-xl border-2 border-dashed"
                              style={{ borderColor: `${color}30` }}
                            >
                              <p className="text-[11px]" style={{ color: "var(--color-text-muted)" }}>
                                Drop deals here
                              </p>
                            </div>
                          )}
                        </DroppableColumn>
                      </SortableContext>
                    </div>

                    {/* add deal to this column */}
                    <button
                      onClick={() => setShowDrawer(true)}
                      className="mx-3 mb-3 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-semibold transition-all"
                      style={{
                        background: `${color}0d`,
                        border: `1px dashed ${color}40`,
                        color,
                      }}
                      onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = `${color}18`}
                      onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = `${color}0d`}
                    >
                      <Plus className="w-3.5 h-3.5" /> Add deal
                    </button>
                  </div>
                );
              })}
            </div>

            <DragOverlay>
              {activeDeal && <DealCard deal={activeDeal} />}
            </DragOverlay>
          </DndContext>
        )}
      </div>

      {/* ── Drawer — always renders when showDrawer=true, NOT gated on board ── */}
      {showDrawer && (
        <NewDealDrawer
          onClose={() => setShowDrawer(false)}
          pipelines={pipelines}
          defaultPipelineId={currentId}
        />
      )}
    </div>
  );
}
