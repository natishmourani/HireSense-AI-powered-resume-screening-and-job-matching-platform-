from werkzeug.datastructures import mixins
import os
import re
from groq import Groq

def parse_groq_output(text):
    sections = {
        'have': [],
        'missing': [],
        'improve': []
    }
    
    current_key = None
    lines = text.strip().split('\n')
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        lower_line = line_stripped.lower()
        if 'what you have' in lower_line:
            current_key = 'have'
            continue
        elif 'what you are missing' in lower_line or 'what you\'re missing' in lower_line:
            current_key = 'missing'
            continue
        elif 'how to improve' in lower_line:
            current_key = 'improve'
            continue
            
        # Extract bullet point
        if current_key and (line_stripped.startswith('*') or line_stripped.startswith('-') or line_stripped.startswith('•') or (line_stripped[0].isdigit() and line_stripped[1] == '.')):
            # Clean up prefix
            bullet = re.sub(r'^[-*•\d.]+\s*', '', line_stripped).strip()
            if bullet:
                sections[current_key].append(bullet)
        elif current_key and line_stripped:
            # If it's a line without bullet point, just append if it's text
            sections[current_key].append(line_stripped)
            
    return sections

def get_mock_explanation(resume_sections, job_description):
    """
    Local rule-based generator for when Groq API key is not set.
    Directly extracts matches/gaps strictly based on the inputs without hallucination.
    """
    skills_raw = resume_sections.get('SKILLS', '')
    # Handle both comma-separated and newline-separated (from PDF table extraction)

    skills_raw = resume_sections.get('SKILLS', '')
    if ',' in skills_raw:
        resume_skills_raw = skills_raw.split(',')
    else:
        resume_skills_raw = re.split(r'[\n\r]+', skills_raw)
    
    # Strip any "Label: " prefix (e.g. "Databases: PostgreSQL" → "PostgreSQL")
    cleaned = []
    for s in resume_skills_raw:
        # Split on newlines first to separate any merged tokens
        sub_tokens = re.split(r'[\n\r]+', s.strip())
        for token in sub_tokens:
            token = token.strip()
            # Strip label prefix like "Languages: " but only if it looks like a label
            if ':' in token:
                parts = token.split(':', 1)
                # Only strip if left side is a short label (1-3 words), not a skill itself
                if len(parts[0].strip().split()) <= 3:
                    token = parts[1].strip()
            if token:
                cleaned.append(token.lower())
    resume_skills = cleaned
        
    job_required_skills = job_description.get('required_skills', [])
    job_required_skills_lower = [s.lower() for s in job_required_skills]
    
    # Matching and missing skills (accounting for simple synonyms)
    have_skills = []
    missing_skills = []
    
    # Simple synonym mapping for mock
    from app.matcher import normalize_skill
    resume_skills_norm = [normalize_skill(s) for s in resume_skills]
    job_skills_norm = [normalize_skill(s) for s in job_required_skills]
    
    for orig, norm in zip(job_required_skills, job_skills_norm):
        if norm in resume_skills_norm:
            have_skills.append(orig)
        else:
            missing_skills.append(orig)
            
    # Compile "What You Have"
    have = []
    if have_skills:
        have.append(f"Matching core technical skills: {', '.join(have_skills)}.")
        
    is_exp_valid = resume_sections.get('EXPERIENCE_VALID', False)
    if is_exp_valid:
        have.append(f"Validated professional experience matching the keywords in the job role.")
        
    edu_text = resume_sections.get('EDUCATION', '').strip()
    if edu_text:
        # Extract degree
        degree_line = edu_text.split('\n')[0]
        have.append(f"Education background listed: '{degree_line}'.")
        

   # Compile "What You Are Missing"
    missing = []
    if missing_skills:
        missing.append(f"Required technical skills not mentioned: {', '.join(missing_skills)}.")
    # else:
    #     missing.append("No critical skill gaps detected — your resume covers all required technical skills for this role.")

    if not is_exp_valid:
        missing.append("A validated experience entry containing a job title, company name, and date range.")

    if not missing:
        missing.append("No significant gaps identified. The candidate's profile aligns well with the required skills and experience for this role.")

    # Compile "How To Improve"
    improve = []
    if missing_skills:
        improve.append(f"Add projects or experience bullet points demonstrating knowledge of: {', '.join(missing_skills)}.")
    if not is_exp_valid:
        improve.append("Format your experience section to clearly show the Job Title, Company/Organization Name, and Duration (e.g. Month Year - Month Year) for each position to pass ATS validation.")
    if not edu_text:
        improve.append("Include an Education section displaying your academic credentials and degree program.")

    # If nothing to improve at all
    if not improve:
        improve.append("Strong profile overall! Consider tailoring your project descriptions to more closely mirror the job's exact terminology for an even higher ATS score.")
        improve.append("Quantify achievements where possible (e.g. 'improved accuracy by 15%') to strengthen impact.")

    return {
        'have': have,
        'missing': missing,
        'improve': improve
    }

