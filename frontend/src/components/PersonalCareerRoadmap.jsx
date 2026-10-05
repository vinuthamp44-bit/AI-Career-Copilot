import React, { useEffect, useState } from 'react';
import { ArrowUpRight, Check, ChevronDown, ChevronUp, RefreshCw, Sparkles } from 'lucide-react';
import { api } from '../services/api';

const initialForm = { target_role: '', experience_level: 'Beginner', education: '', hours_per_week: 8, timeline: '6 months' };

export default function PersonalCareerRoadmap({ dashboard }) {
  const [form, setForm] = useState({ ...initialForm, target_role: dashboard.target_role || '', education: dashboard.profile?.degree || '' });
  const [roadmap, setRoadmap] = useState(null);
  const [expanded, setExpanded] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.careerRoadmap().then((result) => setRoadmap(result.roadmap)).catch((requestError) => setError(requestError.message)).finally(() => setLoading(false));
  }, []);

  const updateForm = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));
  const generate = async (event) => {
    event.preventDefault();
    if (!form.target_role.trim()) return setError('Enter a target job role to build your roadmap.');
    setSaving(true);
    setError('');
    try {
      const result = await api.generateCareerRoadmap({ ...form, hours_per_week: Number(form.hours_per_week) });
      setRoadmap(result.roadmap);
    } catch (requestError) { setError(requestError.message); } finally { setSaving(false); }
  };
  const toggleTask = async (task) => {
    try { setRoadmap((await api.completeRoadmapTask(task.id, !task.completed)).roadmap); } catch (requestError) { setError(requestError.message); }
  };
  const updateRoadmap = async () => {
    setSaving(true);
    setError('');
    try { setRoadmap((await api.updateCareerRoadmap()).roadmap); } catch (requestError) { setError(requestError.message); } finally { setSaving(false); }
  };

  if (loading) return <div className="content"><div className="state"><div className="spinner" />Loading your roadmap...</div></div>;
  return <div className="content roadmap-page">
    <section className="page-heading"><div className="eyebrow">PERSONAL CAREER SYSTEM</div><h1>Personal Career Roadmap</h1><p>A practical plan that adapts to your target role, resume, and progress.</p></section>
    {!roadmap && <SetupForm form={form} updateForm={updateForm} generate={generate} saving={saving} />}
    {error && <p className="form-error" role="alert">{error}</p>}
    {roadmap && <RoadmapReport roadmap={roadmap} expanded={expanded} setExpanded={setExpanded} toggleTask={toggleTask} updateRoadmap={updateRoadmap} saving={saving} />}
  </div>;
}

function SetupForm({ form, updateForm, generate, saving }) {
  return <section className="panel roadmap-setup">
    <div className="panel-head"><div><div className="eyebrow">CAREER GOAL SETUP</div><h2>Where are you headed?</h2></div></div>
    <form onSubmit={generate} className="roadmap-form">
      <label>Target job role<input value={form.target_role} onChange={updateForm('target_role')} placeholder="Python Developer" /></label>
      <label>Experience level<select value={form.experience_level} onChange={updateForm('experience_level')}><option>Beginner</option><option>Intermediate</option><option>Advanced</option></select></label>
      <label>Current education<input value={form.education} onChange={updateForm('education')} placeholder="B.Tech Computer Science" /></label>
      <label>Hours per week<input type="number" min="1" max="80" value={form.hours_per_week} onChange={updateForm('hours_per_week')} /></label>
      <label>Target timeline<select value={form.timeline} onChange={updateForm('timeline')}><option>3 months</option><option>6 months</option><option>12 months</option></select></label>
      <div className="roadmap-resume-note"><Sparkles size={17} /><span>Your existing resume and profile skills will be reused automatically.</span></div>
      <button className="primary" disabled={saving}>{saving ? 'Analyzing...' : 'Analyze my resume and build roadmap'} <ArrowUpRight size={16} /></button>
    </form>
  </section>;
}

