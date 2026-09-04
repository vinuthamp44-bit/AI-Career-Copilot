import React, { useState } from 'react';
import { ArrowUpRight, FileText, Upload } from 'lucide-react';
import { api } from '../services/api';

function ErrorMessage({ children }) { return children ? <p className="form-error">{children}</p> : null; }

export default function ATSCompatibility() {
  const [file, setFile] = useState(null);
  const [description, setDescription] = useState('');
  const [role, setRole] = useState('');
  const [result, setResult] = useState(null);
  const [state, setState] = useState('idle');
  const [error, setError] = useState('');

  const analyze = async (event) => {
    event.preventDefault();
    if (!file) return setError('Please upload your resume.');
    if (!description.trim()) return setError('Please enter a job description.');
    if (file.type !== 'application/pdf' || file.size > 5 * 1024 * 1024) return setError('Please upload a PDF resume smaller than 5 MB.');
    setState('uploading'); setError(''); setResult(null);
    try { setState('analyzing'); setResult(await api.atsAnalyze(file, description, role)); setState('success'); } catch (err) { setState('error'); setError(err.message); }
  };

  return <div className="content"><section className="page-heading"><div className="eyebrow">APPLICATION READINESS</div><h1>ATS compatibility</h1><p>Compare your resume with a specific job description before you apply.</p></section><section className="tool-grid"><section className="panel"><div className="panel-head"><div><div className="eyebrow">INPUTS</div><h2>Analyze ATS fit</h2></div></div><form onSubmit={analyze}><label>Target role <span className="optional">optional</span><input value={role} onChange={(event) => setRole(event.target.value)} placeholder="Frontend Developer" /></label><label className="upload-box"><input type="file" accept="application/pdf" onChange={(event) => setFile(event.target.files[0] || null)} /><span className="upload-label"><Upload size={22} /><b>{file ? file.name : 'Upload your resume PDF'}</b><small>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB selected` : 'PDF only, up to 5 MB'}</small></span></label><label>Job description<textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Paste the complete job description here..." /></label><ErrorMessage>{error}</ErrorMessage><button className="primary" disabled={state === 'uploading' || state === 'analyzing'}>{state === 'uploading' ? 'Uploading...' : state === 'analyzing' ? 'Analyzing...' : 'Analyze ATS'} <ArrowUpRight size={16} /></button>{state === 'success' && <p className="success-message">Analysis complete. Your results are ready.</p>}</form></section>{result ? <Results result={result} /> : <section className="panel"><div className="panel-head"><div><div className="eyebrow">RESULTS</div><h2>Your ATS report</h2></div></div><p className="empty">Upload your resume and paste a job description to see compatibility results here.</p></section>}</section></div>;
}

function Results({ result }) { return <section className="panel ats-report"><div className="panel-head"><div><div className="eyebrow">RESULTS</div><h2>ATS compatibility score</h2></div></div><div className="ats-score"><strong>{result.score}</strong><span>/ 100</span></div><ReportList title="Matched keywords" items={result.matching_keywords} /><ReportList title="Missing keywords" items={result.missing_keywords} /><ReportList title="Matched skills" items={result.matched_skills} /><ReportList title="Missing skills" items={result.missing_skills} /><ReportList title="Resume strengths" items={result.resume_strengths} /><ReportList title="Resume weaknesses" items={result.resume_weaknesses} /><ReportList title="ATS recommendations" items={result.recommendations} /></section>; }
function ReportList({ title, items = [] }) { return <div className="report-list"><h3>{title}</h3>{items.length ? <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul> : <p className="empty">None found.</p>}</div>; }