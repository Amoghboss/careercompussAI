from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import os
import re
import io
from datetime import datetime, timezone
from functools import wraps
from uuid import uuid4
from werkzeug.security import generate_password_hash, check_password_hash

try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    import pytesseract
except Exception:
    pytesseract = None

try:
    import pypdfium2 as pdfium
except Exception:
    pdfium = None

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
except Exception:
    colors = None
    LETTER = None
    getSampleStyleSheet = None
    ParagraphStyle = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
except Exception:
    MongoClient = None
    PyMongoError = Exception

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "careercompass-dev-secret")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

CAREERS = [
    {
        "title": "Data Scientist",
        "salary": "₹110,000 - ₹160,000",
        "demand_level": "High",
        "required_skills": ["Python", "SQL", "Machine Learning", "Statistics"],
        "roadmap": [
            "Learn Python and data libraries",
            "Master SQL and data wrangling",
            "Study ML fundamentals and model evaluation",
            "Build and deploy portfolio projects",
        ],
    },
    {
        "title": "Web Developer",
        "salary": "₹80,000 - ₹130,000",
        "demand_level": "High",
        "required_skills": ["HTML", "CSS", "JavaScript", "React", "APIs"],
        "roadmap": [
            "Build strong HTML/CSS/JavaScript basics",
            "Learn a frontend framework",
            "Understand backend APIs",
            "Create full-stack projects",
        ],
    },
    {
        "title": "UI/UX Designer",
        "salary": "₹75,000 - ₹120,000",
        "demand_level": "Medium",
        "required_skills": ["Figma", "Wireframing", "User Research", "Prototyping"],
        "roadmap": [
            "Learn design principles and typography",
            "Practice wireframing and prototyping in Figma",
            "Conduct user interviews and usability tests",
            "Build a design case-study portfolio",
        ],
    },
    {
        "title": "AI Engineer",
        "salary": "₹120,000 - ₹180,000",
        "demand_level": "Very High",
        "required_skills": ["Python", "Deep Learning", "MLOps", "Cloud"],
        "roadmap": [
            "Master Python and ML foundations",
            "Learn deep learning frameworks",
            "Study model deployment and MLOps",
            "Build production-grade AI systems",
        ],
    },
    {
        "title": "Cybersecurity Analyst",
        "salary": "₹90,000 - ₹140,000",
        "demand_level": "High",
        "required_skills": ["Network Security", "SIEM", "Python", "Threat Analysis"],
        "roadmap": [
            "Learn networking and security fundamentals",
            "Practice threat detection and incident response",
            "Master SIEM tools and security monitoring",
            "Earn industry certifications and build a security portfolio",
        ],
    },
    {
        "title": "Cloud Engineer",
        "salary": "₹105,000 - ₹155,000",
        "demand_level": "Very High",
        "required_skills": ["AWS", "Azure", "Docker", "Kubernetes"],
        "roadmap": [
            "Learn cloud service fundamentals",
            "Build and deploy applications in AWS or Azure",
            "Use containers and orchestration tools",
            "Design secure and scalable cloud architectures",
        ],
    },
    {
        "title": "DevOps Engineer",
        "salary": "₹100,000 - ₹150,000",
        "demand_level": "Very High",
        "required_skills": ["CI/CD", "Docker", "Kubernetes", "Linux"],
        "roadmap": [
            "Learn Linux and scripting basics",
            "Set up CI/CD pipelines",
            "Use containerization and orchestration",
            "Implement monitoring and reliability best practices",
        ],
    },
    {
        "title": "Mobile App Developer",
        "salary": "₹85,000 - ₹135,000",
        "demand_level": "High",
        "required_skills": ["Android", "iOS", "Kotlin", "Swift"],
        "roadmap": [
            "Choose Android or iOS specialization",
            "Build apps with platform-native tools",
            "Integrate APIs and local data storage",
            "Publish and maintain apps in production",
        ],
    },
    {
        "title": "Product Manager",
        "salary": "₹95,000 - ₹160,000",
        "demand_level": "High",
        "required_skills": ["Roadmapping", "Analytics", "Agile", "Stakeholder Communication"],
        "roadmap": [
            "Learn product discovery and user research",
            "Prioritize features based on impact",
            "Work with engineering and design teams",
            "Track outcomes and iterate product strategy",
        ],
    },
    {
        "title": "Data Engineer",
        "salary": "₹105,000 - ₹155,000",
        "demand_level": "Very High",
        "required_skills": ["Python", "SQL", "ETL", "Spark"],
        "roadmap": [
            "Learn SQL, Python, and data modeling",
            "Build batch and streaming ETL pipelines",
            "Work with cloud data warehouses and Spark",
            "Implement reliable, scalable data platforms",
        ],
    },
    {
        "title": "ML Engineer",
        "salary": "₹115,000 - ₹175,000",
        "demand_level": "Very High",
        "required_skills": ["Python", "Machine Learning", "MLOps", "Docker"],
        "roadmap": [
            "Master ML algorithms and feature engineering",
            "Train and evaluate robust models",
            "Deploy models with APIs and containers",
            "Automate retraining and monitoring pipelines",
        ],
    },
    {
        "title": "Backend Developer",
        "salary": "₹95,000 - ₹145,000",
        "demand_level": "High",
        "required_skills": ["Python", "APIs", "Databases", "System Design"],
        "roadmap": [
            "Learn backend framework fundamentals",
            "Build secure REST APIs and auth flows",
            "Design database schemas and query optimization",
            "Scale services with caching and observability",
        ],
    },
    {
        "title": "Business Analyst",
        "salary": "₹75,000 - ₹120,000",
        "demand_level": "High",
        "required_skills": ["Excel", "SQL", "Dashboarding", "Communication"],
        "roadmap": [
            "Learn metrics, KPIs, and business modeling",
            "Query and clean data for decision-making",
            "Build dashboards and present insights",
            "Partner with teams to drive outcomes",
        ],
    },
    {
        "title": "QA Automation Engineer",
        "salary": "₹85,000 - ₹130,000",
        "demand_level": "High",
        "required_skills": ["Selenium", "Python", "API Testing", "CI/CD"],
        "roadmap": [
            "Learn testing fundamentals and test strategy",
            "Write UI and API automation suites",
            "Integrate tests into CI/CD pipelines",
            "Improve release confidence with quality metrics",
        ],
    },
    {
        "title": "AR/VR Developer",
        "salary": "₹95,000 - ₹150,000",
        "demand_level": "Growing",
        "required_skills": ["Unity", "C#", "3D Math", "XR SDKs"],
        "roadmap": [
            "Learn Unity and interactive 3D development",
            "Build immersive prototypes for AR/VR",
            "Optimize performance for target devices",
            "Publish production-ready immersive apps",
        ],
    },
]

