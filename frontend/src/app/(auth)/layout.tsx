"use client";

import React from "react";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen auth-bg flex items-center justify-center p-4 relative overflow-hidden">
      {/* Floating orbs */}
      <div className="absolute top-[-10%] left-[-5%] w-72 h-72 rounded-full opacity-20 animate-float"
        style={{ background: "radial-gradient(circle, #A78BFA 0%, transparent 70%)" }} />
      <div className="absolute bottom-[-5%] right-[-8%] w-96 h-96 rounded-full opacity-15 animate-float"
        style={{ background: "radial-gradient(circle, #7C3AED 0%, transparent 70%)", animationDelay: "3s" }} />
      <div className="absolute top-[40%] right-[10%] w-48 h-48 rounded-full opacity-10 animate-float"
        style={{ background: "radial-gradient(circle, #C4B5FD 0%, transparent 70%)", animationDelay: "1.5s" }} />

      {/* Grid pattern overlay */}
      <div className="absolute inset-0 opacity-[0.03]"
        style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")" }} />

      {/* Card */}
      <div className="relative w-full max-w-md animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: "linear-gradient(135deg, #7C3AED, #A78BFA)" }}>
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5}
                  d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="text-2xl font-bold text-white tracking-tight">Flowra</span>
          </div>
          <p className="text-sm mt-2" style={{ color: "rgba(196,181,253,0.7)" }}>
            AI-powered CRM for modern sales teams
          </p>
        </div>

        {/* Glass form card */}
        <div className="rounded-2xl p-8"
          style={{
            background: "rgba(255,255,255,0.07)",
            backdropFilter: "blur(24px) saturate(180%)",
            WebkitBackdropFilter: "blur(24px) saturate(180%)",
            border: "1px solid rgba(255,255,255,0.12)",
            boxShadow: "0 24px 64px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1)",
          }}>
          {children}
        </div>

        <p className="text-center mt-6 text-xs" style={{ color: "rgba(196,181,253,0.4)" }}>
          © 2025 Flowra · Privacy · Terms
        </p>
      </div>
    </div>
  );
}
