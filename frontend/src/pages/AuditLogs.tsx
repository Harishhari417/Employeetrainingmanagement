import { useEffect, useMemo, useState } from "react";
import { Activity, RefreshCw, Search } from "lucide-react";
import { api } from "../services/api";

type AuditRow = { actorEmployeeId?: string; actorRole?: string; action?: string; entityType?: string; entityId?: string; details?: Record<string, unknown>; createdAt?: string };

export default function AuditLogs() {
  const [rows, setRows] = useState<AuditRow[]>([]);
  const [search, setSearch] = useState("");
  const [action, setAction] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await api.get("/reports/audit", { params: action ? { action } : {} });
      setRows(Array.isArray(response.data) ? response.data : []);
    } catch (e: any) {
      setError(e?.response?.data?.message || "Could not load audit history. Confirm that you are signed in as HR Admin.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, [action]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((r) => [r.actorEmployeeId, r.actorRole, r.action, r.entityType, r.entityId, JSON.stringify(r.details || {})].join(" ").toLowerCase().includes(q));
  }, [rows, search]);

  const dateText = (value?: string) => {
    if (!value) return "—";
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? value : d.toLocaleString();
  };

  return <main className="mx-auto w-full max-w-7xl space-y-6 p-4 sm:p-6 lg:p-8">
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div><p className="text-sm font-semibold uppercase tracking-wide text-indigo-600">Administration</p><h1 className="mt-1 text-2xl font-bold text-slate-900">Audit history</h1><p className="mt-1 text-sm text-slate-500">Review training, attendance and feedback changes recorded by the system.</p></div>
      <button onClick={() => void load()} className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"><RefreshCw size={16}/> Refresh</button>
    </div>
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
      <div className="grid gap-3 sm:grid-cols-[1fr_220px]">
        <label className="relative block"><Search size={17} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"/><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search actor, action, training ID..." className="w-full rounded-xl border border-slate-200 py-2.5 pl-10 pr-3 text-sm outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"/></label>
        <select value={action} onChange={(e) => setAction(e.target.value)} className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-indigo-400"><option value="">All actions</option><option value="training.created">Training created</option><option value="training.updated">Training updated</option><option value="training.deleted">Training deleted</option><option value="training.completed">Training completed</option><option value="attendance.updated">Attendance updated</option><option value="feedback.submitted">Feedback submitted</option></select>
      </div>
      {error && <p role="alert" className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
      <div className="mt-4 overflow-x-auto rounded-xl border border-slate-100">
        <table className="w-full min-w-[850px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-4 py-3">Date / time</th><th className="px-4 py-3">Actor</th><th className="px-4 py-3">Action</th><th className="px-4 py-3">Record</th><th className="px-4 py-3">Details</th></tr></thead><tbody className="divide-y divide-slate-100">
          {loading ? <tr><td colSpan={5} className="px-4 py-12 text-center text-slate-500">Loading audit history…</td></tr> : filtered.length === 0 ? <tr><td colSpan={5} className="px-4 py-12 text-center"><Activity className="mx-auto mb-2 text-slate-300" size={28}/><p className="font-medium text-slate-700">No audit entries found</p><p className="mt-1 text-slate-500">New tracked changes will appear here.</p></td></tr> : filtered.map((r, i) => <tr key={`${r.createdAt}-${r.entityId}-${i}`} className="align-top hover:bg-slate-50"><td className="whitespace-nowrap px-4 py-3 text-slate-600">{dateText(r.createdAt)}</td><td className="px-4 py-3"><p className="font-medium text-slate-900">{r.actorEmployeeId || "System"}</p><p className="mt-0.5 text-xs text-slate-500">{r.actorRole || "—"}</p></td><td className="px-4 py-3"><span className="rounded-lg bg-indigo-50 px-2 py-1 text-xs font-semibold text-indigo-700">{(r.action || "event").replaceAll("_", " ")}</span></td><td className="px-4 py-3"><p className="font-medium text-slate-800">{r.entityType || "record"}</p><p className="mt-0.5 break-all font-mono text-xs text-slate-500">{r.entityId || "—"}</p></td><td className="max-w-md whitespace-pre-wrap break-words px-4 py-3 text-xs text-slate-600">{r.details && Object.keys(r.details).length ? JSON.stringify(r.details, null, 2) : "—"}</td></tr>)}
        </tbody></table>
      </div>
      <p className="mt-3 text-xs text-slate-500">Showing {filtered.length} of {rows.length} loaded records. The server limits results to the latest 1,000 entries.</p>
    </section>
  </main>;
}