KNOWN_SKILLS = {
    "python",
    "sql",
    "machine learning",
    "html",
    "css",
    "javascript",
    "figma",
    "react",
    "statistics",
    "deep learning",
    "cloud",
    "apis",
    "aws",
    "azure",
    "docker",
    "kubernetes",
    "linux",
    "agile",
    "swift",
    "kotlin",
    "android",
    "ios",
    "network security",
    "threat analysis",
    "etl",
    "spark",
    "system design",
    "excel",
    "dashboarding",
    "selenium",
    "api testing",
    "unity",
    "c#",
    "3d math",
    "mlops",
    "databases",
    "node.js",
    "nodejs",
    "typescript",
    "java",
    "c++",
    "go",
    "rust",
    "django",
    "flask",
    "fastapi",
    "spring boot",
    "mongodb",
    "postgresql",
    "mysql",
    "redis",
    "graphql",
    "rest",
    "git",
    "github",
    "gitlab",
    "jira",
    "tableau",
    "power bi",
    "numpy",
    "pandas",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "nlp",
    "computer vision",
    "prompt engineering",
    "data analysis",
    "data visualization",
    "microservices",
    "testing",
    "unit testing",
    "pytest",
    "playwright",
    "cypress",
    "firebase",
    "supabase",
    "figjam",
    "wireframing",
    "prototyping",
}

SKILL_ALIASES = {
    "Node.js": ["node.js", "nodejs", "node js"],
    "TypeScript": ["typescript", "ts"],
    "JavaScript": ["javascript", "js"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "c sharp"],
    "Machine Learning": ["machine learning", "ml"],
    "MLOps": ["mlops", "ml ops"],
    "Power BI": ["power bi", "powerbi"],
    "Scikit-Learn": ["scikit-learn", "sklearn"],
    "PyTorch": ["pytorch", "torch"],
    "REST": ["rest", "rest api", "restful"],
    "API Testing": ["api testing", "postman"],
    "CI/CD": ["ci/cd", "ci cd", "continuous integration", "continuous delivery"],
    "GitHub": ["github", "git hub"],
    "MongoDB": ["mongodb", "mongo db", "mongo"],
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql", "my sql"],
}

SKILL_DISPLAY = {
    "sql": "SQL",
    "nlp": "NLP",
    "rest": "REST",
    "aws": "AWS",
    "ios": "iOS",
    "ci/cd": "CI/CD",
    "mlops": "MLOps",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "power bi": "Power BI",
    "scikit-learn": "Scikit-Learn",
    "pytorch": "PyTorch",
    "mongodb": "MongoDB",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "github": "GitHub",
    "gitlab": "GitLab",
    "c#": "C#",
    "c++": "C++",
}


def extract_skills_from_text(text_lower):
    found = {}

    # Alias-based detection first (captures common variants/abbreviations).
    for canonical, variants in SKILL_ALIASES.items():
        if any(v in text_lower for v in variants):
            found[canonical.lower()] = canonical

    # Generic keyword scan from KNOWN_SKILLS for broad coverage.
    for skill in KNOWN_SKILLS:
        if skill in text_lower:
            display = SKILL_DISPLAY.get(skill.lower(), skill.title())
            found[display.lower()] = display

    return sorted(found.values())

mongo_client = None
mongo_db = None
careers_collection = None
analyses_collection = None
resumes_collection = None
users_collection = None
bookmarks_collection = None
jobs_collection = None
applications_collection = None
resume_versions_collection = None
reminders_collection = None

fallback_users = {}
fallback_analyses = []
fallback_resumes = []
fallback_bookmarks = []
fallback_jobs = []
fallback_applications = []
fallback_resume_versions = []
fallback_reminders = []

