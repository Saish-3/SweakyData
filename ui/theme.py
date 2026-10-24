import streamlit as st

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
    --bg-page: #FFFFFF;
    --bg-sidebar: #F3F7FF;

    /* Royal Blue Primary & Text */
    --text-primary: #2347B8;
    --text-muted: #385DC2;
    --text-dark: #14307F;

    /* Blue Palette Shades */
    --blue-50:  #F3F7FF;
    --blue-100: #E6EEFF;
    --blue-200: #CFDDFF;
    --blue-300: #A8C0FF;
    --blue-500: #4169E1;
    --blue-700: #2347B8;
    --blue-900: #14307F;

    /* Semantic Accent Colors (Optimized for WCAG AA 4.5+:1 on light) */
    --accent-critical: #C72838;
    --accent-high:     #E8702A;
    --accent-medium:   #C27E00;
    --accent-low:      #4169E1;
    --accent-clean:    #137A4B;

    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 12px;
    --shadow-soft: 0 4px 14px rgba(65, 105, 225, 0.08);
    --shadow-hover: 0 8px 24px rgba(65, 105, 225, 0.16);
    --shadow-btn: 0 4px 14px rgba(65, 105, 225, 0.25);
    --transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* Base Body & App View Container */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: var(--bg-page) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--blue-200) !important;
}

[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1100px !important;
}

/* Hide Default Chrome (Menu, Footer, Deploy button) */
#MainMenu, footer, .stDeployButton, [data-testid="stToolbarActions"], [data-testid="stAppDeployButton"] {
    visibility: hidden !important;
    display: none !important;
}

/* Header stays transparent so the sidebar collapse/expand button is accessible */
header[data-testid="stHeader"] {
    background: transparent !important;
}

/* Ensure sidebar collapse & expand toggle button is always visible and royal blue */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
button[aria-label="Open sidebar"],
button[aria-label="Close sidebar"] {
    visibility: visible !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    color: var(--blue-700) !important;
    background-color: var(--blue-50) !important;
    border: 1px solid var(--blue-200) !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: var(--shadow-soft) !important;
    z-index: 1000000 !important;
    transition: var(--transition) !important;
}

[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapseButton"]:hover {
    background-color: var(--blue-100) !important;
    border-color: var(--blue-300) !important;
}

[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapseButton"] svg {
    stroke: var(--blue-700) !important;
    fill: var(--blue-700) !important;
}

/* Force Royal Blue on Headers and Markdown */
h1, h2, h3, h4, h5, h6, .stMarkdown, p, span, label, div {
    color: var(--text-primary);
}

h1 { color: var(--blue-900) !important; font-weight: 800 !important; }
h2 { color: var(--blue-900) !important; font-weight: 700 !important; }
h3 { color: var(--blue-900) !important; font-weight: 700 !important; }

/* Small captions & labels */
.stCaption, small, [data-testid="stCaptionContainer"] {
    color: var(--text-muted) !important;
    font-weight: 500 !important;
}

/* JetBrains Mono for Code & IDs */
code, pre, .mono, [data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Input, Select, and Form Labels */
[data-testid="stWidgetLabel"] label, [data-testid="stWidgetLabel"] p {
    color: var(--text-dark) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
}

[data-testid="stSelectbox"] > div > div, 
[data-testid="stFileUploader"] > div,
[data-testid="stTextInput"] > div > div {
    background-color: var(--blue-50) !important;
    border: 1px solid var(--blue-200) !important;
    color: var(--text-primary) !important;
    border-radius: var(--radius-md) !important;
}

/* Primary Button Styling (Audit with sweakyData): Light Blue Box + Pure White Text */
div.stButton > button[kind="primary"] {
    background: linear-gradient(180deg, #4A82F6 0%, #3B72E6 100%) !important;
    border: 1px solid #3B72E6 !important;
    border-radius: 10px !important;
    box-shadow: 0 4px 14px rgba(59, 114, 230, 0.28) !important;
    transition: var(--transition) !important;
    padding: 0.6rem 1.3rem !important;
}

div.stButton > button[kind="primary"]:hover {
    background: linear-gradient(180deg, #3B72E6 0%, #285EC9 100%) !important;
    border-color: #285EC9 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(59, 114, 230, 0.38) !important;
}

/* Force pure white text on primary button and all internal child elements */
div.stButton > button[kind="primary"],
div.stButton > button[kind="primary"] *,
div.stButton > button[kind="primary"] p,
div.stButton > button[kind="primary"] span,
div.stButton > button[kind="primary"] div {
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.01em !important;
}

/* Secondary Button */
div.stButton > button:not([kind="primary"]) {
    background: var(--blue-50) !important;
    border: 1px solid var(--blue-200) !important;
    color: var(--blue-700) !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    transition: var(--transition) !important;
}

div.stButton > button:not([kind="primary"]):hover {
    background: var(--blue-100) !important;
    border-color: var(--blue-300) !important;
}

/* Expanders in Sidebar and Main Page */
[data-testid="stExpander"] {
    background-color: var(--blue-50) !important;
    border: 1px solid var(--blue-200) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-soft) !important;
    margin-bottom: 12px !important;
}

[data-testid="stExpander"] details summary span {
    color: var(--text-dark) !important;
    font-weight: 600 !important;
}

/* Cards */
.crime-card {
    background-color: var(--blue-50);
    border: 1px solid var(--blue-200);
    border-radius: var(--radius-lg);
    padding: 20px 24px;
    margin-bottom: 16px;
    box-shadow: var(--shadow-soft);
    transition: var(--transition);
    position: relative;
    overflow: hidden;
}

.crime-card:hover {
    border-color: var(--blue-300);
    transform: translateY(-2px);
    box-shadow: var(--shadow-hover);
}

/* Severity Stripes */
.stripe-critical { border-left: 4px solid var(--accent-critical) !important; }
.stripe-high     { border-left: 4px solid var(--accent-high) !important; }
.stripe-medium   { border-left: 4px solid var(--accent-medium) !important; }
.stripe-low      { border-left: 4px solid var(--accent-low) !important; }
.stripe-clean    { border-left: 4px solid var(--accent-clean) !important; }

/* Hero Banner */
.hero-container {
    background: linear-gradient(135deg, #FFFFFF 0%, var(--blue-100) 100%);
    border: 1px solid var(--blue-200);
    border-left: 4px solid var(--blue-500);
    border-radius: var(--radius-lg);
    padding: 24px 28px;
    margin-bottom: 24px;
    box-shadow: var(--shadow-soft);
}

.hero-title {
    font-size: 2.1rem;
    font-weight: 800;
    margin: 0 0 6px 0;
    letter-spacing: -0.03em;
    color: var(--blue-900) !important;
    display: flex;
    align-items: center;
    gap: 12px;
}

.hero-subtitle {
    color: var(--text-primary) !important;
    font-size: 0.98rem;
    line-height: 1.5;
    margin: 0;
}

/* Metric Tiles Grid */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
}

.metric-tile {
    background: var(--blue-100);
    border: 1px solid var(--blue-200);
    border-radius: var(--radius-lg);
    padding: 16px 20px;
    transition: var(--transition);
    box-shadow: var(--shadow-soft);
}

.metric-tile:hover {
    border-color: var(--blue-300);
    transform: translateY(-1px);
}

.metric-tile-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--blue-700);
    line-height: 1.2;
}

