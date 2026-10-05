import os
import random
import uuid
from datetime import date

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pypdf import PdfReader
from werkzeug.utils import secure_filename
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from models import db
from models.models import Achievement, CareerProfile, CareerRoadmap, GDResult, InterviewResult, JobAnalysis, JobApplication, Resume, RoadmapMilestone, RoadmapPhase, RoadmapTask, SkillPlanTask, User
from services.ai_service import GD_TOPICS, achievement_definitions, analyze_job_description, analyze_resume, career_roadmap, compare_resume, evaluate_answer, evaluate_group_discussion, improve_resume_bullet, interview_questions, roadmap, role_matches, skill_gap_analysis, skill_learning_plan

api = Blueprint("api", __name__, url_prefix="/api")
APPLICATION_STATUSES = ("Saved", "Applied", "Assessment", "GD", "Interview", "Selected", "Rejected")


@api.get("/health")
def health():
    return jsonify({"status": "ok", "service": "AI Career Copilot"})


@api.post("/auth/register")
def register():
    body = request.get_json(silent=True) or {}
    email = body.get("email", "").strip().lower()
    if not body.get("name", "").strip() or "@" not in email or len(body.get("password", "")) < 8:
        return jsonify({"error": "Name, email and an 8-character password are required."}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with that email already exists."}), 409
    user = User(name=body["name"].strip(), email=email, auth_provider="email")
    user.set_password(body["password"])
    db.session.add(user)
    db.session.commit()
    return jsonify({"token": create_access_token(identity=str(user.id)), "user": {"id": user.id, "name": user.name, "email": user.email}}), 201


@api.post("/auth/login")
def login():
    body = request.get_json(silent=True) or {}
    user = User.query.filter_by(email=body.get("email", "").strip().lower()).first()
    if not user or not user.check_password(body.get("password", "")):
        return jsonify({"error": "Invalid email or password."}), 401
    return jsonify({"token": create_access_token(identity=str(user.id)), "user": {"id": user.id, "name": user.name, "email": user.email}})


@api.post("/auth/forgot-password")
def forgot_password():
    body = request.get_json(silent=True) or {}
    email = body.get("email", "").strip().lower()
    response = {"message": "If an account exists for that email, reset instructions are ready."}
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify(response)
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    token = serializer.dumps({"user_id": user.id, "email": user.email}, salt="password-reset")
    if current_app.config.get("APP_ENV") != "production":
        response["reset_url"] = f'{current_app.config["FRONTEND_URL"]}/?reset_token={token}'
    return jsonify(response)


@api.post("/auth/reset-password")
def reset_password():
    body = request.get_json(silent=True) or {}
    token = body.get("token", "")
    password = body.get("password", "")
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400
    try:
        data = URLSafeTimedSerializer(current_app.config["SECRET_KEY"]).loads(token, salt="password-reset", max_age=3600)
    except (BadSignature, SignatureExpired):
        return jsonify({"error": "This reset link is invalid or expired."}), 400
    user = User.query.filter_by(id=data.get("user_id"), email=data.get("email")).first()
    if not user:
        return jsonify({"error": "This reset link is invalid or expired."}), 400
    user.set_password(password)
    db.session.commit()
    return jsonify({"message": "Password reset successfully."})


@api.post("/auth/google")
def google_login():
    body = request.get_json(silent=True) or {}
    credential = body.get("credential", "")
    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    if not client_id:
        return jsonify({"error": "Google sign-in is not configured on this server."}), 503
    if not credential:
        return jsonify({"error": "Google sign-in failed. Please try again."}), 400
    try:
        claims = id_token.verify_oauth2_token(credential, google_requests.Request(), client_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Google sign-in could not be verified. Please try again."}), 401
    email = claims.get("email", "").strip().lower()
    name = claims.get("name", "").strip()
    if not email or not claims.get("email_verified") or not name:
        return jsonify({"error": "Google did not provide a verified account."}), 401
    user = User.query.filter_by(email=email).first()
    new_user = user is None
    if new_user:
        user = User(name=name, email=email, auth_provider="google", google_picture=claims.get("picture"))
        db.session.add(user)
        db.session.commit()
    elif user.auth_provider == "email":
        return jsonify({"error": "An account already exists with this email using email/password. Sign in with your password first."}), 409
    elif user.auth_provider == "google":
        user.google_picture = claims.get("picture") or user.google_picture
        db.session.commit()
    return jsonify({"token": create_access_token(identity=str(user.id)), "new_user": new_user, "user": {"id": user.id, "name": user.name, "email": user.email, "picture": user.google_picture, "auth_provider": user.auth_provider}})


def _user():
    return User.query.get(int(get_jwt_identity()))


@api.get("/dashboard")
@jwt_required()
def dashboard():
    user = _user()
    resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.created_at.desc()).first()
    latest_job = JobAnalysis.query.filter_by(user_id=user.id).order_by(JobAnalysis.created_at.desc()).first()
    profile = user.career_profile
    resume_skills = resume.analysis.get("sections", {}).get("skills", []) if resume else []
    profile_skills = profile.skills if profile and isinstance(profile.skills, list) else []
    skills = sorted(set(resume_skills + profile_skills))
    interviews = InterviewResult.query.filter_by(user_id=user.id).order_by(InterviewResult.created_at.desc()).all()
    gd_results = GDResult.query.filter_by(user_id=user.id).order_by(GDResult.created_at.desc()).all()
    interview_count = len(interviews)
    target_role = (profile.target_role if profile and profile.target_role else latest_job.role if latest_job else "Frontend Developer")
    persisted = CareerRoadmap.query.filter_by(user_id=user.id).order_by(CareerRoadmap.generated_at.desc()).first()
    readiness = calculate_readiness(resume, latest_job, interview_count, persisted, profile, interviews, gd_results)
    roadmap_progress = _roadmap_progress(persisted)
    achievements = sync_achievements(user, resume, latest_job, interview_count, roadmap_progress, readiness["overall"])
    daily_actions = [{"title": task.title, "estimated_minutes": task.estimated_minutes} for phase in persisted.phases for task in phase.tasks if not task.completed][:4] if persisted else []
    return jsonify({"user": {"name": user.name, "email": user.email}, "profile": {"degree": profile.degree, "college": profile.college, "graduation_year": profile.graduation_year, "target_role": profile.target_role, "skills": profile.skills, "completed": profile.completed} if profile else None, "resume": resume.analysis if resume else None, "resume_id": resume.id if resume else None, "ats": latest_job.result if latest_job else None, "roles": role_matches(skills, target_role)[:3], "roadmap": roadmap(skills, target_role), "target_role": target_role, "interview_progress": min(100, interview_count * 33), "readiness": readiness, "roadmap_progress": roadmap_progress, "daily_actions": daily_actions, "achievements": achievements})


def _application_payload(record):
    return {"id": record.id, "company": record.company, "role": record.role, "location": record.location or "", "package": record.package or "", "application_date": record.application_date.isoformat() if record.application_date else "", "deadline": record.deadline.isoformat() if record.deadline else "", "description": record.description or "", "notes": record.notes or "", "status": record.status, "created_at": record.created_at.isoformat() if record.created_at else "", "updated_at": record.updated_at.isoformat() if record.updated_at else ""}


def _application_date(value, field_name):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid date in YYYY-MM-DD format.")


@api.get("/applications")
@jwt_required()
def list_applications():
    user_id = int(get_jwt_identity())
    query = JobApplication.query.filter_by(user_id=user_id)
    status = request.args.get("status", "").strip()
    search = request.args.get("q", "").strip()
    if status and status != "All":
        if status not in APPLICATION_STATUSES:
            return jsonify({"error": "Unknown application status."}), 400
        query = query.filter_by(status=status)
    if search:
        pattern = f"%{search}%"
        query = query.filter(db.or_(JobApplication.company.ilike(pattern), JobApplication.role.ilike(pattern), JobApplication.location.ilike(pattern)))
    records = query.order_by(JobApplication.application_date.desc(), JobApplication.created_at.desc()).all()
    all_records = JobApplication.query.filter_by(user_id=user_id).all()
    counts = {item: sum(record.status == item for record in all_records) for item in APPLICATION_STATUSES}
    return jsonify({"applications": [_application_payload(record) for record in records], "counts": counts, "total": len(all_records)})


@api.post("/applications")
@jwt_required()
def create_application():
    body = request.get_json(silent=True) or {}
    if not body.get("company", "").strip() or not body.get("role", "").strip():
        return jsonify({"error": "Company name and job role are required."}), 400
    status = body.get("status", "Saved")
    if status not in APPLICATION_STATUSES:
        return jsonify({"error": "Unknown application status."}), 400
    try:
        application_date = _application_date(body.get("application_date") or date.today().isoformat(), "Application date")
        deadline = _application_date(body.get("deadline"), "Application deadline")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    record = JobApplication(user_id=int(get_jwt_identity()), company=body["company"].strip(), role=body["role"].strip(), location=body.get("location", "").strip(), package=body.get("package", "").strip(), application_date=application_date, deadline=deadline, description=body.get("description", "").strip(), notes=body.get("notes", "").strip(), status=status)
    db.session.add(record)
    db.session.commit()
    return jsonify({"application": _application_payload(record)}), 201


@api.get("/applications/<int:application_id>")
@jwt_required()
def get_application(application_id):
    record = JobApplication.query.filter_by(id=application_id, user_id=int(get_jwt_identity())).first()
    if not record:
        return jsonify({"error": "Application not found."}), 404
    return jsonify({"application": _application_payload(record)})


@api.patch("/applications/<int:application_id>")
@jwt_required()
def update_application(application_id):
    record = JobApplication.query.filter_by(id=application_id, user_id=int(get_jwt_identity())).first()
    if not record:
        return jsonify({"error": "Application not found."}), 404
    body = request.get_json(silent=True) or {}
    for key in ("company", "role", "location", "package", "description", "notes"):
        if key in body:
            value = body[key].strip() if isinstance(body[key], str) else ""
            if key in ("company", "role") and not value:
                return jsonify({"error": "Company name and job role cannot be empty."}), 400
            setattr(record, key, value)
    if "status" in body:
        if body["status"] not in APPLICATION_STATUSES:
            return jsonify({"error": "Unknown application status."}), 400
        record.status = body["status"]
    try:
        if "application_date" in body:
            record.application_date = _application_date(body["application_date"], "Application date")
        if "deadline" in body:
            record.deadline = _application_date(body["deadline"], "Application deadline")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    db.session.commit()
    return jsonify({"application": _application_payload(record)})


@api.delete("/applications/<int:application_id>")
@jwt_required()
def delete_application(application_id):
    record = JobApplication.query.filter_by(id=application_id, user_id=int(get_jwt_identity())).first()
    if not record:
        return jsonify({"error": "Application not found."}), 404
    db.session.delete(record)
    db.session.commit()
    return jsonify({"deleted": True})


def _roadmap_progress(record):
    if not record:
        return 0
    tasks = [task for phase in record.phases for task in phase.tasks]
    return round(sum(task.completed for task in tasks) / len(tasks) * 100) if tasks else 0


def calculate_readiness(resume, latest_job, interview_count, persisted, profile=None, interviews=None, gd_results=None):
    resume_score = resume.analysis.get("score", 0) if resume else 0
    resume_skills = resume.analysis.get("sections", {}).get("skills", []) if resume else []
    profile_skills = profile.skills if profile and isinstance(profile.skills, list) else []
    skills = sorted(set(resume_skills + profile_skills))
    target_role = persisted.target_role if persisted else (profile.target_role if profile else "")
    matches = role_matches(skills, target_role)
    target_match = next((item["match"] for item in matches if item["role"].lower() == target_role.lower()), matches[0]["match"] if matches else 0)
    interviews = interviews or []
    gd_results = gd_results or []
    interview_scores = [item.score for item in interviews]
    interview_score = round(sum(interview_scores) / len(interview_scores)) if interview_scores else 0
    communication_scores = [evaluate_answer(item.answer, item.question).get("communication", 0) for item in interviews]
    communication_scores.extend(item.evaluation.get("metrics", {}).get("communication", 0) for item in gd_results)
    communication_score = round(sum(communication_scores) / len(communication_scores)) if communication_scores else 0
    roadmap_score = _roadmap_progress(persisted)
    project_score = 65 if resume and resume.analysis.get("sections", {}).get("projects") else 0
    values = {"resume": resume_score, "technical": target_match, "projects": project_score, "interview": interview_score, "job_match": latest_job.result.get("score", 0) if latest_job else target_match, "communication": communication_score, "roadmap": roadmap_score}
    weights = {"resume": 20, "technical": 20, "projects": 10, "interview": 15, "job_match": 15, "communication": 10, "roadmap": 10}
    values["overall"] = round(sum(values[key] * weight for key, weight in weights.items()) / sum(weights.values()))
    labels = {"resume": "Resume", "technical": "Technical skills", "projects": "Projects", "interview": "Interview", "job_match": "Job match", "communication": "Communication", "roadmap": "Roadmap progress"}
    ranked = sorted(weights, key=lambda key: values[key])
    gaps = skill_gap_analysis(skills, target_role or "Frontend Developer")["missing"]
    actions = {
        "resume": "Upload and analyze your resume" if not resume else "Improve the weakest resume section and quantify evidence",
        "technical": f"Build evidence for {gaps[0]['skill']}" if gaps else "Deepen your strongest role skills with a practical project",
        "projects": "Add a project with a clear problem, tools, and outcome",
        "interview": "Complete a mock interview and review the feedback",
        "job_match": "Analyze your resume against a target job description",
        "communication": "Practice a GD response and focus on concise structure",
        "roadmap": "Complete the next task in your career roadmap" if persisted else "Generate your personal career roadmap",
    }
    improvements = [{"area": labels[key], "score": values[key], "action": actions[key]} for key in ranked[:3]]
    return {**values, "strongest_area": labels[max(weights, key=lambda key: values[key])], "weakest_area": labels[ranked[0]], "improvements": improvements, "next_action": improvements[0]["action"]}


def sync_achievements(user, resume, latest_job, interview_count, roadmap_progress, readiness_score):
    definitions = achievement_definitions(resume, latest_job.result if latest_job else None, interview_count, roadmap_progress)
    for item in definitions:
        if item["key"] == "jobready":
            item["unlocked"] = readiness_score >= 80
        record = Achievement.query.filter_by(user_id=user.id, key=item["key"]).first()
        if not record:
            record = Achievement(user_id=user.id, key=item["key"])
        record.title = item["title"]
        record.description = item["description"]
        record.unlocked = item["unlocked"]
        db.session.add(record)
    db.session.commit()
    return [{"key": item["key"], "title": item["title"], "description": item["description"], "unlocked": item["unlocked"]} for item in definitions]


@api.get("/skill-gaps")
@jwt_required()
def skill_gaps():
    user = _user()
    profile = user.career_profile
    resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.created_at.desc()).first()
    skills = (resume.analysis.get("sections", {}).get("skills", []) if resume else []) or (profile.skills if profile else [])
    target_role = profile.target_role if profile and profile.target_role else "Frontend Developer"
    analysis = skill_gap_analysis(skills, target_role)
    for item in analysis["all"]:
        if item["status"] == "Strong":
            continue
        for task in skill_learning_plan(item["skill"]):
            record = SkillPlanTask.query.filter_by(user_id=user.id, skill=item["skill"], day=task["day"]).first()
            if not record:
                db.session.add(SkillPlanTask(user_id=user.id, skill=item["skill"], **task))
    db.session.commit()
    for item in analysis["all"]:
        tasks = SkillPlanTask.query.filter_by(user_id=user.id, skill=item["skill"]).order_by(SkillPlanTask.day).all()
        item["plan"] = [{"id": task.id, "day": task.day, "title": task.title, "completed": task.completed} for task in tasks]
        item["progress"] = round(sum(task.completed for task in tasks) / len(tasks) * 100) if tasks else 0
    return jsonify({"target_role": target_role, "analysis": analysis})