JOB_LISTINGS = [
    {"id": "J101", "title": "Junior Data Scientist", "company": "Nova Analytics", "location": "Remote", "job_language": "English", "programming_languages": ["Python", "SQL", "R"], "apply_link": "https://example.com/jobs/J101"},
    {"id": "J102", "title": "Frontend Developer", "company": "PixelForge", "location": "Bengaluru", "job_language": "English", "programming_languages": ["JavaScript", "TypeScript", "HTML", "CSS"], "apply_link": "https://example.com/jobs/J102"},
    {"id": "J103", "title": "AI Engineer", "company": "DeepScale Labs", "location": "Hyderabad", "job_language": "English", "programming_languages": ["Python", "C++"], "apply_link": "https://example.com/jobs/J103"},
    {"id": "J104", "title": "DevOps Engineer", "company": "CloudMesh", "location": "Pune", "job_language": "English", "programming_languages": ["Python", "Go", "Bash"], "apply_link": "https://example.com/jobs/J104"},
    {"id": "J105", "title": "Backend Engineer", "company": "Orbit Systems", "location": "Austin", "job_language": "English", "programming_languages": ["Java", "Spring Boot", "SQL"], "apply_link": "https://example.com/jobs/J105"},
    {"id": "J106", "title": "Full Stack Developer", "company": "LaunchGrid", "location": "Remote", "job_language": "English", "programming_languages": ["JavaScript", "TypeScript", "Node.js"], "apply_link": "https://example.com/jobs/J106"},
    {"id": "J107", "title": "Mobile App Developer", "company": "PocketLabs", "location": "Dubai", "job_language": "English", "programming_languages": ["Kotlin", "Swift"], "apply_link": "https://example.com/jobs/J107"},
    {"id": "J108", "title": "Data Engineer", "company": "StreamDelta", "location": "Singapore", "job_language": "English", "programming_languages": ["Python", "SQL", "Scala"], "apply_link": "https://example.com/jobs/J108"},
    {"id": "J109", "title": "Machine Learning Engineer", "company": "VisionCore", "location": "San Francisco", "job_language": "English", "programming_languages": ["Python", "C++", "SQL"], "apply_link": "https://example.com/jobs/J109"},
    {"id": "J110", "title": "Cloud Platform Engineer", "company": "SkyCompute", "location": "Remote", "job_language": "English", "programming_languages": ["Go", "Python", "Terraform"], "apply_link": "https://example.com/jobs/J110"},
    {"id": "J111", "title": "QA Automation Engineer", "company": "TestPilot", "location": "Chennai", "job_language": "English", "programming_languages": ["Python", "Java", "JavaScript"], "apply_link": "https://example.com/jobs/J111"},
    {"id": "J112", "title": "Site Reliability Engineer", "company": "PulseNet", "location": "Remote", "job_language": "English", "programming_languages": ["Go", "Python", "Bash"], "apply_link": "https://example.com/jobs/J112"},
    {"id": "J113", "title": "NLP Engineer", "company": "LinguaAI", "location": "Berlin", "job_language": "German", "programming_languages": ["Python", "PyTorch"], "apply_link": "https://example.com/jobs/J113"},
    {"id": "J114", "title": "Computer Vision Engineer", "company": "DepthFrame", "location": "Tokyo", "job_language": "Japanese", "programming_languages": ["Python", "C++"], "apply_link": "https://example.com/jobs/J114"},
    {"id": "J115", "title": "Cybersecurity Analyst", "company": "SecureWave", "location": "London", "job_language": "English", "programming_languages": ["Python", "PowerShell"], "apply_link": "https://example.com/jobs/J115"},
    {"id": "J116", "title": "Blockchain Developer", "company": "ChainForge", "location": "Remote", "job_language": "English", "programming_languages": ["Solidity", "JavaScript", "Rust"], "apply_link": "https://example.com/jobs/J116"},
    {"id": "J117", "title": "Game Developer", "company": "PlayArc", "location": "Montreal", "job_language": "French", "programming_languages": ["C#", "C++"], "apply_link": "https://example.com/jobs/J117"},
    {"id": "J118", "title": "ERP Developer", "company": "CoreBusiness", "location": "Madrid", "job_language": "Spanish", "programming_languages": ["Java", "ABAP"], "apply_link": "https://example.com/jobs/J118"},
    {"id": "J119", "title": "Embedded Systems Engineer", "company": "MicroGrid", "location": "Munich", "job_language": "German", "programming_languages": ["C", "C++", "Python"], "apply_link": "https://example.com/jobs/J119"},
    {"id": "J120", "title": "Data Analyst", "company": "MetricFlow", "location": "Remote", "job_language": "English", "programming_languages": ["SQL", "Python", "R"], "apply_link": "https://example.com/jobs/J120"},
    {"id": "J121", "title": "UI Engineer", "company": "DesignLoop", "location": "Paris", "job_language": "French", "programming_languages": ["JavaScript", "TypeScript", "CSS"], "apply_link": "https://example.com/jobs/J121"},
    {"id": "J122", "title": "Backend Developer", "company": "DataHarbor", "location": "Bengaluru", "job_language": "Hindi", "programming_languages": ["Python", "Django", "PostgreSQL"], "apply_link": "https://example.com/jobs/J122"},
    {"id": "J123", "title": "Platform Engineer", "company": "InfraPulse", "location": "Seattle", "job_language": "English", "programming_languages": ["Go", "Rust", "Kubernetes"], "apply_link": "https://example.com/jobs/J123"},
    {"id": "J124", "title": "API Developer", "company": "ServiceMesh Labs", "location": "Remote", "job_language": "English", "programming_languages": ["Node.js", "TypeScript", "GraphQL"], "apply_link": "https://example.com/jobs/J124"},
]


def _filter_jobs(rows, role_query="", language_query="", offset=0, limit=30):
    role_query = (role_query or "").strip().lower()
    language_query = (language_query or "").strip().lower()

    def matches(job):
        title = str(job.get("title", "")).lower()
        company = str(job.get("company", "")).lower()
        job_lang = str(job.get("job_language", "")).lower()
        prog_langs = [str(x).lower() for x in job.get("programming_languages", [])]

        role_ok = True
        lang_ok = True

        if role_query:
            role_ok = role_query in title or role_query in company

        if language_query:
            lang_ok = (
                language_query in job_lang
                or any(language_query in p for p in prog_langs)
            )
        return role_ok and lang_ok

    filtered = [j for j in rows if matches(j)]
    try:
        safe_offset = max(0, int(offset))
    except (TypeError, ValueError):
        safe_offset = 0
    try:
        safe_limit = min(100, max(1, int(limit)))
    except (TypeError, ValueError):
        safe_limit = 30
    return filtered[safe_offset : safe_offset + safe_limit]


def init_mongodb():
    global mongo_client, mongo_db, careers_collection, analyses_collection, resumes_collection, users_collection, bookmarks_collection
    global jobs_collection, applications_collection, resume_versions_collection, reminders_collection

    if MongoClient is None:
        print("MongoDB disabled: pymongo is not installed.")
        return

    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    db_name = os.getenv("MONGO_DB_NAME", "careercompass_ai")

    try:
        mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
        mongo_client.admin.command("ping")
        mongo_db = mongo_client[db_name]
        careers_collection = mongo_db["careers"]
        analyses_collection = mongo_db["analyses"]
        resumes_collection = mongo_db["resumes"]
        users_collection = mongo_db["users"]
        bookmarks_collection = mongo_db["bookmarks"]
        jobs_collection = mongo_db["jobs"]
        applications_collection = mongo_db["applications"]
        resume_versions_collection = mongo_db["resume_versions"]
        reminders_collection = mongo_db["reminders"]

        # Keep careers data in sync on every startup.
        for career in CAREERS:
            careers_collection.update_one(
                {"title": career["title"]},
                {"$set": career},
                upsert=True,
            )

        users_collection.create_index("username", unique=True)
        bookmarks_collection.create_index([("username", 1), ("career_title", 1)], unique=True)
        jobs_collection.create_index("id", unique=True)
        applications_collection.create_index([("username", 1), ("job_id", 1)], unique=True)
        reminders_collection.create_index([("username", 1), ("created_at", -1)])
        resume_versions_collection.create_index([("username", 1), ("created_at", -1)])

        for job in JOB_LISTINGS:
            jobs_collection.update_one({"id": job["id"]}, {"$set": job}, upsert=True)

        print(f"MongoDB connected: {db_name}")
    except PyMongoError as exc:
        mongo_client = None
        mongo_db = None
        careers_collection = None
        analyses_collection = None
        resumes_collection = None
        users_collection = None
        bookmarks_collection = None
        jobs_collection = None
        applications_collection = None
        resume_versions_collection = None
        reminders_collection = None
        print(f"MongoDB unavailable. Using in-memory fallback. Reason: {str(exc)}")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def normalize_skills(raw_skills):
    if isinstance(raw_skills, str):
        return [s.strip() for s in re.split(r"[,\n]", raw_skills) if s.strip()]
    if isinstance(raw_skills, list):
        return [str(s).strip() for s in raw_skills if str(s).strip()]
    return []


