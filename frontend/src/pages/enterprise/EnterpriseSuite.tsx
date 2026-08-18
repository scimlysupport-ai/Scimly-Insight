import { useState, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listSavedDashboards } from "../../services/dashboardService";
import {
  addTeamMember,
  createAlert,
  createSchedule,
  createShare,
  createTeam,
  createVersionSnapshot,
  fetchAuditLogs,
  fetchSharedDashboards,
  fetchTeams,
  fetchUsers,
  fetchVersionHistory,
  fetchTeamMembers,
} from "../../services/enterpriseService";
import AuthStatus from "../../components/AuthStatus";

type TabName = "teams" | "sharing" | "alerts" | "versions" | "audit";

export default function EnterpriseSuite() {
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const initialTab = (searchParams.get("tab") as TabName) || "teams";
  const initialDashboardId = searchParams.get("dashboardId") || "";

  const [activeTab, setActiveTab] = useState<TabName>(initialTab);

  // Input states
  const [teamName, setTeamName] = useState("");
  const [teamDescription, setTeamDescription] = useState("");
  const [dashboardId, setDashboardId] = useState(initialDashboardId);
  const [sharePermission, setSharePermission] = useState("view");
  const [scheduleCron, setScheduleCron] = useState("0 * * * *");
  const [alertMetric, setAlertMetric] = useState("revenue");
  const [alertThreshold, setAlertThreshold] = useState(">1000");
  const [versionLabel, setVersionLabel] = useState("v1");
  const [memberTeamId, setMemberTeamId] = useState("1");
  const [memberUserId, setMemberUserId] = useState("1");
  const [memberRole, setMemberRole] = useState("member");

  const [shareTargetType, setShareTargetType] = useState<"team" | "user">("team");
  const [shareTeamId, setShareTeamId] = useState("");
  const [shareUserId, setShareUserId] = useState("");

  // Queries
  const { data: myDashboards = [] } = useQuery({
    queryKey: ["all-saved-dashboards"],
    queryFn: () => listSavedDashboards(),
  });

  const { data: teams = [] } = useQuery({ queryKey: ["enterprise-teams"], queryFn: fetchTeams });
  const { data: users = [] } = useQuery({ queryKey: ["enterprise-users"], queryFn: fetchUsers });
  const { data: auditLogs = [] } = useQuery({ queryKey: ["enterprise-audit-logs"], queryFn: fetchAuditLogs });

  const hasValidDashboardId = dashboardId && !Number.isNaN(Number(dashboardId)) && myDashboards.some(d => String(d.id) === dashboardId);
  const { data: versionHistory = [] } = useQuery({
    queryKey: ["enterprise-version-history", dashboardId],
    queryFn: () => fetchVersionHistory(Number(dashboardId)),
    enabled: !!hasValidDashboardId,
  });

  const { data: sharedDashboards = [] } = useQuery({
    queryKey: ["enterprise-shared-dashboards"],
    queryFn: fetchSharedDashboards,
  });

  const { data: teamMembers = [] } = useQuery({
    queryKey: ["enterprise-team-members", memberTeamId],
    queryFn: () => fetchTeamMembers(Number(memberTeamId)),
    enabled: !!memberTeamId && memberTeamId !== "",
  });

  useEffect(() => {
    if (!initialDashboardId && myDashboards.length > 0 && (dashboardId === "1" || !dashboardId)) {
      setDashboardId(String(myDashboards[0].id));
    }
  }, [myDashboards, dashboardId, initialDashboardId]);

  useEffect(() => {
    if (teams.length > 0 && (memberTeamId === "1" || !memberTeamId)) {
      setMemberTeamId(String(teams[0].id));
    }
  }, [teams, memberTeamId]);

  useEffect(() => {
    if (teams.length > 0 && !shareTeamId) {
      setShareTeamId(String(teams[0].id));
    }
  }, [teams, shareTeamId]);

  useEffect(() => {
    if (users.length > 0 && !shareUserId) {
      setShareUserId(String(users[0].id));
    }
  }, [users, shareUserId]);

  const renderDashboardSelector = (label: string = "Select Dashboard") => (
    <div className="flex flex-col gap-1.5 w-full">
      <label className="text-[10px] font-semibold text-scimly-muted uppercase tracking-wider">{label}</label>
      <select
        className="w-full bg-scimly-bg border border-scimly-border rounded-xl px-3 py-2 text-sm text-scimly-text focus:border-scimly-primary outline-none transition-colors"
        value={dashboardId}
        onChange={(e) => setDashboardId(e.target.value)}
      >
        {myDashboards.length === 0 ? (
          <option disabled value="">No saved dashboards available</option>
        ) : (
          myDashboards.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name} (File #{d.file_id})
            </option>
          ))
        )}
      </select>
    </div>
  );

  // Mutations
  const createTeamMutation = useMutation({
    mutationFn: () => createTeam(teamName, teamDescription),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["enterprise-teams"] });
      setTeamName("");
      setTeamDescription("");
      alert("Team created successfully");
    },
  });

  const createShareMutation = useMutation({
    mutationFn: () => {
      const payload: Record<string, any> = {
        dashboard_id: Number(dashboardId),
        permission: sharePermission,
      };
      if (shareTargetType === "team") {
        payload.team_id = Number(shareTeamId);
      } else {
        payload.user_id = Number(shareUserId);
      }
      return createShare(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["enterprise-shared-dashboards"] });
      alert("Share rule created successfully");
    },
  });

  const createScheduleMutation = useMutation({
    mutationFn: () =>
      createSchedule({ dashboard_id: Number(dashboardId), cron_expression: scheduleCron, enabled: true }),
    onSuccess: () => alert("Refresh schedule created successfully"),
  });

  const createAlertMutation = useMutation({
    mutationFn: () =>
      createAlert({
        dashboard_id: Number(dashboardId),
        title: `${alertMetric} alert`,
        metric: alertMetric,
        threshold: alertThreshold,
        enabled: true,
      }),
    onSuccess: () => alert("Alert rule created successfully"),
  });

  const createSnapshotMutation = useMutation({
    mutationFn: () => createVersionSnapshot(Number(dashboardId), versionLabel),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["enterprise-version-history", dashboardId] });
      setVersionLabel("");
      alert("Version snapshot saved successfully");
    },
  });

  const [inviteMode, setInviteMode] = useState<"email" | "user">("email");
  const [inviteEmail, setInviteEmail] = useState("");

  const addMemberMutation = useMutation({
    mutationFn: () => {
      if (!memberTeamId || memberTeamId === "") {
        throw new Error("Please select or create a team first.");
      }
      if (inviteMode === "email" && !inviteEmail.trim()) {
        throw new Error("Please enter a valid email address.");
      }
      if (inviteMode === "email") {
        return addTeamMember(Number(memberTeamId), undefined, memberRole, inviteEmail.trim());
      }
      return addTeamMember(Number(memberTeamId), Number(memberUserId), memberRole);
    },
    onSuccess: (res: any) => {
      queryClient.invalidateQueries({ queryKey: ["enterprise-team-members", memberTeamId] });
      setInviteEmail("");
      const successMsg = res?.data?.message || "Teammate invited successfully!";
      alert(successMsg);
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || err?.message || "Failed to invite teammate.";
      alert(`Invitation error: ${detail}`);
    },
  });

  return (
    <div className="min-h-screen bg-scimly-bg text-scimly-text font-body relative overflow-hidden flex flex-col justify-between">
      
      {/* Radial glows */}
      <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-scimly-primary/5 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-scimly-accent/5 rounded-full blur-[100px] pointer-events-none" />

      {/* Header */}
      <header className="relative z-10 w-full max-w-6xl mx-auto px-6 py-6 flex items-center justify-between border-b border-scimly-border/40">
        <div className="flex items-center gap-3">
          <Link to="/" className="inline-flex items-center gap-1.5 text-xs font-medium text-scimly-muted hover:text-scimly-primary transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-3.5 h-3.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
            </svg>
            Back to Home
          </Link>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-[10px] text-scimly-accent font-semibold tracking-wider bg-scimly-accent/10 border border-scimly-accent/20 px-2 py-0.5 rounded uppercase">Enterprise</span>
          <AuthStatus />
        </div>
      </header>

      {/* Main layout */}
      <main className="relative z-10 flex-1 max-w-6xl w-full mx-auto px-6 py-10 flex flex-col gap-6">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Enterprise Suite</h1>
          <p className="text-scimly-muted text-sm mt-1">Manage team access, schedules, alerts, version history, and compliance logging.</p>
        </div>

        {/* Tabbed settings container */}
        <div className="flex flex-col md:flex-row gap-6 items-start flex-1 min-h-[500px]">
          
          {/* Tab sidebar */}
          <nav className="w-full md:w-56 shrink-0 flex md:flex-col gap-1 overflow-x-auto md:overflow-x-visible pb-2 md:pb-0 border-b md:border-b-0 border-scimly-border">
            <button
              onClick={() => setActiveTab("teams")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                activeTab === "teams"
                  ? "bg-scimly-primary/10 text-scimly-primary border border-scimly-primary/20"
                  : "text-scimly-muted hover:text-scimly-text hover:bg-scimly-surface/40 border border-transparent"
              }`}
            >
              👥 Teams & Members
            </button>
            <button
              onClick={() => setActiveTab("sharing")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                activeTab === "sharing"
                  ? "bg-scimly-primary/10 text-scimly-primary border border-scimly-primary/20"
                  : "text-scimly-muted hover:text-scimly-text hover:bg-scimly-surface/40 border border-transparent"
              }`}
            >
              🔗 Dashboard Sharing
            </button>
            <button
              onClick={() => setActiveTab("alerts")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                activeTab === "alerts"
                  ? "bg-scimly-primary/10 text-scimly-primary border border-scimly-primary/20"
                  : "text-scimly-muted hover:text-scimly-text hover:bg-scimly-surface/40 border border-transparent"
              }`}
            >
              ⏱️ Refresh & Alerts
            </button>
            <button
              onClick={() => setActiveTab("versions")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                activeTab === "versions"
                  ? "bg-scimly-primary/10 text-scimly-primary border border-scimly-primary/20"
                  : "text-scimly-muted hover:text-scimly-text hover:bg-scimly-surface/40 border border-transparent"
              }`}
            >
              ⏳ Version History
            </button>
            <button
              onClick={() => setActiveTab("audit")}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                activeTab === "audit"
                  ? "bg-scimly-primary/10 text-scimly-primary border border-scimly-primary/20"
                  : "text-scimly-muted hover:text-scimly-text hover:bg-scimly-surface/40 border border-transparent"
              }`}
            >
              📜 Activity Audit
            </button>
          </nav>

          {/* Active tab content card */}
          <div className="flex-1 w-full bg-scimly-surface/40 border border-scimly-border rounded-2xl p-6 backdrop-blur-md min-h-[480px] flex flex-col">
            
            {/* Tab 1: Teams */}
            {activeTab === "teams" && (
              <div className="grid md:grid-cols-2 gap-8 items-start">
                
                {/* Column 1: Create Team */}
                <div className="space-y-4">
                  <div>
                    <h3 className="font-display font-semibold text-lg text-white">Create a Team</h3>
                    <p className="text-xs text-scimly-muted mt-0.5">Form a workspace team to share dashboards.</p>
                  </div>
                  <div className="space-y-3">
                    <input
                      type="text"
                      className="w-full bg-scimly-bg border border-scimly-border rounded-xl px-3.5 py-2 text-sm text-scimly-text focus:border-scimly-primary outline-none transition-colors"
                      placeholder="Team name"
                      value={teamName}
                      onChange={(e) => setTeamName(e.target.value)}
                    />
                    <textarea
                      rows={3}
                      className="w-full bg-scimly-bg border border-scimly-border rounded-xl px-3.5 py-2 text-sm text-scimly-text focus:border-scimly-primary outline-none transition-colors resize-none"
                      placeholder="Team description (optional)"
                      value={teamDescription}
                      onChange={(e) => setTeamDescription(e.target.value)}
                    />
                    <button
                      onClick={() => createTeamMutation.mutate()}
                      disabled={!teamName.trim()}
                      className="bg-gradient-to-r from-scimly-primary to-blue-600 text-white font-semibold text-xs px-4 py-2.5 rounded-xl hover:scale-[1.01] active:scale-[0.99] transition-all disabled:opacity-50 disabled:pointer-events-none"
                    >
                      Create Team
                    </button>
                  </div>

                  <div className="pt-4 border-t border-scimly-border/50">
                    <h4 className="text-xs font-semibold text-scimly-muted uppercase tracking-wider mb-2">Existing Teams</h4>
                    {teams.length === 0 ? (
                      <p className="text-xs text-scimly-muted italic">No teams created yet.</p>
                    ) : (
                      <ul className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                        {teams.map((team) => (
                          <li key={team.id} className="text-xs bg-scimly-bg/50 border border-scimly-border rounded-lg px-3 py-2 flex items-center justify-between">
                            <span className="font-medium text-white">{team.name}</span>
                            <span className="text-[10px] text-scimly-muted">ID: {team.id}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>

                {/* Column 2: Add Team Member */}
                <div className="space-y-4">
                  <div>
                    <h3 className="font-display font-semibold text-lg text-white">Add Team Member</h3>
                    <p className="text-xs text-scimly-muted mt-0.5">Assign users and roles to specific teams.</p>
                  </div>
                  <div className="space-y-3">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-semibold text-scimly-muted uppercase tracking-wider">Select Team</label>
                      <select
                        className="w-full bg-scimly-bg border border-scimly-border rounded-xl px-3 py-2 text-sm text-scimly-text focus:border-scimly-primary outline-none transition-colors"
                        value={memberTeamId}
                        onChange={(e) => setMemberTeamId(e.target.value)}
                      >
                        {teams.length === 0 ? (
                          <option disabled value="">No teams available</option>
                        ) : (
                          teams.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)
                        )}
                      </select>
                    </div>

                    <div className="flex gap-2 p-1 bg-scimly-bg border border-scimly-border rounded-xl mb-2">
                      <button
                        type="button"
                        onClick={() => setInviteMode("email")}
                        className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                          inviteMode === "email"
                            ? "bg-scimly-primary text-white font-semibold"
                            : "text-scimly-muted hover:text-scimly-text"
                        }`}
                      >
                        Invite by Email
                      </button>
                      <button
                        type="button"
                        onClick={() => setInviteMode("user")}
                        className={`flex-1 py-1.5 text-xs font-medium rounded-lg transition-colors ${
                          inviteMode === "user"
                            ? "bg-scimly-primary text-white font-semibold"
                            : "text-scimly-muted hover:text-scimly-text"
                        }`}
                      >
                        Select Teammate
                      </button>
                    </div>

                    {inviteMode === "email" ? (
                      <div className="flex flex-col gap-1.5">
                        <label className="text-[10px] font-semibold text-scimly-muted uppercase tracking-wider">Teammate Email Address</label>
                        <input
                          type="email"
                          placeholder="e.g. colleague@company.com"
                          className="w-full bg-scimly-bg border border-scimly-border rounded-xl px-3 py-2 text-sm text-scimly-text focus:border-scimly-primary outline-none transition-colors"
                          value={inviteEmail}
                          onChange={(e) => setInviteEmail(e.target.value)}
                        />
                      </div>
                    ) : (
                      <div className="flex flex-col gap-1.5">
                        <label className="text-[10px] font-semibold text-scimly-muted uppercase tracking-wider">Select User</label>
                        <select
                          className="w-full bg-scimly-bg border border-scimly-border rounded-xl px-3 py-2 text-sm text-scimly-text focus:border-scimly-primary outline-none transition-colors"
                          value={memberUserId}
                          onChange={(e) => setMemberUserId(e.target.value)}
                        >
                          {users.length === 0 ? (
                            <option disabled value="">No users available</option>
                          ) : (
                            users.map((u) => <option key={u.id} value={u.id}>{u.name || u.email}</option>)
                          )}
                        </select>
                      </div>
                    )}

                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-semibold text-scimly-muted uppercase tracking-wider">Select Role</label>
                      <select
                        className="w-full bg-scimly-bg border border-scimly-border rounded-xl px-3 py-2 text-sm text-scimly-text focus:border-scimly-primary outline-none transition-colors"
                        value={memberRole}
                        onChange={(e) => setMemberRole(e.target.value)}
                      >
                        <option value="member">Member</option>
                        <option value="admin">Admin</option>
                        <option value="viewer">Viewer</option>
                      </select>
                    </div>

                    <button
                      onClick={() => addMemberMutation.mutate()}
                      disabled={teams.length === 0 || (inviteMode === "email" ? !inviteEmail.trim() : users.length === 0)}
                      className="bg-gradient-to-r from-scimly-primary to-blue-600 text-white font-semibold text-xs px-4 py-2.5 rounded-xl hover:scale-[1.01] active:scale-[0.99] transition-all disabled:opacity-50 disabled:pointer-events-none mb-4"
                    >
                      {inviteMode === "email" ? "Invite Teammate" : "Add Member"}
                    </button>

                    <div className="pt-4 border-t border-scimly-border/50">
                      <h4 className="text-xs font-semibold text-scimly-muted uppercase tracking-wider mb-2">Team Members List</h4>
                      {teamMembers.length === 0 ? (
                        <p className="text-xs text-scimly-muted italic">No members in this team yet.</p>
                      ) : (
                        <ul className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                          {teamMembers.map((m) => (
                            <li key={m.id} className="text-xs bg-scimly-bg/50 border border-scimly-border rounded-lg px-3 py-2 flex items-center justify-between">
                              <div className="min-w-0">
                                <span className="font-medium text-white block truncate">{m.name}</span>
                                <span className="text-[10px] text-scimly-muted block truncate">{m.email}</span>
                              </div>
                              <span className="text-[10px] font-semibold bg-scimly-primary/10 text-scimly-primary border border-scimly-primary/20 px-2 py-0.5 rounded uppercase">
                                {m.role}
                              </span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                </div>

              </div>
            )}

            {/* Tab 2: Sharing */}
            {activeTab === "sharing" && (
              <div className="grid md:grid-cols-2 gap-8 items-start">
                
                {/* Column 1: Share Rule */}
                <div className="space-y-4">
                  <div>
                    <h3 className="font-display font-semibold text-lg text-white">Create a Share Rule</h3>
                    <p className="text-xs text-scimly-muted mt-0.5">Authorise others to view or edit your dashboards.</p>
                  </div>
                  <div className="space-y-3">
                    {renderDashboardSelector("Select Dashboard")}
                    
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-semibold text-scimly-muted uppercase tracking-wider">Share With</label>
                      <select
                        className="w-full bg-scimly-bg border border-scimly-border rounded-xl px-3 py-2 text-sm text-scimly-text focus:border-scimly-primary outline-none transition-colors"
                        value={shareTargetType}
                        onChange={(e) => setShareTargetType(e.target.value as "team" | "user")}
                      >
                        <option value="team">Entire Team</option>
                        <option value="user">Specific Teammate</option>
                      </select>
                    </div>

                    {shareTargetType === "team" ? (
                      <div className="flex flex-col gap-1.5">
                        <label className="text-[10px] font-semibold text-scimly-muted uppercase tracking-wider">Select Team</label>
                        <select
                          className="w-full bg-scimly-bg border border-scimly-border rounded-xl px-3 py-2 text-sm text-scimly-text focus:border-scimly-primary outline-none transition-colors"
                          value={shareTeamId}
                          onChange={(e) => setShareTeamId(e.target.value)}
                        >
                          {teams.length === 0 ? (
                            <option disabled value="">No teams available</option>
                          ) : (
                            teams.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)
                          )}
                        </select>
                      </div>
                    ) : (
                      <div className="flex flex-col gap-1.5">
                        <label className="text-[10px] font-semibold text-scimly-muted uppercase tracking-wider">Select Teammate</label>
                        <select
                          className="w-full bg-scimly-bg border border-scimly-border rounded-xl px-3 py-2 text-sm text-scimly-text focus:border-scimly-primary outline-none transition-colors"
                          value={shareUserId}
                          onChange={(e) => setShareUserId(e.target.value)}
                        >
                          {users.length === 0 ? (
                            <option disabled value="">No teammates available</option>
                          ) : (
                            users.map((u) => <option key={u.id} value={u.id}>{u.name || u.email}</option>)
                          )}
                        </select>
                      </div>
                    )}

                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-semibold text-scimly-muted uppercase tracking-wider">Permission</label>
                      <select
                        className="w-full bg-scimly-bg border border-scimly-border rounded-xl px-3 py-2 text-sm text-scimly-text focus:border-scimly-primary outline-none transition-colors"
                        value={sharePermission}
                        onChange={(e) => setSharePermission(e.target.value)}
                      >
                        <option value="view">View</option>
                        <option value="edit">Edit</option>
                      </select>
                    </div>
                    <button
                      onClick={() => createShareMutation.mutate()}
                      disabled={!dashboardId.trim()}
                      className="bg-gradient-to-r from-scimly-primary to-blue-600 text-white font-semibold text-xs px-4 py-2.5 rounded-xl hover:scale-[1.01] active:scale-[0.99] transition-all disabled:opacity-50"
                    >
                      Create Share Rule
                    </button>
                  </div>
                </div>

                {/* Column 2: Shared List */}
                <div className="space-y-4">
                  <div>
                    <h3 className="font-display font-semibold text-lg text-white">Shared Dashboards</h3>
                    <p className="text-xs text-scimly-muted mt-0.5">Dashboards shared within your workspace.</p>
                  </div>
                  {sharedDashboards.length === 0 ? (
                    <p className="text-xs text-scimly-muted italic bg-scimly-bg/30 border border-scimly-border/40 rounded-xl p-4 text-center">No shared dashboards.</p>
                  ) : (
                    <ul className="space-y-2 max-h-80 overflow-y-auto pr-1">
                      {sharedDashboards.map((item: any) => (
                        <li key={item.id} className="bg-scimly-bg/50 border border-scimly-border rounded-xl p-3 text-xs flex justify-between items-center gap-3">
                          <div className="min-w-0">
                            <span className="font-medium text-white truncate block">{item.name || `Dashboard #${item.dashboard_id}`}</span>
                            <span className="text-[10px] text-scimly-muted">Via: {item.shared_via}</span>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded ${
                              item.permission === "edit"
                                ? "bg-scimly-primary/10 text-scimly-primary border border-scimly-primary/20"
                                : "bg-scimly-accent/10 text-scimly-accent border border-scimly-accent/20"
                            }`}>
                              {item.permission}
                            </span>
                            <Link
                              to={`/dashboard/${item.file_id}/saved/${item.id}`}
                              className="bg-scimly-primary/20 hover:bg-scimly-primary/30 text-scimly-primary border border-scimly-primary/40 text-[10px] font-bold uppercase px-2.5 py-1 rounded transition-colors"
                            >
                              Open ↗
                            </Link>
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

              </div>
            )}

            {/* Tab 3: Alerts & Refresh */}
            {activeTab === "alerts" && (
              <div className="grid md:grid-cols-2 gap-8 items-start">
                
                {/* Column 1: Scheduled Refresh */}
                <div className="space-y-4">
                  <div>
                    <h3 className="font-display font-semibold text-lg text-white">Scheduled Refresh</h3>
                    <p className="text-xs text-scimly-muted mt-0.5">Automate database syncs using Cron expressions.</p>
                  </div>
                  <div className="space-y-3">
                    {renderDashboardSelector("Select Dashboard")}
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-semibold text-scimly-muted uppercase tracking-wider">Cron Expression</label>
                      <input
                        type="text"
                        className="w-full bg-scimly-bg border border-scimly-border rounded-xl px-3.5 py-2 text-sm text-scimly-text focus:border-scimly-primary outline-none transition-colors font-mono"
                        placeholder="e.g. 0 * * * *"
                        value={scheduleCron}
                        onChange={(e) => setScheduleCron(e.target.value)}
                      />
                    </div>
                    <button
                      onClick={() => createScheduleMutation.mutate()}
                      disabled={!dashboardId.trim() || !scheduleCron.trim()}
                      className="bg-gradient-to-r from-scimly-primary to-blue-600 text-white font-semibold text-xs px-4 py-2.5 rounded-xl hover:scale-[1.01] active:scale-[0.99] transition-all disabled:opacity-50"
                    >
                      Save Schedule
                    </button>
                  </div>
                </div>

                {/* Column 2: Alerts */}
                <div className="space-y-4">
                  <div>
                    <h3 className="font-display font-semibold text-lg text-white">Metric Alerts</h3>
                    <p className="text-xs text-scimly-muted mt-0.5">Trigger alerts when numeric metrics breach thresholds.</p>
                  </div>
                  <div className="space-y-3">
                    <input
                      type="text"
                      className="w-full bg-scimly-bg border border-scimly-border rounded-xl px-3.5 py-2 text-sm text-scimly-text focus:border-scimly-primary outline-none transition-colors"
                      placeholder="Metric Name (e.g. revenue)"
                      value={alertMetric}
                      onChange={(e) => setAlertMetric(e.target.value)}
                    />
                    <input
                      type="text"
                      className="w-full bg-scimly-bg border border-scimly-border rounded-xl px-3.5 py-2 text-sm text-scimly-text focus:border-scimly-primary outline-none transition-colors font-mono"
                      placeholder="Threshold (e.g. >1000)"
                      value={alertThreshold}
                      onChange={(e) => setAlertThreshold(e.target.value)}
                    />
                    <button
                      onClick={() => createAlertMutation.mutate()}
                      disabled={!dashboardId.trim() || !alertMetric.trim() || !alertThreshold.trim()}
                      className="bg-gradient-to-r from-scimly-primary to-blue-600 text-white font-semibold text-xs px-4 py-2.5 rounded-xl hover:scale-[1.01] active:scale-[0.99] transition-all disabled:opacity-50"
                    >
                      Create Alert Trigger
                    </button>
                  </div>
                </div>

              </div>
            )}

            {/* Tab 4: Version History */}
            {activeTab === "versions" && (
              <div className="grid md:grid-cols-2 gap-8 items-start">
                
                {/* Column 1: Save Snapshot */}
                <div className="space-y-4">
                  <div>
                    <h3 className="font-display font-semibold text-lg text-white">Save Version Snapshot</h3>
                    <p className="text-xs text-scimly-muted mt-0.5">Create a recovery point for this dashboard.</p>
                  </div>
                  <div className="space-y-3">
                    {renderDashboardSelector("Select Dashboard")}
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-semibold text-scimly-muted uppercase tracking-wider">Version Label</label>
                      <input
                        type="text"
                        className="w-full bg-scimly-bg border border-scimly-border rounded-xl px-3.5 py-2 text-sm text-scimly-text focus:border-scimly-primary outline-none transition-colors"
                        placeholder="e.g. v1.1.0"
                        value={versionLabel}
                        onChange={(e) => setVersionLabel(e.target.value)}
                      />
                    </div>
                    <button
                      onClick={() => createSnapshotMutation.mutate()}
                      disabled={!dashboardId.trim() || !versionLabel.trim()}
                      className="bg-gradient-to-r from-scimly-primary to-blue-600 text-white font-semibold text-xs px-4 py-2.5 rounded-xl hover:scale-[1.01] active:scale-[0.99] transition-all disabled:opacity-50"
                    >
                      Save Snapshot
                    </button>
                  </div>
                </div>

                {/* Column 2: Snapshots List */}
                <div className="space-y-4">
                  <div>
                    <h3 className="font-display font-semibold text-lg text-white">Version Snapshots</h3>
                    <p className="text-xs text-scimly-muted mt-0.5">Available snapshots for Dashboard #{dashboardId}.</p>
                  </div>
                  {versionHistory.length === 0 ? (
                    <p className="text-xs text-scimly-muted italic bg-scimly-bg/30 border border-scimly-border/40 rounded-xl p-4 text-center">No snapshots saved.</p>
                  ) : (
                    <ul className="space-y-2 max-h-80 overflow-y-auto pr-1">
                      {versionHistory.map((snapshot: any) => (
                        <li key={snapshot.id} className="bg-scimly-bg/50 border border-scimly-border rounded-xl p-3 text-xs flex justify-between items-center">
                          <span className="font-medium text-white">{snapshot.version_label}</span>
                          <span className="text-[10px] text-scimly-muted">ID: {snapshot.id}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

              </div>
            )}

            {/* Tab 5: Audit Logs */}
            {activeTab === "audit" && (
              <div className="space-y-4 flex-1 flex flex-col">
                <div>
                  <h3 className="font-display font-semibold text-lg text-white">Activity Audit Trail</h3>
                  <p className="text-xs text-scimly-muted mt-0.5">Secured log of user actions and database events.</p>
                </div>
                
                {auditLogs.length === 0 ? (
                  <p className="text-xs text-scimly-muted italic bg-scimly-bg/30 border border-scimly-border/40 rounded-xl p-6 text-center">No activity logged.</p>
                ) : (
                  <div className="border border-scimly-border rounded-xl overflow-hidden bg-scimly-bg/30 flex-1 max-h-[360px] overflow-y-auto pr-1">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="bg-scimly-surface border-b border-scimly-border text-scimly-muted font-semibold uppercase tracking-wider text-[10px]">
                          <th className="px-4 py-2.5">Action</th>
                          <th className="px-4 py-2.5">Target</th>
                          <th className="px-4 py-2.5">Entity ID</th>
                          <th className="px-4 py-2.5 text-right">Timestamp</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-scimly-border/40">
                        {auditLogs.map((event: any) => {
                          const isDelete = event.action?.toLowerCase().includes("delete");
                          const isCreate = event.action?.toLowerCase().includes("create");
                          
                          return (
                            <tr key={event.id} className="hover:bg-scimly-surface/30">
                              <td className="px-4 py-2">
                                <span className={`font-semibold ${
                                  isDelete ? 'text-red-400' : isCreate ? 'text-scimly-accent' : 'text-scimly-primary'
                                }`}>
                                  {event.action}
                                </span>
                              </td>
                              <td className="px-4 py-2 text-scimly-muted">{event.entity_type}</td>
                              <td className="px-4 py-2 text-scimly-muted font-mono">#{event.entity_id}</td>
                              <td className="px-4 py-2 text-right text-scimly-muted/70">
                                {new Date(event.created_at || Date.now()).toLocaleTimeString()}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 w-full max-w-6xl mx-auto px-6 py-8 border-t border-scimly-border/40 text-center text-xs text-scimly-muted">
        <div>© 2026 Scimly Insight. Compliance Governance Suite.</div>
      </footer>

    </div>
  );
}