@api.patch("/skill-gaps/tasks/<int:task_id>")
@jwt_required()
def update_skill_plan_task(task_id):
    task = SkillPlanTask.query.filter_by(id=task_id, user_id=int(get_jwt_identity())).first()
    if not task:
        return jsonify({"error": "Learning task not found."}), 404
    body = request.get_json(silent=True) or {}
    if not isinstance(body.get("completed"), bool):
        return jsonify({"error": "Completed must be true or false."}), 400
    task.completed = body["completed"]
    db.session.commit()
    tasks = SkillPlanTask.query.filter_by(user_id=task.user_id, skill=task.skill).all()
    return jsonify({"task_id": task.id, "completed": task.completed, "skill": task.skill, "progress": round(sum(item.completed for item in tasks) / len(tasks) * 100) if tasks else 0})


@api.post("/resume/improve-bullet")
@jwt_required()
def resume_bullet_improvement():
    body = request.get_json(silent=True) or {}
    bullet = body.get("bullet", "").strip()
    if not bullet:
        return jsonify({"error": "Enter a resume bullet to improve."}), 400
    if len(bullet) > 1200:
        return jsonify({"error": "Resume bullets must be 1,200 characters or fewer."}), 400
    return jsonify({"result": improve_resume_bullet(bullet)})


