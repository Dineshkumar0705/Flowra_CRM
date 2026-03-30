'use client';

/**
 * Activity Page — Flowra CRM
 * Premium activity feed with heatmap, KPI cards, timeline, and analytics breakdown.
 * Next.js 14 with dynamic recharts imports to avoid Turbopack errors.
 */

import React, { useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import {
  Users, TrendingUp, CheckCircle2, Star, Flame,
  MessageSquare, Mail, Bot, Bell, Zap, Search,
  Calendar, ArrowUpRight, Activity, ChevronDown,
  ChevronRight, Download, RefreshCw, Filter,
  TrendingDown, CheckSquare, Phone, Globe,
  UserPlus, Award, AlertCircle, Clock, Eye,
  BarChart2, Layers,
} from 'lucide-react';
import apiClient from '@/services/apiClient';

// Dynamically import recharts components
const DynamicBreakdownDonut = dynamic(
  () => import('./_activity-charts').then(mod => ({ default: mod.BreakdownDonut })),
  { ssr: false, loading: () => <div style={{ height: 100, width: 100 }} /> }
);

const DynamicDailyTrendBar = dynamic(
  () => import('./_activity-charts').then(mod => ({ default: mod.DailyTrendBar })),
  { ssr: false, loading: () => <div style={{ height: 90 }} /> }
);

// ─── Design tokens ────────────────────────────────────────────────────────────

const T = {
  accent:      '#7C3AED',
  accentLight: 'rgba(124,58,237,0.07)',
  accentBg:    'rgba(124,58,237,0.12)',
  border:      '#E9EAEC',
  borderSub:   '#F3F4F6',
  text:        '#111827',
  textSub:     '#374151',
  textMuted:   '#6B7280',
  textFaint:   '#9CA3AF',
  surface:     '#ffffff',
  bg:          '#F9FAFB',
  green:       '#10B981',
  greenLight:  'rgba(16,185,129,0.07)',
  blue:        '#3B82F6',
  blueLight:   'rgba(59,130,246,0.07)',
  amber:       '#F59E0B',
  amberLight:  'rgba(245,158,11,0.07)',
  red:         '#EF4444',
  redLight:    'rgba(239,68,68,0.07)',
  pink:        '#EC4899',
  teal:        '#14B8A6',
  tealLight:   'rgba(20,184,166,0.07)',
  indigo:      '#6366F1',
  indigoLight: 'rgba(99,102,241,0.07)',
} as const;

// ─── Activity types ────────────────────────────────────────────────────────────

type ActivityType =
  | 'contact_created' | 'contact_imported' | 'contact_scored' | 'hot_lead'
  | 'deal_created'    | 'deal_moved'       | 'deal_won'       | 'deal_lost'
  | 'task_created'    | 'task_completed'
  | 'whatsapp_sent'   | 'email_sent'       | 'call_logged'
  | 'automation'      | 'notification'     | 'integration'    | 'other';

const TYPE_CONFIG: Record<ActivityType, {
  icon:  React.ElementType;
  color: string;
  bg:    string;
  label: string;
  group: string;
}> = {
  contact_created:  { icon: UserPlus,      color: T.accent,  bg: T.accentLight,     label: 'Contact Added',   group: 'contacts' },
  contact_imported: { icon: Users,         color: T.blue,    bg: T.blueLight,       label: 'Import',          group: 'contacts' },
  contact_scored:   { icon: Star,          color: T.amber,   bg: T.amberLight,      label: 'AI Score',        group: 'contacts' },
  hot_lead:         { icon: Flame,         color: T.red,     bg: T.redLight,        label: 'Hot Lead',        group: 'contacts' },
  deal_created:     { icon: TrendingUp,    color: T.blue,    bg: T.blueLight,       label: 'Deal Created',    group: 'deals'    },
  deal_moved:       { icon: ArrowUpRight,  color: T.indigo,  bg: T.indigoLight,     label: 'Stage Move',      group: 'deals'    },
  deal_won:         { icon: Award,         color: T.green,   bg: T.greenLight,      label: 'Deal Won',        group: 'deals'    },
  deal_lost:        { icon: TrendingDown,  color: T.red,     bg: T.redLight,        label: 'Deal Lost',       group: 'deals'    },
  task_created:     { icon: CheckSquare,   color: T.teal,    bg: T.tealLight,       label: 'Task Added',      group: 'tasks'    },
  task_completed:   { icon: CheckCircle2,  color: T.green,   bg: T.greenLight,      label: 'Task Done',       group: 'tasks'    },
  whatsapp_sent:    { icon: MessageSquare, color: '#25D366', bg: 'rgba(37,211,102,0.07)', label: 'WhatsApp', group: 'messages' },
  email_sent:       { icon: Mail,          color: T.red,     bg: T.redLight,        label: 'Email',           group: 'messages' },
  call_logged:      { icon: Phone,         color: T.blue,    bg: T.blueLight,       label: 'Call',            group: 'messages' },
  automation:       { icon: Bot,           color: T.accent,  bg: T.accentLight,     label: 'Automation',      group: 'system'   },
  notification:     { icon: Bell,          color: T.amber,   bg: T.amberLight,      label: 'Alert',           group: 'system'   },
  integration:      { icon: Globe,         color: T.teal,    bg: T.tealLight,       label: 'Integration',     group: 'system'   },
  other:            { icon: Activity,      color: T.textFaint, bg: 'rgba(156,163,175,0.07)', label: 'Activity', group: 'other' },
};

// ─── Demo data ────────────────────────────────────────────────────────────────

interface ActivityEvent {
  id:     string;
  type:   ActivityType;
  title:  string;
  sub:    string;
  time:   string;
  date:   string;
  user?:  string;
  meta?:  string;
}

const DEMO_ACTIVITY: ActivityEvent[] = [
  { id:'1',  type:'contact_created',  title:'New contact added',            sub:'Arjun Sharma — Tata Consultancy Services',   time:'2m ago',    date:'Today',     user:'You',     meta:'Lead score: 72' },
  { id:'2',  type:'deal_moved',       title:'Deal moved to Proposal',       sub:'₹4.5L deal — Infosys Ltd',                   time:'18m ago',   date:'Today',     user:'You',     meta:'From: Qualified' },
  { id:'3',  type:'deal_won',         title:'Deal closed — Won 🎉',         sub:'₹12L deal — Reliance Jio',                   time:'1h ago',    date:'Today',     user:'Priya',   meta:'Pipeline: Enterprise' },
  { id:'4',  type:'contact_scored',   title:'Contact rescored by AI',       sub:'Priya Nair · score 87 → 94',                 time:'2h ago',    date:'Today',     user:'AI',      meta:'+7 points' },
  { id:'5',  type:'hot_lead',         title:'Hot lead detected',            sub:'Vikram Singh — HDFC Bank',                   time:'3h ago',    date:'Today',     user:'AI',      meta:'Score: 91' },
  { id:'6',  type:'whatsapp_sent',    title:'WhatsApp sequence triggered',  sub:'Follow-up sent to 12 contacts',              time:'4h ago',    date:'Today',     user:'Bot',     meta:'Open rate: 89%' },
  { id:'7',  type:'automation',       title:'Autopilot revived 3 deals',    sub:'Stale deal re-engagement triggered',         time:'5h ago',    date:'Today',     user:'System',  meta:'3 deals activated' },
  { id:'8',  type:'task_completed',   title:'Task marked complete',         sub:'Follow up with Rajan Mehta — done',          time:'5h ago',    date:'Today',     user:'You',     meta:'2 days early' },
  { id:'9',  type:'email_sent',       title:'Gmail sequence triggered',     sub:'Email sent to Priya Nair',                   time:'6h ago',    date:'Today',     user:'Bot',     meta:'Sequence: Onboarding' },
  { id:'10', type:'task_created',     title:'Task created',                 sub:'Prepare demo deck for Wipro',                time:'7h ago',    date:'Today',     user:'You',     meta:'Due: Tomorrow' },
  { id:'11', type:'deal_created',     title:'New deal added',               sub:'₹8L — Wipro Technologies',                   time:'Yesterday', date:'Yesterday', user:'Rahul',   meta:'Stage: Discovery' },
  { id:'12', type:'contact_imported', title:'Contacts imported from CSV',   sub:'42 contacts added via bulk import',          time:'Yesterday', date:'Yesterday', user:'You',     meta:'Source: Manual' },
  { id:'13', type:'deal_lost',        title:'Deal closed — Lost',           sub:'₹3.2L deal — Bajaj Finance',                 time:'Yesterday', date:'Yesterday', user:'Rahul',   meta:'Reason: Budget' },
  { id:'14', type:'call_logged',      title:'Call logged',                  sub:'12 min call with Suresh Kumar',              time:'Yesterday', date:'Yesterday', user:'You',     meta:'Duration: 12:04' },
  { id:'15', type:'integration',      title:'Gmail sync completed',         sub:'4,730 emails synced from inbox',             time:'2 days ago', date:'Earlier',   user:'System',  meta:'Inbox: main' },
  { id:'16', type:'automation',       title:'Lead nurture sequence started', sub:'Sent to 28 contacts in "Cold Leads" tag',    time:'2 days ago', date:'Earlier',   user:'System',  meta:'28 contacts' },
  { id:'17', type:'contact_created',  title:'New contact via web form',     sub:'Deepika Sharma — Mahindra & Mahindra',       time:'2 days ago', date:'Earlier',   user:'Web Form',meta:'Source: web_form' },
  { id:'18', type:'notification',     title:'System alert',                 sub:'New WhatsApp template approved by Meta',     time:'3 days ago', date:'Earlier',   user:'System',  meta:'Template: Promo_Q1' },
  { id:'19', type:'deal_won',         title:'Deal closed — Won 🎉',         sub:'₹6.5L deal — HCL Technologies',              time:'3 days ago', date:'Earlier',   user:'Priya',   meta:'Pipeline: SMB' },
  { id:'20', type:'contact_scored',   title:'Batch AI scoring complete',    sub:'127 contacts re-scored overnight',           time:'4 days ago', date:'Earlier',   user:'AI',      meta:'Avg score: 68' },
];

// ─── Heatmap data (7 weeks × 7 days) ─────────────────────────────────────────

function buildHeatmap() {
  const today = new Date();
  const cells: { date: string; count: number; level: 0|1|2|3|4; fullDate: Date }[] = [];
  for (let d = 48; d >= 0; d--) {
    const dt = new Date(today);
    dt.setDate(today.getDate() - d);
    const count = d < 7 ? Math.floor(Math.random() * 12 + 2)
                : d < 14 ? Math.floor(Math.random() * 8 + 1)
                : Math.floor(Math.random() * 6);
    const level = count === 0 ? 0 : count < 3 ? 1 : count < 6 ? 2 : count < 10 ? 3 : 4;
    cells.push({
      date: dt.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }),
      count,
      level,
      fullDate: dt,
    });
  }
  return cells;
}

