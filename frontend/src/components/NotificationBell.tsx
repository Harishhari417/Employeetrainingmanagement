import { Bell, X } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../services/api";

type Notice = { type: string; severity: string; title: string; message: string };

export default function NotificationBell() {
  const [items, setItems] = useState<Notice[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const load = () => api.get<{items: Notice[]}>("/notifications").then(r=>setItems(r.data.items)).catch(()=>{});
    load();
    const timer = window.setInterval(load, 60000);
    return () => window.clearInterval(timer);
  }, []);

  return <div className="relative">
    <button aria-label="Notifications" onClick={()=>setOpen(!open)} className="relative rounded-xl border border-slate-200 bg-white p-2.5 text-slate-600 hover:bg-slate-50">
      <Bell size={19}/>
      {items.length > 0 && <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white">{items.length}</span>}
    </button>
    {open && <div className="absolute right-0 z-40 mt-2 w-[min(22rem,calc(100vw-2rem))] rounded-2xl border border-slate-200 bg-white p-3 shadow-xl">
      <div className="flex items-center justify-between px-2 py-1"><div><p className="font-semibold">Notifications</p><p className="text-xs text-slate-500">{items.length} active</p></div><button onClick={()=>setOpen(false)}><X size={17}/></button></div>
      <div className="mt-2 max-h-80 space-y-2 overflow-y-auto">
        {items.length === 0 ? <p className="p-3 text-sm text-slate-500">You're all caught up.</p> : items.map((x,i)=><div key={i} className="rounded-xl bg-slate-50 p-3"><p className="text-sm font-semibold">{x.title}</p><p className="mt-1 text-xs leading-5 text-slate-500">{x.message}</p></div>)}
      </div>
    </div>}
  </div>;
}
