import { Routes, Route } from "react-router-dom";
import Home from "../pages/Home";
import Upload from "../pages/Upload";
import DataSources from "../pages/DataSources";
import Dashboard from "../pages/Dashboard";
import SavedDashboards from "../pages/SavedDashboards";
import Login from "../pages/Login";
import Register from "../pages/Register";
import AuthCallback from "../pages/AuthCallback";
import Account from "../pages/Account";
import EnterpriseSuite from "../pages/enterprise/EnterpriseSuite";

// Route table for the whole app. New pages get added here in later phases.
export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/upload" element={<Upload />} />
      <Route path="/datasources" element={<DataSources />} />
      <Route path="/dashboards" element={<SavedDashboards />} />
      <Route path="/dashboard/:fileId" element={<Dashboard />} />
      {/* Phase 10 — opening a saved snapshot instead of the auto-generated dashboard */}
      <Route path="/dashboard/:fileId/saved/:savedId" element={<Dashboard />} />
      {/* Phase 12 — Authentication */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route path="/account" element={<Account />} />
      <Route path="/enterprise" element={<EnterpriseSuite />} />
    </Routes>
  );
}
