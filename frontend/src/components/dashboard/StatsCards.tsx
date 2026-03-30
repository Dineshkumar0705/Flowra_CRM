"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Users, TrendingUp, DollarSign, Zap } from "lucide-react";
import apiClient from "@/services/apiClient";
import { Card, CardContent } from "@/components/ui/Card";
import Spinner from "@/components/ui/Spinner";
import { formatCurrency, formatPercentage } from "@/utils/format";

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  suffix?: string;
  trend?: number;
  loading?: boolean;
}

const StatCard: React.FC<StatCardProps> = ({
  icon,
  label,
  value,
  suffix,
  trend,
  loading,
}) => (
  <Card className="flex-1">
    <CardContent className="flex items-center justify-between p-6">
      <div>
        <p className="text-sm text-gray-600 mb-1">{label}</p>
        <div className="flex items-baseline gap-2">
          <p className="text-3xl font-bold text-gray-900">
            {loading ? "..." : value}
          </p>
          {suffix && <span className="text-lg text-gray-600">{suffix}</span>}
        </div>
        {trend !== undefined && (
          <p className={`text-sm mt-2 ${trend >= 0 ? "text-green-600" : "text-red-600"}`}>
            {trend >= 0 ? "+" : ""}{trend}% from last month
          </p>
        )}
      </div>
      <div className="text-indigo-600">{icon}</div>
    </CardContent>
  </Card>
);

export default function StatsCards() {
  const { data, isLoading } = useQuery({
    queryKey: ["analytics", "dashboard"],
    queryFn: async () => {
      const response = await apiClient.get("/analytics/dashboard");
      return response.data.data;
    },
  });

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <StatCard
        icon={<Users className="w-8 h-8" />}
        label="Total Contacts"
        value={data?.total_contacts || 0}
        loading={isLoading}
      />
      <StatCard
        icon={<TrendingUp className="w-8 h-8" />}
        label="Active Deals"
        value={data?.total_deals || 0}
        loading={isLoading}
      />
      <StatCard
        icon={<DollarSign className="w-8 h-8" />}
        label="Total Revenue"
        value={data ? formatCurrency(data.total_revenue) : "₹0"}
        loading={isLoading}
      />
      <StatCard
        icon={<Zap className="w-8 h-8" />}
        label="Win Rate"
        value={data ? formatPercentage(data.win_rate) : "0%"}
        loading={isLoading}
      />
    </div>
  );
}
