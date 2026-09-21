
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Edit3, Plus, Search, Trash2, UserCheck, UserX } from "lucide-react";
import { api } from "../services/api";

type Employee = {
  _id?: string;
  employeeId: string;
  name: string;
  department: string;
  designation: string;
  reportingManager?: string;
  email?: string;
  status: string;
};

type Department = {
  _id: string;
  name: string;
  status: string;
};

type EmployeeForm = {
  employeeId: string;
  name: string;
  department: string;
  designation: string;
  reportingManager: string;
  email: string;
  status: string;
  password: string;
};

const emptyForm: EmployeeForm = {
  employeeId: "",
  name: "",
  department: "",
  designation: "",
  reportingManager: "",
  email: "",
  status: "Active",
  password: "",
};

export default function Employees() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState<Employee | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState<EmployeeForm>(emptyForm);

  const loadData = async () => {
    try {
      setError("");

      const [employeeResponse, departmentResponse] = await Promise.all([
        api.get("/employees"),
        api.get("/departments"),
      ]);

      const employeeData =
        employeeResponse.data?.employees ??
        employeeResponse.data ??
        [];

      const departmentData =
        departmentResponse.data?.departments ??
        departmentResponse.data ??
        [];

      setEmployees(Array.isArray(employeeData) ? employeeData : []);
      setDepartments(Array.isArray(departmentData) ? departmentData : []);
    } catch (err: any) {
      setError(
        err?.response?.data?.message ||
          err?.response?.data?.error ||
          "Unable to load employees."
      );
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredEmployees = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) return employees;

    return employees.filter((employee) =>
      `${employee.employeeId} ${employee.name} ${employee.department} ${employee.designation} ${employee.reportingManager || ""} ${employee.email || ""}`
        .toLowerCase()
        .includes(value)
    );
  }, [employees, search]);

  const openAdd = () => {
    setEditingEmployee(null);

    const firstDepartment = departments.find(
      (department) => department.status !== "Inactive"
    );

    setForm({
      ...emptyForm,
      department: firstDepartment?.name || "",
    });

    setError("");
    setShowModal(true);
  };

  const openEdit = (employee: Employee) => {
    setEditingEmployee(employee);

    setForm({
      employeeId: employee.employeeId || "",
      name: employee.name || "",
      department: employee.department || "",
      designation: employee.designation || "",
      reportingManager: employee.reportingManager || "",
      email: employee.email || "",
      status: employee.status || "Active",
      password: "",
    });

    setError("");
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingEmployee(null);
    setForm(emptyForm);
    setError("");
  };

  const saveEmployee = async (event: FormEvent) => {
    event.preventDefault();

    if (!form.employeeId.trim()) {
      setError("Employee ID is required.");
      return;
    }

    if (!form.name.trim()) {
      setError("Employee name is required.");
      return;
    }

    if (!form.department) {
      setError("Please select a department.");
      return;
    }

    if (!form.designation.trim()) {
      setError("Designation is required.");
      return;
    }

    if (!editingEmployee && !form.password.trim()) {
      setError("Initial password is required.");
      return;
    }

    try {
      setSaving(true);
      setError("");

      if (editingEmployee?._id) {
        const payload: any = {
          employeeId: form.employeeId.trim(),
          name: form.name.trim(),
          department: form.department,
          designation: form.designation.trim(),
          reportingManager: form.reportingManager.trim(),
          email: form.email.trim(),
          status: form.status,
        };

        if (form.password.trim()) {
          payload.password = form.password.trim();
        }

        await api.put(
          `/employees/${editingEmployee._id}`,
          payload
        );
      } else {
        await api.post("/employees", {
          employeeId: form.employeeId.trim(),
          name: form.name.trim(),
          department: form.department,
          designation: form.designation.trim(),
          reportingManager: form.reportingManager.trim(),
          email: form.email.trim(),
          status: form.status,
          password: form.password.trim(),
        });
      }

      closeModal();
      await loadData();
    } catch (err: any) {
      setError(
        err?.response?.data?.message ||
          err?.response?.data?.error ||
          `Unable to ${editingEmployee ? "update" : "create"} employee.`
      );
    } finally {
      setSaving(false);
    }
  };

  const changeStatus = async (employee: Employee) => {
    if (!employee._id) return;

    const active = employee.status === "Active";
    const newStatus = active ? "Inactive" : "Active";

    const confirmed = window.confirm(
      `${active ? "Deactivate" : "Activate"} ${employee.name} (${employee.employeeId})?`
    );

    if (!confirmed) return;

    try {
      setError("");

      await api.put(
        `/employees/${employee._id}/status`,
        { status: newStatus }
      );

      await loadData();
    } catch (err: any) {
      setError(
        err?.response?.data?.message ||
          err?.response?.data?.error ||
          "Unable to change employee status."
      );
    }
  };

  const deleteEmployee = async (employee: Employee) => {
    if (!employee._id) return;

    const confirmed = window.confirm(
      `Delete ${employee.name} (${employee.employeeId}) permanently?`
    );

    if (!confirmed) return;

    try {
      setError("");

      await api.delete(`/employees/${employee._id}`);

      await loadData();
    } catch (err: any) {
      setError(
        err?.response?.data?.message ||
          err?.response?.data?.error ||
          "Unable to delete employee."
      );
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-indigo-600">
            HR / Admin
          </p>

          <h1 className="mt-1 text-2xl font-bold sm:text-3xl">
            Employee Management
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Manage employees, departments, reporting managers and status.
          </p>
        </div>

        <button
          type="button"
          onClick={openAdd}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-3 text-sm font-semibold text-white hover:bg-indigo-700"
        >
          <Plus size={18} />
          Add Employee
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {error}
        </div>
      )}

      <div className="relative">
        <Search
          size={18}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
        />

        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search employee ID, name, department, designation..."
          className="w-full rounded-xl border border-slate-200 bg-white py-3 pl-10 pr-4 text-sm outline-none focus:border-indigo-500"
        />
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-[1200px] w-full text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="p-4 text-left font-semibold text-slate-600">
                  Employee ID
                </th>
                <th className="p-4 text-left font-semibold text-slate-600">
                  Name
                </th>
                <th className="p-4 text-left font-semibold text-slate-600">
                  Department
                </th>
                <th className="p-4 text-left font-semibold text-slate-600">
                  Designation
                </th>
                <th className="p-4 text-left font-semibold text-slate-600">
                  Reporting Manager
                </th>
                <th className="p-4 text-left font-semibold text-slate-600">
                  Email
                </th>
                <th className="p-4 text-left font-semibold text-slate-600">
                  Status
                </th>
                <th className="p-4 text-left font-semibold text-slate-600">
                  Actions
                </th>
              </tr>
            </thead>

            <tbody>
              {filteredEmployees.length === 0 ? (
                <tr>
                  <td
                    colSpan={8}
                    className="p-10 text-center text-sm text-slate-500"
                  >
                    No employees found.
                  </td>
                </tr>
              ) : (
                filteredEmployees.map((employee) => {
                  const active = employee.status === "Active";

                  return (
                    <tr
                      key={employee._id || employee.employeeId}
                      className="border-t border-slate-100"
                    >
                      <td className="p-4 font-semibold text-slate-800">
                        {employee.employeeId}
                      </td>

                      <td className="p-4 text-slate-700">
                        {employee.name}
                      </td>

                      <td className="p-4 text-slate-700">
                        {employee.department}
                      </td>

                      <td className="p-4 text-slate-700">
                        {employee.designation}
                      </td>

                      <td className="p-4 text-slate-700">
                        {employee.reportingManager || "—"}
                      </td>

                      <td className="p-4 text-slate-700">
                        {employee.email || "—"}
                      </td>

                      <td className="p-4">
                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${
                            active
                              ? "bg-emerald-50 text-emerald-700"
                              : "bg-slate-100 text-slate-500"
                          }`}
                        >
                          {employee.status}
                        </span>
                      </td>

                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => openEdit(employee)}
                            title="Edit"
                            className="rounded-lg border border-slate-200 p-2 text-slate-600 hover:bg-slate-50"
                          >
                            <Edit3 size={16} />
                          </button>

                          <button
                            type="button"
                            onClick={() => changeStatus(employee)}
                            title={active ? "Deactivate" : "Activate"}
                            className={`rounded-lg border p-2 ${
                              active
                                ? "border-amber-200 text-amber-600 hover:bg-amber-50"
                                : "border-emerald-200 text-emerald-600 hover:bg-emerald-50"
                            }`}
                          >
                            {active ? (
                              <UserX size={16} />
                            ) : (
                              <UserCheck size={16} />
                            )}
                          </button>

                          <button
                            type="button"
                            onClick={() => deleteEmployee(employee)}
                            title="Delete"
                            className="rounded-lg border border-rose-200 p-2 text-rose-600 hover:bg-rose-50"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <form
            onSubmit={saveEmployee}
            className="max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl"
          >
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                {editingEmployee ? "Edit Employee" : "Add Employee"}
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                {editingEmployee
                  ? "Update employee information."
                  : "Create an employee and their initial login details."}
              </p>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1.5 block text-sm font-medium">
                  Employee ID
                </label>

                <input
                  required
                  value={form.employeeId}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      employeeId: event.target.value,
                    })
                  }
                  className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium">
                  Name
                </label>

                <input
                  required
                  value={form.name}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      name: event.target.value,
                    })
                  }
                  className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium">
                  Department
                </label>

                <select
                  required
                  value={form.department}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      department: event.target.value,
                    })
                  }
                  className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-indigo-500"
                >
                  <option value="">Select Department</option>

                  {departments
                    .filter(
                      (department) =>
                        department.status !== "Inactive"
                    )
                    .map((department) => (
                      <option
                        key={department._id}
                        value={department.name}
                      >
                        {department.name}
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium">
                  Designation
                </label>

                <input
                  required
                  value={form.designation}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      designation: event.target.value,
                    })
                  }
                  className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium">
                  Reporting Manager
                </label>

                <input
                  value={form.reportingManager}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      reportingManager: event.target.value,
                    })
                  }
                  className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium">
                  Email
                </label>

                <input
                  type="email"
                  value={form.email}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      email: event.target.value,
                    })
                  }
                  className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium">
                  Status
                </label>

                <select
                  value={form.status}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      status: event.target.value,
                    })
                  }
                  className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-indigo-500"
                >
                  <option value="Active">Active</option>
                  <option value="Inactive">Inactive</option>
                </select>
              </div>

              <div>
                <label className="mb-1.5 block text-sm font-medium">
                  {editingEmployee
                    ? "New Password (optional)"
                    : "Initial Password"}
                </label>

                <input
                  type="password"
                  required={!editingEmployee}
                  value={form.password}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      password: event.target.value,
                    })
                  }
                  className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={closeModal}
                className="rounded-xl border border-slate-200 px-5 py-2.5 text-sm font-semibold"
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={saving}
                className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
              >
                {saving
                  ? "Saving..."
                  : editingEmployee
                  ? "Update Employee"
                  : "Save Employee"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

