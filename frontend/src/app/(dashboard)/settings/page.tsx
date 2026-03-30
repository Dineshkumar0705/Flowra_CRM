"use client";

import React, { useState } from "react";
import { useAuth } from "@/hooks/useAuth";
import { User, Lock, Building2, Bell, Save } from "lucide-react";
import { toast } from "sonner";

const tabs = [
  { id:"profile",   label:"Profile",   icon:User     },
  { id:"security",  label:"Security",  icon:Lock     },
  { id:"workspace", label:"Workspace", icon:Building2},
  { id:"notifs",    label:"Notifications", icon:Bell },
];

export default function SettingsPage() {
  const { user, workspace, changePassword } = useAuth();
  const [activeTab, setActiveTab] = useState("profile");
  const [pwd, setPwd] = useState({ current:"", next:"", confirm:"" });
  const [saving, setSaving] = useState(false);

  const inputClass = "w-full px-3.5 py-2.5 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-400/40";
  const inputStyle = { background:"rgba(242,238,255,0.8)", border:"1px solid rgba(139,92,246,0.2)", color:"var(--color-text)" };

  const handleChangePwd = async (e: React.FormEvent) => {
    e.preventDefault();
    if(pwd.next !== pwd.confirm) { toast.error("Passwords don't match"); return; }
    if(pwd.next.length < 8) { toast.error("Min 8 characters"); return; }
    setSaving(true);
    await changePassword(pwd.current, pwd.next);
    setPwd({current:"",next:"",confirm:""});
    setSaving(false);
  };

  return (
    <div className="max-w-3xl animate-fade-in">
      {/* Tab bar */}
      <div className="glass rounded-2xl p-1.5 flex gap-1 mb-6">
        {tabs.map(t=>{
          const Icon = t.icon;
          const active = activeTab===t.id;
          return (
            <button key={t.id} onClick={()=>setActiveTab(t.id)}
              className="flex-1 flex items-center justify-center gap-2 py-2 rounded-xl text-sm font-medium transition-all duration-150"
              style={{
                background: active ? "var(--color-primary)" : "transparent",
                color: active ? "#fff" : "var(--color-text-secondary)",
                boxShadow: active ? "0 4px 14px rgba(124,58,237,0.3)" : "none",
              }}>
              <Icon className="w-4 h-4"/>{t.label}
            </button>
          );
        })}
      </div>

      {/* Profile tab */}
      {activeTab==="profile" && (
        <div className="glass rounded-2xl p-6 space-y-5">
          <div className="flex items-center gap-4 pb-4" style={{borderBottom:"1px solid rgba(139,92,246,0.1)"}}>
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-bold text-white"
              style={{background:"linear-gradient(135deg, #7C3AED, #A78BFA)"}}>
              {user?.name?.charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="font-bold text-base" style={{color:"var(--color-text)"}}>{user?.name}</p>
              <p className="text-sm" style={{color:"var(--color-text-secondary)"}}>{user?.email}</p>
              <span className="text-xs px-2.5 py-0.5 rounded-full mt-1 inline-block font-medium"
                style={{background:"rgba(124,58,237,0.12)",color:"var(--color-primary)"}}>
                {user?.role?.replace("_"," ")}
              </span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {[
              {label:"Full Name",value:user?.name,readOnly:false},
              {label:"Email Address",value:user?.email,readOnly:true},
            ].map(({label,value,readOnly})=>(
              <div key={label}>
                <label className="text-xs font-semibold mb-1.5 block" style={{color:"var(--color-text-secondary)"}}>{label}</label>
                <input defaultValue={value||""} readOnly={readOnly}
                  className={inputClass} style={{...inputStyle, opacity:readOnly?0.6:1}}/>
              </div>
            ))}
          </div>
          <div className="flex justify-end">
            <button className="btn-primary flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white">
              <Save className="w-4 h-4"/> Save Changes
            </button>
          </div>
        </div>
      )}

      {/* Security tab */}
      {activeTab==="security" && (
        <div className="glass rounded-2xl p-6">
          <h3 className="font-bold text-base mb-1" style={{color:"var(--color-text)"}}>Change Password</h3>
          <p className="text-xs mb-5" style={{color:"var(--color-text-secondary)"}}>Keep your account secure with a strong password</p>
          <form onSubmit={handleChangePwd} className="space-y-4">
            {[
              {k:"current",label:"Current Password",ph:"Enter current password"},
              {k:"next",   label:"New Password",    ph:"Min 8 characters"},
              {k:"confirm",label:"Confirm New Password",ph:"Re-enter new password"},
            ].map(({k,label,ph})=>(
              <div key={k}>
                <label className="text-xs font-semibold mb-1.5 block" style={{color:"var(--color-text-secondary)"}}>{label}</label>
                <input type="password" placeholder={ph} value={(pwd as any)[k]}
                  onChange={e=>setPwd(p=>({...p,[k]:e.target.value}))}
                  required className={inputClass} style={inputStyle}/>
              </div>
            ))}
            <div className="flex justify-end pt-2">
              <button type="submit" disabled={saving}
                className="btn-primary flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white disabled:opacity-60">
                <Lock className="w-4 h-4"/>{saving?"Updating...":"Update Password"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Workspace tab */}
      {activeTab==="workspace" && (
        <div className="glass rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-3 pb-4" style={{borderBottom:"1px solid rgba(139,92,246,0.1)"}}>
            <div className="w-12 h-12 rounded-xl flex items-center justify-center text-lg font-bold text-white"
              style={{background:"linear-gradient(135deg, #7C3AED, #A78BFA)"}}>
              {workspace?.name?.charAt(0).toUpperCase()||"W"}
            </div>
            <div>
              <p className="font-bold" style={{color:"var(--color-text)"}}>{workspace?.name}</p>
              <span className="text-xs px-2.5 py-0.5 rounded-full font-medium"
                style={{background:"rgba(16,185,129,0.1)",color:"#10B981"}}>
                {workspace?.plan?.toUpperCase() || "FREE"} Plan
              </span>
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold mb-1.5 block" style={{color:"var(--color-text-secondary)"}}>Workspace Name</label>
            <input defaultValue={workspace?.name||""} className={inputClass} style={inputStyle}/>
          </div>
          <div className="p-4 rounded-xl" style={{background:"rgba(124,58,237,0.06)",border:"1px solid rgba(124,58,237,0.15)"}}>
            <p className="text-xs font-semibold mb-1" style={{color:"var(--color-primary)"}}>Workspace ID</p>
            <p className="text-xs font-mono" style={{color:"var(--color-text-secondary)"}}>{workspace?.id||"—"}</p>
          </div>
          <div className="flex justify-end">
            <button className="btn-primary flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white">
              <Save className="w-4 h-4"/> Save Changes
            </button>
          </div>
        </div>
      )}

      {/* Notifications tab */}
      {activeTab==="notifs" && (
        <div className="glass rounded-2xl p-6 space-y-4">
          <h3 className="font-bold text-base mb-1" style={{color:"var(--color-text)"}}>Notification Preferences</h3>
          {[
            {label:"New contact added",       desc:"When a new contact is created"},
            {label:"Deal stage changed",       desc:"When a deal moves to a new stage"},
            {label:"Deal won or lost",         desc:"When a deal is marked as won or lost"},
            {label:"Stale deals alert",        desc:"When a deal has had no activity"},
            {label:"WhatsApp message received",desc:"New WhatsApp message notifications"},
          ].map(({label,desc},i)=>(
            <div key={label} className="flex items-center justify-between p-3.5 rounded-xl"
              style={{background:"rgba(139,92,246,0.04)",border:"1px solid rgba(139,92,246,0.08)"}}>
              <div>
                <p className="text-sm font-medium" style={{color:"var(--color-text)"}}>{label}</p>
                <p className="text-xs mt-0.5" style={{color:"var(--color-text-secondary)"}}>{desc}</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" defaultChecked={i<3} className="sr-only peer"/>
                <div className="w-10 h-5 rounded-full peer peer-checked:after:translate-x-5 after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:w-4 after:h-4 after:rounded-full after:bg-white after:transition-all"
                  style={{background:"rgba(139,92,246,0.2)"}}
                  onMouseEnter={e=>{}}
                  ref={el=>{if(el){const input=el.previousElementSibling as HTMLInputElement;const update=()=>{el.style.background=input.checked?"var(--color-primary)":"rgba(139,92,246,0.2)"};input.addEventListener("change",update);update();}}}
                />
              </label>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
