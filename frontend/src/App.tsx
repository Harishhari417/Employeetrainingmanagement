
import { Routes, Route } from "react-router-dom";
import AppShell from "./components/AppShell";
import ProtectedRoute from "./components/ProtectedRoute";
import Dashboard from "./pages/Dashboard";
import Feedback from "./pages/Feedback";
import Attendance from "./pages/Attendance";
import Trainings from "./pages/Trainings";
import Employees from "./pages/Employees";
import Departments from "./pages/Departments";
import Login from "./pages/Login";
import Evaluations from "./pages/Evaluations";
import Analytics from "./pages/Analytics";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/attendance" element={<Attendance />} />
          <Route path="/feedback" element={<Feedback />} />
          <Route path="/trainings" element={<Trainings />} />
          <Route path="/evaluations" element={<Evaluations />} />

          <Route element={<ProtectedRoute roles={["HR_ADMIN", "MANAGER"]} />}>
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/reports" element={<Reports />} />
          </Route>

          <Route element={<ProtectedRoute roles={["HR_ADMIN"]} />}>
            <Route path="/employees" element={<Employees />} />
            <Route path="/departments" element={<Departments />} />
          </Route>

          <Route path="/settings" element={<Settings />} />
        </Route>
      </Route>
    </Routes>
  );
}

