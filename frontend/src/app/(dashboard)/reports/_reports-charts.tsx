"use client";

/**
 * Charts for Reports Page
 * Separated to avoid Turbopack module factory issues with recharts
 */

import React from "react";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";

// Design tokens (mirrored from page.tsx)
const T = {
  accent:      "#7C3AED",
  accentLight: "rgba(124,58,237,0.07)",
  accentBorder:"rgba(124,58,237,0.14)",
  green:       "#059669",
  greenLight:  "rgba(5,150,105,0.08)",
  red:         "#DC2626",
  redLight:    "rgba(220,38,38,0.08)",
  blue:        "#3B82F6",
  blueLight:   "rgba(59,130,246,0.08)",
  amber:       "#D97706",
  amberLight:  "rgba(217,119,6,0.08)",
  border:      "#E9EAEC",
  borderSub:   "#F3F4F6",
  text:        "#111827",
  textSub:     "#6B7280",
  textMuted:   "#9CA3AF",
  surface:     "#ffffff",
  bg:          "#F9FAFB",
} as const;

// ─── Formatter ──────────────────────────────────────────────────────────

function fmt(n: number): string {
  if (n >= 10_000_000) return `₹${(n / 10_000_000).toFixed(1)}Cr`;
  if (n >= 100_000)    return `₹${(n / 100_000).toFixed(1)}L`;
  if (n >= 1_000)      return `₹${(n / 1_000).toFixed(0)}K`;
  return `₹${n}`;
}

// ─── Custom Tooltip ─────────────────────────────────────────────────────

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="px-3 py-2.5 rounded-xl text-[12px]"
      style={{
        background:   T.surface,
        border:       `1px solid ${T.border}`,
        boxShadow:    "0 4px 16px rgba(0,0,0,0.10)",
        pointerEvents: "none",
      }}
    >
      <p className="font-bold mb-1.5" style={{ color: T.text }}>{label}</p>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span style={{ color: T.textSub }}>{p.name}:</span>
          <span className="font-semibold" style={{ color: T.text }}>
            {p.dataKey === "revenue" ? fmt(p.value) : p.value}
          </span>
        </div>
      ))}
    </div>
  );
}

// ─── Revenue Chart ──────────────────────────────────────────────────────

export function RevenueChart({ data }: { data: any[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -8 }}>
        <defs>
          <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor={T.accent} stopOpacity={0.18} />
            <stop offset="100%" stopColor={T.accent} stopOpacity={0}    />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={T.borderSub} vertical={false} />
        <XAxis
          dataKey="month"
          tick={{ fontSize: 11, fill: T.textMuted }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tickFormatter={(v) => fmt(v)}
          tick={{ fontSize: 10, fill: T.textMuted }}
          axisLine={false}
          tickLine={false}
          width={52}
        />
        <Tooltip content={<ChartTooltip />} />
        <Area
          type="monotone"
          dataKey="revenue"
          name="Revenue"
          stroke={T.accent}
          strokeWidth={2.5}
          fill="url(#revenueGrad)"
          dot={{ r: 3, fill: T.accent, strokeWidth: 0 }}
          activeDot={{ r: 5, fill: T.accent, strokeWidth: 0 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

// ─── Pipeline Chart (Horizontal Bar) ─────────────────────────────────────

export function PipelineChart({ data }: { data: any[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 60 }} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" stroke={T.borderSub} horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 10, fill: T.textMuted }} axisLine={false} tickLine={false} />
        <YAxis
          dataKey="stage"
          type="category"
          tick={{ fontSize: 11, fill: T.text }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            borderRadius: 12,
            border: `1px solid ${T.border}`,
            boxShadow: "0 4px 16px rgba(0,0,0,0.10)",
            fontSize: 12,
            background: T.surface,
          }}
          cursor={{ fill: "rgba(124,58,237,0.04)" }}
        />
        <Bar
          dataKey="count"
          name="Deal Count"
          fill={T.accent}
          radius={[0, 6, 6, 0]}
          maxBarSize={32}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}

// ─── Win/Loss Pie Chart ──────────────────────────────────────────────────

export function WinLossChart({ data }: { data: any[] }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  const winRate = Math.round((data.find((d: any) => d.name === "Won")?.value || 0) / total * 100);

  return (
    <div className="flex flex-col items-center gap-4">
      <ResponsiveContainer width="100%" height={180}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={46}
            outerRadius={68}
            paddingAngle={3}
            dataKey="value"
            strokeWidth={0}
          >
            {data.map((d, i) => (
              <Cell key={i} fill={d.color} />
            ))}
          </Pie>
          <Tooltip
            formatter={(v: number) => [v, ""]}
            contentStyle={{
              borderRadius: 12,
              border: `1px solid ${T.border}`,
              boxShadow: "0 4px 16px rgba(0,0,0,0.10)",
              fontSize: 12,
              background: T.surface,
            }}
          />
        </PieChart>
      </ResponsiveContainer>

      {/* Center label */}
      <div className="text-center">
        <p className="text-[24px] font-bold" style={{ color: T.text }}>{winRate}%</p>
        <p className="text-[11px]" style={{ color: T.textMuted }}>Win Rate</p>
      </div>

      {/* Legend */}
      <div className="space-y-2 w-full">
        {data.map(d => (
          <div key={d.name} className="flex items-center gap-3 text-[12px]">
            <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: d.color }} />
            <span style={{ color: T.textSub }}>{d.name}</span>
            <span className="flex-1" />
            <span className="font-bold" style={{ color: T.text }}>{d.value}</span>
            <span style={{ color: T.textMuted }}>
              {Math.round((d.value / total) * 100)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Deals Closed Chart ──────────────────────────────────────────────────

export function DealsClosedChart({ data }: { data: any[] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={T.borderSub} vertical={false} />
        <XAxis
          dataKey="month"
          tick={{ fontSize: 11, fill: T.textMuted }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 10, fill: T.textMuted }}
          axisLine={false}
          tickLine={false}
          width={24}
        />
        <Tooltip
          contentStyle={{
            borderRadius: 12,
            border: `1px solid ${T.border}`,
            boxShadow: "0 4px 16px rgba(0,0,0,0.10)",
            fontSize: 12,
            background: T.surface,
          }}
        />
        <Bar
          dataKey="deals"
          name="Deals Closed"
          fill={T.accent}
          radius={[6, 6, 0, 0]}
          maxBarSize={44}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
