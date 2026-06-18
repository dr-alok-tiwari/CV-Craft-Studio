"""
CV-Craft-Studio - ATS Resume Scorer
Transparent rule-based scoring system. No AI APIs.

The scorer keeps a stable 100-point ATS score, and adds role-aware context
for Academic/Research, Data/Analytics, Healthcare Analytics, Tech, Business,
and general professional resumes.
"""

import re
from typing import Dict, List, Tuple


ACTION_VERBS = [
    'analyzed', 'designed', 'developed', 'implemented', 'optimized', 'automated',
    'led', 'coordinated', 'evaluated', 'improved', 'built', 'delivered',
    'researched', 'presented', 'managed', 'created', 'established', 'launched',
    'streamlined', 'enhanced', 'reduced', 'increased', 'generated', 'achieved',
    'collaborated', 'facilitated', 'initiated', 'executed', 'deployed', 'integrated',
    'monitored', 'resolved', 'supervised', 'trained', 'mentored', 'spearheaded',
    'conceptualized', 'formulated', 'negotiated', 'identified', 'transformed',
    'accelerated', 'administered', 'advised', 'allocated', 'applied', 'assessed',
    'authored', 'budgeted', 'calculated', 'classified', 'compiled', 'conducted',
    'configured', 'consolidated', 'constructed', 'consulted', 'customized',
    'debugged', 'defined', 'demonstrated', 'directed', 'discovered', 'documented',
    'drove', 'engineered', 'ensured', 'established', 'extracted', 'forecasted',
    'guided', 'handled', 'headed', 'highlighted', 'identified', 'illustrated',
    'influenced', 'informed', 'inspected', 'installed', 'integrated',
    'interpreted', 'introduced', 'investigated', 'maintained', 'measured',
    'migrated', 'modeled', 'modified', 'operated', 'orchestrated', 'organized',
    'planned', 'prepared', 'processed', 'produced', 'programmed', 'proposed',
    'provided', 'published', 'recommended', 'redesigned', 'refined', 'reported',
    'restructured', 'reviewed', 'scheduled', 'secured', 'selected', 'simplified',
    'solved', 'standardized', 'strategized', 'structured', 'supported',
    'synthesized', 'tested', 'tracked', 'updated', 'utilized', 'validated',
    'visualized', 'wrote'
]

WEAK_WORDS = [
    'helped', 'assisted', 'worked on', 'was responsible for', 'tried',
    'attempted', 'participated in', 'involved in', 'handled', 'dealt with',
    'was part of', 'contributed to', 'did', 'made'
]

QUANT_PATTERNS = [
    r'\d+\s*%',
    r'\$\s*\d+',
    r'\d+\s*(?:million|billion|thousand|k|m|b)',
    r'\d+\s*(?:users|customers|clients|employees|team members|projects|reports|students|participants|papers|citations|classes|sessions|datasets|patients|images|records)',
    r'(?:increased|decreased|reduced|improved|grew|boosted|cut|saved|achieved).*\d+',
    r'\d+x\s*(?:faster|better|more)',
    r'from\s+\d+.*to\s+\d+',
    r'top\s+\d+',
    r'\d+\s*(?:hours|days|weeks|months|years)',
    r'\d+\+',
]

