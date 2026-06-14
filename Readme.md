# 🔮 Contentstack Renewal Intelligence Engine (BizOps AI Pipeline)

An enterprise-grade, modular BizOps AI pipeline that ingests, normalizes, and analyzes multi-modal account telemetry and customer sentiment. The system separates data processing, deterministic risk scoring, and LLM reasoning to identify at-risk renewals within a rolling 90-day window, outputting structured risk profiles and actionable CSM playbooks.

---

## 🏗️ Architectural Overview

The pipeline transforms fragmented raw data into proactive business insights through four decoupled layers:

```text
[ Raw Data Zone ] ──> ( Ingestion & Entity Resolution ) ──> [ Processed Snapshots ]
                                                                  │
[ Live Dashboard ] <── ( LLM Inference - Groq 120B ) <── ( Risk Scoring Engine )
```

### 1. Ingestion & Entity Resolution (`src/ingestion.py`)

* Cleans inconsistent schemas using regex normalization
* Standardizes columns to `lowercase_snake_case`
* Resolves entity mismatches via fuzzy matching (`rapidfuzz`)
* Maps noisy inputs to unified `account_id`

### 2. Deterministic Risk Engine (`src/engine.py`)

* Computes Month-over-Month (MoM) usage trends
* Evaluates engineering friction signals
* Aggregates sentiment scores
* Outputs auditable risk tiers (High / Medium / Low)

### 3. LLM Cognitive Layer (`src/llm_analyzer.py`)

* Uses Groq-hosted `openai/gpt-oss-120b`
* Enforces structured output via Pydantic
* Correlates changelogs, logs, and feedback
* Generates JSON-based playbook actions

### 4. Dashboard UI (`app.py`)

* Streamlit-based interactive interface
* Enables CSM-level filtering
* Triggers real-time playbook generation

---

## 🛠️ Data Challenges Solved

* **Fuzzy Naming Variations**
  Resolves mismatched names (e.g., *Acme Inc vs Acme Corp*) using token-based fuzzy matching (≥75% threshold)

* **Irregular Headers**
  Cleans symbols, whitespace, and casing inconsistencies via regex normalization

* **Missing Time Data**
  Handles absent timestamps (e.g., NPS data) using mean aggregation

* **Multilingual Inputs**
  Uses LLM’s native multilingual understanding (no translation layer required)

---

## ⚖️ Key Tradeoffs

### Deterministic vs LLM-Based Scoring

* Risk classification is rule-based for auditability
* LLM is used for reasoning and playbook generation

### In-Memory vs Persistent Storage

* Uses Pandas + local files
* Optimized for speed and prototype simplicity

### Regex Filtering vs Vector Search

* Uses token filtering instead of embeddings
* Reduces cost and latency while remaining effective

---

## 🔮 Future Enhancements

* **RAG for Notes**: Add embeddings + vector DB (ChromaDB / LanceDB)
* **Predictive Analytics**: Implement ARIMA / LSTM for churn forecasting
* **Workflow Integration**: Push playbooks to Jira, HubSpot, Gainsight

---

## 🚀 Production Roadmap

* Replace CSVs with pipelines (dbt / Airflow + Snowflake)
* Add async processing (Celery + Redis)
* Implement rate-limiting + model fallback
* Add CI/CD testing with `pytest`

---

## ⚙️ Setup & Run

### 1. Create Environment

```bash
conda create -n renewal python=3.11 -y
conda activate renewal
```

### 2. Install Dependencies

```bash
pip install streamlit pandas numpy rapidfuzz groq python-dotenv pydantic
```

### 3. Configure Secrets

Create a `.env` file:

```text
GROQ_API_KEY=your_api_key_here
```

### 4. Run Application

```bash
streamlit run app.py
```

---
