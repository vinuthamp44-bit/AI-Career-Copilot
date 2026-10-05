import React, { useState } from 'react';
import { ArrowUpRight } from 'lucide-react';
import { api } from '../services/api';

export default function JobDescriptionAnalyzer() {
  const [description, setDescription] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const analyze = async (event) => { event.preventDefault(); setLoading(true); setError(''); try { setAnalysis((await api.analyzeJobDescription(description)).analysis); } catch (requestError) { setError(requestError.message); } finally { setLoading(false); } };
  return <div className="content jd-page"><section className="page-heading"><div className="eyebrow">ROLE INTELLIGENCE</div><h1>Job Description Analyzer</h1><p>Identify role requirements and compare them with your saved resume and profile skills.</p></section><section className="tool-grid"><section className="panel"><div className="panel-head"><div><div className="eyebrow">JOB DESCRIPTION</div><h2>Paste a role description</h2></div></div><form onSubmit={analyze}><label>Job description<textarea value={description} onChange={(event) => setDescription(event.target.value)} maxLength={30000} placeholder="Paste the complete job description..." required /></label>{error && <p className="form-error" role="alert">{error}</p>}<button className="primary" disabled={loading || !description.trim()}>{loading ? 'Analyzing...' : 'Analyze description'} <ArrowUpRight size={16} /></button></form></section>{analysis ? <JDReport analysis={analysis} /> : <section className="panel"><div className="panel-head"><div><div className="eyebrow">PROFILE MATCH</div><h2>Requirements and fit</h2></div></div><p className="empty">Your role requirements, matched skills, and gaps will appear here.</p></section>}</section></div>;
}

function JDReport({ analysis }) {
  const lists = [['Required technical skills', analysis.required_technical_skills], ['Preferred skills', analysis.preferred_skills], ['Soft skills', analysis.soft_skills], ['Responsibilities', analysis.responsibilities], ['Experience requirements', analysis.experience_requirements], ['Education requirements', analysis.education_requirements], ['Important ATS keywords', analysis.ats_keywords]];
  return <section className="panel jd-report"><div className="panel-head"><div><div className="eyebrow">PROFILE MATCH</div><h2>Job fit analysis</h2></div><strong className="jd-score">{analysis.match_score}%</strong></div><div className="jd-match-lists"><List title="Matched skills" items={analysis.matched_skills} /><List title="Missing skills" items={analysis.missing_skills} /><List title="Recommended skills" items={analysis.recommended_skills} /></div><div className="jd-facts"><div><small>Location</small><b>{analysis.location || 'Not listed'}</b></div><div><small>Salary / package</small><b>{analysis.salary || 'Not listed'}</b></div></div>{lists.map(([title, items]) => <List key={title} title={title} items={items} />)}</section>;
}
function List({ title, items = [] }) { return <div className="jd-list"><h3>{title}</h3>{items.length ? <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="empty">None identified.</p>}</div>; }
