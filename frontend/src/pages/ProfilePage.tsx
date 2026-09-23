import { Award, Building2, CalendarDays, Languages, MapPin, UserRound, UsersRound } from "lucide-react";
import { useEffect } from "react";
import { useParams } from "react-router-dom";

import { api } from "../api";
import { AppShell } from "../components/AppShell";
import { ErrorState, LoadingState } from "../components/PageState";
import { useDemo } from "../context/DemoContext";
import { useResource } from "../hooks/useResource";


export function ProfilePage() {
  const { employeeId = "" } = useParams();
  const { t, setEmployeeId } = useDemo();
  const resource = useResource(() => api.dashboard(employeeId), employeeId);
  useEffect(() => {
    setEmployeeId(employeeId);
  }, [employeeId, setEmployeeId]);
  if (resource.loading) return <AppShell employeeId={employeeId} title={t("profile")}><LoadingState /></AppShell>;
  if (resource.error || !resource.data) return <AppShell employeeId={employeeId} title={t("profile")}><ErrorState error={resource.error || new Error("No data")} onRetry={resource.reload} /></AppShell>;
  const { employee, progress } = resource.data;

  return (
    <AppShell employeeId={employeeId} title={employee.full_name} eyebrow={`${employee.employee_id} · ${employee.role}`}>
      <section className="profile-header">
        <span className="profile-avatar"><UserRound size={36} /></span>
        <div><h2>{employee.full_name}</h2><p>{employee.role} · {employee.grade}</p></div>
        <span className="rank-chip"><Award size={17} />{progress.rank} · {progress.xp.toLocaleString()} XP</span>
      </section>
      <section className="profile-details">
        <div><Building2 size={19} /><span><small>{t("department")}</small><strong>{employee.department}</strong></span></div>
        <div><MapPin size={19} /><span><small>{t("workFormat")}</small><strong>{employee.work_format}</strong></span></div>
        <div><CalendarDays size={19} /><span><small>{t("hireDate")}</small><strong>{employee.hire_date}</strong></span></div>
        <div><CalendarDays size={19} /><span><small>{t("lastReview")}</small><strong>{employee.last_review_date}</strong></span></div>
        <div><Languages size={19} /><span><small>{t("language")}</small><strong>{employee.preferred_language.toUpperCase()}</strong></span></div>
        <div><UsersRound size={19} /><span><small>{t("manager")}</small><strong>{employee.manager_id || "—"}</strong></span></div>
      </section>
      <section className="section-block profile-achievements">
        <div className="section-heading"><div><span className="section-kicker"><Award size={16} />{t("achievements")}</span><h2>{t("achievements")}</h2></div></div>
        <div className="achievement-grid">
          {progress.achievements.map((achievement) => <div key={achievement.code}><Award size={21} /><strong>{achievement.title}</strong></div>)}
        </div>
      </section>
    </AppShell>
  );
}
