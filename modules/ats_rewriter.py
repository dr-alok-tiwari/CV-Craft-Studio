"""
CV-Craft-Studio - ATS Score Based Resume Rewriter
Local, rule-based resume rewrite logic. It improves structure, summary,
section coverage, action verbs, skills, and ATS formatting without using
external AI APIs or inventing unverifiable achievements.
"""

from __future__ import annotations

import copy
import re
from typing import Any, Dict, Iterable, List, Tuple

from modules.parser import extract_keywords, parse_resume
from modules.scorer import score_resume
from modules.export_utils import resume_data_to_text

ACTION_VERB_POOL = [
    "Developed", "Implemented", "Analyzed", "Optimized", "Designed",
    "Built", "Delivered", "Evaluated", "Automated", "Coordinated",
    "Researched", "Presented", "Managed", "Created", "Improved",
    "Validated", "Documented", "Integrated", "Monitored", "Led",
]

TECH_TERMS = {
    "python", "r", "sql", "excel", "tableau", "power bi", "powerbi", "java",
    "javascript", "html", "css", "react", "node", "mongodb", "firebase",
    "aws", "azure", "gcp", "docker", "kubernetes", "git", "github", "flask",
    "django", "spark", "hadoop", "tensorflow", "pytorch", "machine learning",
    "deep learning", "nlp", "computer vision", "statistics", "analytics",
    "data analysis", "visualization", "dashboard", "cloud", "database",
}

ANALYTICAL_TERMS = {
    "data analysis", "statistical analysis", "problem solving", "forecasting",
    "reporting", "dashboarding", "business analysis", "research", "modeling",
    "data visualization", "requirements analysis", "process improvement",
}

SOFT_TERMS = {
    "communication", "presentation", "leadership", "collaboration", "mentoring",
    "stakeholder management", "adaptability", "self-learning", "teamwork",
}

WEAK_REPLACEMENTS = {
    "helped": "Supported",
    "assisted": "Supported",
    "worked on": "Contributed to",
    "was responsible for": "Managed",
    "participated in": "Collaborated on",
    "involved in": "Contributed to",
    "did": "Executed",
    "made": "Created",
}

STOPWORDS = {
    "resume", "curriculum", "vitae", "email", "phone", "linkedin", "github",
    "profile", "summary", "education", "experience", "project", "projects",
    "skills", "certifications", "achievements", "college", "university",
}


def _as_list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [x.strip() for x in re.split(r"[,\n;|]+", value) if x.strip()]
    if isinstance(value, dict):
        out: List[str] = []
        for v in value.values():
            out.extend(_as_list(v))
        return out
    if isinstance(value, Iterable):
        return [str(x).strip() for x in value if str(x).strip()]
    return [str(value).strip()]


def _dedupe(items: List[str], limit: int | None = None) -> List[str]:
    seen = set()
    out = []
    for item in items:
        clean = re.sub(r"\s+", " ", str(item)).strip(" .;•-–—")
        if not clean:
            continue
        key = clean.lower()
        if key not in seen:
            seen.add(key)
            out.append(clean)
    return out[:limit] if limit else out


def _raw_section_lines(text: str, limit: int = 10) -> List[str]:
    lines = []
    for line in (text or "").splitlines():
        clean = re.sub(r"^[\s•\-*–—\d\.)]+", "", line).strip()
        if len(clean) > 3:
            lines.append(clean)
    return _dedupe(lines, limit)


def _extract_years(text: str) -> str:
    years = re.findall(r"(?:19|20)\d{2}(?:\s*[–-]\s*(?:Present|present|(?:19|20)\d{2}))?", text or "")
    return " – ".join(_dedupe(years, 2))


def _ensure_contact(data: Dict, parsed: Dict) -> None:
    personal = data.setdefault("personal", {})
    contact = (parsed or {}).get("contact", {}) or {}
    for field in ["name", "email", "phone", "linkedin", "github"]:
        if not personal.get(field) and contact.get(field):
            personal[field] = contact[field]


def _skill_candidates(raw_text: str, jd_match: Dict | None = None) -> List[str]:
    candidates: List[str] = []
    lower = (raw_text or "").lower()
    for term in sorted(TECH_TERMS | ANALYTICAL_TERMS | SOFT_TERMS):
        if term in lower:
            candidates.append(term.title() if len(term) > 2 else term.upper())
    for kw in extract_keywords(raw_text or "", top_n=35):
        if len(kw) > 2 and kw.lower() not in STOPWORDS:
            candidates.append(kw.title())
    if jd_match:
        # Only include missing JD skills if they already appear somewhere in the resume text.
        for skill in jd_match.get("missing_skills", [])[:10]:
            if skill and skill.lower() in lower:
                candidates.append(skill)
    return _dedupe(candidates, 30)


