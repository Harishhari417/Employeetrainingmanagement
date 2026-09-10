import { ArrowRight, CalendarDays, CheckCircle2, Clock3, MessageSquareText, RefreshCw, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { api } from "../services/api";

type Stats={totalTrainings:number;completedTrainings:number;totalEmployees:number;attendancePercentage:number;feedbackCount:number;pendingFeedback:number;pendingEvaluations:number};
type Progress={trainingId:string;trainingTitle:string;employeeId:string;employeeName:string;department:string;attendance:string;completionStatus:string;feedbackStatus:string;updatedAt?:string|null};

export default function Dashboard(){
  const {user}=useAuth();
  const [s,setS]=useState<Stats>({totalTrainings:0,completedTrainings:0,totalEmployees:0,attendancePercentage:0,feedbackCount:0,pendingFeedback:0,pendingEvaluations:0});
  const [progress,setProgress]=useState<Progress[]>([]);
  const [refreshing,setRefreshing]=useState(false);

  async function load(){
    setRefreshing(true);
    try {
      const [stats, feed] = await Promise.all([api.get<Stats>("/dashboard/admin"), api.get<Progress[]>("/trainings/progress")]);
      setS(stats.data); setProgress(feed.data);
    } finally { setRefreshing(false); }
  }

  useEffect(()=>{ load().catch(()=>{}); const id=window.setInterval(()=>load().catch(()=>{}),5000); return ()=>window.clearInterval(id); },[]);

  const kpis=user?.role==="HR_ADMIN"
    ?[["Total Trainings",s.totalTrainings,"All programmes"],["Active Employees",s.totalEmployees,"Current employees"],["Completed Trainings",s.completedTrainings,"Marked complete"],["Attendance",`${s.attendancePercentage}%`,"Overall attendance"],["Feedback",s.feedbackCount,"Submitted responses"]]
    :user?.role==="MANAGER"
    ?[["Team Trainings",s.totalTrainings,"Assigned sessions"],["Team Members",s.totalEmployees,"Department members"],["Completed",s.completedTrainings,"Completed assignments"],["Attendance",`${s.attendancePercentage}%`,"Team attendance"]]
    :[["Assigned Trainings",s.totalTrainings,"Your assignments"],["Completed",s.completedTrainings,"Completed programmes"],["Attendance",`${s.attendancePercentage}%`,"Your attendance"],["Feedback Due",s.pendingFeedback,"Awaiting submission"]];

  const heading=user?.role==="HR_ADMIN"?"Training overview":user?.role==="MANAGER"?"Team training overview":"My training overview";
  const statusClass=(status:string)=>status==="Completed"?"bg-emerald-50 text-emerald-700":status==="In Progress"?"bg-indigo-50 text-indigo-700":"bg-amber-50 text-amber-700";
  async function updateProgress(p:Progress, status:"In Progress"|"Completed"){
    await api.put(`/trainings/${p.trainingId}/progress`, {employeeId:p.employeeId, completionStatus:status});
    await load();
  }

  return <div className="space-y-6">
    <section><div className="flex items-start justify-between gap-4"><div><p className="text-sm font-medium text-indigo-600">{user?.role.replace("_"," / ")}</p><h1 className="mt-1 text-2xl font-bold tracking-tight sm:text-3xl">{heading}</h1><p className="mt-2 text-sm text-slate-500">Monitor training activity, attendance, feedback and effectiveness.</p></div><button onClick={()=>load().catch(()=>{})} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600"><RefreshCw size={15} className={refreshing?"animate-spin":""}/> Live</button></div></section>
    <div className={`grid grid-cols-2 gap-4 ${kpis.length===5?"xl:grid-cols-5":"xl:grid-cols-4"}`}>{kpis.map(([l,v,n])=><div key={String(l)} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-xs font-medium uppercase tracking-wide text-slate-500">{l}</p><p className="mt-3 text-2xl font-bold">{v}</p><p className="mt-1 text-xs text-slate-500">{n}</p></div>)}</div>

    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between"><div><h2 className="font-semibold">{user?.role==="EMPLOYEE"?"My assigned training":"Live training progress"}</h2><p className="text-sm text-slate-500">{user?.role==="EMPLOYEE"?"Your assignments update as HR or your manager records activity.":"Updates automatically every 5 seconds."}</p></div><span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">Live</span></div>
      {progress.length===0 ? <div className="mt-5 rounded-xl bg-slate-50 p-6 text-center text-sm text-slate-500">No training assignments yet.</div> :
      <div className="mt-5 space-y-3">{progress.map((p,i)=><div key={`${p.trainingId}-${p.employeeId}-${i}`} className="rounded-xl border border-slate-100 p-4"><div className="flex flex-col gap-3 sm:flex-row sm:items-center"><div className="min-w-0 flex-1"><p className="font-semibold">{p.trainingTitle}</p><p className="mt-1 text-xs text-slate-500">{p.employeeName} ({p.employeeId}) · {p.department}</p></div><span className={`w-fit rounded-full px-3 py-1 text-xs font-semibold ${statusClass(p.completionStatus)}`}>{p.completionStatus}</span></div><div className="mt-3 grid grid-cols-2 gap-2 text-xs sm:grid-cols-3"><span className="rounded-lg bg-slate-50 px-3 py-2">Attendance: <b>{p.attendance}</b></span><span className="rounded-lg bg-slate-50 px-3 py-2">Feedback: <b>{p.feedbackStatus}</b></span><span className="rounded-lg bg-slate-50 px-3 py-2">Progress: <b>{p.completionStatus==="Completed"?"100%":p.completionStatus==="In Progress"?"50%":"0%"}</b></span></div>{user?.role==="EMPLOYEE" && p.completionStatus!=="Completed" && <div className="mt-3 flex justify-end"><button onClick={()=>updateProgress(p,p.completionStatus==="Assigned"?"In Progress":"Completed")} className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white">{p.completionStatus==="Assigned"?"Start training":"Mark training complete"}</button></div>}</div>)}</div>}
    </section>

    <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="font-semibold">Action required</h2><p className="text-sm text-slate-500">Items needing attention</p><div className="mt-5 space-y-3">{[
        { title: "Pending feedback", desc: `${s.pendingFeedback} feedback response(s) pending`, Icon: MessageSquareText },
        { title: "Pending evaluations", desc: `${s.pendingEvaluations} effectiveness evaluation(s) due`, Icon: Clock3 },
        { title: "Upcoming trainings", desc: "Review scheduled training sessions", Icon: CalendarDays },
      ].map(({ title, desc, Icon }) => (
        <div className="flex items-center gap-4 rounded-xl bg-slate-50 p-4" key={title}>
          <div className="rounded-xl bg-white p-3 text-indigo-600 shadow-sm"><Icon size={20} /></div>
          <div className="min-w-0 flex-1"><p className="text-sm font-semibold">{title}</p><p className="text-xs text-slate-500">{desc}</p></div>
          <ArrowRight size={17} className="text-slate-400" />
        </div>
      ))}</div></section>
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center gap-3"><div className="rounded-xl bg-indigo-50 p-3 text-indigo-600"><Users size={20}/></div><div><h2 className="font-semibold">Portal workflow</h2><p className="text-sm text-slate-500">Training lifecycle</p></div></div><div className="mt-5 space-y-3 text-sm">{["Create / assign training","Record trainee attendance","Collect training feedback","Complete 3-month effectiveness review","Review analytics and reports"].map((x,i)=><div key={x} className="flex gap-3 rounded-xl bg-slate-50 p-3"><span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-700">{i+1}</span><span className="font-medium">{x}</span></div>)}</div></section>
    </div>
  </div>
}
