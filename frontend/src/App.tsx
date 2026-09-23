import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { CSSProperties, ReactNode } from 'react';
import {
  ArrowRight, ArrowUpRight, Bell, BookOpen, BriefcaseBusiness,
  Check, CheckCircle2, ChevronDown, CircleHelp, Clock3, Compass, GraduationCap,
  LayoutDashboard, Lightbulb, LoaderCircle, LockKeyhole, MessageCircle, RefreshCw,
  Search, ShieldCheck, Sparkles, Target, TrendingUp, Users, WandSparkles, X,
} from 'lucide-react';
import { api } from './api';
import type {
  EmployeeProfileResponse, EmployeeSummary, HROverviewResponse,
  Recommendation, RoadmapResponse, SkillGapResponse,
} from './types';

type View = 'employee' | 'hr';
type DashboardData = {
  profile: EmployeeProfileResponse;
  gap: SkillGapResponse;
  recommendations: Recommendation[];
  roadmap: RoadmapResponse;
};

const gradeOrder = ['Junior', 'Middle', 'Senior', 'Lead'];
const scoreParts: { key: keyof Recommendation['score_breakdown']; label: string; max: number }[] = [
  { key: 'critical_skill_coverage', label: 'Критичные навыки', max: 45 },
  { key: 'total_gap_coverage', label: 'Закрытие разрыва', max: 25 },
  { key: 'career_goal_alignment', label: 'Карьерная цель', max: 15 },
  { key: 'completion_likelihood', label: 'Вероятность завершения', max: 10 },
  { key: 'time_efficiency', label: 'Время', max: 5 },
];

function initials(name: string) {
  return name.split(' ').filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase();
}

function formatDate(date: string | null) {
  if (!date) return 'В любое время';
  const [year, month, day] = date.split('-');
  return `${day}.${month}.${year}`;
}

function percent(value: number | null) {
  return value === null ? '—' : `${value.toLocaleString('ru-RU', { maximumFractionDigits: 1 })}%`;
}

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Что-то пошло не так. Попробуйте ещё раз.';
}

function Brand({ small = false }: { small?: boolean }) {
  return <div className={`brand ${small ? 'brand-small' : ''}`}>
    <span className="brand-mark"><Compass size={small ? 20 : 24} strokeWidth={2.5} /></span>
    <span>career<span className="brand-accent">quest</span><span className="brand-dot">.</span></span>
  </div>;
}

function ErrorBox({ message, onRetry }: { message: string; onRetry: () => void }) {
  return <div className="error-box" role="alert">
    <CircleHelp size={22} />
    <div><strong>Не удалось загрузить данные</strong><p>{message}</p></div>
    <button className="button button-light" onClick={onRetry}><RefreshCw size={16} /> Повторить</button>
  </div>;
}

function LoadingPanel({ label }: { label: string }) {
  return <div className="loading-panel" role="status"><LoaderCircle className="spin" size={28} /><span>{label}</span></div>;
}

