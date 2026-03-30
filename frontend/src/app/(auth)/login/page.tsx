"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { Eye, EyeOff, Mail, Lock, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const { login, isLoading } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs: typeof errors = {};
    if (!email) errs.email = "Email is required";
    if (!password) errs.password = "Password is required";
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    await login(email, password);
  };

  const inputClass = `w-full pl-10 pr-4 py-3 rounded-xl text-sm text-white placeholder-white/30 transition-all duration-200 focus:outline-none`;
  const inputStyle = {
    background: "rgba(255,255,255,0.08)",
    border: "1px solid rgba(255,255,255,0.12)",
  };
  const inputFocusStyle = "focus:ring-2 focus:ring-violet-400/40 focus:border-violet-400/50";

  return (
    <div>
      <div className="mb-7">
        <h1 className="text-2xl font-bold text-white mb-1">Welcome back</h1>
        <p className="text-sm" style={{ color: "rgba(196,181,253,0.65)" }}>
          Sign in to continue to your workspace
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Email */}
        <div>
          <label className="block text-xs font-medium mb-1.5" style={{ color: "#C4B5FD" }}>
            Email address
          </label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: "rgba(196,181,253,0.5)" }} />
            <input
              type="email"
              placeholder="you@company.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className={`${inputClass} ${inputFocusStyle}`}
              style={inputStyle}
            />
          </div>
          {errors.email && <p className="text-xs mt-1 text-red-400">{errors.email}</p>}
        </div>

        {/* Password */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-medium" style={{ color: "#C4B5FD" }}>Password</label>
            <Link href="/forgot-password" className="text-xs hover:text-violet-300 transition-colors"
              style={{ color: "rgba(196,181,253,0.6)" }}>
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: "rgba(196,181,253,0.5)" }} />
            <input
              type={showPwd ? "text" : "password"}
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className={`${inputClass} pr-10 ${inputFocusStyle}`}
              style={inputStyle}
            />
            <button type="button" onClick={() => setShowPwd(!showPwd)}
              className="absolute right-3 top-1/2 -translate-y-1/2 transition-colors"
              style={{ color: "rgba(196,181,253,0.5)" }}>
              {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          {errors.password && <p className="text-xs mt-1 text-red-400">{errors.password}</p>}
        </div>

        {/* Submit */}
        <button type="submit" disabled={isLoading}
          className="btn-primary w-full py-3 rounded-xl text-sm font-semibold text-white flex items-center justify-center gap-2 mt-2 disabled:opacity-60 disabled:cursor-not-allowed">
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Signing in...
            </span>
          ) : (
            <span className="flex items-center gap-2">Sign in <ArrowRight className="w-4 h-4" /></span>
          )}
        </button>
      </form>

      {/* Divider */}
      <div className="my-6 flex items-center gap-3">
        <div className="flex-1 h-px" style={{ background: "rgba(255,255,255,0.1)" }} />
        <span className="text-xs" style={{ color: "rgba(196,181,253,0.45)" }}>New to Flowra?</span>
        <div className="flex-1 h-px" style={{ background: "rgba(255,255,255,0.1)" }} />
      </div>

      <Link href="/signup">
        <button className="w-full py-3 rounded-xl text-sm font-medium transition-all duration-200"
          style={{
            background: "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.12)",
            color: "#C4B5FD",
          }}
          onMouseEnter={e => { (e.target as HTMLButtonElement).style.background = "rgba(255,255,255,0.1)"; }}
          onMouseLeave={e => { (e.target as HTMLButtonElement).style.background = "rgba(255,255,255,0.06)"; }}>
          Create a free account
        </button>
      </Link>
    </div>
  );
}