def current_user():
    return session.get("username")


def get_careers_data():
    if careers_collection is not None:
        return list(careers_collection.find({}, {"_id": 0}))
    return CAREERS


def compute_recommendation(skills):
    careers = get_careers_data()
    lowered = {s.lower().strip() for s in skills if s and s.strip()}
    career_lookup = {c["title"]: c for c in careers}

    ranked = []
    for career in careers:
        required = [s.lower() for s in career.get("required_skills", [])]
        overlap = [s for s in required if s in lowered]
        score = int(round((len(overlap) / max(1, len(required))) * 100))
        missing = [s for s in career.get("required_skills", []) if s.lower() not in lowered]
        ranked.append({
            "career": career["title"],
            "score": score,
            "missing": missing,
            "overlap_count": len(overlap),
        })

    ranked.sort(key=lambda x: (x["overlap_count"], x["score"]), reverse=True)
    top = ranked[0]
    top_matches = []
    for row in ranked[:4]:
        meta = career_lookup.get(row["career"], {})
        top_matches.append({
            "career": row["career"],
            "match_score": row["score"],
            "missing_skills": row["missing"][:4],
            "salary": meta.get("salary", ""),
            "demand_level": meta.get("demand_level", ""),
        })

    alternatives = [r["career"] for r in ranked[1:4]]
    return {
        "career": top["career"],
        "match_score": top["score"],
        "missing_skills": top["missing"][:4],
        "alternatives": alternatives,
        "top_matches": top_matches,
    }


def evaluate_resume_for_jobs(extracted_skills):
    lowered = {s.lower().strip() for s in extracted_skills if s and s.strip()}
    results = []
    for career in get_careers_data():
        required = [s.lower() for s in career.get("required_skills", [])]
        overlap = [s for s in required if s in lowered]
        score = int(round((len(overlap) / max(1, len(required))) * 100))
        missing = [s for s in career.get("required_skills", []) if s.lower() not in lowered]
        acceptable = score >= 50
        results.append({
            "career": career["title"],
            "acceptable": acceptable,
            "fit_score": score,
            "missing_skills": missing[:4],
        })
    results.sort(key=lambda x: x["fit_score"], reverse=True)
    return results[:5]


def extract_text_with_fallback(pdf_path):
    extracted_text = ""
    method = "none"

    # Primary extraction for text-based PDFs.
    if pdfplumber is not None:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages = [page.extract_text() or "" for page in pdf.pages]
            extracted_text = " ".join(pages).strip()
            if extracted_text:
                return extracted_text, "pdf_text"
        except Exception:
            extracted_text = ""

    # OCR fallback for scanned/image-based PDFs.
    if pytesseract is None or pdfium is None:
        return "", method

    tesseract_cmd = os.getenv("TESSERACT_CMD", "").strip()
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    try:
        doc = pdfium.PdfDocument(pdf_path)
        ocr_chunks = []
        for page_index in range(len(doc)):
            page = doc.get_page(page_index)
            bitmap = page.render(scale=2.0)
            pil_image = bitmap.to_pil()
            text = pytesseract.image_to_string(pil_image) or ""
            if text.strip():
                ocr_chunks.append(text)
            page.close()
        extracted_text = " ".join(ocr_chunks).strip()
        if extracted_text:
            method = "ocr"
    except Exception:
        extracted_text = ""

    return extracted_text, method


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            api_prefixes = (
                "/analyze-skills",
                "/upload-resume",
                "/analysis-history",
                "/jobs",
                "/applications",
                "/generate-cover-letter",
                "/mock-interview",
                "/skill-roadmap",
                "/portfolio-analyze",
                "/resume-versions",
                "/export-resume-pdf",
                "/admin-analytics",
                "/reminders",
                "/bookmarks",
                "/dashboard-stats",
                "/career-quiz",
            )
            if request.path.startswith(api_prefixes):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("login_page"))
        return view(*args, **kwargs)
    return wrapped


def build_cover_letter(name, role, company, summary, skills):
    skills_line = ", ".join(skills[:6]) if skills else "problem solving and collaboration"
    return (
        f"Dear Hiring Manager at {company},\n\n"
        f"I am excited to apply for the {role} position. {summary}\n\n"
        f"My relevant skills include {skills_line}. I focus on delivering measurable outcomes, writing maintainable solutions, and collaborating effectively across teams.\n\n"
        f"I am confident I can contribute to {company}'s goals and would welcome the opportunity to discuss this role.\n\n"
        f"Sincerely,\n{name}"
    )


def analyze_portfolio(portfolio_url, role):
    role = (role or "Software Engineer").strip() or "Software Engineer"
    feedback = [
        "Add one featured project with problem statement, architecture, and metrics.",
        "Include screenshots/demo GIF and a clear live/demo link.",
        "Show your role, tech stack, and quantified outcomes for each project.",
        f"Tailor top projects to {role} requirements.",
    ]
    score = 72
    url_lower = portfolio_url.lower()
    if "github.com" in url_lower:
        score += 6
        feedback.append("Pin top repositories and improve README quality.")
    if "linkedin.com" in url_lower:
        score += 3
        feedback.append("Add project links directly in your LinkedIn featured section.")
    if any(host in url_lower for host in ["behance.net", "dribbble.com"]):
        score += 5
        feedback.append("Add case-study context: goal, process, and measurable outcome.")
    score = min(95, score)
    return {"portfolio_url": portfolio_url, "feedback": feedback, "score": score}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard_page():
    return render_template("dashboard.html")


@app.route("/careers-page")
@login_required
def careers_page():
    return render_template("careers.html")


@app.route("/analyze-skills", methods=["POST"])
@login_required
def analyze_skills():
    payload = request.get_json(silent=True) or {}
    skills = normalize_skills(payload.get("skills", []))
    if not skills:
        return jsonify({"error": "At least one skill is required"}), 400
    username = current_user()
    result = compute_recommendation(skills)

    if analyses_collection is not None:
        analyses_collection.insert_one({
            "username": username,
            "skills": skills,
            "result": result,
            "created_at": now_iso(),
        })
    else:
        fallback_analyses.append({
            "username": username,
            "skills": skills,
            "result": result,
            "created_at": now_iso(),
        })

    return jsonify(result)