function EntryScreen({ employees, loading, error, onRetry, onEnter }: {
  employees: EmployeeSummary[]; loading: boolean; error: string | null;
  onRetry: () => void; onEnter: (employeeId: string, view: View) => void;
}) {
  const [query, setQuery] = useState('');
  const [selectedId, setSelectedId] = useState('');
  const [view, setView] = useState<View>('employee');
  const filtered = useMemo(() => employees.filter((item) =>
    `${item.full_name} ${item.role} ${item.department} ${item.employee_id}`.toLocaleLowerCase('ru')
      .includes(query.toLocaleLowerCase('ru')),
  ), [employees, query]);
  const selected = employees.find((item) => item.employee_id === selectedId);

  return <div className="entry-page">
    <div className="entry-left">
      <div className="entry-top"><Brand /><span className="entry-demo-badge"><span /> ДЕМО ВЕРСИЯ</span></div>
      <div className="entry-copy">
        <span className="eyebrow"><Sparkles size={15} /> ВАША КАРЬЕРА, ВАШ МАРШРУТ</span>
        <h1>Следующий шаг<br /><em>начинается здесь.</em></h1>
        <p>Персональный план развития, который показывает, какие навыки прокачать и какие возможности выбрать прямо сейчас.</p>
        <div className="entry-feature-list">
          <div><span><Target size={19} /></span><div><strong>Чёткая карьерная цель</strong><small>Видимый прогресс до следующего грейда</small></div></div>
          <div><span><WandSparkles size={19} /></span><div><strong>Умные рекомендации</strong><small>Активности, которые действительно приближают к цели</small></div></div>
          <div><span><TrendingUp size={19} /></span><div><strong>Результат в цифрах</strong><small>Прогноз влияния каждого шага</small></div></div>
        </div>
      </div>
      <div className="entry-footer">CAREER QUEST · HACKALEM AI</div>
    </div>
    <div className="entry-right">
      <div className="entry-form-card">
        <div className="form-icon"><ArrowUpRight size={25} /></div>
        <span className="section-kicker">НАЧНЁМ ПУТЕШЕСТВИЕ</span>
        <h2>Войти в демо</h2>
        <p className="muted">Выберите сотрудника и режим просмотра. Данные загрузятся из API.</p>
        <div className="form-section-label">РЕЖИМ ПРОСМОТРА</div>
        <div className="role-choices">
          <button className={view === 'employee' ? 'role-choice active' : 'role-choice'} onClick={() => setView('employee')}>
            <span className="role-icon"><BriefcaseBusiness size={20} /></span><strong>Сотрудник</strong><small>Мой путь развития</small>
          </button>
          <button className={view === 'hr' ? 'role-choice active' : 'role-choice'} onClick={() => setView('hr')}>
            <span className="role-icon"><Users size={20} /></span><strong>HR</strong><small>Обзор команды</small>
          </button>
        </div>
        <label className="form-section-label" htmlFor="employee-search">СОТРУДНИК</label>
        <div className="search-wrap"><Search size={18} /><input id="employee-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Поиск по имени, роли или ID" autoComplete="off" /></div>
        {loading ? <div className="employee-pick-state"><LoaderCircle className="spin" size={18} /> Загружаем сотрудников...</div> : error ? <ErrorBox message={error} onRetry={onRetry} /> :
          <div className="employee-list" role="listbox" aria-label="Выберите сотрудника">
            {filtered.length ? filtered.slice(0, 100).map((item) => <button
              key={item.employee_id} type="button" role="option" aria-selected={selectedId === item.employee_id}
              className={`employee-option ${selectedId === item.employee_id ? 'selected' : ''}`}
              onClick={() => setSelectedId(item.employee_id)}>
              <span className="avatar avatar-small">{initials(item.full_name)}</span>
              <span className="employee-option-copy"><strong>{item.full_name}</strong><small>{item.role} · {item.grade} · {item.department}</small></span>
              {selectedId === item.employee_id && <Check size={18} />}
            </button>) : <div className="employee-pick-state">Сотрудники не найдены</div>}
          </div>}
        {filtered.length > 100 && <div className="search-hint">Показаны первые 100 результатов. Уточните поиск.</div>}
        <button className="button button-primary enter-button" disabled={!selected || loading} onClick={() => onEnter(selectedId, view)}>Войти <ArrowRight size={18} /></button>
        <div className="entry-privacy"><LockKeyhole size={14} /> Демо-режим без регистрации</div>
      </div>
    </div>
  </div>;
}

function Sidebar({ view, setView, profile, onExit, onChat }: {
  view: View; setView: (view: View) => void; profile: EmployeeProfileResponse | null;
  onExit: () => void; onChat: () => void;
}) {
  return <aside className="sidebar">
    <Brand small />
    <div className="sidebar-group-label">РАБОЧЕЕ ПРОСТРАНСТВО</div>
    <nav className="side-nav" aria-label="Основная навигация">
      <button className={view === 'employee' ? 'active' : ''} onClick={() => setView('employee')}><LayoutDashboard size={19} /> Мой дашборд</button>
      <button className={view === 'hr' ? 'active' : ''} onClick={() => setView('hr')}><Users size={19} /> HR-обзор</button>
      <button onClick={onChat}><MessageCircle size={19} /> AI-помощник <span className="soon-pill">скоро</span></button>
    </nav>
    <div className="sidebar-spacer" />
    <div className="sidebar-help"><span><Lightbulb size={19} /></span><strong>Развивайтесь осознанно</strong><p>Каждая рекомендация объясняет, как приблизиться к цели.</p></div>
    <button className="sidebar-user" onClick={onExit} title="Выбрать другого сотрудника">
      <span className="avatar">{profile ? initials(profile.employee.full_name) : 'CQ'}</span>
      <span><strong>{profile?.employee.full_name ?? 'Демо-профиль'}</strong><small>Сменить сотрудника <ArrowRight size={13} /></small></span>
    </button>
  </aside>;
}

