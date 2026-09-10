import { useEffect, useState } from "react";
import { CheckCircle2, Save } from "lucide-react";
import { api } from "../services/api";
import { useAuth } from "../auth/AuthContext";

type Training = { _id: string; title: string; trainingDate?: string; venue?: string; trainerName?: string; durationMinutes?: number };
type Row = { employeeId: string; employeeName: string; department: string; attendance: "Present" | "Absent" | "Partial"; feedbackStatus: string };

export default function Attendance() {
  const { user } = useAuth();
  const [trainings, setTrainings] = useState<Training[]>([]);
  const [trainingId, setTrainingId] = useState("");
  const [rows, setRows] = useState<Row[]>([]);
  const [message, setMessage] = useState("");

  useEffect(() => { api.get<Training[]>("/trainings").then(r => { setTrainings(r.data); if (r.data[0]) setTrainingId(r.data[0]._id); }).catch(() => {}); }, []);
  useEffect(() => { if (!trainingId) return; api.get<Row[]>(`/attendance?trainingId=${trainingId}`).then(r => setRows(r.data)).catch(() => setRows([])); }, [trainingId]);

  const save = async () => {
    await api.post("/attendance/bulk", { trainingId, rows: rows.map(r => ({ employeeId: r.employeeId, attendance: r.attendance })) });
    setMessage("Attendance saved successfully."); setTimeout(() => setMessage(""), 3000);
  };
  const selected = trainings.find(t => t._id === trainingId);

  return <div className="space-y-6">
    <div><p className="text-sm font-medium text-indigo-600">Training Attendance</p><h1 className="mt-1 text-2xl font-bold sm:text-3xl">Attendance Sheet</h1><p className="mt-2 text-sm text-slate-500">Mark attendance per trainee for each scheduled training session.</p></div>
    {message && <div className="flex items-center gap-2 rounded-xl bg-emerald-50 p-4 text-sm font-medium text-emerald-700"><CheckCircle2 size={18}/>{message}</div>}
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="lg:col-span-2"><label className="mb-2 block text-sm font-medium">Training / Topic</label><select value={trainingId} onChange={e=>setTrainingId(e.target.value)} className="w-full rounded-xl border border-slate-200 px-3 py-3 text-sm"><option value="">Select training</option>{trainings.map(t=><option key={t._id} value={t._id}>{t.title}</option>)}</select></div>
        <div><p className="text-xs text-slate-500">Faculty</p><p className="mt-1 font-semibold">{selected?.trainerName || "—"}</p></div>
        <div><p className="text-xs text-slate-500">Date / Duration</p><p className="mt-1 font-semibold">{selected?.trainingDate || "—"} · {selected?.durationMinutes ? `${Math.floor(selected.durationMinutes/60)}h ${selected.durationMinutes%60}m` : "—"}</p></div>
        <div className="md:col-span-2 lg:col-span-4"><p className="text-xs text-slate-500">Venue</p><p className="mt-1 font-semibold">{selected?.venue || "—"}</p></div>
      </div>
    </section>
    <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 p-5"><div><h2 className="font-semibold">Trainee attendance</h2><p className="text-sm text-slate-500">{rows.length} assigned participant(s)</p></div>{user?.role !== "EMPLOYEE" && <button onClick={save} disabled={!rows.length} className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"><Save size={17}/> Save Attendance</button>}</div>
      <div className="overflow-x-auto"><table className="min-w-[800px] w-full text-sm"><thead className="bg-slate-50"><tr>{["Sl No","Emp ID","Name of Employee","Dept","Attendance","Feedback"].map(x=><th key={x} className="p-4 text-left font-semibold text-slate-600">{x}</th>)}</tr></thead><tbody>{rows.map((r,i)=><tr key={r.employeeId} className="border-t border-slate-100"><td className="p-4 text-slate-500">{i+1}</td><td className="p-4 font-medium">{r.employeeId}</td><td className="p-4">{r.employeeName}</td><td className="p-4">{r.department}</td><td className="p-4">{user?.role === "EMPLOYEE" ? r.attendance : <select value={r.attendance} onChange={e=>setRows(old=>old.map(x=>x.employeeId===r.employeeId?{...x,attendance:e.target.value as Row["attendance"]}:x))} className="rounded-lg border border-slate-200 px-3 py-2"><option>Present</option><option>Absent</option><option>Partial</option></select>}</td><td className="p-4"><span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold">{r.feedbackStatus}</span></td></tr>)}</tbody></table></div>
    </section>
  </div>;
}