@app.route("/upload-resume", methods=["POST"])
@login_required
def upload_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    username = current_user()
    file_basename, file_ext = os.path.splitext(file.filename)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", file_basename).strip("_") or "resume"
    unique_filename = f"{safe_name}_{uuid4().hex[:8]}{file_ext.lower()}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
    file.save(save_path)

    extracted_text, parse_method = extract_text_with_fallback(save_path)
    if not extracted_text.strip():
        return jsonify({
            "error": (
                "Resume text not found. If this is a scanned PDF, install Tesseract OCR "
                "and set TESSERACT_CMD (for example: C:\\Program Files\\Tesseract-OCR\\tesseract.exe)."
            )
        }), 400

    text_lower = extracted_text.lower()
    found_skills = extract_skills_from_text(text_lower)
    job_assessment = evaluate_resume_for_jobs(found_skills)
    detected_urls = sorted(set(re.findall(r"(https?://[^\s)>\]]+)", extracted_text)))
    portfolio_urls = [
        u for u in detected_urls
        if any(host in u.lower() for host in ["github.com", "linkedin.com", "behance.net", "dribbble.com", "portfolio", "vercel.app", "netlify.app"])
    ][:3]
    inferred_role = job_assessment[0]["career"] if job_assessment else "Software Engineer"
    portfolio_assessment = [analyze_portfolio(url, inferred_role) for url in portfolio_urls]

    if resumes_collection is not None:
        resumes_collection.insert_one({
            "username": username,
            "filename": unique_filename,
            "extracted_skills": found_skills,
            "created_at": now_iso(),
        })
    else:
        fallback_resumes.append({
            "username": username,
            "filename": unique_filename,
            "extracted_skills": found_skills,
            "created_at": now_iso(),
        })

    return jsonify({
        "message": "Resume uploaded successfully",
        "parse_method": parse_method,
        "extracted_skills": found_skills,
        "job_assessment": job_assessment,
        "detected_links": detected_urls[:6],
        "portfolio_assessment": portfolio_assessment,
    })


@app.route("/careers", methods=["GET"])
def get_careers():
    return jsonify(get_careers_data())


@app.route("/jobs", methods=["GET"])
@login_required
def jobs_feed():
    role_query = request.args.get("role", "")
    language_query = request.args.get("language", "")
    limit = request.args.get("limit", 30)
    offset = request.args.get("offset", 0)
    try:
        safe_offset = max(0, int(offset))
    except (TypeError, ValueError):
        safe_offset = 0
    try:
        safe_limit = min(100, max(1, int(limit)))
    except (TypeError, ValueError):
        safe_limit = 30

    if jobs_collection is not None:
        query = {}
        clauses = []
        if role_query.strip():
            escaped_role = re.escape(role_query.strip())
            clauses.append({
                "$or": [
                    {"title": {"$regex": escaped_role, "$options": "i"}},
                    {"company": {"$regex": escaped_role, "$options": "i"}},
                ]
            })
        if language_query.strip():
            escaped_lang = re.escape(language_query.strip())
            clauses.append({
                "$or": [
                    {"job_language": {"$regex": escaped_lang, "$options": "i"}},
                    {"programming_languages": {"$regex": escaped_lang, "$options": "i"}},
                ]
            })
        if clauses:
            query = {"$and": clauses}
        jobs = list(
            jobs_collection.find(query, {"_id": 0})
            .skip(safe_offset)
            .limit(safe_limit)
        )
        return jsonify(jobs)
    if not fallback_jobs:
        fallback_jobs.extend(JOB_LISTINGS)
    return jsonify(_filter_jobs(fallback_jobs, role_query, language_query, safe_offset, safe_limit))


@app.route("/jobs-preview", methods=["GET"])
def jobs_preview():
    language_query = request.args.get("language", "")
    if jobs_collection is not None:
        query = {}
        if language_query.strip():
            escaped_lang = re.escape(language_query.strip())
            query = {
                "$or": [
                    {"job_language": {"$regex": escaped_lang, "$options": "i"}},
                    {"programming_languages": {"$regex": escaped_lang, "$options": "i"}},
                ]
            }
        jobs = list(jobs_collection.find(query, {"_id": 0}).limit(6))
        return jsonify(jobs)
    if not fallback_jobs:
        fallback_jobs.extend(JOB_LISTINGS)
    return jsonify(_filter_jobs(fallback_jobs, "", language_query, 0, 6))


@app.route("/applications", methods=["GET"])
@login_required
def get_applications():
    username = current_user()
    if applications_collection is not None:
        rows = list(applications_collection.find({"username": username}, {"_id": 0}).sort("updated_at", -1))
        return jsonify(rows)
    rows = [a for a in fallback_applications if a.get("username") == username]
    rows.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return jsonify(rows)


@app.route("/applications", methods=["POST"])
@login_required
def create_application():
    payload = request.get_json(silent=True) or {}
    username = current_user()
    job_id = str(payload.get("job_id", "")).strip()
    title = str(payload.get("title", "")).strip()
    company = str(payload.get("company", "")).strip()
    status = str(payload.get("status", "Applied")).strip() or "Applied"

    if not job_id or not title:
        return jsonify({"error": "job_id and title are required"}), 400

    row = {
        "username": username,
        "job_id": job_id,
        "title": title,
        "company": company,
        "status": status,
        "updated_at": now_iso(),
        "created_at": now_iso(),
    }

    if applications_collection is not None:
        applications_collection.update_one(
            {"username": username, "job_id": job_id},
            {"$set": row},
            upsert=True,
        )
    else:
        existing = next((a for a in fallback_applications if a["username"] == username and a["job_id"] == job_id), None)
        if existing:
            existing.update(row)
        else:
            fallback_applications.append(row)
    return jsonify({"success": True, "message": "Application saved", "application": row})


@app.route("/applications/status", methods=["PATCH"])
@login_required
def update_application_status():
    payload = request.get_json(silent=True) or {}
    username = current_user()
    job_id = str(payload.get("job_id", "")).strip()
    status = str(payload.get("status", "")).strip()
    if not job_id or not status:
        return jsonify({"error": "job_id and status are required"}), 400

    if applications_collection is not None:
        applications_collection.update_one(
            {"username": username, "job_id": job_id},
            {"$set": {"status": status, "updated_at": now_iso()}},
        )
    else:
        existing = next((a for a in fallback_applications if a["username"] == username and a["job_id"] == job_id), None)
        if existing:
            existing["status"] = status
            existing["updated_at"] = now_iso()
    return jsonify({"success": True, "message": "Status updated"})


