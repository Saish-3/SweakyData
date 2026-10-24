---
name: dataset-crime-scene-dev
description: Project development conventions and architecture guidelines for Dataset Crime Scene.
metadata:
  version: "1.0"
---

## Project Overview
Dataset Crime Scene is a local-first ML forensic tool that cross-examines tabular CSV datasets before training machine learning models.

## Architecture Rules & Conventions
1. **Separation of Concerns (Golden Rule)**:
   - Python performs all numerical calculations, hypothesis tests, and deterministic checks.
   - Gemma (local LLM via Ollama) only explains the facts and generates human-readable hypotheses and fixes.
   - NEVER let the LLM compute statistics, count rows, or determine status.
2. **Evidence Model**:
   - Every check lives in `checks/` and returns `list[Evidence]`.
   - Each `Evidence` has: `id`, `type`, `columns`, `metric`, `status` ("PROVEN" or "NO_EVIDENCE"), and `summary`.
   - Gemma never alters the `status` of an Evidence object.
3. **LLM Invocation**:
   - Gemma is only invoked via `llm.py:ask_gemma(prompt)`.
   - Skills live in `skills/<skill_name>/SKILL.md` and are loaded via `skills_loader.py`.
   - Routing is deterministic: no LLM-based skill routing.
4. **Performance & Reliability**:
   - Checks must complete quickly even on 50,000-row datasets.
   - Always handle missing data, non-numeric columns, and edge cases gracefully.
   - Always run completely locally with zero cloud dependencies.
