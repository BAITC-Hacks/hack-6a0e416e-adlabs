import { ArrowRight, CheckCircle2, Flag, Save, Target } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import { api } from "../api";
import { AppShell } from "../components/AppShell";
import { CareerRoute } from "../components/CareerRoute";
import { ErrorState, LoadingState } from "../components/PageState";
import { ReadinessRing } from "../components/ReadinessRing";
import { useDemo } from "../context/DemoContext";
import { useResource } from "../hooks/useResource";


export function CareerPage() {
  const { employeeId = "" } = useParams();
  const { t, setEmployeeId } = useDemo();
  const career = useResource(() => api.career(employeeId), employeeId);
  const profiles = useResource(() => api.roleProfiles());
  const [draftRole, setDraftRole] = useState<string | null>(null);
  const [draftGrade, setDraftGrade] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    setEmployeeId(employeeId);
  }, [employeeId, setEmployeeId]);

  const role = draftRole ?? career.data?.goal?.target_role ?? "";
  const grade = draftGrade ?? career.data?.goal?.target_grade ?? "";

  const roles = useMemo(
    () => Array.from(new Set((profiles.data?.results || []).map((profile) => profile.role))),
    [profiles.data],
  );
  const grades = useMemo(
    () => (profiles.data?.results || []).filter((profile) => profile.role === role).map((profile) => profile.grade),
    [profiles.data, role],
  );

  async function saveGoal() {
    if (!role || !grade) return;
    setSaving(true);
    try {
      career.setData(await api.updateGoal(employeeId, role, grade));
      setDraftRole(null);
      setDraftGrade(null);
      setMessage(t("goalSaved"));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Request failed");
    } finally {
      setSaving(false);
    }
  }

  if (career.loading || profiles.loading) return <AppShell employeeId={employeeId} title={t("career")}><LoadingState /></AppShell>;
  if (career.error || profiles.error || !career.data) {
    return <AppShell employeeId={employeeId} title={t("career")}><ErrorState error={career.error || profiles.error || new Error("No data")} onRetry={() => { void career.reload(); void profiles.reload(); }} /></AppShell>;
  }
  const data = career.data;

  return (
    <AppShell employeeId={employeeId} title={t("career")} eyebrow={data.goal ? `${data.goal.target_role} · ${data.goal.target_grade}` : t("noGoalTitle")}>
      {message ? <div className="toast" role="status"><CheckCircle2 size={17} />{message}</div> : null}
      <div className="career-overview">
        <section className="career-position">
          <span className="section-kicker"><Flag size={16} />{t("careerRoute")}</span>
          <div className="position-compare">
            <div><small>{t("currentPosition")}</small><strong>{data.current.role}</strong><span>{data.current.grade}</span></div>
            <ArrowRight aria-hidden="true" />
            <div className={!data.goal ? "muted" : ""}><small>{t("targetPosition")}</small><strong>{data.goal?.target_role || "—"}</strong><span>{data.goal?.target_grade || "—"}</span></div>
          </div>
        </section>
        <ReadinessRing value={data.readiness} label={t("readiness")} />
      </div>

      {data.career_map.length > 1 ? (
        <section className="dashboard-band"><CareerRoute nodes={data.career_map} /></section>
      ) : null}

      <div className="career-columns">
        <section className="section-block goal-editor">
          <div className="section-heading"><div><span className="section-kicker"><Target size={16} />{t("changeGoal")}</span><h2>{data.goal ? t("changeGoal") : t("noGoalTitle")}</h2></div></div>
          {!data.goal ? <p>{t("noGoalText")}</p> : null}
          <div className="form-grid">
            <label><span>{t("role")}</span><select value={role} onChange={(event) => { setDraftRole(event.target.value); setDraftGrade(""); }}><option value="">—</option>{roles.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
            <label><span>{t("grade")}</span><select value={grade} onChange={(event) => setDraftGrade(event.target.value)} disabled={!role}><option value="">—</option>{grades.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
          </div>
          <button className="button button-primary" type="button" disabled={!role || !grade || saving} onClick={saveGoal}><Save size={16} />{t("saveGoal")}</button>
        </section>

        <section className="section-block">
          <div className="section-heading"><div><span className="section-kicker"><Target size={16} />{t("topSkillGaps")}</span><h2>{t("topSkillGaps")}</h2></div></div>
          <div className="gap-breakdown">
            {data.gaps.slice(0, 8).map((gap) => (
              <div key={gap.skill_id}>
                <span><strong>{gap.name}</strong>{gap.critical ? <em>{t("critical")}</em> : null}</span>
                <span className="gap-numbers">{gap.current}<small>/ {gap.required}</small></span>
                <div className="progress-track"><i style={{ width: `${Math.min(gap.current / gap.required * 100, 100)}%` }} /></div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
