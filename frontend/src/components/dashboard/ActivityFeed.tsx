"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import apiClient from "@/services/apiClient";
import { Card, CardHeader, CardContent } from "@/components/ui/Card";
import Spinner from "@/components/ui/Spinner";
import { formatTimeAgo } from "@/utils/format";

export default function ActivityFeed() {
  const { data, isLoading } = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => {
      const response = await apiClient.get("/notifications", {
        params: { page: 1, page_size: 5 },
      });
      return response.data.data;
    },
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold">Recent Activity</h3>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-48">
          <Spinner />
        </CardContent>
      </Card>
    );
  }

  const notifications = data || [];

  return (
    <Card>
      <CardHeader>
        <h3 className="text-lg font-semibold">Recent Activity</h3>
      </CardHeader>
      <CardContent className="space-y-4">
        {notifications.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No recent activity</p>
        ) : (
          notifications.map((notification: any) => (
            <div
              key={notification.id}
              className="flex items-start gap-4 pb-4 border-b border-gray-100 last:border-0 last:pb-0"
            >
              <div className="w-2 h-2 rounded-full bg-indigo-600 mt-2 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">
                  {notification.title}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  {notification.body}
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  {formatTimeAgo(notification.created_at)}
                </p>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
