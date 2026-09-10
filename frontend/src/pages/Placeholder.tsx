export default function Placeholder({ title }: { title: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
      <p className="text-sm font-medium text-indigo-600">Module</p>
      <h1 className="mt-1 text-2xl font-bold">{title}</h1>
      <p className="mt-3 text-sm text-slate-500">This module is scaffolded and ready for the next implementation phase.</p>
    </div>
  );
}