@api.post("/jobs/analyze-description")
@jwt_required()
def analyze_description():
    body = request.get_json(silent=True) or {}
    description = body.get("description", "").strip()
    if not description:
        return jsonify({"error": "Please enter a job description."}), 400
    if len(description) > 30000:
        return jsonify({"error": "Job descriptions must be 30,000 characters or fewer."}), 400
    user = _user()
    profile = user.career_profile
    resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.created_at.desc()).first()
    resume_skills = resume.analysis.get("sections", {}).get("skills", []) if resume else []
    profile_skills = profile.skills if profile and isinstance(profile.skills, list) else []
    return jsonify({"analysis": analyze_job_description(description, sorted(set(resume_skills + profile_skills)))})


@api.get("/gd/topics")
@jwt_required()
def gd_topics():
    return jsonify({"topics": GD_TOPICS})


@api.get("/gd/topics/random")
@jwt_required()
def random_gd_topic():
    return jsonify({"topic": random.choice(GD_TOPICS)})


@api.post("/gd/evaluate")
@jwt_required()
def evaluate_gd():
    body = request.get_json(silent=True) or {}
    topic = body.get("topic", "").strip()
    position = body.get("position", "").upper()
    response = body.get("response", "").strip()
    if not topic or position not in {"FOR", "AGAINST"} or not response:
        return jsonify({"error": "Topic, FOR/AGAINST position, and response are required."}), 400
    if len(response) > 12000:
        return jsonify({"error": "Responses must be 12,000 characters or fewer."}), 400
    evaluation = evaluate_group_discussion(topic, position, response)
    result = GDResult(user_id=int(get_jwt_identity()), topic=topic, position=position, response=response, score=evaluation["score"], evaluation=evaluation)
    db.session.add(result)
    db.session.commit()
    return jsonify(evaluation)


