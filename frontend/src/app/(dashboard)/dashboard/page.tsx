'use client'

/**
 * Dashboard — Flowra CRM
 * Hero greeting card links to every page. Pure-SVG sparkline (no ResponsiveContainer
 * on fixed-size charts). Single-accent design system throughout.
 */

import React from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import {
  Users,
  TrendingUp,
  IndianRupee,
  Target,
  ArrowUpRight,
  ArrowDownRight,
  ChevronRight,
  BarChart3,
  Activity,
  Star,
  CheckCircle2,
  Flame,
  MessageSquare,
  Mail,
  Calendar,
  Bot,
  BellRing,
  ExternalLink,
  CheckSquare,
  Plus,
} from 'lucide-react'
import dynamic from 'next/dynamic'
import apiClient from '@/services/apiClient'

// Dynamic import isolates recharts from Turbopack's build-time module graph.
// recharts cross-imports LineChart inside AreaChart — Turbopack can't wire
// that up statically, so we defer it to client runtime instead.
const RechartsAreaChart = dynamic(() => import('./_area-chart'), {
  ssr: false,
  loading: () => (
    <div
      style={{
        height: 185,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        style={{
          width: 20,
          height: 20,
          borderRadius: '50%',
          border: '2px solid #E9EAEC',
          borderTopColor: '#7C3AED',
          animation: 'spin 0.7s linear infinite',
        }}
      />
    </div>
  ),
})
import { useAuth } from '@/hooks/useAuth'

// ─── Design tokens ────────────────────────────────────────────────────────────

const T = {
  accent: '#7C3AED',
  accentLight: 'rgba(124,58,237,0.07)',
  accentBorder: 'rgba(124,58,237,0.13)',
  border: '#E9EAEC',
  borderSub: '#F3F4F6',
  text: '#111827',
  textSub: '#6B7280',
  textMuted: '#9CA3AF',
  surface: '#ffffff',
  bg: '#F9FAFB',
} as const

// ─── Formatters ───────────────────────────────────────────────────────────────

function fmtCurrency(n: number): string {
  if (n >= 10_000_000) return `₹${(n / 10_000_000).toFixed(1)}Cr`
  if (n >= 100_000) return `₹${(n / 100_000).toFixed(1)}L`
  if (n >= 1_000) return `₹${(n / 1_000).toFixed(1)}K`
  return `₹${n}`
}

// ─── Static data ──────────────────────────────────────────────────────────────

const DEMO_SPARK = [34, 48, 41, 60, 52, 68, 63, 75, 70, 85, 79, 95]
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const INTEGRATIONS = [
  {
    icon: MessageSquare,
    name: 'WhatsApp Business',
    category: 'Messaging',
    stat: '1,284 messages',
    statLabel: 'sent today',
  },
  { icon: Mail, name: 'Gmail', category: 'Email', stat: '4,730 emails', statLabel: 'synced' },
  {
    icon: Calendar,
    name: 'Google Calendar',
    category: 'Calendar',
    stat: '312 events',
    statLabel: 'synchronized',
  },
  {
    icon: Bot,
    name: 'Autopilot',
    category: 'Automation',
    stat: '37 deals',
    statLabel: 'auto-revived',
  },
  {
    icon: IndianRupee,
    name: 'Razorpay',
    category: 'Payments',
    stat: '₹38.4L',
    statLabel: 'revenue tracked',
  },
  {
    icon: BellRing,
    name: 'Notifications',
    category: 'In-App',
    stat: '143 alerts',
    statLabel: 'sent today',
  },
] as const

const AUTOMATION_EVENTS = [
  { icon: Bot, text: 'Autopilot revived 3 stale deals automatically', time: '5m' },
  { icon: MessageSquare, text: 'WhatsApp follow-up sent to 12 contacts', time: '18m' },
  { icon: Mail, text: 'Gmail sequence triggered for Priya Nair', time: '1h' },
] as const

const ACTIVITY_FEED = [
  { icon: Users, title: 'New contact added', sub: 'Arjun Sharma — Tata Consultancy', time: '2m' },
  { icon: TrendingUp, title: 'Deal moved to Proposal', sub: '₹4.5L deal — Infosys', time: '18m' },
  { icon: CheckCircle2, title: 'Deal closed — Won', sub: '₹12L deal — Reliance Jio', time: '1h' },
  { icon: Star, title: 'Contact rescored', sub: 'Priya Nair · 87 → 94', time: '2h' },
  { icon: Flame, title: 'Hot lead detected', sub: 'Vikram Singh — HDFC Bank', time: '3h' },
] as const

const PERF_METRICS = [
  { label: 'Deals Closed', val: '3', delta: '+2', up: true },
  { label: 'Follow-ups', val: '11', delta: '+4', up: true },
  { label: 'Avg Response', val: '2.4h', delta: '−0.8h', up: true },
  { label: 'New Contacts', val: '7', delta: '−1', up: false },
] as const

// Navigation page cards shown in the hero greeting section
const NAV_CARDS = [
  {
    label: 'Contacts',
    icon: Users,
    href: '/contacts',
    color: '#3B82F6',
    bg: 'rgba(59,130,246,0.08)',
    desc: 'Manage leads',
  },
  {
    label: 'Deals',
    icon: TrendingUp,
    href: '/deals',
    color: '#10B981',
    bg: 'rgba(16,185,129,0.08)',
    desc: 'Track pipeline',
  },
  {
    label: 'Tasks',
    icon: CheckSquare,
    href: '/tasks',
    color: '#7C3AED',
    bg: 'rgba(124,58,237,0.08)',
    desc: 'Stay on top',
  },
  {
    label: 'Activity',
    icon: Activity,
    href: '/activity',
    color: '#F59E0B',
    bg: 'rgba(245,158,11,0.08)',
    desc: 'Audit trail',
  },
  {
    label: 'Reports',
    icon: BarChart3,
    href: '/reports',
    color: '#EC4899',
    bg: 'rgba(236,72,153,0.08)',
    desc: 'Analytics',
  },
  {
    label: 'Integrations',
    icon: BellRing,
    href: '/integrations',
    color: '#6B7280',
    bg: 'rgba(107,114,128,0.08)',
    desc: 'Connected apps',
  },
] as const

// ─── Pure SVG sparkline (no ResponsiveContainer needed on fixed sizes) ────────

function Sparkline({
  data,
  width = 72,
  height = 26,
}: {
  data: number[]
  width?: number
  height?: number
}) {
  if (!data.length) return null
  const min = Math.min(...data)
  const max = Math.max(...data)
  const range = max - min || 1
  const pad = 2
  const xs = data.map((_, i) => pad + (i / (data.length - 1)) * (width - pad * 2))
  const ys = data.map((v) => height - pad - ((v - min) / range) * (height - pad * 2))
  const d = xs.map((x, i) => `${i === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${ys[i].toFixed(1)}`).join(' ')
  return (
    <svg width={width} height={height} style={{ overflow: 'visible' }}>
      <path
        d={d}
        fill="none"
        stroke={T.accent}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

// ─── Primitives ───────────────────────────────────────────────────────────────

function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-2xl ${className}`}
      style={{
        background: T.surface,
        border: `1px solid ${T.border}`,
        boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
      }}
    >
      {children}
    </div>
  )
}

function CardHead({
  title,
  sub,
  action,
}: {
  title: string
  sub?: string
  action?: React.ReactNode
}) {
  return (
    <div
      className="flex items-start justify-between px-5 pt-5 pb-4"
      style={{ borderBottom: `1px solid ${T.borderSub}` }}
    >
      <div className="space-y-0.5">
        <p className="text-[13px] font-semibold leading-none" style={{ color: T.text }}>
          {title}
        </p>
        {sub && (
          <p className="text-[11px] font-medium" style={{ color: T.textMuted }}>
            {sub}
          </p>
        )}
      </div>
      {action}
    </div>
  )
}

function IconBox({ icon: Icon, size = 'md' }: { icon: React.ElementType; size?: 'sm' | 'md' }) {
  const dim = size === 'sm' ? { w: 28, h: 28, icon: 13 } : { w: 34, h: 34, icon: 15 }
  return (
    <div
      className="flex items-center justify-center flex-shrink-0 rounded-xl"
      style={{
        width: dim.w,
        height: dim.h,
        background: T.accentLight,
        border: `1px solid ${T.accentBorder}`,
      }}
    >
      <Icon style={{ width: dim.icon, height: dim.icon, color: T.accent }} />
    </div>
  )
}

function TrendBadge({ value }: { value: number }) {
  const up = value >= 0
  return (
    <span
      className="inline-flex items-center gap-0.5 rounded-md font-semibold tabular-nums"
      style={{
        fontSize: 11,
        padding: '2px 6px',
        color: up ? '#059669' : '#DC2626',
        background: up ? 'rgba(5,150,105,0.08)' : 'rgba(220,38,38,0.08)',
      }}
    >
      {up ? (
        <ArrowUpRight style={{ width: 11, height: 11 }} />
      ) : (
        <ArrowDownRight style={{ width: 11, height: 11 }} />
      )}
      {Math.abs(value)}%
    </span>
  )
}

function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`rounded-xl animate-pulse ${className}`} style={{ background: T.borderSub }} />
  )
}

// ─── Stat card ────────────────────────────────────────────────────────────────

interface StatCardProps {
  label: string
  value: string
  icon: React.ElementType
  change?: number
  spark?: number[]
}

function StatCard({ label, value, icon, change, spark }: StatCardProps) {
  return (
    <Card>
      <div className="p-5">
        <div className="flex items-center justify-between mb-5">
          <IconBox icon={icon} size="md" />
          {change !== undefined && <TrendBadge value={change} />}
        </div>
        <p
          className="text-[23px] font-bold leading-none tracking-tight mb-1.5"
          style={{ color: T.text }}
        >
          {value}
        </p>
        <p className="text-[11px] font-medium" style={{ color: T.textMuted }}>
          {label}
        </p>
        {spark && (
          <div className="mt-3 flex justify-end" style={{ opacity: 0.55 }}>
            <Sparkline data={spark} />
          </div>
        )}
      </div>
    </Card>
  )
}

// RechartsAreaChart is dynamically imported above — see the dynamic() call near the top.

// ─── Pipeline row ─────────────────────────────────────────────────────────────

function PipelineRow({ stage, count, pct }: { stage: string; count: number; pct: number }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span
            className="w-1.5 h-1.5 rounded-full flex-shrink-0"
            style={{ background: T.accent }}
          />
          <span className="text-[13px] font-medium capitalize" style={{ color: T.text }}>
            {stage}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[12px] font-semibold tabular-nums" style={{ color: T.text }}>
            {count} deals
          </span>
          <span
            className="text-[11px] tabular-nums text-right"
            style={{ width: 28, color: T.textMuted }}
          >
            {pct}%
          </span>
        </div>
      </div>
      <div className="rounded-full overflow-hidden" style={{ height: 5, background: T.borderSub }}>
        <div
          className="h-full rounded-full"
          style={{
            width: `${pct}%`,
            background: `linear-gradient(90deg, ${T.accent} 0%, #A78BFA 100%)`,
            transition: 'width 0.9s cubic-bezier(0.4,0,0.2,1)',
          }}
        />
      </div>
    </div>
  )
}

// ─── Activity item ────────────────────────────────────────────────────────────

function ActivityItem({
  icon,
  title,
  sub,
  time,
}: {
  icon: React.ElementType
  title: string
  sub: string
  time: string
}) {
  return (
    <div
      className="flex items-start gap-3 py-3"
      style={{ borderBottom: `1px solid ${T.borderSub}` }}
    >
      <IconBox icon={icon} size="sm" />
      <div className="flex-1 min-w-0 pt-0.5">
        <p className="text-[13px] font-semibold leading-tight truncate" style={{ color: T.text }}>
          {title}
        </p>
        <p className="text-[11px] truncate mt-0.5" style={{ color: T.textMuted }}>
          {sub}
        </p>
      </div>
      <time
        className="flex-shrink-0 tabular-nums font-medium pt-0.5"
        style={{ fontSize: 11, color: '#D1D5DB' }}
      >
        {time} ago
      </time>
    </div>
  )
}

// ─── Integration tile ─────────────────────────────────────────────────────────

function IntegrationTile({
  icon: Icon,
  name,
  stat,
  statLabel,
}: {
  icon: React.ElementType
  name: string
  category: string
  stat: string
  statLabel: string
}) {
  return (
    <div
      className="flex items-center gap-3 p-3.5 rounded-xl transition-colors duration-150"
      style={{ border: `1px solid ${T.border}` }}
      onMouseEnter={(e) => (e.currentTarget.style.background = T.bg)}
      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
    >
      <div className="relative flex-shrink-0">
        <IconBox icon={Icon} size="md" />
        <span
          className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-white"
          style={{ background: '#10B981' }}
        />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[12px] font-semibold leading-tight truncate" style={{ color: T.text }}>
          {name}
        </p>
        <p className="text-[10px] truncate mt-0.5" style={{ color: T.textMuted }}>
          <span style={{ fontWeight: 700, color: T.textSub }}>{stat}</span> {statLabel}
        </p>
      </div>
    </div>
  )
}

// ─── Score ring ───────────────────────────────────────────────────────────────

function ScoreRing({ score }: { score: number }) {
  const r = 40,
    circ = 2 * Math.PI * r
  const fill = (score / 100) * circ
  const hue = score >= 80 ? '#059669' : score >= 60 ? '#D97706' : '#DC2626'
  return (
    <div className="relative w-32 h-32">
      <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
        <circle cx="50" cy="50" r={r} fill="none" stroke={T.borderSub} strokeWidth="8" />
        <circle
          cx="50"
          cy="50"
          r={r}
          fill="none"
          stroke={T.accent}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${fill} ${circ}`}
          style={{ transition: 'stroke-dasharray 1s cubic-bezier(0.4,0,0.2,1)' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-bold leading-none" style={{ fontSize: 28, color: hue }}>
          {score}
        </span>
        <span
          className="uppercase tracking-widest font-semibold mt-1"
          style={{ fontSize: 9, color: T.textMuted }}
        >
          Score
        </span>
      </div>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const { user } = useAuth()
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'dashboard'],
    queryFn: async () => {
      const r = await apiClient.get('/analytics/dashboard')
      return r.data?.data
    },
    retry: false,
    staleTime: 60_000,
  })

  const stats: StatCardProps[] = [
    {
      label: 'Total Contacts',
      value: String(data?.total_contacts ?? 0),
      icon: Users,
      change: 12,
      spark: DEMO_SPARK,
    },
    {
      label: 'Active Deals',
      value: String(data?.total_deals ?? 0),
      icon: TrendingUp,
      change: 8,
      spark: DEMO_SPARK.map((v) => v * 0.8),
    },
    {
      label: 'Total Revenue',
      value: fmtCurrency(data?.total_revenue ?? 0),
      icon: IndianRupee,
      change: 23,
      spark: DEMO_SPARK.map((v) => v * 1.1),
    },
    {
      label: 'Win Rate',
      value: `${(data?.win_rate ?? 0).toFixed(1)}%`,
      icon: Target,
      change: -2,
      spark: DEMO_SPARK.map((v) => v * 0.6),
    },
  ]

  const chartData = data?.monthly_revenue ?? MONTHS.map((month) => ({ month, revenue: 0 }))
  const pipeline: Array<{ stage: string; count: number }> = data?.deals_by_stage ?? []

  return (
    <div className="flex flex-col gap-4 animate-fade-in">
      {/* ── Hero greeting + page nav ────────────────────────────── */}
      <Card>
        <div className="px-6 pt-5 pb-5">
          {/* Header row */}
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-5">
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5">
                <span
                  className="w-1.5 h-1.5 rounded-full animate-pulse"
                  style={{ background: '#10B981' }}
                />
                <span className="text-[11px] font-medium" style={{ color: T.textMuted }}>
                  All systems operational
                </span>
              </div>
              <h2
                className="font-bold leading-tight tracking-tight"
                style={{ fontSize: 19, color: T.text }}
              >
                {greeting}, {user?.name?.split(' ')[0] ?? 'there'} 👋
              </h2>
              <p style={{ fontSize: 13, color: T.textMuted }}>
                Your pipeline is healthy — heres what needs attention today.
              </p>
            </div>

            {/* Add Contact CTA */}
            <Link
              href="/contacts"
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold text-white flex-shrink-0 transition-opacity"
              style={{ background: 'linear-gradient(135deg, #7C3AED, #A78BFA)' }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.88')}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
            >
              <Plus style={{ width: 15, height: 15 }} />
              Add Contact
            </Link>
          </div>

          {/* ── Page navigation cards ── */}
          <div className="pt-4" style={{ borderTop: `1px solid ${T.borderSub}` }}>
            <p
              className="text-[10px] font-bold uppercase tracking-widest mb-3"
              style={{ color: T.textMuted }}
            >
              Navigate to
            </p>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
              {NAV_CARDS.map(({ label, icon: Icon, href, color, bg, desc }) => (
                <Link
                  key={href}
                  href={href}
                  className="group flex flex-col items-center gap-2 p-3 rounded-xl transition-all duration-150 text-center"
                  style={{ border: `1px solid ${T.border}`, background: 'transparent' }}
                  onMouseEnter={(e) => {
                    ;(e.currentTarget as HTMLElement).style.background = bg
                    ;(e.currentTarget as HTMLElement).style.borderColor = color + '40'
                    ;(e.currentTarget as HTMLElement).style.transform = 'translateY(-1px)'
                    ;(e.currentTarget as HTMLElement).style.boxShadow = `0 4px 12px ${color}20`
                  }}
                  onMouseLeave={(e) => {
                    ;(e.currentTarget as HTMLElement).style.background = 'transparent'
                    ;(e.currentTarget as HTMLElement).style.borderColor = T.border
                    ;(e.currentTarget as HTMLElement).style.transform = 'translateY(0)'
                    ;(e.currentTarget as HTMLElement).style.boxShadow = 'none'
                  }}
                >
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center transition-colors"
                    style={{ background: bg }}
                  >
                    <Icon style={{ width: 16, height: 16, color }} />
                  </div>
                  <div>
                    <p className="text-[12px] font-bold leading-tight" style={{ color: T.text }}>
                      {label}
                    </p>
                    <p className="text-[10px] mt-0.5 leading-tight" style={{ color: T.textMuted }}>
                      {desc}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* ── Stat cards ──────────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s) => (
          <StatCard key={s.label} {...s} />
        ))}
      </div>

      {/* ── Revenue chart + Pipeline ─────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHead
            title="Revenue Trend"
            sub="Monthly overview · current year"
            action={
              <span
                className="font-semibold rounded-lg"
                style={{
                  fontSize: 11,
                  padding: '4px 10px',
                  color: '#059669',
                  background: 'rgba(5,150,105,0.08)',
                }}
              >
                ↑ 23% YoY
              </span>
            }
          />
          <div className="px-5 pt-5 pb-5">
            {isLoading ? (
              <div className="h-48 flex items-center justify-center">
                <div
                  className="w-5 h-5 rounded-full border-2 animate-spin"
                  style={{ borderColor: '#E9EAEC', borderTopColor: T.accent }}
                />
              </div>
            ) : (
              <RechartsAreaChart data={chartData} height={185} />
            )}
          </div>
        </Card>

        <Card>
          <CardHead
            title="Pipeline Stages"
            sub="Deal distribution"
            action={
              <Link
                href="/deals"
                className="flex items-center gap-0.5 transition-opacity"
                style={{ fontSize: 11, fontWeight: 600, color: T.accent }}
                onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.7')}
                onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
              >
                View all <ChevronRight style={{ width: 13, height: 13 }} />
              </Link>
            }
          />
          <div className="px-5 pt-5 pb-5">
            {isLoading ? (
              <div className="space-y-5">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} className="h-10" />
                ))}
              </div>
            ) : pipeline.length === 0 ? (
              <div className="text-center py-12 space-y-2">
                <BarChart3 style={{ width: 36, height: 36, color: '#E5E7EB', margin: '0 auto' }} />
                <p style={{ fontSize: 13, color: T.textMuted }}>No deals yet</p>
                <Link href="/deals" style={{ fontSize: 11, fontWeight: 600, color: T.accent }}>
                  Create your first deal →
                </Link>
              </div>
            ) : (
              <div className="space-y-5">
                {pipeline.slice(0, 5).map((item) => {
                  const pct = data?.total_deals
                    ? Math.round((item.count / data.total_deals) * 100)
                    : 0
                  return (
                    <PipelineRow key={item.stage} stage={item.stage} count={item.count} pct={pct} />
                  )
                })}
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* ── Connected Apps ───────────────────────────────────────── */}
      <Card>
        <CardHead
          title="Connected Apps"
          sub="6 integrations active · CRM on autopilot"
          action={
            <Link
              href="/integrations"
              className="flex items-center gap-1 transition-opacity"
              style={{ fontSize: 11, fontWeight: 600, color: T.accent }}
              onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.7')}
              onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
            >
              Manage <ExternalLink style={{ width: 11, height: 11 }} />
            </Link>
          }
        />
        <div className="px-5 pt-5 pb-5 space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {INTEGRATIONS.map((p) => (
              <IntegrationTile key={p.name} {...p} />
            ))}
          </div>
          <div className="pt-4" style={{ borderTop: `1px solid ${T.borderSub}` }}>
            <p
              className="uppercase tracking-widest font-semibold mb-3"
              style={{ fontSize: 10, color: T.textMuted }}
            >
              Recent Automation Events
            </p>
            <div className="space-y-2.5">
              {AUTOMATION_EVENTS.map(({ icon: Icon, text, time }, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div
                    className="w-6 h-6 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ background: T.accentLight }}
                  >
                    <Icon style={{ width: 11, height: 11, color: T.accent }} />
                  </div>
                  <p className="flex-1 text-[12px]" style={{ color: T.textSub }}>
                    {text}
                  </p>
                  <time
                    className="flex-shrink-0 tabular-nums font-medium"
                    style={{ fontSize: 11, color: '#D1D5DB' }}
                  >
                    {time} ago
                  </time>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* ── Recent Activity + Performance ───────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHead
            title="Recent Activity"
            sub="Latest events across your CRM"
            action={
              <Link
                href="/activity"
                className="flex items-center gap-0.5 transition-opacity"
                style={{ fontSize: 11, fontWeight: 600, color: T.accent }}
                onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.7')}
                onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
              >
                See all <ChevronRight style={{ width: 13, height: 13 }} />
              </Link>
            }
          />
          <div className="px-5 pb-2">
            {ACTIVITY_FEED.map((item, i) => (
              <ActivityItem key={i} {...item} />
            ))}
            <div className="py-3">
              <Link
                href="/activity"
                className="flex items-center justify-center gap-1.5 py-2 rounded-xl text-[12px] font-semibold transition-colors"
                style={{ color: T.accent, background: T.accentLight }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(124,58,237,0.12)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = T.accentLight)}
              >
                View full activity log <ChevronRight style={{ width: 13, height: 13 }} />
              </Link>
            </div>
          </div>
        </Card>

        <Card>
          <CardHead title="Performance" sub="This week vs last week" />
          <div className="px-5 pt-6 pb-5 flex flex-col items-center gap-6">
            <ScoreRing score={78} />
            <div className="w-full">
              {PERF_METRICS.map(({ label, val, delta, up }) => (
                <div
                  key={label}
                  className="flex items-center justify-between py-2.5"
                  style={{ borderBottom: `1px solid ${T.borderSub}` }}
                >
                  <span style={{ fontSize: 12, color: T.textSub, fontWeight: 500 }}>{label}</span>
                  <div className="flex items-center gap-1.5">
                    <span
                      className="font-bold tabular-nums"
                      style={{ fontSize: 13, color: T.text }}
                    >
                      {val}
                    </span>
                    <span
                      className="rounded-md font-semibold tabular-nums"
                      style={{
                        fontSize: 10,
                        padding: '2px 5px',
                        color: up ? '#059669' : '#DC2626',
                        background: up ? 'rgba(5,150,105,0.08)' : 'rgba(220,38,38,0.08)',
                      }}
                    >
                      {delta}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <Link
              href="/reports"
              className="w-full flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-[12px] font-bold transition-colors"
              style={{
                background: T.accentLight,
                color: T.accent,
                border: `1px solid ${T.accentBorder}`,
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(124,58,237,0.12)')}
              onMouseLeave={(e) => (e.currentTarget.style.background = T.accentLight)}
            >
              <BarChart3 style={{ width: 13, height: 13 }} />
              Full Reports →
            </Link>
          </div>
        </Card>
      </div>

      {/* ── Tasks quick-jump ─────────────────────────────────────── */}
      <Link
        href="/tasks"
        className="flex items-center justify-between px-5 py-4 rounded-2xl transition-all"
        style={{
          background: T.surface,
          border: `1px solid ${T.border}`,
          boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
        }}
        onMouseEnter={(e) => {
          ;(e.currentTarget as HTMLElement).style.borderColor = 'rgba(124,58,237,0.3)'
          ;(e.currentTarget as HTMLElement).style.background = T.accentLight
        }}
        onMouseLeave={(e) => {
          ;(e.currentTarget as HTMLElement).style.borderColor = T.border
          ;(e.currentTarget as HTMLElement).style.background = T.surface
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: T.accentLight, border: `1px solid ${T.accentBorder}` }}
          >
            <CheckSquare style={{ width: 16, height: 16, color: T.accent }} />
          </div>
          <div>
            <p className="text-[13px] font-bold" style={{ color: T.text }}>
              Task Manager
            </p>
            <p className="text-[11px]" style={{ color: T.textMuted }}>
              View your to-dos, follow-ups, and overdue items
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="text-[11px] font-semibold px-2.5 py-1 rounded-full"
            style={{ background: 'rgba(239,68,68,0.08)', color: '#EF4444' }}
          >
            3 overdue
          </span>
          <ChevronRight style={{ width: 16, height: 16, color: T.textMuted }} />
        </div>
      </Link>
    </div>
  )
}
