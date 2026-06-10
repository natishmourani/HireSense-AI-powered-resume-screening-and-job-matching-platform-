import json
import os

# Helper to write a notebook to notebooks/ folder
def save_nb(name, cells):
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    with open(f"notebooks/{name}", "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=2)
    print(f"Notebook {name} written successfully!")

# 1. embedding_generation.ipynb
cells_1 = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# TalentSync AI - Embedding Generation (Base Model)\n",
            "\n",
            "This notebook loads the baseline embedding model (`all-MiniLM-L6-v2`) and generates embeddings for the resumes and job descriptions."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import json\n",
            "import pickle\n",
            "import numpy as np\n",
            "from sentence_transformers import SentenceTransformer\n",
            "\n",
            "# Load model\n",
            "model = SentenceTransformer('all-MiniLM-L6-v2')\n",
            "print(\"Model loaded!\")"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Load eval dataset\n",
            "with open('../data/eval_dataset.json', 'r') as f:\n",
            "    eval_pairs = json.load(f)\n",
            "\n",
            "print(f\"Loaded {len(eval_pairs)} evaluation pairs.\")"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Extract jobs and resumes text\n",
            "jobs_text = [p['job'] for p in eval_pairs]\n",
            "resumes_text = [p['resume'] for p in eval_pairs]\n",
            "\n",
            "print(\"Generating embeddings (Base Model)...\")\n",
            "job_embeddings = model.encode(jobs_text, show_progress_bar=True)\n",
            "resume_embeddings = model.encode(resumes_text, show_progress_bar=True)\n",
            "\n",
            "# Save embeddings\n",
            "os.makedirs('../data', exist_ok=True)\n",
            "with open('../data/base_embeddings.pkl', 'wb') as f:\n",
            "    pickle.dump({\n",
            "        'job_embeddings': job_embeddings,\n",
            "        'resume_embeddings': resume_embeddings\n",
            "    }, f)\n",
            "print(\"Base embeddings saved!\")"
        ]
    }
]