ROLE_PROFILES = {
    'academic_research': {
        'label': 'Academic / Research CV',
        'signals': ['phd', 'research', 'publication', 'journal', 'conference', 'teaching', 'faculty', 'professor', 'assistant professor', 'doctoral', 'thesis', 'grant', 'reviewer', 'course', 'scholar'],
        'keywords': ['research', 'publication', 'teaching', 'methodology', 'journal', 'conference', 'grant', 'supervision', 'curriculum', 'thesis', 'reviewer', 'citation', 'course', 'workshop'],
    },
    'healthcare_analytics': {
        'label': 'Healthcare Analytics / AI in Healthcare',
        'signals': ['healthcare', 'medical', 'clinical', 'patient', 'hospital', 'biomedical', 'diagnosis', 'mri', 'x-ray', 'ct', 'ehr', 'public health', 'epidemiology'],
        'keywords': ['healthcare', 'clinical', 'patient', 'medical', 'biomedical', 'diagnosis', 'imaging', 'ehr', 'hospital', 'predictive modeling', 'ethics', 'privacy'],
    },
    'data_analytics': {
        'label': 'Data / Analytics Resume',
        'signals': ['data analyst', 'analytics', 'dashboard', 'sql', 'python', 'power bi', 'tableau', 'excel', 'kpi', 'forecasting', 'business intelligence'],
        'keywords': ['python', 'sql', 'excel', 'dashboard', 'tableau', 'power bi', 'statistics', 'forecasting', 'etl', 'kpi', 'visualization', 'reporting'],
    },
    'software_tech': {
        'label': 'Software / Tech Resume',
        'signals': ['software', 'developer', 'engineer', 'api', 'backend', 'frontend', 'cloud', 'docker', 'kubernetes', 'github', 'devops', 'microservices'],
        'keywords': ['software', 'api', 'cloud', 'docker', 'kubernetes', 'git', 'testing', 'deployment', 'architecture', 'backend', 'frontend', 'security'],
    },
    'business_management': {
        'label': 'Business / Management Resume',
        'signals': ['business analyst', 'management', 'stakeholder', 'strategy', 'consulting', 'market research', 'operations', 'sales', 'finance', 'risk'],
        'keywords': ['stakeholder', 'strategy', 'process improvement', 'project management', 'consulting', 'market', 'operations', 'finance', 'risk', 'leadership'],
    },
    'general': {
        'label': 'General ATS Resume',
        'signals': [],
        'keywords': [],
    },
}


def _phrase_in_text(text: str, phrase: str) -> bool:
    """Safe phrase search that avoids substring false positives where possible."""
    text = text.lower()
    phrase = phrase.lower().strip()
    if not phrase:
        return False
    pattern = re.escape(phrase)
    if phrase[0].isalnum():
        pattern = r'(?<![a-z0-9])' + pattern
    if phrase[-1].isalnum():
        pattern = pattern + r'(?![a-z0-9])'
    return bool(re.search(pattern, text, re.IGNORECASE))


def _count_phrases(text: str, phrases: List[str]) -> int:
    return sum(1 for phrase in phrases if _phrase_in_text(text, phrase))


def _detected_sections(parsed: Dict) -> List[str]:
    sections = parsed.get('sections', {}) or {}
    return [k for k, v in sections.items() if k != '_header' and str(v).strip()]


def detect_resume_track(parsed: Dict) -> str:
    """Auto-detect the most likely resume track from content signals."""
    text = (parsed.get('raw_text') or '').lower()
    sections = ' '.join(_detected_sections(parsed)).lower()
    combined = f'{text}\n{sections}'
    scores = {}
    for key, profile in ROLE_PROFILES.items():
        if key == 'general':
            continue
        signal_hits = _count_phrases(combined, profile['signals'])
        keyword_hits = _count_phrases(combined, profile['keywords'])
        scores[key] = signal_hits * 2 + keyword_hits

    if not scores:
        return 'general'
    best = max(scores, key=scores.get)
    return best if scores[best] >= 3 else 'general'


def score_contact_info(parsed: Dict) -> Tuple[int, List[str], List[str]]:
    """Score contact information (max 10)."""
    score = 0
    strengths = []
    issues = []
    contact = parsed.get('contact', {})

    if contact.get('email'):
        score += 3
        strengths.append('Email address present')
    else:
        issues.append('Missing email address — critical for ATS')

    if contact.get('phone'):
        score += 3
        strengths.append('Phone number present')
    else:
        issues.append('Missing phone number')

    if contact.get('linkedin'):
        score += 2
        strengths.append('LinkedIn profile linked')
    else:
        issues.append('LinkedIn URL missing — add to improve recruiter reach')

    if contact.get('name'):
        score += 2
        strengths.append('Name detected')
    else:
        issues.append('Name not clearly detected at top of resume')

    return min(score, 10), strengths, issues


