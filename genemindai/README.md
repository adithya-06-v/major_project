# GeneMindAI: Experimental HBB Multi-Disease Sequence Classifier

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141.1-009688.svg)](https://fastapi.tiangolo.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.7.2-orange.svg)](https://scikit-learn.org/)
[![SHAP](https://img.shields.io/badge/SHAP-0.49.1-blueviolet.svg)](https://shap.readthedocs.io/)

---

## 1. Project Overview

**GeneMindAI** is an experimental DNA sequence analysis and bioinformatics platform focused on the Human Hemoglobin Subunit Beta (*HBB*) gene. The existing baseline model distinguishes Healthy from Beta Thalassemia. An opt-in experimental five-class test model is configured for Healthy, Beta Thalassemia, Sickle Cell Disease, Hemoglobin E Disease, and Hemoglobin C Disease. Its Healthy controls and disease examples are synthetic software-test fixtures, not patient data or clinically validated datasets. No model output is a medical diagnosis.

---

## 2. Features

- **DNA Validation**: Strict IUPAC nucleotide rule verification using regex pattern matching (`A`, `T`, `C`, `G`, `N`), enforcing non-empty and non-whitespace sequence criteria.
- **HBB Gene Processing**: Automated extraction of the annotated *HBB* RefSeqGene locus region (`NG_000007.3`) from NCBI GenBank annotations.
- **Mutation Simulation**: In-memory single-nucleotide substitution, insertion, and deletion editing engine (`DNAMutationEngine`) operating on 1-based coordinates.
- **Mutation Library**: Structured clinical catalog (`MutationLibrary`) of documented pathogenic Beta Thalassemia variants (e.g., HbS, Codon 39 Nonsense, IVS-I-1, IVS-I-110, Codon 8/9 insertion, Codon 41/42 deletion).
- **Dataset Generation**: Automated pipeline for synthesizing healthy and mutated FASTA variants into a structured master dataset (`dataset.csv`).
- **K-mer Feature Extraction**: Normalized frequency vector transformation (`KMerEncoder`) converting DNA sequences into overlapping k-mer counts ($k=3$) with guaranteed feature column alignment (`feature_columns.json`).
- **Machine Learning**: Baseline ensemble classification models (`LogisticRegression` and `RandomForestClassifier`) serialized using `joblib`.
- **SHAP Explainability**: TreeExplainer feature attribution producing high-resolution summary beeswarm (`shap_summary.png`) and global feature importance bar charts (`shap_bar.png`).
- **REST API**: Production-grade `FastAPI` service featuring asynchronous endpoints, request validation, lifespan singleton model loading, and HTTP 400 error handling.
- **Swagger Documentation**: Interactive OpenAPI/Swagger documentation available out-of-the-box at `/docs`.
- **Experimental Multi-Disease Test Model**: Optional Random Forest training from the disease-specific sequence CSVs in `dataset/diseases/`.

### Train the experimental multi-disease model

The disease sample CSVs and Healthy controls are marked or treated as `synthetic_test`. Training requires explicitly opting in and writes a separate model under `ai/models/multidisease/`; restart the backend after training so it can load the new model.

```powershell
python scripts/train_multidisease_model.py --allow-synthetic-test-data
```

This model only demonstrates the multi-class software flow. Its predictions and metrics do not establish real disease detection. Replace the test fixtures with properly curated and independently validated variant data before interpreting outputs.

---

## 3. Technology Stack

- **Frontend**: HTML5, Vanilla CSS3, Modern JavaScript (ES6+), React/Vite dashboard.
- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2, Starlette, HTTPX.
- **Machine Learning**: Scikit-Learn, XGBoost, SHAP (SHapley Additive exPlanations), Joblib, NumPy, Pandas.
- **Bioinformatics**: Biopython (`Bio.SeqIO`, `Bio.Entrez`, `Bio.SeqRecord`), Custom DNA Validator & Mutation Engine.
- **Database**: File-based FASTA / GenBank / CSV dataset storage (Relational SQL/PostgreSQL optional for enterprise scale).

---

## 4. Project Structure

```text
genemindAi/
│
├── ai/                              # AI & Machine Learning Subsystem
│   ├── explainability/              # SHAP interpretability module
│   │   ├── __init__.py
│   │   └── shap_explainer.py        # Generates summary & bar feature importance plots
│   ├── models/                      # Serialized ML artifacts & feature schemas
│   │   ├── __init__.py
│   │   ├── feature_columns.json     # Ordered list of training feature names (63 k-mers)
│   │   ├── logistic_regression.pkl  # Trained Logistic Regression model
│   │   └── random_forest.pkl        # Trained Random Forest Classifier model
│   └── training/                    # Model training & cross-validation pipelines
│       ├── __init__.py
│       └── train_baseline_models.py # Data splitting, training, and evaluation script
│
├── backend/                         # FastAPI REST Application Server
│   ├── __init__.py
│   ├── main.py                      # FastAPI application factory, lifespan & routes
│   ├── schemas.py                   # Pydantic request/response schemas
│   └── services/                    # Domain logic & inference handlers
│       ├── __init__.py
│       └── predictor.py             # Predictor service with guaranteed feature ordering
│
├── dataset/                         # Genomic Sequences & Data Matrices
│   ├── healthy/                     # Reference healthy sequence (hbb_gene.fasta)
│   ├── mutated/                     # Simulated mutated FASTA variants
│   ├── processed/                   # Processed datasets (dataset.csv, feature_dataset.csv)
│   └── raw/                         # NCBI GenBank & RefSeq downloads (hbb_reference.gb)
│
├── dna_processing/                  # Bioinformatics Engine
│   ├── feature_extraction/          # K-mer frequency encoder (kmer_encoder.py)
│   ├── mutation/                    # Mutation engine & catalog (mutation_engine.py, mutation_library.py)
│   ├── parsers/                     # Biopython FASTA parser (fasta_parser.py)
│   ├── preprocessing/               # Sequence statistics & GC-content tools
│   └── validation/                  # IUPAC DNA validator (dna_validator.py)
│
├── frontend/                        # Web Dashboard UI App
│
├── reports/                         # Generated SHAP Plots & Diagnostic Reports
│   ├── shap_bar.png                 # Global feature importance bar chart
│   └── shap_summary.png             # Summary beeswarm feature attribution plot
│
├── scripts/                         # CLI Automation & Pipeline Scripts
│   ├── download_hbb_genbank.py      # Fetches RefSeqGene NG_000007.3 from NCBI
│   ├── extract_gene.py              # Slices HBB gene region into FASTA
│   ├── generate_dataset.py          # Builds dataset.csv with healthy & mutated samples
│   └── test_mutation_engine.py      # Test suite for DNAMutationEngine
│
├── tests/                           # Pytest Automation Test Suite
│   ├── __init__.py
│   └── test_api.py                  # API integration & edge case test suite
│
├── requirements.txt                 # Python dependencies manifest
├── README.md                        # Technical documentation
└── LICENSE                          # Open-source MIT license
```

---

## 5. Installation & Setup

### 1. Prerequisites
- Python 3.10 or higher
- Git

### 2. Clone the Repository & Setup Virtual Environment

#### On macOS / Linux:
```bash
git clone https://github.com/your-username/genemindAi.git
cd genemindAi
python3 -m venv .venv
source .venv/bin/activate
```

#### On Windows (PowerShell):
```powershell
git clone https://github.com/your-username/genemindAi.git
cd genemindAi
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Curated HBB Dataset
To build a reproducible dataset from ClinVar-reviewed HBB variants, run this from the repository root:
```bash
python scripts/build_clinvar_dataset.py
```
The builder includes multi-submitter/no-conflict and expert-panel records, uses beta-thalassemia-specific pathogenic classifications, excludes sickle-associated positives and uncertain variants, and validates each SNV against the local GRCh38 HBB reference. It writes raw sequences and k-mer features under `dataset/processed/`; `dataset_split` holds out entire genomic positions as a challenge set. These records are for research and education, not clinical diagnosis.

To train and evaluate a separate candidate model on the curated feature dataset without overwriting the model currently used by the API:
```bash
python ai/training/train_baseline_models.py --dataset dataset/processed/clinvar_hbb_feature_dataset.csv --model-dir ai/models/clinvar_candidate
```
The trainer uses the position-held-out challenge partition and grouped cross-validation for this dataset.

### 4. Running the Backend Server
Start the FastAPI server using Uvicorn:
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
The server will start at `http://127.0.0.1:8000`. Access interactive API docs (Swagger UI) at `http://127.0.0.1:8000/docs`.

### 5. Running the Frontend (Future Phases)
```bash
cd frontend
npm install
npm run dev
```

---

## 6. API Documentation

### Health Check Endpoint
- **URL**: `GET /`
- **Description**: Verifies API availability.
- **Response**: `200 OK`
  ```json
  {
      "message": "GeneMindAI API Running"
  }
  ```

---

### Sequence Prediction Endpoint
- **URL**: `POST /predict`
- **Description**: Validates a raw DNA sequence, computes k-mer frequencies, and returns prediction label with confidence score.

#### Request Example
```json
{
    "sequence": "ACATTTGCTTCTGACACAACTGTGTTCACTAGCAACCTCAAACAGACACCATGGTGCAT"
}
```

#### Response Example (`200 OK`)
```json
{
    "prediction": "Mutated (Beta Thalassemia)",
    "confidence": 0.7100
}
```

#### Error Response Example (`400 Bad Request` - Invalid DNA)
```json
{
    "detail": "Invalid DNA sequence: Sequence contains invalid characters: '1', '2', '3'. Only A, T, C, G, and N are allowed."
}
```

#### Error Response Example (`400 Bad Request` - Empty String)
```json
{
    "detail": "Invalid DNA sequence: Sequence is empty; provide at least one nucleotide."
}
```

---

## 7. Workflow Architecture

```text
┌───────────────────────────────────────────────────────────┐
│                    1. DNA Upload                          │
│     Raw nucleotide sequence string (CLI / REST API)       │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│                    2. DNA Validation                      │
│   DNAValidator checks IUPAC rules & non-empty criteria    │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│                 3. Feature Extraction                     │
│   KMerEncoder (k=3) computes normalized frequencies       │
│   Aligned with saved feature_columns.json (63 features)   │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│                    4. AI Prediction                       │
│   Random Forest Classifier computes class & confidence    │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│                  5. XAI Explainability                    │
│   SHAP TreeExplainer outputs feature impact & bar plots   │
└─────────────────────────────┬─────────────────────────────┘
```

---

## 8. Future Improvements

- **Deep Learning Architectures**: Integrate 1D CNNs, Recurrent Neural Networks (LSTMs), and Genomic Transformer models for raw sequence token classification.
- **Expanded Pathogenic Mutation Library**: Broaden mutation coverage to include Alpha Thalassemia (*HBA1*/*HBA2*), Sickle Cell Disease variants, and Sickle-Beta interaction alleles.
- **Relational & Vector Database Storage**: Integrate PostgreSQL with pgvector / Cloud Firestore for persistent patient sequence registry and fast vector search.
- **Full React Dashboard**: Complete interactive UI with real-time sequence alignment heatmaps, mutation diff viewers, and downloadable PDF diagnostic reports.

---

## 9. Contributors

- **Deekshith** - Lead Bioinformatics & Machine Learning Engineer

---

## 10. License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for complete details.