.metric-tile-lbl {
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    margin-top: 4px;
}

/* Badge Styles */
.badge-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.badge-proven-fact {
    background: var(--blue-700);
    color: #FFFFFF !important;
    border: 1px solid var(--blue-700);
}

.badge-proven-fact svg {
    stroke: #FFFFFF;
}

.badge-hypothesis-pill {
    background: #FFFFFF;
    color: var(--blue-700);
    border: 1.5px solid var(--blue-500);
}

.badge-hypothesis-pill svg {
    stroke: var(--blue-500);
}

.badge-clean-pill {
    background: #FFFFFF;
    color: var(--accent-clean);
    border: 1.5px solid var(--accent-clean);
}

.badge-clean-pill svg {
    stroke: var(--accent-clean);
}

/* Severity Chip */
.severity-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 3px 8px;
    border-radius: var(--radius-sm);
    background: var(--blue-100);
    border: 1px solid var(--blue-200);
    color: var(--blue-700);
}

.dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
}
.dot-critical { background-color: var(--accent-critical); box-shadow: 0 0 4px var(--accent-critical); }
.dot-high     { background-color: var(--accent-high); }
.dot-medium   { background-color: var(--accent-medium); }
.dot-low      { background-color: var(--accent-low); }
.dot-clean    { background-color: var(--accent-clean); }

/* Suspect Cards for Empty State */
.suspect-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 14px;
    margin: 24px 0;
}

.suspect-card {
    background: var(--blue-100);
    border: 1px solid var(--blue-200);
    border-radius: var(--radius-lg);
    padding: 18px;
    text-align: left;
    transition: var(--transition);
}

.suspect-card:hover {
    border-color: var(--blue-300);
    transform: translateY(-2px);
    box-shadow: var(--shadow-hover);
}

/* Gemma Reading Box */
.reading-box {
    background: #FFFFFF;
    border: 1px solid var(--blue-200);
    border-left: 3px solid var(--blue-500);
    border-radius: var(--radius-sm);
    padding: 12px 16px;
    margin-top: 14px;
}

.suggested-fix-box {
    background: #FFFFFF;
    border: 1px solid var(--blue-200);
    border-left: 3px solid var(--accent-clean);
    border-radius: var(--radius-sm);
    padding: 10px 14px;
    margin-top: 10px;
}

/* Streamlit Tabs Customization */
div[data-testid="stTabs"] button[role="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    border-bottom: 2px solid transparent !important;
    padding: 8px 16px !important;
    background: transparent !important;
}

div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--blue-900) !important;
    border-bottom: 2px solid var(--blue-500) !important;
}

/* Streamlit Status Box Override */
[data-testid="stStatusWidget"] {
    background-color: var(--blue-50) !important;
    border: 1px solid var(--blue-200) !important;
    border-radius: var(--radius-md) !important;
}

/* Dataframe Overrides */
[data-testid="stDataFrame"] {
    border: 1px solid var(--blue-200) !important;
    border-radius: var(--radius-md) !important;
}

/* Animations */
@keyframes fadeInSlideUp {
    from {
        opacity: 0;
        transform: translateY(6px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-in {
    animation: fadeInSlideUp 200ms cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>
"""


def inject_theme():
    """Injects central royal blue light theme stylesheet."""
    st.markdown(THEME_CSS, unsafe_allow_html=True)