const HEATMAP = buildHeatmap();

const HEATMAP_COLORS = [
  '#F3F4F6',
  'rgba(124,58,237,0.2)',
  'rgba(124,58,237,0.5)',
  'rgba(124,58,237,0.75)',
  '#7C3AED',
];

// ─── Breakdown chart data ─────────────────────────────────────────────────────

const BREAKDOWN_DATA = [
  { name: 'Contacts',   value: 8,  color: T.accent  },
  { name: 'Deals',      value: 5,  color: T.blue    },
  { name: 'Messages',   value: 4,  color: '#25D366' },
  { name: 'Tasks',      value: 3,  color: T.teal    },
  { name: 'Automation', value: 3,  color: T.indigo  },
  { name: 'System',     value: 2,  color: T.amber   },
];

const DAILY_TREND = [
  { day: 'Mon', count: 4  },
  { day: 'Tue', count: 9  },
  { day: 'Wed', count: 6  },
  { day: 'Thu', count: 14 },
  { day: 'Fri', count: 11 },
  { day: 'Sat', count: 3  },
  { day: 'Sun', count: 7  },
];

const TOP_USERS = [
  { name: 'You',    events: 12, initials: 'DK', color: T.accent  },
  { name: 'Priya',  events: 8,  initials: 'PR', color: T.blue    },
  { name: 'Rahul',  events: 5,  initials: 'RV', color: T.green   },
  { name: 'AI Bot', events: 9,  initials: 'AI', color: T.amber   },
  { name: 'System', events: 4,  initials: 'SY', color: T.textFaint },
];

