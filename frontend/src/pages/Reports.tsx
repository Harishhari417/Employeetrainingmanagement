import { BarChart3, Download, FileSpreadsheet, Users } from "lucide-react";
import { api } from "../services/api";
import { useAuth } from "../auth/AuthContext";

async function downloadReport(path: string, filename: string) {
  const response = await api.get(path, { responseType: "blob" });
  const url = URL.createObjectURL(response.data);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export default function Reports() {
  const { user } = useAuth();
  const isAdmin = user?.role === "HR_ADMIN";

  return <div className="space-y-6">
    <div>
      <p className="text-sm font-medium text-indigo-600">Reports</p>
      <h1 className="mt-1 text-2xl font-bold sm:text-3xl">Training Reports</h1>
      <p className="mt-2 text-sm text-slate-500">Export operational training data for review and management reporting.</p>
    </div>

    <div className="grid gap-5 md:grid-cols-2">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600"><BarChart3 size={22}/></div>
        <h2 className="mt-5 text-lg font-bold">Training report</h2>
        <p className="mt-2 text-sm leading-6 text-slate-500">Training title, trainer, date, venue, participant count, attendance and feedback response count.</p>
        <button onClick={()=>downloadReport("/reports/training","training-report.csv")} className="mt-5 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700"><Download size={17}/> Export CSV</button>
      </section>

      {isAdmin && <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600"><Users size={22}/></div>
        <h2 className="mt-5 text-lg font-bold">Employee training report</h2>
        <p className="mt-2 text-sm leading-6 text-slate-500">Employee, department, reporting manager, assigned training count and attendance percentage.</p>
        <button onClick={()=>downloadReport("/reports/employees","employee-training-report.csv")} className="mt-5 inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-700"><FileSpreadsheet size={17}/> Export CSV</button>
      </section>}
    </div>

    <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
      <strong>Reporting note:</strong> CSV exports are intended for the first reporting layer. The analytics dashboard remains the place for interactive trend analysis.
    </section>
  </div>;
}
