import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend, } from "recharts";
import { RefreshCw, GraduationCap, Clock3, MessageSquareText, CheckCircle2, ClipboardCheck, ClipboardList, } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { api } from "../services/api";
type MonthlyTraining = {
    month: string;
    count: number;
};
type Stats = {
    totalTrainings: number;
    completedTrainings: number;
    totalTrainingHours: number;
    attendancePercentage: number;
    feedbackCompleted: number;
    pendingFeedback: number;
    pendingEvaluations: number;
    evaluationCompleted: number;
    trainingTypes: {
        type: string;
        count: number;
    }[];
    monthlyTrainingHours?: {
        month: string;
        hours: number;
    }[];
    monthlyTrainings?: MonthlyTraining[];
    attendanceCounts?: Record<string, number>;
    feedbackCounts?: Record<string, number>;
};
const empty: Stats = {
    totalTrainings: 0,
    completedTrainings: 0,
    totalTrainingHours: 0,
    attendancePercentage: 0,
    feedbackCompleted: 0,
    pendingFeedback: 0,
    pendingEvaluations: 0,
    evaluationCompleted: 0,
    trainingTypes: [],
    monthlyTrainingHours: [],
    monthlyTrainings: [],
    attendanceCounts: {},
    feedbackCounts: {},
};
const colors = ["#16a34a", "#f59e0b", "#6366f1", "#ef4444", "#0ea5e9"];
function PiePanel({ title, data, }: {
    title: string;
    data: {
        name: string;
        value: number;
    }[];
}) {
    const safe = data.filter((item) => item.value > 0);
    return (<section className="min-w-0 overflow-hidden rounded-2xl border bg-white p-4 shadow-sm sm:p-5">
      <h2 className="break-words text-base font-semibold">{title}</h2>
      <div className="mt-3 h-[310px] min-w-0">
        {safe.length ? (<ResponsiveContainer width="100%" height="100%">
            <PieChart margin={{ top: 12, right: 12, bottom: 28, left: 12 }}>
              <Pie data={safe} dataKey="value" nameKey="name" cx="50%" cy="43%" outerRadius="65%" label={false}>
                {safe.map((item, index) => (<Cell key={item.name} fill={colors[index % colors.length]}/>))}
              </Pie>
              <Tooltip />
              <Legend verticalAlign="bottom" align="center" wrapperStyle={{ fontSize: 12, paddingTop: 14 }}/>
            </PieChart>
          </ResponsiveContainer>) : (<div className="flex h-full items-center justify-center text-sm text-slate-500">
            No records for this period
          </div>)}
      </div>
    </section>);
}
export default function Dashboard() {
    const { user } = useAuth();
    const [stats, setStats] = useState<Stats>(empty);
    const [fromDate, setFromDate] = useState("");
    const [toDate, setToDate] = useState("");
    const [year, setYear] = useState(String(new Date().getFullYear()));
    const [refreshing, setRefreshing] = useState(false);
    const load = async () => {
        setRefreshing(true);
        try {
            const params = new URLSearchParams();
            if (fromDate)
                params.set("startDate", fromDate);
            if (toDate)
                params.set("endDate", toDate);
            params.set("year", year);
            const response = await api.get<Stats>(`/dashboard?${params.toString()}`);
            setStats({ ...empty, ...response.data });
        }
        finally {
            setRefreshing(false);
        }
    };
    useEffect(() => {
        load().catch(() => undefined);
    }, [year, fromDate, toDate]);
    const monthlyTrainings = (stats.monthlyTrainings || []).length
        ? stats.monthlyTrainings || []
        : (stats.monthlyTrainingHours || []).map((item) => ({
            month: item.month,
            count: 0,
        }));
    const feedbackPie = [
        { name: "Completed", value: stats.feedbackCompleted },
        { name: "Pending", value: stats.pendingFeedback },
    ];
    const cards = [
        { label: "Total Training", value: stats.totalTrainings, Icon: GraduationCap },
        { label: "Total Training Hours", value: stats.totalTrainingHours, Icon: Clock3 },
        { label: "Feedback Pending", value: stats.pendingFeedback, Icon: MessageSquareText },
        { label: "Feedback Completed", value: stats.feedbackCompleted, Icon: CheckCircle2 },
        { label: "Effectiveness Pending", value: stats.pendingEvaluations, Icon: ClipboardList },
        { label: "Effectiveness Completed", value: stats.evaluationCompleted, Icon: CheckCircle2 },
        { label: "Attendance Percentage", value: `${stats.attendancePercentage}%`, Icon: ClipboardCheck },
    ];
    return (<div className="space-y-6">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div className="min-w-0">
          <p className="text-sm font-medium text-indigo-600">
            {user?.role.replace("_", " / ")}
          </p>
          <h1 className="mt-1 text-2xl font-bold sm:text-3xl">
            Training Dashboard
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Training, feedback, attendance and effectiveness overview.
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-2">
          <label className="text-xs font-medium text-slate-600">
            Year
            <select value={year} onChange={(event) => setYear(event.target.value)} className="mt-1 block w-full rounded-lg border bg-white px-2 py-2 text-sm">
              {Array.from({ length: 10 }, (_, index) => String(new Date().getFullYear() - index)).map((item) => (<option key={item} value={item}>
                  {item}
                </option>))}
            </select>
          </label>
          <label className="text-xs font-medium text-slate-600">
            From
            <input type="date" value={fromDate} onChange={(event) => setFromDate(event.target.value)} className="mt-1 block w-full rounded-lg border bg-white px-2 py-2 text-sm"/>
          </label>
          <label className="text-xs font-medium text-slate-600">
            To
            <input type="date" value={toDate} onChange={(event) => setToDate(event.target.value)} className="mt-1 block w-full rounded-lg border bg-white px-2 py-2 text-sm"/>
          </label>
          <button onClick={() => load().catch(() => undefined)} className="inline-flex items-center gap-2 rounded-xl border bg-white px-3 py-2.5 text-sm font-semibold">
            <RefreshCw size={15} className={refreshing ? "animate-spin" : ""}/>
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 2xl:grid-cols-4">
        {cards.map(({ label, value, Icon }) => (<div key={label} className="min-w-0 rounded-2xl border bg-white p-4 shadow-sm sm:p-5">
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs font-medium text-slate-500 sm:text-sm">{label}</p>
              <Icon size={18} className="shrink-0 text-indigo-600"/>
            </div>
            <p className="mt-3 break-words text-2xl font-bold text-slate-900">{value}</p>
          </div>))}
      </div>

      <div className="grid min-w-0 gap-5 xl:grid-cols-3">
        <section className="min-w-0 overflow-hidden rounded-2xl border bg-white p-4 shadow-sm sm:p-5 xl:col-span-1">
          <div className="mb-3">
            <h2 className="text-base font-semibold">Monthly Trainings</h2>
            <p className="mt-1 text-xs text-slate-500">Number of trainings scheduled in {year}</p>
          </div>
          <div className="h-[330px] min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyTrainings} margin={{ top: 12, right: 8, left: -18, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false}/>
                <XAxis dataKey="month" tick={{ fontSize: 11 }} interval={0}/>
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }}/>
                <Tooltip />
                <Bar dataKey="count" name="Trainings" fill="#6366f1" radius={[5, 5, 0, 0]}/>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
        <PiePanel title="Feedback Status" data={feedbackPie}/>
        <PiePanel title="Evaluation Status" data={[
            { name: "Completed", value: stats.evaluationCompleted },
            { name: "Pending", value: stats.pendingEvaluations },
        ]}/>
      </div>
    </div>);
}
