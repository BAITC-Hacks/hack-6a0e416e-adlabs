import { Award, CheckCircle2, Flag, Sparkles, Target, Trophy } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api";
import { AppShell } from "../components/AppShell";
import { CareerRoute } from "../components/CareerRoute";
import { ErrorState, LoadingState } from "../components/PageState";
import { QuestCard } from "../components/QuestCard";
import { ReadinessRing } from "../components/ReadinessRing";
import { useDemo } from "../context/DemoContext";
import { useResource } from "../hooks/useResource";


export function DashboardPage() {
  const { employeeId = "" } = useParams();
  const { t, setEmployeeId } = useDemo();
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState("");
  const resource = useResource(() => api.dashboard(employeeId), employeeId);

  useEffect(() => {
    setEmployeeId(employeeId);
  }, [employeeId, setEmployeeId]);
  useEffect(() => {
    if (!toast) return undefined;
    const timeout = window.setTimeout(() => setToast(""), 4000);
    return () => window.clearTimeout(timeout);
  }, [toast]);

  async function startQuest(eventId: string) {
    setBusy(true);
    try {
      await api.startQuest(employeeId, eventId);
      setToast(t("questStarted"));
      await resource.reload();
    } catch (error) {
      setToast(error instanceof Error ? error.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  if (resource.loading) return <AppShell employeeId={employeeId}><LoadingState /></AppShell>;
  if (resource.error || !resource.data) {
    return <AppShell employeeId={employeeId}><ErrorState error={resource.error || new Error("No data")} onRetry={resource.reload} /></AppShell>;
  }
  const data = resource.data;
  const progressRange = Math.max(data.progress.next_rank_xp - data.progress.rank_floor, 1);
  const progressValue = Math.max(data.progress.xp - data.progress.rank_floor, 0);

  return (
    <AppShell employeeId={employeeId} title={data.employee.full_name} eyebrow={`${data.employee.role} · ${data.employee.grade}`}>
      {toast ? <div className="toast" role="status"><CheckCircle2 size={17} />{toast}</div> : null}
      <section className="dashboard-hero">
        <div className="dashboard-identity">
          <span className="section-kicker"><Sparkles size={16} />{t("careerGoal")}</span>
          <h2>
            {data.career_goal
              ? `${data.career_goal.target_role} · ${data.career_goal.target_grade}`
              : t("noGoalTitle")}
          </h2>
          <p>{data.employee.department} · {data.employee.work_format}</p>
          {!data.career_goal ? <Link className="button button-primary" to={`/career/${employeeId}`}>{t("changeGoal")}</Link> : null}
        </div>
        <ReadinessRing value={data.readiness} label={t("readiness")} />
      </section>

      <section className="dashboard-band">
        <div className="section-heading">
          <div><span className="section-kicker"><Flag size={16} />{t("careerRoute")}</span><h2>{t("careerRoute")}</h2></div>
          <Link className="text-link" to={`/career/${employeeId}`}>{t("career")} →</Link>
        </div>
        <CareerRoute nodes={data.career_map} />
      </section>

      <div className="dashboard-columns">
        <section className="section-block">
          <div className="section-heading"><div><span className="section-kicker"><Target size={16} />{t("nextBestQuest")}</span><h2>{t("nextBestQuest")}</h2></div></div>
          {data.next_quest ? (
            <QuestCard quest={data.next_quest} variant="recommended" busy={busy} onStart={startQuest} />
          ) : (
            <div className="inline-empty"><p>{data.career_goal ? t("noQuests") : t("noGoalText")}</p></div>
          )}
        </section>

        <aside className="section-block gap-summary">
          <div className="section-heading"><div><span className="section-kicker"><Target size={16} />{t("topSkillGaps")}</span><h2>{t("topSkillGaps")}</h2></div></div>
          <ol className="gap-list">
            {data.top_gaps.map((gap) => (
              <li key={gap.skill_id}>
                <span>{gap.name}{gap.critical ? <em>{t("critical")}</em> : null}</span>
                <strong>{gap.current}<small>/ {gap.required}</small></strong>
                <span className="mini-progress"><i style={{ width: `${Math.min(gap.current / gap.required * 100, 100)}%` }} /></span>
              </li>
            ))}
          </ol>
          <Link className="text-link" to={`/skills/${employeeId}`}>{t("skills")} →</Link>
        </aside>
      </div>

      <section className="progress-band">
        <div className="rank-block">
          <span className="rank-icon"><Trophy size={22} /></span>
          <div><small>{t("progress")}</small><strong>{data.progress.rank}</strong><span>{data.progress.xp.toLocaleString()} XP</span></div>
        </div>
        <div className="rank-progress">
          <span><strong>{data.progress.next_rank}</strong><small>{t("xpToNext")}: {Math.max(data.progress.next_rank_xp - data.progress.xp, 0)}</small></span>
          <div className="progress-track"><i style={{ width: `${Math.min(progressValue / progressRange * 100, 100)}%` }} /></div>
        </div>
        <div className="achievement-row" aria-label={t("achievements")}>
          {data.progress.achievements.slice(0, 4).map((achievement) => (
            <span key={achievement.code}><Award size={17} />{achievement.title}</span>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
