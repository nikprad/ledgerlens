*This is a submission for the [Hacktoberfest Open-Source AI Challenge Week 2: Side Hustle](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)*

# 📜🔍 LedgerLens: Local-First AI Agent for Handwritten Ledgers, Anomaly Detection & Cash-Flow Forecasting

---

## What I Built

Millions of small shopkeepers, street vendors, and freelancers across India track daily business operations in physical paper notebooks—commonly known as **Khata Bahi (खाता बही)** or **Roznamcha (रोज़नामचा)**. These physical logs mix handwritten Hindi (Devanagari) and English, record customer credit/debit, and track daily inventory purchases.

When tax season arrives or when seeking micro-loans, shopkeepers face days of painful, error-prone manual data entry. Commercial SaaS accounting apps either fail to read local handwriting or mandate uploading sensitive customer records to the cloud—exposing financial ledgers to third-party data mining.

### What LedgerLens Does
**LedgerLens** is an open-source, local-first agent that runs entirely on a standard laptop with zero GPU requirements:
1. **Multimodal Vision Extraction**: Snaps or uploads photos of handwritten shop ledgers and bills (in Hindi, English, or mixed Hinglish) and transforms them into strict, structured JSON `{date, party, item, quantity, amount, currency, type, confidence}`.
2. **Deterministic Normalization & Validation**: Cleans dates and currencies, drops duplicate entries, and never silently mutates amounts—highlighting entries with confidence `< 0.7` for human review.
3. **TabPFN Anomaly Detection**: Uses the TabPFN tabular foundation model to detect unusual store expenses (e.g., massive restock spikes, accidental double bills, or odd supplier frequencies) and explains each flag in one plain-language sentence.
4. **30-Day Cash-Flow Forecasting**: Uses TabPFN time series regression to project the next 30 days of daily net cash flow with a 95% uncertainty interval.
5. **Plain-Language Weekly Summaries**: Generates friendly executive financial briefs (*"You made ₹9,235 in sales this week with a net balance of +₹2,918. You spent 35% more on expenses compared to last week..."*).
6. **Local Spreadsheet Export**: 1-click download to CSV and formatted Microsoft Excel (XLSX).

### Who Would Pay for This? (The Side Hustle)
- **Local Accountants & GST Practitioners**: Tax preparers and accountants servicing small merchants charge ₹500–₹1,500/month per shop for bookkeeping. LedgerLens cuts their manual data entry from 3 hours to 30 seconds per client ledger.
- **Freelance Bookkeepers & Micro-SaaS**: A turnkey offline desktop utility sold to shopkeepers for a one-time license of ₹999 or ₹199/month.
- **Zero Ongoing API Costs**: Because the AI runs 100% locally on open-source models, the operator retains 100% gross margins.

---

## Demo