@api.get("/career-readiness")
@jwt_required()
def career_readiness():
    user = _user()
    resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.created_at.desc()).first()
    latest_job = JobAnalysis.query.filter_by(user_id=user.id).order_by(JobAnalysis.created_at.desc()).first()
    persisted = CareerRoadmap.query.filter_by(user_id=user.id).order_by(CareerRoadmap.generated_at.desc()).first()
    interviews = InterviewResult.query.filter_by(user_id=user.id).order_by(InterviewResult.created_at.desc()).all()
    gd_results = GDResult.query.filter_by(user_id=user.id).order_by(GDResult.created_at.desc()).all()
    return jsonify({"readiness": calculate_readiness(resume, latest_job, len(interviews), persisted, user.career_profile, interviews, gd_results)})


@api.get("/achievements")
@jwt_required()
def achievements():
    user = _user()
    resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.created_at.desc()).first()
    latest_job = JobAnalysis.query.filter_by(user_id=user.id).order_by(JobAnalysis.created_at.desc()).first()
    persisted = CareerRoadmap.query.filter_by(user_id=user.id).order_by(CareerRoadmap.generated_at.desc()).first()
    interview_count = InterviewResult.query.filter_by(user_id=user.id).count()
    interviews = InterviewResult.query.filter_by(user_id=user.id).order_by(InterviewResult.created_at.desc()).all()
    gd_results = GDResult.query.filter_by(user_id=user.id).order_by(GDResult.created_at.desc()).all()
    readiness = calculate_readiness(resume, latest_job, interview_count, persisted, user.career_profile, interviews, gd_results)
    return jsonify({"achievements": sync_achievements(user, resume, latest_job, interview_count, _roadmap_progress(persisted), readiness["overall"])})