@app.route("/generate-cover-letter", methods=["POST"])
@login_required
def generate_cover_letter():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "Candidate")).strip() or "Candidate"
    role = str(payload.get("role", "Role")).strip() or "Role"
    company = str(payload.get("company", "Company")).strip() or "Company"
    summary = str(payload.get("summary", "I bring strong technical and collaboration skills.")).strip()
    skills = normalize_skills(payload.get("skills", []))
    letter = build_cover_letter(name, role, company, summary, skills)
    return jsonify({"cover_letter": letter})


@app.route("/mock-interview/questions", methods=["POST"])
@login_required
def interview_questions():
    payload = request.get_json(silent=True) or {}
    role = str(payload.get("role", "Software Engineer")).strip() or "Software Engineer"
    role_lower = role.lower()

    common = [
        f"Walk me through your strongest project for the {role} role using STAR (Situation, Task, Action, Result).",
        "Describe a technically hard problem you solved. What options did you consider and why did you choose the final approach?",
        "Tell me about a time your first solution failed. How did you diagnose root cause and recover?",
        "How do you prioritize tasks when multiple stakeholders mark their request as urgent?",
        "Give one example where your work created measurable impact. Include exact metrics.",
        "How do you ensure quality before shipping? Explain your testing and validation process.",
        "How do you handle feedback that you disagree with from a manager or teammate?",
        "What are your first 30-60-90 day priorities if selected for this role?",
    ]

    role_specific = {
        "data scientist": [
            "How would you frame a churn prediction problem end-to-end, from business objective to deployment?",
            "How do you choose between precision and recall in an imbalanced dataset? Give a concrete scenario.",
            "Explain how you detect data leakage and prevent it during model training.",
            "How would you explain model decisions to a non-technical stakeholder?",
        ],
        "ai engineer": [
            "How do you move an ML prototype to production with monitoring, rollback, and retraining strategy?",
            "How would you reduce model latency while preserving acceptable accuracy?",
            "Explain your approach to prompt evaluation and guardrails for LLM-based features.",
            "How do you detect model drift and what triggers retraining?",
        ],
        "web developer": [
            "How do you optimize Core Web Vitals for a slow page? Which metrics do you prioritize first?",
            "Explain your strategy for API error handling and retries in frontend apps.",
            "How do you design reusable components without over-engineering?",
            "Describe how you debug a production issue that only appears on mobile Safari.",
        ],
        "ui/ux designer": [
            "How do you convert ambiguous product requirements into clear user flows and wireframes?",
            "How do you validate a design decision with evidence instead of opinion?",
            "Describe a usability issue you found through testing and how your redesign improved outcomes.",
            "How do you balance accessibility, brand, and engineering constraints?",
        ],
        "backend developer": [
            "How would you design an idempotent API for payment or order creation?",
            "How do you choose between SQL and NoSQL for a new service?",
            "Explain how you troubleshoot high p95 latency in a backend endpoint.",
            "How do you implement authentication and authorization safely in distributed systems?",
        ],
        "devops engineer": [
            "How do you design a CI/CD pipeline with fast feedback and safe production releases?",
            "How do you investigate and resolve recurring Kubernetes pod restarts?",
            "What is your incident response flow during a production outage?",
            "How do you define SLOs and error budgets for a service?",
        ],
    }

    targeted = []
    for key, qset in role_specific.items():
        if key in role_lower:
            targeted = qset
            break

    if not targeted:
        targeted = [
            f"What core competencies should a strong {role} demonstrate in the first 3 months?",
            f"Describe one domain-specific challenge in {role} and how you would solve it.",
            "How do you collaborate across product, design, and engineering to deliver outcomes?",
            "How do you decide what to automate vs what to do manually?",
        ]

    questions = (targeted + common)[:12]
    return jsonify({"role": role, "questions": questions})


@app.route("/mock-interview/feedback", methods=["POST"])
@login_required
def interview_feedback():
    payload = request.get_json(silent=True) or {}
    answers = payload.get("answers", [])
    scored = []
    for idx, ans in enumerate(answers):
        text = str(ans).strip()
        length_score = 40 if len(text.split()) >= 30 else 20
        impact_score = 30 if re.search(r"\d|%|users|revenue|latency", text.lower()) else 10
        clarity_score = 30 if len(text) >= 120 else 15
        total = min(100, length_score + impact_score + clarity_score)
        tips = []
        if impact_score < 20:
            tips.append("Add measurable outcomes (numbers, percentages, impact).")
        if length_score < 30:
            tips.append("Give more detail using situation-task-action-result format.")
        if clarity_score < 25:
            tips.append("Use clearer structure: context, action, result, reflection.")
        scored.append({"question_index": idx + 1, "score": total, "tips": tips or ["Strong answer."]})
    return jsonify({"feedback": scored})


@app.route("/skill-roadmap", methods=["POST"])
@login_required
def skill_roadmap():
    payload = request.get_json(silent=True) or {}
    missing = normalize_skills(payload.get("missing_skills", []))
    if not missing:
        missing = ["Communication", "Problem Solving"]
    roadmap = []
    for i, skill in enumerate(missing[:6], start=1):
        roadmap.append({
            "week": i,
            "focus_skill": skill,
            "tasks": [
                f"Learn fundamentals of {skill}",
                f"Build one mini project using {skill}",
                f"Write notes and revision checklist for {skill}",
            ],
        })
    return jsonify({"roadmap": roadmap})


@app.route("/portfolio-analyze", methods=["POST"])
@login_required
def portfolio_analyze():
    payload = request.get_json(silent=True) or {}
    portfolio_url = str(payload.get("portfolio_url", "")).strip()
    role = str(payload.get("role", "Software Engineer")).strip() or "Software Engineer"
    if not portfolio_url:
        return jsonify({"error": "portfolio_url is required"}), 400
    return jsonify(analyze_portfolio(portfolio_url, role))


@app.route("/resume-versions", methods=["GET"])
@login_required
def get_resume_versions():
    username = current_user()
    if resume_versions_collection is not None:
        rows = list(
            resume_versions_collection.find({"username": username}, {"_id": 0}).sort("created_at", -1).limit(20)
        )
        return jsonify(rows)
    rows = [r for r in fallback_resume_versions if r.get("username") == username]
    rows.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return jsonify(rows[:20])


