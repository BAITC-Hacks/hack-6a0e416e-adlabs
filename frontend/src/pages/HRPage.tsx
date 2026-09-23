import { AlertCircle, BarChart3, BriefcaseBusiness, Database, Target, UserRound, UsersRound } from "lucide-react";
import { useEffect } from "react";

import { api } from "../api";
import { AppShell } from "../components/AppShell";
import { EmptyState, ErrorState, LoadingState } from "../components/PageState";
import { useDemo } from "../context/DemoContext";
import { useResource } from "../hooks/useResource";


const STATUS_LABELS: Record<string, string> = {
  completed: "statusCompleted",
  in_progress: "statusInProgress",
  dropped: "statusDropped",
  declined: "statusDeclined",
  no_show: "statusNoShow",
  overdue: "statusOverdue",
};

export function HRPage() {
  const { t, setRole } = useDemo();
  const resource = useResource(() => api.hrOverview());
  useEffect(() => {
    setRole("hr");
  }, [setRole]);
  if (resource.loading) return <AppShell title={t("hrOverview")}><LoadingState /></AppShell>;
  if (resource.error || !resource.data) return <AppShell title={t("hrOverview")}><ErrorState error={resource.error || new Error("No data")} onRetry={resource.reload} /></AppShell>;
  const data = resource.data;
  const maxGap = Math.max(...data.top_gaps.map((gap) => gap.employees), 1);
  const maxParticipation = Math.max(...Object.values(data.participation), 1);

  return (
    <AppShell title={t("hrOverview")} eyebrow={t("hrEyebrow")}>
      <p className="page-lead">{t("hrSubtitle")}</p>
      <section className="metric-strip">
        <div><span><UsersRound size={20} /></span><strong>{data.totals.employees}</strong><small>{t("employees")}</small></div>
        <div><span><BriefcaseBusiness size={20} /></span><strong>{data.totals.events}</strong><small>{t("learningEvents")}</small></div>
        <div><span><Database size={20} /></span><strong>{data.totals.activity_records.toLocaleString()}</strong><small>{t("activityRecords")}</small></div>
        <div><span><AlertCircle size={20} /></span><strong>{data.employees_without_goal.length}</strong><small>{t("withoutGoal")}</small></div>
      </section>

      <div className="hr-grid">
        <section className="section-block">
          <div className="section-heading"><div><span className="section-kicker"><Target size={16} />{t("frequentGaps")}</span><h2>{t("frequentGaps")}</h2></div></div>
          <div className="bar-list">
            {data.top_gaps.map((gap) => (
              <div key={gap.skill_id}>
                <span><strong>{gap.name}</strong>{gap.critical ? <em>{t("critical")}</em> : null}</span>
                <div><i style={{ width: `${gap.employees / maxGap * 100}%` }} /><b>{gap.employees}</b></div>
              </div>
            ))}
          </div>
        </section>

        <section className="section-block">
          <div className="section-heading"><div><span className="section-kicker"><BarChart3 size={16} />{t("participation")}</span><h2>{t("participation")}</h2></div></div>
          <div className="participation-list">
            {Object.entries(data.participation).sort((a, b) => b[1] - a[1]).map(([status, count]) => (
              <div key={status}><span>{STATUS_LABELS[status] ? t(STATUS_LABELS[status]) : status}</span><div><i style={{ width: `${count / maxParticipation * 100}%` }} /></div><strong>{count}</strong></div>
            ))}
          </div>
        </section>
      </div>

      <div className="hr-grid hr-lists">
        <section className="section-block">
          <div className="section-heading"><div><span className="section-kicker"><UserRound size={16} />{t("withoutGoal")}</span><h2>{t("withoutGoal")}</h2></div><span className="count-badge">{data.employees_without_goal.length}</span></div>
          {data.employees_without_goal.length ? <EmployeeRows employees={data.employees_without_goal} /> : <EmptyState title={t("noData")} />}
        </section>
        <section className="section-block">
          <div className="section-heading"><div><span className="section-kicker"><AlertCircle size={16} />{t("withoutNextStep")}</span><h2>{t("withoutNextStep")}</h2></div><span className="count-badge">{data.employees_without_next_step.length}</span></div>
          {data.employees_without_next_step.length ? <EmployeeRows employees={data.employees_without_next_step} /> : <EmptyState title={t("noData")} />}
        </section>
      </div>
    </AppShell>
  );
}

function EmployeeRows({ employees }: { employees: Array<{ employee_id: string; full_name: string; role: string; grade: string }> }) {
  return (
    <div className="employee-rows">
      {employees.slice(0, 12).map((employee) => (
        <div key={employee.employee_id}><span className="avatar avatar-small">{employee.full_name.split(" ").map((part) => part[0]).slice(0, 2).join("")}</span><span><strong>{employee.full_name}</strong><small>{employee.role} · {employee.grade}</small></span><em>{employee.employee_id}</em></div>
      ))}
    </div>
  );
}
