import { useEffect, useMemo, useState } from "react";
import { Database, Plus, Pencil, Trash2, RefreshCw, Search, X } from "lucide-react";
import { api } from "../services/api";
type CollectionInfo = {
    key: string;
    label: string;
    count: number;
};
type RecordItem = Record<string, unknown> & {
    _id: string;
};
type RecordResponse = {
    records: RecordItem[];
    total: number;
    page: number;
    limit: number;
};
export default function AdminDatabase() {
    const [collections, setCollections] = useState<CollectionInfo[]>([]);
    const [collection, setCollection] = useState("employees");
    const [records, setRecords] = useState<RecordItem[]>([]);
    const [selected, setSelected] = useState<RecordItem | null>(null);
    const [editor, setEditor] = useState(false);
    const [json, setJson] = useState("{}");
    const [search, setSearch] = useState("");
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const currentCollection = useMemo(() => collections.find((item) => item.key === collection), [collections, collection]);
    const loadCollections = async () => {
        const response = await api.get<CollectionInfo[]>("/admin/collections");
        setCollections(response.data);
    };
    const loadRecords = async () => {
        setBusy(true);
        setError("");
        try {
            const response = await api.get<RecordResponse>(`/admin/data/${collection}`, {
                params: { search, page: 1, limit: 100 },
            });
            setRecords(response.data.records || []);
            await loadCollections();
        }
        catch (requestError: any) {
            setError(requestError.response?.data?.message || "Unable to load database records.");
        }
        finally {
            setBusy(false);
        }
    };
    useEffect(() => {
        loadCollections().catch(() => setError("Unable to load database collections."));
    }, []);
    useEffect(() => {
        loadRecords();
    }, [collection]);
    const openCreate = () => {
        setSelected(null);
        setJson(collection === "employees"
            ? JSON.stringify({ employeeId: "", name: "", department: "", designation: "", email: "", mobile: "", status: "Active" }, null, 2)
            : "{}");
        setEditor(true);
        setMessage("");
        setError("");
        window.scrollTo({ top: 0, behavior: "smooth" });
    };
    const openEdit = (record: RecordItem) => {
        setSelected(record);
        const { _id: recordId, ...editable } = record;
        void recordId;
        setJson(JSON.stringify(editable, null, 2));
        setEditor(true);
        setMessage("");
        setError("");
        window.scrollTo({ top: 0, behavior: "smooth" });
    };
    const save = async () => {
        setError("");
        setMessage("");
        let payload: Record<string, unknown>;
        try {
            payload = JSON.parse(json);
            if (!payload || Array.isArray(payload) || typeof payload !== "object") {
                throw new Error("Enter a valid JSON object.");
            }
        }
        catch (parseError) {
            setError(parseError instanceof Error ? parseError.message : "Invalid JSON.");
            return;
        }
        setBusy(true);
        try {
            if (selected?._id) {
                await api.put(`/admin/data/${collection}/${selected._id}`, payload);
                setMessage("Record updated successfully.");
            }
            else {
                await api.post(`/admin/data/${collection}`, payload);
                setMessage("Record created successfully.");
            }
            setEditor(false);
            await loadRecords();
            window.scrollTo({ top: 0, behavior: "smooth" });
        }
        catch (requestError: any) {
            setError(requestError.response?.data?.message || "Unable to save record.");
        }
        finally {
            setBusy(false);
        }
    };
    const remove = async (record: RecordItem) => {
        if (!window.confirm("Delete this database record permanently? This action cannot be undone."))
            return;
        setBusy(true);
        setError("");
        try {
            await api.delete(`/admin/data/${collection}/${record._id}`);
            setMessage("Record deleted successfully.");
            await loadRecords();
            window.scrollTo({ top: 0, behavior: "smooth" });
        }
        catch (requestError: any) {
            setError(requestError.response?.data?.message || "Unable to delete record.");
        }
        finally {
            setBusy(false);
        }
    };
    const displayValue = (value: unknown) => {
        if (value === null || value === undefined || value === "")
            return "—";
        if (typeof value === "object")
            return JSON.stringify(value);
        return String(value);
    };
    return (<div className="mx-auto w-full max-w-[1600px] space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-indigo-600"><Database size={20}/><span className="text-sm font-semibold">HR Admin</span></div>
          <h1 className="mt-1 text-2xl font-bold text-slate-900 sm:text-3xl">Database Management</h1>
          <p className="mt-2 text-sm text-slate-500">View, create, edit and delete application records. Employee records include email and mobile details.</p>
        </div>
        <button onClick={openCreate} className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700"><Plus size={17}/> Add Record</button>
      </div>

      {message && <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{message}</div>}
      {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      {editor && (<section className="scroll-mt-4 rounded-2xl border border-indigo-200 bg-white p-4 shadow-sm sm:p-6">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div><h2 className="font-semibold text-slate-900">{selected ? "Edit Record" : "Create Record"}</h2><p className="text-xs text-slate-500">{currentCollection?.label || collection}</p></div>
            <button aria-label="Close editor" onClick={() => setEditor(false)} className="rounded-lg p-2 hover:bg-slate-100"><X size={18}/></button>
          </div>
          <label className="mb-2 block text-sm font-medium text-slate-700">Record fields (JSON)</label>
          <textarea value={json} onChange={(event) => setJson(event.target.value)} rows={14} spellCheck={false} className="w-full rounded-xl border border-slate-300 bg-slate-950 p-4 font-mono text-xs text-emerald-100 outline-none focus:border-indigo-500 sm:text-sm"/>
          <p className="mt-2 text-xs text-slate-500">Edit all fields as JSON. Do not include _id. Password fields are excluded from this management screen.</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <button disabled={busy} onClick={save} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{busy ? "Saving…" : "Save Record"}</button>
            <button onClick={() => setEditor(false)} className="rounded-xl border px-4 py-2.5 text-sm font-semibold text-slate-700">Cancel</button>
          </div>
        </section>)}

      <section className="rounded-2xl border bg-white p-4 shadow-sm sm:p-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <label className="block min-w-0 flex-1 text-xs font-semibold text-slate-600">Database collection
            <select value={collection} onChange={(event) => { setCollection(event.target.value); setEditor(false); }} className="mt-1 block w-full rounded-xl border bg-white px-3 py-2.5 text-sm">
              {collections.map((item) => <option key={item.key} value={item.key}>{item.label} ({item.count})</option>)}
            </select>
          </label>
          <div className="flex w-full gap-2 lg:max-w-md">
            <div className="relative min-w-0 flex-1"><Search size={16} className="absolute left-3 top-3 text-slate-400"/><input value={search} onChange={(event) => setSearch(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter")
        loadRecords(); }} placeholder="Search name, employee ID, email…" className="w-full rounded-xl border py-2.5 pl-9 pr-3 text-sm"/></div>
            <button onClick={loadRecords} className="inline-flex items-center gap-2 rounded-xl border px-3 py-2.5 text-sm font-semibold"><RefreshCw size={15} className={busy ? "animate-spin" : ""}/> Refresh</button>
          </div>
        </div>
        <div className="mt-4 overflow-x-auto rounded-xl border">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-4 py-3">Record ID</th><th className="px-4 py-3">Name / Title</th><th className="px-4 py-3">Employee ID</th><th className="px-4 py-3">Email</th><th className="px-4 py-3">Mobile</th><th className="px-4 py-3">Details</th><th className="px-4 py-3">Actions</th></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {records.map((record) => <tr key={record._id} className="align-top hover:bg-slate-50">
                <td className="max-w-32 truncate px-4 py-3 font-mono text-xs text-slate-500" title={record._id}>{record._id}</td>
                <td className="max-w-48 break-words px-4 py-3 font-medium text-slate-800">{displayValue(record.name || record.title || record.trainingName)}</td>
                <td className="px-4 py-3">{displayValue(record.employeeId)}</td>
                <td className="max-w-48 break-all px-4 py-3">{displayValue(record.email)}</td>
                <td className="px-4 py-3">{displayValue(record.mobile)}</td>
                <td className="max-w-64 px-4 py-3 text-xs text-slate-500">{Object.keys(record).filter((key) => !["_id", "name", "title", "trainingName", "employeeId", "email", "mobile"].includes(key)).slice(0, 4).map((key) => `${key}: ${displayValue(record[key])}`).join(" · ")}</td>
                <td className="px-4 py-3"><div className="flex gap-1"><button title="Edit record" onClick={() => openEdit(record)} className="rounded-lg p-2 text-indigo-600 hover:bg-indigo-50"><Pencil size={16}/></button><button title="Delete record" onClick={() => remove(record)} className="rounded-lg p-2 text-red-600 hover:bg-red-50"><Trash2 size={16}/></button></div></td>
              </tr>)}
              {!records.length && <tr><td colSpan={7} className="px-4 py-12 text-center text-sm text-slate-500">{busy ? "Loading records…" : "No records found in this collection."}</td></tr>}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-xs text-slate-500">Showing {records.length} records · {currentCollection?.count ?? 0} total in collection</p>
      </section>
    </div>);
}