def score_summary(parsed: Dict) -> Tuple[int, List[str], List[str]]:
    """Score professional summary (max 10)."""
    sections = parsed.get('sections', {})
    summary_text = sections.get('summary', '')
    score = 0
    strengths = []
    issues = []

    if not summary_text or len(summary_text.strip()) < 30:
        issues.append('Professional summary missing or too short')
        return 0, strengths, issues

    score += 5
    strengths.append('Professional summary present')

    word_count = len(summary_text.split())
    if 40 <= word_count <= 100:
        score += 3
        strengths.append('Summary length is appropriate (40–100 words)')
    elif word_count > 100:
        issues.append('Summary is too long — aim for 40–100 words')
        score += 1
    else:
        issues.append('Summary is too brief — expand to 40–100 words')
        score += 1

    keyword_hits = _count_phrases(summary_text, ACTION_VERBS[:20])
    if keyword_hits >= 2:
        score += 2
        strengths.append('Summary uses strong action language')
    else:
        issues.append('Summary lacks strong action verbs')

    return min(score, 10), strengths, issues


def score_education(parsed: Dict) -> Tuple[int, List[str], List[str]]:
    """Score education section (max 10)."""
    sections = parsed.get('sections', {})
    edu_text = sections.get('education', '')
    score = 0
    strengths = []
    issues = []

    if not edu_text or len(edu_text.strip()) < 20:
        issues.append('Education section missing or too brief')
        return 0, strengths, issues

    score += 5
    strengths.append('Education section present')

    degree_keywords = ['bachelor', 'master', 'phd', 'ph.d', 'b.tech', 'm.tech', 'mba', 'bsc', 'msc', 'b.com', 'm.com', 'be', 'me', 'diploma', 'degree', 'graduate', 'postgraduate', 'pgdm', 'bba']
    has_degree = any(_phrase_in_text(edu_text, kw) for kw in degree_keywords)
    if has_degree:
        score += 3
        strengths.append('Degree/qualification mentioned')
    else:
        issues.append('Degree type not clearly mentioned')

    if re.search(r'(20\d\d|19\d\d)', edu_text):
        score += 2
        strengths.append('Education dates/years present')
    else:
        issues.append('Education years/dates missing')

    return min(score, 10), strengths, issues


def score_skills(parsed: Dict) -> Tuple[int, List[str], List[str]]:
    """Score skills section (max 15)."""
    sections = parsed.get('sections', {})
    skills_text = sections.get('skills', '')
    score = 0
    strengths = []
    issues = []

    if not skills_text or len(skills_text.strip()) < 20:
        issues.append('Skills section missing — this is critical for ATS parsing')
        return 0, strengths, issues

    score += 5
    strengths.append('Skills section present')

    skill_items = re.split(r'[,|\n•·\-]+', skills_text)
    skill_items = [s.strip() for s in skill_items if len(s.strip()) > 1]
    num_skills = len(skill_items)

    if num_skills >= 10:
        score += 5
        strengths.append(f'{num_skills} skills listed — good coverage')
    elif num_skills >= 5:
        score += 3
        strengths.append(f'{num_skills} skills listed — consider adding more')
        issues.append('Add more relevant skills (target 10+)')
    else:
        issues.append(f'Only {num_skills} skills listed — ATS needs more keywords')
        score += 1

    tech_terms = [
        'python', 'sql', 'excel', 'java', 'javascript', 'r', 'tableau', 'powerbi', 'power bi',
        'machine learning', 'deep learning', 'nlp', 'aws', 'azure', 'gcp', 'docker', 'kubernetes',
        'git', 'html', 'css', 'react', 'node', 'django', 'flask', 'spark', 'hadoop', 'sas',
        'spss', 'stata', 'matlab', 'tensorflow', 'pytorch', 'research design', 'statistical analysis',
        'regression', 'survey design', 'clinical analytics', 'medical imaging'
    ]
    tech_hits = _count_phrases(skills_text, tech_terms)
    if tech_hits >= 3:
        score += 5
        strengths.append(f'{tech_hits} technical/research tools or methods mentioned')
    elif tech_hits >= 1:
        score += 2
        issues.append('Include more specific tools, methods, and technologies')
    else:
        issues.append('No specific technologies/tools/methods detected in skills')

    return min(score, 15), strengths, issues


