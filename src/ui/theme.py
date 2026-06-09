from __future__ import annotations

from html import escape
from textwrap import dedent

import streamlit as st

from src.config import APP_TITLE


LANGUAGES = ["English", "Hindi", "Kannada", "Marathi", "Tamil", "Telugu"]


def setup_page(page_title: str) -> None:
    try:
        st.set_page_config(page_title=f"{page_title} | {APP_TITLE}", page_icon="🌾", layout="wide")
    except st.errors.StreamlitAPIException:
        pass
    apply_theme()


def apply_theme() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

            /* ═══════════════ DESIGN TOKENS ═══════════════ */
            :root {
                --mm-green:       #1b8a3a;
                --mm-green-dark:  #0d4a20;
                --mm-green-light: #27ae4f;
                --mm-green-soft:  #e6f7eb;
                --mm-green-glow:  rgba(27,138,58,0.14);

                --mm-gold:        #d4920a;
                --mm-gold-soft:   #fef7e6;

                --mm-blue:        #1565c0;
                --mm-blue-soft:   #e3f0fd;

                --mm-red:         #c0392b;
                --mm-red-soft:    #fdecea;

                --mm-ink:         #111d14;
                --mm-ink-2:       #2d3f32;
                --mm-muted:       #5e7963;
                --mm-line:        #cddcd0;
                --mm-bg:          #f0f6ee;
                --mm-card:        #ffffff;

                --mm-radius:      14px;
                --mm-radius-sm:   10px;

                --mm-shadow-xs:   0 1px 2px rgba(13,74,32,0.05);
                --mm-shadow-sm:   0 2px 6px rgba(13,74,32,0.07);
                --mm-shadow-md:   0 6px 20px rgba(13,74,32,0.09);
                --mm-shadow-lg:   0 12px 36px rgba(13,74,32,0.12);

                --mm-transition:  0.24s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            }

            /* ═══════════════ ANIMATIONS ═══════════════ */
            @keyframes mmSlideUp {
                from { opacity: 0; transform: translateY(16px); }
                to   { opacity: 1; transform: translateY(0); }
            }
            @keyframes mmSlideRight {
                from { opacity: 0; transform: translateX(-12px); }
                to   { opacity: 1; transform: translateX(0); }
            }
            @keyframes mmScaleIn {
                from { opacity: 0; transform: scale(0.96); }
                to   { opacity: 1; transform: scale(1); }
            }
            @keyframes mmGradientShift {
                0%   { background-position: 0% 50%; }
                50%  { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }

            /* ═══════════════ GLOBAL ═══════════════ */
            .stApp {
                background: var(--mm-bg);
                background-image:
                    radial-gradient(circle at 1px 1px, rgba(27,138,58,0.025) 1px, transparent 0);
                background-size: 32px 32px;
                color: var(--mm-ink);
                font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
            }

            body, p, span, div, li, td, th, input, select, textarea, button, a, label,
            h1, h2, h3, h4, h5, h6 {
                font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
            }

            /* ═══════════════ SIDEBAR ═══════════════ */
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #ffffff 0%, #f5faf2 50%, #edf5ea 100%);
                border-right: 1px solid var(--mm-line);
                box-shadow: 2px 0 12px rgba(13,74,32,0.03);
                min-width: 280px;
            }

            section[data-testid="stSidebar"] h1,
            section[data-testid="stSidebar"] h2,
            section[data-testid="stSidebar"] h3 {
                color: var(--mm-green-dark);
                font-weight: 800;
                font-size: 0.95rem;
                letter-spacing: -0.01em;
                position: relative;
                padding-left: 16px;
                margin-top: 8px;
                margin-bottom: 6px;
            }

            section[data-testid="stSidebar"] p {
                font-size: 0.82rem;
                line-height: 1.5;
                color: var(--mm-muted);
            }

            /* Sidebar info sections */
            section[data-testid="stSidebar"] .block-container {
                padding: 1rem 0.8rem;
            }

            section[data-testid="stSidebar"] h3::before {
                content: '';
                position: absolute;
                left: 0;
                top: 3px;
                bottom: 3px;
                width: 4px;
                border-radius: 3px;
                background: linear-gradient(180deg, var(--mm-green) 0%, var(--mm-gold) 100%);
            }

            section[data-testid="stSidebar"] hr {
                border: none;
                height: 2px;
                background: linear-gradient(90deg, transparent, var(--mm-line), transparent);
                margin: 14px 0;
            }

            section[data-testid="stSidebar"] .stCaption p {
                font-size: 0.82rem;
                line-height: 1.55;
                color: var(--mm-muted);
            }

            /* ═══════════════ TYPOGRAPHY ═══════════════ */
            h1, h2, h3 {
                color: var(--mm-green-dark);
                letter-spacing: -0.02em;
                font-weight: 800;
            }

            h1 { font-size: clamp(1.5rem, 2.5vw, 2.1rem); line-height: 1.2; }
            h2 { font-size: 1.2rem; }
            h3 { font-size: 1.05rem; }

            /* ═══════════════ BLOCK CONTAINER ═══════════════ */
            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
                max-width: 1360px;
            }

            /* ═══════════════ HERO BANNER ═══════════════ */
            .mm-hero {
                background: linear-gradient(135deg,
                    rgba(27,138,58,0.08) 0%,
                    rgba(212,146,10,0.06) 40%,
                    rgba(21,101,192,0.04) 100%);
                backdrop-filter: blur(1px);
                border: 1px solid rgba(27,138,58,0.15);
                border-radius: var(--mm-radius);
                padding: clamp(22px, 3vw, 32px) clamp(24px, 3vw, 36px);
                margin-bottom: 24px;
                box-shadow: var(--mm-shadow-md), inset 0 1px 0 rgba(255,255,255,0.7);
                animation: mmSlideUp 0.45s ease-out both;
                position: relative;
                overflow: hidden;
            }

            .mm-hero::before {
                content: '';
                position: absolute;
                top: 0; right: 0;
                width: 320px;
                height: 100%;
                background: radial-gradient(ellipse at top right,
                    rgba(27,138,58,0.08) 0%,
                    transparent 65%);
                pointer-events: none;
            }

            .mm-hero::after {
                content: '';
                position: absolute;
                bottom: -20px; left: -20px;
                width: 180px;
                height: 180px;
                background: radial-gradient(circle,
                    rgba(212,146,10,0.06) 0%,
                    transparent 60%);
                pointer-events: none;
            }

            .mm-eyebrow {
                color: var(--mm-green);
                font-size: 0.8rem;
                font-weight: 800;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .mm-eyebrow::before {
                content: '🌾';
                font-size: 1rem;
            }

            .mm-hero h1 {
                font-size: clamp(1.5rem, 3vw, 2.3rem);
                line-height: 1.15;
                margin: 0;
                font-weight: 900;
                color: var(--mm-green-dark);
                position: relative;
                z-index: 1;
            }

            .mm-hero p {
                color: var(--mm-muted);
                font-size: 0.96rem;
                max-width: 860px;
                margin: 10px 0 0 0;
                line-height: 1.65;
                position: relative;
                z-index: 1;
            }

            /* ═══════════════ METRIC CARDS ═══════════════ */
            .mm-metric {
                background: var(--mm-card);
                border: 1px solid var(--mm-line);
                border-radius: var(--mm-radius);
                padding: 14px 16px 12px;
                height: 160px;
                box-shadow: var(--mm-shadow-sm);
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                transition: all var(--mm-transition);
                animation: mmScaleIn 0.35s ease-out both;
                position: relative;
                overflow: hidden;
            }

            .mm-metric::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 100%;
                opacity: 0;
                transition: opacity var(--mm-transition);
                pointer-events: none;
                background: linear-gradient(135deg,
                    rgba(27,138,58,0.02) 0%,
                    transparent 100%);
            }

            .mm-metric:hover {
                transform: translateY(-4px);
                box-shadow: var(--mm-shadow-lg);
                border-color: rgba(27,138,58,0.25);
            }

            .mm-metric:hover::after {
                opacity: 1;
            }

            .mm-metric.green {
                border-top: 5px solid var(--mm-green);
            }
            .mm-metric.gold {
                border-top: 5px solid var(--mm-gold);
            }
            .mm-metric.blue {
                border-top: 5px solid var(--mm-blue);
            }
            .mm-metric.red {
                border-top: 5px solid var(--mm-red);
            }

            .mm-metric-label {
                color: var(--mm-muted);
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.07em;
                margin-bottom: 6px;
            }

            .mm-metric-value {
                color: var(--mm-ink);
                font-size: 1.1rem;
                line-height: 1.3;
                font-weight: 900;
                word-break: break-word;
            }

            .mm-metric-caption {
                color: var(--mm-muted);
                font-size: 0.8rem;
                margin-top: auto;
                padding-top: 6px;
                line-height: 1.4;
                border-top: 1px solid rgba(205,220,208,0.5);
            }

            /* ═══════════════ SECTION HEADER ═══════════════ */
            .mm-section {
                margin: 28px 0 14px 0;
                animation: mmSlideRight 0.3s ease-out both;
            }

            .mm-section h2 {
                font-size: 1.2rem;
                margin-bottom: 4px;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .mm-section h2::before {
                content: '';
                display: inline-block;
                width: 5px;
                height: 1.15em;
                border-radius: 3px;
                background: linear-gradient(180deg, var(--mm-green) 0%, var(--mm-green-light) 100%);
                flex-shrink: 0;
            }

            .mm-section p {
                color: var(--mm-muted);
                margin: 0;
                font-size: 0.9rem;
                padding-left: 15px;
                line-height: 1.5;
            }

            /* ═══════════════ ADVISORY CARD ═══════════════ */
            .mm-advisory {
                background: var(--mm-card);
                border: 1px solid var(--mm-line);
                border-left: 6px solid var(--mm-green);
                border-radius: var(--mm-radius);
                padding: 22px 24px;
                margin-bottom: 16px;
                box-shadow: var(--mm-shadow-md);
                transition: all var(--mm-transition);
                animation: mmSlideUp 0.4s ease-out both;
                position: relative;
                overflow: hidden;
            }

            .mm-advisory::before {
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0;
                height: 4px;
                background: linear-gradient(90deg,
                    var(--mm-green) 0%,
                    var(--mm-green-light) 50%,
                    var(--mm-gold) 100%);
                opacity: 0.6;
            }

            .mm-advisory:hover {
                transform: translateY(-3px);
                box-shadow: var(--mm-shadow-lg);
            }

            .mm-advisory h3 {
                margin: 4px 0 12px 0;
                font-size: 1.2rem;
                color: var(--mm-green-dark);
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .mm-advisory h3::before {
                content: '📋';
                font-size: 1.1rem;
            }

            .mm-advisory p {
                margin: 7px 0;
                color: var(--mm-ink-2);
                font-size: 0.93rem;
                line-height: 1.6;
            }

            .mm-advisory p strong {
                color: var(--mm-ink);
                font-weight: 700;
            }

            /* ═══════════════ PILL BADGES ═══════════════ */
            .mm-pill {
                display: inline-flex;
                align-items: center;
                border-radius: 999px;
                padding: 3px 12px;
                font-size: 0.76rem;
                font-weight: 800;
                letter-spacing: 0.03em;
                border: 1.5px solid;
                box-shadow: var(--mm-shadow-xs);
                transition: transform var(--mm-transition);
            }

            .mm-pill:hover { transform: scale(1.06); }

            .mm-pill.low {
                color: #15803d;
                background: #dcfce7;
                border-color: #86efac;
            }
            .mm-pill.medium {
                color: #b45309;
                background: #fef3c7;
                border-color: #fcd34d;
            }
            .mm-pill.high {
                color: #b91c1c;
                background: #fee2e2;
                border-color: #fca5a5;
            }

            /* ═══════════════ GENERIC CARD ═══════════════ */
            .mm-card {
                background: var(--mm-card);
                border: 1px solid var(--mm-line);
                border-radius: var(--mm-radius);
                padding: 20px;
                box-shadow: var(--mm-shadow-sm);
                transition: all var(--mm-transition);
            }

            .mm-card:hover {
                transform: translateY(-2px);
                box-shadow: var(--mm-shadow-md);
            }

            .mm-card h3 { font-size: 1.05rem; margin: 0 0 8px 0; }
            .mm-card p { color: var(--mm-muted); margin: 0 0 8px 0; }

            .mm-small-muted {
                color: var(--mm-muted);
                font-size: 0.88rem;
            }

            /* ═══════════════ STREAMLIT METRIC WIDGET ═══════════════ */
            div[data-testid="stMetric"] {
                background: var(--mm-card);
                border: 1px solid var(--mm-line);
                border-left: 5px solid var(--mm-green);
                border-radius: var(--mm-radius);
                padding: 16px 20px 14px;
                box-shadow: var(--mm-shadow-sm);
                transition: all var(--mm-transition);
            }

            div[data-testid="stMetric"]:hover {
                transform: translateY(-2px);
                box-shadow: var(--mm-shadow-md);
            }

            /* ═══════════════ DATAFRAMES ═══════════════ */
            div[data-testid="stDataFrame"] {
                border: 1px solid var(--mm-line);
                border-radius: var(--mm-radius);
                overflow: hidden;
                box-shadow: var(--mm-shadow-xs);
            }

            div[data-testid="stDataFrame"] [data-testid="stDataFrameResizable"] {
                border-radius: var(--mm-radius);
            }

            div[data-testid="stDataFrame"] ::-webkit-scrollbar { width: 6px; height: 6px; }
            div[data-testid="stDataFrame"] ::-webkit-scrollbar-track {
                background: var(--mm-green-soft); border-radius: 4px;
            }
            div[data-testid="stDataFrame"] ::-webkit-scrollbar-thumb {
                background: var(--mm-line); border-radius: 4px;
            }
            div[data-testid="stDataFrame"] ::-webkit-scrollbar-thumb:hover {
                background: var(--mm-muted);
            }

            /* ═══════════════ BUTTONS ═══════════════ */
            .stButton > button,
            .stDownloadButton > button {
                border-radius: var(--mm-radius-sm);
                border: 1.5px solid var(--mm-green);
                font-weight: 700;
                font-size: 0.88rem;
                padding: 0.55rem 1.6rem;
                min-height: 42px;
                transition: all var(--mm-transition);
                letter-spacing: 0.01em;
                cursor: pointer;
                background: var(--mm-card);
                color: var(--mm-green-dark);
            }

            .stButton > button:hover,
            .stDownloadButton > button:hover {
                background: linear-gradient(135deg, var(--mm-green) 0%, var(--mm-green-dark) 100%);
                border-color: var(--mm-green);
                color: #fff;
                box-shadow: 0 4px 16px rgba(27,138,58,0.3);
                transform: translateY(-2px);
            }

            .stButton > button:active,
            .stDownloadButton > button:active {
                transform: translateY(0);
                box-shadow: 0 2px 6px rgba(27,138,58,0.2);
            }

            .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, var(--mm-green) 0%, var(--mm-green-dark) 100%);
                color: #fff;
                border-color: var(--mm-green);
                box-shadow: 0 3px 12px rgba(27,138,58,0.2);
            }

            .stButton > button[kind="primary"]:hover {
                box-shadow: 0 6px 24px rgba(27,138,58,0.35);
                transform: translateY(-2px);
            }

            /* ═══════════════ PAGE LINKS ═══════════════ */
            div[data-testid="stPageLink"] a {
                background: var(--mm-card);
                border: 1.5px solid var(--mm-line);
                border-left: 4px solid transparent;
                border-radius: var(--mm-radius-sm);
                padding: 0.65rem 1rem 0.65rem 1.15rem;
                font-weight: 700;
                font-size: 0.88rem;
                transition: all var(--mm-transition);
                display: flex;
                align-items: center;
                color: var(--mm-ink-2);
            }

            div[data-testid="stPageLink"] a:hover {
                border-left-color: var(--mm-green);
                color: var(--mm-green-dark);
                background: var(--mm-green-soft);
                transform: translateX(4px);
                box-shadow: var(--mm-shadow-sm);
            }

            /* ═══════════════ INPUTS ═══════════════ */
            div[data-testid="stTextInput"] input,
            div[data-testid="stNumberInput"] input,
            div[data-testid="stSelectbox"] [data-baseweb="select"],
            div[data-testid="stMultiSelect"] [data-baseweb="select"] {
                border-radius: var(--mm-radius-sm) !important;
                border-color: var(--mm-line) !important;
                transition: border-color var(--mm-transition), box-shadow var(--mm-transition);
            }

            div[data-testid="stTextInput"] input:focus,
            div[data-testid="stNumberInput"] input:focus {
                border-color: var(--mm-green) !important;
                box-shadow: 0 0 0 2px var(--mm-green-glow) !important;
            }

            /* ═══════════════ CHECKBOXES ═══════════════ */
            div[data-testid="stCheckbox"] label {
                font-weight: 600;
                font-size: 0.9rem;
            }

            /* ═══════════════ RADIO BUTTONS ═══════════════ */
            div[data-testid="stRadio"] label {
                font-weight: 600;
                font-size: 0.88rem;
            }

            /* ═══════════════ SLIDER ═══════════════ */
            div[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
                background: var(--mm-green) !important;
            }

            /* ═══════════════ EXPANDER ═══════════════ */
            details[data-testid="stExpander"] {
                border: 1px solid var(--mm-line);
                border-radius: var(--mm-radius);
                background: var(--mm-card);
                box-shadow: var(--mm-shadow-xs);
                transition: box-shadow var(--mm-transition);
            }

            details[data-testid="stExpander"]:hover {
                box-shadow: var(--mm-shadow-sm);
            }

            details[data-testid="stExpander"] summary {
                font-weight: 700;
                color: var(--mm-ink-2);
            }

            /* ═══════════════ ALERTS ═══════════════ */
            div[data-testid="stAlert"] {
                border-radius: var(--mm-radius-sm);
                border: none;
                box-shadow: var(--mm-shadow-xs);
                font-size: 0.9rem;
            }

            /* ═══════════════ SPINNER ═══════════════ */
            .stSpinner > div {
                border-top-color: var(--mm-green) !important;
            }

            /* ═══════════════ TABS ═══════════════ */
            .stTabs [data-baseweb="tab-list"] { gap: 4px; }
            .stTabs [data-baseweb="tab"] {
                border-radius: 8px 8px 0 0;
                padding: 8px 22px;
                font-weight: 600;
                transition: background var(--mm-transition);
            }

            /* ═══════════════ PLOTLY CHARTS CONTAINER ═══════════════ */
            div[data-testid="stPlotlyChart"] {
                border-radius: var(--mm-radius);
                overflow: hidden;
                box-shadow: var(--mm-shadow-xs);
                border: 1px solid rgba(205,220,208,0.6);
                background: var(--mm-card);
            }

            /* ═══════════════ COLUMN GAPS & EQUAL HEIGHT ═══════════════ */
            div[data-testid="stHorizontalBlock"] {
                gap: 14px;
                align-items: stretch;
            }

            /* ═══════════════ MARKDOWN LISTS ═══════════════ */
            .stMarkdown ul {
                padding-left: 1.2rem;
            }

            .stMarkdown li {
                margin-bottom: 4px;
                line-height: 1.55;
                font-size: 0.92rem;
            }

            /* ═══════════════ SIDEBAR PAGE LINKS ═══════════════ */
            section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {
                font-size: 0.88rem;
                padding: 6px 12px;
                border-radius: 8px;
                transition: background var(--mm-transition);
            }

            section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover {
                background: var(--mm-green-soft);
            }

            section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"] {
                background: var(--mm-green-soft);
                font-weight: 700;
                color: var(--mm-green-dark);
            }

            /* ═══════════════ DARK MODE ═══════════════ */
            @media (prefers-color-scheme: dark) {
                :root {
                    --mm-bg:          #0c1710;
                    --mm-card:        #141f17;
                    --mm-ink:         #dce8df;
                    --mm-ink-2:       #b0c5b5;
                    --mm-muted:       #7d9a84;
                    --mm-line:        #243a29;
                    --mm-green-soft:  #162b1c;
                    --mm-green-glow:  rgba(27,138,58,0.2);
                    --mm-shadow-xs:   0 1px 2px rgba(0,0,0,0.15);
                    --mm-shadow-sm:   0 2px 6px rgba(0,0,0,0.2);
                    --mm-shadow-md:   0 6px 20px rgba(0,0,0,0.25);
                    --mm-shadow-lg:   0 12px 36px rgba(0,0,0,0.3);
                }
            }

            [data-theme="dark"] {
                --mm-bg:          #0c1710;
                --mm-card:        #141f17;
                --mm-ink:         #dce8df;
                --mm-ink-2:       #b0c5b5;
                --mm-muted:       #7d9a84;
                --mm-line:        #243a29;
                --mm-green-soft:  #162b1c;
                --mm-green-glow:  rgba(27,138,58,0.2);
                --mm-shadow-xs:   0 1px 2px rgba(0,0,0,0.15);
                --mm-shadow-sm:   0 2px 6px rgba(0,0,0,0.2);
                --mm-shadow-md:   0 6px 20px rgba(0,0,0,0.25);
                --mm-shadow-lg:   0 12px 36px rgba(0,0,0,0.3);
            }

            [data-theme="dark"] section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #141f17 0%, #0c1710 100%);
                border-right-color: var(--mm-line);
            }

            /* ═══════════════ HIDE STREAMLIT CHROME ═══════════════ */
            footer, #MainMenu { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str, eyebrow: str = "MarketMitra AI") -> None:
    st.markdown(
        dedent(
            f"""
        <div class="mm-hero">
            <div class="mm-eyebrow">{escape(eyebrow)}</div>
            <h1>{escape(title)}</h1>
            <p>{escape(subtitle)}</p>
        </div>
        """,
        ).strip(),
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = "") -> None:
    sub_html = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        dedent(
            f"""
        <div class="mm-section">
            <h2>{escape(title)}</h2>
            {sub_html}
        </div>
        """,
        ).strip(),
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, caption: str = "", accent: str = "green") -> None:
    # Truncate long values so they never overflow the card
    display_value = value if len(value) <= 22 else value[:20] + "…"
    caption_html = f'<div class="mm-metric-caption">{escape(caption)}</div>' if caption else ""
    st.markdown(
        dedent(
            f"""
        <div class="mm-metric {escape(accent)}" style="height:160px;min-height:160px;max-height:160px;box-sizing:border-box;">
            <div class="mm-metric-label">{escape(label)}</div>
            <div class="mm-metric-value" style="font-size:1.1rem;line-height:1.35;overflow:hidden;">{escape(display_value)}</div>
            {caption_html}
        </div>
        """,
        ).strip(),
        unsafe_allow_html=True,
    )


