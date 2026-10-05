import React, { useEffect, useState } from 'react';
import { ArrowUpRight, CheckCircle2, CircleAlert, CircleX } from 'lucide-react';
import { api } from '../services/api';

export default function SkillGapAnalyzer() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [openSkill, setOpenSkill] = useState('');
  useEffect(() => { api.skillGaps().then(setData).catch((requestError) => setError(requestError.message)); }, []);
  const toggleTask = async (skill, task) => {
    try {
      const result = await api.updateSkillPlanTask(task.id, !task.completed);
      setData((current) => {
        const analysis = Object.fromEntries(Object.entries(current.analysis).map(([group, items]) => [group, items.map((item) => item.skill !== skill ? item : { ...item, progress: result.progress, plan: item.plan.map((entry) => entry.id === task.id ? { ...entry, completed: result.completed } : entry) })]));
        return { ...current, analysis };
      });
    } catch (requestError) { setError(requestError.message); }
  };
  if (error) return <div className="content"><p className="form-error">{error}</p></div>;
  if (!data) return <div className="content"><div className="state"><div className="spinner" />Analyzing your skill profile...</div></div>;
  return <div className="content skill-gap-page"><section className="page-heading"><div className="eyebrow">ROLE READINESS</div><h1>Skill Gap Analyzer</h1><p>Turn the skills your target role needs into a practical, trackable learning plan.</p></section><div className="skill-gap-columns"><SkillColumn title="Strong skills" eyebrow="READY TO USE" icon={CheckCircle2} tone="strong" items={data.analysis.strong} openSkill={openSkill} setOpenSkill={setOpenSkill} onToggleTask={toggleTask} /><SkillColumn title="Needs improvement" eyebrow="BUILD DEPTH" icon={CircleAlert} tone="improve" items={data.analysis.needs_improvement} openSkill={openSkill} setOpenSkill={setOpenSkill} onToggleTask={toggleTask} /><SkillColumn title="Missing skills" eyebrow="HIGH IMPACT GAPS" icon={CircleX} tone="missing" items={data.analysis.missing} openSkill={openSkill} setOpenSkill={setOpenSkill} onToggleTask={toggleTask} /></div></div>;
}

function SkillColumn({ title, eyebrow, icon: Icon, tone, items, openSkill, setOpenSkill, onToggleTask }) {
  return <section className={`panel skill-column ${tone}`}><div className="panel-head"><div><div className="eyebrow">{eyebrow}</div><h2>{title}</h2></div><Icon size={19} /></div>{items.length ? items.map((item) => <article className="skill-detail" key={item.skill}><div><b>{item.skill}</b><small>{item.current_level} → {item.required_level} · {item.priority} priority</small></div><p>{item.why_it_matters}</p><span><ArrowUpRight size={13} /> {item.recommended_action}</span>{item.plan?.length > 0 && <><button className="skill-plan-toggle" onClick={() => setOpenSkill((current) => current === item.skill ? '' : item.skill)}>{item.progress}% complete · {openSkill === item.skill ? 'Hide' : 'View'} 7-day plan</button>{openSkill === item.skill && <div className="skill-plan"><div className="progress-bar"><i style={{ width: `${item.progress}%` }} /></div>{item.plan.map((task) => <label className={task.completed ? 'skill-plan-task complete' : 'skill-plan-task'} key={task.id}><input type="checkbox" checked={task.completed} onChange={() => onToggleTask(item.skill, task)} /><span><b>Day {task.day}</b> {task.title}</span></label>)}</div>}</>}</article>) : <p className="empty">No skills in this category yet.</p>}</section>;
}
