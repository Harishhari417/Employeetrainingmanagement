import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { LockKeyhole, LogIn, UserPlus, UserRound } from "lucide-react";
import LogoPlaceholder from "../components/LogoPlaceholder";
import { useAuth } from "../auth/AuthContext";
import { api } from "../services/api";

const departments = ["Production","QA / Quality","Store","HR","Maintenance","Engineering / R&D","Finance","Purchase","Sales","Management","Other"];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login"|"signup">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [form, setForm] = useState({
    employeeId:"", name:"", email:"", password:"", confirmPassword:"",
    department:"Production", designation:"", reportingManager:""
  });
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submitLogin(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setError(""); setSubmitting(true);
    try { await login(username.trim(), password); navigate("/", { replace: true }); }
    catch (err:any) { setError(err?.response?.data?.message ?? "Unable to sign in. Please check your credentials."); }
    finally { setSubmitting(false); }
  }

  async function submitSignup(e: FormEvent<HTMLFormElement>) {
    e.preventDefault(); setError(""); setMessage("");
    if (form.password !== form.confirmPassword) { setError("Passwords do not match."); return; }
    setSubmitting(true);
    try {
      await api.post("/auth/signup", {
        employeeId: form.employeeId, name: form.name, email: form.email,
        password: form.password, department: form.department,
        designation: form.designation, reportingManager: form.reportingManager
      });
      setMessage("Signup successful. You can now sign in with your Employee ID and password.");
      setUsername(form.employeeId.toUpperCase()); setPassword("");
      setMode("login");
      setForm({...form, password:"", confirmPassword:""});
    } catch (err:any) {
      setError(err?.response?.data?.message ?? "Unable to create the employee account.");
    } finally { setSubmitting(false); }
  }

  return <main className="min-h-screen bg-slate-50 px-4 py-8 sm:px-6 lg:px-8">
    <div className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-5xl items-center gap-8 lg:grid-cols-2">
      <section className="hidden lg:block">
        <div className="mb-6 flex items-center gap-3"><LogoPlaceholder/><div><p className="font-bold">Training Management</p><p className="text-sm text-slate-500">Employee Training & Effectiveness Portal</p></div></div>
        <h1 className="text-4xl font-bold tracking-tight">One place for training, attendance and feedback.</h1>
        <p className="mt-4 max-w-xl text-slate-600">Employees can register with their complete profile, HR can create employee accounts, and training progress is shared across employee, manager and HR dashboards.</p>
        <div className="mt-8 grid grid-cols-2 gap-4">{["Employee signup","Training planning","Live progress","Attendance & feedback"].map(item=><div key={item} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"><p className="text-sm font-semibold">{item}</p></div>)}</div>
      </section>

      <section className="mx-auto w-full max-w-xl rounded-3xl border border-slate-200 bg-white p-6 shadow-xl sm:p-8">
        <div className="flex justify-center lg:hidden"><LogoPlaceholder/></div>
        <div className="mt-5 text-center"><h2 className="text-2xl font-bold">{mode==="login"?"Welcome back":"Create your employee account"}</h2><p className="mt-2 text-sm text-slate-500">{mode==="login"?"Sign in with the Employee ID and password stored in the portal.":"All fields marked with * are required."}</p></div>

        <div className="mt-6 grid grid-cols-2 rounded-xl bg-slate-100 p-1">
          <button type="button" onClick={()=>{setMode("login");setError("");setMessage("");}} className={`rounded-lg px-3 py-2.5 text-sm font-semibold ${mode==="login"?"bg-white text-indigo-700 shadow-sm":"text-slate-600"}`}><span className="inline-flex items-center gap-2"><LogIn size={16}/> Sign in</span></button>
          <button type="button" onClick={()=>{setMode("signup");setError("");setMessage("");}} className={`rounded-lg px-3 py-2.5 text-sm font-semibold ${mode==="signup"?"bg-white text-indigo-700 shadow-sm":"text-slate-600"}`}><span className="inline-flex items-center gap-2"><UserPlus size={16}/> Sign up</span></button>
        </div>

        {error && <div className="mt-5 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
        {message && <div className="mt-5 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</div>}

        {mode==="login" ? <form onSubmit={submitLogin} className="mt-6 space-y-4">
          <label className="block"><span className="mb-1.5 block text-sm font-medium">Employee ID / HR ID</span><div className="relative"><UserRound size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"/><input required value={username} onChange={e=>setUsername(e.target.value)} autoComplete="username" className="w-full rounded-xl border border-slate-200 py-3 pl-10 pr-4 outline-none focus:border-indigo-500" placeholder="e.g. E001"/></div></label>
          <label className="block"><span className="mb-1.5 block text-sm font-medium">Password</span><div className="relative"><LockKeyhole size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"/><input required type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password" className="w-full rounded-xl border border-slate-200 py-3 pl-10 pr-4 outline-none focus:border-indigo-500"/></div></label>
          <button disabled={submitting} className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3 font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"><LogIn size={18}/>{submitting?"Signing in...":"Sign in"}</button>
          <p className="text-center text-xs text-slate-500">Employees can sign in only after self-signup or after HR creates their account.</p>
        </form> : <form onSubmit={submitSignup} className="mt-6 grid gap-4 sm:grid-cols-2">
          {[
            ["Employee ID *","employeeId","text"],["Full name *","name","text"],["Email *","email","email"],["Position / Designation *","designation","text"],["Reporting Manager","reportingManager","text"]
          ].map(([label,key,type])=><label key={key} className={key==="email"?"block":"block"}><span className="mb-1.5 block text-sm font-medium">{label}</span><input required={!["reportingManager"].includes(key)} type={type} value={(form as any)[key]} onChange={e=>setForm({...form,[key]:e.target.value})} className="w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-indigo-500"/></label>)}
          <label><span className="mb-1.5 block text-sm font-medium">Department *</span><select required value={form.department} onChange={e=>setForm({...form,department:e.target.value})} className="w-full rounded-xl border border-slate-200 px-3 py-2.5">{departments.map(d=><option key={d}>{d}</option>)}</select></label>
          <label><span className="mb-1.5 block text-sm font-medium">Password *</span><input required minLength={8} type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} className="w-full rounded-xl border border-slate-200 px-3 py-2.5"/></label>
          <label><span className="mb-1.5 block text-sm font-medium">Confirm Password *</span><input required minLength={8} type="password" value={form.confirmPassword} onChange={e=>setForm({...form,confirmPassword:e.target.value})} className="w-full rounded-xl border border-slate-200 px-3 py-2.5"/></label>
          <div className="sm:col-span-2"><button disabled={submitting} className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3 font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"><UserPlus size={18}/>{submitting?"Creating account...":"Create employee account"}</button></div>
        </form>}
      </section>
    </div>
  </main>;
}
