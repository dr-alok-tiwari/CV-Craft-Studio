"""
CV-Craft-Studio - Resume Improvement Report Generator
Creates a concise offline report from ATS, role-aware diagnostics, and JD analyses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List


def _lines(items: List[str], prefix: str = "- ") -> str:
    if not items:
        return f"{prefix}None detected\n"
    return "".join(f"{prefix}{item}\n" for item in items)


def _top_actions(ats_score: Dict[str, Any] | None, jd_match: Dict[str, Any] | None) -> List[str]:
    actions: List[str] = []
    if ats_score:
        actions.extend(ats_score.get('critical_fixes', [])[:4])
        actions.extend(ats_score.get('quick_wins', [])[:4])
        role_context = ats_score.get('role_context', {}) or {}
        actions.extend(role_context.get('issues', [])[:3])
        actions.extend(role_context.get('suggestions', [])[:3])
    if jd_match:
        missing_skills = jd_match.get('missing_skills', [])[:5]
        missing_keywords = jd_match.get('missing_keywords', [])[:8]
        if missing_skills:
            actions.append("Verify whether you genuinely have these JD skills before adding them: " + ", ".join(missing_skills))
        if missing_keywords:
            actions.append("Naturally integrate applicable JD keywords: " + ", ".join(missing_keywords))
    seen = set()
    unique = []
    for item in actions:
        key = item.lower().strip()
        if key and key not in seen:
            unique.append(item)
            seen.add(key)
    return unique[:12]


def generate_improvement_report(resume_data: Dict[str, Any], ats_score: Dict[str, Any] | None = None,
                                jd_match: Dict[str, Any] | None = None) -> bytes:
    """Return a UTF-8 TXT report summarizing score, role fit, gaps, and next actions."""
    personal = resume_data.get('personal', {}) if resume_data else {}
    name = personal.get('name') or 'Unnamed Candidate'
    generated_at = datetime.now().strftime('%d %b %Y, %I:%M %p')
    role_context = (ats_score or {}).get('role_context', {}) or {}

    report = []
    report.append("CV-Craft-Studio Resume Improvement Report\n")
    report.append("=" * 52 + "\n")
    report.append(f"Candidate: {name}\n")
    report.append(f"Generated: {generated_at}\n")
    report.append("Privacy: Generated locally; no paid or external AI API used.\n\n")

    report.append("1. Score Summary\n")
    report.append("-" * 52 + "\n")
    if ats_score:
        report.append(f"ATS score: {ats_score.get('total_score', '-')}/100 ({ats_score.get('grade', '-')})\n")
        if role_context:
            report.append(f"Detected resume track: {role_context.get('label', 'General ATS Resume')}\n")
            report.append(f"Role-context score: {role_context.get('score', '-')}/{role_context.get('max', 10)}\n")
    else:
        report.append("ATS score: Not generated yet. Run ATS Resume Scorer for a fuller report.\n")
    if jd_match:
        report.append(f"JD fit score: {jd_match.get('fit_score', '-')}/100\n")
        report.append(f"Keyword match: {jd_match.get('keyword_match_pct', 0)}% ({jd_match.get('keyword_match_count', 0)}/{jd_match.get('keyword_total', 0)})\n")
        report.append(f"Skill match: {jd_match.get('skill_match_pct', 0)}% ({len(jd_match.get('matched_skills', []))}/{len(jd_match.get('jd_skills', []))})\n")
    else:
        report.append("JD fit score: Not generated yet. Paste a JD and run the matcher.\n")
    report.append("\n")

    if role_context:
        report.append("2. Role-Specific Diagnostics\n")
        report.append("-" * 52 + "\n")
        matched = role_context.get('matched_keywords', [])
        missing = role_context.get('missing_keywords', [])
        report.append("Matched role keywords:\n")
        report.append(_lines(matched[:12]))
        report.append("\nRole-specific gaps / suggestions:\n")
        report.append(_lines((role_context.get('issues', []) + role_context.get('suggestions', []))[:12]))
        report.append("\n")
        next_section = 3
    else:
        next_section = 2

    report.append(f"{next_section}. Strengths\n")
    report.append("-" * 52 + "\n")
    report.append(_lines((ats_score or {}).get('strengths', [])[:10]))
    report.append("\n")
    next_section += 1

    report.append(f"{next_section}. Issues and Red Flags\n")
    report.append("-" * 52 + "\n")
    report.append(_lines((ats_score or {}).get('issues', [])[:12]))
    flags = (ats_score or {}).get('red_flags', [])
    if flags:
        report.append("\nRed flags:\n")
        for flag in flags[:10]:
            report.append(f"- [{flag.get('severity', 'info')}] {flag.get('flag', '')}\n")
    report.append("\n")
    next_section += 1

    report.append(f"{next_section}. JD Keyword and Skill Gaps\n")
    report.append("-" * 52 + "\n")
    if jd_match:
        report.append("Skills already present:\n")
        report.append(_lines(jd_match.get('matched_skills', [])[:15]))
        report.append("\nSkills missing but add only if truthful:\n")
        report.append(_lines(jd_match.get('missing_skills', [])[:15]))
        report.append("\nMissing JD keywords:\n")
        report.append(_lines(jd_match.get('missing_keywords', [])[:20]))
    else:
        report.append("No JD analysis available. Run Job Description Matcher first.\n")
    report.append("\n")
    next_section += 1

    report.append(f"{next_section}. Priority Action Plan\n")
    report.append("-" * 52 + "\n")
    actions = _top_actions(ats_score, jd_match)
    if actions:
        for i, action in enumerate(actions, 1):
            report.append(f"{i}. {action}\n")
    else:
        report.append("1. Upload/build a resume, then run ATS and JD analysis.\n")
    report.append("\n")
    next_section += 1

    report.append(f"{next_section}. Responsible Use Note\n")
    report.append("-" * 52 + "\n")
    report.append("Do not claim skills, tools, certifications, metrics, publications, employers, or achievements unless they are accurate and verifiable. Replace every bracketed placeholder with real evidence only if true.\n")

    return "".join(report).encode('utf-8')
