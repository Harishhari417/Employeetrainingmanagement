
import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { LockKeyhole, LogIn, UserPlus, UserRound, MailCheck } from "lucide-react";
import LogoPlaceholder from "../components/LogoPlaceholder";
import { useAuth } from "../auth/AuthContext";
import { api } from "../services/api";

const departments = ["HR","Management","Finance","Maintenance","Production","QA / Quality","Stores","OQC"];

type Form = {
  employeeId:string; name:string; email:string; password:string; confirmPassword:string;
  department:string; designation:string; reportingManager:string; role:string;
};

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [mode,setMode]=useState<"login"|"signup">("login");
  const [signupStep,setSignupStep]=useState<"details"|"code">("details");
  const [username,setUsername]=useState(""); const [password,setPassword]=useState("");
  const [code,setCode]=useState("");
  const [form,setForm]=useState<Form>({employeeId:"",name:"",email:"",password:"",confirmPassword:"",department:"Production",designation:"",reportingManager:"",role:"EMPLOYEE"});
  const [error,setError]=useState(""); const [message,setMessage]=useState(""); const [submitting,setSubmitting]=useState(false);

  const resetMessages=()=>{setError("");setMessage("")};

  async function submitLogin(e:FormEvent<HTMLFormElement>) {
    e.preventDefault(); resetMessages(); setSubmitting(true);
    try {
      await login(username.trim(),password);
      const raw=localStorage.getItem("auth_user"); const role=raw?JSON.parse(raw).role:"EMPLOYEE";
      navigate(role==="HR_ADMIN"?"/admin":role==="MANAGER"?"/manager":"/employee",{replace:true});
    } catch(err:any) { setError(err?.response?.data?.message??"Unable to sign in. Please check your credentials."); }
    finally { setSubmitting(false); }
  }

  async function requestCode(e:FormEvent<HTMLFormElement>) {
    e.preventDefault(); resetMessages();
    if(form.password!==form.confirmPassword){setError("Passwords do not match.");return;}
    setSubmitting(true);
    try {
      await api.post("/auth/signup/request-code",form);
      setSignupStep("code");
      setMessage(`A 6-digit verification code was sent to ${form.email}.`);
    } catch(err:any) {setError(err?.response?.data?.message??"Unable to send verification code.");}
    finally{setSubmitting(false);}
  }

  async function verifySignup(e:FormEvent<HTMLFormElement>) {
    e.preventDefault(); resetMessages();
    if(!/^\d{6}$/.test(code)){setError("Enter the 6-digit verification code.");return;}
    setSubmitting(true);
    try {
      await api.post("/auth/signup/verify",{email:form.email,code});
      setMessage("Email verified and account created. You can now sign in.");
      setUsername(form.employeeId.toUpperCase()); setPassword(""); setCode(""); setSignupStep("details"); setMode("login");
      setForm({...form,password:"",confirmPassword:""});
    } catch(err:any){setError(err?.response?.data?.message??"Unable to verify the email.");}
    finally{setSubmitting(false);}
  }

  return <main className="min-h-screen bg-slate-50 px-4 py-8 sm:px-6 lg:px-8">
    <div className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-5xl items-center gap-8 lg:grid-cols-2">
      <section className="hidden lg:block">
        <div className="mb-6 flex items-center gap-3"><LogoPlaceholder/><div><p className="font-bold">Training Management</p><p className="text-sm text-slate-500">Employee Training & Effectiveness Portal</p></div></div>
        <h1 className="text-4xl font-bold tracking-tight">One place for training, attendance and feedback.</h1>
        <p className="mt-4 max-w-xl text-slate-600">Secure employee, manager and HR access with email verification and time-limited sessions.</p>
      </section>

      <section className="mx-auto w-full max-w-xl rounded-3xl border border-slate-200 bg-white p-6 shadow-xl sm:p-8">
        <div className="flex justify-center"><LogoPlaceholder/></div>
        <div className="mt-5 text-center"><h2 className="text-2xl font-bold">{mode==="login"?"Welcome back":signupStep==="code"?"Verify your email":"Create your account"}</h2><p className="mt-2 text-sm text-slate-500">{mode==="login"?"Sign in with your Employee ID and password.":signupStep==="code"?"Enter the 6-digit code sent to your email.":"All fields marked with * are required."}</p></div>
        <div className="mt-6 grid grid-cols-2 rounded-xl bg-slate-100 p-1">
          <button type="button" onClick={()=>{setMode("login");setSignupStep("details");resetMessages()}} className={`rounded-lg px-3 py-2.5 text-sm font-semibold ${mode==="login"?"bg-white text-indigo-700 shadow-sm":"text-slate-600"}`}><span className="inline-flex items-center gap-2"><LogIn size={16}/>Sign in</span></button>
          <button type="button" onClick={()=>{setMode("signup");resetMessages()}} className={`rounded-lg px-3 py-2.5 text-sm font-semibold ${mode==="signup"?"bg-white text-indigo-700 shadow-sm":"text-slate-600"}`}><span className="inline-flex items-center gap-2"><UserPlus size={16}/>Sign up</span></button>
        </div>
        {error&&<div className="mt-5 rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
        {message&&<div className="mt-5 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{message}</div>}

        {mode==="login"?<form onSubmit={submitLogin} className="mt-6 space-y-4">
          <label className="block"><span className="mb-1.5 block text-sm font-medium">Employee ID / HR ID</span><div className="relative"><UserRound size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"/><input required value={username} onChange={e=>setUsername(e.target.value)} autoComplete="username" className="w-full rounded-xl border py-3 pl-10 pr-4 outline-none focus:border-indigo-500"/></div></label>
          <label className="block"><span className="mb-1.5 block text-sm font-medium">Password</span><div className="relative"><LockKeyhole size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"/><input required type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password" className="w-full rounded-xl border py-3 pl-10 pr-4 outline-none focus:border-indigo-500"/></div></label>
          <button disabled={submitting} className="flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3 font-semibold text-white disabled:opacity-60"><LogIn size={18}/>{submitting?"Signing in...":"Sign in"}</button>
        </form>:signupStep==="details"?<form onSubmit={requestCode} className="mt-6 grid gap-4 sm:grid-cols-2">
          {([["Employee ID *","employeeId","text"],["Full name *","name","text"],["Email *","email","email"],["Position / Designation *","designation","text"],["Reporting Manager","reportingManager","text"]] as string[][]).map(([label,key,type])=><label key={key}><span className="mb-1.5 block text-sm font-medium">{label}</span><input required={key!=="reportingManager"} type={type} value={(form as any)[key]} onChange={e=>setForm({...form,[key]:e.target.value})} className="w-full rounded-xl border px-3 py-2.5 outline-none focus:border-indigo-500"/></label>)}
          <label><span className="mb-1.5 block text-sm font-medium">Account type *</span><select value={form.role} onChange={e=>setForm({...form,role:e.target.value})} className="w-full rounded-xl border px-3 py-2.5"><option value="EMPLOYEE">Employee</option><option value="MANAGER">Manager</option><option value="ADMIN">Admin</option></select></label>
          <label><span className="mb-1.5 block text-sm font-medium">Department *</span><select value={form.department} onChange={e=>setForm({...form,department:e.target.value})} className="w-full rounded-xl border px-3 py-2.5">{departments.map(d=><option key={d}>{d}</option>)}</select></label>
          <label><span className="mb-1.5 block text-sm font-medium">Password *</span><input required minLength={8} type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} className="w-full rounded-xl border px-3 py-2.5"/></label>
          <label><span className="mb-1.5 block text-sm font-medium">Confirm Password *</span><input required minLength={8} type="password" value={form.confirmPassword} onChange={e=>setForm({...form,confirmPassword:e.target.value})} className="w-full rounded-xl border px-3 py-2.5"/></label>
          <button disabled={submitting} className="sm:col-span-2 flex w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 py-3 font-semibold text-white disabled:opacity-60"><MailCheck size={18}/>{submitting?"Sending code...":"Send verification code"}</button>
        </form>:<form onSubmit={verifySignup} className="mt-6 space-y-5">
          <div className="rounded-xl bg-indigo-50 p-4 text-sm text-indigo-800">Verification code sent to <b>{form.email}</b>. The code expires in 10 minutes.</div>
          <input autoFocus required maxLength={6} inputMode="numeric" value={code} onChange={e=>setCode(e.target.value.replace(/\D/g,"").slice(0,6))} placeholder="000000" className="w-full rounded-xl border px-4 py-4 text-center text-2xl font-bold tracking-[0.5em]"/>
          <button disabled={submitting} className="w-full rounded-xl bg-indigo-600 py-3 font-semibold text-white disabled:opacity-60">{submitting?"Verifying...":"Verify & Create Account"}</button>
          <button type="button" onClick={()=>setSignupStep("details")} className="w-full rounded-xl border py-3 text-sm font-semibold">Back</button>
        </form>}
      </section>
    </div>
  </main>;
}
