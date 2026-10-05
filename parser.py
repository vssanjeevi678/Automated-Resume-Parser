import os
import re
from typing import Dict, List, Optional, Any

# PDF & Document extractors
import pdfplumber
import pypdf
import docx

# Optional NLP libraries with safe fallbacks
nlp = None
try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = None
except Exception:
    nlp = None

nltk_available = False
try:
    import nltk
    nltk_available = True
except Exception:
    nltk_available = False


# Skill categories mapping
SKILL_CATEGORIES = {
    "Programming Languages": [
        "python", "java", "c", "c++", "c#", "javascript", "typescript", "go", "golang",
        "rust", "ruby", "php", "swift", "kotlin", "r", "scala", "dart", "perl",
        "bash", "shell", "powershell", "sql", "html", "html5", "css", "css3", "scss", "sass"
    ],
    "Frameworks & Libraries": [
        "react", "react.js", "react native", "angular", "angularjs", "vue", "vue.js",
        "next.js", "nuxt.js", "node.js", "express", "express.js", "django", "flask",
        "fastapi", "spring", "spring boot", "asp.net", ".net", ".net core", "laravel",
        "ruby on rails", "jquery", "redux", "tailwind css", "tailwind", "bootstrap", "graphql", "rest api"
    ],
    "AI, ML & Data Science": [
        "machine learning", "deep learning", "artificial intelligence", "nlp",
        "natural language processing", "computer vision", "data science", "data analysis",
        "data analytics", "pandas", "numpy", "scikit-learn", "tensorflow", "keras",
        "pytorch", "opencv", "nltk", "spacy", "huggingface", "transformers", "llm",
        "generative ai", "prompt engineering", "tableau", "power bi", "matplotlib", "seaborn",
        "spark", "pyspark", "hadoop"
    ],
    "Databases": [
        "mysql", "postgresql", "sqlite", "mongodb", "redis", "oracle", "cassandra",
        "dynamodb", "mariadb", "firebase", "firestore", "supabase", "neo4j", "microsoft sql server", "elasticsearch"
    ],
    "Cloud & DevOps": [
        "aws", "amazon web services", "azure", "microsoft azure", "google cloud platform", "gcp",
        "docker", "kubernetes", "terraform", "ansible", "jenkins", "ci/cd", "git", "github",
        "gitlab", "bitbucket", "linux", "unix", "ubuntu", "nginx", "apache", "kafka", "rabbitmq", "microservices"
    ],
    "Methodologies & Tools": [
        "agile", "scrum", "jira", "sdlc", "oop", "object-oriented programming",
        "data structures", "algorithms", "system design", "unit testing", "tdd", "selenium", "pytest", "postman"
    ]
}


