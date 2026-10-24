from typing import List, Dict, Any, Optional
import streamlit as st
from models import Evidence

# Inline Lucide-style SVG Icons in Royal Blue & Semantic Accents
ICON_SEARCH = """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4169E1" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>"""
ICON_SIREN = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4169E1" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M12 2v4"></path><path d="m4.93 10.93 1.41 1.41"></path><path d="M2 18h2"></path><path d="M20 18h2"></path><path d="m19.07 10.93-1.41 1.41"></path><path d="M22 22H2"></path><path d="m8 22 4-10 4 10"></path></svg>"""
ICON_GEAR = """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4169E1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path><circle cx="12" cy="12" r="3"></circle></svg>"""
ICON_ROBOT = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4169E1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><rect width="18" height="12" x="3" y="6" rx="2"></rect><path d="M12 2v4"></path><path d="M8 12h.01"></path><path d="M16 12h.01"></path></svg>"""
ICON_STETHOSCOPE = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4169E1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"></path><path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"></path><circle cx="20" cy="10" r="2"></circle></svg>"""
ICON_FOLDER = """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4169E1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"></path></svg>"""

ICON_CHECK_WHITE = """<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><polyline points="20 6 9 17 4 12"></polyline></svg>"""
ICON_CHECK_GREEN = """<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#1F9D63" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><polyline points="20 6 9 17 4 12"></polyline></svg>"""
ICON_HELP_BLUE = """<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#4169E1" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>"""
ICON_SHIELD_GREEN = """<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#137A4B" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>"""

ICON_LEAK = """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4169E1" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v8"></path><path d="m4.93 10.93 1.41 1.41"></path><path d="M2 18h2"></path><path d="M20 18h2"></path><path d="m19.07 10.93-1.41 1.41"></path><path d="M22 22H2"></path><path d="m8 22 4-10 4 10"></path></svg>"""
ICON_DUPS = """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4169E1" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"></rect><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"></path></svg>"""
ICON_LABELS = """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4169E1" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>"""
ICON_CORR = """<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4169E1" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 3 3 9-3 9"></path><path d="m21 3-3 9 3 9"></path><line x1="6" y1="12" x2="18" y2="12"></line></svg>"""
ICON_BRAIN = """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#4169E1" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M12 2a5 5 0 0 0-5 5v1a5 5 0 0 0-3 4.5 5 5 0 0 0 2 4.1V18a3 3 0 0 0 3 3h6a3 3 0 0 0 3-3v-1.4a5 5 0 0 0 2-4.1 5 5 0 0 0-3-4.5V7a5 5 0 0 0-5-5Z"></path></svg>"""
ICON_SPARKLES = """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#137A4B" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"></path></svg>"""


def badge(label: str, kind: str = "proven") -> str:
    """
    Returns HTML for badges:
    - PROVEN: solid royal blue pill with white text
    - HYPOTHESIS: white fill with royal blue outline and text
    - CLEAN: white fill with green outline and text
    """
    kind_lower = kind.lower()
    if kind_lower == "proven":
        return f'<span class="badge-pill badge-proven-fact">{ICON_CHECK_WHITE} {label}</span>'
    elif kind_lower == "hypothesis":
        return f'<span class="badge-pill badge-hypothesis-pill">{ICON_HELP_BLUE} {label}</span>'
    elif kind_lower == "clean":
        return f'<span class="badge-pill badge-clean-pill">{ICON_SHIELD_GREEN} {label}</span>'
    return f'<span class="badge-pill" style="background:var(--blue-100); color:var(--blue-700); border:1px solid var(--blue-200);">{label}</span>'


def severity_chip(level: str) -> str:
    """
    Returns colored dot + severity label HTML.
    Dot keeps semantic accent (critical, high, medium, low, clean);
    chip text stays royal blue.
    """
    lvl = (level or "low").lower()
    dot_class = f"dot dot-{lvl}" if lvl in ["critical", "high", "medium", "low", "clean"] else "dot dot-low"
    return f'<span class="severity-chip"><span class="{dot_class}"></span><span>{lvl.upper()}</span></span>'


