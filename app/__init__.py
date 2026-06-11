import os
import json
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from app.parser import parse_resume
from app.matcher import calculate_match_scores
from app.groq_client import get_groq_explanation
from dotenv import load_dotenv

# Load environment variables from project root .env
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(BASE_DIR, '.env'))

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['UPLOAD_FOLDER'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/uploads'))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Preload Job Descriptions
JOBS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/jobs.json'))
jobs_db = []
if os.path.exists(JOBS_PATH):
    try:
        with open(JOBS_PATH, 'r', encoding='utf-8') as f:
            jobs_db = json.load(f)
        print(f"Preloaded {len(jobs_db)} jobs from jobs.json.")
    except Exception as e:
        print(f"Error loading jobs.json: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/comparison')
def comparison():
    return render_template('comparison.html')

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    return jsonify(jobs_db)

@app.route('/api/match', methods=['POST'])
def match_resume():
    if 'resume' not in request.files:
        return jsonify({"success": False, "error": "No resume file uploaded."}), 400
        
    file = request.files['resume']
    job_id = request.form.get('job_id')
    
    if file.filename == '':
        return jsonify({"success": False, "error": "No file selected."}), 400
        
    if not job_id:
        return jsonify({"success": False, "error": "No job description selected."}), 400
        
    # Find selected job details
    selected_job = next((j for j in jobs_db if j['id'] == job_id), None)
    if not selected_job:
        return jsonify({"success": False, "error": f"Job ID {job_id} not found in database."}), 404
        
    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        try:
            # 1. Parse Resume
            parsed_result = parse_resume(upload_path)
            
            # Clean up upload file
            if os.path.exists(upload_path):
                try:
                    os.remove(upload_path)
                except Exception:
                    pass
            
            if not parsed_result['success']:
                return jsonify({"success": False, "error": parsed_result['error']}), 400
                
            resume_data = parsed_result['data']
            
            # 2. Score Match with Model A (Base Model)
            match_results_base = calculate_match_scores(resume_data, selected_job, use_tuned_model=False)
            
            # 3. Score Match with Model B (Fine-Tuned Model)
            match_results_tuned = calculate_match_scores(resume_data, selected_job, use_tuned_model=True)
            
            # 4. Generate Explainable Feedback (Groq API / fallback)
            explanation, is_live_groq = get_groq_explanation(resume_data, selected_job)
            
            response_payload = {
                "success": True,
                "job": selected_job,
                "parsed_resume": {
                    "skills": resume_data.get('SKILLS', ''),
                    "experience": resume_data.get('EXPERIENCE', ''),
                    "projects": resume_data.get('PROJECTS', ''),
                    "education": resume_data.get('EDUCATION', ''),
                    "experience_valid": resume_data.get('EXPERIENCE_VALID', False)
                },
                "base_model_match": match_results_base,
                "tuned_model_match": match_results_tuned,
                "explanation": explanation,
                "is_live_groq": is_live_groq,
                "has_groq_key": bool(os.environ.get("GROQ_API_KEY"))
            }
            
            return jsonify(response_payload)
            
        except Exception as e:
            # Clean up file in case of exception
            if os.path.exists(upload_path):
                try:
                    os.remove(upload_path)
                except Exception:
                    pass
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "error": f"An error occurred during processing: {str(e)}"}), 500
            
    else:
        return jsonify({"success": False, "error": "Only PDF resumes are supported."}), 400

@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    # Exposes saved model comparison metrics JSON for dashboard widgets
    metrics_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static/metrics_comparison.json'))
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify([])
