'use client'

/**
 * Isolated recharts area chart — loaded via next/dynamic to bypass
 * the Turbopack "module factory not available" error with recharts.
 * recharts internally cross-imports LineChart from AreaChart; Turbopack
 * can't resolve that at build time. Deferring to runtime fixes it entirely.
 */

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts'

// ─── Local constants (duplicated from page to keep this file standalone) ──────
const ACCENT = '#7C3AED'
const BORDER_SUB = '#F3F4F6'
const BORDER = '#E9EAEC'
const TEXT_MUTED = '#9CA3AF'

function fmtCurrency(n: number): string {
  if (n >= 10_000_000) return `₹${(n / 10_000_000).toFixed(1)}Cr`
  if (n >= 100_000) return `₹${(n / 100_000).toFixed(1)}L`
  if (n >= 1_000) return `₹${(n / 1_000).toFixed(1)}K`
  return `₹${n}`
}

// ─── Tooltip ──────────────────────────────────────────────────────────────────

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: { value: number }[]
  label?: string
}) {
  if (!active || !payload?.length) return null
  return (
    <div
      style={{
        background: '#111827',
        border: '1px solid rgba(255,255,255,0.07)',
        borderRadius: 10,
        padding: '6px 10px',
        boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
      }}
    >
      <p style={{ fontSize: 10, color: TEXT_MUTED, marginBottom: 1 }}>{label}</p>
      <p style={{ fontSize: 12, fontWeight: 700, color: '#fff' }}>
        {fmtCurrency(payload[0].value)}
      </p>
    </div>
  )
}

// ─── Chart ────────────────────────────────────────────────────────────────────

export interface AreaPoint {
  month: string
  revenue: number
}

export default function AreaChartComponent({
  data,
  height = 185,
}: {
  data: AreaPoint[]
  height?: number
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={ACCENT} stopOpacity={0.18} />
            <stop offset="100%" stopColor={ACCENT} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={BORDER_SUB} vertical={false} />
        <XAxis
          dataKey="month"
          tick={{ fontSize: 11, fill: TEXT_MUTED }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tickFormatter={fmtCurrency}
          tick={{ fontSize: 11, fill: TEXT_MUTED }}
          tickLine={false}
          axisLine={false}
          width={52}
        />
        <Tooltip
          content={<ChartTooltip />}
          cursor={{ stroke: BORDER, strokeWidth: 1, strokeDasharray: '4 2' }}
        />
        <Area
          type="monotone"
          dataKey="revenue"
          stroke={ACCENT}
          strokeWidth={2}
          fill="url(#areaGrad)"
          dot={false}
          activeDot={{ r: 5, fill: ACCENT, stroke: '#fff', strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