# 2. base_model_evaluation.ipynb
cells_2 = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# TalentSync AI - Base Model Evaluation\n",
            "\n",
            "This notebook evaluates the baseline model's performance on the evaluation dataset using retrieval metrics."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import json\n",
            "import pickle\n",
            "import numpy as np\n",
            "from sklearn.metrics.pairwise import cosine_similarity\n",
            "\n",
            "# Load eval dataset\n",
            "with open('../data/eval_dataset.json', 'r') as f:\n",
            "    eval_pairs = json.load(f)\n",
            "\n",
            "# Load base embeddings\n",
            "with open('../data/base_embeddings.pkl', 'rb') as f:\n",
            "    embeddings = pickle.load(f)\n",
            "    \n",
            "job_embs = embeddings['job_embeddings']\n",
            "resume_embs = embeddings['resume_embeddings']"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Calculate cosine similarities\n",
            "similarities = []\n",
            "for i in range(len(eval_pairs)):\n",
            "    sim = cosine_similarity([job_embs[i]], [resume_embs[i]])[0][0]\n",
            "    similarities.append(float(sim))\n",
            "    \n",
            "labels = [p['label'] for p in eval_pairs]\n",
            "\n",
            "# Calculate ranking, Precision, Recall, F1, Top-K\n",
            "# We evaluate by treating each distinct job in the eval dataset as a query.\n",
            "# In eval dataset, there are 10 jobs and 50 resumes (total 500 pairs).\n",
            "# Let's reshape into query matrices.\n",
            "num_jobs = 10\n",
            "num_resumes = 50\n",
            "\n",
            "sim_matrix = np.array(similarities).reshape(num_jobs, num_resumes)\n",
            "label_matrix = np.array(labels).reshape(num_jobs, num_resumes)\n",
            "\n",
            "precisions = []\n",
            "recalls = []\n",
            "f1s = []\n",
            "mrr_list = []\n",
            "top5_hits = 0\n",
            "\n",
            "# Similarity threshold for classification (honest threshold)\n",
            "threshold = 0.45\n",
            "\n",
            "for i in range(num_jobs):\n",
            "    sims = sim_matrix[i]\n",
            "    lbls = label_matrix[i]\n",
            "    \n",
            "    # Sort indices by similarity descending\n",
            "    sorted_indices = np.argsort(sims)[::-1]\n",
            "    sorted_lbls = lbls[sorted_indices]\n",
            "    \n",
            "    # Classification metrics at threshold\n",
            "    preds = (sims >= threshold).astype(int)\n",
            "    tp = np.sum((preds == 1) & (lbls == 1))\n",
            "    fp = np.sum((preds == 1) & (lbls == 0))\n",
            "    fn = np.sum((preds == 0) & (lbls == 1))\n",
            "    \n",
            "    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0\n",
            "    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0\n",
            "    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0\n",
            "    \n",
            "    precisions.append(prec)\n",
            "    recalls.append(rec)\n",
            "    f1s.append(f1)\n",
            "    \n",
            "    # Top-K hit rate (Top-5)\n",
            "    if np.sum(sorted_lbls[:5]) > 0:\n",
            "        top5_hits += 1\n",
            "        \n",
            "    # MRR (Mean Reciprocal Rank)\n",
            "    ranks = np.where(sorted_lbls == 1)[0]\n",
            "    if len(ranks) > 0:\n",
            "        mrr_list.append(1.0 / (ranks[0] + 1))\n",
            "    else:\n",
            "        mrr_list.append(0.0)\n",
            "\n",
            "metrics = {\n",
            "    \"Precision\": float(np.mean(precisions)),\n",
            "    \"Recall\": float(np.mean(recalls)),\n",
            "    \"F1 Score\": float(np.mean(f1s)),\n",
            "    \"Top-K Accuracy\": float(top5_hits / num_jobs),\n",
            "    \"Mean Similarity Score\": float(np.mean(sim_matrix[label_matrix == 1])),\n",
            "    \"Ranking Accuracy (MRR)\": float(np.mean(mrr_list))\n}\n",
            "\n",
            "print(\"Base Model Metrics:\")\n",
            "print(json.dumps(metrics, indent=2))\n",
            "\n",
            "with open('../data/base_metrics.json', 'w') as f:\n",
            "    json.dump(metrics, f, indent=2)"
        ]
    }
]

# 3. fine_tuning.ipynb
cells_3 = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# TalentSync AI - Model Fine-Tuning\n",
            "\n",
            "This notebook loads the training dataset, wraps the resume-job pairs into `InputExample` objects, and fine-tunes the `all-MiniLM-L6-v2` embedding model using `MultipleNegativesRankingLoss` to capture technical alignment and domain specific matching."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import json\n",
            "from sentence_transformers import SentenceTransformer, InputExample, losses\n",
            "from torch.utils.data import DataLoader\n",
            "\n",
            "# Load model\n",
            "model = SentenceTransformer('all-MiniLM-L6-v2')\n",
            "print(\"Base model loaded!\")"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Load train dataset\n",
            "with open('../data/train_dataset.json', 'r') as f:\n",
            "    train_data = json.load(f)\n",
            "\n",
            "print(f\"Loaded {len(train_data)} training items.\")"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Sentence Transformers fine-tuning setup\n",
            "# We filter only positive examples (label=1.0) because MultipleNegativesRankingLoss trains\n",
            "# on pairs of (anchor, positive) and uses other items in the batch as implicit negatives.\n",
            "train_examples = []\n",
            "for item in train_data:\n",
            "    if item['label'] == 1.0:\n",
            "        train_examples.append(InputExample(texts=[item['job'], item['resume']]))\n",
            "\n",
            "print(f\"Prepared {len(train_examples)} positive pair examples for MultipleNegativesRankingLoss.\")"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# PyTorch DataLoader\n",
            "train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)\n",
            "train_loss = losses.MultipleNegativesRankingLoss(model)\n",
            "\n",
            "# Tune parameters for fast/clean CPU execution\n",
            "epochs = 2\n",
            "warmup_steps = int(len(train_dataloader) * epochs * 0.1)\n",
            "\n",
            "print(f\"Starting fine-tuning for {epochs} epochs...\")\n",
            "model.fit(\n",
            "    train_objectives=[(train_dataloader, train_loss)],\n",
            "    epochs=epochs,\n",
            "    warmup_steps=warmup_steps,\n",
            "    show_progress_bar=True\n",
            ")\n",
            "\n",
            "# Save fine-tuned model\n",
            "model.save('../models/fine_tuned_model')\n",
            "print(\"Fine-tuned model saved successfully to ../models/fine_tuned_model!\")"
        ]
    }
]

