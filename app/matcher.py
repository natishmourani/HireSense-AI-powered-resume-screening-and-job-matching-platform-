import re
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Synonym taxonomy mapping (lowercase canonical mapping)
SYNONYMS = {
    'js': 'javascript',
    'javascript': 'javascript',
    'ml': 'machine learning',
    'machine learning': 'machine learning',
    'postgres': 'postgresql',
    'postgresql': 'postgresql',
    'c sharp': 'c#',
    'csharp': 'c#',
    '.net': 'c#',
    'c#': 'c#',
    'py': 'python',
    'python': 'python',
    'python3': 'python',
    'scikit-learn': 'scikit-learn',
    'sklearn': 'scikit-learn',
    'scikit learn': 'scikit-learn'
}

# Degree level rankings
DEGREE_LEVELS = {
    'phd': 4,
    'doctor': 4,
    'master': 3,
    'ms': 3,
    'mba': 3,
    'bachelor': 2,
    'bs': 2,
    'ba': 2,
    'b.s.': 2,
    'b.a.': 2,
    'engineering': 2,
    'associate': 1
}

# Fields of study mapping
FIELDS_OF_STUDY = {
    'computer science': 'cs',
    'cs': 'cs',
    'information technology': 'it',
    'it': 'it',
    'data science': 'ds',
    'ds': 'ds',
    'software engineering': 'cs',
    'electrical engineering': 'ee',
    'ee': 'ee',
    'mathematics': 'math',
    'math': 'math',
    'business': 'business',
    'mba': 'business',
    'history': 'history'
}

# Cache for models to avoid reloading on every request
_models_cache = {}

def get_model(use_tuned_model=True):
    model_key = 'tuned' if use_tuned_model else 'base'
    if model_key not in _models_cache:
        if use_tuned_model:
            # Look for local fine-tuned model path
            model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../models/fine_tuned_model'))
            if os.path.exists(model_path):
                _models_cache[model_key] = SentenceTransformer(model_path)
            else:
                # Fallback to base model if fine-tuned is not found
                print(f"Warning: Fine-tuned model not found at {model_path}. Falling back to base model.")
                _models_cache[model_key] = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            _models_cache[model_key] = SentenceTransformer('all-MiniLM-L6-v2')
    return _models_cache[model_key]

def normalize_skill(skill):
    skill_cleaned = re.sub(r'[^\w\s#.\+\-]', '', skill.lower()).strip()
    return SYNONYMS.get(skill_cleaned, skill_cleaned)

def calculate_keyword_overlap(text1, text2):
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))
    stopwords = {'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with', 'using', 'of', 'by', 'is', 'are', 'that', 'this'}
    words1 = words1 - stopwords
    words2 = words2 - stopwords
    if not words1 or not words2:
        return 0.0
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union)

def parse_degree_info(education_text):
    # Default outputs
    degree_level = 0
    field_key = 'other'
    
    text_lower = education_text.lower()
    
    # Identify degree level
    for d_word, level in DEGREE_LEVELS.items():
        if re.search(r'\b' + re.escape(d_word) + r'\b', text_lower):
            degree_level = max(degree_level, level)
            
    # Identify field of study
    for f_word, f_key in FIELDS_OF_STUDY.items():
        if re.search(r'\b' + re.escape(f_word) + r'\b', text_lower):
            field_key = f_key
            break
            
    return degree_level, field_key

def calculate_education_rule_score(resume_edu, job_edu_req):
    res_level, res_field = parse_degree_info(resume_edu)
    req_level, req_field = parse_degree_info(job_edu_req)
    
    # 1. Degree level weight multiplier
    if res_level >= req_level:
        level_mult = 1.0
    elif res_level == req_level - 1:
        level_mult = 0.8
    else:
        level_mult = 0.5
        
    # If no degree found in resume but required
    if res_level == 0 and req_level > 0:
        level_mult = 0.2
        
    # 2. Field relevance weight multiplier
    if res_field == req_field:
        field_mult = 1.0
    elif (res_field in ['cs', 'it', 'ds'] and req_field in ['cs', 'it', 'ds']):
        field_mult = 0.9  # Highly related STEM
    elif (res_field == 'ee' and req_field in ['cs', 'it']):
        field_mult = 0.8  # Related STEM
    elif (res_field == 'math' and req_field == 'ds'):
        field_mult = 0.95 # Highly related DS math
    elif res_field == 'other' or req_field == 'other':
        field_mult = 0.5  # Standard default relatedness
    else:
        field_mult = 0.2  # Unrelated (e.g. History vs CS)
        
    return level_mult * field_mult * 100

