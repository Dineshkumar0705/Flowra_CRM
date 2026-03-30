"use client";

import React, { useState, useEffect } from "react";
import { Contact } from "@/types";
import { X, Users } from "lucide-react";
import { contactService } from "@/services/contactService";
import { toast } from "sonner";

interface ContactDrawerProps {
  open: boolean;
  onClose: () => void;
  contact?: Contact;
  onSave: () => void;
}

const SOURCE_META: Record<string, { label: string; color: string; bg: string }> = {
  manual:   { label: "Manual",   color: "#7C3AED", bg: "rgba(124,58,237,0.10)"  },
  import:   { label: "Import",   color: "#6B7280", bg: "rgba(107,114,128,0.10)" },
  whatsapp: { label: "WhatsApp", color: "#10B981", bg: "rgba(16,185,129,0.10)"  },
  gmail:    { label: "Gmail",    color: "#3B82F6", bg: "rgba(59,130,246,0.10)"  },
  web_form: { label: "Web Form", color: "#F59E0B", bg: "rgba(245,158,11,0.10)"  },
  referral: { label: "Referral", color: "#EC4899", bg: "rgba(236,72,153,0.10)"  },
};

function TagChip({ label }: { label: string }) {
  return (
    <span className="text-[10px] px-2 py-0.5 rounded-full font-medium"
      style={{ background: "rgba(124,58,237,0.09)", color: "var(--color-primary)" }}>
      {label}
    </span>
  );
}

