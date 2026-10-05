import re

SKILL_GROUPS = {
    "Technical skills": ["python", "javascript", "react", "node.js", "sql", "flask", "java", "machine learning", "data analysis", "rest api", "html", "css", "git"],
    "Tools": ["docker", "aws", "figma", "tableau", "power bi", "kubernetes", "excel", "postman"],
    "Soft skills": ["communication", "leadership", "collaboration", "problem solving", "adaptability", "mentoring"],
}

ROLE_REQUIREMENTS = {
    "Frontend Developer": ["javascript", "react", "html", "css", "git", "rest api"],
    "Software Developer": ["python", "java", "javascript", "sql", "git", "rest api"],
    "Full Stack Developer": ["javascript", "react", "node.js", "sql", "git", "rest api"],
    "Data Analyst": ["sql", "python", "excel", "tableau", "data analysis", "communication"],
    "Backend Engineer": ["python", "flask", "sql", "rest api", "docker", "git"],
    "Java Developer": ["java", "sql", "rest api", "git", "docker"],
    "Python Developer": ["python", "flask", "sql", "rest api", "git", "docker"],
    "AI/ML Engineer": ["python", "machine learning", "sql", "docker", "aws", "data analysis"],
    "Product Designer": ["figma", "user research", "communication", "collaboration", "prototyping"],
    "Machine Learning Engineer": ["python", "machine learning", "sql", "docker", "aws", "data analysis"],
    "UI/UX Designer": ["figma", "user research", "communication", "collaboration", "prototyping"],
}

GD_TOPICS = [
    "AI and jobs", "Work from home", "Degree vs skills", "Technical skills vs communication skills",
    "Social media", "Online education", "Startup vs MNC", "High salary vs learning opportunities",
    "Automation", "Remote work", "Leadership", "Teamwork",
]


def _present(text, term):
    return re.search(rf"(?<!\w){re.escape(term.lower())}(?!\w)", text.lower()) is not None


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
    recommendations = [f"Add evidence for {skill} in a project or experience bullet" for skill in missing[:4]]
    why_losing = "Your resume is well aligned with this role. Strengthen the evidence for the matched skills with measurable outcomes."
    if missing:
        listed = " and ".join(missing[:2])
        why_losing = f"Your technical profile is missing evidence for {listed}. Showing these skills in a project or experience bullet could improve your match."
    fastest_way = [f"Add {skill} to a focused project or experience bullet" for skill in missing[:3]]
    fastest_way.append("Rewrite one project bullet with a measurable result")
    return {"score": score, "matching_keywords": matching, "missing_keywords": missing, "recommendations": recommendations, "why_losing": why_losing, "fastest_way_to_improve": fastest_way}


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


def interview_questions(role, skills, job_description="", interview_type="Mixed", difficulty="Medium", resume_text=""):
    context = next((skill for skill in skills if isinstance(skill, str)), "your strongest technical skill")
    job_hint = " Review the job requirements and connect your answer to them." if job_description.strip() else ""
    project = next((line.strip() for line in resume_text.splitlines() if any(word in line.lower() for word in ("project", "built", "developed"))), "a project from your resume")
    questions = [{"type": "Technical", "question": f"Walk me through {project} and explain how you used {context} to solve a real problem.{job_hint}"}, {"type": "Technical", "question": f"At {difficulty.lower()} difficulty, how would you debug a production issue involving {context}?"}, {"type": "Behavioral", "question": "Tell me about a time you received difficult feedback. Use Situation, Task, Action, and Result."}, {"type": "HR", "question": f"Why are you pursuing a {role} role, and what would you contribute in your first 90 days?"}]
    if interview_type != "Mixed":
        questions = [question for question in questions if question["type"].lower() == interview_type.lower()] or questions
    return questions


