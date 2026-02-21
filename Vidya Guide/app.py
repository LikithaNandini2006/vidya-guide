import os
import json
import re
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import PyPDF2
from groq import Groq

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# Flask setup
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXT = {"pdf"}


# --------------------------
# PDF TEXT EXTRACTOR
# --------------------------
def extract_pdf_text(path):
    try:
        reader = PyPDF2.PdfReader(path)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content
        return text
    except:
        return ""


# --------------------------
# ROUTES
# --------------------------

@app.route("/")
def home():
    return render_template("dashboard.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/chat")
def chat_ui():
    return render_template("chat.html")


# --------------------------
# CHATBOT (LIVE GROQ AI)
# --------------------------
@app.route("/chatbot", methods=["POST"])
def chatbot():
    user_msg = request.json.get("message", "")

    if not user_msg:
        return jsonify({"reply": "Please type a message."})

    try:
        ai_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": user_msg}],
            temperature=0.4
        )

        reply = ai_response.choices[0].message.content

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"❌ Groq Error: {str(e)}"})


# --------------------------
# RESUME ANALYZER (JSON SAFE)
# --------------------------
@app.route("/analyze", methods=["POST"])
def analyze_resume():
    if "file" not in request.files:
        return jsonify({"error": "Upload a PDF file!"})

    file = request.files["file"]

    if not (file and file.filename.endswith(".pdf")):
        return jsonify({"error": "Only PDF allowed!"})

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Extract text
    resume_text = extract_pdf_text(filepath)

    if len(resume_text.strip()) < 20:
        return jsonify({"error": "Could not extract text. Try another PDF!"})

    # ====== AI PROMPT ======
    prompt = f"""
You are VidyaGuide AI – a strict JSON-only Resume Analyzer.
Your output MUST be VALID JSON ONLY, no text, no markdown.

Return EXACTLY this structure:

{{
 "score": 0,
 "strengths": [],
 "weaknesses": [],
 "skills_missing": [],
 "job_roles": [],
 "career_paths": [],
 "roadmap_6m": [],
 "roadmap_12m": [],
 "interview_questions": [],
 "summary": ""
}}

Analyze this resume:
{resume_text}
    """

    try:
        ai_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=2000
        )

        raw_output = ai_response.choices[0].message.content

        # Extract JSON using regex
        json_match = re.search(r"\{[\s\S]*\}", raw_output)

        if not json_match:
            return jsonify({
                "error": "AI did not return valid JSON!",
                "raw": raw_output
            })

        json_text = json_match.group(0)
        data = json.loads(json_text)

    except Exception as e:
        return jsonify({
            "error": "AI Processing Failed",
            "exception": str(e),
            "raw_output": raw_output if 'raw_output' in locals() else "NO RAW OUTPUT"
        })

    return render_template("result.html", data=data)


# --------------------------
# START SERVER
# --------------------------
if __name__ == "__main__":
    print("🚀 VidyaGuide AI Running at http://127.0.0.1:5000")
    app.run(debug=True)