// ─── Filter config ─────────────────────────────────────────────────────────────

const FILTER_TABS = [
  { key: 'all',      label: 'All Events' },
  { key: 'contacts', label: 'Contacts'   },
  { key: 'deals',    label: 'Deals'      },
  { key: 'tasks',    label: 'Tasks'      },
  { key: 'messages', label: 'Messages'   },
  { key: 'system',   label: 'System'     },
];

const DATE_RANGES = [
  { key: 'today',  label: 'Today'   },
  { key: '7d',     label: '7 days'  },
  { key: '30d',    label: '30 days' },
  { key: 'all',    label: 'All time' },
];

// ─── Component: Card ──────────────────────────────────────────────────────────

function Card({
  children,
  className = '',
  style = {},
}: {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <div
      className={`rounded-2xl ${className}`}
      style={{
        background:  T.surface,
        border:      `1px solid ${T.border}`,
        boxShadow:   '0 1px 3px rgba(0,0,0,0.04)',
        ...style,
      }}
    >
      {children}
    </div>
  );
}

// ─── Component: Trend Badge ───────────────────────────────────────────────────

function TrendBadge({ value, suffix = '%' }: { value: number; suffix?: string }) {
  const up = value >= 0;
  return (
    <span
      className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-md text-[10px] font-bold"
      style={{
        background: up ? 'rgba(16,185,129,0.10)' : 'rgba(239,68,68,0.10)',
        color:      up ? T.green                  : T.red,
      }}
    >
      {up ? '↑' : '↓'} {Math.abs(value)}{suffix}
    </span>
  );
}

// ─── Component: KPI Card ──────────────────────────────────────────────────────

interface KpiProps {
  icon:    React.ElementType;
  label:   string;
  value:   string | number;
  trend:   number;
  color:   string;
  sub?:    string;
}

function KpiCard({ icon: Icon, label, value, trend, color, sub }: KpiProps) {
  return (
    <Card>
      <div className="p-4 flex flex-col gap-3">
        <div className="flex items-start justify-between">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center transition-transform"
            style={{
              background: `${color}12`,
              border: `1px solid ${color}25`,
            }}
          >
            <Icon style={{ width: 18, height: 18, color }} />
          </div>
          <TrendBadge value={trend} />
        </div>
        <div>
          <p className="text-[24px] font-bold leading-none" style={{ color: T.text }}>
            {value}
          </p>
          <p className="text-[11px] font-medium mt-1.5" style={{ color: T.textMuted }}>
            {label}
          </p>
          {sub && <p className="text-[10px] mt-0.5" style={{ color: T.textFaint }}>{sub}</p>}
        </div>
      </div>
    </Card>
  );
}