def score_experience(parsed: Dict) -> Tuple[int, List[str], List[str]]:
    """Score experience/projects (max 20)."""
    sections = parsed.get('sections', {})
    exp_text = sections.get('experience', '') + '\n' + sections.get('projects', '') + '\n' + sections.get('internship', '')
    score = 0
    strengths = []
    issues = []

    if len(exp_text.strip()) < 50:
        issues.append('No experience, internship, or project content found')
        return 0, strengths, issues

    bullets = re.findall(r'^[•\-*\d+\.)]\s*.+', exp_text, re.MULTILINE)
    if len(bullets) >= 5:
        score += 8
        strengths.append(f'{len(bullets)} bullet points found')
    elif len(bullets) >= 2:
        score += 4
        issues.append('Add more bullet points for each role/project (target 3–5 each)')
    else:
        issues.append('Use bullet points to list accomplishments — not paragraphs')

    if re.search(r'(20\d\d|19\d\d)', exp_text):
        score += 4
        strengths.append('Work/project dates present')
    else:
        issues.append('Add dates to experience/project entries')

    if len(exp_text.split()) > 100:
        score += 4
        strengths.append('Experience section has sufficient detail')
    else:
        issues.append('Expand experience descriptions with more detail')

    org_pattern = r'(?:at|@|for)\s+([A-Z][a-zA-Z0-9\s&,]+)'
    orgs = re.findall(org_pattern, exp_text)
    if orgs:
        score += 4
        strengths.append('Organization names detected in experience')
    else:
        score += 2

    return min(score, 20), strengths, issues


def score_action_verbs(parsed: Dict) -> Tuple[int, List[str], List[str]]:
    """Score use of action verbs (max 10)."""
    text = parsed.get('raw_text', '').lower()
    strengths = []
    issues = []

    unique_verbs = sorted({verb for verb in ACTION_VERBS if _phrase_in_text(text, verb)})

    if len(unique_verbs) >= 8:
        score = 10
        strengths.append(f'{len(unique_verbs)} unique action verbs used')
    elif len(unique_verbs) >= 5:
        score = 7
        strengths.append(f'{len(unique_verbs)} action verbs used')
        issues.append('Use more varied action verbs (target 8+)')
    elif len(unique_verbs) >= 2:
        score = 4
        issues.append(f'Only {len(unique_verbs)} action verbs found — use more')
    else:
        score = 1
        issues.append('Almost no action verbs found — critical issue')

    weak_found = [word for word in WEAK_WORDS if _phrase_in_text(text, word)]
    if weak_found:
        issues.append(f'Weak phrasing detected: {", ".join(weak_found[:3])}')

    return min(score, 10), strengths, issues


def score_quantified(parsed: Dict) -> Tuple[int, List[str], List[str]]:
    """Score quantified achievements (max 10)."""
    text = parsed.get('raw_text', '')
    strengths = []
    issues = []

    quant_hits = []
    for pattern in QUANT_PATTERNS:
        quant_hits.extend(re.findall(pattern, text, re.IGNORECASE))
    unique_hits = len(set(str(hit) for hit in quant_hits))

    if unique_hits >= 5:
        score = 10
        strengths.append(f'{unique_hits} quantified achievements/metrics found')
    elif unique_hits >= 3:
        score = 7
        strengths.append(f'{unique_hits} quantified metrics found')
        issues.append('Add more measurable results (percentages, numbers, outcomes)')
    elif unique_hits >= 1:
        score = 4
        issues.append('Very few quantified achievements — add metrics where truthful')
    else:
        score = 0
        issues.append('No quantified achievements — add real numbers/percentages where applicable')

    return min(score, 10), strengths, issues


