"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const isAuthenticated = useAuthStore(s => s.isAuthenticated);

  useEffect(() => {
    if (!isAuthenticated) router.replace("/login");
  }, [isAuthenticated, router]);

  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen overflow-hidden bg-mesh" style={{ padding: "12px", gap: "12px" }}>
      {/* Floating sidebar */}
      <Sidebar />

      {/* Right column: floating header + content */}
      <div className="flex-1 flex flex-col min-w-0" style={{ gap: "12px" }}>
        <Header />
        <main
          className="flex-1 overflow-y-auto"
          style={{
            background: "var(--color-surface-alt, rgba(242,238,255,0.4))",
            borderRadius: "18px",
            border: "1px solid rgba(139,92,246,0.08)",
          }}
        >
          <div className="p-5 min-h-full">{children}</div>
        </main>
      </div>
    </div>
  );
}
