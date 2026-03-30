"use client";

/**
 * Tasks Page — Flowra CRM
 * Full task management: kanban-style status view, create/edit drawer,
 * priority + due-date filtering, overdue alerts, analytics strip.
 *
 * PREMIUM UI with:
 * - Gradient KPI cards with bottom borders
 * - Beautiful kanban columns with empty states
 * - Priority-colored left borders on task cards
 * - Smooth hover animations (inline styles)
 * - Elegant filter pills and view toggles
 * - FAB button for quick task creation
 * - Progress bar at bottom
 */

import React, { useState, useMemo, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  CheckSquare, CheckCircle2, Clock, AlertCircle, Plus,
  Search, RefreshCw, X, Edit2, ArrowUpRight,
  Flame, Circle, Activity, Users, TrendingUp,
  List, Columns
} from "lucide-react";
import apiClient from "@/services/apiClient";
import type { Task, TaskStatus, TaskPriority } from "@/types";

// ─── Design tokens ────────────────────────────────────────────────────────────

const T = {
  accent:      "#7C3AED",
  accentLight: "rgba(124,58,237,0.07)",
  border:      "#E9EAEC",
  borderSub:   "#F3F4F6",
  text:        "#111827",
  textSub:     "#374151",
  textMuted:   "#6B7280",
  textFaint:   "#9CA3AF",
  surface:     "#ffffff",
  bg:          "#F9FAFB",
  green:       "#10B981",
  blue:        "#3B82F6",
  amber:       "#F59E0B",
  red:         "#EF4444",
  teal:        "#14B8A6",
  indigo:      "#6366F1",
} as const;

// ─── Status / Priority config ─────────────────────────────────────────────────

const STATUS_CONFIG: Record<TaskStatus, {
  label:  string;
  color:  string;
  bg:     string;
  icon:   React.ElementType;
  border: string;
}> = {
  todo:        { label: "To Do",       color: T.textMuted, bg: T.borderSub,                icon: Circle,       border: T.border  },
  in_progress: { label: "In Progress", color: T.blue,      bg: "rgba(59,130,246,0.08)",    icon: RefreshCw,    border: "#BFDBFE" },
  done:        { label: "Done",        color: T.green,     bg: "rgba(16,185,129,0.08)",    icon: CheckCircle2, border: "#A7F3D0" },
  cancelled:   { label: "Cancelled",   color: T.textFaint, bg: "rgba(156,163,175,0.08)",   icon: X,            border: T.borderSub },
};

const PRIORITY_CONFIG: Record<TaskPriority, {
  label: string;
  color: string;
  bg:    string;
  dot:   string;
  borderColor: string;
}> = {
  low:    { label: "Low",    color: T.textMuted, bg: T.borderSub,               dot: T.textFaint, borderColor: T.textFaint },
  medium: { label: "Medium", color: T.blue,      bg: "rgba(59,130,246,0.08)",   dot: T.blue, borderColor: T.blue },
  high:   { label: "High",   color: T.amber,     bg: "rgba(245,158,11,0.08)",   dot: T.amber, borderColor: T.amber },
  urgent: { label: "Urgent", color: T.red,       bg: "rgba(239,68,68,0.08)",    dot: T.red, borderColor: T.red },
};

// ─── Demo data ────────────────────────────────────────────────────────────────

