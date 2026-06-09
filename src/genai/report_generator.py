from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date

from dotenv import load_dotenv

from src.recommendations.strategy_engine import SellingRecommendation

load_dotenv()


@dataclass
class GenAIResult:
    text: str | None
    provider: str
    model: str
    used_api: bool
    error: str | None = None


def get_provider_status() -> dict[str, bool]:
    return {
        "Groq": bool(os.getenv("GROQ_API_KEY")),
        "Gemini": bool(os.getenv("GEMINI_API_KEY")),
    }


def build_report_prompt(
    commodity: str,
    state: str,
    district: str,
    market: str,
    summary: dict,
    forecast: dict,
    market_pressure: dict,
    recommendation: SellingRecommendation,
    language: str = "English",
) -> str:
    evidence = "; ".join(recommendation.reasoning + market_pressure.get("reasons", []))
    return f"""You are an agricultural market intelligence analyst helping Indian farmers.

Use only the structured data below. Do not invent prices, dates, mandi names, policies, or guarantees.

Commodity: {commodity}
Location: {market}, {district}, {state}
Report date: {date.today().isoformat()}
Current modal price: INR {summary.get('current_price')}/quintal
30-day average: INR {summary.get('avg_30d')}/quintal
Week-over-week price change: {summary.get('wow_change_pct')}%
Month-over-month price change: {summary.get('mom_change_pct')}%
Arrival change: {summary.get('arrival_change_pct')}%
Volatility: {summary.get('volatility_label')}
7-day forecast price: INR {forecast.get('forecast_price')}/quintal
Forecast range: INR {forecast.get('forecast_lower')} to INR {forecast.get('forecast_upper')}/quintal
Forecast trend: {forecast.get('forecast_trend')}
Market pressure: {market_pressure.get('pressure')}
System recommendation: {recommendation.action}
Recommended market: {recommendation.recommended_market}
Expected net gain: INR {recommendation.expected_net_gain}/quintal
Risk level: {recommendation.risk_level}
Confidence: {int(recommendation.confidence_score * 100)}%
Evidence: {evidence}

Write a weekly market intelligence report with these sections:
1. Executive summary
2. Price movement
3. Demand-supply pressure
4. Forecast
5. Recommended selling strategy
6. Risk alert
7. Data confidence

Write the report in {language}. Use simple farmer-friendly language and keep it concise.
If {language} is not English, keep market names, commodity names, and INR values unchanged.
"""


def generate_template_report(
    commodity: str,
    state: str,
    district: str,
    market: str,
    summary: dict,
    forecast: dict,
    market_pressure: dict,
    recommendation: SellingRecommendation,
    language: str = "English",
) -> str:
    reasons = "\n".join(f"- {reason}" for reason in recommendation.reasoning)
    pressure_reasons = "\n".join(f"- {reason}" for reason in market_pressure.get("reasons", []))

    language_note = ""
    if language != "English":
        language_note = f"\n\nNote: Offline template reports are generated in English. Select Groq or Gemini for {language} output.\n"

    return f"""# Weekly Market Intelligence Report

Region: {district}, {state}  
Market: {market}  
Commodity: {commodity}  
Report date: {date.today().isoformat()}
{language_note}

## Executive Summary

The current modal price for {commodity} in {market} is INR {summary.get('current_price')}/quintal. The 7-day forecast is INR {forecast.get('forecast_price')}/quintal with a {forecast.get('forecast_trend', 'Unknown').lower()} trend. The system recommendation is: **{recommendation.action}**.

## Price Movement

- 30-day average price: INR {summary.get('avg_30d')}/quintal
- Week-over-week change: {summary.get('wow_change_pct')}%
- Month-over-month change: {summary.get('mom_change_pct')}%
- Volatility: {summary.get('volatility_label')}

## Demand-Supply Pressure

Market pressure: **{market_pressure.get('pressure')}**

{pressure_reasons}

## Forecast

- 7-day forecast price: INR {forecast.get('forecast_price')}/quintal
- Forecast range: INR {forecast.get('forecast_lower')} to INR {forecast.get('forecast_upper')}/quintal

## Recommended Selling Strategy

Recommended action: **{recommendation.action}**  
Recommended market: **{recommendation.recommended_market}**  
Expected net gain: **INR {recommendation.expected_net_gain}/quintal**  
Risk level: **{recommendation.risk_level}**  
Confidence: **{int(recommendation.confidence_score * 100)}%**

Reasoning:

{reasons}

## Risk Alert

This recommendation is based on recent market data and short-term forecasting. Farmers should also consider crop quality, storage condition, transport availability, and immediate cash needs before making the final decision.
"""


