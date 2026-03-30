"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { useQuery } from "@tanstack/react-query";
import apiClient from "@/services/apiClient";
import { Card, CardHeader, CardContent } from "@/components/ui/Card";
import Spinner from "@/components/ui/Spinner";
import { formatCurrency } from "@/utils/format";

export default function RevenueChart() {
  const { data, isLoading } = useQuery({
    queryKey: ["deals", "dashboard"],
    queryFn: async () => {
      const response = await apiClient.get("/deals/dashboard");
      return response.data.data;
    },
  });

  if (isLoading) {
    return (
      <Card className="lg:col-span-2">
        <CardHeader>
          <h3 className="text-lg font-semibold">Revenue Trend</h3>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64">
          <Spinner />
        </CardContent>
      </Card>
    );
  }

  const chartData = data?.monthly_revenue || [];

  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <h3 className="text-lg font-semibold">Revenue Trend</h3>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="month" stroke="#6b7280" />
            <YAxis stroke="#6b7280" />
            <Tooltip
              contentStyle={{
                backgroundColor: "#fff",
                border: "1px solid #e5e7eb",
                borderRadius: "8px",
              }}
              formatter={(value: any) => formatCurrency(value)}
            />
            <Line
              type="monotone"
              dataKey="revenue"
              stroke="#6366f1"
              strokeWidth={2}
              dot={{ fill: "#6366f1", r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
