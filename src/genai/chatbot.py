from __future__ import annotations

import re

from src.genai.report_generator import _generate_with_gemini_result, _generate_with_groq_result
from src.recommendations.strategy_engine import SellingRecommendation


def _extract_comparable_mandis(extra_context: str, current_price: float) -> list[str]:
    """Parse comparable mandi data from analytics context and RAG-retrieved documents."""
    insights: list[str] = []

    # Parse "Top comparable mandis" section from analytics context
    mandi_pattern = re.compile(
        r"- (.+?):\s*avg INR ([\d.]+)/quintal,\s*latest INR ([\d.]+)/quintal"
    )
    for match in mandi_pattern.finditer(extra_context):
        mandi_name = match.group(1).strip()
        avg_price = float(match.group(2))
        latest_price = float(match.group(3))
        if latest_price > current_price:
            insights.append(
                f"{mandi_name}: latest **INR {latest_price:,.0f}**/qtl (avg INR {avg_price:,.0f}/qtl)"
            )

    # Parse RAG-retrieved documents
    rag_doc_pattern = re.compile(
        r"Market/Mandi:\s*(.+?)\n.*?"
        r"Latest modal price:\s*INR ([\d.]+).*?"
        r"Average modal price:\s*INR ([\d.]+)",
        re.DOTALL,
    )
    seen = {m.split(":")[0] for m in insights}
    for match in rag_doc_pattern.finditer(extra_context):
        mandi_name = match.group(1).strip()
        latest_price = float(match.group(2))
        avg_price = float(match.group(3))
        if mandi_name not in seen and latest_price > current_price:
            insights.append(
                f"{mandi_name}: latest **INR {latest_price:,.0f}**/qtl (avg INR {avg_price:,.0f}/qtl)"
            )
            seen.add(mandi_name)

    return insights[:6]


def answer_market_question(
    question: str,
    commodity: str,
    market: str,
    summary: dict,
    forecast: dict,
    market_pressure: dict,
    recommendation: SellingRecommendation,
    use_llm: bool = False,
    provider: str = "Groq",
    language: str = "English",
    extra_context: str = "",
) -> str:
    current_price = summary.get("current_price", 0)

    # Always extract comparable mandis from RAG context
    comparable_mandis = _extract_comparable_mandis(extra_context, current_price) if extra_context else []

    # Build mandi section for the prompt
    mandi_section = ""
    if comparable_mandis:
        mandi_lines = "\n".join(f"  - {m}" for m in comparable_mandis)
        mandi_section = f"""
COMPARABLE MANDIS WITH HIGHER PRICES:
{mandi_lines}
"""

    context = f"""
Commodity: {commodity}
Market: {market}
Current price: INR {current_price}/quintal
30-day average: INR {summary.get('avg_30d')}/quintal
7-day forecast: INR {forecast.get('forecast_price')}/quintal
Forecast trend: {forecast.get('forecast_trend')}
Market pressure: {market_pressure.get('pressure')}
Recommendation: {recommendation.action}
Recommended market: {recommendation.recommended_market}
Expected net gain: INR {recommendation.expected_net_gain}/quintal
Risk: {recommendation.risk_level}
Confidence: {int(recommendation.confidence_score * 100)}%
Reasons: {'; '.join(recommendation.reasoning)}
{mandi_section}
"""

    prompt = f"""You are MarketMitra AI, an agricultural market advisory assistant for Indian farmers.
Answer the farmer's question using ONLY the context below.

CONTEXT:
{context}

QUESTION: {question}

Answer in {language} in 4-6 sentences. Cite actual INR prices and mandi names.
Do NOT invent any data not present above.
"""

    # Try LLM first
    llm_answer = ""
    if use_llm:
        if provider.lower().startswith("gemini"):
            result = _generate_with_gemini_result(prompt)
        else:
            result = _generate_with_groq_result(prompt)
        if result.text:
            llm_answer = result.text

    # Build answer: either LLM or deterministic fallback
    if llm_answer:
        answer = llm_answer.strip()
    else:
        answer = (
            f"For **{commodity}** in **{market}**, the current modal price is "
            f"**INR {current_price:,.0f}/quintal** and the 7-day forecast is "
            f"**INR {forecast.get('forecast_price'):,.0f}/quintal** with a "
            f"**{forecast.get('forecast_trend', 'unknown').lower()}** trend. "
            f"The recommended action is **{recommendation.action}** — "
            f"expected net gain of **INR {recommendation.expected_net_gain:,.0f}/quintal** "
            f"after transport cost. "
            f"{recommendation.reasoning[0]} "
            f"Risk level: **{recommendation.risk_level}** "
            f"(confidence: {int(recommendation.confidence_score * 100)}%)."
        )

    # ALWAYS append comparable mandis section regardless of LLM or fallback
    if comparable_mandis:
        answer += (
            "\n\n---\n📊 **Comparable mandis with higher prices** *(from RAG knowledge base)*:\n"
            + "\n".join(f"- {item}" for item in comparable_mandis)
        )

    return answer
