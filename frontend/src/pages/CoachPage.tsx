import { ArrowUp, Bot, ExternalLink, Sparkles, UserRound } from "lucide-react";
import { type FormEvent, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api";
import { AppShell } from "../components/AppShell";
import { useDemo } from "../context/DemoContext";
import type { CoachReply } from "../types";


interface Message {
  id: number;
  role: "user" | "assistant";
  text: string;
  actions?: CoachReply["actions"];
}

export function CoachPage() {
  const { employeeId = "" } = useParams();
  const { t, language, setEmployeeId } = useDemo();
  const [question, setQuestion] = useState("");
  const [sending, setSending] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, role: "assistant", text: t("coachGreeting") },
  ]);
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    setEmployeeId(employeeId);
  }, [employeeId, setEmployeeId]);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const presets = [t("presetMiddle"), t("presetWhy"), t("presetWeak"), t("presetFirst")];

  async function send(text: string) {
    const clean = text.trim();
    if (!clean || sending) return;
    const timestamp = Date.now();
    setMessages((current) => [...current, { id: timestamp, role: "user", text: clean }]);
    setQuestion("");
    setSending(true);
    try {
      const reply = await api.coach(employeeId, clean, language);
      setMessages((current) => [...current, { id: timestamp + 1, role: "assistant", text: reply.answer, actions: reply.actions }]);
    } catch (error) {
      setMessages((current) => [...current, { id: timestamp + 1, role: "assistant", text: error instanceof Error ? error.message : "Request failed" }]);
    } finally {
      setSending(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void send(question);
  }

  return (
    <AppShell employeeId={employeeId} title={t("coachTitle")} eyebrow={t("coachEyebrow")}>
      <section className="coach-layout">
        <div className="coach-context">
          <span className="coach-symbol"><Bot size={28} /></span>
          <div><h2>{t("coachTitle")}</h2><p>{t("coachSubtitle")}</p></div>
        </div>
        <div className="coach-presets" aria-label={t("suggestedQuestions")}>
          {presets.map((preset) => <button type="button" key={preset} onClick={() => void send(preset)}>{preset}</button>)}
        </div>
        <div className="chat-log" aria-live="polite">
          {messages.map((message) => (
            <article className={`chat-message chat-message-${message.role}`} key={message.id}>
              <span>{message.role === "assistant" ? <Sparkles size={17} /> : <UserRound size={17} />}</span>
              <div>
                <p>{message.text}</p>
                {message.actions?.length ? (
                  <div className="chat-actions">
                    {message.actions.map((action, index) => action.type === "navigate" ? (
                      <Link key={`${action.type}-${index}`} to={`/${action.to}/${employeeId}`}><ExternalLink size={14} />{t(action.to)}</Link>
                    ) : (
                      <Link key={action.event_id} to={`/quests/${employeeId}`}><ExternalLink size={14} />{action.label}</Link>
                    ))}
                  </div>
                ) : null}
              </div>
            </article>
          ))}
          {sending ? <article className="chat-message chat-message-assistant"><span><Sparkles size={17} /></span><div className="typing"><i /><i /><i /></div></article> : null}
          <div ref={endRef} />
        </div>
        <form className="chat-composer" onSubmit={submit}>
          <label className="sr-only" htmlFor="coach-question">{t("askQuestion")}</label>
          <textarea id="coach-question" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder={t("askQuestion")} rows={2} />
          <button className="icon-button icon-button-primary" type="submit" disabled={!question.trim() || sending} title={t("send")} aria-label={t("send")}><ArrowUp size={20} /></button>
        </form>
      </section>
    </AppShell>
  );
}
