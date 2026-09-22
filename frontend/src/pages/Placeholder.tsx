export default function Placeholder({ title }: { title: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
      <div className="flex items-center gap-4">
        <img
          src="/EVIG-Intergration_horizantal_Logo_1500-1.png"
          alt="Company Logo"
          className="h-14 w-14 object-contain"
        />

        <div>
          <p className="text-sm font-medium text-indigo-600">Module</p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">{title}</h1>
        </div>
      </div>

      <p className="mt-4 text-sm text-slate-500">
        This module is scaffolded and ready for the next implementation phase.
      </p>
    </div>
  );
}