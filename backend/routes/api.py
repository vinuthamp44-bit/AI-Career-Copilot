import os
import uuid

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from pypdf import PdfReader
from werkzeug.utils import secure_filename

from models import db
from models.models import InterviewResult, JobAnalysis, Resume, User
from services.ai_service import analyze_resume, compare_resume, evaluate_answer, interview_questions, roadmap, role_matches

api = Blueprint("api", __name__, url_prefix="/api")


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
    user = User(name=body["name"].strip(), email=email)
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


def _user():
    return User.query.get(int(get_jwt_identity()))


@api.get("/dashboard")
@jwt_required()
def dashboard():
    user = _user()
    resume = Resume.query.filter_by(user_id=user.id).order_by(Resume.created_at.desc()).first()
    latest_job = JobAnalysis.query.filter_by(user_id=user.id).order_by(JobAnalysis.created_at.desc()).first()
    skills = resume.analysis.get("sections", {}).get("skills", []) if resume else []
    interview_count = InterviewResult.query.filter_by(user_id=user.id).count()
    return jsonify({"user": {"name": user.name, "email": user.email}, "resume": resume.analysis if resume else None, "resume_id": resume.id if resume else None, "ats": latest_job.result if latest_job else None, "roles": role_matches(skills)[:3], "roadmap": roadmap(skills, latest_job.role if latest_job else "Frontend Developer"), "interview_progress": min(100, interview_count * 33)})


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
    return jsonify({"questions": interview_questions(body.get("role", "Target role"), body.get("skills", []), body.get("job_description", ""))})


@api.post("/roadmap")
@jwt_required()
def learning_roadmap():
    body = request.get_json(silent=True) or {}
    if not isinstance(body.get("skills", []), list):
        return jsonify({"error": "Skills must be sent as a list."}), 400
    return jsonify({"roadmap": roadmap(body.get("skills", []), body.get("target_role", "Frontend Developer"))})


@api.post("/interview/evaluate")
@jwt_required()
def evaluate():
    body = request.get_json(silent=True) or {}
    if not body.get("answer") or not body.get("question"):
        return jsonify({"error": "Question and answer are required."}), 400
    score, feedback = evaluate_answer(body["answer"])
    result = InterviewResult(user_id=int(get_jwt_identity()), role=body.get("role", "Target role"), question=body["question"], answer=body["answer"], score=score, feedback=feedback)
    db.session.add(result)
    db.session.commit()
    return jsonify({"score": score, "feedback": feedback})
