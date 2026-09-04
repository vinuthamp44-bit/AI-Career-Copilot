import re

SKILL_GROUPS = {
    "Technical skills": ["python", "javascript", "react", "sql", "flask", "java", "machine learning", "data analysis", "rest api", "html", "css", "git"],
    "Tools": ["docker", "aws", "figma", "tableau", "power bi", "kubernetes", "excel", "postman"],
    "Soft skills": ["communication", "leadership", "collaboration", "problem solving", "adaptability", "mentoring"],
}

ROLE_REQUIREMENTS = {
    "Frontend Developer": ["javascript", "react", "html", "css", "git", "rest api"],
    "Data Analyst": ["sql", "python", "excel", "tableau", "data analysis", "communication"],
    "Backend Engineer": ["python", "flask", "sql", "rest api", "docker", "git"],
    "Product Designer": ["figma", "user research", "communication", "collaboration", "prototyping"],
    "Machine Learning Engineer": ["python", "machine learning", "sql", "docker", "aws", "data analysis"],
}


def _present(text, term):
    return term in text.lower()


def analyze_resume(text):
    lower = text.lower()
    found = [skill for group in SKILL_GROUPS.values() for skill in group if _present(lower, skill)]
    sections = {
        "skills": sorted(set(found)),
        "education": bool(re.search(r"education|university|college|bachelor|master|degree", lower)),
        "projects": bool(re.search(r"projects?|built|developed|portfolio", lower)),
        "experience": bool(re.search(r"experience|intern|work history|employment", lower)),
        "certifications": bool(re.search(r"certif|credential|aws certified|google", lower)),
    }
    strengths = ["Clear skills signal" if sections["skills"] else "Room to surface more skills", "Projects are visible" if sections["projects"] else "Add 1-2 outcome-led projects"]
    weaknesses = [label.title() + " section is missing" for label in ("education", "experience", "certifications") if not sections[label]]
    score = min(98, 38 + len(sections["skills"]) * 4 + sum(sections[key] for key in sections if key != "skills") * 8)
    return {"score": score, "sections": sections, "strengths": strengths, "weaknesses": weaknesses, "suggestions": ["Quantify impact with metrics", "Tailor the summary to a target role", "Use strong action verbs at the start of bullets"]}


def compare_resume(text, description, role):
    resume_skills = set(analyze_resume(text)["sections"]["skills"])
    required = set(ROLE_REQUIREMENTS.get(role, []))
    required.update(skill for group in SKILL_GROUPS.values() for skill in group if _present(description, skill))
    matching = sorted(resume_skills & required)
    missing = sorted(required - resume_skills)
    score = round(len(matching) / len(required) * 100) if required else 0
    return {"score": score, "matching_keywords": matching, "missing_keywords": missing, "recommendations": [f"Add evidence for {skill} in a project or experience bullet" for skill in missing[:4]]}


def role_matches(skills, target_role=""):
    owned = {skill.lower().strip() for skill in skills if isinstance(skill, str)}
    roles = []
    for role, required in ROLE_REQUIREMENTS.items():
        matched = sorted(owned & set(required))
        score = round(len(matched) / len(required) * 100)
        roles.append({"role": role, "match": score, "matched_skills": matched, "missing_skills": sorted(set(required) - owned), "reason": f"You match {len(matched)} of {len(required)} core skills."})
    if target_role:
        target = target_role.lower().strip()
        roles.sort(key=lambda item: (item["role"].lower() != target, -item["match"]))
    else:
        roles.sort(key=lambda item: item["match"], reverse=True)
    return roles


def interview_questions(role, skills, job_description=""):
    context = next((skill for skill in skills if isinstance(skill, str)), "your strongest technical skill")
    job_hint = " Review the job requirements and connect your answer to them." if job_description.strip() else ""
    return [{"type": "Technical", "question": f"Walk me through a project where you used {context} to solve a real problem.{job_hint}"}, {"type": "Technical", "question": f"How would you approach your first 30 days as a {role}?"}, {"type": "HR", "question": "Tell me about a time you received difficult feedback and what you changed afterward."}]


def roadmap(skills, target_role):
    required = ROLE_REQUIREMENTS.get(target_role, ROLE_REQUIREMENTS.get("Frontend Developer"))
    missing = [skill for skill in required if skill not in {item.lower() for item in skills}]
    return [{"title": skill.title(), "category": next((name for name, values in SKILL_GROUPS.items() if skill in values), "Technical skills"), "status": "Next up" if index == 0 else "Queued", "resource": f"Build a small {skill.title()} project and document the outcome."} for index, skill in enumerate(missing[:6])]


def evaluate_answer(answer):
    words = len(answer.split())
    score = min(96, 35 + words * 2 + (15 if any(token in answer.lower() for token in ("result", "impact", "because", "learned")) else 0))
    feedback = "Strong structure and useful evidence." if score >= 70 else "Add a specific situation, your actions, and the measurable result."
    return score, feedback