@api.post("/profile")
@jwt_required()
def save_profile():
    body = request.get_json(silent=True) or {}
    user = _user()
    profile = user.career_profile or CareerProfile(user_id=user.id)
    profile.degree = body.get("degree", "").strip()
    profile.college = body.get("college", "").strip()
    profile.graduation_year = str(body.get("graduation_year", "")).strip()
    profile.target_role = body.get("target_role", "").strip()
    profile.skills = body.get("skills", []) if isinstance(body.get("skills", []), list) else []
    profile.completed = bool(body.get("completed", False))
    db.session.add(profile)
    db.session.commit()
    return jsonify({"profile": {"degree": profile.degree, "college": profile.college, "graduation_year": profile.graduation_year, "target_role": profile.target_role, "skills": profile.skills, "completed": profile.completed}})


@api.post("/resume/analyze")
@jwt_required()
def upload_resume():
    file = request.files.get("resume")
    if not file or not file.filename or not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Please upload a PDF resume."}), 400
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(path)
    try:
        text = "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    except Exception:
        if os.path.exists(path):
            os.remove(path)
        return jsonify({"error": "The PDF could not be read."}), 422
    if not text.strip():
        os.remove(path)
        return jsonify({"error": "No readable text was found in that PDF."}), 422
    result = analyze_resume(text)
    resume = Resume(user_id=int(get_jwt_identity()), filename=filename, extracted_text=text, analysis=result)
    db.session.add(resume)
    db.session.commit()
    return jsonify({"resume_id": resume.id, "analysis": result})


