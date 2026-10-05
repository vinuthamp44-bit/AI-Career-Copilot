import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from config import Config
from models import db
from models.models import User
from services.ai_service import analyze_job_description, compare_resume, evaluate_group_discussion, improve_resume_bullet, skill_learning_plan


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-secret"
    GOOGLE_CLIENT_ID = "test-client.apps.googleusercontent.com"


def test_health():
    app = create_app(TestConfig)
    with app.test_client() as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json["status"] == "ok"
    with app.app_context():
        db.drop_all()


def test_register_login():
    app = create_app(TestConfig)
    with app.test_client() as client:
        response = client.post("/api/auth/register", json={"name": "Test User", "email": "test@example.com", "password": "password123"})
        assert response.status_code == 201
        assert response.json["token"]
        login = client.post("/api/auth/login", json={"email": "test@example.com", "password": "password123"})
        assert login.status_code == 200
    with app.app_context():
        db.drop_all()


def test_profile_drives_dashboard_role_and_roadmap():
    app = create_app(TestConfig)
    with app.test_client() as client:
        registered = client.post("/api/auth/register", json={"name": "Profile User", "email": "profile@example.com", "password": "password123"})
        token = registered.json["token"]
        headers = {"Authorization": f"Bearer {token}"}
        profile = client.post("/api/profile", headers=headers, json={"degree": "B.Tech", "college": "State University", "graduation_year": "2027", "target_role": "Python Developer", "skills": ["python"], "completed": True})
        assert profile.status_code == 200

        dashboard = client.get("/api/dashboard", headers=headers)
        assert dashboard.status_code == 200
        assert dashboard.json["target_role"] == "Python Developer"
        assert dashboard.json["roles"][0]["role"] == "Python Developer"
        assert dashboard.json["roadmap"][0]["title"] == "Flask"
    with app.app_context():
        db.drop_all()


def test_ats_returns_actionable_gap_explanation():
    result = compare_resume("Python developer with SQL projects", "Python developer with Docker and AWS experience", "Python Developer")
    assert result["missing_keywords"]
    assert "why_losing" in result
    assert result["fastest_way_to_improve"]


def test_resume_bullet_improver_preserves_claims():
    result = improve_resume_bullet("Made a website using HTML CSS JavaScript.")
    assert result["professional"] == "Developed a website using HTML, CSS, and JavaScript."
    assert "users" not in result["ats_friendly"].lower()
    assert 0 < len(result["short"]) < len(result["professional"])
    assert result["improvements"]


def test_job_description_analysis_matches_profile_skills():
    result = analyze_job_description("Location: Pune\nRequired: Java and SQL. Preferred: AWS. 2+ years experience. Bachelor's degree.", ["java"])
    assert result["matched_skills"] == ["java"]
    assert "sql" in result["missing_skills"]
    assert "aws" in result["preferred_skills"]
    assert result["location"] == "Pune"
    assert result["match_score"] == 50


def test_group_discussion_feedback_has_metrics_and_grounded_sample():
    response = "I believe remote work is useful. For example, my team shares updates online. In conclusion, teamwork still matters."
    result = evaluate_group_discussion("Remote work", "FOR", response)
    assert 0 <= result["score"] <= 100
    assert {"content", "relevance", "structure", "communication", "examples", "confidence", "repetition", "conclusion"} == set(result["metrics"])
    assert "my team shares updates online" in result["sample_answer"]
    assert "not vocal tone" in result["confidence_note"]
    against = evaluate_group_discussion("Remote work", "AGAINST", response)
    assert "why I oppose this position" in against["sample_answer"]


def test_skill_learning_plan_has_seven_uncompleted_days():
    plan = skill_learning_plan("SQL")
    assert len(plan) == 7
    assert [item["day"] for item in plan] == list(range(1, 8))
    assert all(item["completed"] is False for item in plan)
    assert "JOINs" in plan[2]["title"]
    assert "GROUP BY" in plan[3]["title"]


def test_job_applications_support_crud_status_counts_and_search():
    app = create_app(TestConfig)
    with app.test_client() as client:
        registered = client.post("/api/auth/register", json={"name": "Tracker User", "email": "tracker@example.com", "password": "password123"})
        headers = {"Authorization": f"Bearer {registered.json['token']}"}
        created = client.post("/api/applications", headers=headers, json={"company": "TCS", "role": "Software Developer", "status": "Assessment", "location": "Pune"})
        assert created.status_code == 201
        application_id = created.json["application"]["id"]
        listed = client.get("/api/applications?q=TCS", headers=headers)
        assert listed.json["total"] == 1
        assert listed.json["counts"]["Assessment"] == 1
        updated = client.patch(f"/api/applications/{application_id}", headers=headers, json={"status": "Interview", "notes": "Technical round"})
        assert updated.json["application"]["status"] == "Interview"
        assert client.get(f"/api/applications/{application_id}").status_code == 401
        assert client.delete(f"/api/applications/{application_id}", headers=headers).status_code == 200
        assert client.get("/api/applications", headers=headers).json["total"] == 0
    with app.app_context():
        db.drop_all()