function RoadmapReport({ roadmap, expanded, setExpanded, toggleTask, updateRoadmap, saving }) {
  const priorities = roadmap.skill_analysis?.required?.filter((item) => item.status !== 'Strong').slice(0, 4) || [];
  return <>
    <section className="roadmap-summary"><div><div className="eyebrow">CAREER READINESS</div><strong>{roadmap.readiness?.overall || 0}<small>/100</small></strong><span>{roadmap.readiness?.overall >= 70 ? 'You are becoming job-ready.' : 'Build momentum one task at a time.'}</span></div><div className="roadmap-progress"><div className="progress-label"><span>Overall roadmap progress</span><b>{roadmap.progress}%</b></div><div className="progress-bar"><i style={{ width: `${roadmap.progress}%` }} /></div><small>{roadmap.completed_tasks} of {roadmap.total_tasks} tasks completed</small></div><button className="secondary" onClick={updateRoadmap} disabled={saving}><RefreshCw size={15} /> Update roadmap</button></section>
    <ScoreGrid readiness={roadmap.readiness} />
    <section className="panel daily-actions"><div className="panel-head"><div><div className="eyebrow">TODAY'S ACTIONS</div><h2>Small steps for today</h2></div></div>{roadmap.daily_actions?.length ? roadmap.daily_actions.slice(0, 4).map((action) => <div className="daily-action" key={action.id}><Check size={15} /><span>{action.title}</span><small>{action.estimated_minutes} min</small></div>) : <p className="empty">All current tasks are complete. Update your roadmap for the next set of actions.</p>}</section>
    <section className="roadmap-columns"><div><div className="section-heading"><div><div className="eyebrow">THE PLAN</div><h2>{roadmap.target_role}</h2></div></div>{roadmap.phases.map((phase) => <PhaseCard key={phase.id} phase={phase} expanded={expanded[phase.id]} setExpanded={setExpanded} toggleTask={toggleTask} />)}</div><aside><SkillPanel priorities={priorities} /><MilestonePanel milestones={roadmap.milestones} /></aside></section>
  </>;
}

function ScoreGrid({ readiness }) {
  const scores = [['Technical skills', readiness?.technical], ['Resume strength', readiness?.resume], ['Projects', readiness?.projects], ['Interview readiness', readiness?.interview], ['Job match', readiness?.job_match]];
  return <section className="roadmap-score-grid">{scores.map(([label, value]) => <div className="score-card" key={label}><small>{label}</small><strong>{value || 0}%</strong><div className="progress-bar"><i style={{ width: `${value || 0}%` }} /></div></div>)}</section>;
}

function PhaseCard({ phase, expanded, setExpanded, toggleTask }) {
  return <article className="phase-card"><button className="phase-toggle" onClick={() => setExpanded((current) => ({ ...current, [phase.id]: !current[phase.id] }))}><span className="phase-number">0{phase.position}</span><span><b>{phase.title}</b><small>{phase.duration} · {phase.progress}% complete</small></span>{expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}</button>{expanded && <div className="phase-body"><p>{phase.objective}</p><div className="tag-list">{phase.skills.map((skill) => <span key={skill}>{skill}</span>)}</div><h3>Weekly tasks</h3>{phase.tasks.map((task) => <label className={task.completed ? 'road-task complete' : 'road-task'} key={task.id}><input type="checkbox" checked={task.completed} onChange={() => toggleTask(task)} /><span><b>Week {task.week}: {task.title}</b><small>{task.description} · {task.estimated_minutes} min</small></span>{task.completed && <Check size={16} />}</label>)}<h3>Recommended project</h3><div className="project-recommendation"><b>{phase.recommended_project.title}</b><span>{phase.recommended_project.difficulty} · {phase.recommended_project.skills.join(', ') || 'Portfolio evidence'}</span><button className="text-btn" type="button">Add to roadmap</button></div></div>}</article>;
}

function SkillPanel({ priorities }) {
  return <section className="panel skill-panel"><div className="panel-head"><div><div className="eyebrow">SKILL GAPS</div><h2>What to focus on</h2></div></div>{priorities.length ? priorities.map((item) => <div className="skill-gap" key={item.skill}><span className={item.status === 'Missing' ? 'status-dot missing' : 'status-dot'} /><div><b>{item.skill}</b><small>{item.status} · {item.importance} priority</small></div></div>) : <p className="empty">Your current skills cover the target role requirements.</p>}</section>;
}

function MilestonePanel({ milestones }) {
  return <section className="panel milestone-panel"><div className="panel-head"><div><div className="eyebrow">MILESTONES</div><h2>Progress markers</h2></div></div>{milestones.map((milestone) => <div className={milestone.completed ? 'milestone complete' : 'milestone'} key={milestone.id}><span>{milestone.completed ? <Check size={14} /> : milestone.position}</span><div><b>{milestone.title}</b><small>{milestone.required_progress}% roadmap progress</small></div></div>)}</section>;
}
