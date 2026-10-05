import React, { useEffect, useState } from 'react';
import { ArrowRight, Check, ChevronLeft, Eye, EyeOff, FileUp, LockKeyhole, Search, Sparkles, UserRound, X } from 'lucide-react';
import { api, auth } from '../services/api';

const roles = ['Software Developer', 'Full Stack Developer', 'Data Analyst', 'AI/ML Engineer', 'Java Developer', 'Python Developer', 'UI/UX Designer', 'Other'];
const skills = ['Python', 'Java', 'JavaScript', 'React', 'Node.js', 'SQL', 'MySQL', 'MongoDB', 'Git', 'AWS', 'Machine Learning'];
const icons = [Sparkles, ArrowRight, Search, UserRound, LockKeyhole, FileUp, UserRound, Sparkles];

export default function AuthFlow({ onboarding = false, token, onAuthenticated, onComplete, initialError = '' }) {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm: '' });
  const [error, setError] = useState(initialError);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [step, setStep] = useState(0);
  const [profile, setProfile] = useState({ name: '', degree: '', college: '', graduation_year: '', target_role: '', skills: [] });
  const [customRole, setCustomRole] = useState('');
  const [skillQuery, setSkillQuery] = useState('');
  const [file, setFile] = useState(null);
  const [saved, setSaved] = useState(false);
  const [googleReady, setGoogleReady] = useState(false);
  const [resetToken] = useState(() => new URLSearchParams(window.location.search).get('reset_token') || '');

  useEffect(() => {
    if (onboarding) return undefined;
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    if (!clientId) return undefined;
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.onload = () => {
      window.google?.accounts.id.initialize({ client_id: clientId, auto_select: false, cancel_on_tap_outside: true, callback: async ({ credential }) => {
        setLoading(true); setError('');
        try { const result = await auth.google(credential); setError('Signed in successfully.'); onAuthenticated(result.token, result.new_user); } catch (requestError) { setError(requestError.message); } finally { setLoading(false); }
      } });
      setGoogleReady(true);
    };
    script.onerror = () => setError('Unable to connect. Please check your internet connection.');
    document.head.appendChild(script);
    return () => { script.remove(); setGoogleReady(false); };
  }, [onboarding, onAuthenticated]);

  const signInWithGoogle = () => {
    if (loading) return;
    if (!import.meta.env.VITE_GOOGLE_CLIENT_ID) return setError('Google sign-in is not configured. Add VITE_GOOGLE_CLIENT_ID to frontend/.env and restart Vite.');
    if (!googleReady || !window.google?.accounts?.id) return setError('Google sign-in is still loading. Please try again.');
    setError('');
    window.google.accounts.id.prompt((notification) => {
      if (notification.isSkippedMoment?.() || notification.isDismissedMoment?.()) setError('Google sign-in was cancelled.');
    });
  };

  useEffect(() => {
    if (onboarding) return undefined;
    const button = document.querySelector('.social-button');
    if (!button) return undefined;
    button.addEventListener('click', signInWithGoogle);
    return () => button.removeEventListener('click', signInWithGoogle);
  }, [onboarding, googleReady, loading]);

  useEffect(() => {
    if (onboarding || mode !== 'login') return undefined;
    const resetButton = document.querySelector('.text-link');
    if (!resetButton) return undefined;
    const showResetStatus = () => { setMode('forgot'); setError(''); };
    resetButton.addEventListener('click', showResetStatus);
    return () => resetButton.removeEventListener('click', showResetStatus);
  }, [onboarding, mode]);

  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const setProfileValue = (key, value) => setProfile((current) => ({ ...current, [key]: value }));
  const emailValid = !form.email || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email);
  const passwordStrong = form.password.length >= 8 && /[A-Z]/.test(form.password) && /\d/.test(form.password);

  const submitAuth = async (event) => {
    event.preventDefault(); setError('');
    if (mode === 'register' && form.password !== form.confirm) return setError('Passwords do not match.');
    if (mode === 'register' && !passwordStrong) return setError('Use 8+ characters with a number and uppercase letter.');
    setLoading(true);
    try {
      const result = mode === 'register' ? await auth.register(form) : await auth.login({ email: form.email, password: form.password });
      if (mode === 'register') setProfileValue('name', form.name);
      onAuthenticated(result.token, mode === 'register');
    } catch (requestError) { setError(requestError.message); } finally { setLoading(false); }
  };

  const finishStep = async (skipResume = false) => {
    setError('');
    if (step === 0 && (!profile.name || !profile.degree || !profile.college || !profile.graduation_year)) return setError('Complete the highlighted fields to continue.');
    if (step === 1 && !profile.target_role) return setError('Choose a target role to continue.');
    if (step === 2 && !profile.skills.length) return setError('Choose at least one skill to continue.');
    setLoading(true);
    try {
      if (step === 3 && file && !skipResume) {
        if (file.type !== 'application/pdf' || file.size > 5 * 1024 * 1024) throw new Error('Please upload a valid PDF under 5 MB.');
        await api.resume(file);
      }
      if (step === 3 || !file) await auth.saveProfile({ ...profile, target_role: profile.target_role === 'Other' ? customRole : profile.target_role, completed: step === 3 });
      if (step < 3) setStep(step + 1); else { setSaved(true); setTimeout(onComplete, 700); }
    } catch (requestError) { setError(requestError.message); } finally { setLoading(false); }
  };

  if (onboarding) return <Onboarding step={step} profile={profile} file={file} setFile={setFile} error={error} loading={loading} customRole={customRole} setCustomRole={setCustomRole} skillQuery={skillQuery} setSkillQuery={setSkillQuery} setProfileValue={setProfileValue} finishStep={finishStep} saved={saved} onComplete={onComplete} onBack={() => setStep(Math.max(0, step - 1))} />;
  if (resetToken) return <PasswordReset token={resetToken} />;
  if (mode === 'forgot') return <ForgotPassword onBack={() => { setMode('login'); setError(''); }} />;
  return <div className="auth-page modern-auth"><section className="auth-art"><div className="auth-brand"><AuthBrand /></div><div className="auth-orbit"><span className="orbit-core"><Sparkles size={28} /></span><span className="orbit-line line-one" /><span className="orbit-line line-two" /><Stat label="ATS Score" value="86%" className="stat-one" /><Stat label="Skill Match" value="92%" className="stat-two" /><Stat label="Career Readiness" value="78%" className="stat-three" /></div><div className="art-copy"><p className="auth-kicker">CAREER INTELLIGENCE, REIMAGINED</p><h1>Your AI-powered path from student to <em>job-ready.</em></h1><p>Analyze. Improve. Prepare. Get hired.</p></div></section><section className="auth-form"><div className="auth-inner"><div className="mobile-brand"><AuthBrand /></div><div className="form-heading"><p className="auth-kicker">{mode === 'register' ? 'YOUR NEXT CHAPTER' : 'WELCOME BACK'}</p><h2>{mode === 'register' ? 'Build your career profile' : 'Welcome back'}</h2><p>{mode === 'register' ? "Let's personalize your AI career journey." : 'Continue your journey toward your dream career.'}</p></div><form onSubmit={submitAuth} noValidate>{mode === 'register' && <Field label="Full name" value={form.name} onChange={(value) => update('name', value)} placeholder="Vinu Kumar" icon={UserRound} />}{mode === 'register' && <p className="field-hint">Use the name you want on your career profile.</p>}<Field label="Email" value={form.email} onChange={(value) => update('email', value)} placeholder="you@example.com" type="email" icon={Search} error={!emailValid ? 'Invalid email' : ''} /> <div className="password-field"><Field label="Password" value={form.password} onChange={(value) => update('password', value)} placeholder="8+ characters" type={showPassword ? 'text' : 'password'} icon={LockKeyhole} /><button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Hide password' : 'Show password'}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div>{mode === 'register' && <><div className="password-meter"><span className={passwordStrong ? 'strong' : form.password ? 'partial' : ''} /><small>{passwordStrong ? 'Strong password' : 'Use 8+ characters, a number and uppercase letter'}</small></div><Field label="Confirm password" value={form.confirm} onChange={(value) => update('confirm', value)} placeholder="Repeat your password" type={showPassword ? 'text' : 'password'} icon={LockKeyhole} error={form.confirm && form.confirm !== form.password ? 'Passwords do not match' : ''} /><label className="check-row"><input type="checkbox" required /> <span>I agree to the <u>terms</u> and <u>privacy policy</u>.</span></label></>}{mode === 'login' && <div className="form-options"><label className="check-row"><input type="checkbox" /> <span>Remember me</span></label><button type="button" className="text-link">Forgot password?</button></div>}{error && <p className="form-error" role="alert">{error}</p>}<button className="primary full auth-submit" disabled={loading}>{loading ? (mode === 'register' ? 'Creating account...' : 'Signing you in...') : mode === 'register' ? 'Create account' : 'Sign in'} <ArrowRight size={17} /></button></form><div className="auth-divider"><span>or continue with</span></div><button className="social-button" type="button" disabled={loading}><span className="google-mark" aria-hidden="true">G</span> {loading ? 'Connecting to Google...' : 'Continue with Google'}</button><p className="switch-auth">{mode === 'register' ? 'Already have an account?' : "Don't have an account?"} <button type="button" onClick={() => { setMode(mode === 'register' ? 'login' : 'register'); setError(''); }}>{mode === 'register' ? 'Sign in' : 'Create one'}</button></p></div></section></div>;
}

