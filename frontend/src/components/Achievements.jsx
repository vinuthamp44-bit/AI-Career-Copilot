import React from 'react';
import { Award, LockKeyhole } from 'lucide-react';

export default function Achievements({ dashboard }) {
  const achievements = dashboard.achievements || [];
  return <div className="content achievements-page"><section className="page-heading"><div className="eyebrow">PROGRESS RECOGNITION</div><h1>Achievements</h1><p>Milestones unlock automatically from your real career activity.</p></section><section className="achievement-grid">{achievements.map((achievement) => <article className={achievement.unlocked ? 'achievement unlocked' : 'achievement'} key={achievement.key}>{achievement.unlocked ? <Award size={21} /> : <LockKeyhole size={18} />}<div><b>{achievement.title}</b><p>{achievement.description}</p></div></article>)}</section>{!achievements.length && <section className="panel empty-state"><p className="empty">Complete a resume analysis, roadmap task, or interview to start unlocking achievements.</p></section>}</div>;
}
