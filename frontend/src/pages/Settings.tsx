import { useState, type FormEvent } from "react";
import { KeyRound, ShieldCheck } from "lucide-react";
import { api } from "../services/api";
import { useAuth } from "../auth/AuthContext";

export default function Settings(){
 const {user,logout}=useAuth();
 const [currentPassword,setCurrentPassword]=useState("");
 const [newPassword,setNewPassword]=useState("");
 const [confirm,setConfirm]=useState("");
 const [message,setMessage]=useState(""); const [error,setError]=useState(""); const [saving,setSaving]=useState(false);
 async function submit(e:FormEvent){e.preventDefault();setError("");setMessage("");if(newPassword!==confirm){setError("New passwords do not match.");return;}setSaving(true);try{await api.put("/auth/password",{currentPassword,newPassword});setMessage("Password changed. Please sign in again.");setTimeout(logout,800);}catch(err:any){setError(err?.response?.data?.message||"Unable to change password.");}finally{setSaving(false);}}
 return <div className="mx-auto max-w-2xl space-y-6">
  <section><p className="text-sm font-medium text-indigo-600">Account</p><h1 className="mt-1 text-2xl font-bold sm:text-3xl">Account & Security</h1><p className="mt-2 text-sm text-slate-500">Change the password for your {user?.employeeId} account.</p></section>
  <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
   <div className="flex items-center gap-3"><div className="rounded-xl bg-indigo-50 p-3 text-indigo-600"><ShieldCheck size={20}/></div><div><h2 className="font-semibold">{user?.name}</h2><p className="text-xs text-slate-500">{user?.employeeId} · {user?.department||user?.role}</p></div></div>
   {error&&<div className="mt-5 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}{message&&<div className="mt-5 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</div>}
   <form onSubmit={submit} className="mt-6 space-y-4">
    <label className="block"><span className="mb-1.5 block text-sm font-medium">Current password</span><input required type="password" value={currentPassword} onChange={e=>setCurrentPassword(e.target.value)} className="w-full rounded-xl border border-slate-200 px-3 py-3"/></label>
    <label className="block"><span className="mb-1.5 block text-sm font-medium">New password</span><input required minLength={8} type="password" value={newPassword} onChange={e=>setNewPassword(e.target.value)} className="w-full rounded-xl border border-slate-200 px-3 py-3"/></label>
    <label className="block"><span className="mb-1.5 block text-sm font-medium">Confirm new password</span><input required minLength={8} type="password" value={confirm} onChange={e=>setConfirm(e.target.value)} className="w-full rounded-xl border border-slate-200 px-3 py-3"/></label>
    <button disabled={saving} className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white disabled:opacity-60"><KeyRound size={17}/>{saving?"Saving...":"Change password"}</button>
   </form>
  </section>
 </div>
}
