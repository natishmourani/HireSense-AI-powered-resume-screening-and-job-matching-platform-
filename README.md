# HireSense — AI-Powered Resume & Job Matching Platform

> Evaluate resume alignment, analyze skill gaps, and explore deep-learning matching models — honestly.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-black?style=flat-square&logo=flask)
![Sentence Transformers](https://img.shields.io/badge/SentenceTransformers-2.x-orange?style=flat-square)
![Groq](https://img.shields.io/badge/Groq-Llama3-green?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)

---

## What is HireSense?

HireSense answers one question: **"How well does this resume fit this job?"**

It parses a PDF resume into structured sections, scores it against a job description using two AI embedding models, and generates explainable feedback — either via Groq's Llama 3 or a local rule-based fallback.

---

## Features

- **PDF Resume Parser** — extracts Skills, Experience, Projects, and Education sections with section isolation
- **Dual Model Scoring** — compares Base Model (all-MiniLM-L6-v2) vs Fine-Tuned Model side by side
- **ATS Skill Coverage** — exact match + synonym taxonomy (JS = JavaScript, Sklearn = Scikit-Learn, etc.)
- **Weighted Scoring** — Skills 40% · Experience 25% · Projects 20% · Education 15%
- **AI Feedback** — Groq Llama 3.3 generates "What You Have / Missing / How to Improve"
- **Rule-Based Fallback** — works fully offline without a Groq API key
- **Model Comparison Page** — F1, Precision, Recall, MRR metrics with charts
- **Download Report** — browser print-to-PDF of the full match assessment

---

## Project Structure

```
HireSense/
│
├── app/                         # Flask application
│   ├── __init__.py              # App factory, routes, API endpoints
│   ├── parser.py                # PDF text extraction & section parser
│   ├── matcher.py               # Scoring engine (embeddings + rules)
│   ├── groq_client.py           # Groq LLM feedback + rule-based fallback
│   ├── static/                  # CSS, JS, charts, metrics JSON
│   └── templates/               # index.html, comparison.html
│
├── data/
│   ├── jobs.json                # 51 job descriptions (8 roles, 3 categories)
│   ├── train_dataset.json       # 6000 synthetic resume-job pairs
│   ├── eval_dataset.json        # Evaluation pairs
│   └── uploads/                 # Temporary PDF uploads (auto-cleaned)
│
├── models/
│   └── fine_tuned_model/        # Fine-tuned SentenceTransformer
│       ├── model.safetensors
│       ├── config.json
│       ├── tokenizer.json
│       └── ...
│
├── notebooks/                   # ML pipeline (offline training)
│   ├── data_preprocessing.ipynb       # Synthetic resume + job generation
│   ├── embedding_generation.ipynb     # Embedding pre-computation
│   ├── fine_tuning.ipynb              # Model fine-tuning pipeline
│   ├── resume_parser.ipynb            # Parser development & testing
│   ├── base_model_evaluation.ipynb    # Base model metrics
│   ├── fine_tuned_model_evaluation.ipynb
│   └── model_comparison.ipynb         # Side-by-side evaluation
│
├── .env                         # Environment variables (not committed)
├── .gitignore
├── requirements.txt
└── run.py                       # App entry point
```

---

## How It Works

### 1. Resume Parsing (`parser.py`)
- Extracts raw text from PDF using `pdfplumber`
- Detects section headers via regex (Skills, Experience, Projects, Education)
- Enforces **Critical Section Isolation** — prevents content bleed between sections
- Validates Experience entries: must contain job role + company name + date range
- Rejects scanned/image-only PDFs with a user-friendly error

### 2. Match Scoring (`matcher.py`)

| Category | Weight | Method |
|---|---|---|
| Skills | 40% | 60% keyword coverage + 40% embedding similarity |
| Experience | 25% | Cosine similarity between experience text and job description |
| Projects | 20% | 70% semantic similarity + 30% keyword overlap |
| Education | 15% | 50% embedding similarity + 50% rule-based degree/field matching |

### 3. Two Models

| | Base Model A | Fine-Tuned Model B |
|---|---|---|
| Architecture | all-MiniLM-L6-v2 | all-MiniLM-L6-v2 (fine-tuned) |
| Training | Pre-trained (HuggingFace) | Fine-tuned on 754 resume-job pairs |
| Loss Function | — | MultipleNegativesRankingLoss |
| Precision | ~15.6% | ~62.3% |
| F1 Score | 0.268 | 0.741 |

### 4. AI Feedback (`groq_client.py`)
- Sends parsed resume sections + job requirements to **Groq Llama 3.3-70b**
- Returns structured bullets under: What You Have · What You Are Missing · How To Improve
- Falls back to local rule-based explanation if API key is missing or call fails

---

## Setup & Installation

### Prerequisites
- Python 3.10+
- pip

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/hiresense.git
cd hiresense
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_groq_api_key_here
```
> The app works without a Groq API key — it falls back to rule-based feedback automatically.

### 4. Run the app
```bash
python run.py
```

Visit `http://localhost:5000` in your browser.

---

## Usage

1. **Select a Job** — choose from 51 available job descriptions across 8 roles
2. **Upload Resume** — drag & drop or browse for a text-based PDF
3. **Analyze Match** — click "Analyze Match" to run the full pipeline
4. **View Results** — toggle between Base Model A and Fine-Tuned Model B
5. **Explore Tabs** — ATS Skill Gap · AI Feedback · Parsed Sections
6. **Compare Models** — visit the Model Comparison page for evaluation metrics

---

## Training Pipeline (Offline)

The fine-tuned model was trained offline using Jupyter notebooks — not at runtime.

```
data_preprocessing.ipynb     →  Generate 200 synthetic resumes + 50 jobs
                             →  Create 6000 labeled pairs (match / no-match)
                             ↓
fine_tuning.ipynb            →  Fine-tune all-MiniLM-L6-v2
                             →  MultipleNegativesRankingLoss, 2 epochs
                             →  Save to models/fine_tuned_model/
                             ↓
model_comparison.ipynb       →  Evaluate F1, Precision, Recall, MRR
                             →  Export metrics to static/metrics_comparison.json
```

> **Note:** Training data is synthetic — generated from structured skill pools and role templates. This is a deliberate design choice: publicly available resume datasets do not include labeled resume-job match pairs required for contrastive fine-tuning.

---

## Known Limitations

| Limitation | Impact |
|---|---|
| Parser requires standard section headers | Non-standard headers (e.g. "Work History", "Featured Work") score 0% for those sections |
| Synonym taxonomy is manually curated | Uncommon skill aliases may not be recognized |
| Semantic similarity ≠ qualification | A verbose resume matches better than a concise one with identical skills |
| Synthetic training data | Model performance on real-world resume diversity may vary |
| Experience scoring uses text similarity | Does not extract or verify actual years of experience numerically |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| PDF Parsing | pdfplumber |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| ML | scikit-learn, PyTorch |
| LLM Feedback | Groq API (Llama 3.3-70b-versatile) |
| Frontend | HTML, Bootstrap 5, Vanilla JS |
| Data | JSON (jobs, training pairs, metrics) |

---

## Available Job Roles

HireSense includes 51 job descriptions across 8 roles and 3 seniority categories (A/B/C):

- Machine Learning Engineer
- Data Scientist
- Backend Developer
- Frontend Developer
- Software Engineer
- DevOps Engineer
- QA Engineer
- Product Manager

---

## Academic Context

This project was developed as part of a Computer Science undergraduate curriculum at **Mohammad Ali Jinnah University (MAJU), Karachi**. It demonstrates applied machine learning concepts including:

- Sentence embedding models and fine-tuning with contrastive loss
- PDF parsing and NLP preprocessing pipelines
- Hybrid scoring systems (rule-based + semantic)
- Flask REST API design and frontend integration
- Model evaluation metrics (F1, Precision, Recall, MRR)

---

## License

This project is licensed under the MIT License.

---

*Built by Natish — CS Undergraduate, MAJU Karachi*
