import { Fragment, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { api } from './api'
import type { Snapshot } from './types'
import type ru from './locales/ru.json'

type Turn = { id: number; question: string; answer: string; mode: string; created_at: string }
type History = { turns: Turn[]; has_more: boolean; next_before: number | null }
type Props = { snap: Snapshot; t: (key: keyof typeof ru) => string; lang: 'ru' | 'en' | 'kk' }

export default function Coach({ snap, t, lang }: Props) {
  const [question, setQuestion] = useState('')
  const [turns, setTurns] = useState<Turn[]>([])
  const [nextBefore, setNextBefore] = useState<number | null>(null)
  const [pending, setPending] = useState('')
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)
  const [historyFailed, setHistoryFailed] = useState(false)
  const [error, setError] = useState<'chatLoadError' | 'chatSendError' | 'chatClearError' | null>(null)
  const [attempt, setAttempt] = useState(0)
  const [olderLoading, setOlderLoading] = useState(false)
  const scroller = useRef<HTMLDivElement>(null)
  const previousHeight = useRef<number | null>(null)
  const sending = useRef(false)
  const historyPath = `/employees/${encodeURIComponent(snap.employee.id)}/chat-history/`

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setHistoryFailed(false)
    setError(null)
    api<History>(historyPath, { signal: controller.signal }).then(data => {
      if (controller.signal.aborted) return
      setTurns(data.turns)
      setNextBefore(data.next_before)
    }).catch(() => {
      if (!controller.signal.aborted) { setHistoryFailed(true); setError('chatLoadError') }
    }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [historyPath, attempt])

  useLayoutEffect(() => {
    const element = scroller.current
    if (!element) return
    if (previousHeight.current !== null) {
      element.scrollTop += element.scrollHeight - previousHeight.current
      previousHeight.current = null
    } else {
      element.scrollTop = element.scrollHeight
    }
  }, [turns, pending, busy])

  const loadOlder = async () => {
    if (!nextBefore || olderLoading) return
    setOlderLoading(true)
    setError(null)
    try {
      const data = await api<History>(`${historyPath}?before=${nextBefore}`)
      previousHeight.current = scroller.current?.scrollHeight ?? null
      setTurns(old => [...data.turns, ...old])
      setNextBefore(data.next_before)
    } catch { setError('chatLoadError') }
    finally { setOlderLoading(false) }
  }

  const send = async (value: string) => {
    const text = value.trim()
    if (!text || sending.current || busy || loading || historyFailed) return
    sending.current = true
    setBusy(true)
    setPending(text)
    setQuestion('')
    setError(null)
    try {
      const data = await api<{ turn: Turn }>('/ai/chat/', {
        method: 'POST',
        body: JSON.stringify({ employee_id: snap.employee.id, message: text, language: lang }),
      })
      setTurns(old => [...old, data.turn])
    } catch {
      setQuestion(text)
      setError('chatSendError')
    } finally {
      setPending('')
      setBusy(false)
      sending.current = false
    }
  }

  const clear = async () => {
    if (busy || loading || olderLoading || !window.confirm(t('chatClearConfirm'))) return
    setBusy(true)
    setError(null)
    try {
      await api<History>(historyPath, { method: 'DELETE' })
      setTurns([])
      setNextBefore(null)
    } catch { setError('chatClearError') }
    finally { setBusy(false) }
  }

  const timestamp = (value: string) => new Intl.DateTimeFormat(
    lang === 'kk' ? 'kk-KZ' : lang, { dateStyle: 'short', timeStyle: 'short' },
  ).format(new Date(value))

  return <main className="page coach-page">
    <div className="page-heading"><div><span className="eyebrow">{t('coach')}</span><h1>{t('coach')}</h1></div></div>
    <div className="chat">
      <div className="chat-toolbar">
        <div><strong>{t('chatHistory')}</strong><small>{snap.employee.name} · {t('chatSaved')}</small></div>
        {turns.length > 0 && <button className="secondary" disabled={busy || loading || olderLoading} onClick={() => void clear()}>{t('chatClear')}</button>}
      </div>
      <div className="chat-messages" ref={scroller} role="log" aria-label={t('chatHistory')} aria-live="polite">
        {loading && <p role="status">{t('loading')}</p>}
        {!loading && nextBefore && <button className="secondary chat-older" disabled={olderLoading || busy} onClick={() => void loadOlder()}>{olderLoading ? t('loading') : t('chatOlder')}</button>}
        {!loading && !historyFailed && turns.length === 0 && !pending && <div className="chat-intro">
          <span className="coach-symbol">✳</span><h2>{t('ask')}</h2>
          <button disabled={busy} onClick={() => void send(t('question'))}>{t('question')} ↗</button>
        </div>}
        {turns.map(turn => <Fragment key={turn.id}>
          <div className="bubble user"><small className="chat-speaker">{t('chatYou')}</small>{turn.question}<time dateTime={turn.created_at}>{timestamp(turn.created_at)}</time></div>
          <div className="bubble coach"><small className="chat-speaker">{t('coach')}</small>{turn.answer}<time dateTime={turn.created_at}>{timestamp(turn.created_at)}</time></div>
        </Fragment>)}
        {pending && <div className="bubble user"><small className="chat-speaker">{t('chatYou')}</small>{pending}</div>}
        {pending && busy && <div className="bubble coach" role="status">{t('chatThinking')}</div>}
      </div>
      {error && <div className="chat-error" role="alert"><span>{t(error)}</span>{historyFailed && <button className="secondary" onClick={() => setAttempt(old => old + 1)}>{t('retry')}</button>}</div>}
      <p className="disclaimer">{t('disclaimer')}</p>
      <form className="chat-composer" onSubmit={event => { event.preventDefault(); void send(question) }}>
        <input value={question} maxLength={1000} disabled={busy || loading || historyFailed} onChange={event => setQuestion(event.target.value)} placeholder={t('ask')} aria-label={t('ask')}/>
        <button className="primary" disabled={busy || loading || historyFailed || !question.trim()}>{t('send')}</button>
      </form>
    </div>
  </main>
}