@api.post("/ats/analyze")
@jwt_required()
def ats_analyze():
    body = request.form if request.files else (request.get_json(silent=True) or {})
    description = body.get("description", "").strip()
    if not description:
        return jsonify({"error": "Please enter a job description."}), 400
    resume_file = request.files.get("resume")
    user_id = int(get_jwt_identity())
    resume = None
    temporary_path = None
    if resume_file:
        if not resume_file.filename or not resume_file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Please upload a PDF resume."}), 400
        os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
        filename = f"{uuid.uuid4().hex}_{secure_filename(resume_file.filename)}"
        temporary_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        resume_file.save(temporary_path)
        try:
            text = "\n".join(page.extract_text() or "" for page in PdfReader(temporary_path).pages)
        except Exception:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)
            return jsonify({"error": "The PDF could not be read."}), 422
        if not text.strip():
            os.remove(temporary_path)
            return jsonify({"error": "No readable text was found in that PDF."}), 422
        resume = Resume(user_id=user_id, filename=filename, extracted_text=text, analysis=analyze_resume(text))
        db.session.add(resume)
        db.session.flush()
    else:
        resume = Resume.query.filter_by(id=body.get("resume_id"), user_id=user_id).first()
        if not resume:
            return jsonify({"error": "Please upload your resume."}), 400
    result = compare_resume(resume.extracted_text, description, body.get("role", ""))
    resume_analysis = analyze_resume(resume.extracted_text)
    result.update({"matched_skills": result["matching_keywords"], "missing_skills": result["missing_keywords"], "resume_strengths": resume_analysis["strengths"], "resume_weaknesses": resume_analysis["weaknesses"]})
    record = JobAnalysis(user_id=user_id, resume_id=resume.id, role=body.get("role", "Target role"), description=description, result=result)
    db.session.add(record)
    db.session.commit()
    return jsonify(result)


@api.post("/jobs/match")
@jwt_required()
def job_match():
    body = request.get_json(silent=True) or {}
    if not isinstance(body.get("skills", []), list):
        return jsonify({"error": "Skills must be sent as a list."}), 400
    return jsonify({"roles": role_matches(body.get("skills", []), body.get("target_role", ""))})


