import { useEffect, useMemo, useState } from "react";
import {
  CalendarDays,
  CheckCircle2,
  Clock3,
  Eye,
  Filter,
  Plus,
  Search,
  UserPlus,
  Users,
  X,
} from "lucide-react";
import { api } from "../services/api";

type Training = {
  _id: string;
  title: string;
  content?: string;
  trainingType?: string;
  trainerName?: string;
  trainerEmployeeId?: string;
  trainerCategory?: string;
  venue?: string;
  trainingDate?: string;
  trainingMode?: string;
  durationMinutes?: number;
  status?: string;
  departments?: string[];
  traineeIds?: string[];
};

type Employee = {
  _id?: string;
  employeeId: string;
  name?: string;
  employeeName?: string;
  department?: string;
  designation?: string;
  status?: string;
  email?: string;
};

type AssignmentMode = "all" | "department" | "one" | "selected";

const fallbackDepartments = [
  "Production",
  "QA / Quality",
  "Store",
  "HR",
  "Maintenance",
  "Engineering / R&D",
  "Finance",
  "Purchase",
  "Sales",
  "Management",
  "Other",
];

const trainingTypes = [
  "Technical",
  "Behavioural",
  "Leadership",
];

const trainerCategories = [
  "Internal",
  "External",
];

const getEmployeeName = (employee: Employee) =>
  employee.name ||
  employee.employeeName ||
  employee.employeeId;

const isActiveEmployee = (employee: Employee) =>
  employee.status?.toLowerCase() !== "inactive";

const getTrainingStatus = (training: Training) => {
  if (training.status === "Completed") return "Completed";
  if (training.status === "Cancelled") return "Cancelled";

  if (!training.trainingDate) return "Upcoming";

  const date = new Date(training.trainingDate);
  const now = new Date();

  if (Number.isNaN(date.getTime())) return "Upcoming";

  if (date > now) return "Upcoming";

  return "Ongoing";
};

const formatDate = (date?: string) => {
  if (!date) return "Not specified";

  const parsed = new Date(date);

  if (Number.isNaN(parsed.getTime())) return date;

  return parsed.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
};

