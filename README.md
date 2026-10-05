# 📄 Automated Resume Parser & ATS Matcher

An intelligent, production-ready **Automated Resume Parser & Applicant Tracking System (ATS) Matcher** built with Python and Flask. It extracts key candidate attributes from resumes across multiple formats (**PDF**, **DOCX**, **TXT**), extracts skills with domain categorization, evaluates job description fit with ATS scoring, and stores candidate profiles in a resilient database (**SQLite** default or **PostgreSQL**).

---

## 🌟 Key Features

- **Multi-Format Document Parsing**:
  - Supports `.pdf` (using `pdfplumber` with fallback to `pypdf`), `.docx` (via `python-docx`), and `.txt`.
- **NLP & Heuristic Information Extraction**:
  - **Candidate Name**: Multi-tier header detection and POS-tagging heuristics with spaCy/NLTK fallbacks.
  - **Contact Details**: International & Indian 10-digit phone numbers and RFC-compliant emails.
  - **Professional Links**: Automatic extraction of LinkedIn and GitHub profile links.
  - **Categorized Skills**: Strict word-boundary matching across Programming Languages, Frameworks, AI/ML, Databases, Cloud & DevOps, and Methodologies.
  - **Education & Degrees**: Identification of degrees (B.Tech, M.Tech, B.E., BSc, BCA, MCA, MBA, PhD, etc.).
  - **Experience**: Detection of total experience and active timeframe ranges.
- **🎯 ATS Resume Matcher**:
  - Compare any resume against a target **Job Description (JD)**.
  - Generates an **ATS Match Percentage**, lists **Matched Skills**, and highlights **Missing Skills**.
- **💾 Zero-Configuration Database**:
  - Uses **SQLite** by default (runs immediately out-of-the-box with zero setup).
  - Easily configurable for **PostgreSQL** via environment variables (`DATABASE_URL` or `USE_POSTGRES=true`).
- **🖥️ Modern Responsive UI**:
  - Clean Bootstrap 5 dashboard with drag-and-drop resume uploader.
  - Candidate profile cards with color-coded skill badges.
  - Candidate Directory table with instant search and filtering.
  - Downloadable candidate exports (**CSV** and **JSON**).
- **🔌 REST API**:
  - Full programmatic access (`/api/parse`, `/api/candidates`).

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/vssanjeevi678/Automated-Resume-Parser.git
cd Automated-Resume-Parser
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📁 Project Structure

```text
Automated-Resume-Parser/
├── app.py                 # Flask server, web routes & REST API endpoints
├── parser.py              # Resume extraction engine (PDF, DOCX, TXT, NLP, ATS)
├── database.py            # SQLite & PostgreSQL database manager
├── skills.txt             # Categorized skills database
├── requirements.txt       # Python dependencies
├── templates/
│   ├── index.html         # Main dashboard & drag-and-drop resume parser
│   ├── candidates.html    # Candidate directory table with search & actions
│   └── candidate_detail.html # Detailed candidate profile view
└── uploads/               # Temporary uploaded resume storage
```

---

## 📡 REST API Documentation

### 1. Parse a Resume
- **Endpoint**: `POST /api/parse`
- **Body**: `multipart/form-data`
  - `resume`: File (`.pdf`, `.docx`, or `.txt`)
  - `job_description`: *(Optional)* Target JD text
- **Response**:
```json
{
  "success": true,
  "data": {
    "name": "Jane Doe",
    "email": "jane.doe@example.com",
    "phone": "+91 9876543210",
    "linkedin": "https://linkedin.com/in/janedoe",
    "github": "https://github.com/janedoe",
    "skills": ["Python", "Flask", "Docker", "PostgreSQL"],
    "skills_count": 4,
    "education": ["B.Tech in Computer Science"],
    "experience": {"years": "2"},
    "ats_result": {
      "score": 80.0,
      "matched_skills": ["Python", "Flask", "Docker"],
      "missing_skills": ["Kubernetes"],
      "total_jd_skills": 4
    }
  }
}
```

### 2. List All Candidates
- **Endpoint**: `GET /api/candidates?q=python`
- **Response**: List of candidate records matching query.

---

## 🗄️ Database Configuration (Optional PostgreSQL)

By default, the application runs on **SQLite** (`resume_db.sqlite`). If you wish to connect to PostgreSQL:
```bash
# On Linux/macOS
export DATABASE_URL="postgresql://postgres:password@localhost:5432/resume_db"

# On Windows PowerShell
$env:DATABASE_URL="postgresql://postgres:password@localhost:5432/resume_db"

python app.py
```

---

## 📄 License
This project is open-source and available under the MIT License.