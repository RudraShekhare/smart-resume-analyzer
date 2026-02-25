import os
import re
from sentence_transformers import SentenceTransformer, util

SKILL_ALIASES = {
    # Core AI / ML
    "ml": "machine learning",
    "machinelearning": "machine learning",
    "ai": "artificial intelligence",
    "artificialintelligence": "artificial intelligence",
    "dl": "deep learning",
    "deeplearning": "deep learning",
    "nlp": "natural language processing",
    "naturallanguageprocessing": "natural language processing",
    "cv": "computer vision",
    "computervision": "computer vision",

    # Programming Languages
    "py": "python",
    "python": "python",
    "java": "java",
    "c": "c",
    "cpp": "c++",
    "c++": "c++",
    "csharp": "c#",
    "c#": "c#",
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "r": "r",
    "golang": "go",
    "go": "go",
    "rustlang": "rust",
    "rust": "rust",

    # Data & ML Libraries
    "numpy": "numpy",
    "np": "numpy",
    "pandas": "pandas",
    "pd": "pandas",
    "sklearn": "scikit-learn",
    "scikitlearn": "scikit-learn",
    "tf": "tensorflow",
    "tensorflow": "tensorflow",
    "keras": "keras",
    "torch": "pytorch",
    "pytorch": "pytorch",
    "hf": "huggingface",
    "huggingface": "huggingface",

    # Web & Backend
    "flask": "flask",
    "django": "django",
    "fastapi": "fastapi",
    "spring": "spring",
    "springboot": "spring boot",
    "node": "nodejs",
    "nodejs": "nodejs",
    "express": "expressjs",
    "expressjs": "expressjs",

    # APIs
    "api": "rest api",
    "apis": "rest api",
    "rest": "rest api",
    "restapi": "rest api",
    "restful": "rest api",
    "graphql": "graphql",
    "grpc": "grpc",

    # Databases
    "sql": "sql",
    "mysql": "mysql",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "sqlite": "sqlite",
    "nosql": "nosql",
    "mongodb": "mongodb",
    "mongo": "mongodb",
    "redis": "redis",

    # DevOps & Cloud
    "git": "git",
    "github": "git",
    "gitlab": "git",
    "docker": "docker",
    "dockercompose": "docker",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "aws": "aws",
    "ec2": "aws ec2",
    "s3": "aws s3",
    "lambda": "aws lambda",
    "azure": "azure",
    "gcp": "google cloud",

    # OS & Tools
    "linux": "linux",
    "unix": "unix",
    "bash": "bash",
    "shell": "bash",
    "powershell": "powershell",

    # Data & BI
    "excel": "excel",
    "ms-excel": "excel",
    "powerbi": "power bi",
    "power-bi": "power bi",
    "tableau": "tableau",

    # Concepts
    "ds": "data science",
    "datascience": "data science",
    "eda": "exploratory data analysis",
    "etl": "etl",
    "oop": "object oriented programming",
    "oops": "object oriented programming",
    "dsa": "data structures and algorithms",
}

# -------------------------------
# Model (loaded once)
# -------------------------------
_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

# -------------------------------
# Paths
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_FILE = os.path.join(BASE_DIR, "..", "data", "skills.txt")

# -------------------------------
# Lazy-loaded globals
# -------------------------------
_SKILL_LIST = None
_SKILL_EMB = None


def _load_skills():
    global _SKILL_LIST

    if _SKILL_LIST is not None:
        return _SKILL_LIST

    try:
        with open(SKILL_FILE, "r", encoding="utf-8") as f:
            skills = [line.strip().lower() for line in f if line.strip()]

        print(f"✅ Loaded {len(skills)} skills from skills.txt")
        _SKILL_LIST = skills
        return skills

    except Exception as e:
        print("❌ Failed to load skills.txt:", e)
        _SKILL_LIST = []
        return []


def _load_skill_embeddings():
    global _SKILL_EMB

    if _SKILL_EMB is not None:
        return _SKILL_EMB

    skills = _load_skills()
    if not skills:
        print("⚠️ Skill list empty — SBERT disabled")
        _SKILL_EMB = None
        return None

    _SKILL_EMB = _MODEL.encode(
        skills,
        convert_to_tensor=True,
        normalize_embeddings=True
    )

    print("🧠 Skill embeddings shape:", _SKILL_EMB.shape)
    return _SKILL_EMB


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _make_candidate_phrases(text: str):
    words = re.findall(r"[a-z0-9\+\#]+", text)
    phrases = set()

    for n in (1, 2, 3, 4):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i:i+n])
            if len(phrase) > 2:
                phrases.add(phrase)

    return list(phrases)


def extract_skills_sbert(text: str, threshold: float = 0.40, max_skills: int = 60):

    if not text or len(text.strip()) < 30:
        return []

    SKILL_EMB = _load_skill_embeddings()
    SKILL_LIST = _load_skills()

    if SKILL_EMB is None or not SKILL_LIST:
        return []

    text_clean = _clean_text(text)

    detected = set()

    # 1️⃣ Exact keyword + alias matching (HIGH PRECISION)
    for word in re.findall(r"[a-z\+\#]+", text_clean):
        if word in SKILL_LIST:
            detected.add(word)
        if word in SKILL_ALIASES:
            detected.add(SKILL_ALIASES[word])

    # 2️⃣ Phrase-level exact match
    for skill in SKILL_LIST:
        if skill in text_clean:
            detected.add(skill)

    # 3️⃣ Semantic matching (SBERT fallback)
    candidates = _make_candidate_phrases(text_clean)
    if candidates:
        cand_emb = _MODEL.encode(
            candidates,
            convert_to_tensor=True,
            normalize_embeddings=True
        )
        scores = util.cos_sim(cand_emb, SKILL_EMB)

        for i in range(scores.shape[0]):
            idx = int(scores[i].argmax())
            score = float(scores[i][idx])
            if score >= threshold:
                detected.add(SKILL_LIST[idx])

    return sorted(detected)[:max_skills]




def skill_match_percent(resume_skills, required_skills):
    req = set(required_skills)
    res = set(resume_skills)

    if not req:
        return 0.0, [], list(res)

    overlap = sorted(req & res)
    missing = sorted(req - res)
    pct = round((len(overlap) / len(req)) * 100, 2)

    return pct, overlap, missing