def score_ats_formatting(parsed: Dict) -> Tuple[int, List[str], List[str]]:
    """Score ATS formatting simplicity (max 10)."""
    text = parsed.get('raw_text', '')
    score = 8
    strengths = ['Standard text content detected (ATS-readable)']
    issues = []

    if len(re.findall(r'[|│]', text)) > 10:
        score -= 2
        issues.append('Possible table or column separator detected — avoid in ATS version')
    if len(re.findall(r'[★☆●○■□►▶]', text)) > 3:
        score -= 2
        issues.append('Special symbols/graphics detected — may confuse ATS parsers')

    detected_sections = _detected_sections(parsed)
    if len(detected_sections) >= 4:
        score += 2
        strengths.append(f'{len(detected_sections)} distinct sections detected')
    else:
        issues.append('Section headings may not be ATS-friendly — use standard headings')

    return max(0, min(score, 10)), strengths, issues


def score_length_readability(parsed: Dict) -> Tuple[int, List[str], List[str]]:
    """Score resume length and readability (max 5)."""
    text = parsed.get('raw_text', '')
    word_count = len(text.split())
    strengths = []
    issues = []

    if 300 <= word_count <= 700:
        score = 5
        strengths.append(f'Resume length is optimal ({word_count} words)')
    elif 200 <= word_count < 300:
        score = 3
        issues.append(f'Resume is short ({word_count} words) — consider expanding')
    elif 700 < word_count <= 1000:
        score = 3
        issues.append(f'Resume is a bit long ({word_count} words) — consider trimming')
    elif word_count > 1000:
        score = 1
        issues.append(f'Resume is very long ({word_count} words) — aim for 1–2 pages')
    else:
        score = 1
        issues.append(f'Resume is very short ({word_count} words) — add more content')

    return min(score, 5), strengths, issues


def score_role_context(parsed: Dict, track: str) -> Dict:
    """Return role-aware diagnostics without changing the 100-point ATS score."""
    text = parsed.get('raw_text', '')
    sections = parsed.get('sections', {}) or {}
    profile = ROLE_PROFILES.get(track, ROLE_PROFILES['general'])
    label = profile['label']
    keywords = profile.get('keywords', [])
    matched_keywords = [kw for kw in keywords if _phrase_in_text(text, kw)]
    score = min(6, len(matched_keywords))
    strengths = []
    issues = []
    suggestions = []

    if track == 'academic_research':
        if sections.get('publications') or _phrase_in_text(text, 'publication') or _phrase_in_text(text, 'journal'):
            score += 2
            strengths.append('Academic evidence detected: publications/research outputs are visible')
        else:
            issues.append('Academic CV mode: add a Publications / Working Papers section if applicable')
        if _phrase_in_text(text, 'teaching') or _phrase_in_text(text, 'course') or _phrase_in_text(text, 'class'):
            score += 1
            strengths.append('Teaching evidence detected')
        else:
            suggestions.append('Academic CV mode: add Teaching Experience, courses taught, sessions, evaluations, or student mentoring')
        if any(_phrase_in_text(text, term) for term in ['methodology', 'regression', 'machine learning', 'qualitative', 'quantitative', 'survey', 'experiment', 'case study']):
            score += 1
            strengths.append('Research methods or analytical capability detected')
        else:
            suggestions.append('Academic CV mode: add research methods, datasets, tools, or domain techniques')
        if not any(_phrase_in_text(text, term) for term in ['grant', 'funded', 'project', 'consulting', 'mdp', 'fdp', 'workshop']):
            suggestions.append('Academic CV mode: add grants, sponsored projects, workshops/FDP/MDP, invited talks, or outreach where truthful')

    elif track == 'healthcare_analytics':
        if any(_phrase_in_text(text, term) for term in ['patient', 'clinical', 'hospital', 'medical imaging', 'mri', 'x-ray', 'ehr']):
            score += 2
            strengths.append('Healthcare domain evidence detected')
        else:
            issues.append('Healthcare role fit: add clinical/medical context, datasets, or healthcare outcomes if applicable')
        if any(_phrase_in_text(text, term) for term in ['privacy', 'ethics', 'hipaa', 'consent', 'bias', 'fairness']):
            score += 1
        else:
            suggestions.append('Healthcare role fit: mention privacy, ethics, fairness, validation, or clinical safety when relevant')

    elif track == 'data_analytics':
        if any(_phrase_in_text(text, term) for term in ['dashboard', 'kpi', 'power bi', 'tableau', 'sql', 'python']):
            score += 2
            strengths.append('Analytics tool/domain evidence detected')
        else:
            issues.append('Data role fit: add tools such as SQL, Python, Excel, Tableau/Power BI, dashboards, or KPIs')
        if any(_phrase_in_text(text, term) for term in ['business impact', 'stakeholder', 'decision', 'reporting time', 'forecast']):
            score += 1
        else:
            suggestions.append('Data role fit: connect analysis to business decisions, stakeholders, time savings, or revenue/cost impact')

    elif track == 'software_tech':
        if any(_phrase_in_text(text, term) for term in ['github', 'api', 'deployment', 'testing', 'docker', 'cloud', 'architecture']):
            score += 2
            strengths.append('Software delivery evidence detected')
        else:
            issues.append('Tech role fit: add repositories, deployments, APIs, tests, architecture, or production scale where applicable')

    elif track == 'business_management':
        if any(_phrase_in_text(text, term) for term in ['stakeholder', 'strategy', 'market', 'operations', 'risk', 'consulting', 'project management']):
            score += 2
            strengths.append('Business/management language detected')
        else:
            issues.append('Business role fit: add stakeholder, strategy, operations, market, finance, or risk outcomes')

    else:
        suggestions.append('General ATS mode: tailor the resume to a specific target role for sharper keyword matching')

    score = max(0, min(10, score))
    if matched_keywords:
        strengths.append(f'{label}: matched role keywords — {", ".join(matched_keywords[:6])}')
    elif track != 'general':
        issues.append(f'{label}: role-specific keywords are thin; add only truthful domain terms')

    return {
        'track': track,
        'label': label,
        'score': score,
        'max': 10,
        'matched_keywords': matched_keywords[:12],
        'missing_keywords': [kw for kw in keywords if kw not in matched_keywords][:12],
        'strengths': strengths,
        'issues': issues,
        'suggestions': suggestions,
    }