function Topbar({ title, subtitle, profile, onExit }: { title: string; subtitle: string; profile: EmployeeProfileResponse | null; onExit: () => void }) {
  return <header className="topbar"><div><div className="topbar-breadcrumb">Career Quest <span>/</span> {title}</div><div className="topbar-title-mobile">{title}</div></div><div className="topbar-actions"><span className="topbar-subtitle">{subtitle}</span><span className="topbar-separator" /><span className="topbar-live"><span /> Демо</span><button className="topbar-avatar" onClick={onExit} title="Сменить сотрудника">{profile ? initials(profile.employee.full_name) : 'CQ'} <ChevronDown size={14} /></button></div></header>;
}

function ProgressRing({ value }: { value: number | null }) {
  return <div className="progress-ring" style={{ '--progress': `${Math.max(0, Math.min(100, value ?? 0))}%` } as CSSProperties}>
    <div><strong>{percent(value)}</strong><span>{value === null ? 'нет цели' : 'к цели'}</span></div>
  </div>;
}

function StatCard({ icon, label, value, detail, variant }: { icon: ReactNode; label: string; value: string; detail: string; variant?: string }) {
  return <div className={`stat-card ${variant ?? ''}`}><div className="stat-icon">{icon}</div><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>;
}

function SkillGap({ gap }: { gap: SkillGapResponse }) {
  const open = gap.skills.filter((skill) => skill.gap > 0);
  return <section className="panel skill-panel" id="skills">
    <div className="panel-head"><div><span className="section-kicker">КАРТА НАВЫКОВ</span><h2>Что осталось освоить</h2></div><span className="panel-count">{open.length} {open.length === 1 ? 'навык' : 'навыков'} в фокусе</span></div>
    {gap.status === 'no_target' ? <div className="empty-state"><Target size={28} /><strong>Цель пока не определена</strong><p>Для грейда Lead без карьерной цели разрыв навыков не рассчитывается.</p></div> : open.length === 0 ?
      <div className="empty-state positive"><CheckCircle2 size={28} /><strong>Все требования выполнены</strong><p>Ваши навыки соответствуют выбранному целевому профилю.</p></div> :
      <div className="skill-list">{open.slice(0, 6).map((skill) => <div className="skill-row" key={skill.skill_id}>
        <div className="skill-title"><div><strong>{skill.name}</strong><small>{skill.category} · {skill.type === 'hard' ? 'Профессиональный' : 'Гибкий'} навык</small></div>{skill.critical && <span className="critical-pill">Критичный</span>}</div>
        <div className="skill-levels"><span>Уровень {skill.current_level} / {skill.required_level}</span><span>−{skill.gap}</span></div>
        <div className="skill-bar"><span style={{ width: `${Math.min(100, (skill.current_level / skill.required_level) * 100)}%` }} /></div>
      </div>)}</div>}
    {open.length > 6 && <p className="panel-footnote">И ещё {open.length - 6} навыков в целевом профиле</p>}
  </section>;
}