def _ensure_skills(data: Dict, raw_text: str, jd_match: Dict | None, actions: List[str]) -> None:
    skills = data.get("skills") or {"technical": [], "analytical": [], "soft": []}
    if isinstance(skills, list):
        skills = {"technical": skills, "analytical": [], "soft": []}
    for key in ["technical", "analytical", "soft"]:
        skills.setdefault(key, [])

    existing = _as_list(skills)
    candidates = [s for s in _skill_candidates(raw_text, jd_match) if s.lower() not in {e.lower() for e in existing}]

    for cand in candidates:
        c = cand.lower()
        if c in SOFT_TERMS:
            skills["soft"].append(cand)
        elif c in ANALYTICAL_TERMS:
            skills["analytical"].append(cand)
        else:
            skills["technical"].append(cand)

    skills["technical"] = _dedupe(skills.get("technical", []), 18)
    skills["analytical"] = _dedupe(skills.get("analytical", []), 10)
    skills["soft"] = _dedupe(skills.get("soft", []), 8)
    data["skills"] = skills

    if len(_as_list(skills)) >= 10:
        actions.append("Expanded the skills section to improve ATS keyword coverage using terms already present in the resume/JD evidence.")


def _infer_role(data: Dict, raw_text: str) -> str:
    text = (raw_text or "").lower()
    skills = ", ".join(_as_list(data.get("skills")))
    if any(x in text for x in ["professor", "research", "publication", "teaching"]):
        return "research and academic professional"
    if any(x in text for x in ["data", "analytics", "python", "sql", "dashboard"]):
        return "data and analytics professional"
    if any(x in text for x in ["software", "developer", "react", "cloud"]):
        return "technology professional"
    if skills:
        return "professional"
    return "candidate"


def _ensure_summary(data: Dict, raw_text: str, actions: List[str]) -> None:
    current = (data.get("summary") or "").strip()
    words = len(current.split())
    needs_rewrite = words < 40 or words > 100
    if current and not needs_rewrite:
        return

    role = _infer_role(data, raw_text)
    skills = _dedupe(_as_list(data.get("skills")), 8)
    skill_text = ", ".join(skills[:6]) if skills else "role-relevant tools, structured problem solving, and evidence-based communication"
    has_projects = bool(data.get("projects") or data.get("_raw_projects"))
    has_exp = bool(data.get("experience") or data.get("_raw_experience"))
    proof = "professional experience" if has_exp else "projects" if has_projects else "documented academic and professional work"

    data["summary"] = (
        f"ATS-focused {role} with experience across {proof}. Skilled in {skill_text}. "
        "Strong record of analyzing requirements, building structured solutions, documenting outputs, "
        "and communicating results clearly for recruiters, hiring managers, and automated screening systems. "
        "Focused on measurable outcomes, clean formatting, and role-aligned keywords."
    )
    actions.append("Rebuilt the professional summary to reach the 40–100 word ATS-friendly range with stronger action language.")


def _choose_verb(text: str, idx: int = 0) -> str:
    lower = text.lower()
    if any(k in lower for k in ["data", "analysis", "report", "dashboard", "model"]):
        return "Analyzed"
    if any(k in lower for k in ["develop", "build", "web", "app", "system", "software", "code"]):
        return "Developed"
    if any(k in lower for k in ["lead", "team", "coordinate", "event", "volunteer"]):
        return "Coordinated"
    if any(k in lower for k in ["research", "paper", "study", "survey"]):
        return "Researched"
    return ACTION_VERB_POOL[idx % len(ACTION_VERB_POOL)]


def _improve_bullet(text: str, idx: int = 0) -> Tuple[str, bool]:
    original = re.sub(r"^[\s•\-*–—\d\.)]+", "", text or "").strip()
    if not original:
        return "", False

    changed = False
    improved = original
    low = improved.lower()
    for weak, repl in WEAK_REPLACEMENTS.items():
        if low.startswith(weak):
            improved = re.sub(re.escape(weak), repl, improved, count=1, flags=re.IGNORECASE)
            changed = True
            break

    first_word = re.match(r"^[A-Za-z]+", improved)
    if not first_word or first_word.group(0).lower() not in {v.lower() for v in ACTION_VERB_POOL}:
        verb = _choose_verb(improved, idx)
        improved = f"{verb} {improved[0].lower() + improved[1:] if improved else improved}"
        changed = True

    if not re.search(r"\d", improved):
        improved = improved.rstrip(".") + "; add a verified number, percentage, user count, or outcome metric before final submission"
        changed = True

    # Keep bullet concise enough for one to two lines.
    words = improved.split()
    if len(words) > 32:
        improved = " ".join(words[:32]).rstrip(" ,;")
        changed = True

    if improved and not improved.endswith("."):
        improved += "."
    return improved, changed