def detect_red_flags(parsed: Dict, track: str | None = None) -> List[Dict]:
    """Return list of detected red flags with severity."""
    flags = []
    contact = parsed.get('contact', {})
    sections = parsed.get('sections', {})
    text = parsed.get('raw_text', '')
    word_count = len(text.split())
    track = track or detect_resume_track(parsed)

    if not contact.get('email'):
        flags.append({'flag': 'Missing email', 'severity': 'critical'})
    if not contact.get('phone'):
        flags.append({'flag': 'Missing phone number', 'severity': 'high'})
    if not contact.get('linkedin'):
        flags.append({'flag': 'Missing LinkedIn URL', 'severity': 'medium'})

    if not sections.get('summary'):
        flags.append({'flag': 'No professional summary/objective', 'severity': 'high'})
    if not sections.get('skills'):
        flags.append({'flag': 'No skills section', 'severity': 'critical'})
    if not sections.get('experience') and not sections.get('projects') and not sections.get('internship'):
        flags.append({'flag': 'No experience, internship, or projects', 'severity': 'critical'})
    if not sections.get('education'):
        flags.append({'flag': 'No education section', 'severity': 'high'})

    action_verb_count = _count_phrases(text, ACTION_VERBS)
    if action_verb_count < 3:
        flags.append({'flag': 'Insufficient action verbs', 'severity': 'high'})

    weak_count = _count_phrases(text, WEAK_WORDS)
    if weak_count >= 3:
        flags.append({'flag': f'Passive/weak language detected ({weak_count} instances)', 'severity': 'medium'})

    quant_hits = sum(1 for pattern in QUANT_PATTERNS if re.search(pattern, text, re.IGNORECASE))
    if quant_hits == 0:
        flags.append({'flag': 'No quantified achievements (numbers/percentages)', 'severity': 'high'})

    if word_count > 1000:
        flags.append({'flag': f'Resume too long ({word_count} words)', 'severity': 'medium'})
    elif word_count < 150:
        flags.append({'flag': f'Resume too short ({word_count} words)', 'severity': 'high'})

    verb_freq = {}
    for verb in ACTION_VERBS:
        count = len(re.findall(r'(?<![a-z0-9])' + re.escape(verb) + r'(?![a-z0-9])', text.lower()))
        if count > 3:
            verb_freq[verb] = count
    if verb_freq:
        most_repeated = max(verb_freq, key=lambda key: verb_freq[key])
        flags.append({'flag': f'Repeated action verb: "{most_repeated}" used {verb_freq[most_repeated]}x', 'severity': 'low'})

    if track == 'academic_research':
        if not sections.get('publications') and not _phrase_in_text(text, 'publication') and not _phrase_in_text(text, 'journal'):
            flags.append({'flag': 'Academic CV mode: publications / working papers not visible', 'severity': 'medium'})
        if not any(_phrase_in_text(text, term) for term in ['teaching', 'course', 'class', 'student', 'mentored']):
            flags.append({'flag': 'Academic CV mode: teaching/mentoring evidence not visible', 'severity': 'medium'})
    if track == 'healthcare_analytics' and not any(_phrase_in_text(text, term) for term in ['patient', 'clinical', 'hospital', 'medical', 'healthcare']):
        flags.append({'flag': 'Healthcare fit: clinical/healthcare context is weak', 'severity': 'medium'})

    return flags


