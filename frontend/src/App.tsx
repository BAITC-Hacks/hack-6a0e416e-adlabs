import { useEffect, useMemo, useState } from 'react'
import { Link, NavLink, Route, Routes, useNavigate } from 'react-router-dom'
import { api } from './api'
import Coach from './Coach'
import type { EmployeeOption, Gap, Quest, Snapshot } from './types'
import ru from './locales/ru.json'
import en from './locales/en.json'
import kk from './locales/kk.json'

type Lang = 'ru'|'en'|'kk'
type Key = keyof typeof ru
const dictionaries = {ru,en,kk}
const nav: {path:string;key:Key;icon:string}[] = [
  {path:'/dashboard',key:'dashboard',icon:'◫'}, {path:'/career',key:'career',icon:'◇'},
  {path:'/skills',key:'skills',icon:'▤'}, {path:'/quests',key:'quests',icon:'◎'},
  {path:'/coach',key:'coach',icon:'✳'}, {path:'/profile',key:'profile',icon:'◯'}
]

function App() {
  const [lang,setLang] = useState<Lang>(() => (localStorage.getItem('cq_lang') as Lang) || 'ru')
  const [employeeId,setEmployeeId] = useState(() => localStorage.getItem('cq_employee') || '')
  const [snap,setSnap] = useState<Snapshot|null>(null)
  const [loading,setLoading] = useState(false)
  const [error,setError] = useState('')
  const navigate = useNavigate()
  const t = (key:Key) => dictionaries[lang][key]
  const refresh = async () => {
    if (!employeeId) return
    setLoading(true); setError('')
    try { setSnap(await api<Snapshot>(`/employees/${encodeURIComponent(employeeId)}/dashboard/`)) }
    catch (e) { setError(e instanceof Error ? e.message : 'REQUEST_FAILED') }
    finally { setLoading(false) }
  }
  useEffect(() => { void refresh() },[employeeId])
  useEffect(() => { localStorage.setItem('cq_lang',lang); document.documentElement.lang=lang },[lang])
  const choose = (employee:EmployeeOption) => {
    localStorage.setItem('cq_employee',employee.id); setEmployeeId(employee.id)
    if (!localStorage.getItem('cq_lang')) setLang((['ru','en','kk'].includes(employee.language) ? employee.language : 'ru') as Lang)
    navigate('/dashboard')
  }
  const switchEmployee = () => { localStorage.removeItem('cq_employee'); setEmployeeId(''); setSnap(null); navigate('/') }
  return <div className="app">
    {employeeId && <aside className="sidebar">
      <Link to="/dashboard" className="brand"><span className="brand-mark">CQ</span><span>{t('brand')}<small>{t('tagline')}</small></span></Link>
      <nav aria-label="Main">{nav.map(item=><NavLink key={item.path} to={item.path} className={({isActive})=>isActive?'nav-link active':'nav-link'}><span aria-hidden="true">{item.icon}</span>{t(item.key)}</NavLink>)}</nav>
      <button className="switch" onClick={switchEmployee}>{t('switchEmployee')} ↗</button>
    </aside>}
    <div className="workspace">
      <header className="topbar">
        {!employeeId && <div className="brand compact"><span className="brand-mark">CQ</span><span>{t('brand')}</span></div>}
        {employeeId && <span className="eyebrow">CAREER QUEST / {snap?.employee.department || ''}</span>}
        <div className="language" aria-label="Language">{(['ru','en','kk'] as Lang[]).map(code=><button key={code} className={lang===code?'selected':''} onClick={()=>setLang(code)} aria-pressed={lang===code}>{code==='kk'?'ҚАЗ':code.toUpperCase()}</button>)}</div>
      </header>
      {!employeeId ? <Selector t={t} choose={choose}/> :
        loading && !snap ? <div className="page skeleton">{t('loading')}</div> :
        error ? <div className="page state"><h2>{t('error')}</h2><p>{error}</p><button className="primary" onClick={refresh}>{t('retry')}</button></div> :
        snap ? <Routes>
          <Route path="/" element={<Dashboard snap={snap} t={t}/>}/>
          <Route path="/dashboard" element={<Dashboard snap={snap} t={t}/>}/>
          <Route path="/career" element={<Career snap={snap} t={t} refresh={refresh}/>}/>
          <Route path="/skills" element={<Skills snap={snap} t={t}/>}/>
          <Route path="/quests" element={<Quests snap={snap} t={t} refresh={refresh}/>}/>
          <Route path="/coach" element={<Coach key={snap.employee.id} snap={snap} t={t} lang={lang}/>}/>
          <Route path="/profile" element={<Profile snap={snap} t={t} switchEmployee={switchEmployee}/>}/>
        </Routes> : null}
    </div>
    {employeeId && <nav className="bottom-nav" aria-label="Mobile">{nav.map(item=><NavLink key={item.path} to={item.path} className={({isActive})=>isActive?'active':''}><span aria-hidden="true">{item.icon}</span><small>{t(item.key)}</small></NavLink>)}</nav>}
  </div>
}

