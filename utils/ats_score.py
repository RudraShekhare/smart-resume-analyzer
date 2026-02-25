import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_ats_score(
    resume_text,
    relevant_skills=None,
    missing_skills=None,
    jd_provided=False
):
    """
    Job-aware ATS score.
    Returns a dict for UI explainability.
    """

    score = 0
    breakdown = {}

    # -------------------------------
    # 1. Resume Structure (30 points)
    # -------------------------------
    structure_score = 0

    if re.search(r'\bskills\b', resume_text, re.I):
        structure_score += 10
    if re.search(r'\bexperience\b|\bprojects\b', resume_text, re.I):
        structure_score += 10
    if re.search(r'\beducation\b', resume_text, re.I):
        structure_score += 10

    breakdown["structure"] = structure_score
    score += structure_score

    # -------------------------------
    # 2. Resume Length (10 points)
    # -------------------------------
    length_score = 10 if 150 <= len(resume_text.split()) <= 1000 else 5
    breakdown["length"] = length_score
    score += length_score

    # -------------------------------
    # 3. Metrics & Action Verbs (20 points)
    # -------------------------------
    metrics_score = 0

    if re.search(r'\d+%|\d+\s*(users|accuracy|projects|models)', resume_text, re.I):
        metrics_score += 10
    if re.search(r'\b(built|developed|implemented|designed|improved)\b', resume_text, re.I):
        metrics_score += 10

    breakdown["impact"] = metrics_score
    score += metrics_score

    # -------------------------------
    # 4. Job-Relevant Skills (40 points)
    # -------------------------------
    skill_score = 0

    if jd_provided and relevant_skills is not None:
        matched = len(relevant_skills)
        missing = len(missing_skills) if missing_skills else 0

        if matched > 0:
            skill_score = min(40, matched * 8)
        if missing > 0:
            skill_score -= min(10, missing * 2)

        skill_score = max(skill_score, 0)
    else:
        # generic fallback
        skill_score = 20

    breakdown["skills"] = skill_score
    score += skill_score

    return {
        "score": min(score, 100),
        "breakdown": breakdown
    }


def match_score(resume_text, jd_text):
    """
    TF-IDF similarity score (baseline JD match).
    Used as a secondary signal.
    """
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform([resume_text, jd_text])
    similarity = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
    return round(similarity * 100, 2)