def advisory_card(
    action: str,
    market: str,
    gain: float,
    risk: str,
    confidence: float,
    current_price: float | None = None,
    forecast_price: float | None = None,
) -> None:
    price_lines: list[str] = []
    if current_price is not None:
        price_lines.append(f"<p>Current price: <strong>{escape(money(current_price))}/qtl</strong></p>")
    if forecast_price is not None:
        price_lines.append(f"<p>Forecast/reference price: <strong>{escape(money(forecast_price))}/qtl</strong></p>")
    html = "\n".join(
        [
            '<div class="mm-advisory">',
            f"<h3>{escape(action)}</h3>",
            f"<p>Recommended market: <strong>{escape(market)}</strong></p>",
            *price_lines,
            f"<p>Expected net gain: <strong>{escape(money(gain))}/qtl</strong></p>",
            f"<p>Risk: {risk_badge(risk)} &nbsp; Confidence: <strong>{int(confidence * 100)}%</strong></p>",
            "</div>",
        ]
    )
    st.markdown(
        html,
        unsafe_allow_html=True,
    )


def risk_class(risk: str) -> str:
    return {
        "Low": "low",
        "Medium": "medium",
        "High": "high",
    }.get(risk, "medium")


def risk_badge(risk: str) -> str:
    return f'<span class="mm-pill {risk_class(risk)}">{escape(risk)}</span>'


def money(value: float | int | None) -> str:
    if value is None:
        return "INR 0"
    return f"INR {float(value):,.0f}"


def pct(value: float | int | None) -> str:
    if value is None:
        return "0.0%"
    return f"{float(value):+.1f}%"