@app.route("/resume-versions", methods=["POST"])
@login_required
def create_resume_version():
    payload = request.get_json(silent=True) or {}
    username = current_user()
    version_name = str(payload.get("version_name", "Untitled Version")).strip() or "Untitled Version"
    role = str(payload.get("role", "General")).strip() or "General"
    content = str(payload.get("content", "")).strip()
    if not content:
        return jsonify({"error": "content is required"}), 400

    row = {
        "id": uuid4().hex[:10],
        "username": username,
        "version_name": version_name,
        "role": role,
        "content": content,
        "created_at": now_iso(),
    }
    if resume_versions_collection is not None:
        resume_versions_collection.insert_one(row)
    else:
        fallback_resume_versions.append(row)
    return jsonify({"success": True, "version": row})


@app.route("/export-resume-pdf", methods=["POST"])
@login_required
def export_resume_pdf():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("content", "")).strip()
    filename = str(payload.get("filename", "careercompass_resume")).strip() or "careercompass_resume"
    if not text:
        return jsonify({"error": "content is required"}), 400

    if LETTER is None or SimpleDocTemplate is None or ParagraphStyle is None:
        return jsonify({"error": "PDF export requires reportlab. Install with: pip install reportlab"}), 500

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=44,
        rightMargin=44,
        topMargin=42,
        bottomMargin=42,
    )
    styles = getSampleStyleSheet()
    heading_style = ParagraphStyle(
        "ResumeHeading",
        parent=styles["Heading4"],
        fontSize=11,
        leading=13,
        textColor=colors.HexColor("#0f2b35"),
        spaceBefore=9,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "ResumeBody",
        parent=styles["BodyText"],
        fontSize=10.2,
        leading=14,
        textColor=colors.HexColor("#1a2530"),
    )
    bullet_style = ParagraphStyle(
        "ResumeBullet",
        parent=body_style,
        leftIndent=12,
    )
    story = []

    lines = [line.rstrip() for line in text.splitlines()]
    lines = [line for line in lines if line.strip()]

    # First two lines are rendered as name and contact header for cleaner resume layout.
    if lines:
        name_style = ParagraphStyle(
            "ResumeName",
            parent=styles["Heading1"],
            fontSize=18,
            leading=21,
            textColor=colors.HexColor("#0b1f2c"),
            spaceAfter=4,
        )
        story.append(Paragraph(lines[0], name_style))
        lines = lines[1:]
    if lines:
        contact_style = ParagraphStyle(
            "ResumeContact",
            parent=styles["BodyText"],
            fontSize=9.7,
            leading=12,
            textColor=colors.HexColor("#355060"),
            spaceAfter=8,
        )
        story.append(Paragraph(lines[0], contact_style))
        lines = lines[1:]

    section_headers = {"SUMMARY", "SKILLS", "EXPERIENCE", "PROJECTS", "EDUCATION", "CERTIFICATIONS", "TARGET ROLE"}
    for line in lines:
        clean = line.strip()
        if not clean:
            continue
        if clean.upper() in section_headers and len(clean) <= 30:
            story.append(Paragraph(clean.upper(), heading_style))
            continue
        if clean.startswith("- "):
            story.append(Paragraph(f"• {clean[2:]}", bullet_style))
        else:
            story.append(Paragraph(clean, body_style))
        story.append(Spacer(1, 3))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    output_name = f"{filename}.pdf"
    output_path = os.path.join(app.config["UPLOAD_FOLDER"], output_name)
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
    return jsonify({
        "success": True,
        "message": "PDF exported",
        "file_path": output_path,
        "download_url": url_for("download_resume_pdf", filename=output_name),
    })