@api.post("/interview/questions")
@jwt_required()
def questions():
    body = request.get_json(silent=True) or {}
    if not isinstance(body.get("skills", []), list):
        return jsonify({"error": "Skills must be sent as a list."}), 400
    user = _user()
    profile = user.career_profile
    resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.created_at.desc()).first()
    skills = body.get("skills") or (resume.analysis.get("sections", {}).get("skills", []) if resume else []) or (profile.skills if profile else [])
    role = body.get("role") or (profile.target_role if profile else "Target role")
    return jsonify({"questions": interview_questions(role, skills, body.get("job_description", ""), body.get("interview_type", "Mixed"), body.get("difficulty", "Medium"), resume.extracted_text if resume else "")})


@api.post("/roadmap")
@jwt_required()
def learning_roadmap():
    body = request.get_json(silent=True) or {}
    if not isinstance(body.get("skills", []), list):
        return jsonify({"error": "Skills must be sent as a list."}), 400
    return jsonify({"roadmap": roadmap(body.get("skills", []), body.get("target_role", "Frontend Developer"))})


def _roadmap_payload(record):
    tasks = [task for phase in record.phases for task in phase.tasks]
    completed_tasks = sum(task.completed for task in tasks)
    progress = round(completed_tasks / len(tasks) * 100) if tasks else 0
    return {"id": record.id, "target_role": record.target_role, "experience_level": record.experience_level, "education": record.education, "hours_per_week": record.hours_per_week, "timeline": record.timeline, "readiness": record.readiness, "skill_analysis": record.skill_analysis, "progress": progress, "completed_tasks": completed_tasks, "total_tasks": len(tasks), "daily_actions": [{"id": task.id, "title": task.title, "estimated_minutes": task.estimated_minutes} for task in tasks if not task.completed][:5], "phases": [{"id": phase.id, "position": phase.position, "title": phase.title, "duration": phase.duration, "objective": phase.objective, "skills": phase.skills, "topics": phase.topics, "practice_tasks": phase.practice_tasks, "recommended_project": phase.recommended_project, "completion_criteria": phase.completion_criteria, "progress": round(sum(task.completed for task in phase.tasks) / len(phase.tasks) * 100) if phase.tasks else 0, "tasks": [{"id": task.id, "week": task.week, "position": task.position, "title": task.title, "description": task.description, "estimated_minutes": task.estimated_minutes, "completed": task.completed} for task in phase.tasks]} for phase in record.phases], "milestones": [{"id": milestone.id, "position": milestone.position, "title": milestone.title, "required_progress": milestone.required_progress, "completed": milestone.completed} for milestone in record.milestones]}


def _create_roadmap(user, body, existing=None):
    profile = user.career_profile
    resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.created_at.desc()).first()
    resume_skills = resume.analysis.get("sections", {}).get("skills", []) if resume else []
    profile_skills = profile.skills if profile and isinstance(profile.skills, list) else []
    skills = sorted(set(resume_skills + profile_skills))
    target_role = (body.get("target_role") or profile.target_role if profile else body.get("target_role")) or "Frontend Developer"
    experience_level = body.get("experience_level", "Beginner")
    hours_per_week = body.get("hours_per_week", 8)
    timeline = body.get("timeline", "6 months")
    completed_titles = [task.title for phase in existing.phases for task in phase.tasks if task.completed] if existing else []
    generated = career_roadmap(skills, target_role, experience_level, hours_per_week, timeline, completed_titles)
    record = existing or CareerRoadmap(user_id=user.id)
    record.target_role = target_role
    record.experience_level = experience_level
    record.education = body.get("education", profile.degree if profile else "")
    record.hours_per_week = hours_per_week
    record.timeline = timeline
    record.readiness = generated["readiness"]
    record.skill_analysis = generated["skill_analysis"]
    record.phases = []
    record.milestones = []
    db.session.add(record)
    db.session.flush()
    for phase_data in generated["phases"]:
        phase = RoadmapPhase(roadmap_id=record.id, position=phase_data["position"], title=phase_data["title"], duration=phase_data["duration"], objective=phase_data["objective"], skills=phase_data["skills"], topics=phase_data["topics"], practice_tasks=phase_data["practice_tasks"], recommended_project=phase_data["recommended_project"], completion_criteria=phase_data["completion_criteria"])
        db.session.add(phase)
        db.session.flush()
        for task_data in phase_data["tasks"]:
            db.session.add(RoadmapTask(phase_id=phase.id, **task_data))
    for milestone_data in generated["milestones"]:
        db.session.add(RoadmapMilestone(roadmap_id=record.id, **milestone_data))
    db.session.commit()
    return record