# 4. fine_tuned_model_evaluation.ipynb
cells_4 = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# TalentSync AI - Fine-Tuned Model Evaluation\n",
            "\n",
            "This notebook evaluates the performance of the newly fine-tuned embedding model."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import json\n",
            "import numpy as np\n",
            "from sentence_transformers import SentenceTransformer\n",
            "from sklearn.metrics.pairwise import cosine_similarity\n",
            "\n",
            "# Load fine-tuned model\n",
            "model = SentenceTransformer('../models/fine_tuned_model')\n",
            "print(\"Fine-tuned model loaded!\")"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Load eval dataset\n",
            "with open('../data/eval_dataset.json', 'r') as f:\n",
            "    eval_pairs = json.load(f)\n",
            "\n",
            "jobs_text = [p['job'] for p in eval_pairs]\n",
            "resumes_text = [p['resume'] for p in eval_pairs]\n",
            "labels = [p['label'] for p in eval_pairs]\n",
            "\n",
            "# Generate Embeddings\n",
            "print(\"Generating embeddings (Fine-Tuned model)...\")\n",
            "job_embs = model.encode(jobs_text, show_progress_bar=True)\n",
            "resume_embs = model.encode(resumes_text, show_progress_bar=True)"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Calculate similarities\n",
            "similarities = []\n",
            "for i in range(len(eval_pairs)):\n",
            "    sim = cosine_similarity([job_embs[i]], [resume_embs[i]])[0][0]\n",
            "    similarities.append(float(sim))\n",
            "\n",
            "num_jobs = 10\n",
            "num_resumes = 50\n",
            "\n",
            "sim_matrix = np.array(similarities).reshape(num_jobs, num_resumes)\n",
            "label_matrix = np.array(labels).reshape(num_jobs, num_resumes)\n",
            "\n",
            "precisions = []\n",
            "recalls = []\n",
            "f1s = []\n",
            "mrr_list = []\n",
            "top5_hits = 0\n",
            "threshold = 0.45\n",
            "\n",
            "for i in range(num_jobs):\n",
            "    sims = sim_matrix[i]\n",
            "    lbls = label_matrix[i]\n",
            "    \n",
            "    sorted_indices = np.argsort(sims)[::-1]\n",
            "    sorted_lbls = lbls[sorted_indices]\n",
            "    \n",
            "    preds = (sims >= threshold).astype(int)\n",
            "    tp = np.sum((preds == 1) & (lbls == 1))\n",
            "    fp = np.sum((preds == 1) & (lbls == 0))\n",
            "    fn = np.sum((preds == 0) & (lbls == 1))\n",
            "    \n",
            "    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0\n",
            "    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0\n",
            "    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0\n",
            "    \n",
            "    precisions.append(prec)\n",
            "    recalls.append(rec)\n",
            "    f1s.append(f1)\n",
            "    \n",
            "    if np.sum(sorted_lbls[:5]) > 0:\n",
            "        top5_hits += 1\n",
            "        \n",
            "    ranks = np.where(sorted_lbls == 1)[0]\n",
            "    if len(ranks) > 0:\n",
            "        mrr_list.append(1.0 / (ranks[0] + 1))\n",
            "    else:\n",
            "        mrr_list.append(0.0)\n",
            "\n",
            "metrics = {\n",
            "    \"Precision\": float(np.mean(precisions)),\n",
            "    \"Recall\": float(np.mean(recalls)),\n",
            "    \"F1 Score\": float(np.mean(f1s)),\n",
            "    \"Top-K Accuracy\": float(top5_hits / num_jobs),\n",
            "    \"Mean Similarity Score\": float(np.mean(sim_matrix[label_matrix == 1])),\n",
            "    \"Ranking Accuracy (MRR)\": float(np.mean(mrr_list))\n}\n",
            "\n",
            "print(\"Fine-Tuned Model Metrics:\")\n",
            "print(json.dumps(metrics, indent=2))\n",
            "\n",
            "with open('../data/fine_tuned_metrics.json', 'w') as f:\n",
            "    json.dump(metrics, f, indent=2)"
        ]
    }
]

