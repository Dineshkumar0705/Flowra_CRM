"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { Eye, EyeOff, Mail, Lock, User, Building2, ArrowRight } from "lucide-react";

export default function SignupPage() {
  const [form, setForm] = useState({ name: "", email: "", password: "", workspace_name: "" });
  const [showPwd, setShowPwd] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const { signup, isLoading } = useAuth();

  const update = (k: keyof typeof form, v: string) =>
    setForm(f => ({ ...f, [k]: v }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (!form.name.trim()) errs.name = "Name is required";
    if (!form.email.trim()) errs.email = "Email is required";
    if (!form.password || form.password.length < 8) errs.password = "Min 8 characters";
    if (!form.workspace_name.trim()) errs.workspace_name = "Workspace name is required";
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    await signup(form.name, form.email, form.password, form.workspace_name);
  };

  const inputBase =
    "w-full pl-10 pr-4 py-3 rounded-xl text-sm text-white placeholder-white/30 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-violet-400/40";
  const inputStyle = {
    background: "rgba(255,255,255,0.08)",
    border: "1px solid rgba(255,255,255,0.12)",
  };
  const iconStyle = { color: "rgba(196,181,253,0.5)" };
  const labelStyle = { color: "#C4B5FD" };

  return (
    <div>
      <div className="mb-7">
        <h1 className="text-2xl font-bold text-white mb-1">Create your account</h1>
        <p className="text-sm" style={{ color: "rgba(196,181,253,0.65)" }}>
          Start your 14-day free trial · No credit card required
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Full name */}
        <div>
          <label className="block text-xs font-medium mb-1.5" style={labelStyle}>
            Full name
          </label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={iconStyle} />
            <input
              type="text"
              placeholder="John Doe"
              value={form.name}
              onChange={e => update("name", e.target.value)}
              className={inputBase}
              style={inputStyle}
              autoComplete="name"
            />
          </div>
          {errors.name && <p className="text-xs mt-1 text-red-400">{errors.name}</p>}
        </div>

        {/* Work email */}
        <div>
          <label className="block text-xs font-medium mb-1.5" style={labelStyle}>
            Work email
          </label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={iconStyle} />
            <input
              type="email"
              placeholder="you@company.com"
              value={form.email}
              onChange={e => update("email", e.target.value)}
              className={inputBase}
              style={inputStyle}
              autoComplete="email"
            />
          </div>
          {errors.email && <p className="text-xs mt-1 text-red-400">{errors.email}</p>}
        </div>

        {/* Workspace name */}
        <div>
          <label className="block text-xs font-medium mb-1.5" style={labelStyle}>
            Workspace name
          </label>
          <div className="relative">
            <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={iconStyle} />
            <input
              type="text"
              placeholder="My Agency"
              value={form.workspace_name}
              onChange={e => update("workspace_name", e.target.value)}
              className={inputBase}
              style={inputStyle}
              autoComplete="organization"
            />
          </div>
          {errors.workspace_name && (
            <p className="text-xs mt-1 text-red-400">{errors.workspace_name}</p>
          )}
        </div>

        {/* Password */}
        <div>
          <label className="block text-xs font-medium mb-1.5" style={labelStyle}>
            Password
          </label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={iconStyle} />
            <input
              type={showPwd ? "text" : "password"}
              placeholder="Min 8 characters"
              value={form.password}
              onChange={e => update("password", e.target.value)}
              className={`${inputBase} pr-10`}
              style={inputStyle}
              autoComplete="new-password"
            />
            <button
              type="button"
              onClick={() => setShowPwd(p => !p)}
              className="absolute right-3 top-1/2 -translate-y-1/2"
              style={iconStyle}
            >
              {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          {errors.password && <p className="text-xs mt-1 text-red-400">{errors.password}</p>}
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isLoading}
          className="btn-primary w-full py-3 rounded-xl text-sm font-semibold text-white flex items-center justify-center gap-2 mt-2 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Creating account...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              Get started free <ArrowRight className="w-4 h-4" />
            </span>
          )}
        </button>
      </form>

      <p className="text-center mt-5 text-xs" style={{ color: "rgba(196,181,253,0.5)" }}>
        Already have an account?{" "}
        <Link href="/login" className="text-violet-300 hover:text-white font-medium transition-colors">
          Sign in
        </Link>
      </p>

      <p className="text-center mt-3 text-xs" style={{ color: "rgba(196,181,253,0.35)" }}>
        By signing up you agree to our Terms & Privacy Policy
      </p>
    </div>
  );
}
