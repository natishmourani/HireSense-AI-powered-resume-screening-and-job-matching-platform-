<div align="center">

```
██╗  ██╗██╗██████╗ ███████╗███████╗███╗   ██╗███████╗███████╗
██║  ██║██║██╔══██╗██╔════╝██╔════╝████╗  ██║██╔════╝██╔════╝
███████║██║██████╔╝█████╗  ███████╗██╔██╗ ██║███████╗█████╗  
██╔══██║██║██╔══██╗██╔══╝  ╚════██║██║╚██╗██║╚════██║██╔══╝  
██║  ██║██║██║  ██║███████╗███████║██║ ╚████║███████║███████╗
╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝╚══════╝╚══════╝
```

### *Does your resume actually fit the job — or just look like it does?*

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Sentence Transformers](https://img.shields.io/badge/Sentence_Transformers-Embeddings-FF6B35?style=for-the-badge&logo=huggingface&logoColor=white)](https://sbert.net/)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70b-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

<br/>

> **HireSense** parses your resume, scores it against a job description using two AI embedding models,  
> and tells you *exactly* what's missing — with AI-generated feedback you can act on.

</div>

---

## 🧠 How the scoring actually works

Most resume tools give you a vague percentage and call it a day. HireSense breaks it down section by section, so you know *where* you're losing points.

```
Your Resume                          Job Description
    │                                      │
    ▼                                      ▼
┌─────────────┐                   ┌─────────────────┐
│   Parser    │  ←── pdfplumber   │  Requirements   │
│─────────────│                   │─────────────────│
│ ✦ Skills    │──── 40% weight ──▶│ Required Skills │
│ ✦ Experience│──── 25% weight ──▶│ Role Context    │
│ ✦ Projects  │──── 20% weight ──▶│ Tech Relevance  │
│ ✦ Education │──── 15% weight ──▶│ Degree / Field  │
└─────────────┘                   └─────────────────┘
        │                                  │
        └──────────────┬───────────────────┘
                       ▼
           ┌───────────────────────┐
           │   Embedding Engine    │
           │  all-MiniLM-L6-v2    │
           │  (Base vs Fine-Tuned) │
           └───────────────────────┘
                       │
                       ▼
           ┌───────────────────────┐
           │    Match Score  🎯    │
           │  + ATS Skill Gap      │
           │  + AI Feedback        │
           │  (Groq Llama 3.3)    │
           └───────────────────────┘
```

---

## ⚔️ Two Models Enter. You Decide Which Wins.

HireSense runs **both** models on your resume simultaneously and lets you compare results side by side — not just scores, but full evaluation metrics.

<div align="center">

|  | 🅰️ Base Model | 🅱️ Fine-Tuned Model |
|---|---|---|
| **Architecture** | `all-MiniLM-L6-v2` | `all-MiniLM-L6-v2` |
| **Training** | Pre-trained (HuggingFace) | Fine-tuned on 754 resume-job pairs |
| **Loss Function** | — | MultipleNegativesRankingLoss |
| **Precision** | ~15.6% | ~62.3% |
| **F1 Score** | 0.268 | **0.741** |
| **Verdict** | Baseline | 🏆 4× better |

</div>

> The fine-tuned model isn't just better in theory — it's been specifically trained to understand what makes a resume *actually relevant* to a job posting, not just semantically similar.

---

## ✨ Features

| 🔍 Feature | 💬 What it does |
|---|---|
| **PDF Resume Parser** | Extracts Skills, Experience, Projects, Education with strict section isolation — no content bleed |
| **ATS Skill Coverage** | Exact match + synonym taxonomy: `JS = JavaScript`, `Sklearn = Scikit-Learn`, and 50+ more |
| **Weighted Scoring** | Skills 40% · Experience 25% · Projects 20% · Education 15% |
| **Dual Model Comparison** | Base Model A vs Fine-Tuned Model B — scores, metrics, and charts |
| **AI Gap Analysis** | Groq Llama 3.3-70b generates: *What You Have · What's Missing · How to Improve* |
| **Offline Fallback** | Full rule-based feedback — works with zero API key |
| **Download Report** | Browser print-to-PDF of your full match assessment |

---

## 🗂️ Project Structure

```
HireSense/
│
├── 🧠 app/
│   ├── __init__.py           ← Flask app factory, routes, API endpoints
│   ├── parser.py             ← PDF text extraction + section parser
│   ├── matcher.py            ← Scoring engine (embeddings + weighted rules)
│   ├── groq_client.py        ← Groq Llama 3.3 feedback + rule-based fallback
│   ├── static/               ← CSS, JS, charts, metrics JSON
│   └── templates/            ← index.html, comparison.html
│
├── 📦 data/
│   ├── jobs.json             ← 51 job descriptions (8 roles, 3 seniority levels)
│   ├── train_dataset.json    ← 6,000 synthetic resume-job pairs
│   ├── eval_dataset.json     ← Evaluation set
│   └── uploads/              ← Temp PDF storage (auto-cleaned)
│
├── 🤖 models/
│   └── fine_tuned_model/     ← Fine-tuned SentenceTransformer weights
│       ├── model.safetensors
│       ├── config.json
│       └── tokenizer.json
│
├── 📓 notebooks/             ← Full ML training pipeline (offline)
│   ├── data_preprocessing.ipynb
│   ├── fine_tuning.ipynb
│   ├── base_model_evaluation.ipynb
│   ├── fine_tuned_model_evaluation.ipynb
│   └── model_comparison.ipynb
│
├── ⚙️ .env                   ← API keys (not committed)
├── 📋 requirements.txt
└── 🚀 run.py                 ← Entry point
```

---

## 🚀 Getting Started

### Prerequisites

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![pip](https://img.shields.io/badge/pip-required-3775A9?style=flat-square&logo=pypi&logoColor=white)](https://pip.pypa.io)

---

**1 — Clone**
```bash
git clone https://github.com/natishmourani/hiresense.git
cd hiresense
```

**2 — Install**
```bash
pip install -r requirements.txt
```

**3 — Configure** *(optional — app works without this)*
```bash
# Create .env in the project root
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
```
> 💡 No Groq key? The app automatically falls back to rule-based feedback — full functionality, offline.

**4 — Run**
```bash
python run.py
```
```
 * Running on http://localhost:5000
```

---

## 🎮 Usage Flow

```
1. Select a Job      →  51 descriptions across 8 roles & 3 seniority levels
        │
        ▼
2. Upload Resume     →  Drag & drop a text-based PDF
        │
        ▼
3. Analyze Match     →  Full pipeline runs in seconds
        │
        ▼
4. View Results      →  Toggle between Model A (Base) and Model B (Fine-Tuned)
        │
        ├──▶  📊  ATS Skill Gap          (exact + synonym matches)
        ├──▶  🤖  AI Feedback            (what to add, what to remove)
        ├──▶  📄  Parsed Sections        (see what the parser extracted)
        └──▶  📈  Model Comparison Page  (F1, Precision, Recall, MRR)
```

---

## 🏋️ Training Pipeline

The fine-tuned model was trained **offline** — not at runtime. Here's the full pipeline:

```
data_preprocessing.ipynb
  → Generate 200 synthetic resumes + 50 job descriptions
  → Create 6,000 labeled pairs (match / no-match)
          │
          ▼
fine_tuning.ipynb
  → Fine-tune all-MiniLM-L6-v2
  → Loss: MultipleNegativesRankingLoss
  → Epochs: 2  |  Training pairs: 754
  → Save to models/fine_tuned_model/
          │
          ▼
model_comparison.ipynb
  → Evaluate F1, Precision, Recall, MRR
  → Export → static/metrics_comparison.json
```

> **Why synthetic data?** Publicly available resume datasets don't include the labeled resume-job *match pairs* needed for contrastive fine-tuning. Synthetic generation from structured skill pools and role templates was a deliberate design choice — not a shortcut.

---

## 💼 Supported Job Roles

<div align="center">

`Machine Learning Engineer` · `Data Scientist` · `Backend Developer` · `Frontend Developer`  
`Software Engineer` · `DevOps Engineer` · `QA Engineer` · `Product Manager`

**51 job descriptions · 8 roles · 3 seniority levels (A / B / C)**

</div>

---

## ⚠️ Known Limitations

*Being honest about what it can't do is part of what makes it trustworthy.*

| ⚡ Limitation | 📉 Impact |
|---|---|
| Requires standard section headers | Non-standard headers like "Work History" or "Featured Work" score 0% for that section |
| Synonym taxonomy is manually curated | Uncommon skill aliases may be missed |
| Semantic similarity ≠ qualification | A verbose resume can outscore a concise one with identical skills |
| Synthetic training data | Real-world resume diversity may expose edge cases |
| Experience scoring uses text similarity | Does not numerically extract or verify years of experience |

---

## 🛠️ Tech Stack

<div align="center">

| Layer | Technology |
|---|---|
| 🖥️ Backend | Python · Flask |
| 📄 PDF Parsing | pdfplumber |
| 🧬 Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| 🤖 ML | scikit-learn · PyTorch |
| 💬 LLM Feedback | Groq API (`llama-3.3-70b-versatile`) |
| 🎨 Frontend | HTML · Bootstrap 5 · Vanilla JS |
| 📦 Data | JSON (jobs · training pairs · metrics) |

</div>

---

## 🎓 Academic Context

This project was built as part of a CS undergraduate curriculum at **Mohammad Ali Jinnah University (MAJU), Karachi**. It demonstrates:

- Sentence embedding models and contrastive fine-tuning
- PDF parsing and NLP preprocessing pipelines
- Hybrid scoring (rule-based + semantic similarity)
- Flask REST API design and frontend integration
- Model evaluation: F1, Precision, Recall, MRR

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for details.

---

<div align="center">

Built by **Natish Mourani**  
CS Undergraduate · Mohammad Ali Jinnah University, Karachi

[![GitHub](https://img.shields.io/badge/GitHub-natishmourani-181717?style=for-the-badge&logo=github)](https://github.com/natishmourani)

<br/>

*If your resume doesn't fit the job, HireSense will tell you why — and what to do about it.*

</div>
