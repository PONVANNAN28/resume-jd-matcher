from flask import Flask, request, jsonify, render_template
import pdfplumber
import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")


def extract_job_search_terms(resume_text):
    prompt = f"""You are a career assistant. Read the resume text below and identify:
1. The 5-8 most relevant technical/professional skills
2. The 2-3 best-fitting job titles to search for (e.g. "Software Engineer Intern")
3. A short one-line search query combining the top skills and role, suitable for searching a job board

Resume text:
{resume_text}

Respond ONLY in this exact JSON format, nothing else:
{{
  "skills": ["skill1", "skill2"],
  "job_titles": ["title1", "title2"],
  "search_query": "short search string"
}}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    raw = response.choices[0].message.content
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)


def search_jobs(query, country="in", results=10):
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": query,
        "results_per_page": results,
        "content-type": "application/json"
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print("ADZUNA ERROR:", response.status_code, response.text)

    response.raise_for_status()
    data = response.json()

    jobs = []
    for job in data.get("results", []):
        jobs.append({
            "title": job.get("title"),
            "company": job.get("company", {}).get("display_name", "Unknown"),
            "location": job.get("location", {}).get("display_name", "Unknown"),
            "url": job.get("redirect_url"),
            "description": (job.get("description") or "")[:200] + "..."
        })

    return jobs


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['resume']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Please upload a valid PDF file"}), 400

    try:
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception:
        return jsonify({"error": "Could not read this PDF. It may be corrupted or scanned as an image."}), 400

    if not text.strip():
        return jsonify({"error": "No readable text found in this PDF. It may be a scanned image."}), 400

    try:
        ai_result = extract_job_search_terms(text)
    except Exception as e:
        return jsonify({"error": f"AI analysis failed: {str(e)}"}), 500

    try:
        jobs = search_jobs(ai_result["job_titles"][0])
    except Exception as e:
        return jsonify({"error": f"Job search failed: {str(e)}"}), 500

    return jsonify({
        "skills": ai_result["skills"],
        "job_titles": ai_result["job_titles"],
        "search_query": ai_result["search_query"],
        "jobs": jobs
    })


if __name__ == '__main__':
    app.run(debug=True)