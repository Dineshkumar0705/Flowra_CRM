"use client";

/**
 * Reports Page — Flowra CRM
 * Premium analytics dashboard with revenue trends, pipeline velocity, and team performance.
 * Recharts components loaded via next/dynamic to avoid Turbopack module factory errors.
 */

import React, { useState } from "react";
import dynamic from "next/dynamic";
import { useQuery } from "@tanstack/react-query";
import {
  TrendingUp, TrendingDown, IndianRupee, Users, Target,
  Award, Download, RefreshCw, CheckCircle2, Zap, Users2, Calendar,
} from "lucide-react";
import apiClient from "@/services/apiClient";

// ─── Dynamic Recharts Imports ──────────────────────────────────────────

const DynamicRevenueChart = dynamic(
  () => import("./_reports-charts").then(m => ({ default: m.RevenueChart })),
  {
    ssr: false,
    loading: () => (
      <div style={{ height: 240, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span style={{ color: "#9CA3AF", fontSize: 12 }}>Loading chart…</span>
      </div>
    ),
  }
);

const DynamicPipelineChart = dynamic(
  () => import("./_reports-charts").then(m => ({ default: m.PipelineChart })),
  {
    ssr: false,
    loading: () => (
      <div style={{ height: 240, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span style={{ color: "#9CA3AF", fontSize: 12 }}>Loading chart…</span>
      </div>
    ),
  }
);

const DynamicWinLossChart = dynamic(
  () => import("./_reports-charts").then(m => ({ default: m.WinLossChart })),
  {
    ssr: false,
    loading: () => (
      <div style={{ height: 240, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span style={{ color: "#9CA3AF", fontSize: 12 }}>Loading chart…</span>
      </div>
    ),
  }
);

const DynamicDealsClosedChart = dynamic(
  () => import("./_reports-charts").then(m => ({ default: m.DealsClosedChart })),
  {
    ssr: false,
    loading: () => (
      <div style={{ height: 200, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span style={{ color: "#9CA3AF", fontSize: 12 }}>Loading chart…</span>
      </div>
    ),
  }
);

// ─── Design tokens ─────────────────────────────────────────────────────────

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

// ─── Static fallback / demo data ───────────────────────────────────────────

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const DEMO_MONTHLY_REVENUE = [
  { month: "Oct", revenue: 420000, deals: 8  },
  { month: "Nov", revenue: 560000, deals: 11 },
  { month: "Dec", revenue: 390000, deals: 7  },
  { month: "Jan", revenue: 710000, deals: 14 },
  { month: "Feb", revenue: 830000, deals: 17 },
  { month: "Mar", revenue: 1120000, deals: 22 },
];

const DEMO_PIPELINE = [
  { stage: "Lead",     count: 48, value: 2400000 },
  { stage: "Proposal", count: 21, value: 1890000 },
  { stage: "Negotiation", count: 12, value: 1440000 },
  { stage: "Won",      count: 9,  value: 1080000 },
];

const DEMO_WIN_LOSS = [
  { name: "Won",  value: 38, color: T.green  },
  { name: "Lost", value: 19, color: T.red    },
  { name: "Open", value: 43, color: T.accent },
];

const DEMO_LEAD_SOURCES = [
  { source: "WhatsApp",  count: 34, color: "#25D366" },
  { source: "Gmail",     count: 27, color: "#EA4335" },
  { source: "Manual",    count: 21, color: T.accent   },
  { source: "Import",    count: 14, color: T.blue     },
  { source: "Web Form",  count: 8,  color: T.amber    },
];

const DEMO_TOP_REPS = [
  { name: "Arjun Sharma",   won: 14, value: 4200000, rate: 74 },
  { name: "Priya Nair",     won: 11, value: 3300000, rate: 68 },
  { name: "Vikram Singh",   won: 9,  value: 2700000, rate: 56 },
  { name: "Ananya Rao",     won: 7,  value: 2100000, rate: 53 },
];

const RANGE_OPTIONS = [
  { key: "30d",  label: "Last 30d"  },
  { key: "90d",  label: "Last 90d"  },
  { key: "1yr",  label: "This Year" },
  { key: "all",  label: "All Time"  },
];

// ─── Helpers ───────────────────────────────────────────────────────────────

function fmtCurrency(n: number): string {
  if (n >= 10_000_000) return `₹${(n / 10_000_000).toFixed(1)}Cr`;
  if (n >= 100_000)    return `₹${(n / 100_000).toFixed(1)}L`;
  if (n >= 1_000)      return `₹${(n / 1_000).toFixed(0)}K`;
  return `₹${n}`;
}

function pct(a: number, b: number): string {
  if (!b) return "0%";
  return `${Math.round((a / b) * 100)}%`;
}

// ─── Sub-components ────────────────────────────────────────────────────────

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-2xl ${className}`}
      style={{
        background: T.surface,
        border: `1px solid ${T.border}`,
        boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
      }}
    >
      {children}
    </div>
  );
}

function SectionHead({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="px-6 pt-6 pb-4" style={{ borderBottom: `1px solid ${T.borderSub}` }}>
      <p className="text-[14px] font-bold" style={{ color: T.text }}>{title}</p>
      {sub && <p className="text-[11px] mt-0.5" style={{ color: T.textMuted }}>{sub}</p>}
    </div>
  );
}

interface KpiCardProps {
  label: string;
  value: string;
  sub: string;
  trend?: number;
  icon: React.ElementType;
  iconColor: string;
  iconBg: string;
  targetPercent?: number;
}

function KpiCard({
  label, value, sub, trend, icon: Icon, iconColor, iconBg, targetPercent = 75
}: KpiCardProps) {
  const up = trend !== undefined && trend > 0;
  const dn = trend !== undefined && trend < 0;

  return (
    <Card>
      <div className="px-5 py-5">
        <div className="flex items-start justify-between gap-2 mb-4">
          <div
            className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: iconBg }}
          >
            <Icon style={{ width: 20, height: 20, color: iconColor }} />
          </div>
          {trend !== undefined && (
            <span
              className="flex items-center gap-0.5 text-[11px] font-bold px-2.5 py-1 rounded-full whitespace-nowrap"
              style={{
                background: up ? T.greenLight : dn ? T.redLight : T.blueLight,
                color:      up ? T.green      : dn ? T.red      : T.blue,
              }}
            >
              {up ? <TrendingUp style={{ width: 11, height: 11 }} /> : <TrendingDown style={{ width: 11, height: 11 }} />}
              {Math.abs(trend)}%
            </span>
          )}
        </div>

        <p className="text-[26px] font-bold leading-none" style={{ color: T.text }}>{value}</p>
        <p className="text-[12px] font-semibold mt-2" style={{ color: T.textSub }}>{label}</p>
        <p className="text-[11px] mt-0.5 mb-4" style={{ color: T.textMuted }}>{sub}</p>

        {/* Progress bar */}
        <div className="h-1.5 rounded-full overflow-hidden" style={{ background: T.borderSub }}>
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${targetPercent}%`,
              background: iconColor,
            }}
          />
        </div>
      </div>
    </Card>
  );
}

function TrendBadge({ value, label }: { value: number; label: string }) {
  const up = value > 0;
  return (
    <span
      className="flex items-center gap-1 text-[12px] font-bold px-3 py-1.5 rounded-full"
      style={{
        background: up ? T.greenLight : T.redLight,
        color: up ? T.green : T.red,
      }}
    >
      {up ? <TrendingUp style={{ width: 12, height: 12 }} /> : <TrendingDown style={{ width: 12, height: 12 }} />}
      {Math.abs(value)}% {label}
    </span>
  );
}

function InsightCard({ icon: Icon, title, value }: { icon: React.ElementType; title: string; value: string }) {
  return (
    <div
      className="flex items-center gap-3 px-4 py-3 rounded-xl"
      style={{ background: T.borderSub }}
    >
      <Icon style={{ width: 18, height: 18, color: T.accent, flexShrink: 0 }} />
      <div>
        <p className="text-[11px]" style={{ color: T.textMuted }}>{title}</p>
        <p className="text-[13px] font-bold" style={{ color: T.text }}>{value}</p>
      </div>
    </div>
  );
}

// ─── Page ──────────────────────────────────────────────────────────────────

export default function ReportsPage() {
  const [range, setRange] = useState("90d");
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch dashboard analytics
  const { data: analyticsData } = useQuery({
    queryKey: ["analytics", "dashboard", range],
    queryFn: async () => {
      const r = await apiClient.get(`/analytics/dashboard?range=${range}`);
      return r.data;
    },
    staleTime: 60_000,
    retry: false,
  });

  // Fetch deals dashboard
  const { data: dealsData } = useQuery({
    queryKey: ["analytics", "deals", range],
    queryFn: async () => {
      const r = await apiClient.get(`/analytics/deals?range=${range}`);
      return r.data;
    },
    staleTime: 60_000,
    retry: false,
  });

  // Merge real + demo data
  const dash = analyticsData?.data ?? null;
  const dealsDash = dealsData?.data ?? null;

  const totalRevenue = dash?.total_revenue ?? 1120000;
  const totalDeals = dash?.total_deals ?? 90;
  const activeDeals = 47;
  const avgDealSize = totalRevenue / Math.max(totalDeals, 1);
  const winRate = dash?.win_rate ?? 62;

  const monthlyRevenue = (dash?.monthly_revenue?.length > 0 ? dash.monthly_revenue : DEMO_MONTHLY_REVENUE).map(
    (m: any) => ({ ...m, month: m.month?.slice(0, 3) ?? m.month })
  );

  const pipelineStages = dealsDash?.deals_by_stage?.length > 0
    ? dealsDash.deals_by_stage
    : DEMO_PIPELINE;

  const maxPipelineValue = Math.max(...DEMO_PIPELINE.map(p => p.value));
  const maxLeadSourceCount = DEMO_LEAD_SOURCES[0].count;

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await new Promise(r => setTimeout(r, 800));
    setIsRefreshing(false);
  };

  return (
    <div className="flex flex-col gap-6">

      {/* ──────── PAGE HEADER ──────── */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-bold leading-none" style={{ color: T.text }}>
            Reports & Analytics
          </h1>
          <p className="text-[13px] mt-2" style={{ color: T.textMuted }}>
            Revenue, pipeline, and team performance insights
          </p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Range selector pills */}
          <div className="flex items-center gap-2 p-1 rounded-xl" style={{ background: T.borderSub }}>
            {RANGE_OPTIONS.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setRange(key)}
                className="px-3 py-2 rounded-lg text-[12px] font-semibold transition-all whitespace-nowrap"
                style={{
                  background: range === key ? T.surface : "transparent",
                  color: range === key ? T.text : T.textMuted,
                  boxShadow: range === key ? "0 1px 3px rgba(0,0,0,0.06)" : "none",
                }}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Refresh button */}
          <button
            onClick={handleRefresh}
            className="flex items-center justify-center w-9 h-9 rounded-lg transition-all"
            style={{
              background: T.borderSub,
              color: T.textMuted,
              transform: isRefreshing ? "rotate(180deg)" : "rotate(0deg)",
              transitionDuration: "0.6s",
            }}
          >
            <RefreshCw style={{ width: 16, height: 16 }} />
          </button>

          {/* Download PDF button */}
          <button
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-[12px] font-semibold transition-all"
            style={{
              background: T.accentLight,
              border: `1px solid ${T.accentBorder}`,
              color: T.accent,
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.background = "rgba(124,58,237,0.12)";
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.background = T.accentLight;
            }}
          >
            <Download style={{ width: 14, height: 14 }} />
            PDF
          </button>
        </div>
      </div>

      {/* ──────── TOP KPI STRIP ──────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Total Revenue"
          value={fmtCurrency(totalRevenue)}
          sub="Closed deals this period"
          trend={23}
          icon={IndianRupee}
          iconColor={T.green}
          iconBg={T.greenLight}
          targetPercent={85}
        />
        <KpiCard
          label="Active Deals"
          value={activeDeals.toString()}
          sub="Currently in pipeline"
          trend={8}
          icon={Target}
          iconColor={T.amber}
          iconBg={T.amberLight}
          targetPercent={68}
        />
        <KpiCard
          label="Win Rate"
          value={`${winRate}%`}
          sub="Won vs. total closed"
          trend={5}
          icon={Award}
          iconColor={T.accent}
          iconBg={T.accentLight}
          targetPercent={winRate}
        />
        <KpiCard
          label="Avg Deal Size"
          value={fmtCurrency(avgDealSize)}
          sub="Average per closed deal"
          trend={-2}
          icon={Users}
          iconColor={T.blue}
          iconBg={T.blueLight}
          targetPercent={72}
        />
      </div>

      {/* ──────── REVENUE TREND + PIPELINE VELOCITY ──────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Revenue Trend (2/3 width) */}
        <Card className="lg:col-span-2">
          <div className="px-6 pt-6 pb-0" style={{ borderBottom: `1px solid ${T.borderSub}` }}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-[14px] font-bold" style={{ color: T.text }}>Revenue Trend</p>
                <p className="text-[11px] mt-0.5" style={{ color: T.textMuted }}>
                  Monthly closed-won revenue and deal count
                </p>
              </div>
              <TrendBadge value={23} label="vs last period" />
            </div>
          </div>
          <div className="px-6 pb-6 pt-6">
            <DynamicRevenueChart data={monthlyRevenue} />
          </div>
        </Card>

        {/* Pipeline Velocity (1/3 width) */}
        <Card>
          <SectionHead
            title="Pipeline Velocity"
            sub="Deal count by stage"
          />
          <div className="px-6 pb-6 pt-6">
            <DynamicPipelineChart data={pipelineStages} />
          </div>
        </Card>
      </div>

      {/* ──────── WIN/LOSS + LEAD SOURCES ──────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* Win/Loss Breakdown */}
        <Card>
          <SectionHead
            title="Win/Loss Breakdown"
            sub="Deal outcomes across all deals"
          />
          <div className="px-6 pb-6 pt-6">
            <DynamicWinLossChart data={DEMO_WIN_LOSS} />
          </div>
        </Card>

        {/* Lead Sources */}
        <Card>
          <SectionHead
            title="Lead Sources"
            sub="Where your contacts are coming from"
          />
          <div className="px-6 pb-6 pt-6 space-y-4">
            {DEMO_LEAD_SOURCES.map((src) => (
              <div key={src.source}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ background: src.color }}
                    />
                    <span className="text-[12px] font-medium" style={{ color: T.text }}>
                      {src.source}
                    </span>
                  </div>
                  <span className="text-[12px] font-bold" style={{ color: T.text }}>
                    {src.count}
                  </span>
                </div>
                <div className="h-2 rounded-full overflow-hidden" style={{ background: T.borderSub }}>
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${(src.count / maxLeadSourceCount) * 100}%`,
                      background: src.color,
                      opacity: 0.85,
                    }}
                  />
                </div>
                <p className="text-[10px] mt-1" style={{ color: T.textMuted }}>
                  {Math.round((src.count / DEMO_LEAD_SOURCES.reduce((s, l) => s + l.count, 0)) * 100)}%
                </p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* ──────── TOP PERFORMERS LEADERBOARD ──────── */}
      <Card>
        <SectionHead
          title="Top Performers"
          sub="Sales reps ranked by deals won and revenue"
        />
        <div className="px-6 pb-6 pt-6">
          {/* Table header */}
          <div
            className="grid gap-4 px-4 py-3 rounded-lg mb-3 text-[10px] font-bold uppercase tracking-wider"
            style={{
              gridTemplateColumns: "1fr 100px 120px 100px",
              background: T.borderSub,
              color: T.textMuted,
            }}
          >
            <span>Rep</span>
            <span className="text-center">Deals Won</span>
            <span className="text-center">Revenue</span>
            <span className="text-right">Win Rate</span>
          </div>

          {/* Rows */}
          {DEMO_TOP_REPS.map((rep, i) => {
            const medals = ["🥇", "🥈", "🥉"];
            const medal = i < 3 ? medals[i] : null;
            return (
              <div
                key={rep.name}
                className="grid gap-4 px-4 py-4 rounded-xl items-center"
                style={{
                  gridTemplateColumns: "1fr 100px 120px 100px",
                  borderBottom: i < DEMO_TOP_REPS.length - 1 ? `1px solid ${T.borderSub}` : "none",
                  background: i < 3 ? T.borderSub : "transparent",
                }}
              >
                {/* Name + rank badge */}
                <div className="flex items-center gap-3">
                  {medal && <span className="text-base">{medal}</span>}
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                    style={{ background: `hsl(${(i * 67 + 260) % 360}, 65%, 55%)` }}
                  >
                    {rep.name.split(" ").map(w => w[0]).join("").slice(0, 2)}
                  </div>
                  <span className="text-[13px] font-semibold" style={{ color: T.text }}>
                    {rep.name}
                  </span>
                </div>

                {/* Deals won */}
                <div className="flex items-center justify-center gap-1.5">
                  <CheckCircle2 style={{ width: 13, height: 13, color: T.green }} />
                  <span className="text-[13px] font-bold" style={{ color: T.text }}>{rep.won}</span>
                </div>

                {/* Revenue */}
                <div className="text-center">
                  <span className="text-[13px] font-bold" style={{ color: T.text }}>
                    {fmtCurrency(rep.value)}
                  </span>
                </div>

                {/* Win rate */}
                <div className="flex items-center justify-end">
                  <span
                    className="text-[12px] font-bold px-2.5 py-1 rounded-full"
                    style={{
                      background:
                        rep.rate >= 65
                          ? T.greenLight
                          : rep.rate >= 50
                          ? T.amberLight
                          : T.redLight,
                      color:
                        rep.rate >= 65
                          ? T.green
                          : rep.rate >= 50
                          ? T.amber
                          : T.red,
                    }}
                  >
                    {rep.rate}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* ──────── DEALS CLOSED OVER TIME ──────── */}
      <Card>
        <SectionHead
          title="Deals Closed per Month"
          sub="Volume of won deals over time"
        />
        <div className="px-6 pb-6 pt-6">
          <DynamicDealsClosedChart data={monthlyRevenue} />
        </div>
      </Card>

      {/* ──────── INSIGHTS STRIP ──────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <InsightCard
          icon={TrendingUp}
          title="Best Month"
          value="March (+34%)"
        />
        <InsightCard
          icon={Zap}
          title="Top Source"
          value="WhatsApp (34%)"
        />
        <InsightCard
          icon={Calendar}
          title="Fastest Close"
          value="8 days avg"
        />
      </div>

    </div>
  );
}