export default function ContactDrawer({
  open, onClose, contact, onSave,
}: ContactDrawerProps) {
  const [form, setForm] = useState({
    first_name:   "",
    last_name:    "",
    email:        "",
    phone:        "",
    company_name: "",
    job_title:    "",
    source:       "manual",
    tags:         "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors]       = useState<Record<string, string>>({});

  useEffect(() => {
    if (contact) {
      setForm({
        first_name:   contact.first_name,
        last_name:    contact.last_name    ?? "",
        email:        contact.email        ?? "",
        phone:        contact.phone        ?? "",
        company_name: contact.company_name ?? "",
        job_title:    contact.job_title    ?? "",
        source:       contact.source,
        tags:         contact.tags.join(", "),
      });
    } else {
      setForm({
        first_name: "", last_name: "", email: "", phone: "",
        company_name: "", job_title: "", source: "manual", tags: "",
      });
    }
    setErrors({});
  }, [contact, open]);

  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!form.first_name.trim()) errs.first_name = "Required";
    if (form.email && !form.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/))
      errs.email = "Invalid email";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setIsLoading(true);
    try {
      const data = {
        first_name:   form.first_name.trim(),
        last_name:    form.last_name.trim()    || undefined,
        email:        form.email               || undefined,
        phone:        form.phone               || undefined,
        company_name: form.company_name        || undefined,
        job_title:    form.job_title           || undefined,
        source:       form.source,
        tags:         form.tags.split(",").map(t => t.trim()).filter(Boolean),
      };
      if (contact) {
        await contactService.updateContact(contact.id, data);
        toast.success("Contact updated");
      } else {
        await contactService.createContact(data);
        toast.success("Contact created");
      }
      onSave();
      onClose();
    } catch (err: any) {
      toast.error(err.response?.data?.message || "Failed to save contact");
    } finally {
      setIsLoading(false);
    }
  };

  const inputBase = "w-full px-3.5 py-2.5 rounded-xl text-sm transition-all focus:outline-none focus:ring-2 focus:ring-violet-400/40";
  const inputStyle: React.CSSProperties = {
    background: "rgba(242,238,255,0.85)",
    border: "1px solid rgba(139,92,246,0.18)",
    color: "var(--color-text)",
  };

  const SectionLabel = ({ children }: { children: string }) => (
    <p className="text-[10px] font-bold uppercase tracking-widest mb-3"
      style={{ color: "var(--color-text-secondary)" }}>
      {children}
    </p>
  );

  const Field = ({
    label, fieldKey, placeholder, type = "text", required = false,
  }: {
    label: string; fieldKey: string; placeholder?: string;
    type?: string; required?: boolean;
  }) => (
    <div>
      <label className="block text-xs font-semibold mb-1.5"
        style={{ color: "var(--color-text-secondary)" }}>
        {label}{required && <span className="text-red-400 ml-0.5">*</span>}
      </label>
      <input
        type={type}
        placeholder={placeholder}
        value={(form as any)[fieldKey]}
        onChange={e => set(fieldKey, e.target.value)}
        required={required}
        className={inputBase}
        style={{
          ...inputStyle,
          borderColor: errors[fieldKey] ? "#EF4444" : "rgba(139,92,246,0.18)",
        }}
      />
      {errors[fieldKey] && (
        <p className="text-xs mt-1 text-red-500">{errors[fieldKey]}</p>
      )}
    </div>
  );

  if (!open) return null;

  return (
    <>
      {/* backdrop */}
      <div className="fixed inset-0 bg-black/25 backdrop-blur-sm z-30" onClick={onClose} />

      {/* panel */}
      <div
        className="fixed right-0 top-0 h-screen w-[440px] flex flex-col z-40"
        style={{
          background: "#f9f6ff",
          backdropFilter: "blur(24px)",
          borderLeft: "1px solid rgba(139,92,246,0.14)",
          boxShadow: "-24px 0 64px rgba(26,15,58,0.18)",
        }}
      >
        {/* header */}
        <div className="flex items-center justify-between px-6 py-5"
          style={{ borderBottom: "1px solid rgba(139,92,246,0.10)" }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(124,58,237,0.12)" }}>
              <Users className="w-4 h-4" style={{ color: "#7C3AED" }} />
            </div>
            <div>
              <h2 className="font-bold text-base leading-none" style={{ color: "var(--color-text)" }}>
                {contact ? "Edit Contact" : "New Contact"}
              </h2>
              <p className="text-xs mt-0.5" style={{ color: "var(--color-text-secondary)" }}>
                {contact ? "Update contact details" : "Add to your CRM"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-xl flex items-center justify-center transition-all"
            style={{ background: "rgba(139,92,246,0.08)" }}
            onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "rgba(239,68,68,0.10)"}
            onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "rgba(139,92,246,0.08)"}
          >
            <X className="w-4 h-4" style={{ color: "var(--color-text-secondary)" }} />
          </button>
        </div>

        {/* form */}
        <form id="drawer-contact-form" onSubmit={handleSubmit}
          className="flex-1 overflow-y-auto px-6 py-5 space-y-5">

          <div>
            <SectionLabel>Basic Info</SectionLabel>
            <div className="grid grid-cols-2 gap-3">
              <Field label="First Name" fieldKey="first_name" placeholder="Arjun" required />
              <Field label="Last Name"  fieldKey="last_name"  placeholder="Sharma" />
            </div>
          </div>

          <div>
            <SectionLabel>Contact Info</SectionLabel>
            <div className="space-y-3">
              <Field label="Email" fieldKey="email" placeholder="arjun@company.com" type="email" />
              <Field label="Phone" fieldKey="phone" placeholder="+91 98765 43210" />
            </div>
          </div>

          <div>
            <SectionLabel>Work Details</SectionLabel>
            <div className="space-y-3">
              <Field label="Company"   fieldKey="company_name" placeholder="Tata Consultancy" />
              <Field label="Job Title" fieldKey="job_title"    placeholder="Product Manager" />
            </div>
          </div>

          <div>
            <SectionLabel>CRM Details</SectionLabel>
            <div className="space-y-4">
              {/* Source pills */}
              <div>
                <label className="block text-xs font-semibold mb-2"
                  style={{ color: "var(--color-text-secondary)" }}>
                  Source
                </label>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(SOURCE_META).map(([k, v]) => (
                    <button
                      key={k}
                      type="button"
                      onClick={() => set("source", k)}
                      className="text-[11px] px-2.5 py-1 rounded-full font-semibold transition-all"
                      style={{
                        background: form.source === k ? v.color : v.bg,
                        color:      form.source === k ? "#fff"   : v.color,
                        border:     `1px solid ${form.source === k ? v.color : "transparent"}`,
                      }}
                    >
                      {v.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tags */}
              <div>
                <label className="block text-xs font-semibold mb-1.5"
                  style={{ color: "var(--color-text-secondary)" }}>
                  Tags <span className="font-normal opacity-60">(comma separated)</span>
                </label>
                <input
                  type="text"
                  placeholder="vip, hot-lead, enterprise"
                  value={form.tags}
                  onChange={e => set("tags", e.target.value)}
                  className={inputBase}
                  style={inputStyle}
                />
                {form.tags && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {form.tags.split(",").map(t => t.trim()).filter(Boolean).map(t => (
                      <TagChip key={t} label={t} />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </form>

        {/* footer */}
        <div className="px-6 py-4 flex gap-3"
          style={{ borderTop: "1px solid rgba(139,92,246,0.10)" }}>
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium transition-all"
            style={{ border: "1px solid rgba(139,92,246,0.20)", color: "var(--color-text-secondary)" }}
            onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "rgba(139,92,246,0.05)"}
            onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "transparent"}
          >
            Cancel
          </button>
          <button
            type="submit"
            form="drawer-contact-form"
            disabled={isLoading}
            className="flex-1 py-2.5 rounded-xl text-sm font-bold text-white transition-all disabled:opacity-60"
            style={{ background: "linear-gradient(135deg, #7C3AED, #A78BFA)" }}
          >
            {isLoading ? "Saving…" : contact ? "Save Changes" : "Add Contact"}
          </button>
        </div>
      </div>
    </>
  );
}
