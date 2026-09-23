import { AlertTriangle, CheckCircle2, Filter, Sparkles, Target } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import { api } from "../api";
import { AppShell } from "../components/AppShell";
import { ErrorState, LoadingState } from "../components/PageState";
import { ReadinessRing } from "../components/ReadinessRing";
import { useDemo } from "../context/DemoContext";
import { useResource } from "../hooks/useResource";


type FilterMode = "all" | "gaps" | "critical";

export function SkillsPage() {
  const { employeeId = "" } = useParams();
  const { t, setEmployeeId } = useDemo();
  const [filter, setFilter] = useState<FilterMode>("all");
  const resource = useResource(() => api.skills(employeeId), employeeId);
  useEffect(() => {
    setEmployeeId(employeeId);
  }, [employeeId, setEmployeeId]);

  const skills = useMemo(() => (resource.data?.skills || []).filter((skill) => {
    if (filter === "gaps") return skill.gap > 0;
    if (filter === "critical") return skill.critical;
    return true;
  }), [filter, resource.data]);

  if (resource.loading) return <AppShell employeeId={employeeId} title={t("skills")}><LoadingState /></AppShell>;
  if (resource.error || !resource.data) return <AppShell employeeId={employeeId} title={t("skills")}><ErrorState error={resource.error || new Error("No data")} onRetry={resource.reload} /></AppShell>;

  return (
    <AppShell employeeId={employeeId} title={t("skills")} eyebrow={resource.data.career_goal ? `${resource.data.career_goal.target_role} · ${resource.data.career_goal.target_grade}` : t("noGoalTitle")}>
      <section className="skills-summary">
        <div><span className="section-kicker"><Sparkles size={16} />{t("effectiveSkills")}</span><h2>{t("skills")}</h2><p>{t("effectiveSkillsHint")}</p></div>
        <ReadinessRing value={resource.data.readiness} label={t("readiness")} size="small" />
      </section>

      <div className="toolbar">
        <span><Filter size={16} />{t("filter")}</span>
        <div className="segmented">
          <button className={filter === "all" ? "active" : ""} type="button" onClick={() => setFilter("all")}>{t("all")}</button>
          <button className={filter === "gaps" ? "active" : ""} type="button" onClick={() => setFilter("gaps")}>{t("gapsOnly")}</button>
          <button className={filter === "critical" ? "active" : ""} type="button" onClick={() => setFilter("critical")}>{t("criticalOnly")}</button>
        </div>
      </div>

      <section className="skills-table" aria-label={t("skills")}>
        <div className="skills-row skills-header"><span>{t("skill")}</span><span>{t("current")}</span><span>{t("required")}</span><span>{t("gap")}</span><span>{t("status")}</span></div>
        {skills.map((skill) => (
          <div className="skills-row" key={skill.skill_id}>
            <span className="skill-name"><strong>{skill.name}</strong><small>{skill.category}</small></span>
            <span className="skill-level"><b>{skill.current}</b><i style={{ width: `${skill.current / 5 * 100}%` }} /></span>
            <span className="skill-level"><b>{skill.required}</b><i style={{ width: `${skill.required / 5 * 100}%` }} /></span>
            <span className="gap-value">{skill.gap}</span>
            <span className="skill-status">
              {skill.critical && skill.gap > 0 ? <em className="status status-danger"><AlertTriangle size={14} />{t("critical")}</em> : null}
              {!skill.gap ? <em className="status status-success"><CheckCircle2 size={14} />{t("ready")}</em> : null}
              {skill.improved_after_review ? <em className="status status-info"><Target size={14} />{t("improved")}</em> : null}
            </span>
          </div>
        ))}
      </section>
    </AppShell>
  );
}
