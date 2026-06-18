"""Quick verification script for CV-Craft-Studio."""
import sys
sys.path.insert(0, '.')

print("=" * 60)
print("CV-Craft-Studio - Verification")
print("=" * 60)

# Test 1: Parser
from modules.parser import parse_resume, parse_resume_file, MAX_UPLOAD_BYTES
from modules.sample_data import SAMPLE_FRESHER_RESUME, SAMPLE_JD_DATA_ANALYST, DEMO_BUILDER_DATA
parsed = parse_resume(SAMPLE_FRESHER_RESUME.encode(), 'test.txt')
wc = parsed['word_count']
sc = len([k for k, v in parsed['sections'].items() if k != '_header' and v.strip()])
print(f"[OK] Parser: {wc} words, {sc} sections detected")
print(f"     Contact: {parsed['contact']['name']}, {parsed['contact']['email']}")

# Test 2: Upload size guard
try:
    parse_resume_file(b'x' * (MAX_UPLOAD_BYTES + 1), 'large.txt')
    raise AssertionError('Upload size guard did not trigger')
except ValueError:
    print("[OK] Upload Guard: files over 10 MB are rejected")

# Test 3: Scorer
from modules.scorer import score_resume
score = score_resume(parsed)
print(f"[OK] Scorer: {score['total_score']}/100 - {score['grade']}")
print(f"     Red flags: {len(score['red_flags'])}")

# Test 4: JD Matcher
from modules.jd_matcher import match_resume_to_jd
match = match_resume_to_jd(parsed, SAMPLE_JD_DATA_ANALYST)
print(f"[OK] JD Matcher: Fit={match['fit_score']}, KW match={match['keyword_match_pct']}%")

# Test 5: Bullet Improver
from modules.bullet_improver import improve_bullet
result = improve_bullet("Worked on sales data.")
print(f"[OK] Bullet Improver: '{result['original'][:30]}' -> '{result['improved'][:40]}'")

# Test 6: Export TXT and builder decode compatibility
from modules.export_utils import export_txt, resume_data_to_text
resume_text = resume_data_to_text(DEMO_BUILDER_DATA)
assert isinstance(resume_text.decode('utf-8'), str)
txt = export_txt(DEMO_BUILDER_DATA)
print(f"[OK] TXT Export: {len(txt)} bytes, decode-safe text helper")

# Test 7: Export PDF
from modules.export_utils import export_pdf
pdf = export_pdf(DEMO_BUILDER_DATA)
print(f"[OK] PDF Export: {len(pdf)} bytes")

# Test 8: Export DOCX
from modules.export_utils import export_docx
docx = export_docx(DEMO_BUILDER_DATA)
print(f"[OK] DOCX Export: {len(docx)} bytes")

# Test 9: LaTeX Export
from modules.latex_exporter import export_latex_resume
tex = export_latex_resume(DEMO_BUILDER_DATA)
assert "\\documentclass" in tex and "\\begin{document}" in tex
print(f"[OK] LaTeX Export: {len(tex)} chars")

# Test 10: ATS Rewrite
from modules.ats_rewriter import rewrite_resume_from_ats
rewrite_result = rewrite_resume_from_ats(DEMO_BUILDER_DATA, parsed, score, match)
assert rewrite_result.get('resume_data') and rewrite_result.get('new_score') is not None
print(f"[OK] ATS Rewrite: {rewrite_result.get('old_score')} -> {rewrite_result.get('new_score')}")

# Test 11: HTML Template
from modules.templates import render_resume_html
html = render_resume_html(DEMO_BUILDER_DATA)
print(f"[OK] HTML Template: {len(html)} chars")

# Test 12: Role Profiles
from modules.role_profiles import get_all_roles, get_role_profile
roles = get_all_roles()
profile = get_role_profile('Data Analyst')
print(f"[OK] Role Profiles: {len(roles)} roles, DA has {len(profile['keywords'])} keywords")

print()
print("=" * 60)
print("ALL VERIFICATION TESTS PASSED!")
print("Run: streamlit run app.py")
print("=" * 60)
