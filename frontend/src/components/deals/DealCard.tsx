"use client";

import React from "react";
import { Deal } from "@/types";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical } from "lucide-react";
import Badge from "@/components/ui/Badge";
import { formatCurrency, formatDate } from "@/utils/format";
import { cn } from "@/utils/cn";

interface DealCardProps {
  deal: Deal;
  contactName?: string;
  isOverlay?: boolean;
}

const priorityColors: Record<string, string> = {
  low: "default",
  medium: "info",
  high: "warning",
  urgent: "danger",
};

export default function DealCard({
  deal,
  contactName,
  isOverlay,
}: DealCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: deal.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cn(
        "bg-white border border-gray-200 rounded-lg p-4 cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow",
        isOverlay && "shadow-lg z-50",
        isDragging && "opacity-50"
      )}
    >
      <div className="flex items-start gap-3">
        <div
          {...attributes}
          {...listeners}
          className="text-gray-400 hover:text-gray-600 mt-0.5 flex-shrink-0"
        >
          <GripVertical className="w-4 h-4" />
        </div>

        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-gray-900 text-sm truncate">
            {deal.title}
          </h4>

          {contactName && (
            <p className="text-xs text-gray-600 mt-1 truncate">
              {contactName}
            </p>
          )}

          <div className="flex items-center gap-2 mt-3 flex-wrap">
            {deal.value && (
              <span className="text-sm font-semibold text-indigo-600">
                {formatCurrency(deal.value)}
              </span>
            )}
            <Badge variant={priorityColors[deal.priority] as any}>
              {deal.priority}
            </Badge>
          </div>

          <p className="text-xs text-gray-500 mt-2">
            {formatDate(deal.created_at)}
          </p>
        </div>
      </div>
    </div>
  );
}
