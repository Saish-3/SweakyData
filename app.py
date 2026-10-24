import os
import json
import time
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import streamlit as st
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder

from models import Evidence
from checks import run_all_checks
from checks.duplicates import check_duplicates
from checks.leakage import check_leakage
from checks.labels import check_labels
from checks.correlation import check_correlation
import skills_loader
import llm
from samples.make_crime_scene import generate_crime_scene_dataset
from samples.make_ai_models_crime_scene import generate_ai_models_crime_scene

import ui.theme as theme
import ui.components as ui_comp

# 1. Page Configuration
st.set_page_config(
    page_title="SweakyData | AI ML Forensic Cross-Examiner",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject central CSS design system (Light Theme + Royal Blue)
theme.inject_theme()


# Helper: Engine Health Ping
@st.cache_data(ttl=60, show_spinner=False)
def check_engine_health() -> Dict[str, Any]:
    """Lightweight health check with 3-second timeout."""
    info = llm.get_backend_info()
    status = {"healthy": False, "provider": info.get("provider", "unknown"), "model": info.get("model", "")}

    if info.get("provider") == "google_genai":
        client = llm.get_genai_client()
        if client:
            status["healthy"] = True
            status["mode"] = "Google GenAI API (Gemma 4)"
    elif info.get("provider") == "ollama":
        ollama_stat = llm.check_ollama_status()
        status["healthy"] = ollama_stat.get("available", False)
        status["mode"] = "Local Ollama"
    else:
        status["healthy"] = True
        status["mode"] = "Offline Factual Proofs"

    return status


def evaluate_model_impact(
    df: pd.DataFrame,
    target_col: str,
    evidence_list: List[Evidence],
    split_col: Optional[str] = None,
) -> Optional[Tuple[float, float, List[str]]]:
    """
    Evaluates before vs after ML performance:
    Before: Model trained on raw columns (including leaks)
    After: Model trained after dropping flagged leaky columns and duplicate rows
    """
    if not target_col or target_col not in df.columns:
        return None

    valid_df = df.dropna(subset=[target_col]).copy()
    if len(valid_df) < 30:
        return None

    leaky_cols = set()
    for ev in evidence_list:
        if ev.status == "PROVEN" and ev.type == "leakage":
            for col in ev.columns:
                if col != target_col:
                    leaky_cols.add(col)

    y_raw = valid_df[target_col]
    is_clf = y_raw.nunique() <= 10 or y_raw.dtype == "object" or y_raw.dtype == "bool"
    if is_clf:
        le = LabelEncoder()
        y_before = le.fit_transform(y_raw.astype(str))
        model_cls = RandomForestClassifier
        scoring = "roc_auc" if len(np.unique(y_before)) == 2 else "accuracy"
    else:
        y_before = pd.to_numeric(y_raw, errors="coerce").fillna(0).values
        model_cls = RandomForestRegressor
        scoring = "r2"

    def prepare_X(data: pd.DataFrame, drop_cols: set) -> np.ndarray:
        feats = [c for c in data.columns if c not in drop_cols and c != target_col and c != split_col]
        X_cols = []
        for c in feats:
            col_s = data[c]
            if col_s.dtype == "object" or col_s.dtype == "bool":
                X_cols.append(pd.factorize(col_s.astype(str))[0].reshape(-1, 1))
            else:
                X_cols.append(pd.to_numeric(col_s, errors="coerce").fillna(0).values.reshape(-1, 1))
        return np.hstack(X_cols) if X_cols else np.zeros((len(data), 1))

    try:
        X_before = prepare_X(valid_df, set())
        cv = 3
        model_before = model_cls(n_estimators=25, max_depth=5, random_state=42, n_jobs=1)
        scores_before = cross_val_score(model_before, X_before, y_before, cv=cv, scoring=scoring)
        score_before_val = float(np.mean(scores_before))

        cleaned_df = valid_df.drop_duplicates().copy()
        y_after_raw = cleaned_df[target_col]
        if is_clf:
            y_after = le.fit_transform(y_after_raw.astype(str))
        else:
            y_after = pd.to_numeric(y_after_raw, errors="coerce").fillna(0).values

        X_after = prepare_X(cleaned_df, leaky_cols)
        model_after = model_cls(n_estimators=25, max_depth=5, random_state=42, n_jobs=1)
        scores_after = cross_val_score(model_after, X_after, y_after, cv=cv, scoring=scoring)
        score_after_val = float(np.mean(scores_after))

        return score_before_val, score_after_val, list(leaky_cols)
    except Exception:
        return None


def generate_markdown_report(
    evidence_items: List[Evidence],
    explanations: Dict[str, Dict[str, Any]],
    case_verdict: Dict[str, Any],
    dataset_name: str,
    before_after: Optional[Tuple[float, float, List[str]]],
) -> str:
    """Generates comprehensive forensic markdown report for download."""
    proven_crimes = [e for e in evidence_items if e.status == "PROVEN"]
    lines = [
        f"# SweakyData — Forensic Investigation Report",
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S UTC')}  ",
        f"**Dataset:** `{dataset_name}`  ",
        f"**Verdict:** {'CRIME SCENE CONTAMINATED' if proven_crimes else 'CASE DISMISSED / CLEAN'}  ",
        "",
        "## Executive Verdict",
        f"- **Summary:** {case_verdict.get('explanation', '')}",
        f"- **Hypothesis:** {case_verdict.get('hypothesis', '')}",
        f"- **Action Plan:** {case_verdict.get('suggested_fix', '')}",
        "",
    ]

    if before_after:
        sb, sa, dropped = before_after
        lines.extend([
            "## Model Impact Simulation",
            f"- **Raw (Leaked) Score:** `{sb * 100:.1f}%`",
            f"- **True Generalizable Score:** `{sa * 100:.1f}%`",
            f"- **Generalization Gap:** `{(sb - sa) * 100:+.1f}%`",
            f"- **Dropped Leaky Features:** `{', '.join(dropped) if dropped else 'None'}`",
            "",
        ])

    lines.append("## Chain of Evidence (Proven Crimes)")
    for ev in proven_crimes:
        expl = explanations.get(ev.id, {})
        lines.extend([
            f"### [{ev.id}] {ev.type.upper()} ({expl.get('severity', 'medium').upper()})",
            f"- **Columns:** `{', '.join(ev.columns)}`",
            f"- **Forensic Fact:** {ev.summary}",
            f"- **Gemma Explanation:** {expl.get('explanation', '')}",
            f"- **Hypothesis:** {expl.get('hypothesis', '')}",
            f"- **Suggested Fix:** {expl.get('suggested_fix', '')}",
            "",
        ])

    clean_items = [e for e in evidence_items if e.status == "NO_EVIDENCE"]
    if clean_items:
        lines.append("## Cleared Suspects (Clean Checks)")
        for ev in clean_items:
            lines.append(f"- **[{ev.id}] {ev.type.upper()}**: {ev.summary}")
        lines.append("")

    return "\n".join(lines)


# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:14px;">
        {ui_comp.ICON_SEARCH}
        <div>
            <h3 style="margin:0; font-size:1.15rem; color:var(--blue-900); font-weight:800; letter-spacing:-0.01em;">SweakyData</h3>
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:600;">AI ML Forensic Examiner</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# 1. Dataset Source (radio)
dataset_choice = st.sidebar.radio(
    "Dataset Source",
    ["AI Models Benchmark (Broken Scene)", "Medical Diagnosis (Planted Demo)", "Upload Custom CSV"],
    index=0,
)

df: Optional[pd.DataFrame] = None
dataset_name = "AI Models Benchmark"

if dataset_choice == "AI Models Benchmark (Broken Scene)":
    dataset_name = "AI Models Benchmark"
    if "ai_demo_df" not in st.session_state:
        st.session_state["ai_demo_df"] = generate_ai_models_crime_scene()
    df = st.session_state["ai_demo_df"]

elif dataset_choice == "Medical Diagnosis (Planted Demo)":
    dataset_name = "Medical Breast Cancer"
    if "demo_df" not in st.session_state:
        st.session_state["demo_df"] = generate_crime_scene_dataset()
    df = st.session_state["demo_df"]

else:
    dataset_name = "Custom Upload"
    uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            dataset_name = uploaded_file.name
            st.sidebar.success(f"Loaded {len(df):,} rows × {len(df.columns)} cols")
        except Exception as e:
            st.sidebar.error(f"Error reading CSV: {e}")

# 2. Big Full-Width Primary Investigate Button
investigate_sidebar = st.sidebar.button("Audit with SweakyData", type="primary", use_container_width=True)
investigate_clicked = investigate_sidebar or st.session_state.get("trigger_investigate", False)
if st.session_state.get("trigger_investigate", False):
    st.session_state["trigger_investigate"] = False

# 3. Advanced Settings (Collapsed Expander)
target_col = None
split_col = None
row_cap = 50000

if df is not None:
    cols = list(df.columns)
    with st.sidebar.expander("Advanced Settings", expanded=False):
        row_cap = st.slider(
            "Row Sampling Cap",
            min_value=1000,
            max_value=100000,
            value=50000,
            step=5000,
            help="Limits rows used for model-based checks to ensure rapid results under 5s.",
        )
        if len(df) > row_cap:
            df = df.sample(n=row_cap, random_state=42).copy()

        # Target Column detection
        default_target_idx = 0
        for cand in ["benchmark_passed", "diagnosis", "target", "label", "survived", "outcome"]:
            if cand in cols:
                default_target_idx = cols.index(cand)
                break
        target_col = st.selectbox("Target Column", cols, index=default_target_idx)

        # Split Column detection
        split_options = ["None"] + [c for c in cols if c != target_col]
        default_split_idx = 0
        for cand in ["eval_split", "data_split", "split", "fold", "partition"]:
            if cand in split_options:
                default_split_idx = split_options.index(cand)
                break
        selected_split = st.selectbox("Split Column (Optional)", split_options, index=default_split_idx)
        split_col = None if selected_split == "None" else selected_split

        # Regenerate button
        if dataset_choice == "AI Models Benchmark (Broken Scene)":
            if st.button("Regenerate AI Dataset", use_container_width=True):
                st.session_state["ai_demo_df"] = generate_ai_models_crime_scene()
                st.rerun()
        elif dataset_choice == "Medical Diagnosis (Planted Demo)":
            if st.button("Regenerate Medical Dataset", use_container_width=True):
                st.session_state["demo_df"] = generate_crime_scene_dataset()
                st.rerun()

# 4. Gemma Engine Status (Collapsed Expander at Bottom)
engine_health = check_engine_health()
with st.sidebar.expander("Gemma Engine Status", expanded=False):
    backend_info = llm.get_backend_info()
    dot_color = "var(--accent-clean)" if engine_health["healthy"] else "var(--accent-critical)"
    st.markdown(
        f'<div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">'
        f'<span class="dot" style="background-color:{dot_color};"></span>'
        f'<strong>Mode:</strong> {engine_health.get("mode", "Online")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"**Model ID:** `{backend_info.get('model', 'gemma-4-26b-a4b-it')}`")

    # Local vs API toggle if available
    has_api_key = bool(os.getenv("GEMINI_API_KEY"))
    ollama_stat = llm.check_ollama_status()
    if has_api_key and ollama_stat["available"]:
        provider_pref = st.radio("Backend Provider", ["Google GenAI API (Gemma 4)", "Local Ollama"], index=0)
        if provider_pref == "Local Ollama":
            os.environ["PREFER_LOCAL_OLLAMA"] = "1"
        else:
            os.environ.pop("PREFER_LOCAL_OLLAMA", None)

    st.caption("Deterministic checks find the crimes; Gemma explains them.")


# ==========================================
# MAIN INTERFACE
# ==========================================
ui_comp.hero(
    title="SweakyData",
    subtitle="AI ML Forensic Cross-Examiner: Python proves the facts with mathematical certainty. Gemma 4 diagnoses the motives and root causes.",
)

if df is None:
    ui_comp.empty_state()
    st.stop()


# Investigation Execution State
if investigate_clicked:
    t_start = time.perf_counter()

    with st.status("Conducting Forensic Cross-Examination...", expanded=True) as status_box:
        # Step 1: Duplicates & Split checks
        st.write("Checking exact duplicates & train/test split cross-contamination...")
        t0 = time.perf_counter()
        dup_ev = check_duplicates(df, split_col=split_col, id_prefix="E", start_index=1)
        st.write(f"✓ Checked duplicates & partitions ({time.perf_counter() - t0:.2f}s)")

        # Step 2: Leakage checks
        st.write("Auditing predictive leakage, ID columns & zero-variance features...")
        t0 = time.perf_counter()
        leak_ev = check_leakage(df, target_col=target_col, id_prefix="E", start_index=len(dup_ev) + 1)
        st.write(f"✓ Audited target leakage ({time.perf_counter() - t0:.2f}s)")

        # Step 3: Label Noise checks
        label_ev = []
        if target_col and target_col in df.columns:
            st.write("Auditing conflicting labels on identical feature vectors...")
            t0 = time.perf_counter()
            label_ev = check_labels(df, target_col=target_col, split_col=split_col, id_prefix="E", start_index=len(dup_ev) + len(leak_ev) + 1)
            st.write(f"✓ Audited label consistency ({time.perf_counter() - t0:.2f}s)")

        # Step 4: Simpson's Paradox
        st.write("Checking for Simpson's paradox across categorical subgroups...")
        t0 = time.perf_counter()
        corr_ev = check_correlation(df, id_prefix="E", start_index=len(dup_ev) + len(leak_ev) + len(label_ev) + 1)
        st.write(f"✓ Evaluated correlation sign reversals ({time.perf_counter() - t0:.2f}s)")

        all_ev = dup_ev + leak_ev + label_ev + corr_ev
        for i, ev in enumerate(all_ev, start=1):
            ev.id = f"E{i}"

        # Step 5: Query Gemma via Agent Skills
        st.write("Dispatching Agent Skills & querying Gemma 4 in parallel...")
        t0 = time.perf_counter()
        explanations: Dict[str, Dict[str, Any]] = {}

        # Instantly resolve NO_EVIDENCE clean checks without burning LLM network latency
        for ev in all_ev:
            if ev.status == "NO_EVIDENCE":
                explanations[ev.id] = {
                    "evidence_id": ev.id,
                    "explanation": f"Column evaluated cleanly: {ev.summary}",
                    "severity": "low",
                    "hypothesis": "HYPOTHESIS: Statistical distribution is consistent with clean baseline data.",
                    "suggested_fix": "No remediation needed. Feature safe to include in training.",
                }

        # Query PROVEN crimes concurrently in parallel
        proven_items = [e for e in all_ev if e.status == "PROVEN"]
        if proven_items:
            def query_proven(ev_item):
                s_name = skills_loader.route(ev_item.type)
                p = skills_loader.build_prompt(s_name, ev_item)
                return ev_item.id, llm.ask_gemma(p, fallback_evidence_id=ev_item.id, fallback_summary=ev_item.summary)

            with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(proven_items))) as pool:
                future_results = pool.map(query_proven, proven_items)
                for eid, expl in future_results:
                    explanations[eid] = expl

        st.write(f"✓ Gemma 4 explanations complete ({time.perf_counter() - t0:.2f}s)")

        # Step 6: Case Summary
        st.write("Lead Detective synthesizing overall Case Verdict...")
        compact_summary_ev = [
            {
                "id": e.id,
                "type": e.type,
                "status": e.status,
                "columns": e.columns,
                "metric": e.metric,
                "summary": e.summary,
            }
            for e in all_ev
        ]
        summary_prompt = skills_loader.build_prompt("case-summary", compact_summary_ev)
        case_verdict = llm.ask_gemma(summary_prompt, fallback_evidence_id="ALL", fallback_summary="Forensic dataset audit complete.")

        status_box.update(label=f"Cross-examination complete in {time.perf_counter() - t_start:.2f}s", state="complete", expanded=False)

    st.session_state["results"] = {
        "evidence": [ev.to_dict() for ev in all_ev],
        "explanations": explanations,
        "case_verdict": case_verdict,
        "dataset_name": dataset_name,
    }