# 5. model_comparison.ipynb
cells_5 = [
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# TalentSync AI - Model Comparison & Analytics\n",
            "\n",
            "This notebook compares Model A (Base Model) vs Model B (Fine-Tuned Model) across all metrics and exports visualizations and results for the dashboard."
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import os\n",
            "import json\n",
            "import pandas as pd\n",
            "import matplotlib.pyplot as plt\n",
            "import seaborn as sns\n",
            "\n",
            "# Load metrics\n",
            "with open('../data/base_metrics.json', 'r') as f:\n",
            "    base_metrics = json.load(f)\n",
            "\n",
            "with open('../data/fine_tuned_metrics.json', 'r') as f:\n",
            "    tuned_metrics = json.load(f)\n",
            "\n",
            "print(\"Base Metrics Loaded:\", base_metrics)\n",
            "print(\"Tuned Metrics Loaded:\", tuned_metrics)"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Build Comparison DataFrame\n",
            "data = {\n",
            "    'Metric': list(base_metrics.keys()),\n",
            "    'Base Model (Model A)': list(base_metrics.values()),\n",
            "    'Fine-Tuned Model (Model B)': list(tuned_metrics.values())\n",
            "}\n",
            "df = pd.DataFrame(data)\n",
            "df['Improvement'] = df['Fine-Tuned Model (Model B)'] - df['Base Model (Model A)']\n",
            "\n",
            "print(\"--- Model Comparison Table ---\")\n",
            "print(df.to_string(index=False))\n",
            "\n",
            "# Save comparison metrics for the dashboard\n",
            "comparison_metrics = []\n",
            "for key in base_metrics.keys():\n",
            "    comparison_metrics.append({\n",
            "        \"metric\": key,\n",
            "        \"base\": base_metrics[key],\n",
            "        \"tuned\": tuned_metrics[key],\n",
            "        \"improvement\": tuned_metrics[key] - base_metrics[key]\n",
            "    })\n",
            "\n",
            "os.makedirs('../app/static', exist_ok=True)\n",
            "with open('../app/static/metrics_comparison.json', 'w') as f:\n",
            "    json.dump(comparison_metrics, f, indent=2)\n",
            "print(\"metrics_comparison.json written for dashboard!\")"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# Create Comparison Bar Charts\n",
            "df_melted = pd.melt(df, id_vars=['Metric'], value_vars=['Base Model (Model A)', 'Fine-Tuned Model (Model B)'], var_name='Model', value_name='Score')\n",
            "\n",
            "plt.figure(figsize=(12, 6))\n",
            "sns.set_theme(style=\"whitegrid\")\n",
            "sns.barplot(data=df_melted, x='Metric', y='Score', hue='Model', palette='muted')\n",
            "plt.title('TalentSync AI: Embedding Model Performance Comparison', fontsize=14, pad=15)\n",
            "plt.xticks(rotation=15)\n",
            "plt.ylim(0, 1.1)\n",
            "plt.ylabel('Value')\n",
            "plt.legend(loc='lower right')\n",
            "plt.tight_layout()\n",
            "\n",
            "os.makedirs('../app/static/charts', exist_ok=True)\n",
            "plt.savefig('../app/static/charts/model_comparison.png', dpi=300)\n",
            "plt.show()\n",
            "print(\"model_comparison.png saved!\")"
        ]
    }
]

# Write all notebooks
save_nb("embedding_generation.ipynb", cells_1)
save_nb("base_model_evaluation.ipynb", cells_2)
save_nb("fine_tuning.ipynb", cells_3)
save_nb("fine_tuned_model_evaluation.ipynb", cells_4)
save_nb("model_comparison.ipynb", cells_5)
print("All notebooks created successfully!")
