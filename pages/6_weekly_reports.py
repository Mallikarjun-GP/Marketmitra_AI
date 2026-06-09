from __future__ import annotations

import streamlit as st

from src.genai.pdf_export import report_to_pdf_bytes
from src.genai.report_generator import generate_market_report_with_status, get_provider_status
from src.genai.report_store import save_report_pdf, save_report_text
from src.ui.dashboard_state import build_market_context
from src.ui.theme import LANGUAGES, page_header, section_header, setup_page


setup_page("Weekly Reports")
ctx = build_market_context()

page_header(
    "Weekly Market Intelligence Reports",
    "Generate judge-ready market reports using deterministic templates or live GenAI providers, then download as Markdown or PDF.",
)

provider_status = get_provider_status()
section_header("Report Generator", "Choose provider and language.")
status_col, provider_col, language_col = st.columns([1.2, 1, 1])
with status_col:
    st.caption(
        "API status: "
        f"Groq={'configured' if provider_status['Groq'] else 'missing'}, "
        f"Gemini={'configured' if provider_status['Gemini'] else 'missing'}"
    )
with provider_col:
    provider = st.radio("Report generator", ["Template", "Groq", "Gemini"], horizontal=True, key="report_provider")
with language_col:
    report_language = st.selectbox("Report language", LANGUAGES, index=0, key="report_language")

report_result = generate_market_report_with_status(
    commodity=ctx.selected_commodity,
    state=ctx.selected_state,
    district=ctx.selected_district,
    market=ctx.selected_market,
    summary=ctx.summary,
    forecast=ctx.forecast_info,
    market_pressure=ctx.market_pressure,
    recommendation=ctx.recommendation,
    provider=provider,
    language=report_language,
)
report = report_result.text or ""

if report_result.used_api:
    st.success(f"Generated using {report_result.provider} API model `{report_result.model}`.")
elif report_result.error:
    st.warning(f"Using offline template. {report_result.provider} API issue: {report_result.error}")
else:
    st.info("Using offline template report.")

section_header("Generated Report", ctx.selected_label)
st.markdown(report)

pdf_bytes = report_to_pdf_bytes(f"MarketMitra AI - {ctx.selected_commodity} Report", report)

dl_md, dl_pdf, sv_md, sv_pdf = st.columns(4)
with dl_md:
    st.download_button(
        label="📥 Download Markdown",
        data=report,
        file_name=f"marketmitra_{ctx.selected_commodity}_{ctx.selected_market}_report.md".replace(" ", "_").lower(),
        mime="text/markdown",
    )
with dl_pdf:
    if pdf_bytes:
        st.download_button(
            label="📄 Download PDF",
            data=pdf_bytes,
            file_name=f"marketmitra_{ctx.selected_commodity}_{ctx.selected_market}_report.pdf".replace(" ", "_").lower(),
            mime="application/pdf",
        )
    else:
        st.caption("Install reportlab for PDF export")
with sv_md:
    if st.button("💾 Save Report", key="save_report_text"):
        saved_path = save_report_text(ctx.selected_commodity, ctx.selected_market, report_result.provider, report)
        st.success(f"Saved: {saved_path}")
with sv_pdf:
    if pdf_bytes and st.button("💾 Save PDF", key="save_report_pdf"):
        saved_pdf_path = save_report_pdf(ctx.selected_commodity, ctx.selected_market, report_result.provider, pdf_bytes)
        st.success(f"Saved: {saved_pdf_path}")
