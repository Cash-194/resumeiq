from flask import Flask, render_template, request
import pdfplumber
from groq import Groq
import json
import os
import re

app = Flask(__name__)

client = Groq(api_key="GROQ_API_KEY")

os.makedirs("uploads", exist_ok=True)

def extract_json(text):
    text = text.replace("```json", "").replace("```", "")
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    file = request.files.get("resume")

    if not file:
        return "No file selected"

    filepath = "uploads/" + file.filename
    file.save(filepath)

    text = ""
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

    prompt = f"""
You are an expert technical recruiter and career coach.
Analyze this resume THOROUGHLY and respond ONLY with valid JSON, no markdown, no backticks.

IMPORTANT:
- Cover EVERY skill, project, technology, and achievement mentioned in the resume
- HR questions must cover personality, teamwork, goals, strengths, weaknesses, situations
- Technical questions must cover every single technology, project, language, concept in the resume
- Suggested answers must be confident, specific, and reference actual resume content
- Weak areas must be written from a RECRUITER perspective pointing out missing skills. Be direct and critical.
- Do NOT write weak areas from the candidate's perspective

{{
  "summary": "<6-7 line detailed candidate summary covering all key points>",
  "resume_score": {{
    "overall": <number out of 100>,
    "breakdown": {{
      "skills": <score out of 20>,
      "projects": <score out of 20>,
      "experience": <score out of 20>,
      "education": <score out of 20>,
      "presentation": <score out of 20>
    }},
    "verdict": "<one line honest verdict>"
  }},
  "hr_questions": [
    {{"question": "<HR question>", "answer": "<3-4 line suggested answer>"}},
    {{"question": "<HR question>", "answer": "<3-4 line suggested answer>"}},
    {{"question": "<HR question>", "answer": "<3-4 line suggested answer>"}},
    {{"question": "<HR question>", "answer": "<3-4 line suggested answer>"}},
    {{"question": "<HR question>", "answer": "<3-4 line suggested answer>"}},
    {{"question": "<HR question>", "answer": "<3-4 line suggested answer>"}},
    {{"question": "<HR question>", "answer": "<3-4 line suggested answer>"}}
  ],
  "technical_questions": [
    {{"question": "<technical question>", "answer": "<3-4 line answer>"}},
    {{"question": "<technical question>", "answer": "<3-4 line answer>"}},
    {{"question": "<technical question>", "answer": "<3-4 line answer>"}},
    {{"question": "<technical question>", "answer": "<3-4 line answer>"}},
    {{"question": "<technical question>", "answer": "<3-4 line answer>"}},
    {{"question": "<technical question>", "answer": "<3-4 line answer>"}},
    {{"question": "<technical question>", "answer": "<3-4 line answer>"}},
    {{"question": "<technical question>", "answer": "<3-4 line answer>"}},
    {{"question": "<technical question>", "answer": "<3-4 line answer>"}},
    {{"question": "<technical question>", "answer": "<3-4 line answer>"}}
  ],
  "improved_bullets": [
    {{"original": "<weak bullet from resume>", "improved": "<stronger rewritten version>"}},
    {{"original": "<weak bullet from resume>", "improved": "<stronger rewritten version>"}},
    {{"original": "<weak bullet from resume>", "improved": "<stronger rewritten version>"}}
  ],
  "missing_keywords": [
    "<missing keyword 1>",
    "<missing keyword 2>",
    "<missing keyword 3>",
    "<missing keyword 4>",
    "<missing keyword 5>",
    "<missing keyword 6>"
  ],
  "weak_areas": [
    "<recruiter observation about gap 1>",
    "<recruiter observation about gap 2>",
    "<recruiter observation about gap 3>",
    "<recruiter observation about gap 4>",
    "<recruiter observation about gap 5>"
  ],
  "career_advice": "<6-7 lines of very specific, actionable career advice>"
}}

RESUME:
{text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=4000
    )

    raw = response.choices[0].message.content
    clean = extract_json(raw)

    try:
        data = json.loads(clean)
    except Exception:
        return f"<h3>JSON Parsing Failed</h3><pre>{clean}</pre>"

    return render_template("result.html", data=data)


if __name__ == "__main__":
    app.run(debug=True)