def roadmap(skills, target_role):
    required = ROLE_REQUIREMENTS.get(target_role, ROLE_REQUIREMENTS.get("Frontend Developer"))
    missing = [skill for skill in required if skill not in {item.lower() for item in skills}]
    return [{"title": skill.title(), "category": next((name for name, values in SKILL_GROUPS.items() if skill in values), "Technical skills"), "status": "Next up" if index == 0 else "Queued", "resource": f"Build a small {skill.title()} project and document the outcome."} for index, skill in enumerate(missing[:6])]


def career_roadmap(skills, target_role, experience_level="Beginner", hours_per_week=8, timeline="6 months", completed_titles=None):
    normalized = {item.lower().strip() for item in skills if isinstance(item, str) and item.strip()}
    required = ROLE_REQUIREMENTS.get(target_role, ROLE_REQUIREMENTS.get("Frontend Developer"))
    missing = [skill for skill in required if skill not in normalized]
    completed_titles = {item.lower().strip() for item in (completed_titles or [])}
    phases = []
    phase_specs = [
        ("Foundations", "Build a reliable study routine and close the first skill gap.", missing[:2]),
        ("Core role skills", "Develop working competence in the skills most important for the target role.", missing[2:4]),
        ("Real-world practice", "Turn the most important skills into evidence through a practical project.", missing[4:]),
        ("Interview and job preparation", "Convert your progress into interview-ready stories and application evidence.", []),
    ]
    for index, (title, objective, phase_skills) in enumerate(phase_specs):
        phase_topics = phase_skills or ["portfolio", "communication", "technical interview"]
        task_titles = [f"Study {skill.title()} fundamentals" for skill in phase_skills]
        task_titles += ["Complete a focused practice exercise", "Document what you learned"]
        phases.append({
            "position": index + 1,
            "title": title,
            "duration": f"{max(1, min(4, len(task_titles)))} weeks",
            "objective": objective,
            "skills": phase_skills,
            "topics": phase_topics,
            "practice_tasks": [f"Practice {topic}" for topic in phase_topics],
            "recommended_project": {"title": f"{target_role} portfolio project", "difficulty": experience_level, "skills": phase_skills or ["communication"]},
            "completion_criteria": [f"Complete {len(task_titles)} tasks", "Write one reflection on the outcome"],
            "tasks": [{"week": min(index + 1, 4), "position": task_index + 1, "title": title_text, "description": f"Spend about {max(25, round(240 / max(1, hours_per_week)))} minutes making measurable progress.", "estimated_minutes": max(25, round(240 / max(1, hours_per_week))), "completed": title_text.lower() in completed_titles} for task_index, title_text in enumerate(task_titles)],
        })
    total_tasks = sum(len(phase["tasks"]) for phase in phases)
    completed_tasks = sum(task["completed"] for phase in phases for task in phase["tasks"])
    technical = round(len(normalized & set(required)) / len(required) * 100) if required else 0
    readiness = {"overall": round((technical + min(100, completed_tasks / max(1, total_tasks) * 100) + (35 if "projects" in normalized else 0) + 40) / 3), "technical": technical, "resume": 40, "projects": 35 if "projects" in normalized else 0, "interview": 40, "job_match": technical}
    skill_analysis = {"current": sorted(normalized), "required": [{"skill": skill, "importance": "High" if index < 3 else "Medium", "current_level": "Strong" if skill in normalized else "Missing", "required_level": "Working proficiency", "gap": 0 if skill in normalized else 1, "status": "Strong" if skill in normalized else "Missing"} for index, skill in enumerate(required)]}
    return {"phases": phases, "readiness": readiness, "skill_analysis": skill_analysis, "completed_tasks": completed_tasks, "total_tasks": total_tasks, "milestones": [{"position": index + 1, "title": title, "required_progress": progress, "completed": readiness["overall"] >= progress} for index, (title, progress) in enumerate((("Foundation complete", 20), ("Core skills complete", 45), ("First project complete", 65), ("Interview ready", 85), ("Job ready", 100)))]}