function Onboarding({ step, profile, file, setFile, error, loading, customRole, setCustomRole, skillQuery, setSkillQuery, setProfileValue, finishStep, saved, onComplete, onBack }) {
  const titles = ['Let\'s get to know you', 'Where do you want to go?', 'What can you already do?', "Let's understand your experience"];
  if (saved) return <div className="onboarding-page"><main className="onboarding-main welcome-complete"><div className="success-check"><Check size={22} /></div><p className="auth-kicker">PROFILE READY</p><h1>You&apos;re all set, {profile.name.split(' ')[0] || 'there'}.</h1><p className="onboarding-sub">Your career copilot is ready.</p><div className="welcome-summary"><div><small>Target role</small><strong>{profile.target_role === 'Other' ? customRole : profile.target_role}</strong></div><div><small>Skills</small><strong>{profile.skills.join(' • ') || 'Getting started'}</strong></div><div><small>Profile</small><strong>78% complete</strong></div></div><button className="primary" type="button" onClick={onComplete}>Build my career dashboard <ArrowRight size={17} /></button></main></div>;
  return <div className="onboarding-page"><header className="onboarding-header"><AuthBrand /><span>Step {String(step + 1).padStart(2, '0')} of 04</span></header><main className="onboarding-main"><div className="progress-steps">{['About You', 'Career Goal', 'Skills', 'Resume'].map((label, index) => <div className={index <= step ? 'progress-step active' : 'progress-step'} key={label}><span>{index < step ? <Check size={14} /> : `0${index + 1}`}</span><small>{label}</small></div>)}</div><section className="onboarding-card"><p className="auth-kicker">YOUR CAREER PROFILE</p><h1>{saved ? "You're all set." : titles[step]}</h1><p className="onboarding-sub">{saved ? 'Your career copilot is ready.' : ['A few details help us make every recommendation more relevant.', 'Choose a direction. You can always change it later.', 'Add the tools you know today. There is no wrong starting point.', 'A resume helps us understand your experience, but it is never required.'][step]}</p>{step === 0 && <div className="onboard-grid"><Field label="Name" value={profile.name} onChange={(value) => setProfileValue('name', value)} placeholder="Your full name" /><Field label="Degree" value={profile.degree} onChange={(value) => setProfileValue('degree', value)} placeholder="B.Tech Computer Science" /><Field label="College / university" value={profile.college} onChange={(value) => setProfileValue('college', value)} placeholder="Your university" /><Field label="Graduation year" value={profile.graduation_year} onChange={(value) => setProfileValue('graduation_year', value)} placeholder="2027" type="number" /></div>}{step === 1 && <div className="role-grid">{roles.map((role, index) => { const Icon = icons[index]; return <button type="button" className={profile.target_role === role ? 'role-card selected' : 'role-card'} onClick={() => setProfileValue('target_role', role)} key={role}><Icon size={18} /><span>{role}</span>{profile.target_role === role && <Check size={15} />}</button>; })}</div>}{step === 1 && profile.target_role === 'Other' && <input className="standalone-input" value={customRole} onChange={(event) => setCustomRole(event.target.value)} placeholder="Type your target role" aria-label="Custom target role" />}{step === 2 && <><div className="skill-search"><Search size={17} /><input value={skillQuery} onChange={(event) => setSkillQuery(event.target.value)} placeholder="Search skills" aria-label="Search skills" /></div><div className="skill-options">{skills.filter((skill) => skill.toLowerCase().includes(skillQuery.toLowerCase())).map((skill) => <button type="button" className={profile.skills.includes(skill) ? 'skill-option selected' : 'skill-option'} onClick={() => setProfileValue('skills', profile.skills.includes(skill) ? profile.skills.filter((item) => item !== skill) : [...profile.skills, skill])} key={skill}>{skill}{profile.skills.includes(skill) ? <Check size={14} /> : <span>+</span>}</button>)}</div><div className="selected-skills">{profile.skills.map((skill) => <span key={skill}>{skill}<button type="button" onClick={() => setProfileValue('skills', profile.skills.filter((item) => item !== skill))} aria-label={`Remove ${skill}`}><X size={12} /></button></span>)}</div></>}{step === 3 && <ResumeInput file={file} setFile={setFile} />}{error && <p className="form-error" role="alert">{error}</p>} {!saved && <div className="onboarding-actions">{step > 0 && <button className="back-button" type="button" onClick={onBack}><ChevronLeft size={17} /> Back</button>}<button className="primary" type="button" onClick={finishStep} disabled={loading}>{loading ? step === 3 ? 'Uploading...' : 'Saving...' : step === 3 ? 'Finish profile' : 'Continue'} <ArrowRight size={17} /></button>{step === 3 && <button className="skip-button" type="button" onClick={() => { setFile(null); finishStep(); }}>Skip for now</button>}</div>}</section></main></div>;
}

