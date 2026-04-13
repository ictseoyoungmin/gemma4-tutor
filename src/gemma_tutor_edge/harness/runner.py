from __future__ import annotations

import argparse
import asyncio
import json
import re
import time
from pathlib import Path
from typing import Any

import httpx
import yaml
from httpx import ASGITransport

from gemma_tutor_edge.harness.models import HarnessCase
from gemma_tutor_edge.schemas import HarnessCaseResult, HarnessRunResponse, QuizPack


CASES_DIR = Path(__file__).resolve().parent / "sample_cases"
HANGUL_PATTERN = re.compile(r"[가-힣]")


def load_cases() -> list[HarnessCase]:
    cases: list[HarnessCase] = []
    for path in sorted(CASES_DIR.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        cases.append(HarnessCase.model_validate(raw))
    return cases


async def run_case(client: httpx.AsyncClient, case: HarnessCase) -> dict[str, Any]:
    route = "/v1/chat" if case.route == "chat" else "/v1/quiz/generate"
    start = time.perf_counter()
    resp = await client.post(route, json=case.payload)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    ok = resp.status_code == 200
    body: dict[str, Any] = {}
    if ok:
        body = resp.json()
        for key in case.expect_keys:
            if key not in body:
                ok = False
                break
    if elapsed_ms > case.max_latency_ms:
        ok = False
    return {
        "case_id": case.case_id,
        "status_code": resp.status_code,
        "elapsed_ms": round(elapsed_ms, 2),
        "passed": ok,
        "body_preview": json.dumps(body, ensure_ascii=False)[:300],
    }


def validate_generated_pack(
    pack: QuizPack,
    *,
    require_english_items: bool = True,
    require_korean_explanations: bool = True,
) -> dict[str, Any]:
    failures: list[str] = []
    if not pack.title.strip():
        failures.append("missing_title")
    if len(pack.items) < 3:
        failures.append("too_few_items")
    for index, item in enumerate(pack.items):
        if not item.prompt.strip():
            failures.append(f"item_{index}_missing_prompt")
        if require_english_items:
            if HANGUL_PATTERN.search(item.prompt):
                failures.append(f"item_{index}_prompt_not_english")
            if any(HANGUL_PATTERN.search(choice) for choice in item.choices):
                failures.append(f"item_{index}_choice_not_english")
            if HANGUL_PATTERN.search(item.answer):
                failures.append(f"item_{index}_answer_not_english")
        if require_korean_explanations and not HANGUL_PATTERN.search(item.explanation):
            failures.append(f"item_{index}_explanation_not_korean")
        if item.choices:
            if len(item.choices) != 4:
                failures.append(f"item_{index}_invalid_choice_count")
            if len(set(item.choices)) != len(item.choices):
                failures.append(f"item_{index}_duplicate_choices")
            if item.answer not in item.choices:
                failures.append(f"item_{index}_answer_not_in_choices")
    return {
        "passed": not failures,
        "failures": failures,
        "item_count": len(pack.items),
    }


async def execute_harness(*, mode: str = "asgi", base_url: str = "http://127.0.0.1:8000") -> HarnessRunResponse:
    cases = load_cases()
    if mode == "asgi":
        from gemma_tutor_edge.app import app

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            results = [HarnessCaseResult.model_validate(await run_case(client, case)) for case in cases]
    else:
        async with httpx.AsyncClient(base_url=base_url) as client:
            results = [HarnessCaseResult.model_validate(await run_case(client, case)) for case in cases]
    passed = sum(1 for r in results if r.passed)
    return HarnessRunResponse(passed=passed, total=len(results), results=results)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["asgi", "http"], default="asgi")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    result = await execute_harness(mode=args.mode, base_url=args.base_url)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