def load_skills() -> List[str]:
    """Load skills list from skills.txt if present, with categorized defaults fallback."""
    skills_file = os.path.join(os.path.dirname(__file__), "skills.txt")
    loaded = []
    if os.path.exists(skills_file):
        with open(skills_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    loaded.append(line.lower())

    if not loaded:
        for cat_skills in SKILL_CATEGORIES.values():
            loaded.extend(cat_skills)

    # Return unique sorted by length descending so multi-word skills match first
    return sorted(list(set(loaded)), key=lambda s: len(s), reverse=True)


SKILLS = load_skills()


def extract_text(file_path: str) -> str:
    """Extract text from PDF, DOCX, or TXT file with fallback strategies."""
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext == ".pdf":
        # First attempt: pdfplumber
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception:
            pass

        # Fallback attempt: pypdf
        if not text.strip():
            try:
                reader = pypdf.PdfReader(file_path)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            except Exception:
                pass

    elif ext in [".docx", ".doc"]:
        try:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text + "\n"
            for table in doc.tables:
                for row in table.rows:
                    row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_text:
                        text += " | ".join(row_text) + "\n"
        except Exception:
            pass

    elif ext == ".txt":
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            pass

    return text.strip()


def extract_email(text: str) -> str:
    """Extract candidate email using regex."""
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    match = re.search(email_pattern, text)
    return match.group(0).strip().rstrip(".") if match else ""


def extract_phone(text: str) -> str:
    """Extract phone number (international, Indian 10-digit, US/formatted)."""
    phone_patterns = [
        # Indian phone numbers with optional +91 or 0
        r'(?:(?:\+|0{0,2})91[\s-]?)?[6789]\d{9}',
        # Standard formatted international / US numbers
        r'\+?\d{1,3}[\s-]?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}',
        # General bracketed or spaced numbers
        r'\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}'
    ]
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(0).strip()
            # Clean up candidate string
            digits = re.sub(r'\D', '', candidate)
            if 10 <= len(digits) <= 15:
                return candidate
    return ""


def extract_links(text: str) -> Dict[str, str]:
    """Extract LinkedIn, GitHub, and Portfolio URLs."""
    links = {"linkedin": "", "github": "", "portfolio": ""}

    linkedin_pattern = r'(https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+)'
    github_pattern = r'(https?://(?:www\.)?github\.com/[a-zA-Z0-9_-]+)'
    url_pattern = r'https?://[^\s/$.?#].[^\s]*'

    li_match = re.search(linkedin_pattern, text, re.IGNORECASE)
    if li_match:
        links["linkedin"] = li_match.group(0)

    gh_match = re.search(github_pattern, text, re.IGNORECASE)
    if gh_match:
        links["github"] = gh_match.group(0)

    urls = re.findall(url_pattern, text)
    for u in urls:
        if "linkedin.com" not in u.lower() and "github.com" not in u.lower():
            links["portfolio"] = u
            break

    return links


def extract_name(text: str) -> str:
    """Extract candidate name using heuristic analysis, NLTK/POS tagging, or spaCy."""
    # 1. Fallback to spaCy if available
    if nlp is not None:
        try:
            doc = nlp(text[:1000])
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    clean = ent.text.strip().replace("\n", " ")
                    if len(clean.split()) in [2, 3, 4] and not any(ch in clean for ch in "@/:0123456789"):
                        return clean.title()
        except Exception:
            pass

    # 2. Heuristic extraction from first 10 non-empty lines
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    ignore_words = {
        "resume", "curriculum", "vitae", "cv", "profile", "contact",
        "phone", "email", "address", "education", "experience", "skills",
        "projects", "objective", "summary", "page", "developer", "engineer",
        "software", "data", "scientist", "analyst", "portfolio", "linkedin", "github"
    }

    for line in lines[:10]:
        # Skip lines containing email, URL, phone, or pure symbols
        if "@" in line or "http" in line or "www" in line:
            continue
        if re.search(r'\d{5,}', line):
            continue

        clean_line = re.sub(r'[^a-zA-Z\s.]', '', line).strip()
        words = clean_line.split()

        # Typical names are 2 to 4 words long
        if 2 <= len(words) <= 4:
            first_word_lower = words[0].lower()
            if any(ign in line.lower() for ign in ignore_words):
                continue
            # Ensure words look like real names (alphabetic, proper capitalization or uppercase)
            if all(w.isalpha() for w in words):
                return clean_line.title()

    # If first line has a single name or single word
    if lines:
        first_line = re.sub(r'[^a-zA-Z\s]', '', lines[0]).strip()
        if 1 <= len(first_line.split()) <= 3 and first_line.lower() not in ignore_words:
            return first_line.title()

    return "Candidate"


def extract_skills(text: str) -> Dict[str, Any]:
    """
    Extract skills using strict word boundaries to avoid false positives.
    Returns both categorized skills and a flat list of found skills.
    """
    found_flat = set()
    categorized = {category: [] for category in SKILL_CATEGORIES}
    text_lower = " " + text.lower() + " "

    for skill in SKILLS:
        skill_lower = skill.lower()
        # Handle special characters in tech skills (e.g., C++, C#, .NET)
        if skill_lower in ["c++", "c#", ".net"]:
            pattern = r'(?<![a-zA-Z0-9])' + re.escape(skill_lower) + r'(?![a-zA-Z0-9])'
        else:
            pattern = r'\b' + re.escape(skill_lower) + r'\b'

        if re.search(pattern, text_lower):
            display_name = skill.title() if not skill.isupper() else skill
            # Format popular acronyms and canonical tech names
            special_names = {
                "sql": "SQL", "html": "HTML", "html5": "HTML5", "css": "CSS", "css3": "CSS3",
                "aws": "AWS", "gcp": "GCP", "ci/cd": "CI/CD", "api": "API", "rest api": "REST API",
                "nlp": "NLP", "llm": "LLM", "ai": "AI", "oop": "OOP", "sdlc": "SDLC", "tdd": "TDD",
                "c++": "C++", "c#": "C#", ".net": ".NET", "php": "PHP", "ui/ux": "UI/UX",
                "pytorch": "PyTorch", "tensorflow": "TensorFlow", "scikit-learn": "Scikit-Learn",
                "javascript": "JavaScript", "typescript": "TypeScript", "mongodb": "MongoDB",
                "postgresql": "PostgreSQL", "mysql": "MySQL", "sqlite": "SQLite",
                "next.js": "Next.js", "node.js": "Node.js", "vue.js": "Vue.js", "react.js": "React.js",
                "express.js": "Express.js", "graphql": "GraphQL", "github": "GitHub", "gitlab": "GitLab",
                "powershell": "PowerShell"
            }
            if skill_lower in special_names:
                display_name = special_names[skill_lower]

            found_flat.add(display_name)

            # Categorize the skill
            for cat, cat_skills in SKILL_CATEGORIES.items():
                if skill_lower in cat_skills:
                    if display_name not in categorized[cat]:
                        categorized[cat].append(display_name)

    # Remove empty categories
    active_categories = {k: v for k, v in categorized.items() if v}

    return {
        "skills_list": sorted(list(found_flat)),
        "categorized": active_categories,
        "total_count": len(found_flat)
    }


def extract_education(text: str) -> List[str]:
    """Extract education degrees, majors, and institutions."""
    degree_keywords = [
        r'\bB\.?Tech(?:nology)?\b',
        r'\bM\.?Tech(?:nology)?\b',
        r'\bB\.?E\.?\b',
        r'\bM\.?E\.?\b',
        r'\bB\.?Sc\.?\b|\bBachelor of Science\b',
        r'\bM\.?Sc\.?\b|\bMaster of Science\b',
        r'\bBCA\b|\bBachelor of Computer Applications?\b',
        r'\bMCA\b|\bMaster of Computer Applications?\b',
        r'\bBBA\b|\bBachelor of Business Administration\b',
        r'\bMBA\b|\bMaster of Business Administration\b',
        r'\bPh\.?D\.?\b|\bDoctor of Philosophy\b',
        r'\bBachelor(?:\'s)?(?:\s+degree)?\b',
        r'\bMaster(?:\'s)?(?:\s+degree)?\b',
        r'\bDiploma\b',
        r'\bHigher Secondary\b|\b12th\b|\bHigh School\b'
    ]

    found_degrees = []
    lines = text.split("\n")

    for line in lines:
        for deg_pat in degree_keywords:
            if re.search(deg_pat, line, re.IGNORECASE):
                cleaned = line.strip()
                # Limit length to avoid huge paragraphs
                if len(cleaned) <= 120 and cleaned not in found_degrees:
                    found_degrees.append(cleaned)
                break

    # If no line matches degree context, look for general degree terms
    if not found_degrees:
        simple_degrees = ["B.Tech", "M.Tech", "B.E", "BSc", "MSc", "BCA", "MCA", "MBA", "PhD", "Bachelor", "Master"]
        for deg in simple_degrees:
            if re.search(r'\b' + re.escape(deg) + r'\b', text, re.IGNORECASE):
                found_degrees.append(deg)

    return list(dict.fromkeys(found_degrees))


def extract_experience(text: str) -> Dict[str, Any]:
    """Extract years of experience and work experience highlights."""
    exp_info = {
        "years": "0",
        "details": []
    }

    # Search for explicit years of experience pattern
    year_patterns = [
        r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?experience',
        r'experience\s*:\s*(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)'
    ]
    for pat in year_patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            exp_info["years"] = match.group(1)
            break

    # Search for date ranges like (2020 - 2023) or (2021 - Present)
    date_ranges = re.findall(r'\b(20\d{2}|19\d{2})\s*(?:-|to|–)\s*(20\d{2}|Present|Current)\b', text, re.IGNORECASE)
    if date_ranges:
        exp_info["date_ranges"] = [f"{start} - {end}" for start, end in date_ranges]

    return exp_info


def calculate_ats_score(resume_skills: List[str], job_description: str) -> Dict[str, Any]:
    """
    Calculate ATS match score between resume skills and Job Description.
    Returns score percentage, matched skills, and missing skills.
    """
    if not job_description or not job_description.strip():
        return {
            "score": None,
            "matched_skills": [],
            "missing_skills": [],
            "total_jd_skills": 0,
            "summary": "No job description provided for ATS matching."
        }

    # Extract required skills from the job description
    jd_skills_data = extract_skills(job_description)
    jd_skills = jd_skills_data["skills_list"]

    if not jd_skills:
        return {
            "score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "total_jd_skills": 0,
            "summary": "Could not identify specific technical skills in the provided job description."
        }

    resume_skills_lower = {s.lower() for s in resume_skills}
    matched = []
    missing = []

    for s in jd_skills:
        if s.lower() in resume_skills_lower:
            matched.append(s)
        else:
            missing.append(s)

    match_percentage = round((len(matched) / len(jd_skills)) * 100, 1)

    return {
        "score": match_percentage,
        "matched_skills": matched,
        "missing_skills": missing,
        "total_jd_skills": len(jd_skills),
        "summary": f"Resume matches {len(matched)} out of {len(jd_skills)} required skills ({match_percentage}%)."
    }


def parse_resume(file_path: str, job_description: Optional[str] = None) -> Dict[str, Any]:
    """
    Master function to parse a resume document and optionally compute ATS score.
    """
    raw_text = extract_text(file_path)

    name = extract_name(raw_text)
    email = extract_email(raw_text)
    phone = extract_phone(raw_text)
    links = extract_links(raw_text)
    skills_data = extract_skills(raw_text)
    education = extract_education(raw_text)
    experience = extract_experience(raw_text)
    ats_result = calculate_ats_score(skills_data["skills_list"], job_description or "")

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": links["linkedin"],
        "github": links["github"],
        "portfolio": links["portfolio"],
        "skills": skills_data["skills_list"],
        "skills_categorized": skills_data["categorized"],
        "skills_count": skills_data["total_count"],
        "education": education,
        "experience": experience,
        "ats_result": ats_result,
        "raw_text_length": len(raw_text)
    }