// ─── Component: Activity Heatmap ──────────────────────────────────────────────

function ActivityHeatmap() {
  const [hovered, setHovered] = useState<{ date: string; count: number } | null>(null);

  // Arrange heatmap into 7 columns (weeks)
  const weeks: typeof HEATMAP[] = [];
  for (let i = 0; i < HEATMAP.length; i += 7) {
    weeks.push(HEATMAP.slice(i, i + 7));
  }

  const dayLabels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <div>
          <p className="text-[12px] font-bold uppercase tracking-widest" style={{ color: T.text }}>
            Activity Heatmap
          </p>
          <p className="text-[11px] mt-0.5" style={{ color: T.textMuted }}>
            Last 49 days · darker = more activity
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px]" style={{ color: T.textFaint }}>Less</span>
          {HEATMAP_COLORS.map((c, i) => (
            <div
              key={i}
              className="w-3 h-3 rounded-sm cursor-pointer transition-transform hover:scale-110"
              style={{
                background: c,
                border: `1px solid ${T.border}`,
              }}
              title={i === 0 ? 'No activity' : i === 4 ? 'Very high activity' : 'Medium activity'}
            />
          ))}
          <span className="text-[10px]" style={{ color: T.textFaint }}>More</span>
        </div>
      </div>

      <div className="flex gap-0.5">
        {/* Day labels */}
        <div className="flex flex-col gap-0.5 pr-2 pt-5">
          {dayLabels.map((day, idx) => (
            <div
              key={day}
              className="w-8 h-5 flex items-center justify-center text-[9px] font-medium"
              style={{ color: T.textFaint }}
            >
              {day}
            </div>
          ))}
        </div>

        {/* Heatmap weeks */}
        <div className="flex gap-1">
          {weeks.map((week, weekIdx) => (
            <div key={weekIdx} className="flex flex-col gap-0.5">
              {/* Week date label */}
              <div className="h-5 flex items-center justify-center text-[8px]" style={{ color: T.textFaint }}>
                {week[0] && week[0].date.split(' ')[0]}
              </div>
              {/* Week cells */}
              {week.map((cell, dayIdx) => (
                <div
                  key={`${weekIdx}-${dayIdx}`}
                  className="w-5 h-5 rounded-sm cursor-pointer transition-all hover:scale-110"
                  style={{
                    background: HEATMAP_COLORS[cell.level],
                    border: `1px solid ${cell.level > 0 ? 'rgba(124,58,237,0.15)' : T.borderSub}`,
                  }}
                  onMouseEnter={() => setHovered(cell)}
                  onMouseLeave={() => setHovered(null)}
                  title={`${cell.date}: ${cell.count} events`}
                />
              ))}
            </div>
          ))}
        </div>
      </div>

      {hovered && (
        <div className="mt-3 p-2.5 rounded-lg" style={{ background: T.borderSub }}>
          <p className="text-[11px]" style={{ color: T.text }}>
            <span className="font-semibold">{hovered.count} events</span>
            <span style={{ color: T.textMuted }}> on {hovered.date}</span>
          </p>
        </div>
      )}
    </div>
  );
}

// ─── Component: Activity Row ──────────────────────────────────────────────────