def hero(title: str, subtitle: str) -> None:
    """Renders hero banner with white-to-blue-100 gradient and royal blue typography."""
    html = f"""
    <div class="hero-container fade-in">
        <h1 class="hero-title">
            {ICON_SEARCH} {title}
        </h1>
        <p class="hero-subtitle">{subtitle}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def metric_tile(label: str, value: Any, delta: Optional[str] = None) -> str:
    """Returns HTML for a metric tile styled in --blue-100 with royal blue text."""
    delta_html = f'<span style="font-size:0.75rem; color:var(--text-muted); margin-left:6px; font-weight:600;">{delta}</span>' if delta else ""
    return f"""
    <div class="metric-tile">
        <div class="metric-tile-val">{value}{delta_html}</div>
        <div class="metric-tile-lbl">{label}</div>
    </div>
    """


def render_metric_tiles(tiles: List[Dict[str, Any]]) -> None:
    """Renders a responsive grid of metric tiles."""
    html_parts = "".join([metric_tile(t.get("label", ""), t.get("value", ""), t.get("delta")) for t in tiles])
    st.markdown(f'<div class="metric-grid fade-in">{html_parts}</div>', unsafe_allow_html=True)


def empty_state() -> None:
    """
    Renders empty state with 4 suspect tiles in --blue-100 with royal blue icons,
    titles in --blue-900, and an in-card primary Investigate button.
    """
    html = f"""
    <div class="crime-card fade-in" style="text-align: center; padding: 32px 24px; border: 1.5px solid var(--blue-200);">
        <h3 style="margin: 0 0 8px 0; color: var(--blue-900); font-size: 1.35rem; font-weight:800;">Dataset Ready for Forensic Cross-Examination</h3>
        <p style="color: var(--text-primary); font-size: 0.95rem; max-width: 640px; margin: 0 auto 20px auto; line-height: 1.5;">
            Machine learning models fail silently when trained on contaminated data.
            <strong>SweakyData</strong> cross-examines your CSV to uncover four hidden crimes before training:
        </p>
        <div class="suspect-grid">
            <div class="suspect-card">
                <div style="margin-bottom: 8px;">{ICON_LEAK}</div>
                <strong style="color: var(--blue-900); font-size: 0.96rem; display: block; margin-bottom: 4px;">Target Leakage</strong>
                <span style="color: var(--text-primary); font-size: 0.82rem; line-height: 1.4; display: block;">
                    Features with suspiciously high single-column predictive power (AUC ≥ 0.95).
                </span>
            </div>
            <div class="suspect-card">
                <div style="margin-bottom: 8px;">{ICON_DUPS}</div>
                <strong style="color: var(--blue-900); font-size: 0.96rem; display: block; margin-bottom: 4px;">Split Duplication</strong>
                <span style="color: var(--text-primary); font-size: 0.82rem; line-height: 1.4; display: block;">
                    Identical records crossing the boundary between train and test partitions.
                </span>
            </div>
            <div class="suspect-card">
                <div style="margin-bottom: 8px;">{ICON_LABELS}</div>
                <strong style="color: var(--blue-900); font-size: 0.96rem; display: block; margin-bottom: 4px;">Label Contradictions</strong>
                <span style="color: var(--text-primary); font-size: 0.82rem; line-height: 1.4; display: block;">
                    Identical feature vectors assigned conflicting ground truth target labels.
                </span>
            </div>
            <div class="suspect-card">
                <div style="margin-bottom: 8px;">{ICON_CORR}</div>
                <strong style="color: var(--blue-900); font-size: 0.96rem; display: block; margin-bottom: 4px;">Simpson's Paradox</strong>
                <span style="color: var(--text-primary); font-size: 0.82rem; line-height: 1.4; display: block;">
                    Feature correlations that flip sign when conditioned on categorical subgroups.
                </span>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    # In-card large primary Investigate button
    col_l, col_btn, col_r = st.columns([1, 2, 1])
    with col_btn:
        if st.button("Audit with SweakyData", type="primary", use_container_width=True, key="empty_state_investigate_btn"):
            st.session_state["trigger_investigate"] = True
            st.rerun()


