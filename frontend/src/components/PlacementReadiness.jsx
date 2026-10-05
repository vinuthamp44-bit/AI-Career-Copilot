import React, { useEffect, useState } from 'react';
import { ArrowRight, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

const scoreLabels = [['resume', 'Resume'], ['technical', 'Technical skills'], ['projects', 'Projects'], ['interview', 'Interview'], ['job_match', 'Job match'], ['communication', 'Communication'], ['roadmap', 'Roadmap progress']];

export default function PlacementReadiness({ dashboard, onNavigate }) {
  const [readiness, setReadiness] = useState(dashboard.readiness || null);
  const [error, setError] = useState('');
  const refresh = async () => {
    setError('');
    try { setReadiness((await api.careerReadiness()).readiness); } catch (requestError) { setError(requestError.message); }
  };
  useEffect(() => { refresh(); }, []);
  const score = readiness?.overall || 0;
  return <div className="content readiness-page">
    <section className="page-heading"><div className="eyebrow">PLACEMENT READINESS</div><h1>Your career signal</h1><p>A live view of your profile evidence, practice, and preparation progress.</p></section>
    {error && <p className="form-error" role="alert">{error}</p>}
    <section className="panel readiness-summary"><div className="readiness-total"><span>OVERALL</span><strong>{score}<small>/100</small></strong><span>{score >= 75 ? 'Strong momentum' : score >= 50 ? 'Building readiness' : 'Start with one focused improvement'}</span></div><div className="readiness-guidance"><div><small>STRONGEST AREA</small><b>{readiness?.strongest_area || 'Add profile evidence'}</b></div><div><small>WEAKEST AREA</small><b>{readiness?.weakest_area || 'Add profile evidence'}</b></div><div className="next-action"><small>RECOMMENDED NEXT ACTION</small><b>{readiness?.next_action || 'Add your skills and resume to get a personalized score.'}</b><button className="text-btn" onClick={() => onNavigate?.(readiness?.weakest_area === 'Interview' ? 'Interview prep' : 'Skill Gap Analyzer')}>Open next step <ArrowRight size={14} /></button></div></div><button className="icon-btn" onClick={refresh} aria-label="Refresh readiness score" title="Refresh readiness score"><RefreshCw size={17} /></button></section>
    <section className="readiness-score-grid">{scoreLabels.map(([key, label]) => { const value = readiness?.[key] || 0; return <article className="panel readiness-score" key={key}><div><small>{label}</small><strong>{value}%</strong></div><div className="progress-bar"><i style={{ width: `${value}%` }} /></div></article>; })}</section>
    <section className="panel readiness-improvements"><div className="panel-head"><div><div className="eyebrow">HIGHEST-IMPACT GAPS</div><h2>What to improve next</h2></div></div>{readiness?.improvements?.length ? readiness.improvements.map((item, index) => <article className="readiness-improvement" key={item.area}><span>0{index + 1}</span><div><b>{item.area} · {item.score}%</b><p>{item.action}</p></div></article>) : <p className="empty">Complete your profile, add a resume, or practice an interview to build your readiness signal.</p>}</section>
  </div>;
}