function RecommendationCard({ item, index, completing, onComplete }: {
  item: Recommendation; index: number; completing: boolean; onComplete: (eventId: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const impact = item.projected_impact;
  return <article className="recommendation-card">
    <div className="rec-main"><div className="rec-number">{String(index + 1).padStart(2, '0')}</div><div className="rec-content">
      <div className="rec-heading"><div className="rec-tags"><span className="rec-type">{item.type}</span><span className="rec-format">{item.format === 'self_paced' ? 'В своём темпе' : item.format === 'online' ? 'Онлайн' : 'Офлайн'}</span></div><div className="match-score"><Sparkles size={16} /> {item.score.toLocaleString('ru-RU', { maximumFractionDigits: 1 })}<small>/ 100</small></div></div>
      <h3>{item.title}</h3><p className="rec-description">{item.description}</p>
      <div className="rec-meta"><span><Clock3 size={15} /> {item.duration_hours} ч</span><span><Bell size={15} /> {formatDate(item.next_session_date)}</span></div>
      <div className="rec-skill-chips">{item.matched_skill_gains.filter((skill) => skill.gap_closed > 0).map((skill) => <span key={skill.skill_id}>+{skill.gap_closed} {skill.name}</span>)}</div>
      <p className="rec-explanation"><Lightbulb size={17} /> {item.explanation}</p>
      <div className="rec-actions"><button className="button button-primary" disabled={completing} onClick={() => onComplete(item.event_id)}>{completing ? <><LoaderCircle className="spin" size={16} /> Обновляем...</> : <><Check size={17} /> Отметить выполненным</>}</button><button className="text-button" aria-expanded={expanded} onClick={() => setExpanded(!expanded)}>{expanded ? 'Скрыть расчёт' : 'Почему эта рекомендация?'} <ChevronDown className={expanded ? 'flip' : ''} size={16} /></button></div>
    </div></div>
    <div className="rec-impact"><span className="impact-label">ПРОГНОЗ ВЛИЯНИЯ</span><div className="impact-value"><ArrowUpRight size={20} /> +{impact.progress_delta_pct.toLocaleString('ru-RU', { maximumFractionDigits: 1 })} п.п.</div><small>к прогрессу цели</small><div className="impact-rule" /><div className="impact-progress"><span>Прогресс после</span><strong>{percent(impact.progress_after_pct)}</strong></div><div className="impact-progress"><span>Разрыв после</span><strong>{impact.total_gap_points_after} балл.</strong></div></div>
    {expanded && <div className="score-detail"><div className="score-detail-title">Из чего складывается оценка <strong>{item.score.toLocaleString('ru-RU', { maximumFractionDigits: 1 })} / 100</strong></div><div className="score-bars">{scoreParts.map((part) => <div key={part.key} className="score-row"><span>{part.label}</span><div><span style={{ width: `${Math.max(0, Math.min(100, item.score_breakdown[part.key] / part.max * 100))}%` }} /></div><strong>{item.score_breakdown[part.key]} / {part.max}</strong></div>)}</div></div>}
  </article>;
}

function Roadmap({ roadmap }: { roadmap: RoadmapResponse }) {
  return <section className="panel roadmap-panel" id="roadmap"><div className="panel-head"><div><span className="section-kicker">ПОШАГОВЫЙ ПЛАН</span><h2>Ваш маршрут к цели</h2></div><div className="roadmap-end"><TrendingUp size={17} /> {roadmap.ending_progress_pct === null ? 'Цель не задана' : `до ${percent(roadmap.ending_progress_pct)}`}</div></div>
    {roadmap.steps.length ? <div className="roadmap-steps">{roadmap.steps.map((step) => <div className="roadmap-step" key={`${step.order}-${step.recommendation.event_id}`}><div className="roadmap-node">{step.order}</div><div className="roadmap-step-copy"><strong>{step.recommendation.title}</strong><span>{step.recommendation.format === 'self_paced' ? 'В своём темпе' : formatDate(step.recommendation.next_session_date)} · {step.recommendation.duration_hours} ч</span></div><div className="roadmap-gain">{percent(step.progress_before_pct)} <ArrowRight size={15} /> <strong>{percent(step.progress_after_pct)}</strong></div></div>)}</div> :
      <div className="empty-state compact">{roadmap.status === 'ready' ? <CheckCircle2 size={27} /> : <BookOpen size={27} />}<strong>{roadmap.status === 'ready' ? 'Цель достигнута' : roadmap.status === 'no_target' ? 'Маршрут появится после выбора цели' : 'Подходящих активностей пока нет'}</strong><p>{roadmap.status === 'ready' ? 'Все требования целевого профиля выполнены.' : roadmap.status === 'no_target' ? 'Для сотрудника Lead без карьерной цели маршрут не строится.' : 'Для оставшегося разрыва нет доступных мероприятий.'}</p></div>}
    {roadmap.steps.length > 0 && <p className="roadmap-note">Прогноз рассчитан последовательно. Это симуляция развития навыков, а не гарантия повышения.</p>}
    {roadmap.steps.length > 0 && roadmap.status === 'no_activities' && <p className="roadmap-note">После этих шагов остаётся разрыв навыков, но доступных активностей для него пока нет.</p>}
  </section>;
}

function EmployeeDashboard({ data, loading, error, onRetry, completingId, onComplete, notice, clearNotice }: {
  data: DashboardData | null; loading: boolean; error: string | null; onRetry: () => void;
  completingId: string | null; onComplete: (eventId: string) => void;
  notice: string | null; clearNotice: () => void;
}) {
  if (loading && !data) return <LoadingPanel label="Собираем ваш карьерный маршрут..." />;
  if (error && !data) return <div className="page-error"><ErrorBox message={error} onRetry={onRetry} /></div>;
  if (!data) return null;
  const { employee, target } = data.profile;
  const { gap, recommendations, roadmap } = data;
  const nextGrade = gradeOrder[gradeOrder.indexOf(employee.grade) + 1];
  return <div className="dashboard-content">
    {notice && <div className="notice success" role="status"><CheckCircle2 size={20} /> {notice}<button onClick={clearNotice} aria-label="Закрыть"><X size={16} /></button></div>}
    {error && <ErrorBox message={error} onRetry={onRetry} />}
    <div className="page-intro"><div><span className="section-kicker">ВАШЕ КАРЬЕРНОЕ ПРОСТРАНСТВО</span><h1>Привет, {employee.full_name.split(' ')[0] ?? employee.full_name} <span>👋</span></h1><p>Вот где вы сейчас и какие шаги помогут двигаться дальше.</p></div><div className="date-pill"><ShieldCheck size={17} /> Персональный план развития</div></div>
    <section className="hero-card"><div className="hero-card-copy"><span className="hero-label"><Sparkles size={15} /> ВАШ КАРЬЕРНЫЙ ПУТЬ</span><h2>{employee.role}</h2><div className="career-ladder"><span className="grade-current">{employee.grade}</span><ArrowRight size={20} /><span className="grade-target">{target ? target.grade : 'Цель не выбрана'}</span></div><p>{target ? target.source === 'career_goal' ? `Ваша карьерная цель — ${target.role}, ${target.grade}.` : `Следующий шаг — ${target.role}, ${target.grade}.` : 'Вы достигли верхнего грейда текущей роли. Задайте карьерную цель, чтобы продолжить путь.'}</p>{target && nextGrade && target.grade !== nextGrade && <small className="next-grade-note">Следующий грейд в текущей роли: {nextGrade}</small>}</div><div className="hero-progress"><ProgressRing value={gap.progress_pct} /><span>{gap.status === 'ready' ? 'Требования выполнены' : gap.status === 'no_target' ? 'Ожидает цели' : 'Готовность к цели'}</span></div><div className="hero-decoration circle-one" /><div className="hero-decoration circle-two" /></section>
    <div className="stats-grid"><StatCard icon={<Target size={21} />} label="Разрыв навыков" value={target ? `${gap.total_gap_points} балл.` : '—'} detail={target ? 'до целевого профиля' : 'цель не задана'} /><StatCard icon={<ShieldCheck size={21} />} label="Критичные навыки" value={target ? `${gap.critical_skills_met} / ${gap.critical_skills_total}` : '—'} detail="уже на нужном уровне" /><StatCard icon={<GraduationCap size={21} />} label="Текущий грейд" value={employee.grade} detail={employee.department} /><StatCard icon={<TrendingUp size={21} />} label="Рекомендации" value={`${recommendations.length}`} detail="подобраны под вашу цель" variant="stat-accent" /></div>
    <div className="section-head recommendations-head" id="recommendations"><div><span className="section-kicker">СЛЕДУЮЩИЕ ШАГИ</span><h2>Рекомендовано для вас</h2><p>Активности ранжированы по навыкам, цели, завершению и затратам времени.</p></div><span className="section-count">ТОП-{recommendations.length}</span></div>
    {recommendations.length ? <div className="recommendations-list">{recommendations.map((item, index) => <RecommendationCard key={item.event_id} item={item} index={index} completing={completingId === item.event_id} onComplete={onComplete} />)}</div> : <div className="panel empty-recommendations"><div className="empty-state">{gap.status === 'ready' ? <CheckCircle2 size={29} /> : <BookOpen size={29} />}<strong>{gap.status === 'ready' ? 'Вы уже готовы к цели' : gap.status === 'no_target' ? 'Сначала нужна карьерная цель' : 'Сейчас нет подходящих активностей'}</strong><p>{gap.status === 'ready' ? 'Все целевые навыки достигнуты. Новые рекомендации появятся при новой цели.' : gap.status === 'no_target' ? 'Для грейда Lead без явной карьерной цели рекомендации не строятся.' : 'Ни одно доступное мероприятие сейчас не сокращает оставшийся разрыв навыков.'}</p></div></div>}
    <div className="lower-grid"><SkillGap gap={gap} /><Roadmap roadmap={roadmap} /></div>
    <div className="foot-disclaimer"><CircleHelp size={16} /> Отметка о выполнении обновляет навыки только в демо-сессии сервера. После перезапуска API прогресс сбросится.</div>
  </div>;
}

function HrDashboard({ overview, loading, error, onRetry }: { overview: HROverviewResponse | null; loading: boolean; error: string | null; onRetry: () => void }) {
  if (loading && !overview) return <LoadingPanel label="Собираем HR-обзор..." />;
  if (error && !overview) return <div className="page-error"><ErrorBox message={error} onRetry={onRetry} /></div>;
  if (!overview) return null;
  const largestGrade = Math.max(...Object.values(overview.grade_counts), 1);
  return <div className="dashboard-content">
    {error && <ErrorBox message={error} onRetry={onRetry} />}
    <div className="page-intro"><div><span className="section-kicker">АНАЛИТИКА КОМАНДЫ</span><h1>Обзор развития <span>↗</span></h1><p>Общая картина карьерных целей и готовности сотрудников.</p></div><div className="date-pill"><Bell size={17} /> Данные на {formatDate(overview.as_of_date)}</div></div>
    <section className="hr-hero"><div><span className="hero-label"><Users size={16} /> HR-ПАНЕЛЬ</span><h2>Потенциал команды<br />в одном месте.</h2><p>Следите за прогрессом, находите зоны роста и помогайте сотрудникам двигаться к целям.</p></div><div className="hr-hero-metric"><strong>{overview.employee_count}</strong><span>сотрудников в команде</span></div></section>
    <div className="stats-grid hr-stats"><StatCard icon={<Target size={21} />} label="Средний прогресс" value={percent(overview.average_progress_pct)} detail="среди сотрудников с целью" variant="stat-accent" /><StatCard icon={<CheckCircle2 size={21} />} label="Готовы к цели" value={`${overview.employees_ready}`} detail="достигли требований" /><StatCard icon={<Sparkles size={21} />} label="Явная цель" value={`${overview.employees_with_explicit_goal}`} detail="сотрудников указали цель" /><StatCard icon={<Compass size={21} />} label="Без цели" value={`${overview.employees_without_target}`} detail="требуется новый ориентир" /></div>
    <div className="hr-grid"><section className="panel hr-panel"><div className="panel-head"><div><span className="section-kicker">СТРУКТУРА КОМАНДЫ</span><h2>Грейды сотрудников</h2></div></div><div className="grade-bars">{gradeOrder.map((grade) => <div className="grade-bar-row" key={grade}><span>{grade}</span><div><span style={{ width: `${(overview.grade_counts[grade as keyof typeof overview.grade_counts] / largestGrade) * 100}%` }} /></div><strong>{overview.grade_counts[grade as keyof typeof overview.grade_counts]}</strong></div>)}</div><div className="hr-insight"><Lightbulb size={18} /> {overview.employees_without_explicit_goal} сотрудников пока не задали собственную карьерную цель.</div></section><section className="panel hr-panel"><div className="panel-head"><div><span className="section-kicker">ПО ПОДРАЗДЕЛЕНИЯМ</span><h2>Прогресс команд</h2></div></div>{overview.departments.length ? <div className="dept-list">{overview.departments.map((dept) => <div className="dept-row" key={dept.department}><span className="dept-icon"><BriefcaseBusiness size={18} /></span><div><strong>{dept.department}</strong><small>{dept.employee_count} сотрудников · {dept.employees_ready} готовы</small></div><span className="dept-progress">{percent(dept.average_progress_pct)}</span></div>)}</div> : <div className="empty-state compact"><Users size={25} /><strong>Подразделений пока нет</strong><p>Данные появятся после загрузки сотрудников.</p></div>}</section></div>
    <div className="foot-disclaimer"><CircleHelp size={16} /> Средний прогресс не включает сотрудников без карьерной цели. Показатели обновляются из текущего состояния API.</div>
  </div>;
}

function ChatPlaceholder({ onClose }: { onClose: () => void }) {
  return <div className="chat-overlay" onMouseDown={onClose}><aside className="chat-panel" onMouseDown={(event) => event.stopPropagation()} aria-label="AI-помощник"><div className="chat-head"><div><span className="chat-icon"><Sparkles size={20} /></span><div><strong>AI-помощник</strong><small>Скоро в Career Quest</small></div></div><button onClick={onClose} aria-label="Закрыть"><X size={20} /></button></div><div className="chat-body"><div className="chat-illustration"><MessageCircle size={36} /></div><h2>Помощник уже в пути</h2><p>Здесь можно будет обсудить карьерный маршрут и получить ответы по навыкам и активностям.</p><div className="chat-example">«Что мне изучить для следующего грейда?»</div><div className="chat-example">«Почему мне подходит эта активность?»</div></div><div className="chat-input"><input disabled placeholder="Скоро можно будет задать вопрос..." /><button disabled><ArrowRight size={19} /></button></div></aside></div>;
}

function App() {
  const [employees, setEmployees] = useState<EmployeeSummary[]>([]);
  const [employeeListLoading, setEmployeeListLoading] = useState(true);
  const [employeeListError, setEmployeeListError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [view, setView] = useState<View>('employee');
  const [data, setData] = useState<DashboardData | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [dashboardError, setDashboardError] = useState<string | null>(null);
  const [hrOverview, setHrOverview] = useState<HROverviewResponse | null>(null);
  const [hrLoading, setHrLoading] = useState(false);
  const [hrError, setHrError] = useState<string | null>(null);
  const [completingId, setCompletingId] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const activeEmployeeId = useRef<string | null>(null);
  const sessionGeneration = useRef(0);
  const dashboardRequest = useRef(0);
  const hrRequest = useRef(0);

  const loadEmployees = useCallback(async () => {
    setEmployeeListLoading(true); setEmployeeListError(null);
    try { setEmployees((await api.employees()).employees); }
    catch (error) { setEmployeeListError(getErrorMessage(error)); }
    finally { setEmployeeListLoading(false); }
  }, []);

  useEffect(() => { void loadEmployees(); }, [loadEmployees]);

  const loadDashboard = useCallback(async (id: string) => {
    const requestId = ++dashboardRequest.current;
    setDashboardLoading(true); setDashboardError(null);
    try {
      const [profile, gap, recommendations, roadmap] = await Promise.all([
        api.profile(id), api.skillGap(id), api.recommendations(id), api.roadmap(id),
      ]);
      if (requestId === dashboardRequest.current && activeEmployeeId.current === id) {
        setData({ profile, gap, recommendations: recommendations.recommendations, roadmap });
      }
    } catch (error) {
      if (requestId === dashboardRequest.current && activeEmployeeId.current === id) setDashboardError(getErrorMessage(error));
    } finally {
      if (requestId === dashboardRequest.current && activeEmployeeId.current === id) setDashboardLoading(false);
    }
  }, []);

  const loadHr = useCallback(async () => {
    const requestId = ++hrRequest.current;
    const employeeId = activeEmployeeId.current;
    setHrLoading(true); setHrError(null);
    try {
      const overview = await api.hrOverview();
      if (requestId === hrRequest.current && activeEmployeeId.current === employeeId) setHrOverview(overview);
    } catch (error) {
      if (requestId === hrRequest.current && activeEmployeeId.current === employeeId) setHrError(getErrorMessage(error));
    } finally {
      if (requestId === hrRequest.current && activeEmployeeId.current === employeeId) setHrLoading(false);
    }
  }, []);

  const enter = (id: string, nextView: View) => {
    sessionGeneration.current++;
    activeEmployeeId.current = id;
    dashboardRequest.current++;
    hrRequest.current++;
    setSelectedId(id); setView(nextView); setData(null); setHrOverview(null);
    setDashboardError(null); setHrError(null); setNotice(null); setCompletingId(null);
    void loadDashboard(id);
    if (nextView === 'hr') void loadHr();
  };

  const changeView = (nextView: View) => {
    setView(nextView);
    if (nextView === 'hr' && !hrOverview) void loadHr();
  };

  const complete = async (eventId: string) => {
    if (!selectedId || completingId) return;
    const employeeId = selectedId;
    const sessionId = sessionGeneration.current;
    setCompletingId(eventId); setDashboardError(null); setNotice(null);
    try {
      const result = await api.complete(employeeId, eventId);
      if (activeEmployeeId.current !== employeeId || sessionGeneration.current !== sessionId) return;
      dashboardRequest.current++;
      setDashboardLoading(false);
      setData((previous) => {
        if (!previous) return null;
        const skills = { ...previous.profile.employee.skills };
        for (const gain of result.applied_skill_gains) skills[gain.skill_id] = gain.after_level;
        return {
          ...previous,
          profile: { ...previous.profile, employee: { ...previous.profile.employee, skills } },
          gap: result.skill_gap,
          recommendations: result.recommendations,
          roadmap: result.roadmap,
        };
      });
      const totalGains = result.applied_skill_gains.reduce((sum, skill) => sum + skill.gain, 0);
      setNotice(totalGains > 0 ? `Активность выполнена. Навыки и рекомендации обновлены (+${totalGains} к уровням навыков).` : 'Активность выполнена. Навыки уже достигли доступного максимума.');
      if (hrOverview) void loadHr();
    } catch (error) {
      if (activeEmployeeId.current === employeeId && sessionGeneration.current === sessionId) setDashboardError(getErrorMessage(error));
    } finally {
      if (activeEmployeeId.current === employeeId && sessionGeneration.current === sessionId) setCompletingId(null);
    }
  };

  const exit = () => {
    sessionGeneration.current++;
    activeEmployeeId.current = null;
    dashboardRequest.current++;
    hrRequest.current++;
    setSelectedId(null); setData(null); setHrOverview(null); setChatOpen(false); setNotice(null);
    setDashboardLoading(false); setHrLoading(false); setCompletingId(null);
  };

  if (!selectedId) return <EntryScreen employees={employees} loading={employeeListLoading} error={employeeListError} onRetry={() => void loadEmployees()} onEnter={enter} />;

  return <div className="app-shell"><Sidebar view={view} setView={changeView} profile={data?.profile ?? null} onExit={exit} onChat={() => setChatOpen(true)} /><div className="app-main"><Topbar title={view === 'employee' ? 'Мой дашборд' : 'HR-обзор'} subtitle={view === 'employee' ? 'Личный маршрут развития' : 'Обзор команды'} profile={data?.profile ?? null} onExit={exit} />{view === 'employee' ? <EmployeeDashboard data={data} loading={dashboardLoading} error={dashboardError} onRetry={() => void loadDashboard(selectedId)} completingId={completingId} onComplete={(id) => void complete(id)} notice={notice} clearNotice={() => setNotice(null)} /> : <HrDashboard overview={hrOverview} loading={hrLoading} error={hrError} onRetry={() => void loadHr()} />}</div>{chatOpen && <ChatPlaceholder onClose={() => setChatOpen(false)} />}</div>;
}

export default App;
