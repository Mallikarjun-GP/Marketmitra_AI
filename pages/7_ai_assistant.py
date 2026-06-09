from __future__ import annotations

import streamlit as st

from src.genai.chatbot import answer_market_question
from src.genai.context_builder import build_market_context as build_text_market_context
from src.genai.rag_store import build_market_documents, format_rag_matches
from src.genai.report_generator import get_provider_status
from src.ui.dashboard_state import build_market_context, get_rag_store
from src.ui.theme import LANGUAGES, page_header, section_header, setup_page


setup_page("AI Assistant")
ctx = build_market_context()

page_header(
    "AI Market Assistant",
    "Ask grounded market questions using current analytics plus optional ChromaDB vector-store retrieval.",
)

provider_status = get_provider_status()
section_header("Assistant Controls", "The assistant stays grounded in selected mandi data and retrieved market context.")
provider_col, language_col, toggle_col1, toggle_col2 = st.columns(4)
with provider_col:
    chat_provider = st.selectbox("Provider", ["Groq", "Gemini"], index=0, key="assistant_provider")
with language_col:
    chat_language = st.selectbox("Language", LANGUAGES, index=0, key="assistant_language")
with toggle_col1:
    use_live_llm = st.checkbox("🔗 Use live GenAI", value=True, key="assistant_use_live_llm")
with toggle_col2:
    use_rag = st.checkbox("🧠 Use ChromaDB RAG", value=True, key="assistant_use_rag")

rag_text = ""
rag_store = None
if use_rag:
    try:
        rag_store = get_rag_store()
        rag_count = rag_store.count()
        st.caption(f"ChromaDB RAG index documents: {rag_count}")
        build_col, _ = st.columns([1, 2])
        with build_col:
            if st.button("🔄 Build / refresh RAG index", key="build_rag_index"):
                with st.spinner("Building ChromaDB RAG index from forecast-ready market series..."):
                    docs = build_market_documents(ctx.df_full, min_dates=90, limit=500)
                    rag_store.reset()
                    inserted = rag_store.upsert_documents(docs)
                st.success(f"Built RAG index with {inserted} documents.")
                get_rag_store.clear()
                rag_store = get_rag_store()
    except Exception as exc:
        st.warning(f"ChromaDB RAG unavailable: {exc}")
        rag_store = None

q_col, btn_col = st.columns([4, 1])
with q_col:
    question = st.text_input(
        "Ask your question",
        value=f"Should I sell {ctx.selected_commodity} today or wait?",
        key="assistant_question",
    )
with btn_col:
    st.markdown("<br>", unsafe_allow_html=True)
    ask_question = st.button("🚀 Generate", type="primary", key="assistant_generate_answer")

if question and ask_question:
    retrieved_context = build_text_market_context(
        commodity=ctx.selected_commodity,
        state=ctx.selected_state,
        district=ctx.selected_district,
        market=ctx.selected_market,
        summary=ctx.summary,
        forecast=ctx.forecast_info,
        market_pressure=ctx.market_pressure,
        recommendation=ctx.recommendation,
        market_comparison=ctx.market_comparison,
    )
    if use_rag and rag_store is not None and rag_store.count() > 0:
        matches = rag_store.query(
            question=question,
            commodity=ctx.selected_commodity,
            state=ctx.selected_state,
            n_results=4,
        )
        rag_text = format_rag_matches(matches)
        retrieved_context = f"{retrieved_context}\n\nVector-store retrieved market knowledge:\n{rag_text}"

    if use_live_llm and not provider_status.get(chat_provider, False):
        st.warning(f"{chat_provider} API key is not configured. Using deterministic fallback answer.")

    answer = answer_market_question(
        question=question,
        commodity=ctx.selected_commodity,
        market=ctx.selected_market,
        summary=ctx.summary,
        forecast=ctx.forecast_info,
        market_pressure=ctx.market_pressure,
        recommendation=ctx.recommendation,
        use_llm=use_live_llm and provider_status.get(chat_provider, False),
        provider=chat_provider,
        language=chat_language,
        extra_context=retrieved_context,
    )
    section_header("MarketMitra Answer")
    st.markdown(answer)
    with st.expander("Retrieved market context used by assistant"):
        st.code(retrieved_context)
elif question:
    st.info("Click Generate answer to ask the assistant using the selected market context.")