def evidence_card(ev: Evidence, gemma_result: Dict[str, Any], animation_delay_ms: int = 0) -> None:
    """
    Renders an individual evidence finding card:
    - 4px semantic severity stripe (critical #D93A4A, high #E8702A, medium #E0A100, low #4169E1, clean #1F9D63)
    - Card fill in --blue-50, border in --blue-200
    - PROVEN badge (solid royal blue) or CLEAN badge
    - Gemma's reading box with HYPOTHESIS badge (white with royal blue border)
    - Suggested fix box
    - Collapsible JSON expander
    """
    severity = (gemma_result.get("severity") or "low").lower()
    if ev.status == "NO_EVIDENCE":
        severity = "clean"

    stripe_class = f"stripe-{severity}"
    proven_badge_html = badge("PROVEN FACT", "proven") if ev.status == "PROVEN" else badge("NO EVIDENCE", "clean")
    hypo_badge_html = badge("GEMMA HYPOTHESIS", "hypothesis")

    # Metrics Pills
    scalar_metrics = [(k, v) for k, v in ev.metric.items() if not isinstance(v, (dict, list))]
    metric_tiles_html = ""
    if scalar_metrics:
        pills = "".join([f'<span class="badge-pill" style="background:var(--blue-100); border:1px solid var(--blue-200); color:var(--blue-700); font-family:JetBrains Mono, monospace; font-size:0.75rem;"><span style="color:var(--text-muted);">{k}:</span> <strong>{v}</strong></span>' for k, v in scalar_metrics])
        metric_tiles_html = f'<div style="margin: 8px 0; display:flex; flex-wrap:wrap; gap:6px;">{pills}</div>'

    cols_str = ", ".join(ev.columns) if ev.columns else "Global Dataset"
    delay_style = f"animation-delay: {animation_delay_ms}ms;" if animation_delay_ms > 0 else ""

    card_html = f"""
    <div class="crime-card {stripe_class} fade-in" style="{delay_style}">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; flex-wrap:wrap; gap:8px;">
            <div style="display:flex; align-items:center; gap:8px;">
                <span class="mono" style="background:var(--blue-100); color:var(--blue-900); padding:3px 8px; border-radius:6px; font-weight:700; font-size:0.8rem; border:1px solid var(--blue-200);">{ev.id}</span>
                <span style="font-weight:700; font-size:1.05rem; color:var(--blue-900); letter-spacing:-0.01em;">{ev.type.replace('_', ' ').upper()}</span>
                {severity_chip(severity)}
            </div>
            <div style="font-size:0.82rem; color:var(--text-muted); font-weight:500;">
                Targeted: <span class="mono" style="color:var(--blue-700); font-weight:600;">{cols_str}</span>
            </div>
        </div>
        
        <div style="margin-bottom: 8px;">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom: 6px;">
                {proven_badge_html}
                <span style="color:var(--text-primary); font-size:0.94rem; font-weight:600;">{ev.summary}</span>
            </div>
            {metric_tiles_html}
        </div>

        <div class="reading-box">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom: 6px;">
                {hypo_badge_html}
                <span style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; color:var(--blue-700); font-weight:700;">
                    {ICON_BRAIN} Gemma's Forensic Reading
                </span>
            </div>
            <p style="margin: 0 0 6px 0; color: var(--text-primary); font-size: 0.91rem; line-height: 1.45;">
                {gemma_result.get('explanation', '')}
            </p>
            <p style="margin: 0; color: var(--blue-900); font-size: 0.86rem; font-weight: 500; font-style: italic;">
                {gemma_result.get('hypothesis', '')}
            </p>
        </div>

        <div class="suggested-fix-box">
            <span style="font-size:0.74rem; text-transform:uppercase; letter-spacing:0.05em; color:var(--accent-clean); font-weight:700;">
                {ICON_SPARKLES} Suggested Fix
            </span>
            <p style="margin: 3px 0 0 0; color: var(--text-primary); font-size: 0.88rem; font-weight: 500;">
                {gemma_result.get('suggested_fix', '')}
            </p>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    with st.expander(f"Raw Evidence JSON ({ev.id})", expanded=False):
        st.json(ev.to_dict())
        if ev.sample_rows:
            st.caption("Sample offending rows:")
            import pandas as pd
            st.dataframe(pd.DataFrame(ev.sample_rows), use_container_width=True)
