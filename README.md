# 🧡 CV-Craft-Studio

**Build, score, refine, match, and export job-ready resumes — privately, locally, and without paid APIs.**

CV-Craft-Studio is a Streamlit-based resume and career-readiness studio designed for students, freshers, working professionals, academic applicants, and analytics/data roles. It provides resume parsing, guided resume building, ATS scoring, job description matching, bullet improvement, spelling/grammar checks, analytics, templates, version history, and export utilities.

---

## Key Features

- **Resume Parser**: Upload PDF, DOCX, DOC, or TXT resumes and extract contact details, sections, keywords, and document statistics.
- **Guided Resume Builder**: Build personal details, summary, education, experience, internships, projects, skills, certifications, achievements, and publications.
- **ATS Resume Scorer**: Transparent 100-point rule-based scoring across contact, summary, education, skills, experience/projects, action verbs, quantified achievements, ATS formatting, and readability.
- **Smart JD Matcher**: Paste or upload a job description as PDF, DOCX, DOC, or TXT, then compare resume content using local TF-IDF/cosine similarity and keyword/skill matching.
- **Bullet Point Improver**: Rule-based rewriting using action verb + task + method/tool + measurable impact structure. It uses placeholders instead of inventing metrics.
- **Spell & Grammar Check**: Local rule-based checks with optional spellchecker support.
- **Resume Analytics Dashboard**: Word frequency, readability, action verb usage, quantified achievement rate, section coverage, and writing recommendations.
- **Role-Based Guidance**: Profiles for data, analytics, AI/ML, business, academic, research, healthcare, consulting, and fresher/internship roles.
- **Templates and Export**: Preview multiple visibly distinct resume templates and export resume as PDF, DOCX, and TXT.
- **Improvement Report Export**: Download a resume improvement report summarizing ATS score, JD fit, red flags, missing keywords, missing skills, and priority fixes.
- **Version History**: Save, restore, import, and export resume versions within the session.
- **Demo Mode**: Load sample resumes and job descriptions without uploading files.
- **About Developer**: Includes developer profile, photo, portfolio link, core areas, and copyright note.

---

## Privacy and No-API Assurance

CV-Craft-Studio is designed to run locally and does not use paid or external AI APIs.

It does **not** use:

- OpenAI / ChatGPT API
- Google Gemini API
- Claude / Anthropic API
- Groq API
- Perplexity API
- Paid OCR APIs
- Cloud databases or external storage

It uses free/local libraries such as Streamlit, scikit-learn, pdfplumber, python-docx, reportlab, Plotly, and rule-based Python logic. Files are not permanently stored unless the user explicitly downloads or exports them.

---

## Folder Structure

```text
CV-Craft-Studio/
├── app.py
├── requirements.txt
├── runtime.txt
├── README.md
├── verify.py
├── assets/
│   ├── style.css
│   └── developer_photo.jpeg
├── modules/
│   ├── analytics.py
│   ├── bullet_improver.py
│   ├── export_utils.py
│   ├── grammar_checker.py
│   ├── jd_matcher.py
│   ├── parser.py
│   ├── privacy.py
│   ├── report_generator.py
│   ├── resume_builder.py
│   ├── role_profiles.py
│   ├── sample_data.py
│   ├── scorer.py
│   ├── spell_checker.py
│   ├── templates.py
│   ├── ui_components.py
│   └── version_history.py
├── samples/
├── tests/
└── exports/
```

---

## Installation

### 1. Create and activate an environment

```bash
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate         # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

For local auto-open in your default browser, use:

```bash
streamlit run app.py --server.headless=false
```

Or double-click `start_app.bat` on Windows / run `./start_app.sh` on macOS or Linux. The app opens at `http://localhost:8501`.

---

## Quick Workflow

1. Open **Demo Mode** to test the app quickly, or go to **Upload & Parse Resume**.
2. Build or import your resume into the **Resume Builder**.
3. Run **ATS Resume Scorer**.
4. Paste or upload a target job description in **Job Description Matcher**.
5. Improve weak bullets in **Bullet Point Improver**.
6. Use **Resume Preview & Export** to download PDF, DOCX, TXT, and the improvement report.

---

## Verification

Run the built-in verification script:

```bash
python verify.py
```

Run tests:

```bash
python -m pytest tests/ -v
```

Current verification status during packaging:

- `python verify.py`: passed
- `python -m pytest tests/ -v`: 40 passed

---

## Known Limitations

- Scanned/image-only PDFs cannot be parsed reliably because OCR is not included.
- Name and section detection are heuristic and work best with standard English resume formats.
- ATS scoring is a rule-based guide, not a guarantee of recruiter or ATS acceptance.
- JD matching is keyword/statistical matching, not a substitute for domain judgment.
- Bullet improvement is template-based; every placeholder must be replaced with truthful evidence only.
- The app is best suited to English-language resumes.

---

## Streamlit Cloud Deployment

1. Push the project to GitHub.
2. Go to Streamlit Community Cloud.
3. Select the repository.
4. Set the main file as `app.py`.
5. Deploy.

No API keys are required.

---


