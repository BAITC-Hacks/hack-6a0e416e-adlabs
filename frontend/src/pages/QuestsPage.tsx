import { CheckCircle2, Compass, ListChecks, PlayCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { api } from "../api";
import { AppShell } from "../components/AppShell";
import { EmptyState, ErrorState, LoadingState } from "../components/PageState";
import { QuestCard } from "../components/QuestCard";
import { useDemo } from "../context/DemoContext";
import { useResource } from "../hooks/useResource";


type Tab = "recommended" | "active" | "completed";

export function QuestsPage() {
  const { employeeId = "" } = useParams();
  const { t, setEmployeeId } = useDemo();
  const [tab, setTab] = useState<Tab>("recommended");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [toast, setToast] = useState("");
  const resource = useResource(() => api.quests(employeeId), employeeId);
  useEffect(() => {
    setEmployeeId(employeeId);
  }, [employeeId, setEmployeeId]);

  async function start(eventId: string) {
    setBusyId(eventId);
    try {
      await api.startQuest(employeeId, eventId);
      setToast(t("questStarted"));
      setTab("active");
      await resource.reload();
    } catch (error) {
      setToast(error instanceof Error ? error.message : "Request failed");
    } finally {
      setBusyId(null);
    }
  }

  async function complete(eventId: string) {
    setBusyId(eventId);
    try {
      const result = await api.completeQuest(employeeId, eventId);
      setToast(`${t("questCompleted")} · +${result.xp_awarded} XP`);
      setTab("completed");
      await resource.reload();
    } catch (error) {
      setToast(error instanceof Error ? error.message : "Request failed");
    } finally {
      setBusyId(null);
    }
  }

  if (resource.loading) return <AppShell employeeId={employeeId} title={t("quests")}><LoadingState /></AppShell>;
  if (resource.error || !resource.data) return <AppShell employeeId={employeeId} title={t("quests")}><ErrorState error={resource.error || new Error("No data")} onRetry={resource.reload} /></AppShell>;
  const items = resource.data[tab];

  return (
    <AppShell employeeId={employeeId} title={t("quests")} eyebrow={t("questEyebrow")}>
      {toast ? <div className="toast" role="status"><CheckCircle2 size={17} />{toast}</div> : null}
      <div className="quest-tabs" role="tablist" aria-label={t("quests")}>
        <button type="button" role="tab" aria-selected={tab === "recommended"} className={tab === "recommended" ? "active" : ""} onClick={() => setTab("recommended")}><Compass size={17} />{t("recommended")}<span>{resource.data.recommended.length}</span></button>
        <button type="button" role="tab" aria-selected={tab === "active"} className={tab === "active" ? "active" : ""} onClick={() => setTab("active")}><PlayCircle size={17} />{t("active")}<span>{resource.data.active.length}</span></button>
        <button type="button" role="tab" aria-selected={tab === "completed"} className={tab === "completed" ? "active" : ""} onClick={() => setTab("completed")}><ListChecks size={17} />{t("completed")}<span>{resource.data.completed.length}</span></button>
      </div>
      {items.length ? (
        <section className="quest-list">
          {items.map((quest) => (
            <QuestCard
              key={quest.event_id}
              quest={quest}
              variant={tab}
              busy={busyId === quest.event_id}
              onStart={start}
              onComplete={complete}
            />
          ))}
        </section>
      ) : <EmptyState title={t("noQuests")} />}
    </AppShell>
  );
}