def score_resume(parsed: Dict) -> Dict:
    """Run full ATS scoring on a parsed resume and return a scoring report."""
    track = detect_resume_track(parsed)
    role_context = score_role_context(parsed, track)

    contact_score, contact_strengths, contact_issues = score_contact_info(parsed)
    summary_score, summary_strengths, summary_issues = score_summary(parsed)
    edu_score, edu_strengths, edu_issues = score_education(parsed)
    skills_score, skills_strengths, skills_issues = score_skills(parsed)
    exp_score, exp_strengths, exp_issues = score_experience(parsed)
    verb_score, verb_strengths, verb_issues = score_action_verbs(parsed)
    quant_score, quant_strengths, quant_issues = score_quantified(parsed)
    format_score, format_strengths, format_issues = score_ats_formatting(parsed)
    length_score, length_strengths, length_issues = score_length_readability(parsed)

    total = (contact_score + summary_score + edu_score + skills_score +
             exp_score + verb_score + quant_score + format_score + length_score)

    all_strengths = (contact_strengths + summary_strengths + edu_strengths +
                     skills_strengths + exp_strengths + verb_strengths +
                     quant_strengths + format_strengths + length_strengths +
                     role_context.get('strengths', []))
    all_issues = (contact_issues + summary_issues + edu_issues + skills_issues +
                  exp_issues + verb_issues + quant_issues + format_issues + length_issues +
                  role_context.get('issues', []) + role_context.get('suggestions', []))

    critical_fixes = [issue for issue in all_issues if any(word in issue.lower() for word in ['missing', 'no ', 'critical', 'almost no', 'not visible'])]
    quick_wins = [issue for issue in all_issues if issue not in critical_fixes]
    red_flags = detect_red_flags(parsed, track)

    return {
        'total_score': max(0, min(100, total)),
        'max_score': 100,
        'grade': _get_grade(total),
        'detected_track': track,
        'role_context': role_context,
        'sections': {
            'contact_info': {'score': contact_score, 'max': 10},
            'professional_summary': {'score': summary_score, 'max': 10},
            'education': {'score': edu_score, 'max': 10},
            'skills': {'score': skills_score, 'max': 15},
            'experience_projects': {'score': exp_score, 'max': 20},
            'action_verbs': {'score': verb_score, 'max': 10},
            'quantified_achievements': {'score': quant_score, 'max': 10},
            'ats_formatting': {'score': format_score, 'max': 10},
            'length_readability': {'score': length_score, 'max': 5},
        },
        'strengths': _dedupe(all_strengths),
        'issues': _dedupe(all_issues),
        'critical_fixes': _dedupe(critical_fixes),
        'quick_wins': _dedupe(quick_wins),
        'red_flags': red_flags,
    }


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        key = item.lower().strip()
        if key and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _get_grade(score: int) -> str:
    if score >= 85:
        return 'A - Excellent'
    if score >= 70:
        return 'B - Good'
    if score >= 55:
        return 'C - Average'
    if score >= 40:
        return 'D - Needs Work'
    return 'F - Critical Issues'