def skill_gap_analysis(skills, target_role):
    owned = {item.lower().strip() for item in skills if isinstance(item, str) and item.strip()}
    required = ROLE_REQUIREMENTS.get(target_role, ROLE_REQUIREMENTS.get("Frontend Developer"))
    result = []
    for index, skill in enumerate(required):
        status = "Strong" if skill in owned else "Missing"
        if skill in owned and index >= max(1, len(required) // 2):
            status = "Needs improvement"
        result.append({"skill": skill, "status": status, "current_level": "Working proficiency" if skill in owned else "Not demonstrated", "required_level": "Working proficiency", "priority": "High" if index < 3 else "Medium", "why_it_matters": f"{skill.title()} is part of the core {target_role} requirements.", "recommended_action": f"Practice {skill.title()} through a small project and document the result."})
    return {"strong": [item for item in result if item["status"] == "Strong"], "needs_improvement": [item for item in result if item["status"] == "Needs improvement"], "missing": [item for item in result if item["status"] == "Missing"], "all": result}


def achievement_definitions(resume, ats, interview_count, roadmap_progress):
    return [
        {"key": "resume", "title": "First Resume Analysis", "description": "Your resume has been analyzed.", "unlocked": bool(resume)},
        {"key": "ats80", "title": "ATS Score Above 80", "description": "You reached an ATS match score above 80.", "unlocked": bool(ats and ats.get("score", 0) >= 80)},
        {"key": "interview", "title": "First Mock Interview", "description": "You completed your first interview response.", "unlocked": interview_count > 0},
        {"key": "roadmap25", "title": "Roadmap 25% Complete", "description": "You completed a quarter of your roadmap.", "unlocked": roadmap_progress >= 25},
        {"key": "roadmap50", "title": "Roadmap 50% Complete", "description": "You completed half of your roadmap.", "unlocked": roadmap_progress >= 50},
        {"key": "jobready", "title": "Job Ready", "description": "Your career readiness score reached 80 or more.", "unlocked": False},
    ]


def evaluate_answer(answer, question="", interview_type="Mixed"):
    words = len(answer.split())
    score = min(96, 35 + words * 2 + (15 if any(token in answer.lower() for token in ("result", "impact", "because", "learned")) else 0))
    lower = answer.lower()
    has_structure = any(token in lower for token in ("first", "then", "finally", "situation", "result"))
    has_evidence = any(token in lower for token in ("built", "used", "improved", "reduced", "%", "users"))
    feedback = "Strong structure and useful evidence." if score >= 70 else "Add a specific situation, your actions, and the measurable result."
    return {"score": score, "technical_accuracy": min(100, score + (8 if has_evidence else 0)), "communication": min(100, score + (6 if has_structure else 0)), "relevance": score, "structure": min(100, score + (8 if has_structure else 0)), "problem_solving": min(100, score + (5 if has_evidence else 0)), "strengths": ["Specific evidence" if has_evidence else "Willingness to explain your approach"], "weaknesses": ["Add measurable evidence" if not has_evidence else "Make the answer more concise"], "feedback": feedback, "suggested_structure": "Situation → Task → Action → Result" if interview_type.lower() in ("hr", "behavioral") else "Context → Approach → Trade-off → Result"}


def skill_learning_plan(skill):
    skill_name = skill.strip()
    curricula = {
        "sql": ["SQL basics and relational tables", "SELECT, WHERE, and ORDER BY", "INNER and LEFT JOINs", "GROUP BY and aggregate functions", "Subqueries and common table expressions", "SQL interview questions with query explanations", "Build a small database project and document your queries"],
        "python": ["Python data types and control flow", "Functions, collections, and comprehensions", "Modules, exceptions, and file handling", "Practice problem-solving with lists and dictionaries", "Use APIs and JSON in a small script", "Explain common Python interview questions", "Build and document a small Python project"],
        "javascript": ["JavaScript values, scope, and control flow", "Functions, arrays, and objects", "DOM events and browser APIs", "Promises, async/await, and fetch", "Practice debugging and small coding problems", "Review JavaScript interview questions", "Build a small interactive browser project"],
        "java": ["Java syntax, types, and control flow", "Classes, objects, and encapsulation", "Collections and generics", "Exceptions, interfaces, and inheritance", "Solve basic data-structure exercises", "Review Java interview questions", "Build a small Java application"],
    }
    topics = curricula.get(skill_name.lower(), [
        f"Learn {skill_name} fundamentals and core terminology",
        f"Practice the basic syntax and common operations in {skill_name}",
        f"Work through intermediate {skill_name} concepts and patterns",
        f"Solve practical exercises using {skill_name}",
        f"Apply {skill_name} with a realistic use case",
        f"Review common {skill_name} interview questions and explain your answers",
        f"Build a small {skill_name} project and document what you learned",
    ])
    return [{"day": index + 1, "title": title, "completed": False} for index, title in enumerate(topics)]


def improve_resume_bullet(bullet):
    original = " ".join(bullet.strip().split())
    replacements = ((r"\bmade\b", "developed"), (r"\bhelped\b", "supported"), (r"\bworked on\b", "contributed to"), (r"\bused\b", "utilized"))
    professional = original
    changes = []
    for pattern, replacement in replacements:
        updated, count = re.subn(pattern, lambda match: replacement.capitalize() if match.group(0)[0].isupper() else replacement, professional, count=1, flags=re.IGNORECASE)
        if count:
            professional = updated
            changes.append(f"Replaced '{pattern[2:-2]}' with '{replacement}' for a more precise action verb.")
            break
    professional = re.sub(r"\bhtml\s+css\s+(?:and\s+)?javascript\b", "HTML, CSS, and JavaScript", professional, flags=re.IGNORECASE)
    professional = re.sub(r"\s+([,.!?])", r"\1", professional).rstrip(" .") + "."
    if professional == original.rstrip(".") + ".":
        changes.append("Standardized capitalization and punctuation while preserving the original claim.")
    else:
        changes.append("Improved action-verb choice and formatting without adding metrics or experience.")
    ats_friendly = professional
    short = re.sub(r"\b(?:successfully|effectively|various|multiple|a|an|the)\b\s*", "", professional, flags=re.IGNORECASE)
    short = re.sub(r"\busing\b", "with", short, flags=re.IGNORECASE)
    short = re.sub(r"\s+", " ", short).strip()
    return {"professional": professional, "ats_friendly": ats_friendly, "short": short, "improvements": list(dict.fromkeys(changes))}


def analyze_job_description(description, profile_skills):
    text = description.strip()
    lower = text.lower()
    technical_skills = sorted({skill for group, values in SKILL_GROUPS.items() if group != "Soft skills" for skill in values if _present(lower, skill)})
    soft_skills = sorted({skill for skill in SKILL_GROUPS["Soft skills"] if _present(lower, skill)})
    preferred_markers = ("preferred", "prefer", "nice to have", "bonus", "plus", "desired")
    preferred = []
    required = []
    for skill in technical_skills:
        position = lower.find(skill)
        context = lower[max(0, position - 100):position]
        (preferred if any(marker in context for marker in preferred_markers) else required).append(skill)
    responsibilities = [line.strip(" -•\t") for line in text.splitlines() if re.search(r"\b(responsible for|you will|responsibilities|build|develop|design|maintain|collaborate|manage|deliver)\b", line, re.IGNORECASE)]
    experience = re.findall(r"\b(?:\d+\+?\s+years?[^,.\n]*|entry[- ]level|senior|junior|internship)\b", text, re.IGNORECASE)
    education = [line.strip(" -•\t") for line in text.splitlines() if re.search(r"\b(degree|bachelor|master|b\.tech|bsc|mba|education|graduate)\b", line, re.IGNORECASE)]
    location_match = re.search(r"\b(?:location|based in|located in)\s*[:\-]?\s*([^\n.;]+)", text, re.IGNORECASE)
    salary_match = re.search(r"(?:[$₹€£]\s?[\d,]+(?:\s?[-–]\s?[$₹€£]?\s?[\d,]+)?(?:\s?(?:k|lpa|lakh|per annum|annually))?|\b\d+(?:\.\d+)?\s?lpa\b)", text, re.IGNORECASE)
    owned = {skill.lower().strip() for skill in profile_skills if isinstance(skill, str)}
    matched = sorted(set(required) & owned)
    missing = sorted(set(required) - owned)
    score = round(len(matched) / len(required) * 100) if required else 0
    return {
        "required_technical_skills": required,
        "preferred_skills": preferred,
        "soft_skills": soft_skills,
        "responsibilities": list(dict.fromkeys(responsibilities))[:10],
        "experience_requirements": list(dict.fromkeys(item.strip() for item in experience)),
        "education_requirements": list(dict.fromkeys(education))[:5],
        "ats_keywords": sorted(set(technical_skills + soft_skills)),
        "location": location_match.group(1).strip() if location_match else "",
        "salary": salary_match.group(0).strip() if salary_match else "",
        "match_score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "recommended_skills": missing[:5],
    }


def evaluate_group_discussion(topic, position, response):
    text = " ".join(response.split())
    lower = text.lower()
    words = re.findall(r"\b[\w']+\b", lower)
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
    repeated = len(words) - len(set(words))
    repetition = min(100, round(repeated / max(1, len(words)) * 500))
    has_opening = any(term in lower for term in ("i believe", "in my view", "i agree", "i disagree", "from my perspective"))
    has_example = any(term in lower for term in ("for example", "for instance", "such as", "example"))
    has_conclusion = any(term in lower for term in ("in conclusion", "to conclude", "overall", "therefore", "to sum up"))
    has_linking = any(term in lower for term in ("first", "second", "because", "however", "furthermore", "also"))
    confidence = max(0, min(100, 78 - sum(lower.count(filler) for filler in (" um ", " uh ", " maybe ", " i think ")) * 8))
    scores = {
        "content": min(100, 35 + min(30, len(words) // 3) + 15 * bool(has_example)),
        "relevance": 80 if _present(lower, topic) or any(term in lower for term in topic.lower().split()) else 55,
        "structure": min(100, 45 + 20 * has_opening + 20 * has_linking + 15 * has_conclusion),
        "communication": min(100, 45 + min(35, len(sentences) * 7) + (10 if 60 <= len(words) <= 220 else 0)),
        "examples": 85 if has_example else 45,
        "confidence": confidence,
        "repetition": max(0, 100 - repetition),
        "conclusion": 85 if has_conclusion else 45,
    }
    overall = round(sum(scores.values()) / len(scores))
    strengths = max(("Content", "Structure", "Communication", "Examples", "Confidence", "Relevance"), key=lambda key: scores[key.lower()])
    improvements = []
    if not has_example:
        improvements.append("Support your main point with a specific example.")
    if not has_conclusion:
        improvements.append("Finish with a concise conclusion that restates your position.")
    if not has_linking:
        improvements.append("Use signposts such as 'first', 'however', and 'therefore' to connect ideas.")
    if repetition:
        improvements.append("Reduce repeated words and restate each idea only once.")
    if not improvements:
        improvements.append("Keep the same clear structure and make your example more specific.")
    lead = sentences[0] if sentences else ""
    example_sentence = next((sentence for sentence in sentences if re.search(r"\b(for example|for instance|such as|example)\b", sentence, re.IGNORECASE)), "")
    stance = "FOR" if position.upper() == "FOR" else "AGAINST"
    sample = f"I take the {stance} position on {topic}. {lead}"
    if example_sentence and example_sentence != lead:
        sample += f" {example_sentence}"
    conclusion = "support" if stance == "FOR" else "oppose"
    sample += f" In conclusion, these points explain why I {conclusion} this position."
    return {
        "score": overall, "metrics": scores, "strongest_point": f"{strengths} is your strongest measured area.",
        "improvements": improvements, "sample_answer": sample,
        "confidence_note": "Confidence is estimated from transcript wording and filler phrases, not vocal tone.",
    }