function ResumeInput({ file, setFile }) { return <label className={file ? 'resume-drop has-file' : 'resume-drop'}><input type="file" accept="application/pdf" onChange={(event) => setFile(event.target.files[0])} /><FileUp size={28} /><strong>{file ? file.name : 'Drop your resume here'}</strong><span>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB · PDF` : 'PDF only, up to 5 MB'}</span>{file && <button type="button" onClick={(event) => { event.preventDefault(); setFile(null); }}>Remove and replace</button>}</label>; }
function Field({ label, value, onChange, placeholder, type = 'text', icon: Icon = UserRound, error }) { return <label className="auth-field"><span>{label}</span><div><Icon size={16} /><input type={type} value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} required={label !== 'Degree' && label !== 'College / university' && label !== 'Graduation year'} aria-invalid={Boolean(error)} />{error && <small className="inline-error">{error}</small>}</div></label>; }
function ForgotPassword({ onBack }) {
  const [email, setEmail] = useState(''); const [message, setMessage] = useState(''); const [resetUrl, setResetUrl] = useState(''); const [error, setError] = useState(''); const [loading, setLoading] = useState(false);
  const submit = async (event) => { event.preventDefault(); setLoading(true); setError(''); setMessage(''); try { const result = await auth.forgotPassword(email); setMessage(result.message); setResetUrl(result.reset_url || ''); } catch (requestError) { setError(requestError.message); } finally { setLoading(false); } };
  return <div className="auth-page modern-auth"><section className="auth-art"><div className="auth-brand"><AuthBrand /></div><div className="art-copy"><p className="auth-kicker">ACCOUNT ACCESS</p><h1>Find your way back to your <em>career path.</em></h1><p>We will help you get back to building your next move.</p></div></section><section className="auth-form"><div className="auth-inner"><div className="mobile-brand"><AuthBrand /></div><div className="form-heading"><p className="auth-kicker">RESET PASSWORD</p><h2>Forgot your password?</h2><p>Enter your account email and we will send reset instructions.</p></div><form onSubmit={submit}><Field label="Email" value={email} onChange={setEmail} placeholder="you@example.com" type="email" icon={Search} />{error && <p className="form-error" role="alert">{error}</p>}{message && <p className="form-success" role="status">{message}</p>}{resetUrl && <a className="dev-reset-link" href={resetUrl}>Open reset page</a>}<button className="primary full auth-submit" disabled={loading}>{loading ? 'Sending instructions...' : 'Send reset instructions'} <ArrowRight size={17} /></button></form><p className="switch-auth"><button type="button" onClick={onBack}><ChevronLeft size={14} /> Back to sign in</button></p></div></section></div>;
}

function PasswordReset({ token }) {
  const [password, setPassword] = useState(''); const [confirm, setConfirm] = useState(''); const [message, setMessage] = useState(''); const [error, setError] = useState(''); const [loading, setLoading] = useState(false);
  const submit = async (event) => { event.preventDefault(); if (password !== confirm) return setError('Passwords do not match.'); setLoading(true); setError(''); try { const result = await auth.resetPassword(token, password); setMessage(result.message); window.history.replaceState({}, '', '/'); } catch (requestError) { setError(requestError.message); } finally { setLoading(false); } };
  return <div className="auth-page modern-auth"><section className="auth-art"><div className="auth-brand"><AuthBrand /></div><div className="art-copy"><p className="auth-kicker">A FRESH START</p><h1>Make your next move with a <em>clear head.</em></h1><p>Your career copilot is ready when you are.</p></div></section><section className="auth-form"><div className="auth-inner"><div className="mobile-brand"><AuthBrand /></div><div className="form-heading"><p className="auth-kicker">NEW PASSWORD</p><h2>Set a new password</h2><p>Choose a strong password for your account.</p></div><form onSubmit={submit}><Field label="New password" value={password} onChange={setPassword} placeholder="8+ characters" type="password" icon={LockKeyhole} /><Field label="Confirm password" value={confirm} onChange={setConfirm} placeholder="Repeat your password" type="password" icon={LockKeyhole} />{error && <p className="form-error" role="alert">{error}</p>}{message && <p className="form-success" role="status">{message} <a href="/">Sign in</a></p>}<button className="primary full auth-submit" disabled={loading || Boolean(message)}>{loading ? 'Updating password...' : 'Update password'} <ArrowRight size={17} /></button></form></div></section></div>;
}

function AuthBrand() { return <div className="auth-brand-lockup"><span className="brand-mark"><Sparkles size={17} /></span><strong>career<span>copilot</span></strong></div>; }
function Stat({ label, value, className }) { return <div className={`floating-stat ${className}`}><span>{label}</span><strong>{value}</strong></div>; }
