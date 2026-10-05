import React, { useEffect, useState } from 'react';
import { BriefcaseBusiness, Pencil, Plus, Search, Trash2, X } from 'lucide-react';
import { api } from '../services/api';

const statuses = ['Saved', 'Applied', 'Assessment', 'GD', 'Interview', 'Selected', 'Rejected'];
const blank = { company: '', role: '', location: '', package: '', application_date: new Date().toISOString().slice(0, 10), deadline: '', description: '', notes: '', status: 'Saved' };

export default function JobApplications() {
  const [applications, setApplications] = useState([]);
  const [counts, setCounts] = useState({});
  const [total, setTotal] = useState(0);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('All');
  const [form, setForm] = useState(blank);
  const [editing, setEditing] = useState(null);
  const [selected, setSelected] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const load = async () => {
    const params = new URLSearchParams();
    if (query.trim()) params.set('q', query.trim());
    if (filter !== 'All') params.set('status', filter);
    const data = await api.applications(params.toString());
    setApplications(data.applications); setCounts(data.counts); setTotal(data.total);
  };
  useEffect(() => { load().catch((requestError) => setError(requestError.message)); }, [query, filter]);
  const update = (key) => (event) => setForm((current) => ({ ...current, [key]: event.target.value }));
  const closeForm = () => { setShowForm(false); setEditing(null); setForm(blank); setError(''); };
  const save = async (event) => {
    event.preventDefault(); setLoading(true); setError('');
    try { if (editing) await api.updateApplication(editing, form); else await api.createApplication(form); closeForm(); await load(); }
    catch (requestError) { setError(requestError.message); } finally { setLoading(false); }
  };
  const edit = (application) => { setSelected(null); setEditing(application.id); setForm({ ...application }); setShowForm(true); };
  const remove = async (application) => { if (!window.confirm(`Delete the ${application.role} application at ${application.company}?`)) return; try { await api.deleteApplication(application.id); if (selected?.id === application.id) setSelected(null); await load(); } catch (requestError) { setError(requestError.message); } };
  const setStatus = async (application, status) => { try { await api.updateApplication(application.id, { status }); await load(); if (selected?.id === application.id) setSelected({ ...application, status }); } catch (requestError) { setError(requestError.message); } };

  return <div className="content applications-page">
    <section className="page-heading"><div className="eyebrow">APPLICATION PIPELINE</div><h1>My Applications</h1><p>Keep every opportunity, deadline, and next step in one place.</p></section>
    {error && <p className="form-error" role="alert">{error}</p>}
    <section className="application-counts">{[['All', total], ...statuses.map((status) => [status, counts[status] || 0])].map(([status, count]) => <button className={filter === status ? 'application-count active' : 'application-count'} key={status} onClick={() => setFilter(status)}><small>{status}</small><strong>{count}</strong></button>)}</section>
    <section className="panel application-list"><div className="application-toolbar"><label className="application-search"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search company, role, or location" /></label><button className="primary" onClick={() => { setForm(blank); setEditing(null); setShowForm(true); }}><Plus size={16} /> Add application</button></div>
      {showForm && <form className="application-form" onSubmit={save}><div className="application-form-head"><b>{editing ? 'Edit application' : 'New application'}</b><button className="icon-btn" type="button" onClick={closeForm} aria-label="Close form"><X size={17} /></button></div><label>Company<input required value={form.company} onChange={update('company')} /></label><label>Job role<input required value={form.role} onChange={update('role')} /></label><label>Location<input value={form.location} onChange={update('location')} /></label><label>Package / salary<input value={form.package} onChange={update('package')} /></label><label>Application date<input type="date" value={form.application_date} onChange={update('application_date')} /></label><label>Deadline<input type="date" value={form.deadline} onChange={update('deadline')} /></label><label>Status<select value={form.status} onChange={update('status')}>{statuses.map((status) => <option key={status}>{status}</option>)}</select></label><label className="application-wide">Job description<textarea value={form.description} onChange={update('description')} /></label><label className="application-wide">Notes<textarea value={form.notes} onChange={update('notes')} /></label><div className="application-wide"><button className="primary" disabled={loading}>{loading ? 'Saving...' : editing ? 'Save changes' : 'Add application'}</button></div></form>}
      <div className="application-table-wrap"><table className="application-table"><thead><tr><th>Company / role</th><th>Location</th><th>Applied</th><th>Status</th><th>Actions</th></tr></thead><tbody>{applications.map((application) => <tr key={application.id}><td><button className="application-link" onClick={() => setSelected(application)}><b>{application.company}</b><span>{application.role}</span></button></td><td>{application.location || '—'}</td><td>{application.application_date || '—'}</td><td><select aria-label={`Status for ${application.company}`} value={application.status} onChange={(event) => setStatus(application, event.target.value)}>{statuses.map((status) => <option key={status}>{status}</option>)}</select></td><td><div className="application-actions"><button className="icon-btn" title="Edit application" aria-label="Edit application" onClick={() => edit(application)}><Pencil size={15} /></button><button className="icon-btn" title="View details" aria-label="View details" onClick={() => setSelected(application)}><BriefcaseBusiness size={15} /></button><button className="icon-btn danger" title="Delete application" aria-label="Delete application" onClick={() => remove(application)}><Trash2 size={15} /></button></div></td></tr>)}</tbody></table>{!applications.length && <p className="empty">No applications match this view. Add an opportunity to start tracking.</p>}</div>
    </section>
    {selected && <section className="panel application-detail"><div className="panel-head"><div><div className="eyebrow">APPLICATION DETAILS</div><h2>{selected.company} · {selected.role}</h2></div><button className="icon-btn" onClick={() => setSelected(null)} aria-label="Close details"><X size={17} /></button></div><div className="application-detail-grid"><div><small>Location</small><b>{selected.location || 'Not specified'}</b></div><div><small>Package</small><b>{selected.package || 'Not specified'}</b></div><div><small>Application date</small><b>{selected.application_date || 'Not specified'}</b></div><div><small>Deadline</small><b>{selected.deadline || 'Not specified'}</b></div></div><h3>Job description</h3><p>{selected.description || 'No description added.'}</p><h3>Notes</h3><p>{selected.notes || 'No notes added.'}</p></section>}
  </div>;
}
