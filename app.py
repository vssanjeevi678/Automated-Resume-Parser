import os
import csv
import io
import json
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify, Response
)
from werkzeug.utils import secure_filename

import parser
import database

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "resume_parser_secret_key_2026")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    recent_candidates = database.get_all_candidates()[:5]
    return render_template("index.html", recent_candidates=recent_candidates)


@app.route("/upload", methods=["POST"])
def upload():
    if "resume" not in request.files:
        flash("No file part selected.", "warning")
        return redirect(url_for("home"))

    file = request.files["resume"]
    job_description = request.form.get("job_description", "").strip()

    if file.filename == "":
        flash("No resume file selected for upload.", "warning")
        return redirect(url_for("home"))

    if not allowed_file(file.filename):
        flash("Unsupported file format. Please upload a PDF, DOCX, or TXT file.", "danger")
        return redirect(url_for("home"))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        parsed_data = parser.parse_resume(filepath, job_description=job_description)

        # Format fields for database storage
        education_str = ", ".join(parsed_data["education"]) if parsed_data["education"] else "Not Specified"
        skills_str = ", ".join(parsed_data["skills"]) if parsed_data["skills"] else "Not Specified"
        ats_score_val = parsed_data["ats_result"].get("score")

        candidate_id = database.insert_candidate(
            name=parsed_data["name"],
            email=parsed_data["email"],
            phone=parsed_data["phone"],
            education=education_str,
            skills=skills_str,
            linkedin=parsed_data["linkedin"],
            github=parsed_data["github"],
            experience=parsed_data["experience"].get("years", "0"),
            ats_score=ats_score_val,
            filename=filename
        )

        flash("Resume uploaded and parsed successfully!", "success")

        return render_template(
            "index.html",
            parsed=parsed_data,
            candidate_id=candidate_id,
            job_description=job_description,
            recent_candidates=database.get_all_candidates()[:5]
        )

    except Exception as e:
        flash(f"Error parsing resume: {str(e)}", "danger")
        return redirect(url_for("home"))


@app.route("/candidates")
def list_candidates():
    query = request.args.get("q", "").strip()
    candidates = database.get_all_candidates(search=query if query else None)
    return render_template("candidates.html", candidates=candidates, query=query)


@app.route("/candidates/<int:candidate_id>")
def get_candidate(candidate_id):
    candidate = database.get_candidate_by_id(candidate_id)
    if not candidate:
        flash("Candidate not found.", "warning")
        return redirect(url_for("list_candidates"))
    return render_template("candidate_detail.html", candidate=candidate)


@app.route("/delete/<int:candidate_id>", methods=["POST"])
def delete_candidate(candidate_id):
    database.delete_candidate(candidate_id)
    flash("Candidate record deleted successfully.", "info")
    return redirect(url_for("list_candidates"))


@app.route("/export/csv")
def export_csv():
    candidates = database.get_all_candidates()
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["ID", "Name", "Email", "Phone", "LinkedIn", "GitHub", "Education", "Skills", "Experience (Years)", "ATS Score (%)", "Filename", "Date Added"])

    for c in candidates:
        writer.writerow([
            c.get("id"),
            c.get("name"),
            c.get("email"),
            c.get("phone"),
            c.get("linkedin"),
            c.get("github"),
            c.get("education"),
            c.get("skills"),
            c.get("experience"),
            c.get("ats_score"),
            c.get("filename"),
            c.get("created_at")
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=candidates_export.csv"}
    )


@app.route("/export/json")
def export_json():
    candidates = database.get_all_candidates()
    return Response(
        json.dumps(candidates, indent=2, default=str),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=candidates_export.json"}
    )


# ==========================================
# REST API Endpoints
# ==========================================

@app.route("/api/parse", methods=["POST"])
def api_parse():
    if "resume" not in request.files:
        return jsonify({"error": "No resume file provided in 'resume' form field"}), 400

    file = request.files["resume"]
    job_description = request.form.get("job_description", "")

    if file.filename == "" or not allowed_file(file.filename):
        return jsonify({"error": "Valid PDF, DOCX, or TXT file required"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        parsed_data = parser.parse_resume(filepath, job_description=job_description)
        education_str = ", ".join(parsed_data["education"]) if parsed_data["education"] else ""
        skills_str = ", ".join(parsed_data["skills"]) if parsed_data["skills"] else ""

        candidate_id = database.insert_candidate(
            name=parsed_data["name"],
            email=parsed_data["email"],
            phone=parsed_data["phone"],
            education=education_str,
            skills=skills_str,
            linkedin=parsed_data["linkedin"],
            github=parsed_data["github"],
            experience=parsed_data["experience"].get("years", "0"),
            ats_score=parsed_data["ats_result"].get("score"),
            filename=filename
        )

        parsed_data["candidate_id"] = candidate_id
        return jsonify({"success": True, "data": parsed_data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/candidates", methods=["GET"])
def api_candidates():
    query = request.args.get("q", "").strip()
    candidates = database.get_all_candidates(search=query if query else None)
    return jsonify({"count": len(candidates), "candidates": candidates})


@app.route("/api/candidates/<int:candidate_id>", methods=["GET", "DELETE"])
def api_candidate_by_id(candidate_id):
    if request.method == "GET":
        candidate = database.get_candidate_by_id(candidate_id)
        if not candidate:
            return jsonify({"error": "Candidate not found"}), 404
        return jsonify(candidate)

    elif request.method == "DELETE":
        success = database.delete_candidate(candidate_id)
        return jsonify({"success": success, "message": f"Candidate {candidate_id} deleted."})


if __name__ == "__main__":
    app.run(debug=True, port=5000)