def _generate_with_groq_result(prompt: str) -> GenAIResult:
    api_key = os.getenv("GROQ_API_KEY")
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    if not api_key:
        return GenAIResult(None, "Groq", model_name, False, "GROQ_API_KEY is not configured.")
    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=900,
        )
        return GenAIResult(response.choices[0].message.content, "Groq", model_name, True)
    except Exception as exc:
        return GenAIResult(None, "Groq", model_name, False, str(exc))


def _generate_with_gemini_result(prompt: str) -> GenAIResult:
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    if not api_key:
        return GenAIResult(None, "Gemini", model_name, False, "GEMINI_API_KEY is not configured.")
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model_name, contents=prompt)
        return GenAIResult(response.text, "Gemini", model_name, True)
    except Exception as primary_exc:
        try:
            import google.generativeai as legacy_genai

            legacy_genai.configure(api_key=api_key)
            model = legacy_genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return GenAIResult(response.text, "Gemini", model_name, True)
        except Exception as fallback_exc:
            return GenAIResult(
                None,
                "Gemini",
                model_name,
                False,
                f"{primary_exc}; fallback failed: {fallback_exc}",
            )


def _generate_with_groq(prompt: str) -> str | None:
    return _generate_with_groq_result(prompt).text


def _generate_with_gemini(prompt: str) -> str | None:
    return _generate_with_gemini_result(prompt).text


def generate_market_report(
    commodity: str,
    state: str,
    district: str,
    market: str,
    summary: dict,
    forecast: dict,
    market_pressure: dict,
    recommendation: SellingRecommendation,
    provider: str = "Template",
    language: str = "English",
) -> str:
    result = generate_market_report_with_status(
        commodity=commodity,
        state=state,
        district=district,
        market=market,
        summary=summary,
        forecast=forecast,
        market_pressure=market_pressure,
        recommendation=recommendation,
        provider=provider,
        language=language,
    )
    return result.text or ""


def generate_market_report_with_status(
    commodity: str,
    state: str,
    district: str,
    market: str,
    summary: dict,
    forecast: dict,
    market_pressure: dict,
    recommendation: SellingRecommendation,
    provider: str = "Template",
    language: str = "English",
) -> GenAIResult:
    prompt = build_report_prompt(
        commodity=commodity,
        state=state,
        district=district,
        market=market,
        summary=summary,
        forecast=forecast,
        market_pressure=market_pressure,
        recommendation=recommendation,
        language=language,
    )

    if provider.lower().startswith("groq"):
        result = _generate_with_groq_result(prompt)
        if result.text:
            return result
    elif provider.lower().startswith("gemini"):
        result = _generate_with_gemini_result(prompt)
        if result.text:
            return result
    else:
        result = GenAIResult(None, "Template", "offline-template", False)

    fallback_text = generate_template_report(
        commodity=commodity,
        state=state,
        district=district,
        market=market,
        summary=summary,
        forecast=forecast,
        market_pressure=market_pressure,
        recommendation=recommendation,
        language=language,
    )
    return GenAIResult(
        text=fallback_text,
        provider="Template",
        model="offline-template",
        used_api=False,
        error=result.error,
    )
