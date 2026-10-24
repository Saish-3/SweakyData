# 🔍 sweakyData
**AI ML Forensic Cross-Examiner**

> *"Python proves the crimes. Gemma 4 explains the motives."*

sweakyData cross-examines tabular CSV datasets before training machine learning models, constructing an unassailable chain of forensic evidence for target leakage, duplicate records, cross-split contamination, suspicious conflicting labels, and Simpson's paradox.

---

## 🏛️ Core Architecture Rule
1. **Deterministic Python finds the facts**: Pure mathematical tests and scikit-learn models evaluate the data and return structured `Evidence` objects with statuses `PROVEN` or `NO_EVIDENCE`.
2. **Gemma explains the findings**: Gemma (served locally via Ollama) receives the structured evidence JSON (never raw rows) and outputs plain-English explanations, severity ratings, explicit hypotheses, and recommended fixes.
3. **Gemma never alters an Evidence status**: The UI displays `PROVEN FACT` and `GEMMA HYPOTHESIS` as separate, distinct badges.

---

## 🧩 Agent Skills Format
Runtime skills for Gemma follow the open Agent Skills format in `./skills/`:
- `skills/explain-leakage/SKILL.md`
- `skills/explain-duplicates/SKILL.md`
- `skills/audit-labels/SKILL.md`
- `skills/explain-correlation/SKILL.md`
- `skills/case-summary/SKILL.md`
- Developer conventions skill: `.github/skills/dataset-crime-scene-dev/SKILL.md`

Skills are loaded via `skills_loader.py` with progressive disclosure: only metadata is loaded into the catalog; full skill bodies are injected on demand with deterministic routing.

---

## ⚡ Quick Start

### 1. Requirements & Dependencies
Ensure Python 3.11+ is installed. Then install requirements:
```bash
pip install -r requirements.txt
```

### 2. Gemma 4 Engine (API & Local Ollama Support)
Dataset Crime Scene seamlessly connects to **Gemma 4**:

- **Option A (Google Gemma 4 API — Active)**:
  Configure `GEMINI_API_KEY` and `GEMMA_MODEL_ID` in your `.env` file:
  ```env
  GEMINI_API_KEY=your_key_here
  GEMMA_MODEL_ID=gemma-4-26b-a4b-it
  ```
- **Option B (Local Ollama)**:
  If you prefer running fully locally with Ollama:
  ```bash
  ollama serve
  ollama pull gemma4:e4b
  export GEMMA_MODEL="gemma4:e4b"
  ```
- **Option C (Graceful Fallback)**:
  If neither API nor Ollama is reachable, the engine gracefully presents deterministic forensic facts without crashing.

### 3. Run Forensic Self-Test
Verify all checks and planted data crimes against the benchmark dataset:
```bash
python samples/make_crime_scene.py --selftest
```
Output:
```
✓ Target leakage detected (post_biopsy_malignancy_index)
✓ Cross-split duplicate leakage detected (data_split)
✓ Identical feature conflicting labels detected
✓ Simpson's paradox detected (drug_dosage_mg vs cellular_biomarker_level)
✓ Innocent column 'suspicious_risk_index' confirmed NO_EVIDENCE
```

### 4. Launch the Detective Streamlit UI
```bash
streamlit run app.py
```

---

## 🗂️ Project Structure
```
├── app.py                         # Streamlit detective forensic UI
├── models.py                      # Evidence and Explanation dataclasses + serialization
├── skills_loader.py               # Progressive disclosure Agent Skills loader & deterministic router
├── llm.py                         # Local Ollama client (JSON mode, temperature 0.2, fallback)
├── checks/                        # Deterministic forensic checks
│   ├── __init__.py                # run_all_checks orchestrator
│   ├── duplicates.py              # Exact duplicates & cross-split contamination
│   ├── leakage.py                 # Depth-2 CV single-feature predictive power & ID/constant checks
│   ├── labels.py                  # Identical feature conflicting labels & CV disagreement
│   └── correlation.py             # Simpson's paradox correlation sign reversal check
├── skills/                        # Runtime Agent Skills (Gemma)
│   ├── explain-leakage/SKILL.md
│   ├── explain-duplicates/SKILL.md
│   ├── audit-labels/SKILL.md
│   ├── explain-correlation/SKILL.md
│   └── case-summary/SKILL.md
├── samples/
│   ├── make_crime_scene.py        # Demo generator with planted crimes & --selftest
│   └── crime_scene_dataset.csv    # Generated demo dataset
├── .github/skills/
│   └── dataset-crime-scene-dev/   # Developer rules & conventions skill
├── requirements.txt
└── README.md
```

---

## ⚖️ Features & Capabilities
- **Chain of Evidence Cards**: Color-coded severity stripes (Critical, High, Medium, Low) with explicit `PROVEN FACT` and `GEMMA HYPOTHESIS` badges.
- **Before vs. After Model Simulation**: Trains an out-of-fold Random Forest before and after dropping proven leaks and duplicates to reveal the "Generalization Gap".
- **Raw Evidence Collapsible**: Full JSON inspection with offending rows for complete transparency during hackathon judging.