@app.route("/download-resume/<path:filename>", methods=["GET"])
@login_required
def download_resume_pdf(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@app.route("/admin-analytics", methods=["GET"])
@login_required
def admin_analytics():
    if analyses_collection is not None:
        total_analyses = analyses_collection.count_documents({})
    else:
        total_analyses = len(fallback_analyses)

    if resumes_collection is not None:
        total_resumes = resumes_collection.count_documents({})
    else:
        total_resumes = len(fallback_resumes)

    if bookmarks_collection is not None:
        total_bookmarks = bookmarks_collection.count_documents({})
    else:
        total_bookmarks = len(fallback_bookmarks)

    if applications_collection is not None:
        total_apps = applications_collection.count_documents({})
    else:
        total_apps = len(fallback_applications)

    top_careers = {}
    source = list(analyses_collection.find({}, {"_id": 0, "result.career": 1})) if analyses_collection is not None else fallback_analyses
    for row in source:
        career = (row.get("result", {}) or {}).get("career")
        if career:
            top_careers[career] = top_careers.get(career, 0) + 1
    ranked = sorted(top_careers.items(), key=lambda x: x[1], reverse=True)[:5]

    return jsonify({
        "total_analyses": total_analyses,
        "total_resumes": total_resumes,
        "total_bookmarks": total_bookmarks,
        "total_applications": total_apps,
        "top_careers": [{"career": c, "count": n} for c, n in ranked],
    })


@app.route("/reminders", methods=["GET"])
@login_required
def get_reminders():
    username = current_user()
    if reminders_collection is not None:
        rows = list(reminders_collection.find({"username": username}, {"_id": 0}).sort("created_at", -1))
        return jsonify(rows)
    rows = [r for r in fallback_reminders if r.get("username") == username]
    rows.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return jsonify(rows)


@app.route("/reminders", methods=["POST"])
@login_required
def create_reminder():
    payload = request.get_json(silent=True) or {}
    username = current_user()
    text = str(payload.get("text", "")).strip()
    due_date = str(payload.get("due_date", "")).strip()
    if not text:
        return jsonify({"error": "text is required"}), 400
    row = {
        "id": uuid4().hex[:10],
        "username": username,
        "text": text,
        "due_date": due_date,
        "completed": False,
        "created_at": now_iso(),
    }
    if reminders_collection is not None:
        reminders_collection.insert_one(row)
    else:
        fallback_reminders.append(row)
    return jsonify({"success": True, "reminder": row})


@app.route("/reminders", methods=["PATCH"])
@login_required
def update_reminder():
    payload = request.get_json(silent=True) or {}
    username = current_user()
    reminder_id = str(payload.get("id", "")).strip()
    completed = bool(payload.get("completed", False))
    if not reminder_id:
        return jsonify({"error": "id is required"}), 400
    if reminders_collection is not None:
        reminders_collection.update_one({"username": username, "id": reminder_id}, {"$set": {"completed": completed}})
    else:
        row = next((r for r in fallback_reminders if r["username"] == username and r["id"] == reminder_id), None)
        if row:
            row["completed"] = completed
    return jsonify({"success": True})


@app.route("/career-quiz", methods=["POST"])
@login_required
def career_quiz():
    payload = request.get_json(silent=True) or {}
    interests = [str(x).strip().lower() for x in payload.get("interests", []) if str(x).strip()]
    if not interests:
        return jsonify({"error": "Select at least one interest"}), 400

    interest_map = {
        "ai": "AI Engineer",
        "data": "Data Scientist",
        "design": "UI/UX Designer",
        "frontend": "Web Developer",
        "security": "Cybersecurity Analyst",
        "cloud": "Cloud Engineer",
        "automation": "DevOps Engineer",
        "mobile": "Mobile App Developer",
        "product": "Product Manager",
    }
    mapped = [interest_map[i] for i in interests if i in interest_map]
    if not mapped:
        mapped = ["Web Developer"]

    primary = mapped[0]
    alternatives = [m for m in mapped[1:4] if m != primary]
    if not alternatives:
        alternatives = [c["title"] for c in get_careers_data() if c["title"] != primary][:3]

    return jsonify({
        "career": primary,
        "match_score": 78,
        "missing_skills": [],
        "alternatives": alternatives,
    })


@app.route("/auth/login-register", methods=["POST"])
def login_register():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip().lower()
    password = str(payload.get("password", "")).strip()

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400
    if len(username) < 3:
        return jsonify({"success": False, "message": "Username must be at least 3 characters."}), 400
    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters."}), 400

    password_hash = generate_password_hash(password)

    if users_collection is not None:
        existing = users_collection.find_one({"username": username})
        if existing is None:
            users_collection.insert_one({
                "username": username,
                "password_hash": password_hash,
                "created_at": now_iso(),
                "updated_at": now_iso(),
            })
            session["username"] = username
            return jsonify({"success": True, "message": "Registration successful. Logged in.", "mode": "register"})

        if check_password_hash(existing.get("password_hash", ""), password):
            users_collection.update_one({"username": username}, {"$set": {"updated_at": now_iso()}})
            session["username"] = username
            return jsonify({"success": True, "message": "Login successful", "mode": "login"})

        return jsonify({"success": False, "message": "Invalid password."}), 401

    existing_hash = fallback_users.get(username)
    if existing_hash is None:
        fallback_users[username] = password_hash
        session["username"] = username
        return jsonify({"success": True, "message": "Registration successful. Logged in.", "mode": "register"})

    if check_password_hash(existing_hash, password):
        session["username"] = username
        return jsonify({"success": True, "message": "Login successful", "mode": "login"})

    return jsonify({"success": False, "message": "Invalid password."}), 401


@app.route("/auth/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return jsonify({"success": True, "message": "Logged out"})


@app.route("/session-status", methods=["GET"])
def session_status():
    username = current_user()
    return jsonify({"logged_in": bool(username), "username": username})


@app.route("/analysis-history", methods=["GET"])
@login_required
def analysis_history():
    username = current_user()
    if analyses_collection is not None:
        history = list(
            analyses_collection.find(
                {"username": username},
                {"_id": 0, "skills": 1, "result": 1, "created_at": 1},
            ).sort("created_at", -1).limit(10)
        )
        return jsonify(history)

    history = [item for item in fallback_analyses if item.get("username") == username][-10:]
    history.reverse()
    return jsonify(history)


@app.route("/bookmarks", methods=["GET"])
@login_required
def get_bookmarks():
    username = current_user()
    if bookmarks_collection is not None:
        rows = list(
            bookmarks_collection.find({"username": username}, {"_id": 0, "career_title": 1, "created_at": 1}).sort("created_at", -1)
        )
        return jsonify(rows)
    rows = [b for b in fallback_bookmarks if b.get("username") == username]
    rows.reverse()
    return jsonify(rows)


@app.route("/bookmarks", methods=["POST"])
@login_required
def toggle_bookmark():
    payload = request.get_json(silent=True) or {}
    career_title = str(payload.get("career_title", "")).strip()
    if not career_title:
        return jsonify({"error": "career_title is required"}), 400

    username = current_user()
    if bookmarks_collection is not None:
        existing = bookmarks_collection.find_one({"username": username, "career_title": career_title})
        if existing:
            bookmarks_collection.delete_one({"username": username, "career_title": career_title})
            return jsonify({"saved": False, "message": "Bookmark removed"})
        bookmarks_collection.insert_one({"username": username, "career_title": career_title, "created_at": now_iso()})
        return jsonify({"saved": True, "message": "Bookmark saved"})

    existing = next((b for b in fallback_bookmarks if b["username"] == username and b["career_title"] == career_title), None)
    if existing:
        fallback_bookmarks.remove(existing)
        return jsonify({"saved": False, "message": "Bookmark removed"})
    fallback_bookmarks.append({"username": username, "career_title": career_title, "created_at": now_iso()})
    return jsonify({"saved": True, "message": "Bookmark saved"})


@app.route("/dashboard-stats", methods=["GET"])
@login_required
def dashboard_stats():
    username = current_user()
    if analyses_collection is not None:
        analysis_count = analyses_collection.count_documents({"username": username})
    else:
        analysis_count = len([a for a in fallback_analyses if a.get("username") == username])

    if resumes_collection is not None:
        resume_count = resumes_collection.count_documents({"username": username})
    else:
        resume_count = len([r for r in fallback_resumes if r.get("username") == username])

    if bookmarks_collection is not None:
        bookmark_count = bookmarks_collection.count_documents({"username": username})
    else:
        bookmark_count = len([b for b in fallback_bookmarks if b.get("username") == username])

    return jsonify({
        "analyses": analysis_count,
        "resumes": resume_count,
        "bookmarks": bookmark_count,
    })


@app.route("/db-status", methods=["GET"])
def db_status():
    return jsonify({
        "mongodb_connected": mongo_db is not None,
        "database": os.getenv("MONGO_DB_NAME", "careercompass_ai"),
    })


init_mongodb()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)

