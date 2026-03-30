'use client';

/**
 * Activity Charts — Recharts components for Activity page
 * Separated to avoid Turbopack module factory errors
 */

import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  PieChart, Pie,
} from 'recharts';

const T = {
  accent:      "#7C3AED",
  border:      "#E9EAEC",
  borderSub:   "#F3F4F6",
  text:        "#111827",
  textMuted:   "#6B7280",
  textFaint:   "#9CA3AF",
  surface:     "#ffffff",
} as const;

interface BreakdownItem {
  name: string;
  value: number;
  color: string;
}

export function BreakdownDonut({ data }: { data: BreakdownItem[] }) {
  return (
    <PieChart width={100} height={100}>
      <Pie
        data={data}
        dataKey="value"
        cx={50}
        cy={50}
        innerRadius={28}
        outerRadius={46}
        strokeWidth={2}
        stroke={T.surface}
      >
        {data.map((d, i) => (
          <Cell key={`cell-${i}`} fill={d.color} />
        ))}
      </Pie>
    </PieChart>
  );
}

interface DailyTrendItem {
  day: string;
  count: number;
}

export function DailyTrendBar({ data }: { data: DailyTrendItem[] }) {
  return (
    <ResponsiveContainer width="100%" height={90}>
      <BarChart
        data={data}
        barSize={10}
        margin={{ top: 0, right: 0, bottom: 0, left: -24 }}
      >
        <XAxis
          dataKey="day"
          tick={{ fontSize: 9, fill: T.textFaint }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis hide />
        <Tooltip
          contentStyle={{
            background: T.surface,
            border: `1px solid ${T.border}`,
            borderRadius: 8,
            fontSize: 11,
            color: T.text,
          }}
          cursor={{ fill: T.borderSub }}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {data.map((_, i) => (
            <Cell
              key={`cell-${i}`}
              fill={i === 3 ? T.accent : `${T.accent}50`}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
