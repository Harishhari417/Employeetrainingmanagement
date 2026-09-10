
import { useEffect, useState } from "react";
import { CheckCircle2 } from "lucide-react";

import { api } from "../services/api";

type Evaluation = {
  _id: string;
  employeeId: string;
  employeeName: string;
  department: string;
  trainingTitle: string;
  dueDate: string;
  status: string;
  requiredLevel?: number;
  earlierLevel?: number;
  presentLevel?: number;
  suggestions?: string;
};

type LevelField =
  | "requiredLevel"
  | "earlierLevel"
  | "presentLevel";

export default function Evaluations() {
  const [rows, setRows] = useState<Evaluation[]>([]);
  const [message, setMessage] = useState("");

  async function load() {
    try {
      const response = await api.get<Evaluation[]>("/evaluations");
      setRows(response.data);
    } catch {
      setRows([]);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function update(
    id: string,
    field: LevelField | "suggestions" | "status",
    value: number | string,
  ) {
    try {
      await api.put(`/evaluations/${id}`, {
        [field]: value,
      });

      await load();

      setMessage("Evaluation saved.");

      window.setTimeout(() => {
        setMessage("");
      }, 2500);
    } catch {
      setMessage("Unable to save evaluation.");

      window.setTimeout(() => {
        setMessage("");
      }, 2500);
    }
  }

  return (
    <div className="space-y-6">
      {/* Page heading */}
      <div>
        <p className="text-sm font-medium text-indigo-600">
          3-Month Effectiveness
        </p>

        <h1 className="mt-1 text-2xl font-bold sm:text-3xl">
          Training Effectiveness Evaluation
        </h1>

        <p className="mt-2 text-sm text-slate-500">
          Evaluate required, earlier and present competency levels
          after training.
        </p>
      </div>

      {/* Success / error message */}
      {message && (
        <div className="flex items-center gap-2 rounded-xl bg-emerald-50 p-4 text-sm font-medium text-emerald-700">
          <CheckCircle2 size={18} />
          {message}
        </div>
      )}

      {/* Evaluation table */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-[1100px] w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                {[
                  "Employee",
                  "Department",
                  "Training",
                  "Due date",
                  "Required",
                  "Earlier",
                  "Present",
                  "Suggestions",
                  "Status",
                ].map((heading) => (
                  <th
                    key={heading}
                    className="p-4 text-left font-semibold text-slate-600"
                  >
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>

            <tbody>
              {rows.length === 0 ? (
                <tr>
                  <td
                    colSpan={9}
                    className="p-10 text-center text-sm text-slate-500"
                  >
                    No evaluations available.
                  </td>
                </tr>
              ) : (
                rows.map((row) => (
                  <tr
                    key={row._id}
                    className="border-t border-slate-100"
                  >
                    {/* Employee */}
                    <td className="p-4 font-semibold">
                      {row.employeeName}

                      <div className="text-xs font-normal text-slate-500">
                        {row.employeeId}
                      </div>
                    </td>

                    {/* Department */}
                    <td className="p-4">
                      {row.department}
                    </td>

                    {/* Training */}
                    <td className="p-4">
                      {row.trainingTitle}
                    </td>

                    {/* Due date */}
                    <td className="p-4">
                      {row.dueDate
                        ? new Date(row.dueDate).toLocaleDateString()
                        : "—"}
                    </td>

                    {/* Competency levels */}
                    {(
                      [
                        "requiredLevel",
                        "earlierLevel",
                        "presentLevel",
                      ] as LevelField[]
                    ).map((field) => (
                      <td
                        key={field}
                        className="p-4"
                      >
                        <select
                          value={row[field] ?? ""}
                          onChange={(event) => {
                            const value = event.target.value;

                            if (!value) {
                              return;
                            }

                            void update(
                              row._id,
                              field,
                              Number(value),
                            );
                          }}
                          className="w-16 rounded-lg border border-slate-200 px-2 py-2 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                        >
                          <option value="">—</option>

                          {[1, 2, 3, 4, 5].map((level) => (
                            <option
                              key={level}
                              value={level}
                            >
                              {level}
                            </option>
                          ))}
                        </select>
                      </td>
                    ))}

                    {/* Suggestions */}
                    <td className="p-4">
                      <input
                        defaultValue={row.suggestions ?? ""}
                        onBlur={(event) => {
                          void update(
                            row._id,
                            "suggestions",
                            event.target.value,
                          );
                        }}
                        placeholder="Suggestion"
                        className="w-44 rounded-lg border border-slate-200 px-3 py-2 outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                      />
                    </td>

                    {/* Status */}
                    <td className="p-4">
                      <button
                        type="button"
                        onClick={() => {
                          void update(
                            row._id,
                            "status",
                            "Completed",
                          );
                        }}
                        className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ${
                          row.status === "Completed"
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-amber-50 text-amber-700"
                        }`}
                      >
                        {row.status}

                        <CheckCircle2 size={13} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