type T = (key:Key)=>string
function Selector({t,choose}:{t:T;choose:(e:EmployeeOption)=>void}) {
  const [all,setAll] = useState<EmployeeOption[]>([])
  const [query,setQuery] = useState('')
  const [error,setError] = useState('')
  useEffect(()=>{api<EmployeeOption[]>('/employees/').then(setAll).catch(e=>setError(String(e)))},[])
  const filtered=useMemo(()=>all.filter(e=>[e.name,e.id,e.role].join(' ').toLowerCase().includes(query.toLowerCase())),[all,query])
  return <main className="selector page">
    <div className="selector-intro"><span className="eyebrow">CAREER QUEST</span><h1>{t('choose')}<span className="accent">.</span></h1><p>{t('tagline')}</p></div>
    <div className="selector-panel"><label htmlFor="employee-search">{t('search')}</label><input id="employee-search" value={query} onChange={e=>setQuery(e.target.value)} placeholder={t('search')}/>
      {error && <p className="error">{t('error')} — {error}</p>}
      <div className="employee-list">{filtered.slice(0,40).map(e=><button className="employee-row" key={e.id} onClick={()=>choose(e)}><span className="avatar">{e.name.split(' ').map(x=>x[0]).slice(0,2).join('')}</span><span className="employee-info"><strong>{e.name}</strong><small>{e.role} · {e.grade} · {e.id}</small></span><span className="row-arrow" aria-label={t('open')}>↗</span></button>)}{!filtered.length && <p className="muted">{t('noEmployees')}</p>}</div>
    </div>
  </main>
}

