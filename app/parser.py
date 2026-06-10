import re
import pdfplumber

# Header regex dictionary
HEADERS_REGEX = {
    'SKILLS': re.compile(r'^\s*[-*•]?\s*(skills|technical\s+skills|core\s+skills)\s*:?\s*$', re.IGNORECASE | re.MULTILINE),
    'EXPERIENCE': re.compile(r'^\s*[-*•]?\s*(experience|work\s+experience|professional\s+experience|internships)\s*:?\s*$', re.IGNORECASE | re.MULTILINE),
    'PROJECTS': re.compile(r'^\s*[-*•]?\s*(projects|key\s+projects|academic\s+projects|personal\s+projects|notable\s+projects)\s*:?\s*$', re.IGNORECASE | re.MULTILINE),
    'EDUCATION': re.compile(r'^\s*[-*•]?\s*(education|academic\s+background)\s*:?\s*$', re.IGNORECASE | re.MULTILINE)
}

IGNORE_REGEX = {
    'IGNORE': re.compile(r'^\s*[-*•]?\s*(summary|profile|professional\s+summary|career\s+objective|objective|contact|certifications|certificates|references|publications|awards|achievements|honors|languages|hobbies|interests)\s*:?\s*$', re.IGNORECASE | re.MULTILINE)
}

def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return None

def validate_experience_entry(entry_text):
    role_pattern = re.compile(r'(engineer|developer|scientist|manager|intern|analyst|programmer|lead|specialist|architect|coordinator|designer)', re.IGNORECASE)
    company_pattern = re.compile(r'(google|microsoft|meta|amazon|netflix|apple|stripe|uber|airbnb|salesforce|atlassian|slack|technologies|solutions|labs|corp|inc|llc|co\b|global|tech|group|systems|enterprise|ventures)', re.IGNORECASE)
    duration_pattern = re.compile(r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4}\s*(?:-|–|—|to)\s*(?:present|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4})|\d{4}\s*(?:-|–|—|to)\s*(?:\d{4}|present))', re.IGNORECASE)

    has_role = bool(role_pattern.search(entry_text))
    has_company = bool(company_pattern.search(entry_text))
    has_duration = bool(duration_pattern.search(entry_text))

    return has_role and has_company and has_duration

def parse_resume(pdf_path):
    text = extract_text_from_pdf(pdf_path)

    if not text or len(text.strip()) < 100:
        return {
            "success": False,
            "error": "Scanned or image-only PDF detected. Please upload a text-based PDF resume."
        }

    matches = []
    # Match standard sections
    for section, regex in HEADERS_REGEX.items():
        for m in regex.finditer(text):
            matches.append({
                'section': section,
                'start': m.start(),
                'end': m.end(),
                'line': m.group(0)
            })

    # Match ignored sections to prevent contamination
    for section, regex in IGNORE_REGEX.items():
        for m in regex.finditer(text):
            matches.append({
                'section': section,
                'start': m.start(),
                'end': m.end(),
                'line': m.group(0)
            })

    matches = sorted(matches, key=lambda x: x['start'])

    parsed_sections = {
        'SKILLS': '',
        'EXPERIENCE': '',
        'PROJECTS': '',
        'EDUCATION': ''
    }

    for i, m in enumerate(matches):
        if m['section'] == 'IGNORE':
            continue
        start_idx = m['end']
        end_idx = matches[i+1]['start'] if i + 1 < len(matches) else len(text)

        section_text = text[start_idx:end_idx].strip()
        if parsed_sections[m['section']]:
            parsed_sections[m['section']] += "\n" + section_text
        else:
            parsed_sections[m['section']] = section_text

    exp_text = parsed_sections['EXPERIENCE'].strip()
    is_exp_valid = False
    if exp_text:
        entries = [e.strip() for e in exp_text.split('\n\n') if e.strip()]
        for entry in entries:
            if validate_experience_entry(entry):
                is_exp_valid = True
                break

    parsed_sections['EXPERIENCE_VALID'] = is_exp_valid

    return {
        "success": True,
        "data": parsed_sections
    }