def get_groq_explanation(resume_sections, job_description):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return get_mock_explanation(resume_sections, job_description), False
        
    try:
        client = Groq(api_key=api_key)
        
        # Prepare context variables
        res_skills = resume_sections.get('SKILLS', 'Not provided')
        res_exp = resume_sections.get('EXPERIENCE', 'Not provided')
        res_proj = resume_sections.get('PROJECTS', 'Not provided')
        res_edu = resume_sections.get('EDUCATION', 'Not provided')
        
        job_role = job_description.get('role', 'Not provided')
        raw_title = job_description.get('title', 'Not provided')
        job_title = re.sub(r'\s*-\s*Category\s+[A-C]$', '', raw_title).strip()
        job_skills = ', '.join(job_description.get('required_skills', []))
        job_exp = job_description.get('experience_requirements', {}).get('description', 'Not provided')
        job_proj = job_description.get('project_requirements', {}).get('description', 'Not provided')
        job_edu = job_description.get('education_requirements', {}).get('description', 'Not provided')
        
        prompt = f"""
You are an expert career advisor and ATS system validator.
Compare the resume details against the job requirements and provide structured feedback.

--- RESUME SECTIONS ---
SKILLS:
{res_skills}

EXPERIENCE:
{res_exp}

PROJECTS:
{res_proj}

EDUCATION:
{res_edu}

--- JOB REQUIREMENTS ---
Role: {job_role} (Title: {job_title})
Required Skills: {job_skills}
Experience Requirement: {job_exp}
Project Requirement: {job_proj}
Education Requirement: {job_edu}

--- INSTRUCTIONS ---
You must generate structured feedback strictly under the three headings below. Do not include any conversational preamble or sign-off.
For each heading, output bullet points (starting with *).
Do not exaggerate any achievements or hallucinate candidate experience. Use only facts present in the resume.

STRICT RULES:
- Only list a skill as missing if it appears in Required Skills and is completely absent from the resume.
- Do not speculate about whether experience is "sufficient" or "considered sufficient" — if the resume states the experience, accept it.
- Do not suggest adding things that are already present in the resume.
- Do not invent concerns about edge cases or hypothetical disqualifiers.
- If all required skills are present, say so clearly and do not fabricate gaps.
- Category labels like "Category A", "Category B", "Category C" in the job title are internal labels — ignore them completely.

What You Have:
* List candidate's matching skills, matching projects, or verified education details.

What You Are Missing:
* Only list required skills or qualifications that are genuinely absent from the resume. If nothing is missing, say so.

How To Improve:
* Provide only actionable, specific advice based on real gaps. If the resume is a strong match, acknowledge it and suggest minor polish only. Do not suggest adding information that is already present anywhere in the resume text.
"""
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=800
        )
        
        response_text = completion.choices[0].message.content
        parsed = parse_groq_output(response_text)
        
        # Check if parsed correctly, if empty fallback
        if not parsed['have'] and not parsed['missing'] and not parsed['improve']:
            return get_mock_explanation(resume_sections, job_description), False
            
        return parsed, True
        
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return get_mock_explanation(resume_sections, job_description), False
