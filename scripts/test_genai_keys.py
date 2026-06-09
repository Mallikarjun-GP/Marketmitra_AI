from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

from src.genai.report_generator import _generate_with_gemini_result, _generate_with_groq_result, get_provider_status

load_dotenv()


TEST_PROMPT = """Write exactly two short sentences.
Sentence 1: MarketMitra AI test successful.
Sentence 2: Do not include any API key or secret."""


def test_provider(provider: str) -> bool:
    if provider == "groq":
        result = _generate_with_groq_result(TEST_PROMPT)
    elif provider == "gemini":
        result = _generate_with_gemini_result(TEST_PROMPT)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    print(f"\nProvider: {result.provider}")
    print(f"Model: {result.model}")
    print(f"API used: {result.used_api}")

    if result.text:
        print("Status: OK")
        print("Response preview:")
        print(result.text[:300])
        return True

    print("Status: FAILED")
    print(f"Error: {result.error}")
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Test configured Groq/Gemini API keys without printing secrets.")
    parser.add_argument("--provider", choices=["all", "groq", "gemini"], default="all")
    args = parser.parse_args()

    status = get_provider_status()
    print("Configured providers:")
    for name, configured in status.items():
        print(f"- {name}: {'yes' if configured else 'no'}")

    providers = ["groq", "gemini"] if args.provider == "all" else [args.provider]
    results = [test_provider(provider) for provider in providers]

    if not any(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

