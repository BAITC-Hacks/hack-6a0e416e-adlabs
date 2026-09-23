import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Clock3,
  History,
  LockKeyhole,
  Play,
  Sparkles,
  Target,
} from "lucide-react";

import { useDemo } from "../context/DemoContext";
import type { QuestItem, Recommendation } from "../types";


interface QuestCardProps {
  quest: QuestItem | Recommendation;
  variant: "recommended" | "active" | "completed";
  busy?: boolean;
  onStart?: (eventId: string) => void;
  onComplete?: (eventId: string) => void;
}

function isRecommendation(quest: QuestItem | Recommendation): quest is Recommendation {
  return "reasons" in quest;
}

export function QuestCard({ quest, variant, busy = false, onStart, onComplete }: QuestCardProps) {
  const { t } = useDemo();
  const recommendation = isRecommendation(quest) ? quest : null;
  return (
    <article className={`quest-card quest-card-${variant}`}>
      <header className="quest-card-header">
        <span className="quest-format"><BookOpen size={15} aria-hidden="true" />{quest.format}</span>
        <span className="quest-duration"><Clock3 size={15} aria-hidden="true" />{quest.duration_hours} {t("hours")}</span>
      </header>
      <div className="quest-card-body">
        <div>
          <h3>{quest.title}</h3>
          <p>{quest.description}</p>
        </div>
        {recommendation ? (
          <div className="quest-details">
            <div className="quest-impact">
              <Sparkles size={17} aria-hidden="true" />
              <span>{t("impact")}</span>
              <strong>
                {recommendation.impact.readiness_before}% <ArrowRight size={14} aria-hidden="true" /> {recommendation.impact.readiness_after}%
              </strong>
            </div>
            <div className="quest-reasons">
              <strong>{t("reason")}</strong>
              <ul>
                {recommendation.reasons.map((reason) => (
                  <li key={reason.group}>
                    {reason.group === "goal" ? <Target size={15} /> : null}
                    {reason.group === "skills" ? <Sparkles size={15} /> : null}
                    {reason.group === "history" ? <History size={15} /> : null}
                    <span>{reason.text}</span>
                  </li>
                ))}
              </ul>
            </div>
            {recommendation.locked ? (
              <div className="quest-chain">
                <strong><LockKeyhole size={16} aria-hidden="true" />{t("questChain")}</strong>
                <ol>
                  {recommendation.quest_chain.map((step) => <li key={step.event_id}>{step.title}</li>)}
                </ol>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
      <footer className="quest-card-footer">
        {recommendation?.locked ? (
          <span className="status status-warning"><LockKeyhole size={14} />{t("locked")}</span>
        ) : null}
        {variant === "recommended" && onStart ? (
          <button
            className="button button-primary"
            type="button"
            disabled={busy || Boolean(recommendation?.locked)}
            onClick={() => onStart(quest.event_id)}
          >
            <Play size={16} aria-hidden="true" />{t("startQuest")}
          </button>
        ) : null}
        {variant === "active" && onComplete ? (
          <button
            className="button button-primary"
            type="button"
            disabled={busy}
            onClick={() => onComplete(quest.event_id)}
          >
            <CheckCircle2 size={16} aria-hidden="true" />{t("completeQuest")}
          </button>
        ) : null}
        {variant === "completed" ? (
          <span className="status status-success"><CheckCircle2 size={14} />{t("completed")}</span>
        ) : null}
      </footer>
    </article>
  );
}
