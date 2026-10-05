import React, { useState } from 'react';
import { ArrowUpRight, Copy, Sparkles } from 'lucide-react';
import { api } from '../services/api';

export default function ResumeBulletImprover() {
  const [bullet, setBullet] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const submit = async (event) => { event.preventDefault(); setLoading(true); setError(''); setResult(null); try { setResult((await api.improveResumeBullet(bullet)).result); } catch (requestError) { setError(requestError.message); } finally { setLoading(false); } };
  const copy = async (value) => { try { await navigator.clipboard.writeText(value); } catch { setError('Clipboard access is unavailable in this browser.'); } };
  return <div className="content bullet-page"><section className="page-heading"><div className="eyebrow">RESUME LANGUAGE TOOL</div><h1>Resume Bullet Improver</h1><p>Make a real contribution clearer without adding claims you did not make.</p></section><section className="tool-grid"><section className="panel"><div className="panel-head"><div><div className="eyebrow">YOUR ORIGINAL</div><h2>Paste one bullet</h2></div></div><form onSubmit={submit}><label>Resume bullet<textarea value={bullet} onChange={(event) => setBullet(event.target.value)} maxLength={1200} placeholder="Made a website using HTML CSS JavaScript." required /></label><small className="bullet-counter">{bullet.length}/1,200</small>{error && <p className="form-error" role="alert">{error}</p>}<button className="primary" disabled={loading || !bullet.trim()}>{loading ? 'Improving...' : 'Improve bullet'} <Sparkles size={16} /></button></form></section><section className="panel bullet-results"><div className="panel-head"><div><div className="eyebrow">REWRITES</div><h2>Clearer, still yours</h2></div></div>{result ? <><Rewrite title="Professional version" text={result.professional} onCopy={copy} /><Rewrite title="ATS-friendly version" text={result.ats_friendly} onCopy={copy} /><Rewrite title="Short version" text={result.short} onCopy={copy} /><div className="bullet-explanation"><h3>What changed</h3><ul>{result.improvements.map((item) => <li key={item}>{item}</li>)}</ul></div></> : <p className="empty">Your three versions and a brief explanation will appear here.</p>}</section></section></div>;
}

function Rewrite({ title, text, onCopy }) { return <article className="rewrite-version"><div><b>{title}</b><button className="icon-btn" title={`Copy ${title.toLowerCase()}`} aria-label={`Copy ${title.toLowerCase()}`} onClick={() => onCopy(text)}><Copy size={14} /></button></div><p>{text}</p></article>; }