def test_new_analysis_endpoints_and_skill_plan_progress():
    app = create_app(TestConfig)
    with app.test_client() as client:
        registered = client.post("/api/auth/register", json={"name": "Tools User", "email": "tools@example.com", "password": "password123"})
        headers = {"Authorization": f"Bearer {registered.json['token']}"}
        client.post("/api/profile", headers=headers, json={"target_role": "Python Developer", "skills": ["python"]})
        bullet = client.post("/api/resume/improve-bullet", headers=headers, json={"bullet": "Made a website using HTML CSS JavaScript."})
        assert bullet.status_code == 200
        jd = client.post("/api/jobs/analyze-description", headers=headers, json={"description": "Location: Remote\nRequired: Python, Flask, SQL. Preferred: Docker."})
        assert jd.status_code == 200
        assert "python" in jd.json["analysis"]["matched_skills"]
        assert "flask" in jd.json["analysis"]["missing_skills"]
        gd = client.post("/api/gd/evaluate", headers=headers, json={"topic": "AI and jobs", "position": "FOR", "response": "I believe AI changes jobs. For example, it automates repeated work. In conclusion, people can focus on new skills."})
        assert gd.status_code == 200
        assert "metrics" in gd.json
        readiness = client.get("/api/career-readiness", headers=headers).json["readiness"]
        assert readiness["communication"] == gd.json["metrics"]["communication"]
        assert readiness["weakest_area"]
        assert len(readiness["improvements"]) == 3
        gaps = client.get("/api/skill-gaps", headers=headers).json["analysis"]["missing"][0]
        task = gaps["plan"][0]
        updated = client.patch(f"/api/skill-gaps/tasks/{task['id']}", headers=headers, json={"completed": True})
        assert updated.json["progress"] == 14
        assert client.get("/api/skill-gaps", headers=headers).json["analysis"]["missing"][0]["progress"] == 14
    with app.app_context():
        db.drop_all()


def test_google_login_creates_user_without_password():
    app = create_app(TestConfig)
    claims = {"email": "google@example.com", "name": "Google User", "email_verified": True, "picture": "https://example.com/avatar.png"}
    with patch("routes.api.id_token.verify_oauth2_token", return_value=claims):
        with app.test_client() as client:
            response = client.post("/api/auth/google", json={"credential": "verified-id-token"})
            assert response.status_code == 200
            assert response.json["new_user"] is True
            assert response.json["user"]["auth_provider"] == "google"
            assert response.json["user"]["picture"] == claims["picture"]
    with app.app_context():
        user = User.query.filter_by(email="google@example.com").first()
        assert user is not None
        assert user.password_hash is None
        assert user.auth_provider == "google"
        db.drop_all()


def test_google_login_reuses_existing_email_account():
    app = create_app(TestConfig)
    with app.app_context():
        user = User(name="Existing User", email="existing@example.com", auth_provider="email")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
    claims = {"email": "existing@example.com", "name": "Google Name", "email_verified": True}
    with patch("routes.api.id_token.verify_oauth2_token", return_value=claims):
        with app.test_client() as client:
            response = client.post("/api/auth/google", json={"credential": "verified-id-token"})
            assert response.status_code == 409
            assert response.json["error"] == "An account already exists with this email using email/password. Sign in with your password first."
    with app.app_context():
        assert User.query.filter_by(email="existing@example.com").count() == 1
        db.drop_all()


def test_google_login_rejects_invalid_token():
    app = create_app(TestConfig)
    with patch("routes.api.id_token.verify_oauth2_token", side_effect=ValueError):
        with app.test_client() as client:
            response = client.post("/api/auth/google", json={"credential": "invalid-token"})
            assert response.status_code == 401
            assert response.json["error"] == "Google sign-in could not be verified. Please try again."
    with app.app_context():
        db.drop_all()