# Render Results or Empty State
if "results" not in st.session_state:
    ui_comp.empty_state()
else:
    res = st.session_state["results"]
    evidence_objs = [Evidence.from_dict(d) for d in res["evidence"]]
    explanations = res["explanations"]
    case_verdict = res["case_verdict"]

    proven_crimes = [e for e in evidence_objs if e.status == "PROVEN"]
    clean_items = [e for e in evidence_objs if e.status == "NO_EVIDENCE"]

    # Severity sorting: critical > high > medium > low
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    proven_crimes.sort(
        key=lambda e: severity_order.get(explanations.get(e.id, {}).get("severity", "medium").lower(), 2)
    )

    critical_count = sum(
        1 for e in proven_crimes
        if explanations.get(e.id, {}).get("severity", "medium").lower() in ["critical", "high"]
    )

    # Top Metric Tiles Strip
    metric_tiles_data = [
        {"label": "Proven Crimes", "value": f"{len(proven_crimes)}", "delta": "Violations" if proven_crimes else "Clean"},
        {"label": "Critical Severity", "value": f"{critical_count}", "delta": "High Alert" if critical_count else None},
        {"label": "Gemma Hypotheses", "value": f"{len(evidence_objs)}", "delta": "Formulated"},
        {"label": "Cleared Checks", "value": f"{len(clean_items)}", "delta": "No Evidence"},
    ]
    ui_comp.render_metric_tiles(metric_tiles_data)

    # Before / After Simulation calculation
    before_after_impact = evaluate_model_impact(df, target_col, evidence_objs, split_col=split_col) if target_col else None

    # Tabs Layout
    tab_board, tab_verdict, tab_locker = st.tabs(["Case Board", "Verdict & Impact", "Evidence Locker"])

    # ----------------------------------------
    # TAB 1: CASE BOARD
    # ----------------------------------------
    with tab_board:
        if not proven_crimes:
            st.markdown(
                """
                <div class="crime-card" style="border-left: 4px solid var(--accent-clean); padding: 24px;">
                    <h3 style="color: var(--accent-clean); margin-top:0;">No Data Crimes Detected</h3>
                    <p style="color: var(--text-primary); margin-bottom:0;">
                        All deterministic checks passed with flying colors. The dataset appears clean and safe for model training.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for idx, ev in enumerate(proven_crimes):
                gemma_res = explanations.get(ev.id, {})
                ui_comp.evidence_card(ev, gemma_res, animation_delay_ms=idx * 50)

        # Cleared Suspects (Restraint Section)
        if clean_items:
            with st.expander(f"Cleared Suspects ({len(clean_items)} Checks with NO EVIDENCE)", expanded=False):
                st.caption("Demonstrating model restraint: these columns/pairs were thoroughly audited and found completely innocent.")
                for ev in clean_items:
                    gemma_res = explanations.get(ev.id, {})
                    ui_comp.evidence_card(ev, gemma_res)

    # ----------------------------------------
    # TAB 2: VERDICT & IMPACT
    # ----------------------------------------
    with tab_verdict:
        is_clean = len(proven_crimes) == 0
        stripe_color = "var(--accent-clean)" if is_clean else "var(--accent-critical)"
        verdict_title = "CASE DISMISSED — DATASET CLEAN" if is_clean else "VERDICT — CONTAMINATED CRIME SCENE"

        st.markdown(
            f"""
            <div class="crime-card fade-in" style="border-left: 4px solid {stripe_color}; padding: 24px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <h3 style="margin:0; color:var(--blue-900); font-size:1.3rem;">{verdict_title}</h3>
                    {ui_comp.badge("VERDICT SYNTHESIS", "proven" if not is_clean else "clean")}
                </div>
                <p style="color:var(--text-primary); font-size:1.02rem; line-height:1.5; margin-bottom:14px; font-weight:500;">
                    <strong style="color:var(--blue-900);">Lead Detective Summary:</strong> {case_verdict.get('explanation', '')}
                </p>
                <div class="reading-box" style="margin-top:0; margin-bottom:12px;">
                    <strong style="color:var(--blue-700); font-size:0.85rem; text-transform:uppercase;">Hypothesis:</strong>
                    <p style="margin:4px 0 0 0; color:var(--blue-900); font-size:0.92rem; font-weight:500;">{case_verdict.get('hypothesis', '')}</p>
                </div>
                <div class="suggested-fix-box">
                    <strong style="color:var(--accent-clean); font-size:0.85rem; text-transform:uppercase;">Remediation Checklist:</strong>
                    <p style="margin:4px 0 0 0; color:var(--text-primary); font-size:0.9rem; font-weight:500;">{case_verdict.get('suggested_fix', '')}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Before vs After Model Accuracy Impact
        if before_after_impact:
            score_before, score_after, dropped_cols = before_after_impact
            st.markdown("### Generalization Gap (Simulation)")
            st.caption("Comparing model performance trained on contaminated features vs cleaned dataset.")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(
                    ui_comp.metric_tile("Raw (Leaked) Score", f"{score_before * 100:.1f}%", "Biased"),
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    ui_comp.metric_tile("True Generalizable Score", f"{score_after * 100:.1f}%", "Honest"),
                    unsafe_allow_html=True,
                )
            with c3:
                gap = (score_before - score_after) * 100
                st.markdown(
                    ui_comp.metric_tile("Generalization Gap", f"{gap:+.1f}%", "Avoided Overfitting"),
                    unsafe_allow_html=True,
                )

            # Monochrome blue bar chart
            chart_df = pd.DataFrame(
                {
                    "Model Pipeline": ["Raw Dataset (Leaked)", "Cleaned Dataset (Honest)"],
                    "Validation Score (%)": [score_before * 100, score_after * 100],
                }
            ).set_index("Model Pipeline")
            st.bar_chart(chart_df, color="#4169E1")

        # Download Report Button
        report_md = generate_markdown_report(evidence_objs, explanations, case_verdict, dataset_name, before_after_impact)
        st.markdown("---")
        st.download_button(
            label="Download Forensic Case Report (.md)",
            data=report_md,
            file_name=f"crime_scene_report_{time.strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    # ----------------------------------------
    # TAB 3: EVIDENCE LOCKER
    # ----------------------------------------
    with tab_locker:
        st.markdown("### Raw Evidence Data Locker")
        st.dataframe(df.head(25), use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            st.caption(f"**Shape:** {df.shape[0]:,} rows × {df.shape[1]} columns")
            st.caption(f"**Target Column:** `{target_col or 'None'}`")
            st.caption(f"**Split Column:** `{split_col or 'None'}`")
        with col_b:
            evidence_json_export = json.dumps([e.to_dict() for e in evidence_objs], indent=2, default=str)
            st.download_button(
                label="Export Evidence Chain (.json)",
                data=evidence_json_export,
                file_name=f"evidence_chain_{time.strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )
