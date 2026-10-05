import React, { useEffect, useRef, useState } from 'react';
import { Mic, MicOff, RotateCcw, Send } from 'lucide-react';
import { api } from '../services/api';

export default function GDPractice() {
  const [topics, setTopics] = useState([]);
  const [topic, setTopic] = useState('');
  const [position, setPosition] = useState('FOR');
  const [phase, setPhase] = useState('setup');
  const [seconds, setSeconds] = useState(60);
  const [prepLength, setPrepLength] = useState(60);
  const [speakLength, setSpeakLength] = useState(120);
  const [response, setResponse] = useState('');
  const [result, setResult] = useState(null);
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);
  const [error, setError] = useState('');
  useEffect(() => { api.gdTopics().then((data) => { setTopics(data.topics); setTopic(data.topics[0] || ''); }).catch((requestError) => setError(requestError.message)); }, []);
  useEffect(() => {
    if (phase !== 'preparation' && phase !== 'speaking') return undefined;
    const timer = window.setInterval(() => setSeconds((remaining) => {
      if (remaining <= 1) { window.clearInterval(timer); setPhase((current) => current === 'preparation' ? 'ready' : 'finished'); return 0; }
      return remaining - 1;
    }), 1000);
    return () => window.clearInterval(timer);
  }, [phase]);
  const begin = () => { setError(''); setResult(null); setResponse(''); setPhase('preparation'); setSeconds(prepLength); };
  const startSpeaking = () => { setPhase('speaking'); setSeconds(speakLength); };
  const randomTopic = async () => { try { setTopic((await api.randomGdTopic()).topic); } catch (requestError) { setError(requestError.message); } };
  const record = () => {
    if (listening) { recognitionRef.current?.stop(); return; }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return setError('Speech recognition is unavailable in this browser. Type your response instead.');
    const recognition = new SpeechRecognition(); recognition.lang = 'en-US'; recognition.continuous = true; recognition.interimResults = false;
    recognition.onstart = () => setListening(true); recognition.onend = () => setListening(false); recognition.onerror = () => { setListening(false); setError('Could not start speech recognition. You can type your response instead.'); };
    recognition.onresult = (event) => setResponse((current) => `${current} ${event.results[event.results.length - 1][0].transcript}`.trim()); recognitionRef.current = recognition; recognition.start();
  };
  const submit = async () => { setError(''); recognitionRef.current?.stop(); try { setResult(await api.evaluateGd({ topic, position, response })); setPhase('result'); setListening(false); } catch (requestError) { setError(requestError.message); } };
  const reset = () => { setPhase('setup'); setResult(null); setResponse(''); setSeconds(prepLength); setError(''); };
  const clock = `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;

  return <div className="content gd-page"><section className="page-heading"><div className="eyebrow">GROUP DISCUSSION STUDIO</div><h1>GD Practice</h1><p>Prepare a clear position, speak to the clock, and review your response.</p></section>{error && <p className="form-error" role="alert">{error}</p>}
    {phase === 'setup' && <section className="panel gd-setup"><label>Discussion topic<select value={topic} onChange={(event) => setTopic(event.target.value)}>{topics.map((item) => <option key={item}>{item}</option>)}</select></label><button className="secondary" type="button" onClick={randomTopic}>Generate random topic</button><fieldset className="gd-position"><legend>Your position</legend>{['FOR', 'AGAINST'].map((item) => <button type="button" className={position === item ? 'selected' : ''} key={item} onClick={() => setPosition(item)}>{item}</button>)}</fieldset><div className="gd-timer-settings"><label>Preparation time<select value={prepLength} onChange={(event) => setPrepLength(Number(event.target.value))}><option value="30">30 seconds</option><option value="60">1 minute</option><option value="90">1 minute 30 seconds</option><option value="120">2 minutes</option></select></label><label>Speaking time<select value={speakLength} onChange={(event) => setSpeakLength(Number(event.target.value))}><option value="60">1 minute</option><option value="120">2 minutes</option><option value="180">3 minutes</option><option value="300">5 minutes</option></select></label></div><button className="primary" onClick={begin} disabled={!topic}>Start preparation</button></section>}
    {(phase === 'preparation' || phase === 'ready' || phase === 'speaking' || phase === 'finished') && <section className="gd-session"><article className="panel gd-clock"><div className="eyebrow">{phase === 'preparation' ? 'PREPARATION' : phase === 'speaking' ? 'SPEAKING TIME' : phase === 'ready' ? 'READY WHEN YOU ARE' : 'TIME COMPLETE'}</div><strong>{phase === 'ready' || phase === 'finished' ? '00:00' : clock}</strong><h2>{topic}</h2><span className={position === 'FOR' ? 'gd-side for' : 'gd-side against'}>{position}</span>{phase === 'preparation' && <p>Outline one clear claim, supporting reasons, and an example.</p>}{phase === 'preparation' && <button className="primary" onClick={startSpeaking}>Start speaking</button>}{phase === 'ready' && <button className="primary" onClick={startSpeaking}>Start speaking</button>}{phase === 'finished' && <p>Your speaking time ended. Submit what you captured or add the rest in the response field.</p>}</article><article className="panel gd-response"><label>Your response<textarea value={response} onChange={(event) => setResponse(event.target.value)} placeholder="Type your response or use speech recognition..." /></label><div className="gd-response-actions"><button className="secondary" type="button" onClick={record}>{listening ? <MicOff size={16} /> : <Mic size={16} />}{listening ? 'Stop recording' : 'Record response'}</button><button className="primary" onClick={submit} disabled={!response.trim()}><Send size={16} /> Submit response</button></div></article></section>}
    {phase === 'result' && result && <section className="panel gd-report"><div className="gd-result-heading"><div><div className="eyebrow">PERFORMANCE REVIEW</div><h2>GD Performance</h2></div><strong>{result.score}<small>/100</small></strong></div><div className="gd-metrics">{Object.entries(result.metrics).map(([key, value]) => <div key={key}><span>{key.replaceAll('_', ' ')}</span><b>{value}</b><i><em style={{ width: `${value}%` }} /></i></div>)}</div><div className="gd-feedback-grid"><article><small>STRONGEST POINT</small><p>{result.strongest_point}</p></article><article><small>WHAT TO IMPROVE</small><ul>{result.improvements.map((item) => <li key={item}>{item}</li>)}</ul></article><article className="gd-sample"><small>SAMPLE IMPROVED ANSWER</small><p>{result.sample_answer}</p></article></div><p className="gd-confidence-note">{result.confidence_note}</p><button className="secondary" onClick={reset}><RotateCcw size={15} /> Practice another topic</button></section>}
  </div>;
}
