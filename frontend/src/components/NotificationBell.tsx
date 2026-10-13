import { Bell, Check, RefreshCw, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

type Notice = { type: string; severity: string; title: string; message: string; trainingId?: string; action?: string };

export default function NotificationBell() {
  const [items, setItems] = useState<Notice[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const navigate = useNavigate();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get<{ items?: Notice[] }>("/notifications");
      setItems(Array.isArray(response.data.items) ? response.data.items : []);
      setLastUpdated(new Date());
    } catch {
      // Keep the last successful notification list if the network is temporarily unavailable.
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => { if (document.visibilityState === "visible") void load(); }, 30000);
    const onFocus = () => void load();
    const onVisibility = () => { if (document.visibilityState === "visible") void load(); };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [load]);

  function openNotice(notice: Notice) {
    setOpen(false);
    if (notice.action === "attendance") navigate("/attendance");
    else if (notice.action === "feedback") navigate("/feedback");
    else if (notice.trainingId) navigate("/trainings");
    else if (notice.action === "evaluation") navigate("/evaluations");
    else if (notice.action === "training") navigate("/trainings");
  }

  return <div className="relative">
    <button aria-label={`Notifications${items.length ? `, ${items.length} active` : ""}`} aria-expanded={open} onClick={() => { setOpen((value) => !value); if (!open) void load(); }} className="relative rounded-xl border border-slate-200 bg-white p-2.5 text-slate-600 hover:bg-slate-50">
      <Bell size={19}/>
      {items.length > 0 && <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white">{items.length > 99 ? "99+" : items.length}</span>}
    </button>
    {open && <>
      <button aria-label="Close notifications" className="fixed inset-0 z-30 cursor-default" onClick={() => setOpen(false)} />
      <div className="absolute right-0 z-40 mt-2 w-[min(24rem,calc(100vw-2rem))] rounded-2xl border border-slate-200 bg-white p-3 shadow-xl">
        <div className="flex items-center justify-between px-2 py-1"><div><p className="font-semibold text-slate-900">Notifications</p><p className="text-xs text-slate-500">{items.length} active · updates automatically</p></div><div className="flex items-center gap-1"><button aria-label="Refresh notifications" title="Refresh" disabled={loading} onClick={() => void load()} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 disabled:opacity-50"><RefreshCw size={15} className={loading ? "animate-spin" : ""}/></button><button aria-label="Close notifications" onClick={() => setOpen(false)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={17}/></button></div></div>
        <div className="mt-2 max-h-[min(65vh,28rem)] space-y-2 overflow-y-auto">
          {loading && items.length === 0 ? <p className="p-4 text-sm text-slate-500">Loading notifications…</p> : items.length === 0 ? <div className="p-5 text-center"><Check size={24} className="mx-auto text-emerald-600"/><p className="mt-2 text-sm font-medium text-slate-700">You're all caught up.</p><p className="mt-1 text-xs text-slate-500">We'll check for updates automatically.</p></div> : items.map((item, index) => <button key={`${item.type}-${item.trainingId || "general"}-${index}`} onClick={() => openNotice(item)} className="block w-full rounded-xl border border-slate-100 bg-slate-50 p-3 text-left transition hover:border-indigo-200 hover:bg-indigo-50"><span className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${item.severity === "high" ? "bg-rose-100 text-rose-700" : item.severity === "medium" ? "bg-amber-100 text-amber-700" : "bg-indigo-100 text-indigo-700"}`}>{item.type}</span><p className="mt-1 text-sm font-semibold text-slate-900">{item.title}</p><p className="mt-1 text-xs leading-5 text-slate-600">{item.message}</p></button>)}
        </div>
        {lastUpdated && <p className="px-2 pt-2 text-[10px] text-slate-400">Last checked {lastUpdated.toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"})}</p>}
      </div>
    </>}
  </div>;
}