const DEMO_TASKS: Task[] = [
  {
    id: "t1", workspace_id: "w1",
    title: "Follow up with Arjun Sharma re: proposal",
    description: "Send revised proposal with pricing breakdown",
    status: "todo", priority: "urgent",
    due_at: new Date(Date.now() - 86400000).toISOString(),
    contact_id: "c1", assigned_to: "u1", created_by: "u1",
    is_overdue: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
  },
  {
    id: "t2", workspace_id: "w1",
    title: "Prepare demo deck for Wipro Technologies",
    description: "Focus on AI automation and ROI metrics",
    status: "in_progress", priority: "high",
    due_at: new Date(Date.now() + 86400000).toISOString(),
    deal_id: "d1", assigned_to: "u1", created_by: "u1",
    is_overdue: false, created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
  },
  {
    id: "t3", workspace_id: "w1",
    title: "Send onboarding email to Reliance Jio team",
    description: "Include welcome kit, login credentials, and kickoff invite",
    status: "in_progress", priority: "medium",
    due_at: new Date(Date.now() + 2 * 86400000).toISOString(),
    contact_id: "c2", assigned_to: "u2", created_by: "u1",
    is_overdue: false, created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
  },
  {
    id: "t4", workspace_id: "w1",
    title: "Review Q1 pipeline performance report",
    status: "todo", priority: "medium",
    due_at: new Date(Date.now() + 3 * 86400000).toISOString(),
    assigned_to: "u1", created_by: "u1",
    is_overdue: false, created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
  },
  {
    id: "t5", workspace_id: "w1",
    title: "Call Vikram Singh — HDFC Bank",
    description: "Discuss contract renewal terms and additional seats",
    status: "todo", priority: "high",
    due_at: new Date(Date.now() + 86400000).toISOString(),
    contact_id: "c3", assigned_to: "u2", created_by: "u1",
    is_overdue: false, created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
  },
  {
    id: "t6", workspace_id: "w1",
    title: "Update CRM lead scoring model",
    description: "Refine scoring rules based on last 90 days of won/lost deals",
    status: "todo", priority: "low",
    assigned_to: "u1", created_by: "u1",
    is_overdue: false, created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
  },
  {
    id: "t7", workspace_id: "w1",
    title: "Set up WhatsApp automation for cold leads",
    description: "7-day re-engagement sequence for leads tagged cold",
    status: "done", priority: "medium",
    completed_at: new Date(Date.now() - 86400000).toISOString(),
    assigned_to: "u1", created_by: "u1",
    is_overdue: false, created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
  },
  {
    id: "t8", workspace_id: "w1",
    title: "Close Bajaj Finance deal — final negotiation",
    description: "Negotiate final pricing, get legal sign-off",
    status: "done", priority: "urgent",
    completed_at: new Date(Date.now() - 2 * 86400000).toISOString(),
    deal_id: "d2", assigned_to: "u1", created_by: "u1",
    is_overdue: false, created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
  },
  {
    id: "t9", workspace_id: "w1",
    title: "Migrate legacy contacts from Salesforce",
    description: "Export, clean, and import 3,200 contacts",
    status: "cancelled", priority: "low",
    assigned_to: "u2", created_by: "u1",
    is_overdue: false, created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
  },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatDue(due?: string): { label: string; color: string; isOverdue: boolean } {
  if (!due) return { label: "No due date", color: T.textFaint, isOverdue: false };
  const d = new Date(due);
  const diffMs = d.getTime() - Date.now();
  const diffDays = Math.ceil(diffMs / 86400000);
  if (diffMs < 0)   return { label: `${Math.abs(diffDays)}d overdue`,  color: T.red,   isOverdue: true  };
  if (diffDays === 0) return { label: "Due today",                       color: T.amber, isOverdue: false };
  if (diffDays === 1) return { label: "Due tomorrow",                    color: T.amber, isOverdue: false };
  return { label: `Due ${d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" })}`, color: T.textFaint, isOverdue: false };
}

function getPriorityBorder(priority: TaskPriority): string {
  const borders: Record<TaskPriority, string> = {
    urgent: T.red,
    high: T.amber,
    medium: T.blue,
    low: T.textFaint,
  };
  return borders[priority];
}

// ─── KPI Card ─────────────────────────────────────────────────────────────────

function KpiCard({ icon: Icon, label, value, color, sub }: {
  icon: React.ElementType; label: string; value: number; color: string; sub?: string;
}) {
  return (
    <div
      style={{
        background: `linear-gradient(135deg, #fff, ${T.bg})`,
        border: `1px solid ${T.border}`,
        borderRadius: "12px",
        padding: "16px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
        borderBottom: `3px solid ${color}`,
        cursor: "pointer",
        transition: "all 0.3s ease",
        position: "relative",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = "0 4px 16px rgba(0,0,0,0.08)";
        e.currentTarget.style.transform = "translateY(-2px)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.04)";
        e.currentTarget.style.transform = "translateY(0)";
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <div
          style={{
            width: "36px",
            height: "36px",
            borderRadius: "10px",
            background: `${color}12`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <Icon style={{ width: 16, height: 16, color }} />
        </div>
        <div>
          <p style={{ fontSize: "24px", fontWeight: "bold", lineHeight: "1", color: T.text, margin: "0" }}>
            {value}
          </p>
          <p style={{ fontSize: "11px", fontWeight: "500", marginTop: "6px", color: T.textMuted, margin: "6px 0 0 0" }}>
            {label}
          </p>
          {sub && <p style={{ fontSize: "10px", marginTop: "4px", color: T.textFaint, margin: "4px 0 0 0" }}>{sub}</p>}
        </div>
      </div>
    </div>
  );
}

// ─── Priority Badge ───────────────────────────────────────────────────────────

function PriorityBadge({ priority }: { priority: TaskPriority }) {
  const cfg = PRIORITY_CONFIG[priority];
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        paddingLeft: "8px",
        paddingRight: "8px",
        paddingTop: "4px",
        paddingBottom: "4px",
        borderRadius: "20px",
        fontSize: "10px",
        fontWeight: "bold",
        textTransform: "uppercase",
        letterSpacing: "0.5px",
        background: cfg.bg,
        color: cfg.color,
      }}
    >
      <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: cfg.dot, flexShrink: 0 }} />
      {cfg.label}
    </span>
  );
}

// ─── Task Card (Kanban) ────────────────────────────────────────────────────────