def calculate_match_scores(parsed_resume, job, use_tuned_model=True):
    model = get_model(use_tuned_model)
    
    # Initialize category scores
    skills_score = 0.0
    experience_score = 0.0
    projects_score = 0.0
    education_score = 0.0
    
    experience_display = ""
    
    # ------------------ 1. Skills Matching & ATS Coverage ------------------
    resume_skills_raw = parsed_resume.get('SKILLS', '').split(',')
    resume_skills = [normalize_skill(s) for s in resume_skills_raw if s.strip()]
    
    job_required_skills = [s.strip() for s in job.get('required_skills', [])]
    job_required_skills_norm = [normalize_skill(s) for s in job_required_skills]
    
    found_skills = []
    missing_skills = []
    
    for orig_skill, norm_skill in zip(job_required_skills, job_required_skills_norm):
        # Check direct or synonym overlap in resume
        match_found = False
        for rs in resume_skills:
            if norm_skill == rs or norm_skill in rs or rs in norm_skill:
                match_found = True
                break
        if match_found:
            found_skills.append(orig_skill)
        else:
            missing_skills.append(orig_skill)
            
    num_req = len(job_required_skills)
    coverage_pct = (len(found_skills) / num_req * 100) if num_req > 0 else 100.0
    
    # Generate skill embeddings similarity (comparing the exact text sections)
    skills_text_resume = ", ".join(resume_skills_raw).strip()
    skills_text_job = ", ".join(job_required_skills).strip()
    
    if skills_text_resume and skills_text_job:
        embs = model.encode([skills_text_resume, skills_text_job])
        skills_emb_sim = max(0.0, float(cosine_similarity([embs[0]], [embs[1]])[0][0]))
    else:
        skills_emb_sim = 0.0
        
    # Combine keyword coverage and embedding similarity
    skills_score = 0.6 * coverage_pct + 0.4 * (skills_emb_sim * 100)
    skills_score = min(100.0, max(0.0, skills_score))
    
    # ------------------ 2. Experience Matching ------------------
    is_exp_valid = parsed_resume.get('EXPERIENCE_VALID', False)
    resume_exp = parsed_resume.get('EXPERIENCE', '').strip()
    job_exp_req_desc = job.get('experience_requirements', {}).get('description', '')
    
    if not is_exp_valid or not resume_exp:
        experience_score = 0.0
        experience_display = "N/A - Experience section not found"
    else:
        # Calculate semantic embedding similarity between validated experiences and job requirements
        embs = model.encode([resume_exp, job_exp_req_desc])
        exp_sim = float(cosine_similarity([embs[0]], [embs[1]])[0][0])
        
        # Scale to 0-100 (min similarity typically 0.2-0.3)
        experience_score = min(100.0, max(0.0, (exp_sim - 0.2) / 0.6 * 100))
        experience_display = f"Valid ({int(experience_score)}% match)"
        
    # ------------------ 3. Projects Matching ------------------
    resume_projects = parsed_resume.get('PROJECTS', '').strip()
    job_proj_req_desc = job.get('project_requirements', {}).get('description', '')
    
    if not resume_projects or not job_proj_req_desc:
        projects_score = 0.0
    else:
        # 70% semantic similarity + 30% keyword overlap
        embs = model.encode([resume_projects, job_proj_req_desc])
        proj_sim = float(cosine_similarity([embs[0]], [embs[1]])[0][0])
        proj_sim_score = min(100.0, max(0.0, (proj_sim - 0.1) / 0.7 * 100))
        
        overlap_score = calculate_keyword_overlap(resume_projects, job_proj_req_desc) * 100
        
        projects_score = 0.70 * proj_sim_score + 0.30 * overlap_score
        projects_score = min(100.0, max(0.0, projects_score))
        
    # ------------------ 4. Education Matching ------------------
    resume_education = parsed_resume.get('EDUCATION', '').strip()
    job_edu_req_desc = job.get('education_requirements', {}).get('description', '')
    
    if not resume_education or not job_edu_req_desc:
        education_score = 0.0
    else:
        # Calculate semantic similarity
        embs = model.encode([resume_education, job_edu_req_desc])
        edu_sim = float(cosine_similarity([embs[0]], [embs[1]])[0][0])
        edu_sim_score = min(100.0, max(0.0, (edu_sim - 0.1) / 0.7 * 100))
        
        # Calculate rule-based score
        edu_rule_score = calculate_education_rule_score(resume_education, job_edu_req_desc)
        
        education_score = 0.50 * edu_sim_score + 0.50 * edu_rule_score
        education_score = min(100.0, max(0.0, education_score))
        
    # ------------------ 5. Overall Score Calculation ------------------
    overall_score = 0.40 * skills_score + 0.25 * experience_score + 0.20 * projects_score + 0.15 * education_score
    overall_score = min(100.0, max(0.0, overall_score))
    
    return {
        'overall_score': round(overall_score, 1),
        'breakdown': {
            'skills': {
                'score': round(skills_score, 1),
                'required_skills': job_required_skills,
                'found_skills': found_skills,
                'missing_skills': missing_skills,
                'coverage_percentage': round(coverage_pct, 1)
            },
            'experience': {
                'score': round(experience_score, 1),
                'display': experience_display,
                'is_valid': is_exp_valid
            },
            'projects': {
                'score': round(projects_score, 1)
            },
            'education': {
                'score': round(education_score, 1)
            }
        }
    }
