from datetime import date, datetime

from werkzeug.security import check_password_hash, generate_password_hash

from . import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    auth_provider = db.Column(db.String(20), nullable=False, default="email")
    google_picture = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resumes = db.relationship("Resume", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return bool(self.password_hash) and check_password_hash(self.password_hash, password)


class CareerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    degree = db.Column(db.String(160), default="")
    college = db.Column(db.String(200), default="")
    graduation_year = db.Column(db.String(4), default="")
    target_role = db.Column(db.String(160), default="")
    skills = db.Column(db.JSON, nullable=False, default=list)
    completed = db.Column(db.Boolean, default=False)
    user = db.relationship("User", backref=db.backref("career_profile", uselist=False))


class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    extracted_text = db.Column(db.Text, nullable=False)
    analysis = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class JobAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey("resume.id"), nullable=True)
    role = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)
    result = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class InterviewResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role = db.Column(db.String(160), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    feedback = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CareerRoadmap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    target_role = db.Column(db.String(160), nullable=False)
    experience_level = db.Column(db.String(40), nullable=False, default="Beginner")
    education = db.Column(db.String(200), default="")
    hours_per_week = db.Column(db.Integer, nullable=False, default=8)
    timeline = db.Column(db.String(20), nullable=False, default="6 months")
    readiness = db.Column(db.JSON, nullable=False, default=dict)
    skill_analysis = db.Column(db.JSON, nullable=False, default=dict)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("career_roadmaps", lazy=True))
    phases = db.relationship("RoadmapPhase", backref="roadmap", cascade="all, delete-orphan", order_by="RoadmapPhase.position", lazy=True)
    milestones = db.relationship("RoadmapMilestone", backref="roadmap", cascade="all, delete-orphan", order_by="RoadmapMilestone.position", lazy=True)


class RoadmapPhase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roadmap_id = db.Column(db.Integer, db.ForeignKey("career_roadmap.id"), nullable=False, index=True)
    position = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(160), nullable=False)
    duration = db.Column(db.String(80), nullable=False)
    objective = db.Column(db.Text, nullable=False)
    skills = db.Column(db.JSON, nullable=False, default=list)
    topics = db.Column(db.JSON, nullable=False, default=list)
    practice_tasks = db.Column(db.JSON, nullable=False, default=list)
    recommended_project = db.Column(db.JSON, nullable=False, default=dict)
    completion_criteria = db.Column(db.JSON, nullable=False, default=list)
    tasks = db.relationship("RoadmapTask", backref="phase", cascade="all, delete-orphan", order_by="RoadmapTask.position", lazy=True)


class RoadmapTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phase_id = db.Column(db.Integer, db.ForeignKey("roadmap_phase.id"), nullable=False, index=True)
    week = db.Column(db.Integer, nullable=False, default=1)
    position = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(240), nullable=False)
    description = db.Column(db.Text, default="")
    estimated_minutes = db.Column(db.Integer, nullable=False, default=30)
    completed = db.Column(db.Boolean, nullable=False, default=False)


class RoadmapMilestone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roadmap_id = db.Column(db.Integer, db.ForeignKey("career_roadmap.id"), nullable=False, index=True)
    position = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(160), nullable=False)
    required_progress = db.Column(db.Integer, nullable=False, default=0)
    completed = db.Column(db.Boolean, nullable=False, default=False)


class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    key = db.Column(db.String(80), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.String(240), nullable=False)
    unlocked = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("achievements", lazy=True, cascade="all, delete-orphan"))
    __table_args__ = (db.UniqueConstraint("user_id", "key", name="uq_user_achievement"),)


class GitHubAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    username = db.Column(db.String(120), nullable=False)
    profile = db.Column(db.JSON, nullable=False, default=dict)
    repositories = db.Column(db.JSON, nullable=False, default=list)
    analysis = db.Column(db.JSON, nullable=False, default=dict)
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", backref=db.backref("github_analyses", lazy=True, cascade="all, delete-orphan"))


class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    company = db.Column(db.String(180), nullable=False)
    role = db.Column(db.String(180), nullable=False)
    location = db.Column(db.String(180), default="")
    package = db.Column(db.String(120), default="")
    application_date = db.Column(db.Date, nullable=True)
    deadline = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, default="")
    notes = db.Column(db.Text, default="")
    status = db.Column(db.String(24), nullable=False, default="Saved", index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GDResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    topic = db.Column(db.String(240), nullable=False)
    position = db.Column(db.String(8), nullable=False)
    response = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    evaluation = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SkillPlanTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    skill = db.Column(db.String(120), nullable=False)
    day = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(240), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    __table_args__ = (db.UniqueConstraint("user_id", "skill", "day", name="uq_user_skill_plan_day"),)