function TaskCardKanban({ task, onEdit, onStatusChange }: {
  task: Task;
  onEdit: (t: Task) => void;
  onStatusChange: (id: string, s: TaskStatus) => void;
}) {
  const due = formatDue(task.due_at);
  const priorityBorder = getPriorityBorder(task.priority);
  const NEXT: Partial<Record<TaskStatus, TaskStatus>> = { todo: "in_progress", in_progress: "done" };
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      style={{
        padding: "12px",
        background: task.is_overdue ? "rgba(239,68,68,0.04)" : T.surface,
        borderLeft: `4px solid ${priorityBorder}`,
        borderRadius: "8px",
        border: `1px solid ${task.is_overdue ? "rgba(239,68,68,0.15)" : T.border}`,
        cursor: "pointer",
        transition: "all 0.3s ease",
        boxShadow: isHovered ? "0 4px 16px rgba(0,0,0,0.08)" : "0 1px 3px rgba(0,0,0,0.04)",
        transform: isHovered ? "translateY(-1px)" : "translateY(0)",
        marginBottom: "8px",
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onEdit(task)}
    >
      <div style={{ display: "flex", gap: "10px" }}>
        <button
          style={{
            flexShrink: 0,
            width: "20px",
            height: "20px",
            borderRadius: "50%",
            border: `2px solid ${task.status === "done" ? T.green : task.status === "cancelled" ? T.textFaint : T.border}`,
            background: task.status === "done" ? T.green : task.status === "cancelled" ? T.borderSub : T.surface,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            marginTop: "2px",
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "scale(1.1)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "scale(1)";
          }}
          onClick={(e) => {
            e.stopPropagation();
            const next = NEXT[task.status];
            if (next) onStatusChange(task.id, next);
          }}
        >
          {(task.status === "done" || task.status === "cancelled") && (
            <CheckCircle2 style={{ width: 10, height: 10, color: task.status === "done" ? "#fff" : T.textFaint }} />
          )}
        </button>

        <div style={{ flex: 1, minWidth: 0 }}>
          <p
            style={{
              fontSize: "13px",
              fontWeight: "600",
              color: task.status === "done" || task.status === "cancelled" ? T.textFaint : T.text,
              textDecoration: task.status === "done" ? "line-through" : "none",
              margin: "0 0 4px 0",
              lineHeight: "1.4",
            }}
          >
            {task.title}
          </p>

          {task.description && (
            <p
              style={{
                fontSize: "11px",
                color: T.textMuted,
                margin: "0 0 8px 0",
                overflow: "hidden",
                textOverflow: "ellipsis",
                display: "-webkit-box",
                WebkitLineClamp: 2,
                WebkitBoxOrient: "vertical",
              }}
            >
              {task.description}
            </p>
          )}

          <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
            <PriorityBadge priority={task.priority} />
            {task.is_overdue && (
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "4px",
                  fontSize: "9px",
                  fontWeight: "bold",
                  background: "rgba(239,68,68,0.10)",
                  color: T.red,
                  padding: "3px 6px",
                  borderRadius: "4px",
                }}
              >
                <AlertCircle style={{ width: 8, height: 8 }} />
                Overdue
              </span>
            )}
            <span
              style={{
                fontSize: "10px",
                color: due.color,
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <Clock style={{ width: 10, height: 10 }} />
              {due.label}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Kanban Column ────────────────────────────────────────────────────────────

function StatusColumn({ status, tasks, onEdit, onStatusChange, onAdd }: {
  status: TaskStatus;
  tasks: Task[];
  onEdit: (t: Task) => void;
  onStatusChange: (id: string, s: TaskStatus) => void;
  onAdd: (s: TaskStatus) => void;
}) {
  const cfg = STATUS_CONFIG[status];
  const Icon = cfg.icon;
  const overdueCount = tasks.filter(t => t.is_overdue).length;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "14px 16px",
          background: cfg.bg,
          border: `1px solid ${cfg.border}`,
          borderRadius: "12px 12px 0 0",
          borderBottom: "none",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Icon style={{ width: 14, height: 14, color: cfg.color }} />
          <span style={{ fontSize: "12px", fontWeight: "bold", color: cfg.color }}>
            {cfg.label}
          </span>
          <span
            style={{
              fontSize: "10px",
              fontWeight: "bold",
              padding: "4px 8px",
              borderRadius: "12px",
              background: `${cfg.color}18`,
              color: cfg.color,
            }}
          >
            {tasks.length}
          </span>
          {overdueCount > 0 && (
            <span
              style={{
                fontSize: "10px",
                fontWeight: "bold",
                padding: "4px 8px",
                borderRadius: "12px",
                background: "rgba(239,68,68,0.12)",
                color: T.red,
              }}
            >
              {overdueCount} late
            </span>
          )}
        </div>
        <button
          onClick={() => onAdd(status)}
          style={{
            padding: "6px",
            borderRadius: "8px",
            background: "transparent",
            border: "none",
            color: cfg.color,
            cursor: "pointer",
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = `${cfg.color}10`;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
          }}
        >
          <Plus style={{ width: 14, height: 14 }} />
        </button>
      </div>

      <div
        style={{
          flex: 1,
          borderRadius: "0 0 12px 12px",
          overflow: "hidden",
          minHeight: "120px",
          border: `1px solid ${cfg.border}`,
          borderTop: "none",
          background: T.bg,
          padding: "12px",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {tasks.length === 0 ? (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", flex: 1, gap: "8px" }}>
            <Icon style={{ width: 28, height: 28, color: T.borderSub }} />
            <p style={{ fontSize: "12px", color: T.textFaint, margin: 0 }}>No tasks</p>
            <p style={{ fontSize: "11px", color: T.textFaint, margin: 0 }}>Add one to get started</p>
          </div>
        ) : (
          <div>
            {tasks.map(task => (
              <TaskCardKanban key={task.id} task={task} onEdit={onEdit} onStatusChange={onStatusChange} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Task Card (List) ─────────────────────────────────────────────────────────

function TaskCardList({ task, onEdit, onStatusChange, alternating }: {
  task: Task;
  onEdit: (t: Task) => void;
  onStatusChange: (id: string, s: TaskStatus) => void;
  alternating: boolean;
}) {
  const due = formatDue(task.due_at);
  const priorityBorder = getPriorityBorder(task.priority);
  const NEXT: Partial<Record<TaskStatus, TaskStatus>> = { todo: "in_progress", in_progress: "done" };
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        padding: "14px 20px",
        borderBottom: `1px solid ${T.border}`,
        background: alternating ? T.bg : T.surface,
        transition: "all 0.2s ease",
        backgroundColor: isHovered ? T.bg : undefined,
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onEdit(task)}
    >
      {/* Status circle */}
      <button
        style={{
          flexShrink: 0,
          width: "24px",
          height: "24px",
          borderRadius: "50%",
          border: `2px solid ${task.status === "done" ? T.green : task.status === "cancelled" ? T.textFaint : T.border}`,
          background: task.status === "done" ? T.green : task.status === "cancelled" ? T.borderSub : T.surface,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          transition: "all 0.2s ease",
        }}
        onClick={(e) => {
          e.stopPropagation();
          const next = NEXT[task.status];
          if (next) onStatusChange(task.id, next);
        }}
      >
        {(task.status === "done" || task.status === "cancelled") && (
          <CheckCircle2 style={{ width: 10, height: 10, color: task.status === "done" ? "#fff" : T.textFaint }} />
        )}
      </button>

      {/* Priority dot */}
      <div
        style={{
          width: "8px",
          height: "8px",
          borderRadius: "50%",
          background: priorityBorder,
          flexShrink: 0,
        }}
      />

      {/* Title */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <p
          style={{
            fontSize: "13px",
            fontWeight: "500",
            color: task.status === "done" || task.status === "cancelled" ? T.textFaint : T.text,
            textDecoration: task.status === "done" ? "line-through" : "none",
            margin: 0,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {task.title}
        </p>
      </div>

      {/* Assignee */}
      <div
        style={{
          width: "32px",
          height: "32px",
          borderRadius: "50%",
          background: T.accentLight,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <span style={{ fontSize: "12px", fontWeight: "bold", color: T.accent }}>A</span>
      </div>

      {/* Due date */}
      <span
        style={{
          fontSize: "12px",
          color: due.color,
          display: "flex",
          alignItems: "center",
          gap: "4px",
          whiteSpace: "nowrap",
          minWidth: "100px",
        }}
      >
        <Clock style={{ width: 12, height: 12 }} />
        {due.label}
      </span>

      {/* Status badge */}
      <span
        style={{
          fontSize: "11px",
          fontWeight: "600",
          padding: "4px 10px",
          borderRadius: "20px",
          background: STATUS_CONFIG[task.status].bg,
          color: STATUS_CONFIG[task.status].color,
          whiteSpace: "nowrap",
        }}
      >
        {STATUS_CONFIG[task.status].label}
      </span>

      {/* Edit button */}
      {isHovered && (
        <button
          style={{
            padding: "6px",
            borderRadius: "6px",
            background: "transparent",
            border: "none",
            color: T.textMuted,
            cursor: "pointer",
            transition: "all 0.2s ease",
          }}
          onClick={(e) => {
            e.stopPropagation();
            onEdit(task);
          }}
        >
          <Edit2 style={{ width: 14, height: 14 }} />
        </button>
      )}
    </div>
  );
}

// ─── Create / Edit Drawer ─────────────────────────────────────────────────────

function TaskDrawer({ task, onClose, onSave }: {
  task: Partial<Task> | null;
  onClose: () => void;
  onSave: (t: Partial<Task>) => void;
}) {
  const isNew = !task?.id;
  const [form, setForm] = useState<Partial<Task>>({
    title:       task?.title       ?? "",
    description: task?.description ?? "",
    status:      task?.status      ?? "todo",
    priority:    task?.priority    ?? "medium",
    due_at:      task?.due_at ? new Date(task.due_at).toISOString().slice(0, 16) : "",
  });
  const update = (k: keyof Task, v: any) => setForm((f: Partial<Task>) => ({ ...f, [k]: v }));

  return (
    <>
      <div
        style={{
          position: "fixed",
          inset: 0,
          zIndex: 40,
          background: "rgba(0,0,0,0.25)",
          backdropFilter: "blur(2px)",
        }}
        onClick={onClose}
      />
      <div
        style={{
          position: "fixed",
          right: 0,
          top: 0,
          bottom: 0,
          zIndex: 50,
          display: "flex",
          flexDirection: "column",
          width: "min(480px, 95vw)",
          background: T.surface,
          boxShadow: "-8px 0 40px rgba(0,0,0,0.12)",
          borderLeft: `1px solid ${T.border}`,
          animation: "slideIn 0.3s ease-out",
        }}
      >
        <style>{`
          @keyframes slideIn {
            from {
              transform: translateX(100%);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
        `}</style>

        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "20px", borderBottom: `1px solid ${T.border}` }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{ width: "32px", height: "32px", borderRadius: "10px", background: T.accentLight, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <CheckSquare style={{ width: 16, height: 16, color: T.accent }} />
            </div>
            <h2 style={{ fontSize: "16px", fontWeight: "bold", color: T.text, margin: 0 }}>
              {isNew ? "New Task" : "Edit Task"}
            </h2>
          </div>
          <button
            onClick={onClose}
            style={{
              padding: "8px",
              borderRadius: "8px",
              background: "transparent",
              border: "none",
              color: T.textMuted,
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = T.borderSub;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
            }}
          >
            <X style={{ width: 18, height: 18 }} />
          </button>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: "auto", padding: "20px", display: "flex", flexDirection: "column", gap: "20px" }}>
          <div>
            <label style={{ display: "block", fontSize: "11px", fontWeight: "bold", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.5px", color: T.textMuted }}>
              Task Title *
            </label>
            <input
              value={form.title ?? ""}
              onChange={e => update("title", e.target.value)}
              placeholder="What needs to be done?"
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: "10px",
                fontSize: "13px",
                outline: "none",
                border: `1px solid ${T.border}`,
                background: T.borderSub,
                color: T.text,
                transition: "all 0.2s ease",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = T.accent;
                e.currentTarget.style.background = T.surface;
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = T.border;
                e.currentTarget.style.background = T.borderSub;
              }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "11px", fontWeight: "bold", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.5px", color: T.textMuted }}>
              Description
            </label>
            <textarea
              value={form.description ?? ""}
              onChange={e => update("description", e.target.value)}
              placeholder="Add more context…"
              rows={3}
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: "10px",
                fontSize: "13px",
                outline: "none",
                border: `1px solid ${T.border}`,
                background: T.borderSub,
                color: T.text,
                fontFamily: "inherit",
                resize: "none",
                transition: "all 0.2s ease",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = T.accent;
                e.currentTarget.style.background = T.surface;
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = T.border;
                e.currentTarget.style.background = T.borderSub;
              }}
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: "bold", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.5px", color: T.textMuted }}>
                Status
              </label>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {(Object.keys(STATUS_CONFIG) as TaskStatus[]).map(s => {
                  const cfg = STATUS_CONFIG[s];
                  const Ic = cfg.icon;
                  return (
                    <button
                      key={s}
                      onClick={() => update("status", s)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        padding: "10px 12px",
                        borderRadius: "10px",
                        fontSize: "12px",
                        fontWeight: "600",
                        textAlign: "left",
                        background: form.status === s ? cfg.bg : "transparent",
                        color: form.status === s ? cfg.color : T.textMuted,
                        border: `1px solid ${form.status === s ? cfg.border : T.border}`,
                        cursor: "pointer",
                        transition: "all 0.2s ease",
                      }}
                      onMouseEnter={(e) => {
                        if (form.status !== s) {
                          e.currentTarget.style.background = cfg.bg;
                          e.currentTarget.style.borderColor = cfg.border;
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (form.status !== s) {
                          e.currentTarget.style.background = "transparent";
                          e.currentTarget.style.borderColor = T.border;
                        }
                      }}
                    >
                      <Ic style={{ width: 12, height: 12 }} />
                      {cfg.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <label style={{ display: "block", fontSize: "11px", fontWeight: "bold", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.5px", color: T.textMuted }}>
                Priority
              </label>
              <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                {(Object.keys(PRIORITY_CONFIG) as TaskPriority[]).map(p => {
                  const cfg = PRIORITY_CONFIG[p];
                  return (
                    <button
                      key={p}
                      onClick={() => update("priority", p)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        padding: "10px 12px",
                        borderRadius: "10px",
                        fontSize: "12px",
                        fontWeight: "600",
                        textAlign: "left",
                        background: form.priority === p ? cfg.bg : "transparent",
                        color: form.priority === p ? cfg.color : T.textMuted,
                        border: `1px solid ${form.priority === p ? cfg.color + "40" : T.border}`,
                        cursor: "pointer",
                        transition: "all 0.2s ease",
                      }}
                      onMouseEnter={(e) => {
                        if (form.priority !== p) {
                          e.currentTarget.style.background = cfg.bg;
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (form.priority !== p) {
                          e.currentTarget.style.background = "transparent";
                        }
                      }}
                    >
                      <span style={{ width: "8px", height: "8px", borderRadius: "50%", flexShrink: 0, background: cfg.dot }} />
                      {cfg.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <div>
            <label style={{ display: "block", fontSize: "11px", fontWeight: "bold", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.5px", color: T.textMuted }}>
              Due Date
            </label>
            <input
              type="datetime-local"
              value={form.due_at as string ?? ""}
              onChange={e => update("due_at", e.target.value)}
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: "10px",
                fontSize: "13px",
                outline: "none",
                border: `1px solid ${T.border}`,
                background: T.borderSub,
                color: T.text,
                transition: "all 0.2s ease",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = T.accent;
                e.currentTarget.style.background = T.surface;
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = T.border;
                e.currentTarget.style.background = T.borderSub;
              }}
            />
          </div>
        </div>

        {/* Footer */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "16px 20px", borderTop: `1px solid ${T.border}` }}>
          <button
            onClick={onClose}
            style={{
              flex: 1,
              padding: "10px",
              borderRadius: "10px",
              fontSize: "13px",
              fontWeight: "600",
              background: T.borderSub,
              color: T.textMuted,
              border: `1px solid ${T.border}`,
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = T.border;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = T.borderSub;
            }}
          >
            Cancel
          </button>
          <button
            onClick={() => onSave({ ...task, ...form, due_at: form.due_at ? new Date(form.due_at as string).toISOString() : undefined })}
            disabled={!form.title?.trim()}
            style={{
              flex: 1,
              padding: "10px",
              borderRadius: "10px",
              fontSize: "13px",
              fontWeight: "bold",
              background: form.title?.trim() ? `linear-gradient(135deg, ${T.accent}, ${T.indigo})` : T.borderSub,
              color: form.title?.trim() ? "#fff" : T.textFaint,
              border: "none",
              cursor: form.title?.trim() ? "pointer" : "not-allowed",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              if (form.title?.trim()) {
                e.currentTarget.style.boxShadow = "0 4px 12px rgba(124,58,237,0.3)";
              }
            }}
            onMouseLeave={(e) => {
              if (form.title?.trim()) {
                e.currentTarget.style.boxShadow = "none";
              }
            }}
          >
            {isNew ? "Create Task" : "Save Changes"}
          </button>
        </div>
      </div>
    </>
  );
}

// ─── Filter tabs ──────────────────────────────────────────────────────────────

const FILTER_TABS = [
  { key: "all",     label: "All Tasks"   },
  { key: "urgent",  label: "Urgent"      },
  { key: "overdue", label: "Overdue"     },
  { key: "today",   label: "Due Today"   },
];

const STATUS_ORDER: TaskStatus[] = ["todo", "in_progress", "done", "cancelled"];

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function TasksPage() {
  const queryClient = useQueryClient();
  const [search,     setSearch]     = useState("");
  const [filterTab,  setFilterTab]  = useState("all");
  const [drawerTask, setDrawerTask] = useState<Partial<Task> | null | false>(false);
  const [viewMode,   setViewMode]   = useState<"kanban" | "list">("kanban");

  // ── Fetch ──────────────────────────────────────────────────────────────────
  const { data: apiData, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["tasks"],
    queryFn:  async () => {
      const r = await apiClient.get("/tasks?page=1&limit=100");
      return r.data;
    },
    staleTime: 30_000,
    retry: false,
  });

  const rawTasks: Task[] = useMemo(() => {
    const items = apiData?.data ?? [];
    return items.length > 0 ? items : DEMO_TASKS;
  }, [apiData]);

  const tasks = useMemo(() =>
    rawTasks.map(t => ({
      ...t,
      is_overdue: t.status !== "done" && t.status !== "cancelled" && !!t.due_at && new Date(t.due_at) < new Date(),
    })), [rawTasks]);

  // ── Mutations ──────────────────────────────────────────────────────────────
  const saveMutation = useMutation({
    mutationFn: async (task: Partial<Task>) => {
      if (task.id) return apiClient.put(`/tasks/${task.id}`, task);
      return apiClient.post("/tasks", task);
    },
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["tasks"] }); setDrawerTask(false); },
    onError:   () => { setDrawerTask(false); },
  });

  const updateStatus = useCallback((id: string, status: TaskStatus) => {
    queryClient.setQueryData(["tasks"], (old: any) => {
      if (!old?.data) return old;
      return { ...old, data: old.data.map((t: Task) => t.id === id ? { ...t, status } : t) };
    });
  }, [queryClient]);

  // ── Filter ─────────────────────────────────────────────────────────────────
  const filtered = useMemo(() => tasks.filter(t => {
    const now = new Date();
    const due = t.due_at ? new Date(t.due_at) : null;
    const matchTab =
      filterTab === "all"     ? true :
      filterTab === "urgent"  ? t.priority === "urgent" :
      filterTab === "overdue" ? t.is_overdue :
      filterTab === "today"   ? !!(due && due.toDateString() === now.toDateString()) : true;
    const matchSearch = !search ||
      t.title.toLowerCase().includes(search.toLowerCase()) ||
      (t.description ?? "").toLowerCase().includes(search.toLowerCase());
    return matchTab && matchSearch;
  }), [tasks, filterTab, search]);

  // ── Kanban groups ──────────────────────────────────────────────────────────
  const byStatus = useMemo(() => {
    const g: Record<TaskStatus, Task[]> = { todo: [], in_progress: [], done: [], cancelled: [] };
    filtered.forEach(t => { if (g[t.status]) g[t.status].push(t); });
    return g;
  }, [filtered]);

  // ── KPIs ───────────────────────────────────────────────────────────────────
  const kpis = [
    { icon: CheckSquare,  label: "Total Tasks",  value: tasks.length,                                               color: T.accent },
    { icon: RefreshCw,    label: "In Progress",  value: tasks.filter(t => t.status === "in_progress").length,       color: T.blue   },
    { icon: CheckCircle2, label: "Completed",    value: tasks.filter(t => t.status === "done").length,              color: T.green  },
    { icon: AlertCircle,  label: "Overdue",      value: tasks.filter(t => t.is_overdue).length,                     color: T.red    },
    { icon: Flame,        label: "Urgent",       value: tasks.filter(t => t.priority === "urgent").length,          color: T.amber  },
    { icon: Clock,        label: "Due Today",    value: tasks.filter(t => t.due_at && new Date(t.due_at).toDateString() === new Date().toDateString()).length, color: T.teal },
  ];

  const openDrawer = useCallback((task?: Partial<Task>, defaultStatus?: TaskStatus) => {
    setDrawerTask(task ?? { status: defaultStatus ?? "todo", priority: "medium" });
  }, []);

  const doneCount  = tasks.filter(t => t.status === "done").length;
  const donePct    = tasks.length ? Math.round((doneCount / tasks.length) * 100) : 0;
  const overdueCount = tasks.filter(t => t.is_overdue).length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", padding: "24px", maxWidth: "100%", animation: "fadeIn 0.3s ease-in" }}>
      <style>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(4px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>

      {/* ── Top bar ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "16px", flexWrap: "wrap" }}>
        <div>
          <h1 style={{ fontSize: "20px", fontWeight: "bold", color: T.text, margin: "0 0 6px 0" }}>Tasks</h1>
          <p style={{ fontSize: "13px", color: T.textMuted, margin: 0 }}>
            {tasks.length} tasks · {overdueCount} overdue
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {/* View toggle */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px", padding: "6px", borderRadius: "10px", background: T.borderSub, border: `1px solid ${T.border}` }}>
            {(["kanban", "list"] as const).map(v => (
              <button
                key={v}
                onClick={() => setViewMode(v)}
                style={{
                  padding: "8px 12px",
                  borderRadius: "8px",
                  fontSize: "11px",
                  fontWeight: "600",
                  textTransform: "capitalize",
                  background: viewMode === v ? T.surface : "transparent",
                  color: viewMode === v ? T.text : T.textMuted,
                  border: `1px solid ${viewMode === v ? T.border : "transparent"}`,
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                {v === "kanban" ? <Columns style={{ width: 12, height: 12 }} /> : <List style={{ width: 12, height: 12 }} />}
                {v}
              </button>
            ))}
          </div>

          {/* New task button */}
          <button
            onClick={() => openDrawer()}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              padding: "10px 16px",
              borderRadius: "10px",
              fontSize: "12px",
              fontWeight: "bold",
              background: `linear-gradient(135deg, ${T.accent}, ${T.indigo})`,
              color: "#fff",
              border: "none",
              cursor: "pointer",
              transition: "all 0.2s ease",
              boxShadow: "0 2px 8px rgba(124,58,237,0.2)",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = "0 4px 16px rgba(124,58,237,0.3)";
              e.currentTarget.style.transform = "translateY(-1px)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = "0 2px 8px rgba(124,58,237,0.2)";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            <Plus style={{ width: 14, height: 14 }} />
            New Task
          </button>
        </div>
      </div>

      {/* ── KPI strip ── */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "16px" }}>
        {kpis.map((k, i) => <KpiCard key={i} {...k} />)}
      </div>

      {/* ── Overdue alert ── */}
      {overdueCount > 0 && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "16px",
            borderRadius: "12px",
            background: "rgba(239,68,68,0.06)",
            border: "1px solid rgba(239,68,68,0.20)",
            flexWrap: "wrap",
            gap: "12px",
            animation: "slideDown 0.3s ease-out",
          }}
        >
          <style>{`
            @keyframes slideDown {
              from {
                opacity: 0;
                transform: translateY(-8px);
              }
              to {
                opacity: 1;
                transform: translateY(0);
              }
            }
          `}</style>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <AlertCircle style={{ width: 20, height: 20, color: T.red, flexShrink: 0 }} />
            <p style={{ fontSize: "13px", fontWeight: "600", color: T.red, margin: 0 }}>
              {overdueCount} overdue {overdueCount === 1 ? "task needs" : "tasks need"} your attention
            </p>
          </div>
          <button
            onClick={() => setFilterTab("overdue")}
            style={{
              fontSize: "12px",
              fontWeight: "bold",
              padding: "8px 14px",
              borderRadius: "8px",
              background: T.red,
              color: "#fff",
              border: "none",
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = "0 4px 12px rgba(239,68,68,0.3)";
              e.currentTarget.style.transform = "translateY(-1px)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = "none";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            View overdue
          </button>
        </div>
      )}

      {/* ── Search + Filters ── */}
      <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            flex: "1 1 200px",
            padding: "10px 14px",
            borderRadius: "10px",
            border: `1px solid ${T.border}`,
            background: T.surface,
            transition: "all 0.2s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = T.accent;
            e.currentTarget.style.boxShadow = "0 0 0 3px rgba(124,58,237,0.1)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = T.border;
            e.currentTarget.style.boxShadow = "none";
          }}
        >
          <Search style={{ width: 14, height: 14, color: T.textMuted, flexShrink: 0 }} />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search tasks…"
            style={{
              flex: 1,
              fontSize: "13px",
              outline: "none",
              background: "transparent",
              border: "none",
              color: T.text,
            }}
          />
          {search && (
            <button
              onClick={() => setSearch("")}
              style={{
                padding: "4px",
                borderRadius: "4px",
                background: "transparent",
                border: "none",
                color: T.textFaint,
                cursor: "pointer",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = T.borderSub;
                e.currentTarget.style.color = T.textMuted;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "transparent";
                e.currentTarget.style.color = T.textFaint;
              }}
            >
              <X style={{ width: 14, height: 14 }} />
            </button>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "6px", overflowX: "auto", paddingBottom: "2px" }}>
          {FILTER_TABS.map(({ key, label }) => {
            const active = filterTab === key;
            return (
              <button
                key={key}
                onClick={() => setFilterTab(key)}
                style={{
                  padding: "8px 14px",
                  borderRadius: "10px",
                  fontSize: "11px",
                  fontWeight: "600",
                  whiteSpace: "nowrap",
                  background: active ? T.accent : T.surface,
                  color: active ? "#fff" : T.textMuted,
                  border: `1px solid ${active ? T.accent : T.border}`,
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                }}
                onMouseEnter={(e) => {
                  if (!active) {
                    e.currentTarget.style.background = T.borderSub;
                  }
                }}
                onMouseLeave={(e) => {
                  if (!active) {
                    e.currentTarget.style.background = T.surface;
                  }
                }}
              >
                {label}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Main view ── */}
      {isLoading ? (
        <div
          style={{
            padding: "48px 20px",
            borderRadius: "12px",
            background: T.surface,
            border: `1px solid ${T.border}`,
            textAlign: "center",
          }}
        >
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "50%",
              border: `2px solid ${T.borderSub}`,
              borderTopColor: T.accent,
              margin: "0 auto 12px",
              animation: "spin 1s linear infinite",
            }}
          />
          <style>{`
            @keyframes spin {
              to {
                transform: rotate(360deg);
              }
            }
          `}</style>
          <p style={{ fontSize: "13px", color: T.textMuted, margin: 0 }}>Loading tasks…</p>
        </div>
      ) : viewMode === "kanban" ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "16px", alignItems: "start" }}>
          {STATUS_ORDER.map(status => (
            <StatusColumn
              key={status}
              status={status}
              tasks={byStatus[status]}
              onEdit={openDrawer}
              onStatusChange={updateStatus}
              onAdd={s => openDrawer(undefined, s)}
            />
          ))}
        </div>
      ) : (
        <div style={{ borderRadius: "12px", border: `1px solid ${T.border}`, background: T.surface, overflow: "hidden" }}>
          {filtered.length === 0 ? (
            <div style={{ padding: "48px 20px", textAlign: "center" }}>
              <CheckSquare style={{ width: 40, height: 40, color: T.borderSub, margin: "0 auto 12px" }} />
              <p style={{ fontSize: "13px", fontWeight: "600", color: T.textMuted, margin: 0 }}>No tasks match your filter</p>
            </div>
          ) : (
            <>
              {filtered.map((task, idx) => (
                <TaskCardList
                  key={task.id}
                  task={task}
                  onEdit={openDrawer}
                  onStatusChange={updateStatus}
                  alternating={idx % 2 === 1}
                />
              ))}
              <div style={{ padding: "12px 20px", textAlign: "right", borderTop: `1px solid ${T.border}` }}>
                <span style={{ fontSize: "11px", color: T.textFaint }}>
                  {filtered.length} task{filtered.length !== 1 ? "s" : ""}
                </span>
              </div>
            </>
          )}
        </div>
      )}

      {/* ── Progress strip ── */}
      <div
        style={{
          borderRadius: "12px",
          border: `1px solid ${T.accent}15`,
          background: `linear-gradient(135deg, ${T.accent}06, ${T.teal}06)`,
          padding: "20px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "10px",
                background: T.accentLight,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Activity style={{ width: 18, height: 18, color: T.accent }} />
            </div>
            <div>
              <p style={{ fontSize: "13px", fontWeight: "bold", color: T.text, margin: "0 0 8px 0" }}>
                {doneCount} of {tasks.length} tasks completed
              </p>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <div
                  style={{
                    width: "140px",
                    height: "6px",
                    borderRadius: "10px",
                    overflow: "hidden",
                    background: T.borderSub,
                  }}
                >
                  <div
                    style={{
                      height: "100%",
                      borderRadius: "10px",
                      width: `${donePct}%`,
                      background: `linear-gradient(90deg, ${T.green}, ${T.teal})`,
                      transition: "width 0.5s ease",
                    }}
                  />
                </div>
                <span style={{ fontSize: "11px", color: T.textMuted, fontWeight: "600", minWidth: "45px" }}>
                  {donePct}% done
                </span>
              </div>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <Link
              href="/activity"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "10px 14px",
                borderRadius: "10px",
                fontSize: "12px",
                fontWeight: "600",
                background: T.surface,
                border: `1px solid ${T.border}`,
                color: T.textMuted,
                textDecoration: "none",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = T.borderSub;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = T.surface;
              }}
            >
              <Activity style={{ width: 12, height: 12 }} />
              Activity
            </Link>
            <Link
              href="/reports"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "10px 14px",
                borderRadius: "10px",
                fontSize: "12px",
                fontWeight: "bold",
                background: `linear-gradient(135deg, ${T.accent}, ${T.indigo})`,
                color: "#fff",
                textDecoration: "none",
                transition: "all 0.2s ease",
                boxShadow: "0 2px 8px rgba(124,58,237,0.2)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = "0 4px 16px rgba(124,58,237,0.3)";
                e.currentTarget.style.transform = "translateY(-1px)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = "0 2px 8px rgba(124,58,237,0.2)";
                e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              <ArrowUpRight style={{ width: 12, height: 12 }} />
              Reports
            </Link>
          </div>
        </div>
      </div>

      {/* ── FAB (Floating Action Button) ── */}
      <button
        onClick={() => openDrawer()}
        style={{
          position: "fixed",
          bottom: "32px",
          right: "32px",
          width: "56px",
          height: "56px",
          borderRadius: "50%",
          background: `linear-gradient(135deg, ${T.accent}, ${T.indigo})`,
          color: "#fff",
          border: "none",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 4px 16px rgba(124,58,237,0.3)",
          transition: "all 0.3s ease",
          zIndex: 30,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.boxShadow = "0 8px 24px rgba(124,58,237,0.4)";
          e.currentTarget.style.transform = "scale(1.1)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.boxShadow = "0 4px 16px rgba(124,58,237,0.3)";
          e.currentTarget.style.transform = "scale(1)";
        }}
      >
        <Plus style={{ width: 24, height: 24 }} />
      </button>

      {/* ── Drawer ── */}
      {drawerTask !== false && (
        <TaskDrawer
          task={drawerTask}
          onClose={() => setDrawerTask(false)}
          onSave={task => saveMutation.mutate(task)}
        />
      )}
    </div>
  );
}