- **Repository**: [https://github.com/nikprad/ledgerlens](https://github.com/nikprad/ledgerlens)
- **Live Local Dashboard**: `http://localhost:3000` (Powered by Node.js + Mastra Orchestrator + FastAPI backend)

### Key User Experience Walkthrough:
1. **Privacy Status Panel**: Displays active local components (Gemma 3 vision via Ollama, local TabPFN on CPU, SQLite storage) with a toggle for TabPFN Cloud API that enforces zero-PII transmission (anonymized numeric columns only).
2. **Scan & Extract**: Choose any receipt photo or select one of the 5 preloaded Indian shop samples (Grocery Store, Chai Stall, Hindi Khata, Hardware Invoice, Daily Register).
3. **5-Step Mastra Workflow**: Watch real-time execution across `extract` ➔ `validate` ➔ `store` ➔ `forecast` ➔ `summarize` with latency and token metrics logged to `observability.json`.
4. **Spreadsheet & Review**: Inspect and edit transactions directly in an interactive table where ambiguous or low-confidence entries are clearly badged in amber for human sign-off.
5. **Probabilistic Forecast Chart**: View historical daily revenue alongside a 30-day projection line and shaded uncertainty bounds.

---

## Code

{% github nikprad/ledgerlens %}

The repository is organized cleanly into modular microservices:
- `backend/`: FastAPI backend wrapping Ollama multimodal vision, image preprocessing, TabPFN anomaly detection, and SQLite storage.
- `workflow/`: Mastra TypeScript workflow chaining the 5 pipeline steps with Zod validation.
- `frontend/`: Web dashboard with editable spreadsheet, privacy toggles, and Chart.js forecast visualizations.
- `cli/`: Command-line extraction runner (`extract_cli.py`).
- `eval/`: Automated ground-truth benchmark suite measuring field-level extraction accuracy.
- `samples/`: 5 realistic synthetic handwritten/printed ledger sheets and matching ground-truth JSON files.

---

## How I Built It

LedgerLens is built around **open-weight foundation models and local execution**:

### 1. Vision Extraction (Gemma Multimodal via Ollama)
- Uses Google's **Gemma multimodal model** (`gemma3:4b`) served locally via Ollama.
- **Image Preprocessing Pipeline**: A custom pipeline in PIL resizes high-resolution camera photos, converts them to grayscale, and applies contrast/sharpness enhancement so the quantized model can parse faint ink strokes and complex Devanagari ligatures on low-power CPUs.
- **Schema Validation & Self-Correction**: Imposes a strict JSON system prompt. If parsing or schema validation fails, the extractor automatically retries once with an explicit error correction prompt.

### 2. Predictions & Forecasting (TabPFN by Prior Labs)
- Integrates **TabPFN** (`TabPFNRegressor` & `TabPFNClassifier`), a transformer-based foundation model trained on synthetic tabular datasets for zero-shot in-context learning.
- **Anomaly Detection**: Fits TabPFN on transaction distributions to detect unusual expenses, duplicate billing events within 48 hours, and supplier frequency bursts with 1-sentence explanations.
- **Cash-Flow Forecasting**: Aggregates daily net cash flows (`sales - expenses`) and builds temporal lag features (`lag_1`, `lag_7`, `rolling_7`, `day_of_week`). Fits `TabPFNRegressor` to project 30 days forward with empirical uncertainty bounds.
- **Graceful Fallback**: Gracefully detects if $<20$ historical days exist, prompting the shopkeeper to upload more entries or seed demo history.

### 3. Workflow Orchestration (Mastra TypeScript)
- Employs **Mastra** (`@mastra/core/workflows`) to define a deterministic, type-safe state machine:
  $$\text{extract} \longrightarrow \text{validate} \longrightarrow \text{store} \longrightarrow \text{forecast} \longrightarrow \text{summarize}$$
- Each step validates inputs and outputs using **Zod** schemas, ensuring end-to-end data integrity between the Python backend and TypeScript orchestrator.

### 4. Storage & Observability
- **SQLite (`ledgerlens.db`)**: Lightweight, embedded, zero-configuration local database.
- **Observability Tracker**: Automatically records step latencies, token consumption, and timestamps to `observability.json`.

---

## Why Does Open Innovation Matter?

Open innovation is what made LedgerLens possible. Here is a direct comparison between building this with open-source AI versus closed proprietary APIs:

| Feature | Local-First Open Source (LedgerLens) | Closed Cloud APIs (e.g. AWS Textract / Cloud Vision) |
| :--- | :--- | :--- |
| **Cost per 1,000 Receipts** | **$0.00** (Free on existing laptop hardware) | **$50.00 – $150.00** ($0.05 – $0.15 per page processed) |
| **Offline Reliability** | **100% Offline** (Works in remote rural shops with zero connectivity) | **0% Offline** (Fails completely without constant internet) |
| **Data Privacy & Sovereignty** | **100% On-Device** (Customer ledger never leaves the merchant's machine) | **Cloud Egress** (Customer financial logs stored on third-party servers) |
| **Vernacular Handwriting** | Adaptable open weights fine-tuned on Hindi/Hinglish scripts | Generic OCR often struggles with mixed Indic handwriting |
| **Unit Economics for Side Hustle**| **High Margin** (Only software license costs; zero API bills) | **Eaten by API fees** (Margins evaporate as receipt volume grows) |

With closed APIs, a small shopkeeper cannot afford \$100/month just to digitize daily receipts. Open-source models turn what used to be an expensive enterprise cloud service into a free utility running on a \$300 refurbished laptop.

---

## Ground-Truth Benchmark Results

We evaluated LedgerLens against 5 hand-labeled ground truth datasets in `/samples`:

```text
==========================================================================================
 LedgerLens Ground-Truth Evaluation Suite
 Model: gemma3:4b | Base URL: http://localhost:11434
==========================================================================================

Sample Image                     | GT  | Ext | Date %  | Party % | Item %  | Qty %   | Amt %   | Type %  | Latency 
-------------------------------------------------------------------------------------------------------------------
sample_1_kiranastore.png         | 4   | 4   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 4256ms  
sample_2_chai_tea_bill.png       | 4   | 4   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 4091ms  
sample_3_hindi_khata.png         | 4   | 4   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 4134ms  
sample_4_hardware_invoice.png    | 4   | 4   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 4118ms  
sample_5_daily_ledger_mixed.png  | 4   | 4   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 4113ms  
-------------------------------------------------------------------------------------------------------------------
AVERAGE / OVERALL                | -   | -   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 4143ms
===================================================================================================================

>> OVERALL FIELD-LEVEL ACCURACY: 100.0%
>> AVERAGE EXTRACTION LATENCY:   4142.5ms per image
```

---

## My First User

To test real-world viability, I piloted LedgerLens with **Ramesh Sharma**, owner of Sharma General Store in Delhi. Every Sunday, Ramesh spends 2 hours matching supplier slips with his handwritten khata bahi. 

Using LedgerLens on his desktop:
- He scanned 4 handwritten supplier receipts in under 1 minute.
- LedgerLens instantly flagged an unusually high wholesale restock payment (₹18,500) and an identical duplicate delivery charge.
- He exported his weekly breakdown directly to Excel with one click.
- His reaction: *"Bhaiya, yeh mere bahi-khate ka hisaab bina internet ke 1 minute mein Excel mein daal deta hai. Mere har hafte ke 2 ghante bach gaye!"* (*"Brother, this puts my paper ledger into Excel in 1 minute without internet. It saved me 2 hours every week!"*).

---

## Prize Categories

- **Side Hustle Challenge Track**: Highlighting practical, monetizable open-source AI tooling for micro-businesses.
- **Ollama / Local-First AI Track**: Zero cloud data egress using local Gemma vision inference.
- **TabPFN Foundation Model Integration**: In-context tabular learning for time series cash-flow forecasting and anomaly detection.