def _ensure_entries_from_raw(data: Dict, key: str, raw_key: str, title: str, actions: List[str]) -> None:
    if data.get(key):
        return
    raw = data.get(raw_key, "")
    bullets = _raw_section_lines(raw, 6)
    if not bullets:
        return
    if key in {"experience", "internships"}:
        data[key] = [{
            "title": title,
            "company": "From uploaded resume",
            "duration": _extract_years(raw),
            "location": "",
            "bullets": bullets,
        }]
    elif key == "projects":
        data[key] = [{
            "title": title,
            "tech": "",
            "year": _extract_years(raw),
            "bullets": bullets,
        }]
    actions.append(f"Converted raw {title.lower()} text into structured ATS-readable bullet points.")


def _ensure_education_from_raw(data: Dict, actions: List[str]) -> None:
    if data.get("education"):
        return
    raw = data.get("_raw_education", "")
    lines = _raw_section_lines(raw, 4)
    if not lines:
        return
    data["education"] = [{
        "degree": lines[0],
        "institution": lines[1] if len(lines) > 1 else "",
        "year": _extract_years(raw),
        "grade": "",
        "details": " ".join(lines[2:4]),
    }]
    actions.append("Converted raw education text into a structured Education entry with standard heading and year field.")


def _improve_all_bullets(data: Dict, actions: List[str]) -> None:
    changed_count = 0
    for section in ["experience", "internships", "projects"]:
        for entry in data.get(section, []) or []:
            new_bullets = []
            for idx, bullet in enumerate(entry.get("bullets", []) or []):
                improved, changed = _improve_bullet(bullet, idx)
                if improved:
                    new_bullets.append(improved)
                if changed:
                    changed_count += 1
            if new_bullets:
                entry["bullets"] = new_bullets[:6]
    if changed_count:
        actions.append(f"Rewrote {changed_count} bullet point(s) with stronger action verbs, cleaner phrasing, and metric prompts where verified numbers were absent.")


def _ensure_section_minimums(data: Dict, actions: List[str]) -> None:
    _ensure_education_from_raw(data, actions)
    _ensure_entries_from_raw(data, "experience", "_raw_experience", "Professional Experience", actions)
    _ensure_entries_from_raw(data, "projects", "_raw_projects", "Key Project", actions)


def rewrite_resume_from_ats(
    resume_data: Dict,
    parsed_resume: Dict | None,
    ats_score: Dict | None,
    jd_match: Dict | None = None,
) -> Dict:
    """Rewrite the full resume using generated ATS score feedback."""
    data = copy.deepcopy(resume_data or {})
    parsed_resume = parsed_resume or {}
    raw_text = parsed_resume.get("raw_text") or resume_data_to_text(data)
    actions: List[str] = []

    _ensure_contact(data, parsed_resume)
    _ensure_section_minimums(data, actions)
    _ensure_skills(data, raw_text, jd_match, actions)
    _ensure_summary(data, raw_text, actions)
    _improve_all_bullets(data, actions)

    # Preserve raw parsed sections for LaTeX export if the builder could not fully structure them.
    sections = parsed_resume.get("sections", {}) or {}
    raw_map = {
        "_raw_education": "education",
        "_raw_experience": "experience",
        "_raw_projects": "projects",
        "_raw_certifications": "certifications",
        "_raw_achievements": "achievements",
    }
    for raw_key, section_key in raw_map.items():
        if not data.get(raw_key) and sections.get(section_key):
            data[raw_key] = sections[section_key]

    updated_text = resume_data_to_text(data)
    updated_parsed = parse_resume(updated_text.encode("utf-8"), "ats_rewritten_resume.txt")
    updated_score = score_resume(updated_parsed)

    old_total = (ats_score or {}).get("total_score")
    new_total = updated_score.get("total_score")
    if old_total is not None:
        actions.append(f"Re-scored the rewritten resume locally: {old_total}/100 → {new_total}/100.")

    return {
        "resume_data": data,
        "updated_text": updated_text,
        "parsed_resume": updated_parsed,
        "updated_score": updated_score,
        "actions": _dedupe(actions),
        "old_score": old_total,
        "new_score": new_total,
        "remaining_issues": updated_score.get("issues", []),
    }