def test_career_roadmap_persists_and_tracks_task_progress():
    app = create_app(TestConfig)
    with app.test_client() as client:
        registered = client.post("/api/auth/register", json={"name": "Roadmap User", "email": "roadmap@example.com", "password": "password123"})
        headers = {"Authorization": f"Bearer {registered.json['token']}"}
        client.post("/api/profile", headers=headers, json={"degree": "B.Tech", "target_role": "Python Developer", "skills": ["python"], "completed": True})
        generated = client.post("/api/career-roadmap", headers=headers, json={"experience_level": "Beginner", "hours_per_week": 8, "timeline": "6 months"})
        assert generated.status_code == 200
        roadmap = generated.json["roadmap"]
        assert roadmap["target_role"] == "Python Developer"
        assert roadmap["total_tasks"] > 0
        task_id = roadmap["phases"][0]["tasks"][0]["id"]
        updated = client.patch(f"/api/career-roadmap/tasks/{task_id}", headers=headers, json={"completed": True})
        assert updated.status_code == 200
        assert updated.json["roadmap"]["completed_tasks"] == 1
        fetched = client.get("/api/career-roadmap", headers=headers)
        assert fetched.status_code == 200
        assert fetched.json["roadmap"]["progress"] > 0
        regenerated = client.post("/api/career-roadmap/update", headers=headers)
        assert regenerated.status_code == 200
        assert regenerated.json["roadmap"]["completed_tasks"] == 1
    with app.app_context():
        db.drop_all()


def test_career_roadmap_requires_authentication_and_valid_input():
    app = create_app(TestConfig)
    with app.test_client() as client:
        assert client.post("/api/career-roadmap", json={}).status_code == 401
        registered = client.post("/api/auth/register", json={"name": "Validation User", "email": "validation@example.com", "password": "password123"})
        headers = {"Authorization": f"Bearer {registered.json['token']}"}
        invalid = client.post("/api/career-roadmap", headers=headers, json={"hours_per_week": 0})
        assert invalid.status_code == 400
    with app.app_context():
        db.drop_all()


def test_skill_gaps_and_readiness_use_authenticated_profile_data():
    app = create_app(TestConfig)
    with app.test_client() as client:
        registered = client.post("/api/auth/register", json={"name": "Signals User", "email": "signals@example.com", "password": "password123"})
        headers = {"Authorization": f"Bearer {registered.json['token']}"}
        client.post("/api/profile", headers=headers, json={"target_role": "Python Developer", "skills": ["python"], "completed": True})
        gaps = client.get("/api/skill-gaps", headers=headers)
        readiness = client.get("/api/career-readiness", headers=headers)
        assert gaps.status_code == 200
        assert gaps.json["target_role"] == "Python Developer"
        assert any(item["skill"] == "python" for item in gaps.json["analysis"]["strong"])
        assert any(item["skill"] == "flask" for item in gaps.json["analysis"]["missing"])
        assert readiness.status_code == 200
        assert 0 <= readiness.json["readiness"]["overall"] <= 100
    with app.app_context():
        db.drop_all()


def test_dashboard_exposes_daily_actions_and_achievements():
    app = create_app(TestConfig)
    with app.test_client() as client:
        registered = client.post("/api/auth/register", json={"name": "Achievement User", "email": "achievement@example.com", "password": "password123"})
        headers = {"Authorization": f"Bearer {registered.json['token']}"}
        client.post("/api/profile", headers=headers, json={"target_role": "Python Developer", "skills": ["python"], "completed": True})
        client.post("/api/career-roadmap", headers=headers, json={"hours_per_week": 8, "timeline": "6 months"})
        dashboard = client.get("/api/dashboard", headers=headers)
        assert dashboard.status_code == 200
        assert dashboard.json["daily_actions"]
        assert any(item["key"] == "roadmap25" for item in dashboard.json["achievements"])
        achievements = client.get("/api/achievements", headers=headers)
        assert achievements.status_code == 200
    with app.app_context():
        db.drop_all()


def test_mock_interview_is_personalized_and_persists_history():
    app = create_app(TestConfig)
    with app.test_client() as client:
        registered = client.post("/api/auth/register", json={"name": "Interview User", "email": "interview@example.com", "password": "password123"})
        headers = {"Authorization": f"Bearer {registered.json['token']}"}
        questions = client.post("/api/interview/questions", headers=headers, json={"role": "Python Developer", "skills": ["python", "sql"], "interview_type": "Technical", "difficulty": "Hard", "job_description": "Build APIs"})
        assert questions.status_code == 200
        assert len(questions.json["questions"]) > 0
        assert "python" in questions.json["questions"][0]["question"].lower()
        evaluation = client.post("/api/interview/evaluate", headers=headers, json={"role": "Python Developer", "question": questions.json["questions"][0]["question"], "answer": "I built an API, improved response time by 20%, and documented the result.", "interview_type": "Technical"})
        assert evaluation.status_code == 200
        assert evaluation.json["score"] > 0
        assert "suggested_structure" in evaluation.json
        history = client.get("/api/interview/history", headers=headers)
        assert history.status_code == 200
        assert len(history.json["history"]) == 1
    with app.app_context():
        db.drop_all()
