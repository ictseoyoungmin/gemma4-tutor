from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any

import httpx
import yaml
from httpx import ASGITransport

from gemma_tutor_edge.app import app
from gemma_tutor_edge.harness.models import HarnessCase


CASES_DIR = Path(__file__).resolve().parent / "sample_cases"


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


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["asgi", "http"], default="asgi")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    cases = load_cases()
    if args.mode == "asgi":
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            results = [await run_case(client, case) for case in cases]
    else:
        async with httpx.AsyncClient(base_url=args.base_url) as client:
            results = [await run_case(client, case) for case in cases]

    passed = sum(1 for r in results if r["passed"])
    print(json.dumps({"passed": passed, "total": len(results), "results": results}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