@api.get("/career-roadmap")
@jwt_required()
def get_career_roadmap():
    user = _user()
    record = CareerRoadmap.query.filter_by(user_id=user.id).order_by(CareerRoadmap.generated_at.desc()).first()
    return jsonify({"roadmap": _roadmap_payload(record) if record else None})


@api.post("/career-roadmap")
@jwt_required()
def generate_career_roadmap():
    body = request.get_json(silent=True) or {}
    if body.get("experience_level", "Beginner") not in {"Beginner", "Intermediate", "Advanced"}:
        return jsonify({"error": "Experience level must be Beginner, Intermediate or Advanced."}), 400
    if body.get("timeline", "6 months") not in {"3 months", "6 months", "12 months"}:
        return jsonify({"error": "Timeline must be 3 months, 6 months or 12 months."}), 400
    try:
        hours = int(body.get("hours_per_week", 8))
    except (TypeError, ValueError):
        return jsonify({"error": "Hours per week must be a whole number."}), 400
    if hours < 1 or hours > 80:
        return jsonify({"error": "Hours per week must be between 1 and 80."}), 400
    body["hours_per_week"] = hours
    user = _user()
    existing = CareerRoadmap.query.filter_by(user_id=user.id).first()
    record = _create_roadmap(user, body, existing=existing)
    return jsonify({"roadmap": _roadmap_payload(record)}), 200


@api.patch("/career-roadmap/tasks/<int:task_id>")
@jwt_required()
def update_career_roadmap_task(task_id):
    user = _user()
    task = RoadmapTask.query.join(RoadmapPhase).join(CareerRoadmap).filter(RoadmapTask.id == task_id, CareerRoadmap.user_id == user.id).first()
    if not task:
        return jsonify({"error": "Roadmap task not found."}), 404
    body = request.get_json(silent=True) or {}
    if not isinstance(body.get("completed"), bool):
        return jsonify({"error": "Completed must be true or false."}), 400
    task.completed = body["completed"]
    db.session.commit()
    return jsonify({"task_id": task.id, "completed": task.completed, "roadmap": _roadmap_payload(task.phase.roadmap)})


@api.post("/career-roadmap/update")
@jwt_required()
def update_career_roadmap():
    user = _user()
    existing = CareerRoadmap.query.filter_by(user_id=user.id).first()
    if not existing:
        return jsonify({"error": "Create a roadmap before updating it."}), 404
    record = _create_roadmap(user, {"target_role": existing.target_role, "experience_level": existing.experience_level, "education": existing.education, "hours_per_week": existing.hours_per_week, "timeline": existing.timeline}, existing=existing)
    return jsonify({"roadmap": _roadmap_payload(record)})


@api.post("/interview/evaluate")
@jwt_required()
def evaluate():
    body = request.get_json(silent=True) or {}
    if not body.get("answer") or not body.get("question"):
        return jsonify({"error": "Question and answer are required."}), 400
    evaluation = evaluate_answer(body["answer"], body["question"], body.get("interview_type", "Mixed"))
    result = InterviewResult(user_id=int(get_jwt_identity()), role=body.get("role", "Target role"), question=body["question"], answer=body["answer"], score=evaluation["score"], feedback=evaluation["feedback"])
    db.session.add(result)
    db.session.commit()
    return jsonify(evaluation)


@api.get("/interview/history")
@jwt_required()
def interview_history():
    results = InterviewResult.query.filter_by(user_id=int(get_jwt_identity())).order_by(InterviewResult.created_at.desc()).limit(30).all()
    return jsonify({"history": [{"id": item.id, "role": item.role, "question": item.question, "answer": item.answer, "score": item.score, "feedback": item.feedback, "created_at": item.created_at.isoformat()} for item in results]})