function ActivityRow({
  event,
  isLast,
}: {
  event:   ActivityEvent;
  isLast:  boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const cfg = TYPE_CONFIG[event.type] ?? TYPE_CONFIG.other;
  const Icon = cfg.icon;

  return (
    <div
      className="relative transition-all"
      style={{
        borderBottom: isLast ? 'none' : `1px solid ${T.borderSub}`,
      }}
    >
      {/* Vertical timeline connector */}
      {!isLast && (
        <div
          className="absolute z-0"
          style={{
            left:       '28px',
            top:        '52px',
            width:      '2px',
            bottom:     '-1px',
            background: `linear-gradient(to bottom, ${T.border}, transparent)`,
          }}
        />
      )}

      {/* Row */}
      <div
        className="flex items-start gap-3 px-4 py-3.5 cursor-pointer group relative z-10 transition-all"
        style={{
          background: expanded ? T.accentBg : 'transparent',
          borderRadius: '0',
        }}
        onClick={() => setExpanded(e => !e)}
      >
        {/* Icon bubble */}
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all"
          style={{
            background: cfg.bg,
            border:     `1px solid ${cfg.color}25`,
            marginTop:  '2px',
            transform: 'scale(1)',
          }}
        >
          <Icon style={{ width: 16, height: 16, color: cfg.color }} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <p className="text-[13px] font-semibold" style={{ color: T.text }}>
              {event.title}
            </p>
            <span
              className="inline-flex items-center px-2 py-0.5 rounded-lg text-[9px] font-bold uppercase tracking-wider"
              style={{ background: cfg.bg, color: cfg.color }}
            >
              {cfg.label}
            </span>
          </div>
          <p className="text-[12px] truncate" style={{ color: T.textMuted }}>
            {event.sub}
          </p>

          {expanded && (
            <div className="mt-3 p-3 rounded-lg text-[11px]" style={{ background: 'rgba(0,0,0,0.02)' }}>
              <div className="grid grid-cols-2 gap-x-6 gap-y-2">
                {event.user && (
                  <>
                    <span style={{ color: T.textFaint }}>Triggered by</span>
                    <span style={{ color: T.text, fontWeight: 600 }}>{event.user}</span>
                  </>
                )}
                {event.meta && (
                  <>
                    <span style={{ color: T.textFaint }}>Details</span>
                    <span style={{ color: T.text, fontWeight: 600 }}>{event.meta}</span>
                  </>
                )}
                <span style={{ color: T.textFaint }}>Time</span>
                <span style={{ color: T.text, fontWeight: 600 }}>{event.time}</span>
              </div>
            </div>
          )}
        </div>

        {/* Right side: time + user avatar */}
        <div className="flex flex-col items-end gap-2 flex-shrink-0">
          <time className="text-[10px] font-medium" style={{ color: T.textFaint }}>
            {event.time}
          </time>
          {event.user && (
            <div
              className="w-6 h-6 rounded-lg flex items-center justify-center text-[8px] font-bold transition-all"
              style={{
                background: ['AI', 'System', 'Bot'].includes(event.user) ? T.borderSub : T.accentBg,
                color:      ['AI', 'System', 'Bot'].includes(event.user) ? T.textFaint  : T.accent,
                border:     `1px solid ${T.border}`,
              }}
            >
              {event.user.slice(0, 2).toUpperCase()}
            </div>
          )}
        </div>

        {/* Expand chevron */}
        <div
          className="flex-shrink-0 transition-transform mt-0.5"
          style={{ transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)' }}
        >
          <ChevronRight style={{ width: 14, height: 14, color: T.textFaint }} />
        </div>
      </div>
    </div>
  );
}

// ─── Component: Date Group Header ─────────────────────────────────────────────

function DateGroupLabel({ label, count }: { label: string; count: number }) {
  return (
    <div className="flex items-center gap-3 px-1 mb-2 mt-4">
      <p
        className="text-[10px] font-bold uppercase tracking-widest whitespace-nowrap"
        style={{ color: T.textMuted, letterSpacing: '0.08em' }}
      >
        {label}
      </p>
      <div className="flex-1 h-px" style={{ background: T.borderSub }} />
      <span
        className="text-[10px] font-semibold px-2 py-0.5 rounded-lg"
        style={{ background: T.borderSub, color: T.textMuted }}
      >
        {count}
      </span>
    </div>
  );
}

// ─── Component: Breakdown Sidebar ─────────────────────────────────────────────

function BreakdownSidebar({ allItems }: { allItems: ActivityEvent[] }) {
  const breakdown = useMemo(() => {
    const counts: Record<string, number> = {};
    allItems.forEach(item => {
      const group = TYPE_CONFIG[item.type]?.group ?? 'other';
      counts[group] = (counts[group] ?? 0) + 1;
    });
    return BREAKDOWN_DATA.map(d => ({
      ...d,
      value: counts[d.name.toLowerCase()] ?? d.value,
    }));
  }, [allItems]);

  const total = breakdown.reduce((s, d) => s + d.value, 0);

  return (
    <div className="flex flex-col gap-4">

      {/* Event Breakdown */}
      <Card>
        <div className="p-4">
          <p className="text-[12px] font-bold mb-4" style={{ color: T.text }}>
            Event Breakdown
          </p>
          <div className="flex items-center gap-4">
            <DynamicBreakdownDonut data={breakdown} />
            <div className="flex flex-col gap-2.5 flex-1 min-w-0">
              {breakdown.map(d => (
                <div key={d.name} className="flex items-center gap-2">
                  <div
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ background: d.color }}
                  />
                  <span className="text-[11px] flex-1 truncate" style={{ color: T.textMuted }}>
                    {d.name}
                  </span>
                  <span className="text-[11px] font-bold" style={{ color: T.text }}>
                    {d.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Daily Trend */}
      <Card>
        <div className="p-4">
          <p className="text-[12px] font-bold mb-4" style={{ color: T.text }}>
            This Week
          </p>
          <DynamicDailyTrendBar data={DAILY_TREND} />
        </div>
      </Card>

      {/* Top Contributors */}
      <Card>
        <div className="p-4">
          <p className="text-[12px] font-bold mb-3" style={{ color: T.text }}>
            Top Contributors
          </p>
          <div className="flex flex-col gap-3">
            {TOP_USERS.map((u) => {
              const pct = Math.round((u.events / 12) * 100);
              return (
                <div key={u.name}>
                  <div className="flex items-center gap-2 mb-1.5">
                    <div
                      className="w-6 h-6 rounded-lg flex items-center justify-center text-[9px] font-bold flex-shrink-0"
                      style={{
                        background: `${u.color}15`,
                        color: u.color,
                        border: `1px solid ${u.color}20`,
                      }}
                    >
                      {u.initials}
                    </div>
                    <span className="text-[11px] font-semibold flex-1" style={{ color: T.text }}>
                      {u.name}
                    </span>
                    <span className="text-[10px]" style={{ color: T.textMuted }}>
                      {u.events}
                    </span>
                  </div>
                  <div
                    className="h-1.5 rounded-full overflow-hidden"
                    style={{ background: T.borderSub }}
                  >
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${pct}%`,
                        background: u.color,
                        transitionDuration: '0.6s',
                        transitionTimingFunction: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </Card>

      {/* Quick Navigation */}
      <Card>
        <div className="p-4">
          <p className="text-[12px] font-bold mb-3" style={{ color: T.text }}>
            Quick Links
          </p>
          <div className="flex flex-col gap-1.5">
            {[
              { href: '/contacts', label: 'Contacts',     icon: Users, color: T.accent  },
              { href: '/deals',    label: 'Deals',        icon: TrendingUp, color: T.blue    },
              { href: '/tasks',    label: 'Tasks',        icon: CheckSquare, color: T.teal    },
              { href: '/reports',  label: 'Reports',      icon: BarChart2, color: T.pink    },
            ].map(item => {
              const IconComp = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl transition-all"
                  style={{
                    background: T.borderSub,
                  }}
                >
                  <IconComp
                    style={{
                      width: 14,
                      height: 14,
                      color: item.color,
                      flexShrink: 0,
                    }}
                  />
                  <span className="text-[12px] font-medium flex-1" style={{ color: T.textSub }}>
                    {item.label}
                  </span>
                  <ChevronRight style={{ width: 12, height: 12, color: T.textFaint }} />
                </Link>
              );
            })}
          </div>
        </div>
      </Card>

    </div>
  );
}

// ─── Main Page Component ──────────────────────────────────────────────────────

export default function ActivityPage() {
  const [groupFilter, setGroupFilter]   = useState('all');
  const [dateRange,   setDateRange]     = useState('7d');
  const [search,      setSearch]        = useState('');
  const [page,        setPage]          = useState(1);
  const PAGE_SIZE = 10;

  // ── API fetch ──────────────────────────────────────────────────────────────
  const { data: notifData, isLoading, refetch, isFetching } = useQuery({
    queryKey:  ['notifications', 'list'],
    queryFn:   async () => {
      const r = await apiClient.get('/notifications?page=1&limit=100');
      return r.data;
    },
    staleTime: 30_000,
    retry:     false,
  });

  const realItems: ActivityEvent[] = useMemo(() => {
    return (notifData?.data ?? []).map((n: any) => ({
      id:    n.id,
      type:  'notification' as ActivityType,
      title: n.title,
      sub:   n.body,
      time:  new Date(n.created_at).toLocaleString('en-IN', {
        day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
      }),
      date:  'Recent',
      user:  'System',
    }));
  }, [notifData]);

  const allItems = realItems.length > 0 ? realItems : DEMO_ACTIVITY;

  // ── Filtering ──────────────────────────────────────────────────────────────
  const filtered = useMemo(() => {
    return allItems.filter(item => {
      const cfg        = TYPE_CONFIG[item.type] ?? TYPE_CONFIG.other;
      const matchGroup = groupFilter === 'all' || cfg.group === groupFilter;
      const matchDate  = dateRange === 'all'
        ? true
        : dateRange === 'today'
          ? item.date === 'Today'
          : dateRange === '7d'
            ? item.date !== 'Earlier'
            : true;
      const matchSearch = !search ||
        item.title.toLowerCase().includes(search.toLowerCase()) ||
        item.sub.toLowerCase().includes(search.toLowerCase());
      return matchGroup && matchDate && matchSearch;
    });
  }, [allItems, groupFilter, dateRange, search]);

  // ── Grouping ───────────────────────────────────────────────────────────────
  const DATE_ORDER = ['Today', 'Yesterday', 'Earlier', 'Recent'];
  const grouped = useMemo(() => {
    const g: Record<string, ActivityEvent[]> = {};
    filtered.forEach(item => {
      const key = item.date ?? 'Recent';
      if (!g[key]) g[key] = [];
      g[key].push(item);
    });
    return g;
  }, [filtered]);

  const groupKeys = Object.keys(grouped).sort((a, b) => {
    const ai = DATE_ORDER.indexOf(a), bi = DATE_ORDER.indexOf(b);
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
  });

  // ── Pagination ─────────────────────────────────────────────────────────────
  const paginatedKeys = useMemo(() => {
    let shown = 0;
    const result: string[] = [];
    for (const k of groupKeys) {
      if (shown >= page * PAGE_SIZE) break;
      result.push(k);
      shown += grouped[k].length;
    }
    return result;
  }, [groupKeys, grouped, page]);

  const totalShown = paginatedKeys.reduce((s, k) => s + grouped[k].length, 0);
  const hasMore    = totalShown < filtered.length;

  // ── Export CSV ─────────────────────────────────────────────────────────────
  const exportCsv = useCallback(() => {
    const rows = ['Type,Title,Details,Time,User'];
    filtered.forEach(e => {
      rows.push([e.type, e.title, e.sub, e.time, e.user ?? ''].map(v => `"${v}"`).join(','));
    });
    const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = 'flowra-activity.csv'; a.click();
    URL.revokeObjectURL(url);
  }, [filtered]);

  // ── KPI data ───────────────────────────────────────────────────────────────
  const kpis = useMemo(() => ([
    {
      icon:  Activity,
      label: 'Total Events',
      value: allItems.length,
      trend: +18,
      color: T.accent,
      sub:   'All time activity',
    },
    {
      icon:  UserPlus,
      label: 'New Contacts',
      value: allItems.filter(a => a.type === 'contact_created' || a.type === 'contact_imported').length,
      trend: +12,
      color: T.blue,
      sub:   'Added or imported',
    },
    {
      icon:  Award,
      label: 'Deals Won',
      value: allItems.filter(a => a.type === 'deal_won').length,
      trend: +33,
      color: T.green,
      sub:   'Closed successfully',
    },
    {
      icon:  Bot,
      label: 'Automations',
      value: allItems.filter(a => a.type === 'automation').length,
      trend: +5,
      color: T.indigo,
      sub:   'Triggered sequences',
    },
    {
      icon:  MessageSquare,
      label: 'Messages Sent',
      value: allItems.filter(a => a.type === 'whatsapp_sent' || a.type === 'email_sent' || a.type === 'call_logged').length,
      trend: +22,
      color: '#25D366',
      sub:   'WhatsApp + Email + Calls',
    },
    {
      icon:  CheckCircle2,
      label: 'Tasks Done',
      value: allItems.filter(a => a.type === 'task_completed').length,
      trend: +8,
      color: T.teal,
      sub:   'Completed this period',
    },
  ]), [allItems]);

  return (
    <div className="flex flex-col gap-6" style={{ color: T.text }}>

      {/* ─── Page Header ──────────────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-[20px] font-bold leading-tight" style={{ color: T.text }}>
            Activity Feed
          </h1>
          <p className="text-[12px] mt-1.5" style={{ color: T.textMuted }}>
            Complete audit trail of all events across Flowra
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => refetch()}
            className="flex items-center gap-1.5 px-3 py-2.5 rounded-xl text-[12px] font-semibold transition-all"
            style={{
              background: T.surface,
              border:     `1px solid ${T.border}`,
              color:      T.textMuted,
              opacity:    isFetching ? 0.6 : 1,
            }}
          >
            <RefreshCw style={{ width: 14, height: 14 }} />
            Refresh
          </button>
          <button
            onClick={exportCsv}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-[12px] font-semibold transition-all"
            style={{
              background: T.accent,
              color:      '#fff',
              border:     'none',
            }}
          >
            <Download style={{ width: 14, height: 14 }} />
            Export CSV
          </button>
        </div>
      </div>

      {/* ─── KPI Cards Grid ───────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
        {kpis.map((k, i) => (
          <KpiCard key={i} {...k} />
        ))}
      </div>

      {/* ─── Activity Heatmap ─────────────────────────────────────────────────────── */}
      <Card className="p-6">
        <ActivityHeatmap />
      </Card>

      {/* ─── Filters & Search ─────────────────────────────────────────────────────── */}
      <div className="flex flex-col gap-3">
        {/* Search + date range */}
        <div className="flex items-center gap-2 flex-wrap">
          <div
            className="flex items-center gap-2 flex-1 min-w-[220px] px-3 py-2.5 rounded-xl"
            style={{ border: `1px solid ${T.border}`, background: T.surface }}
          >
            <Search style={{ width: 14, height: 14, color: T.textMuted, flexShrink: 0 }} />
            <input
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }}
              placeholder="Search events…"
              className="flex-1 text-[13px] outline-none bg-transparent"
              style={{ color: T.text }}
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="text-[14px]"
                style={{ color: T.textFaint }}
              >
                ✕
              </button>
            )}
          </div>

          <div className="flex items-center gap-1 p-1 rounded-lg" style={{ background: T.borderSub }}>
            {DATE_RANGES.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => { setDateRange(key); setPage(1); }}
                className="px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all whitespace-nowrap"
                style={{
                  background: dateRange === key ? T.surface    : 'transparent',
                  color:      dateRange === key ? T.text       : T.textMuted,
                  boxShadow:  dateRange === key ? '0 1px 2px rgba(0,0,0,0.05)' : 'none',
                }}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Event type filter tabs */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1">
          {FILTER_TABS.map(({ key, label }) => {
            const count = key === 'all'
              ? allItems.length
              : allItems.filter(a => (TYPE_CONFIG[a.type]?.group ?? 'other') === key).length;
            const active = groupFilter === key;
            return (
              <button
                key={key}
                onClick={() => { setGroupFilter(key); setPage(1); }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold whitespace-nowrap transition-all"
                style={{
                  background: active ? T.accent         : T.surface,
                  color:      active ? '#fff'           : T.textMuted,
                  border:     `1px solid ${active ? T.accent : T.border}`,
                }}
              >
                {label}
                <span
                  className="px-1.5 py-0.5 rounded-md text-[9px] font-bold"
                  style={{
                    background: active ? 'rgba(255,255,255,0.25)' : T.borderSub,
                    color:      active ? '#fff'                   : T.textMuted,
                  }}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ─── Timeline + Sidebar Layout ────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_280px] gap-6 items-start">

        {/* ─── Timeline ─────────────────────────────────────────────────────────────── */}
        <div className="flex flex-col gap-4">
          {isLoading ? (
            <Card className="p-12 text-center">
              <div className="flex flex-col items-center gap-3">
                <div
                  className="w-8 h-8 rounded-full border-2 border-t-transparent"
                  style={{
                    borderColor: `${T.accent} transparent ${T.accent} ${T.accent}`,
                    animation: 'spin 1s linear infinite',
                  }}
                />
                <p className="text-[13px]" style={{ color: T.textMuted }}>
                  Loading activity…
                </p>
              </div>
            </Card>
          ) : paginatedKeys.length === 0 ? (
            <Card className="p-12 text-center">
              <Activity style={{ width: 40, height: 40, color: T.borderSub, margin: '0 auto 12px' }} />
              <p className="text-[14px] font-semibold mb-1" style={{ color: T.textMuted }}>
                No events found
              </p>
              <p className="text-[12px]" style={{ color: T.textFaint }}>
                Try adjusting your filters or date range
              </p>
              <button
                onClick={() => {
                  setGroupFilter('all');
                  setDateRange('7d');
                  setSearch('');
                  setPage(1);
                }}
                className="mt-4 px-4 py-2 rounded-lg text-[12px] font-semibold transition-all"
                style={{
                  background: T.accentBg,
                  color: T.accent,
                  border: `1px solid ${T.accent}30`,
                }}
              >
                Reset Filters
              </button>
            </Card>
          ) : (
            <>
              {paginatedKeys.map(dateKey => {
                const items = grouped[dateKey];
                return (
                  <div key={dateKey}>
                    <DateGroupLabel label={dateKey} count={items.length} />
                    <Card>
                      {items.map((item, i) => (
                        <ActivityRow
                          key={item.id}
                          event={item}
                          isLast={i === items.length - 1}
                        />
                      ))}
                    </Card>
                  </div>
                );
              })}

              {/* Load more button */}
              {hasMore && (
                <button
                  onClick={() => setPage(p => p + 1)}
                  className="w-full py-3 rounded-xl text-[13px] font-semibold transition-all"
                  style={{
                    background: T.surface,
                    border:     `1px solid ${T.border}`,
                    color:      T.textMuted,
                  }}
                >
                  Load more · {filtered.length - totalShown} remaining
                </button>
              )}

              {/* Footer stats */}
              <p className="text-center text-[11px]" style={{ color: T.textFaint, paddingTop: '8px' }}>
                Showing {Math.min(totalShown, filtered.length)} of {filtered.length} events
              </p>
            </>
          )}
        </div>

        {/* ─── Right Sidebar ────────────────────────────────────────────────────────── */}
        <BreakdownSidebar allItems={allItems} />

      </div>

      {/* ─── Bottom CTA Strip ────────────────────────────────────────────────────── */}
      <Card
        style={{
          background:    `linear-gradient(135deg, ${T.accent}08, ${T.indigo}08)`,
          border:        `1px solid ${T.accent}18`,
          marginTop:     '8px',
        }}
      >
        <div className="flex items-center justify-between px-5 py-4 flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: T.accentLight, border: `1px solid ${T.accent}20` }}
            >
              <BarChart2 style={{ width: 18, height: 18, color: T.accent }} />
            </div>
            <div>
              <p className="text-[13px] font-bold" style={{ color: T.text }}>
                Want deeper insights?
              </p>
              <p className="text-[11px]" style={{ color: T.textMuted }}>
                Explore revenue, pipeline, and performance analytics
              </p>
            </div>
          </div>
          <Link
            href="/reports"
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg text-[12px] font-bold transition-all flex-shrink-0"
            style={{ background: T.accent, color: '#fff', border: 'none' }}
          >
            Open Reports
            <ArrowUpRight style={{ width: 14, height: 14 }} />
          </Link>
        </div>
      </Card>

      {/* Spin animation for loading */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

    </div>
  );
}
