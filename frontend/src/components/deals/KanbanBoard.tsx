"use client";

import React from "react";
import {
  DndContext,
  DragEndEvent,
  closestCorners,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { Deal, Stage } from "@/types";
import DealCard from "./DealCard";
import Spinner from "@/components/ui/Spinner";
import { dealService } from "@/services/dealService";
import { toast } from "sonner";
import { formatCurrency } from "@/utils/format";

interface KanbanBoardProps {
  stages: Stage[];
  deals: Deal[];
  contactMap?: Record<string, string>;
  isLoading?: boolean;
  onDragEnd: (deal: Deal, stageId: string) => Promise<void>;
}

export default function KanbanBoard({
  stages,
  deals,
  contactMap = {},
  isLoading,
  onDragEnd,
}: KanbanBoardProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, {
      distance: 8,
    })
  );

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over) return;

    const deal = deals.find((d) => d.id === active.id);
    if (!deal) return;

    const stageId = String(over.id);
    if (deal.stage_id === stageId) return;

    try {
      await onDragEnd(deal, stageId);
    } catch (error: any) {
      toast.error(error.message || "Failed to move deal");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Spinner />
      </div>
    );
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragEnd={handleDragEnd}
    >
      <div className="flex gap-6 overflow-x-auto pb-4">
        {stages.map((stage) => {
          const stageDealIds = deals
            .filter((d) => d.stage_id === stage.id)
            .map((d) => d.id);

          const stageDealValue = deals
            .filter((d) => d.stage_id === stage.id)
            .reduce((sum, d) => sum + (d.value || 0), 0);

          const stageDealCount = stageDealIds.length;

          return (
            <div
              key={stage.id}
              className="flex-shrink-0 w-96 bg-gray-50 rounded-lg p-4 border border-gray-200"
            >
              {/* Column Header */}
              <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className="w-3 h-3 rounded"
                    style={{
                      backgroundColor: stage.color || "#6366f1",
                    }}
                  />
                  <h3 className="font-semibold text-gray-900">{stage.name}</h3>
                  <span className="text-xs bg-gray-200 text-gray-700 rounded-full px-2 py-1">
                    {stageDealCount}
                  </span>
                </div>
                {stageDealValue > 0 && (
                  <p className="text-sm text-gray-600">
                    {formatCurrency(stageDealValue)}
                  </p>
                )}
              </div>

              {/* Deals List */}
              <SortableContext
                items={stageDealIds}
                strategy={verticalListSortingStrategy}
              >
                <div className="space-y-3">
                  {deals
                    .filter((d) => d.stage_id === stage.id)
                    .map((deal) => (
                      <DealCard
                        key={deal.id}
                        deal={deal}
                        contactName={deal.contact_id ? contactMap[deal.contact_id] : undefined}
                      />
                    ))}
                </div>
              </SortableContext>

              {stageDealCount === 0 && (
                <div className="text-center py-8 text-gray-400">
                  <p className="text-sm">No deals</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </DndContext>
  );
}