const formatDateTime = (date?: string) => {
  if (!date) return "Not specified";

  const parsed = new Date(date);

  if (Number.isNaN(parsed.getTime())) return date;

  return parsed.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export default function Trainings() {
  const [trainings, setTrainings] = useState<Training[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<string[]>(
    fallbackDepartments
  );

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState("All");

  const [showAdd, setShowAdd] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [showAssign, setShowAssign] = useState(false);

  const [selectedTraining, setSelectedTraining] =
    useState<Training | null>(null);

  const [assignmentMode, setAssignmentMode] =
    useState<AssignmentMode>("all");

  const [selectedDepartment, setSelectedDepartment] =
    useState("");

  const [selectedEmployeeId, setSelectedEmployeeId] =
    useState("");

  const [selectedEmployeeIds, setSelectedEmployeeIds] =
    useState<string[]>([]);

  const [employeeSearch, setEmployeeSearch] = useState("");

  const [trainerEmployeeId, setTrainerEmployeeId] =
    useState("");

  const [form, setForm] = useState({
    title: "",
    content: "",
    trainingType: "Technical",
    trainerName: "",
    trainerCategory: "Internal",
    venue: "",
    trainingDate: "",
    trainingMode: "Offline",
    durationMinutes: "",
    departments: [] as string[],
  });

  const activeEmployees = useMemo(
    () => employees.filter(isActiveEmployee),
    [employees]
  );

  const internalTrainers = useMemo(
    () =>
      activeEmployees.filter(
        (employee) =>
          employee.designation ||
          employee.department ||
          employee.name ||
          employee.employeeName
      ),
    [activeEmployees]
  );

  const filteredEmployeeOptions = useMemo(() => {
    const query = employeeSearch.trim().toLowerCase();

    return activeEmployees.filter((employee) => {
      if (!query) return true;

      const code = employee.employeeId?.toLowerCase() || "";
      const name = getEmployeeName(employee).toLowerCase();
      const department =
        employee.department?.toLowerCase() || "";
      const designation =
        employee.designation?.toLowerCase() || "";

      return (
        code.includes(query) ||
        name.includes(query) ||
        department.includes(query) ||
        designation.includes(query)
      );
    });
  }, [activeEmployees, employeeSearch]);

  const departmentEmployees = useMemo(() => {
    if (!selectedDepartment) return [];

    return activeEmployees.filter(
      (employee) =>
        employee.department?.trim().toLowerCase() ===
        selectedDepartment.trim().toLowerCase()
    );
  }, [activeEmployees, selectedDepartment]);

  const selectedEmployees = useMemo(
    () =>
      activeEmployees.filter((employee) =>
        selectedEmployeeIds.includes(employee.employeeId)
      ),
    [activeEmployees, selectedEmployeeIds]
  );

  const loadData = async () => {
    try {
      setLoading(true);

      const [
        trainingResponse,
        employeeResponse,
        departmentResponse,
      ] = await Promise.all([
        api.get("/trainings"),
        api.get("/employees"),
        api.get("/departments"),
      ]);

      const trainingData =
        trainingResponse.data?.trainings ??
        trainingResponse.data ??
        [];

      const employeeData =
        employeeResponse.data?.employees ??
        employeeResponse.data ??
        [];

      const departmentData =
        departmentResponse.data?.departments ??
        departmentResponse.data ??
        [];

      setTrainings(
        Array.isArray(trainingData)
          ? trainingData
          : []
      );

      setEmployees(
        Array.isArray(employeeData)
          ? employeeData
          : []
      );

      if (Array.isArray(departmentData)) {
        const names = departmentData
          .map((item: any) => {
            if (typeof item === "string") return item;

            return (
              item?.name ||
              item?.departmentName ||
              item?.title ||
              ""
            );
          })
          .filter(Boolean);

        if (names.length > 0) {
          setDepartments(names);
        }
      }
    } catch (error) {
      console.error(
        "Failed to load training data",
        error
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredTrainings = useMemo(() => {
    const query = search.trim().toLowerCase();

    return trainings.filter((training) => {
      const status = getTrainingStatus(training);

      const matchesSearch =
        !query ||
        training.title?.toLowerCase().includes(query) ||
        training.trainerName
          ?.toLowerCase()
          .includes(query) ||
        training.trainingType
          ?.toLowerCase()
          .includes(query);

      const matchesType =
        typeFilter === "All" ||
        training.trainingType === typeFilter;

      const matchesStatus =
        statusFilter === "All" ||
        status === statusFilter;

      return (
        matchesSearch &&
        matchesType &&
        matchesStatus
      );
    });
  }, [
    trainings,
    search,
    typeFilter,
    statusFilter,
  ]);

  const counts = useMemo(() => {
    const result = {
      total: trainings.length,
      ongoing: 0,
      upcoming: 0,
      completed: 0,
      cancelled: 0,
    };

    trainings.forEach((training) => {
      const status = getTrainingStatus(training);

      if (status === "Ongoing") result.ongoing++;
      if (status === "Upcoming") result.upcoming++;
      if (status === "Completed") result.completed++;
      if (status === "Cancelled") result.cancelled++;
    });

    return result;
  }, [trainings]);

  const resetForm = () => {
    setForm({
      title: "",
      content: "",
      trainingType: "Technical",
      trainerName: "",
      trainerCategory: "Internal",
      venue: "",
      trainingDate: "",
      trainingMode: "Offline",
      durationMinutes: "",
      departments: [],
    });

    setAssignmentMode("all");
    setSelectedDepartment("");
    setSelectedEmployeeId("");
    setSelectedEmployeeIds([]);
    setEmployeeSearch("");
    setTrainerEmployeeId("");
  };

  const closeAddModal = () => {
    if (saving) return;

    setShowAdd(false);
    resetForm();
  };

  const closeAssignModal = () => {
    if (saving) return;

    setShowAssign(false);
    setSelectedTraining(null);
    setAssignmentMode("all");
    setSelectedDepartment("");
    setSelectedEmployeeId("");
    setSelectedEmployeeIds([]);
    setEmployeeSearch("");
  };

  const handleTrainerChange = (
    employeeId: string
  ) => {
    setTrainerEmployeeId(employeeId);

    const trainer = activeEmployees.find(
      (employee) =>
        employee.employeeId === employeeId
    );

    if (!trainer) {
      setForm((previous) => ({
        ...previous,
        trainerName: "",
      }));

      return;
    }

    setForm((previous) => ({
      ...previous,
      trainerName: getEmployeeName(trainer),
    }));
  };

  const getAssignmentEmployeeIds = () => {
    if (assignmentMode === "all") {
      return activeEmployees.map(
        (employee) => employee.employeeId
      );
    }

    if (assignmentMode === "department") {
      if (!selectedDepartment) {
        alert("Please select a department.");
        return null;
      }

      const ids = departmentEmployees.map(
        (employee) => employee.employeeId
      );

      if (ids.length === 0) {
        alert(
          "No active employees found in the selected department."
        );
        return null;
      }

      return ids;
    }

    if (assignmentMode === "one") {
      if (!selectedEmployeeId) {
        alert("Please select an employee.");
        return null;
      }

      return [selectedEmployeeId];
    }

    if (assignmentMode === "selected") {
      if (selectedEmployeeIds.length === 0) {
        alert("Please select at least one employee.");
        return null;
      }

      return selectedEmployeeIds;
    }

    return null;
  };

  const createTraining = async () => {
    if (saving) return;

    if (!form.title.trim()) {
      alert("Please enter training title.");
      return;
    }

    if (!form.trainingDate) {
      alert("Please select training date.");
      return;
    }

    if (
      form.trainerCategory === "Internal" &&
      !trainerEmployeeId
    ) {
      alert("Please select an internal trainer.");
      return;
    }

    if (
      form.trainerCategory === "External" &&
      !form.trainerName.trim()
    ) {
      alert("Please enter external trainer name.");
      return;
    }

    const traineeIds =
      getAssignmentEmployeeIds();

    if (!traineeIds) return;

    try {
      setSaving(true);

      const response = await api.post(
        "/trainings",
        {
          title: form.title.trim(),
          content: form.content.trim(),
          trainingType: form.trainingType,
          trainerName: form.trainerName.trim(),
          trainerEmployeeId:
            form.trainerCategory === "Internal"
              ? trainerEmployeeId
              : "",
          trainerCategory:
            form.trainerCategory,
          venue: form.venue.trim(),
          trainingDate: form.trainingDate,
          trainingMode: form.trainingMode,
          durationMinutes: Number(
            form.durationMinutes || 0
          ),
          departments: form.departments,
          traineeIds: [],
        }
      );

      const training =
        response.data?.training ??
        response.data;

      const trainingId =
        training?._id ??
        training?.trainingId;

      if (!trainingId) {
        throw new Error(
          "Training was created but training ID was not returned."
        );
      }

      await api.put(
        `/trainings/${trainingId}/participants`,
        {
          employeeIds: traineeIds,
        }
      );

      await loadData();

      closeAddModal();
    } catch (error: any) {
      console.error(
        "Failed to create training",
        error
      );

      alert(
        error?.response?.data?.message ||
          error?.response?.data?.error ||
          "Failed to create training."
      );
    } finally {
      setSaving(false);
    }
  };

  const assignTraining = async () => {
    if (saving || !selectedTraining?._id) {
      return;
    }

    const traineeIds =
      getAssignmentEmployeeIds();

    if (!traineeIds) return;

    try {
      setSaving(true);

      await api.put(
        `/trainings/${selectedTraining._id}/participants`,
        {
          employeeIds: traineeIds,
        }
      );

      await loadData();

      closeAssignModal();
    } catch (error: any) {
      console.error(
        "Failed to assign training",
        error
      );

      alert(
        error?.response?.data?.message ||
          error?.response?.data?.error ||
          "Failed to assign training."
      );
    } finally {
      setSaving(false);
    }
  };

  const markCompleted = async (
    training: Training
  ) => {
    if (!training._id) return;

    if (
      !window.confirm(
        "Mark this training as completed?"
      )
    ) {
      return;
    }

    try {
      setSaving(true);

      await api.post(
        `/trainings/${training._id}/complete`
      );

      await loadData();
    } catch (error: any) {
      console.error(
        "Failed to complete training",
        error
      );

      alert(
        error?.response?.data?.message ||
          error?.response?.data?.error ||
          "Failed to mark training as completed."
      );
    } finally {
      setSaving(false);
    }
  };

  const toggleDepartment = (
    department: string
  ) => {
    setForm((previous) => ({
      ...previous,
      departments:
        previous.departments.includes(department)
          ? previous.departments.filter(
              (item) => item !== department
            )
          : [
              ...previous.departments,
              department,
            ],
    }));
  };

  const toggleEmployee = (
    employeeId: string
  ) => {
    setSelectedEmployeeIds((previous) =>
      previous.includes(employeeId)
        ? previous.filter(
            (id) => id !== employeeId
          )
        : [...previous, employeeId]
    );
  };

  const selectAllFilteredEmployees = () => {
    const ids = filteredEmployeeOptions.map(
      (employee) => employee.employeeId
    );

    setSelectedEmployeeIds((previous) => [
      ...new Set([...previous, ...ids]),
    ]);
  };

  const clearSelectedEmployees = () => {
    setSelectedEmployeeIds([]);
  };

  const openDetails = (
    training: Training
  ) => {
    setSelectedTraining(training);
    setShowDetails(true);
  };

  const openAssign = (
    training: Training
  ) => {
    setSelectedTraining(training);
    setAssignmentMode("all");
    setSelectedDepartment("");
    setSelectedEmployeeId("");
    setSelectedEmployeeIds([]);
    setEmployeeSearch("");
    setShowAssign(true);
  };

  const getTraineeEmployees = (
    training: Training
  ) => {
    if (!training.traineeIds?.length) {
      return [];
    }

    return employees.filter((employee) =>
      training.traineeIds?.includes(
        employee.employeeId
      )
    );
  };

  const renderAssignmentSelector = (
    isAddModal: boolean
  ) => {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => {
              setAssignmentMode("all");
              setSelectedDepartment("");
              setSelectedEmployeeId("");
              setSelectedEmployeeIds([]);
            }}
            className={`rounded-xl border p-4 text-left transition ${
              assignmentMode === "all"
                ? "border-blue-600 bg-blue-50 ring-1 ring-blue-600"
                : "hover:bg-gray-50"
            }`}
          >
            <div className="flex items-center gap-2">
              <Users
                size={18}
                className="text-blue-600"
              />
              <p className="font-semibold text-gray-900">
                All Employees
              </p>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Assign this training to every active employee.
            </p>
            <p className="mt-2 text-xs font-semibold text-blue-600">
              {activeEmployees.length} active employees
            </p>
          </button>

          <button
            type="button"
            onClick={() => {
              setAssignmentMode(
                "department"
              );
              setSelectedEmployeeId("");
              setSelectedEmployeeIds([]);
            }}
            className={`rounded-xl border p-4 text-left transition ${
              assignmentMode ===
              "department"
                ? "border-blue-600 bg-blue-50 ring-1 ring-blue-600"
                : "hover:bg-gray-50"
            }`}
          >
            <div className="flex items-center gap-2">
              <Users
                size={18}
                className="text-blue-600"
              />
              <p className="font-semibold text-gray-900">
                Department
              </p>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Assign the training to all active employees in one department.
            </p>
          </button>

          <button
            type="button"
            onClick={() => {
              setAssignmentMode("one");
              setSelectedDepartment("");
              setSelectedEmployeeIds([]);
            }}
            className={`rounded-xl border p-4 text-left transition ${
              assignmentMode === "one"
                ? "border-blue-600 bg-blue-50 ring-1 ring-blue-600"
                : "hover:bg-gray-50"
            }`}
          >
            <div className="flex items-center gap-2">
              <UserPlus
                size={18}
                className="text-blue-600"
              />
              <p className="font-semibold text-gray-900">
                One-to-One
              </p>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Assign the training to one employee.
            </p>
          </button>

          <button
            type="button"
            onClick={() => {
              setAssignmentMode(
                "selected"
              );
              setSelectedDepartment("");
              setSelectedEmployeeId("");
            }}
            className={`rounded-xl border p-4 text-left transition ${
              assignmentMode ===
              "selected"
                ? "border-blue-600 bg-blue-50 ring-1 ring-blue-600"
                : "hover:bg-gray-50"
            }`}
          >
            <div className="flex items-center gap-2">
              <Users
                size={18}
                className="text-blue-600"
              />
              <p className="font-semibold text-gray-900">
                Custom Employees
              </p>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              Select any number of active employees.
            </p>
          </button>
        </div>

        {assignmentMode ===
          "all" && (
          <div className="rounded-xl border border-blue-100 bg-blue-50 p-4">
            <p className="text-sm font-semibold text-blue-900">
              All active employees will be assigned
            </p>
            <p className="mt-1 text-xs text-blue-700">
              {activeEmployees.length} employees will receive this training.
            </p>
          </div>
        )}

        {assignmentMode ===
          "department" && (
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Select Department
              </label>

              <select
                value={
                  selectedDepartment
                }
                onChange={(e) => {
                  setSelectedDepartment(
                    e.target.value
                  );
                  setEmployeeSearch("");
                }}
                className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-blue-500"
              >
                <option value="">
                  Select Department
                </option>

                {departments.map(
                  (department) => (
                    <option
                      key={department}
                      value={department}
                    >
                      {department}
                    </option>
                  )
                )}
              </select>
            </div>

            {selectedDepartment && (
              <div className="rounded-xl border bg-gray-50 p-4">
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">
                      Employees in{" "}
                      {selectedDepartment}
                    </p>
                    <p className="text-xs text-gray-500">
                      Only active employees from this department are included.
                    </p>
                  </div>

                  <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700">
                    {
                      departmentEmployees.length
                    }{" "}
                    employees
                  </span>
                </div>

                <div className="mt-3 max-h-52 overflow-y-auto rounded-lg border bg-white">
                  {departmentEmployees.length ===
                  0 ? (
                    <p className="p-4 text-sm text-gray-500">
                      No active employees found in this department.
                    </p>
                  ) : (
                    departmentEmployees.map(
                      (employee) => (
                        <div
                          key={
                            employee.employeeId
                          }
                          className="flex items-center justify-between border-b p-3 last:border-b-0"
                        >
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {
                                getEmployeeName(
                                  employee
                                )
                              }
                            </p>
                            <p className="text-xs text-gray-500">
                              {
                                employee.employeeId
                              }
                              {employee.designation
                                ? ` • ${employee.designation}`
                                : ""}
                            </p>
                          </div>
                        </div>
                      )
                    )
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {assignmentMode ===
          "one" && (
          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Search Employee
              </label>

              <div className="relative">
                <Search
                  size={17}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                />

                <input
                  value={
                    employeeSearch
                  }
                  onChange={(e) =>
                    setEmployeeSearch(
                      e.target.value
                    )
                  }
                  placeholder="Search employee code, name or department"
                  className="w-full rounded-lg border py-2.5 pl-10 pr-3 text-sm outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Select Employee
              </label>

              <select
                value={
                  selectedEmployeeId
                }
                onChange={(e) =>
                  setSelectedEmployeeId(
                    e.target.value
                  )
                }
                className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-blue-500"
              >
                <option value="">
                  Select Employee
                </option>

                {filteredEmployeeOptions.map(
                  (employee) => (
                    <option
                      key={
                        employee.employeeId
                      }
                      value={
                        employee.employeeId
                      }
                    >
                      {
                        employee.employeeId
                      }{" "}
                      -{" "}
                      {
                        getEmployeeName(
                          employee
                        )
                      }
                      {employee.department
                        ? ` - ${employee.department}`
                        : ""}
                    </option>
                  )
                )}
              </select>
            </div>

            {selectedEmployeeId && (
              <div className="rounded-lg border border-blue-100 bg-blue-50 p-3">
                {(() => {
                  const employee =
                    activeEmployees.find(
                      (item) =>
                        item.employeeId ===
                        selectedEmployeeId
                    );

                  if (!employee)
                    return null;

                  return (
                    <div>
                      <p className="text-sm font-semibold text-blue-900">
                        {
                          getEmployeeName(
                            employee
                          )
                        }
                      </p>
                      <p className="mt-1 text-xs text-blue-700">
                        {
                          employee.employeeId
                        }
                        {employee.department
                          ? ` • ${employee.department}`
                          : ""}
                        {employee.designation
                          ? ` • ${employee.designation}`
                          : ""}
                      </p>
                    </div>
                  );
                })()}
              </div>
            )}
          </div>
        )}

        {assignmentMode ===
          "selected" && (
          <div className="space-y-3">
            <div className="flex flex-col gap-3 sm:flex-row">
              <div className="relative flex-1">
                <Search
                  size={17}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                />

                <input
                  value={
                    employeeSearch
                  }
                  onChange={(e) =>
                    setEmployeeSearch(
                      e.target.value
                    )
                  }
                  placeholder="Search by employee code, name, department..."
                  className="w-full rounded-lg border py-2.5 pl-10 pr-3 text-sm outline-none focus:border-blue-500"
                />
              </div>

              <button
                type="button"
                onClick={
                  selectAllFilteredEmployees
                }
                className="rounded-lg border px-3 py-2.5 text-sm font-medium hover:bg-gray-50"
              >
                Select Visible
              </button>

              <button
                type="button"
                onClick={
                  clearSelectedEmployees
                }
                className="rounded-lg border px-3 py-2.5 text-sm font-medium hover:bg-gray-50"
              >
                Clear
              </button>
            </div>

            <div className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
              <p className="text-xs text-gray-600">
                Selected employees
              </p>

              <span className="rounded-full bg-blue-100 px-2.5 py-1 text-xs font-semibold text-blue-700">
                {
                  selectedEmployeeIds.length
                }
              </span>
            </div>

            <div className="max-h-72 overflow-y-auto rounded-lg border">
              {filteredEmployeeOptions.length ===
              0 ? (
                <p className="p-5 text-center text-sm text-gray-500">
                  No active employees found.
                </p>
              ) : (
                filteredEmployeeOptions.map(
                  (employee) => {
                    const checked =
                      selectedEmployeeIds.includes(
                        employee.employeeId
                      );

                    return (
                      <label
                        key={
                          employee.employeeId
                        }
                        className={`flex cursor-pointer items-center gap-3 border-b p-3 last:border-b-0 ${
                          checked
                            ? "bg-blue-50"
                            : "hover:bg-gray-50"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() =>
                            toggleEmployee(
                              employee.employeeId
                            )
                          }
                          className="h-4 w-4"
                        />

                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-gray-900">
                            {
                              getEmployeeName(
                                employee
                              )
                            }
                          </p>

                          <p className="text-xs text-gray-500">
                            {
                              employee.employeeId
                            }
                            {employee.department
                              ? ` • ${employee.department}`
                              : ""}
                            {employee.designation
                              ? ` • ${employee.designation}`
                              : ""}
                          </p>
                        </div>
                      </label>
                    );
                  }
                )
              )}
            </div>
          </div>
        )}

        {!isAddModal &&
          selectedTraining && (
            <div className="rounded-lg border border-blue-100 bg-blue-50 p-3">
              <p className="text-xs text-blue-700">
                Current assignment
              </p>

              <p className="mt-1 text-sm font-semibold text-blue-900">
                {
                  selectedTraining
                    .traineeIds?.length
                }{" "}
                employees currently assigned
              </p>
            </div>
          )}
      </div>
    );
  };

  return (
    <div className="space-y-6 p-4 md:p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Trainings
          </h1>

          <p className="mt-1 text-sm text-gray-500">
            Create, assign and track employee training programs.
          </p>
        </div>

        <button
          onClick={() =>
            setShowAdd(true)
          }
          className="flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
        >
          <Plus size={18} />
          Add Training
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <div className="rounded-xl border bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Total
            </p>
            <Users size={20} />
          </div>
          <p className="mt-2 text-2xl font-bold">
            {counts.total}
          </p>
        </div>

        <div className="rounded-xl border bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Ongoing
            </p>
            <Clock3 size={20} />
          </div>
          <p className="mt-2 text-2xl font-bold">
            {counts.ongoing}
          </p>
        </div>

        <div className="rounded-xl border bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Upcoming
            </p>
            <CalendarDays size={20} />
          </div>
          <p className="mt-2 text-2xl font-bold">
            {counts.upcoming}
          </p>
        </div>

        <div className="rounded-xl border bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Completed
            </p>
            <CheckCircle2 size={20} />
          </div>
          <p className="mt-2 text-2xl font-bold">
            {counts.completed}
          </p>
        </div>

        <div className="rounded-xl border bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">
              Cancelled
            </p>
            <X size={20} />
          </div>
          <p className="mt-2 text-2xl font-bold">
            {counts.cancelled}
          </p>
        </div>
      </div>

      <div className="rounded-xl border bg-white p-4 shadow-sm">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <div className="relative">
            <Search
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />

            <input
              value={search}
              onChange={(e) =>
                setSearch(e.target.value)
              }
              placeholder="Search training..."
              className="w-full rounded-lg border py-2.5 pl-10 pr-3 text-sm outline-none focus:border-blue-500"
            />
          </div>

          <select
            value={typeFilter}
            onChange={(e) =>
              setTypeFilter(
                e.target.value
              )
            }
            className="rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-blue-500"
          >
            <option value="All">
              All Training Types
            </option>

            {trainingTypes.map(
              (type) => (
                <option
                  key={type}
                  value={type}
                >
                  {type}
                </option>
              )
            )}
          </select>

          <select
            value={statusFilter}
            onChange={(e) =>
              setStatusFilter(
                e.target.value
              )
            }
            className="rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-blue-500"
          >
            <option value="All">
              All Status
            </option>
            <option value="Ongoing">
              Ongoing
            </option>
            <option value="Upcoming">
              Upcoming
            </option>
            <option value="Completed">
              Completed
            </option>
            <option value="Cancelled">
              Cancelled
            </option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="rounded-xl border bg-white p-10 text-center text-sm text-gray-500">
          Loading trainings...
        </div>
      ) : filteredTrainings.length ===
        0 ? (
        <div className="rounded-xl border bg-white p-10 text-center">
          <Filter
            size={32}
            className="mx-auto text-gray-400"
          />

          <p className="mt-3 font-medium text-gray-700">
            No trainings found
          </p>

          <p className="mt-1 text-sm text-gray-500">
            Create a training or change the filters.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          {filteredTrainings.map(
            (training) => {
              const status =
                getTrainingStatus(
                  training
                );

              return (
                <div
                  key={training._id}
                  className="rounded-xl border bg-white p-5 shadow-sm"
                >
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700">
                          {training.trainingType ||
                            "Training"}
                        </span>

                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                            status ===
                            "Completed"
                              ? "bg-green-50 text-green-700"
                              : status ===
                                "Ongoing"
                              ? "bg-orange-50 text-orange-700"
                              : status ===
                                "Cancelled"
                              ? "bg-red-50 text-red-700"
                              : "bg-gray-100 text-gray-700"
                          }`}
                        >
                          {status}
                        </span>
                      </div>

                      <h2 className="mt-3 text-lg font-bold text-gray-900">
                        {training.title}
                      </h2>
                    </div>
                  </div>

                  <p className="mt-2 line-clamp-2 text-sm text-gray-600">
                    {training.content ||
                      "No training description available."}
                  </p>

                  <div className="mt-4 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
                    <div className="flex items-center gap-2 text-gray-600">
                      <CalendarDays size={17} />
                      {formatDate(
                        training.trainingDate
                      )}
                    </div>

                    <div className="flex items-center gap-2 text-gray-600">
                      <Clock3 size={17} />
                      {training.durationMinutes
                        ? `${training.durationMinutes} minutes`
                        : "Duration not specified"}
                    </div>

                    <div className="flex items-center gap-2 text-gray-600">
                      <Users size={17} />
                      {training.traineeIds
                        ?.length || 0}{" "}
                      employees
                    </div>

                    <div className="flex items-center gap-2 text-gray-600">
                      <UserPlus size={17} />
                      {training.trainerName ||
                        "Trainer not specified"}
                    </div>
                  </div>

                  {training.departments &&
                    training.departments.length >
                      0 && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        {training.departments.map(
                          (department) => (
                            <span
                              key={
                                department
                              }
                              className="rounded-md bg-gray-100 px-2 py-1 text-xs text-gray-600"
                            >
                              {department}
                            </span>
                          )
                        )}
                      </div>
                    )}

                  <div className="mt-5 flex flex-wrap gap-2 border-t pt-4">
                    <button
                      onClick={() =>
                        openDetails(
                          training
                        )
                      }
                      className="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      <Eye size={16} />
                      Details
                    </button>

                    <button
                      onClick={() =>
                        openAssign(
                          training
                        )
                      }
                      className="flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      <UserPlus size={16} />
                      Assign
                    </button>

                    {status ===
                      "Ongoing" && (
                      <button
                        onClick={() =>
                          markCompleted(
                            training
                          )
                        }
                        disabled={saving}
                        className="flex items-center gap-2 rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                      >
                        <CheckCircle2
                          size={16}
                        />
                        Complete
                      </button>
                    )}
                  </div>
                </div>
              );
            }
          )}
        </div>
      )}

      {showAdd && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="max-h-[95vh] w-full max-w-4xl overflow-y-auto rounded-xl bg-white">
            <div className="sticky top-0 z-10 flex items-center justify-between border-b bg-white p-5">
              <div>
                <h2 className="text-xl font-bold text-gray-900">
                  Add Training
                </h2>

                <p className="mt-1 text-sm text-gray-500">
                  Create a training and assign it to employees.
                </p>
              </div>

              <button
                onClick={
                  closeAddModal
                }
                disabled={saving}
                className="rounded-lg p-2 hover:bg-gray-100 disabled:opacity-50"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-6 p-5">
              <div>
                <h3 className="mb-3 text-sm font-semibold text-gray-900">
                  Training Information
                </h3>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium">
                      Training Title *
                    </label>

                    <input
                      value={
                        form.title
                      }
                      onChange={(e) =>
                        setForm({
                          ...form,
                          title:
                            e.target
                              .value,
                        })
                      }
                      className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-blue-500"
                      placeholder="Enter training title"
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium">
                      Training Type
                    </label>

                    <select
                      value={
                        form.trainingType
                      }
                      onChange={(e) =>
                        setForm({
                          ...form,
                          trainingType:
                            e.target
                              .value,
                        })
                      }
                      className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-blue-500"
                    >
                      {trainingTypes.map(
                        (type) => (
                          <option
                            key={type}
                            value={type}
                          >
                            {type}
                          </option>
                        )
                      )}
                    </select>
                  </div>

                  <div className="md:col-span-2">
                    <label className="mb-1 block text-sm font-medium">
                      Training Details
                    </label>

                    <textarea
                      value={
                        form.content
                      }
                      onChange={(e) =>
                        setForm({
                          ...form,
                          content:
                            e.target
                              .value,
                        })
                      }
                      rows={4}
                      className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-blue-500"
                      placeholder="Enter training details"
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium">
                      Trainer Category
                    </label>

                    <select
                      value={
                        form.trainerCategory
                      }
                      onChange={(e) => {
                        const category =
                          e.target
                            .value;

                        setForm({
                          ...form,
                          trainerCategory:
                            category,
                          trainerName:
                            "",
                        });

                        setTrainerEmployeeId(
                          "");
                      }}
                      className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-blue-500"
                    >
                      {trainerCategories.map(
                        (category) => (
                          <option
                            key={category}
                            value={category}
                          >
                            {category}
                          </option>
                        )
                      )}
                    </select>
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium">
                      Trainer
                    </label>

                    {form.trainerCategory ===
                    "Internal" ? (
                      <select
                        value={
                          trainerEmployeeId
                        }
                        onChange={(e) =>
                          handleTrainerChange(
                            e.target
                              .value
                          )
                        }
                        className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-blue-500"
                      >
                        <option value="">
                          Select Employee Trainer
                        </option>

                        {internalTrainers.map(
                          (
                            employee
                          ) => (
                            <option
                              key={
                                employee.employeeId
                              }
                              value={
                                employee.employeeId
                              }
                            >
                              {
                                employee.employeeId
                              }{" "}
                              -{" "}
                              {
                                getEmployeeName(
                                  employee
                                )
                              }
                              {employee.department
                                ? ` - ${employee.department}`
                                : ""}
                            </option>
                          )
                        )}
                      </select>
                    ) : (
                      <input
                        value={
                          form.trainerName
                        }
                        onChange={(e) =>
                          setForm({
                            ...form,
                            trainerName:
                              e.target
                                .value,
                          })
                        }
                        className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-blue-500"
                        placeholder="Enter external trainer name"
                      />
                    )}
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium">
                      Training Date *
                    </label>

                    <input
                      type="datetime-local"
                      value={
                        form.trainingDate
                      }
                      onChange={(e) =>
                        setForm({
                          ...form,
                          trainingDate:
                            e.target
                              .value,
                        })
                      }
                      className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium">
                      Duration
                    </label>

                    <input
                      type="number"
                      min="0"
                      value={
                        form.durationMinutes
                      }
                      onChange={(e) =>
                        setForm({
                          ...form,
                          durationMinutes:
                            e.target
                              .value,
                        })
                      }
                      className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-blue-500"
                      placeholder="Minutes"
                    />
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium">
                      Training Mode
                    </label>

                    <select
                      value={
                        form.trainingMode
                      }
                      onChange={(e) =>
                        setForm({
                          ...form,
                          trainingMode:
                            e.target
                              .value,
                        })
                      }
                      className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-blue-500"
                    >
                      <option value="Offline">
                        Offline
                      </option>
                      <option value="Online">
                        Online
                      </option>
                      <option value="Hybrid">
                        Hybrid
                      </option>
                    </select>
                  </div>

                  <div>
                    <label className="mb-1 block text-sm font-medium">
                      Venue
                    </label>

                    <input
                      value={
                        form.venue
                      }
                      onChange={(e) =>
                        setForm({
                          ...form,
                          venue:
                            e.target
                              .value,
                        })
                      }
                      className="w-full rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-blue-500"
                      placeholder="Training venue"
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-gray-900">
                  Departments
                </label>

                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {departments.map(
                    (department) => (
                      <label
                        key={
                          department
                        }
                        className={`flex cursor-pointer items-center gap-2 rounded-lg border p-3 text-sm ${
                          form.departments.includes(
                            department
                          )
                            ? "border-blue-500 bg-blue-50"
                            : "hover:bg-gray-50"
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={form.departments.includes(
                            department
                          )}
                          onChange={() =>
                            toggleDepartment(
                              department
                            )
                          }
                          className="h-4 w-4"
                        />

                        <span>
                          {
                            department
                          }
                        </span>
                      </label>
                    )
                  )}
                </div>
              </div>

              <div>
                <div className="mb-3">
                  <h3 className="text-sm font-semibold text-gray-900">
                    Assign Training
                  </h3>

                  <p className="mt-1 text-xs text-gray-500">
                    Choose who should receive this training.
                  </p>
                </div>

                {renderAssignmentSelector(
                  true
                )}
              </div>

              <div className="flex flex-col-reverse gap-3 border-t pt-5 sm:flex-row sm:justify-end">
                <button
                  onClick={
                    closeAddModal
                  }
                  disabled={saving}
                  className="rounded-lg border px-5 py-2.5 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>

                <button
                  onClick={
                    createTraining
                  }
                  disabled={saving}
                  className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {saving
                    ? "Creating..."
                    : "Create Training"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showDetails &&
        selectedTraining && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-xl bg-white">
              <div className="sticky top-0 z-10 flex items-center justify-between border-b bg-white p-5">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">
                    Training Details
                  </h2>

                  <p className="mt-1 text-sm text-gray-500">
                    {
                      selectedTraining.title
                    }
                  </p>
                </div>

                <button
                  onClick={() => {
                    setShowDetails(
                      false
                    );
                    setSelectedTraining(
                      null
                    );
                  }}
                  className="rounded-lg p-2 hover:bg-gray-100"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="space-y-6 p-5">
                <div>
                  <div className="flex flex-wrap gap-2">
                    <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
                      {
                        selectedTraining.trainingType ||
                        "Training"
                      }
                    </span>

                    <span
                      className={`rounded-full px-3 py-1 text-xs font-medium ${
                        getTrainingStatus(
                          selectedTraining
                        ) ===
                        "Completed"
                          ? "bg-green-50 text-green-700"
                          : getTrainingStatus(
                              selectedTraining
                            ) ===
                            "Ongoing"
                          ? "bg-orange-50 text-orange-700"
                          : getTrainingStatus(
                              selectedTraining
                            ) ===
                            "Cancelled"
                          ? "bg-red-50 text-red-700"
                          : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {getTrainingStatus(
                        selectedTraining
                      )}
                    </span>
                  </div>

                  <h3 className="mt-3 text-2xl font-bold text-gray-900">
                    {
                      selectedTraining.title
                    }
                  </h3>

                  <p className="mt-2 text-sm leading-6 text-gray-600">
                    {
                      selectedTraining.content ||
                      "No description available."
                    }
                  </p>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="rounded-xl bg-gray-50 p-4">
                    <p className="text-xs text-gray-500">
                      Training Date
                    </p>
                    <p className="mt-1 font-semibold text-gray-900">
                      {formatDateTime(
                        selectedTraining.trainingDate
                      )}
                    </p>
                  </div>

                  <div className="rounded-xl bg-gray-50 p-4">
                    <p className="text-xs text-gray-500">
                      Duration
                    </p>
                    <p className="mt-1 font-semibold text-gray-900">
                      {selectedTraining.durationMinutes
                        ? `${selectedTraining.durationMinutes} minutes`
                        : "Not specified"}
                    </p>
                  </div>

                  <div className="rounded-xl bg-gray-50 p-4">
                    <p className="text-xs text-gray-500">
                      Trainer
                    </p>
                    <p className="mt-1 font-semibold text-gray-900">
                      {
                        selectedTraining.trainerName ||
                        "Not specified"
                      }
                    </p>
                  </div>

                  <div className="rounded-xl bg-gray-50 p-4">
                    <p className="text-xs text-gray-500">
                      Trainer Category
                    </p>
                    <p className="mt-1 font-semibold text-gray-900">
                      {
                        selectedTraining.trainerCategory ||
                        "Not specified"
                      }
                    </p>
                  </div>

                  <div className="rounded-xl bg-gray-50 p-4">
                    <p className="text-xs text-gray-500">
                      Training Mode
                    </p>
                    <p className="mt-1 font-semibold text-gray-900">
                      {
                        selectedTraining.trainingMode ||
                        "Not specified"
                      }
                    </p>
                  </div>

                  <div className="rounded-xl bg-gray-50 p-4">
                    <p className="text-xs text-gray-500">
                      Venue
                    </p>
                    <p className="mt-1 font-semibold text-gray-900">
                      {
                        selectedTraining.venue ||
                        "Not specified"
                      }
                    </p>
                  </div>

                  <div className="rounded-xl bg-gray-50 p-4">
                    <p className="text-xs text-gray-500">
                      Assigned Employees
                    </p>
                    <p className="mt-1 font-semibold text-gray-900">
                      {
                        selectedTraining.traineeIds
                          ?.length || 0
                      }
                    </p>
                  </div>
                </div>

                {selectedTraining.departments &&
                  selectedTraining.departments.length >
                    0 && (
                    <div>
                      <p className="text-sm font-semibold text-gray-900">
                        Departments
                      </p>

                      <div className="mt-2 flex flex-wrap gap-2">
                        {selectedTraining.departments.map(
                          (department) => (
                            <span
                              key={
                                department
                              }
                              className="rounded-md bg-gray-100 px-2.5 py-1 text-xs text-gray-700"
                            >
                              {
                                department
                              }
                            </span>
                          )
                        )}
                      </div>
                    </div>
                  )}

                <div>
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-gray-900">
                      Assigned Employees
                    </p>

                    <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-700">
                      {
                        selectedTraining
                          .traineeIds
                          ?.length || 0
                      }
                    </span>
                  </div>

                  <div className="mt-3 max-h-72 overflow-y-auto rounded-xl border">
                    {getTraineeEmployees(
                      selectedTraining
                    ).length === 0 ? (
                      <p className="p-5 text-center text-sm text-gray-500">
                        No employee details are available for this training.
                      </p>
                    ) : (
                      getTraineeEmployees(
                        selectedTraining
                      ).map(
                        (employee) => (
                          <div
                            key={
                              employee.employeeId
                            }
                            className="flex items-center justify-between border-b p-3 last:border-b-0"
                          >
                            <div>
                              <p className="text-sm font-medium text-gray-900">
                                {
                                  getEmployeeName(
                                    employee
                                  )
                                }
                              </p>

                              <p className="text-xs text-gray-500">
                                {
                                  employee.employeeId
                                }
                                {employee.department
                                  ? ` • ${employee.department}`
                                  : ""}
                                {employee.designation
                                  ? ` • ${employee.designation}`
                                  : ""}
                              </p>
                            </div>
                          </div>
                        )
                      )
                    )}
                  </div>
                </div>

                <div className="flex justify-end border-t pt-4">
                  <button
                    onClick={() => {
                      setShowDetails(
                        false
                      );
                      setSelectedTraining(
                        null
                      );
                    }}
                    className="rounded-lg bg-gray-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-gray-800"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

      {showAssign &&
        selectedTraining && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-xl bg-white">
              <div className="sticky top-0 z-10 flex items-center justify-between border-b bg-white p-5">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">
                    Assign Training
                  </h2>

                  <p className="mt-1 text-sm text-gray-500">
                    {
                      selectedTraining.title
                    }
                  </p>
                </div>

                <button
                  onClick={
                    closeAssignModal
                  }
                  disabled={saving}
                  className="rounded-lg p-2 hover:bg-gray-100 disabled:opacity-50"
                >
                  <X size={20} />
                </button>
              </div>

              <div className="space-y-5 p-5">
                {renderAssignmentSelector(
                  false
                )}

                <div className="flex flex-col-reverse gap-3 border-t pt-5 sm:flex-row sm:justify-end">
                  <button
                    onClick={
                      closeAssignModal
                    }
                    disabled={saving}
                    className="rounded-lg border px-5 py-2.5 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
                  >
                    Cancel
                  </button>

                  <button
                    onClick={
                      assignTraining
                    }
                    disabled={saving}
                    className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {saving
                      ? "Assigning..."
                      : "Assign Training"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
    </div>
  );
}