function Heading({eyebrow,title,aside}:{eyebrow:string;title:string;aside?:React.ReactNode}) { return <div className="page-heading"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1></div>{aside}</div> }
function Readiness({value,label}:{value:number|null;label:string}) { return <div className="readiness"><div className="readiness-value">{value===null?'—':`${value}%`}</div><span>{label}</span><div className="meter"><span style={{width:`${value||0}%`}}/></div></div> }
function GapRow({gap}:{gap:Gap}) { return <div className="gap-row"><div><strong>{gap.name}</strong>{gap.critical && <span className="critical-dot" aria-label="Critical">!</span>}</div><span>{gap.current} / {gap.required}</span><div className="mini-meter"><span style={{width:`${Math.min(gap.current/gap.required,1)*100}%`}}/></div></div> }
function QuestCard({quest,t,names,onStart}:{quest:Quest;t:T;names:Record<string,string>;onStart?:()=>void}) { return <article className={quest.locked?'quest-card locked':'quest-card'}><div className="quest-top"><span className="eyebrow">{quest.event_id} · {quest.format} · {quest.duration_hours} {t('duration')}</span><span className="quest-score">{quest.score}</span></div><h3>{quest.title}</h3><p>{quest.description}</p><div className="tags">{quest.skills.map(s=><span key={s}>{s}</span>)}</div>{quest.locked ? <div className="quest-reason"><strong>{t('requires')}:</strong> {quest.unmet_prerequisites.map(x=>`${names[x.skill_id]||x.skill_id} ${x.current}/${x.required}`).join(', ')}<br/>{quest.chain.length>1 && <><strong>{t('chain')}:</strong> {quest.chain.join(' → ')}</>}</div> : <div className="quest-reason">{quest.reasons.map(r=>`${r.code==='CRITICAL_GAP'?t('critical'):t('gap')}: ${names[r.skill_id]||r.skill_id}`).join(' · ')}</div>}<div className="quest-foot"><span>{t('impact')}: <strong>{quest.readiness_after}%</strong></span>{onStart && <button disabled={quest.locked} className="primary small" onClick={onStart}>{quest.locked?t('locked'):t('start')}</button>}</div></article> }
function Dashboard({snap,t}:{snap:Snapshot;t:T}) {
  const gaps=snap.top_gaps || snap.gaps.filter(g=>g.gap>0).slice(0,5)
  return <main className="page"><Heading eyebrow={t('dashboard')} title={snap.employee.name} aside={<span className="role-chip">{snap.employee.role} · {snap.employee.grade}</span>}/>
    <section className="hero-route"><div className="hero-copy"><span className="eyebrow">{t('career')}</span><h2>{snap.goal ? `${snap.employee.grade} → ${snap.goal.target_grade}` : t('noGoal')}</h2><p>{snap.goal?.target_role || t('setGoal')}</p><div className="route-line"><span className="route-node current">{t('current')}</span><span className="route-track"/><span className="route-node target">{t('target')}</span></div><Link className="text-link" to="/career">{t('career')} ↗</Link></div><Readiness value={snap.readiness} label={t('readiness')}/></section>
    <div className="dashboard-grid"><section className="panel next-panel"><div className="section-title"><span className="eyebrow">01 / {t('nextStep')}</span><Link to="/quests">{t('seeQuests')} ↗</Link></div>{snap.next_quest?<><h2>{snap.next_quest.title}</h2><p>{snap.next_quest.description}</p><div className="tags">{snap.next_quest.skills.map(s=><span key={s}>{s}</span>)}</div><div className="impact-strip">{t('impact')} <strong>{snap.readiness}% → {snap.next_quest.readiness_after}%</strong></div></>:<p>{snap.goal?t('noQuests'):t('noGoal')}</p>}</section>
    <section className="panel"><div className="section-title"><span className="eyebrow">02 / {t('topGaps')}</span><Link to="/skills">{t('viewSkills')} ↗</Link></div>{gaps.length?gaps.map(g=><GapRow key={g.skill_id} gap={g}/>):<p>{t('noGaps')}</p>}</section></div>
    <section className="progress-footer"><div><span className="eyebrow">{t('xp')}</span><strong>{snap.xp} XP</strong></div><div><span className="eyebrow">{t('rank')}</span><strong>{snap.rank}</strong></div><div><span className="eyebrow">{t('active')}</span><strong>{snap.active_quests.length}</strong></div><Link to="/coach">{t('coach')} ↗</Link></section>
  </main>
}
function Career({snap,t,refresh}:{snap:Snapshot;t:T;refresh:()=>Promise<void>}) {
  const [role,setRole]=useState(snap.goal?.target_role||snap.employee.role)
  const [grade,setGrade]=useState(snap.goal?.target_grade||'Middle')
  const [saving,setSaving]=useState(false)
  const [options,setOptions]=useState<{role:string;grade:string}[]>([])
  useEffect(()=>{api<{role:string;grade:string}[]>('/career-options/').then(setOptions).catch(()=>{})},[])
  const roles=Array.from(new Set([snap.employee.role,...options.map(x=>x.role)]))
  const grades=options.filter(x=>x.role===role).map(x=>x.grade)
  const save=async()=>{setSaving(true);try{await api(`/employees/${snap.employee.id}/career-goal/`,{method:'POST',body:JSON.stringify({target_role:role,target_grade:grade})});await refresh()}catch(e){alert(String(e))}finally{setSaving(false)}}
  return <main className="page"><Heading eyebrow={t('career')} title={t('career')}/><section className="hero-route career-route"><div className="hero-copy"><span className="eyebrow">{t('current')}</span><h2>{snap.employee.role}</h2><p>{snap.employee.grade}</p><div className="route-line"><span className="route-node current">01</span><span className="route-track"/><span className="route-node target">02</span></div><span className="eyebrow">{t('target')}</span><h2>{snap.goal?.target_role||t('noGoal')}</h2><p>{snap.goal?.target_grade}</p></div><Readiness value={snap.readiness} label={t('readiness')}/></section><div className="dashboard-grid"><section className="panel"><div className="section-title"><span className="eyebrow">{t('critical')}</span></div>{snap.gaps.filter(g=>g.critical).map(g=><GapRow key={g.skill_id} gap={g}/>)}</section><section className="panel"><div className="section-title"><span className="eyebrow">{t('goalRole')}</span></div><label>{t('goalRole')}<select value={role} onChange={e=>{setRole(e.target.value);setGrade(options.find(x=>x.role===e.target.value)?.grade||'Junior')}}>{roles.map(x=><option key={x}>{x}</option>)}</select></label><label>{t('goalGrade')}<select value={grade} onChange={e=>setGrade(e.target.value)}>{(grades.length?grades:['Junior','Middle','Senior','Lead']).map(x=><option key={x}>{x}</option>)}</select></label><button className="primary" disabled={saving} onClick={save}>{t('saveGoal')}</button></section></div></main>
}
function Skills({snap,t}:{snap:Snapshot;t:T}) { const [filter,setFilter]=useState<'all'|'gaps'|'critical'>('all');const shown=snap.gaps.filter(g=>filter==='all'||(filter==='gaps'?g.gap>0:g.critical));return <main className="page"><Heading eyebrow={t('skills')} title={t('skills')} aside={<span className="role-chip">{snap.goal?.target_role} · {snap.goal?.target_grade}</span>}/><div className="tabs">{(['all','gaps','critical'] as const).map(k=><button key={k} className={filter===k?'active':''} onClick={()=>setFilter(k)}>{t(k)}</button>)}</div><div className="skill-list"><div className="skill-header"><span>{t('skill')}</span><span>{t('level')} / {t('required')}</span><span>{t('gap')}</span></div>{shown.length?shown.map(g=><div className="skill-item" key={g.skill_id}><div><strong>{g.name}</strong>{g.critical&&<span className="critical-badge">{t('critical')}</span>}</div><div className="skill-bars"><div className="mini-meter"><span style={{width:`${Math.min(g.current/Math.max(g.required,1),1)*100}%`}}/></div><span>{g.current} / {g.required}</span></div><strong>{g.gap}</strong></div>):<p className="muted">{t('noGaps')}</p>}</div></main> }
function Quests({snap,t,refresh}:{snap:Snapshot;t:T;refresh:()=>Promise<void>}) {
  const [tab,setTab]=useState<'recommended'|'active'|'completed'>('recommended')
  const [result,setResult]=useState<{xp_awarded:number;readiness_before:number;readiness_after:number;skills_changed:{skill_id:string;before:number;after:number}[]}|null>(null)
  const [error,setError]=useState('')
  const act=async(event_id:string,action:'start'|'complete')=>{setError('');try{const response=await api<{xp_awarded:number;readiness_before:number;readiness_after:number;skills_changed:{skill_id:string;before:number;after:number}[]}>(`/quests/${event_id}/${action}/`,{method:'POST',body:JSON.stringify({employee_id:snap.employee.id})});if(action==='complete')setResult(response);await refresh();setTab(action==='complete'?'recommended':'active')}catch(e){setError(e instanceof Error?e.message:String(e))}}
  return <main className="page"><Heading eyebrow={t('quests')} title={t('quests')} aside={<span className="role-chip">{t('demo')}</span>}/><div className="tabs">{(['recommended','active','completed'] as const).map(k=><button key={k} className={tab===k?'active':''} onClick={()=>setTab(k)}>{t(k)} <span>{k==='recommended'?snap.recommendations.length:k==='active'?snap.active_quests.length:snap.completed_quests.length}</span></button>)}</div>{error&&<p className="error">{error}</p>}{tab==='recommended'&&<div className="quest-grid">{snap.recommendations.length?snap.recommendations.map(q=><QuestCard key={q.event_id} quest={q} t={t} names={snap.skill_names} onStart={()=>act(q.event_id,'start')}/>):<p>{t('noQuests')}</p>}</div>}{tab==='active'&&<div className="quest-grid">{snap.active_quests.length?snap.active_quests.map(q=><article className="quest-card" key={q.event_id}><span className="eyebrow">{q.event_id}</span><h3>{q.title}</h3><button className="primary" onClick={()=>act(q.event_id,'complete')}>{t('complete')}</button></article>):<p>{t('noQuests')}</p>}</div>}{tab==='completed'&&<div className="quest-grid">{snap.completed_quests.length?snap.completed_quests.map(q=><article className="quest-card" key={q.event_id}><span className="eyebrow">{q.event_id}</span><h3>{q.title}</h3><strong>{q.xp>0?`+${q.xp} XP`:t('completed')}</strong></article>):<p>{t('noQuests')}</p>}</div>}{result&&<div className="modal-backdrop"><div className="modal" role="dialog" aria-modal="true"><span className="eyebrow">{t('result')}</span><h2>+{result.xp_awarded} XP</h2><p>{t('readinessChange')}: {result.readiness_before}% → {result.readiness_after}%</p><div className="result-skills">{result.skills_changed.map(x=><div key={x.skill_id}>{snap.skill_names[x.skill_id]||x.skill_id} <strong>{x.before} → {x.after}</strong></div>)}</div><button className="primary" onClick={()=>setResult(null)}>{t('close')}</button></div></div>}</main>
}
function Profile({snap,t,switchEmployee}:{snap:Snapshot;t:T;switchEmployee:()=>void}) {return <main className="page"><Heading eyebrow={t('profile')} title={snap.employee.name}/><div className="profile-card"><div className="profile-avatar">{snap.employee.name.split(' ').map(x=>x[0]).slice(0,2).join('')}</div><div><span className="eyebrow">{snap.employee.id}</span><h2>{snap.employee.role}</h2><p>{snap.employee.grade} · {snap.employee.department}</p></div></div><div className="progress-footer"><div><span className="eyebrow">{t('target')}</span><strong>{snap.goal?.target_role||t('noGoal')} · {snap.goal?.target_grade}</strong></div><div><span className="eyebrow">{t('rank')}</span><strong>{snap.rank}</strong></div><div><span className="eyebrow">{t('xp')}</span><strong>{snap.xp}</strong></div></div><section className="panel achievement-panel"><span className="eyebrow">{t('achievements')}</span><div className="tags">{snap.achievements.map(code=><span key={code}>{t(code as Key)}</span>)}{!snap.achievements.length&&<p>{t('none')}</p>}</div></section><button className="secondary" onClick={switchEmployee}>{t('switchEmployee')}</button></main>}
export default App
