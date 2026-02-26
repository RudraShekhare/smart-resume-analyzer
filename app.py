from flask import Flask, render_template, request, send_file
from dotenv import load_dotenv
import os
import json
import re
from groq import Groq

from utils.resume_parser import extract_text_from_file
from utils.ats_score import calculate_ats_score
from utils.skill_extractor import extract_skills_sbert, skill_match_percent
from utils.pdf_report import generate_resume_report

# --------------------------------------------------
# ENV + LLM SETUP
# --------------------------------------------------
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# --------------------------------------------------
# JSON SAFE PARSER
# --------------------------------------------------
def extract_json(text):
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        fixed = re.sub(r",\s*([}\]])", r"\1", match.group())
        return json.loads(fixed)
    return {}

# --------------------------------------------------
# LLAMA RESUME ANALYSIS
# --------------------------------------------------
def analyze_resume_llm(resume_text: str):

    prompt = f"""
You are an ATS resume intelligence system.

TASKS:
1) Categorize skills into:
   programming, ml_ai, data, tools, soft

2) Extract work experience:
   role, company, duration_years, domain

3) Predict top 3 job roles

4) Write a professional 150–200 word summary

5) Give exactly 8 actionable resume improvement suggestions

OUTPUT JSON ONLY:
{{
  "predicted_roles": [],
  "skills": {{
    "programming": [],
    "ml_ai": [],
    "data": [],
    "tools": [],
    "soft": []
  }},
  "experience": [],
  "summary": "",
  "suggestions": []
}}

Resume:
\"\"\"{resume_text}\"\"\"
"""

    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = resp.choices[0].message.content.strip()
    return extract_json(raw)

# --------------------------------------------------
# RECRUITER RANKING
# --------------------------------------------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def rank_resumes_against_jd(jd_text, files):

    jd_text_lower = jd_text.lower()
    jd_skills = extract_skills_sbert(jd_text)

    if not jd_skills:
        jd_skills = list(set(re.findall(r"[a-zA-Z\+#]+", jd_text_lower)))

    results = []

    for file in files:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        resume_text = extract_text_from_file(filepath)

        try:
            os.remove(filepath)
        except:
            pass

        # ---------- SKILLS ----------
        resume_skills = extract_skills_sbert(resume_text)
        if not resume_skills:
            resume_skills = list(set(re.findall(r"[a-zA-Z\+#]+", resume_text.lower())))

        skill_match, overlap, missing = skill_match_percent(
            resume_skills,
            jd_skills
        )

        # ---------- ATS ----------
        ats = calculate_ats_score(
            resume_text,
            relevant_skills=resume_skills,
            missing_skills=[],
            jd_provided=True
        )["score"]

        # ---------- ROLE MATCH ----------
        role_score = 0
        roles_keywords = [
            "data scientist",
            "ml engineer",
            "ai engineer",
            "software engineer",
            "backend",
            "frontend"
        ]

        for rk in roles_keywords:
            if rk in resume_text.lower() and rk in jd_text_lower:
                role_score = 100
                break

        # ---------- EXPERIENCE ----------
        years = 0
        matches = re.findall(r"(\d+(?:\.\d+)?)\s+years", resume_text.lower())
        for m in matches:
            try:
                years += float(m)
            except:
                pass

        exp_score = min(100, years * 10)

        # ---------- FINAL ----------
        final = (
            0.5 * skill_match +
            0.3 * ats +
            0.1 * role_score +
            0.1 * exp_score
        )

        results.append({
            "filename": file.filename,
            "ats": round(ats, 2),
            "skill_match": round(skill_match, 2),
            "role_match": role_score,
            "experience_years": round(years, 1),
            "final": round(final, 2),
            "overlap": overlap[:8]
        })

    results.sort(key=lambda x: x["final"], reverse=True)
    return results

# --------------------------------------------------
# FLASK APP
# --------------------------------------------------
app = Flask(__name__)

# --------------------------------------------------
# ROUTES
# --------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ---------------- ANALYZE ----------------
@app.route("/analyze", methods=["POST"])
def analyze():

    if "resume" not in request.files:
        return "No file uploaded", 400

    file = request.files["resume"]
    jd_text = request.form.get("jd", "").strip()
    mode = request.form.get("mode", "jobseeker").strip()

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    resume_text = extract_text_from_file(filepath)
    os.remove(filepath)

    resume_skills = extract_skills_sbert(resume_text)

    llm_data = analyze_resume_llm(resume_text)

    categorized_skills = llm_data.get("skills") or {}
    predicted_roles = llm_data.get("predicted_roles") or []
    experience = llm_data.get("experience") or []
    summary_text = llm_data.get("summary") or ""
    suggestions = llm_data.get("suggestions") or []

    jd_skills = []
    skill_match = None

    if mode == "recruiter":
        if jd_text:
            jd_skills = extract_skills_sbert(jd_text)
            skill_match, _, _ = skill_match_percent(
                resume_skills,
                jd_skills
            )
        else:
            skill_match = 0

    ats_result = calculate_ats_score(
        resume_text,
        relevant_skills=resume_skills,
        missing_skills=[],
        jd_provided=bool(jd_text),
    )

    return render_template(
        "result.html",
        mode=mode,
        ats_score=ats_result["score"],
        ats_breakdown=ats_result["breakdown"],
        resume_skills=resume_skills,
        categorized_skills=categorized_skills,
        predicted_roles=predicted_roles,
        experience=experience,
        summary=summary_text,
        suggestions=suggestions,
        skill_match=skill_match,
        jd_skills=jd_skills
    )

# ---------------- PDF REPORT ----------------
@app.route("/download_report", methods=["POST"])
def download_report():

    data = json.loads(request.form["report_data"])

    path = "report.pdf"
    generate_resume_report(path, data)

    return send_file(path, as_attachment=True)

# ---------------- RANK ----------------
@app.route("/rank", methods=["GET", "POST"])
def rank():

    if request.method == "POST":
        jd_text = request.form.get("jd", "")
        files = request.files.getlist("resumes")

        if not jd_text or not files:
            return "Provide JD and resumes", 400

        ranked = rank_resumes_against_jd(jd_text, files)

        return render_template(
            "ranking.html",
            ranked=ranked,
            jd_text=jd_text
        )

    return render_template("ranking.html", ranked=None)

# --------------------------------------------------
# RUN
# --------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
